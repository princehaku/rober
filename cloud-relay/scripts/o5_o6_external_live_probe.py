#!/usr/bin/env python3
"""O5/O6 external live probe with Python stdlib only."""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


SCHEMA = "trashbot.o5_o6.external_live_probe.v1"
RUNNER = "python_stdlib"
PC_AGGREGATE_ENDPOINT = "/api/o5-o6/cloud-relay-health"
O5_ENDPOINT = "/api/o5/readiness/health"
O6_ENDPOINT = "/api/o6/archive/health"
TOKEN_ENVS = ("TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN", "ROBER_CLOUD_RELAY_BEARER_TOKEN")
EXPECTED_SCHEMAS = {
    "o5_readiness": "trashbot.o5.readiness_health.v1",
    "o6_archive": "trashbot.o6.archive_health.v1",
    "pc_aggregate": "trashbot.pc_tools_workstation.o5_o6_cloud_relay_health.v1",
}

# 这里固定 schema，而不是从服务端协商，是为了让现场证据能被后续脚本稳定消费。
# runner 单独标注 Python stdlib，避免把 Node 版外部探针和上位机 stdin runner 混为一谈。
# PC aggregate 是可选观察面；它不可替代 cloud relay 两个 direct health endpoint。
# O5 endpoint 只看 readiness 缺口摘要，不能读取机器人命令或生产控制面。
# O6 endpoint 只看 archive health 摘要，不能读取 task detail 或写 archive store。
# bearer 环境变量兼容历史命名；脚本仍只输出 present/absent，绝不回显 token。
# expected schema 是 contract gate；schema drift 必须 fail closed，不能自动宽容。

# 这些字段一旦在上游 health 中为 true，就说明该 payload 越过了只读证据边界。
DANGEROUS_TRUE_FIELDS = {
    "safe_to_control",
    "sends_commands",
    "robot_control_executed",
    "delivery_success",
    "primary_actions_enabled",
    "production_ready",
    "production_db_connected",
    "connects_cloud_production",
    "reads_hardware",
    "real_oss_upload",
    "real_inference_model_runtime",
}

# safe_to_control 为 true 代表越过用户触点只读探针边界，必须阻断。
# sends_commands 为 true 代表 endpoint 可能触发控制链，不能作为 live health 证据。
# robot_control_executed 为 true 只能来自真实闭环材料，不能由 health probe 声明。
# delivery_success 为 true 会误导 OKR，必须留给真实送达验收材料。
# primary_actions_enabled 为 true 表示产品入口已可操作，外部探针不能背书。
# production_ready 为 true 必须来自完整生产材料，不由本脚本认可。
# production_db_connected 为 true 需要 production DB/queue probe，而不是 health 摘要。
# connects_cloud_production 为 true 需要公网/4G/生产环境材料，不能由本地 mock 替代。
# reads_hardware 为 true 与本脚本的 no_hardware_read contract 冲突。
# real_oss_upload 为 true 需要 OSS/STS/CDN live evidence，health payload 不应声称。
# real_inference_model_runtime 为 true 需要真实推理 runtime 证据，不能从 archive health 推断。

# 敏感 key / 文本 marker 只输出路径，不输出原值，避免 SSH/stdout 证据泄漏现场信息。
SENSITIVE_KEY_PARTS = (
    "authorization",
    "bearer",
    "token",
    "secret",
    "password",
    "credential",
    "state_path",
    "db_url",
    "queue_url",
    "traceback",
    "serial",
    "uart",
    "wave_rover",
    "ros_topic",
    "cmd_vel",
)
SENSITIVE_TEXT_MARKERS = (
    "authorization",
    "bearer ",
    "token=",
    "password=",
    "secret=",
    "traceback",
    "/cmd_vel",
    "/dev/",
    "wave rover",
    "wave_rover",
    "serial",
    "uart",
    "ros topic",
    "oss://",
    "mongodb://",
    "redis://",
    "postgres://",
    "mysql://",
)

# Authorization/bearer/token 等 key 只允许进入路径级告警，不允许进入结果正文。
# state_path 可能暴露现场目录布局，所以按敏感信息处理。
# db_url/queue_url 可能携带账号或内网拓扑，所以只记录 marker 路径。
# traceback 往往包含路径、环境变量或内部实现细节，因此禁止原样输出。
# serial/uart/wave_rover/cmd_vel 是硬件和控制边界 marker，出现在 health 里要归类。
# 文本 marker 覆盖 URL、OSS、数据库协议和设备路径，防止敏感值藏在普通字符串中。


def parse_args(argv: list[str]) -> argparse.Namespace:
    # --once-json 是为了兼容 SSH stdin 运行；本脚本本来就只执行一次并输出 JSON。
    parser = argparse.ArgumentParser(description="Read-only O5/O6 external live probe")
    parser.add_argument("--once-json", action="store_true", help="compat flag; output one JSON object")
    parser.add_argument("--pc-base-url", default="", help="PC workstation API base URL")
    parser.add_argument("--cloud-base-url", default="", help="cloud-relay API base URL")
    parser.add_argument("--timeout-ms", type=int, default=2500, help="HTTP timeout in milliseconds")
    parser.add_argument("--output", default="", help="optional JSON artifact output path")
    return parser.parse_args(argv)


def now_iso() -> str:
    # 使用 UTC 是为了让开发机、云 VM 和上位机输出可直接排序对齐。
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def read_config(args: argparse.Namespace) -> dict:
    # bearer 只允许从环境变量读取，避免命令行参数、shell history 或文档留痕泄漏凭证。
    token = ""
    for name in TOKEN_ENVS:
        # 按优先级取第一个非空 token，避免把多个 token 状态写入证据。
        value = os.environ.get(name, "").strip()
        if value:
            token = value
            break
    # timeout 归一为正数，避免 SSH stdin 误传 0 后让探针无限等待。
    timeout_ms = args.timeout_ms if args.timeout_ms and args.timeout_ms > 0 else 2500
    return {
        # CLI 参数优先，便于一次性现场探测；环境变量保留给自动化和 runbook。
        "pc_base_url": (args.pc_base_url or os.environ.get("ROBER_O5_O6_EXTERNAL_PROBE_PC_BASE_URL", "")).strip(),
        # cloud base URL 兼容专用 probe 变量和历史 relay base URL 变量。
        "cloud_base_url": (
            args.cloud_base_url
            or os.environ.get("ROBER_O5_O6_EXTERNAL_PROBE_CLOUD_BASE_URL", "")
            or os.environ.get("ROBER_CLOUD_RELAY_BASE_URL", "")
        ).strip(),
        "token": token,
        "timeout_s": timeout_ms / 1000.0,
    }


def normalize_base_url(raw: str) -> dict:
    # URL 先做白名单规范化，防止 query/hash/credential 被拼进探测请求或日志。
    value = (raw or "").strip()
    if not value:
        # 未配置是正常 blocked 状态，应输出结构化原因而不是抛异常。
        return {"ok": False, "reason": "base_url_not_configured", "display_url": "not_configured", "normalized": ""}
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        # 只允许 HTTP(S) 是为了禁止 file、ssh、unix socket 等非预期读取面。
        return {"ok": False, "reason": "base_url_invalid", "display_url": "blocked_invalid_url", "normalized": ""}
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        # credential/query/hash 都可能携带 token 或动态参数，统一拒绝并脱敏展示。
        return {
            "ok": False,
            "reason": "base_url_must_not_include_credentials_query_or_hash",
            "display_url": "blocked_credentialed_url",
            "normalized": "",
        }
    path = parsed.path.rstrip("/")
    # 保留 path 前缀是为了支持 relay 挂在反向代理子路径下的部署形态。
    normalized = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, path, "", "")).rstrip("/")
    # display_url 只表达配置形态，不回显 raw host 或 path，避免 artifact 成为公网/内网拓扑清单。
    display_url = f"{parsed.scheme}://{host_status(parsed.hostname or '')}"
    if parsed.port:
        display_url = f"{display_url}:port_configured"
    if path:
        display_url = f"{display_url}/path_configured"
    return {"ok": True, "reason": "ok", "display_url": display_url, "normalized": normalized, "parsed": parsed}


def host_status(hostname: str) -> str:
    # host 只用于分类，不原样输出；IP、localhost 和公网域名分别给 operator 不同判断入口。
    text = (hostname or "").strip().lower()
    if not text:
        return "missing"
    if text in ("localhost", "::1"):
        return "loopback"
    if text.startswith("127.") or text == "0:0:0:0:0:0:0:1":
        return "loopback"
    if text.startswith("10.") or text.startswith("192.168."):
        return "private_lan"
    if text.startswith("172."):
        parts = text.split(".")
        if len(parts) > 1 and parts[1].isdigit() and 16 <= int(parts[1]) <= 31:
            return "private_lan"
    # 这里不做 DNS 解析，避免为分类额外发起网络访问。
    return "redacted_public_or_custom_host"


def redacted_hostname(hostname: str) -> str:
    # host 可能暴露公网域名或内网拓扑，因此只输出短 hash，便于多次证据比对。
    text = (hostname or "").strip().lower()
    if not text:
        return "not_configured"
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    return f"sha256:{digest}"


def parse_cert_time(value: object) -> datetime.datetime | None:
    # Python ssl.getpeercert() 使用固定英文时间格式；解析失败时不抛出到主流程。
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.datetime.strptime(value, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=datetime.timezone.utc)
    except ValueError:
        return None


def summarize_name_tuple(value: object) -> dict:
    # subject/issuer 只保留字段是否存在和条目数，不回显完整 DN 或组织名。
    fields: dict[str, int] = {}
    if isinstance(value, tuple):
        for group in value:
            if not isinstance(group, tuple):
                continue
            for item in group:
                if isinstance(item, tuple) and len(item) >= 2:
                    key = str(item[0])
                    fields[key] = fields.get(key, 0) + 1
    return {
        "field_count": sum(fields.values()),
        "common_name_status": "present" if fields.get("commonName") else "absent",
        "organization_status": "present" if fields.get("organizationName") else "absent",
        "country_status": "present" if fields.get("countryName") else "absent",
    }


def summarize_certificate(cert: object, now: datetime.datetime | None = None) -> dict:
    # 证书摘要只表达有效期和安全计数，不输出 raw subject、issuer 或 SAN 域名。
    record = cert if isinstance(cert, dict) else {}
    not_before = record.get("notBefore")
    not_after = record.get("notAfter")
    parsed_not_after = parse_cert_time(not_after)
    now_utc = now or datetime.datetime.now(datetime.timezone.utc)
    san_entries = record.get("subjectAltName") if isinstance(record.get("subjectAltName"), tuple) else ()
    san_dns_count = sum(1 for item in san_entries if isinstance(item, tuple) and item[:1] == ("DNS",))
    san_ip_count = sum(1 for item in san_entries if isinstance(item, tuple) and item[:1] == ("IP Address",))
    expiry_days = None
    if parsed_not_after:
        # 用整天数便于 operator 判断证书是否快过期；负数表示已经过期。
        expiry_days = int((parsed_not_after - now_utc).total_seconds() // 86400)
    return {
        "not_before": safe_text(not_before, "not_available") if isinstance(not_before, str) else "not_available",
        "not_after": safe_text(not_after, "not_available") if isinstance(not_after, str) else "not_available",
        "certificate_expiry_days": expiry_days,
        "issuer_summary": summarize_name_tuple(record.get("issuer")),
        "subject_summary": summarize_name_tuple(record.get("subject")),
        "subject_alt_name_summary": {
            "dns_name_count": san_dns_count,
            "ip_address_count": san_ip_count,
        },
    }


def classify_tls_error(exc: BaseException) -> str:
    # TLS 错误只输出粗分类，不把 OpenSSL 异常文本或 hostname 写入 artifact。
    if isinstance(exc, ssl.SSLCertVerificationError):
        code = getattr(exc, "verify_code", None)
        if code == 10:
            return "certificate_expired"
        if code in (18, 19, 20, 21):
            return "self_signed_or_untrusted"
        text = str(getattr(exc, "verify_message", "")).lower()
        if "hostname" in text:
            return "hostname_mismatch"
        return "certificate_verify_failed"
    if isinstance(exc, ssl.SSLError):
        return "tls_handshake_failed"
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return "network_timeout"
    if isinstance(exc, OSError):
        return "network_or_service_unreachable"
    return "tls_observation_failed"


def collect_tls_evidence(url_status: dict, timeout_s: float) -> dict:
    # TLS evidence 是外部材料摘要，不改变任何 safety false 字段，也不触发 HTTP POST。
    if not url_status["ok"]:
        return {
            "tls_status": "not_configured" if url_status["reason"] == "base_url_not_configured" else "blocked",
            "scheme": "not_configured",
            "hostname_redacted": "not_configured",
            "host_status": url_status["reason"],
            "port": None,
            "tls_observed": False,
            "tls_version": "not_observed",
            "cipher_status": "not_observed",
            "cipher_bits": None,
            "certificate": summarize_certificate({}),
            "verification_error": url_status["reason"],
        }
    parsed = url_status.get("parsed")
    scheme = parsed.scheme if parsed else "unknown"
    hostname = parsed.hostname if parsed else ""
    port = parsed.port or (443 if scheme == "https" else 80)
    base = {
        "scheme": scheme,
        "hostname_redacted": redacted_hostname(hostname or ""),
        "host_status": host_status(hostname or ""),
        "port": port,
        "tls_observed": False,
        "tls_version": "not_observed",
        "cipher_status": "not_observed",
        "cipher_bits": None,
        "certificate": summarize_certificate({}),
        "verification_error": "not_applicable",
    }
    if scheme != "https":
        # HTTP 明确属于 not_applicable，不把没有 TLS 误报成失败。
        return {"tls_status": "not_applicable", **base}
    try:
        context = ssl.create_default_context()
        # create_connection 只连 cloud base host:port，不访问 path，也不发送 HTTP 请求。
        with socket.create_connection((hostname, port), timeout=timeout_s) as raw_socket:
            with context.wrap_socket(raw_socket, server_hostname=hostname) as tls_socket:
                cipher = tls_socket.cipher() or ("unknown", "unknown", None)
                return {
                    "tls_status": "observed",
                    **base,
                    "tls_observed": True,
                    "tls_version": safe_text(tls_socket.version(), "unknown"),
                    "cipher_status": "present" if cipher[0] != "unknown" else "unknown",
                    "cipher_bits": cipher[2] if isinstance(cipher[2], int) else None,
                    "certificate": summarize_certificate(tls_socket.getpeercert()),
                    "verification_error": "none",
                }
    except BaseException as exc:
        # TLS 观察失败仍必须保留 JSON shape，避免现场网络问题变成 traceback。
        return {"tls_status": "blocked", **base, "verification_error": classify_tls_error(exc)}


def safe_text(value: object, fallback: str = "unknown") -> str:
    # 非字符串统一回退，避免把复杂对象 stringify 后泄漏原始 payload。
    text = value if isinstance(value, str) else fallback
    # 压缩空白并截断，防止服务端错误页或长 traceback 撑爆一行 JSON 证据。
    text = " ".join(text.split())[:160]
    lower = text.lower()
    # 命中敏感 marker 时只保留 redacted 状态，不保留原始片段。
    return "redacted_sensitive_value" if any(marker in lower for marker in SENSITIVE_TEXT_MARKERS) else text


def allowed_safe_metadata_path(path: str) -> bool:
    # PC 聚合 health 的 token_status/token_envs 是安全状态/配置名，不是 token 原值。
    tail = path.rsplit(".", 1)[-1]
    if tail == "token_status":
        # token_status 只能是 present/absent 这类状态，不包含 token 值。
        return True
    if "token_envs" in path:
        # token_envs 只暴露允许读取的环境变量名，便于核对凭证来源边界。
        return True
    return False


def scan_dangerous_true_fields(value: object, prefix: str = "") -> list[str]:
    # 递归扫描 true flag，防止上游把 health payload 误包装成控制或生产能力。
    hits: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            # 记录完整路径，方便定位 drift 字段来自 direct health 还是 PC aggregate。
            path = f"{prefix}.{key}" if prefix else key
            if key in DANGEROUS_TRUE_FIELDS and item is True:
                hits.append(path)
            # 子对象继续扫描，因为危险字段常藏在 summary/capabilities/details 内。
            hits.extend(scan_dangerous_true_fields(item, path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            # list index 进入路径即可，不需要输出 list 原始内容。
            hits.extend(scan_dangerous_true_fields(item, f"{prefix}[{index}]"))
    return hits


def scan_sensitive_markers(value: object, prefix: str = "") -> list[str]:
    # 只返回敏感 marker 的路径，便于分类；原始敏感值不进入 probe 结果。
    hits: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else key
            if any(part in key.lower() for part in SENSITIVE_KEY_PARTS) and not allowed_safe_metadata_path(path):
                # key 本身命中敏感语义时立即记录路径，即使 value 是空字符串也不信任。
                hits.append(path)
            # value 仍需递归，因为敏感字符串可能藏在非敏感 key 下面。
            hits.extend(scan_sensitive_markers(item, path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            # 数组元素同样只暴露路径，避免回显 token-bearing item。
            hits.extend(scan_sensitive_markers(item, f"{prefix}[{index}]"))
    elif isinstance(value, str) and any(marker in value.lower() for marker in SENSITIVE_TEXT_MARKERS):
        # 普通字符串命中 marker 时只记录路径，原字符串不进入结果。
        hits.append(prefix or "payload")
    return hits


def endpoint_base(name: str, endpoint: str, expected_schema: str, url_status: dict) -> dict:
    # 每个 endpoint 先从 fail-closed baseline 开始，只有完整通过扫描才升级为 observed。
    endpoint_display = endpoint.split("?", 1)[0]
    return {
        "name": name,
        "endpoint": endpoint_display,
        "expected_schema": expected_schema,
        "reachable": False,
        "http_status": None,
        "schema": "not_loaded",
        "schema_status": "not_loaded",
        "contract_status": "fail_closed",
        "failure_category": "not_started" if url_status["ok"] else url_status["reason"],
        "blocked_reasons": [] if url_status["ok"] else [url_status["reason"]],
        "dangerous_true_fields": [],
        "sensitive_markers": [],
    }


def fetch_json(base_url: str, endpoint: str, token: str, timeout_s: float) -> dict:
    # urllib 只发 GET；本脚本没有 POST、没有 /robots/*、没有硬件读取路径。
    request = urllib.request.Request(f"{base_url}{endpoint}", method="GET", headers={"Accept": "application/json"})
    if token:
        # bearer 只发给 direct cloud health；调用方负责 PC aggregate 不传 token。
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            # response body 只在本函数内解析，不会原样进入最终 probe 输出。
            raw = response.read().decode("utf-8", errors="replace")
            status = response.getcode()
    except urllib.error.HTTPError as exc:
        # HTTP 4xx/5xx 仍可能有 JSON body，需要保留状态码做结构化分类。
        status = exc.code
        raw = exc.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError):
        # 网络、DNS、连接拒绝和超时统一归为服务不可达，避免泄漏底层异常文本。
        return {"ok": False, "status": None, "body": None, "bad_json": False}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # 坏 JSON 仍说明 HTTP 层可达，但 contract 不可用。
        return {"ok": True, "status": status, "body": None, "bad_json": True}
    # 只接受 JSON object，数组或标量都不能表达 health contract。
    return {"ok": True, "status": status, "body": parsed if isinstance(parsed, dict) else None, "bad_json": not isinstance(parsed, dict)}


def summarize_endpoint(name: str, endpoint: str, expected_schema: str, url_status: dict, fetch_result: dict | None) -> dict:
    summary = endpoint_base(name, endpoint, expected_schema, url_status)
    if not url_status["ok"]:
        # URL 未通过白名单时不发网络请求，直接返回配置类 blocked 原因。
        return summary
    if not fetch_result or not fetch_result["ok"]:
        # 网络失败不区分真实 4G、公网、服务未启动；本脚本只做外部可达性证据。
        summary["failure_category"] = "network_or_service_unreachable"
        summary["blocked_reasons"] = ["network_or_service_unreachable"]
        return summary

    body = fetch_result["body"] if isinstance(fetch_result["body"], dict) else None
    # schema 读取也走 safe_text，防止服务端把敏感字符串塞进 schema 字段。
    schema = safe_text(body.get("schema") if body else None, "missing_schema")
    schema_status = "matched" if schema == expected_schema else "mismatch"
    # dangerous/sensitive 扫描先完成，再统一放入 blocked_reasons，便于单测和人工 review。
    dangerous = [f"{name}.{field}" for field in scan_dangerous_true_fields(body or {})]
    sensitive = [f"{name}.{field}" for field in scan_sensitive_markers(body or {})]
    blocked = []
    if fetch_result["bad_json"]:
        # bad_json 代表 contract 不可消费，即使 HTTP 状态是 200 也必须 fail closed。
        blocked.append("bad_json")
    if not (200 <= int(fetch_result["status"] or 0) < 300):
        # 非 2xx 保留状态码，便于区分未授权、服务不可用和路由不存在。
        blocked.append(f"http_{fetch_result['status']}")
    if schema_status != "matched":
        # schema mismatch 是接口漂移信号，不能用字段猜测继续放行。
        blocked.append("schema_mismatch")
    blocked.extend(f"dangerous_true:{field}" for field in dangerous)
    blocked.extend(f"sensitive_marker:{field}" for field in sensitive)

    summary.update(
        {
            # reachable 只表示 HTTP 层有状态码，不等于 contract 已通过。
            "reachable": fetch_result["status"] is not None,
            "http_status": fetch_result["status"],
            "schema": schema,
            "schema_status": schema_status,
            # 没有 blocked 才能记录 observed_fail_closed_contract，仍不代表 production ready。
            "contract_status": "observed_fail_closed_contract" if not blocked else "fail_closed",
            "failure_category": blocked[0] if blocked else "none",
            "blocked_reasons": blocked,
            "dangerous_true_fields": dangerous,
            "sensitive_markers": sensitive,
        }
    )
    return summary


def final_status(endpoints: list[dict], tls_evidence: dict | None = None) -> dict:
    # 全部 endpoint 都符合 schema 和安全扫描时，仍只是 observed fail-closed contract。
    blocked = [reason for item in endpoints for reason in item["blocked_reasons"]]
    if tls_evidence and tls_evidence.get("tls_status") == "blocked":
        # HTTPS TLS 观察失败代表真实外部 HTTPS 材料仍缺口，整体必须继续 fail closed。
        blocked.append(f"tls_blocked:{tls_evidence.get('verification_error', 'unknown')}")
    if endpoints and all(item["contract_status"] == "observed_fail_closed_contract" for item in endpoints):
        if blocked:
            return {"probe_status": "fail_closed", "blocked_reasons": blocked}
        # observed_fail_closed_contract 只证明只读 health contract 可观测，不提升真实材料结论。
        return {"probe_status": "observed_fail_closed_contract", "blocked_reasons": []}
    # 只要任一 endpoint blocked，整体 probe 必须 fail_closed，方便自动化用 exit code 判断。
    return {"probe_status": "fail_closed", "blocked_reasons": blocked or ["not_all_endpoints_observed"]}


def run_probe(args: argparse.Namespace) -> dict:
    config = read_config(args)
    # PC 和 cloud base URL 分开规范化，因为 PC aggregate 与 direct cloud health 权限边界不同。
    pc_url = normalize_base_url(config["pc_base_url"])
    cloud_url = normalize_base_url(config["cloud_base_url"])

    # direct O5/O6 只在 cloud URL 合法时请求，避免把空 URL 拼成异常网络目标。
    direct_o5 = fetch_json(cloud_url["normalized"], O5_ENDPOINT, config["token"], config["timeout_s"]) if cloud_url["ok"] else None
    direct_o6 = fetch_json(cloud_url["normalized"], O6_ENDPOINT, config["token"], config["timeout_s"]) if cloud_url["ok"] else None
    pc_endpoint = PC_AGGREGATE_ENDPOINT
    if cloud_url["ok"]:
        # cloud URL 作为 query 传给 PC aggregate 只是观察参数，不携带 bearer。
        pc_endpoint = f"{PC_AGGREGATE_ENDPOINT}?baseUrl={urllib.parse.quote(cloud_url['normalized'], safe='')}"
    # PC aggregate 不转发 direct cloud bearer，避免一个探针把云端凭证交给 workstation。
    pc_result = fetch_json(pc_url["normalized"], pc_endpoint, "", config["timeout_s"]) if pc_url["ok"] else None
    tls_evidence = collect_tls_evidence(cloud_url, config["timeout_s"])

    # endpoint 顺序固定为 O5/O6/PC，便于日志 diff 和人工复核。
    endpoints = [
        summarize_endpoint("o5_readiness", O5_ENDPOINT, EXPECTED_SCHEMAS["o5_readiness"], cloud_url, direct_o5),
        summarize_endpoint("o6_archive", O6_ENDPOINT, EXPECTED_SCHEMAS["o6_archive"], cloud_url, direct_o6),
        summarize_endpoint("pc_aggregate", pc_endpoint, EXPECTED_SCHEMAS["pc_aggregate"], pc_url, pc_result),
    ]
    status = final_status(endpoints, tls_evidence)
    return {
        # 顶层 schema/runner/viewpoint 是 evidence consumer 的稳定索引字段。
        "schema": SCHEMA,
        "runner": RUNNER,
        "executed_at": now_iso(),
        "probe_status": status["probe_status"],
        "viewpoint": "external_or_upper_computer_readonly",
        # display_url 已经过 normalize_base_url 脱敏，不包含 query、hash 或 credential。
        "pc_base_url": pc_url["display_url"],
        "cloud_base_url": cloud_url["display_url"],
        "token_status": "present" if config["token"] else "absent",
        "credentials_redacted": True,
        "tls_evidence": tls_evidence,
        "endpoints": endpoints,
        "summary": {
            # summary 只聚合安全计数，避免上层 UI 解析每个 endpoint 才能判断 blocked 状态。
            "endpoint_count": len(endpoints),
            "reachable_count": sum(1 for item in endpoints if item["reachable"]),
            "schema_matched_count": sum(1 for item in endpoints if item["schema_status"] == "matched"),
            "fail_closed_count": sum(1 for item in endpoints if item["contract_status"] != "observed_fail_closed_contract"),
            # 以下 false 字段是证据边界锁，不随 endpoint payload 自动改变。
            "safe_to_control": False,
            "sends_commands": False,
            "robot_control_executed": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "reads_hardware": False,
        },
        "safety_policy": {
            # safety_policy 让审阅者不用读源码也能确认探针没有控制面动作。
            "method_allowlist": ["GET"],
            "endpoint_allowlist": [O5_ENDPOINT, O6_ENDPOINT, PC_AGGREGATE_ENDPOINT],
            "forbidden_paths": ["/robots/*", "/cmd_vel"],
            "bearer_source": "environment_only",
            "no_post": True,
            "no_robot_control": True,
            "no_hardware_read": True,
        },
        # blocked_reasons 截断是为了让 SSH stdout 证据短小稳定，详细原因仍在 endpoints 内。
        "blocked_reasons": status["blocked_reasons"][:20],
        "not_proven": [
            # not_proven 明确把软件探针和真实公网/4G/生产材料隔开。
            "real_public_https_tls_not_proven",
            "real_4g_sim_not_proven",
            "production_db_queue_not_proven",
            "real_oss_cdn_live_traffic_not_proven",
            "real_phone_browser_not_proven",
            "delivery_success_not_proven",
        ],
        # 顶层安全 false 字段给简单 grep / jq 检查使用，避免只读边界被 UI 遗漏。
        "safe_to_control": False,
        "sends_commands": False,
        "reads_hardware": False,
        "robot_control_executed": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def main(argv: list[str]) -> int:
    # stdout 永远输出一个 JSON object，方便 ssh 失败以外的场景被自动化收集。
    args = parse_args(argv)
    result = run_probe(args)
    if args.output:
        # 可选落盘只写同一份脱敏 JSON；目录由调用方显式指定，脚本不猜测仓库位置。
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
    sys.stdout.write(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n")
    # exit 2 代表配置/网络/contract 仍 blocked；stdout 始终可机器读取。
    return 0 if result["probe_status"] == "observed_fail_closed_contract" else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
