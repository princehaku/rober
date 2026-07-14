#!/usr/bin/env python3
"""O5 CDN/TLS external evidence probe.

该 CLI 真实访问 HTTPS 目标，但只持久化脱敏证据：scheme、host hash、
TLS/证书布尔值、HTTP 状态类别、耗时桶、content-length 桶和安全 blocker。
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import ipaddress
import json
import os
import re
import socket
import ssl
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit


# 默认目标来自 OKR O5 KR4。拆成组件是为了避免 artifact/日志误复制完整 URL。
DEFAULT_TARGET_SCHEME = "https"
DEFAULT_TARGET_HOST = "cdn.bytegallop.com"
DEFAULT_TARGET_PATH = "/rober/"
DEFAULT_TARGET = f"{DEFAULT_TARGET_SCHEME}://{DEFAULT_TARGET_HOST}{DEFAULT_TARGET_PATH}"
DEFAULT_ENV_VAR = "ROBER_CDN_PROBE_BASE_URL"

# 这些字段是 Product 验收要求的固定 false 边界，不能被 probe 成功改写。
SCHEMA = "trashbot.o5.cdn_tls_external_evidence.v1"
SCHEMA_VERSION = 1
EVIDENCE_KEY = "cdn_tls_external_evidence"
PROOF_BOUNDARY = "o5_cdn_tls_external_evidence_delta_not_production_ready"
NEXT_LIVE_COMMAND = (
    "ROBER_CDN_PROBE_BASE_URL=<https_base_url> "
    "python3 onboard/scripts/o5_cdn_tls_external_evidence_probe.py "
    "--output <sanitized_artifact_path>"
)
FIXED_FALSE_INVARIANTS = [
    "delivery_success=false",
    "safe_to_control=false",
    "robot_control_executed=false",
    "route_execution_success=false",
    "hil_pass=false",
]
REJECTED_CLAIMS = [
    "production_cloud_ready",
    "oss_object_upload",
    "cdn_origin_fetch",
    "production_db_queue",
    "production_worker_cutover",
    "four_g_sim",
    "real_phone_browser",
    "route_execution",
    "delivery_success",
    "hil",
    "safe_to_control",
]

# 输入只允许公开 HTTPS base/path；这些 marker 一旦出现在 override 中就 fail closed。
SENSITIVE_INPUT_MARKERS = (
    "authorization",
    "bearer",
    "cookie",
    "token",
    "secret",
    "password",
    "passwd",
    "credential",
    "access_key",
    "accesskey",
    "signature",
    "x-oss",
    "x-amz",
    "sts",
)
LOCAL_HOST_SUFFIXES = (".local", ".localhost", ".internal", ".lan")
HOST_ALLOWED = re.compile(r"^[A-Za-z0-9.-]+$")
CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
FULL_URL_PATTERN = re.compile(r"https?://", re.IGNORECASE)
ABSOLUTE_PATH_PATTERN = re.compile(r"(^|[\s\"'])/(Users|home|var|tmp|private|opt|etc)/", re.IGNORECASE)


class ProbeInputError(ValueError):
    """目标 URL 不满足 fail-closed 输入合同。"""

    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


class ProbeRuntimeError(RuntimeError):
    """网络/TLS/HTTP 失败只保留 reason code，不保留异常正文。"""

    def __init__(
        self,
        reason_code: str,
        *,
        external_request_attempted: bool = True,
        tls_handshake_observed: bool = False,
        certificate_valid_for_host: bool = False,
        elapsed_ms: int | None = None,
    ) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code
        self.external_request_attempted = external_request_attempted
        self.tls_handshake_observed = tls_handshake_observed
        self.certificate_valid_for_host = certificate_valid_for_host
        self.elapsed_ms = elapsed_ms


@dataclass(frozen=True)
class SafeTarget:
    """内部可用的目标结构；artifact 只写 hash，不写 host/path。"""

    raw_url: str
    source: str
    hostname: str
    port: int
    request_path: str


@dataclass(frozen=True)
class HttpObservation:
    """网络层返回的最小观察结果，不携带响应体或原始 headers。"""

    method: str
    status_code: int
    elapsed_ms: int
    content_length: int | None
    tls_handshake_observed: bool
    certificate_valid_for_host: bool
    head_rejected_get_fallback_attempted: bool = False


def utc_now_iso() -> str:
    """统一用 UTC，避免 macOS/Docker 时区差异污染 sprint 证据。"""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _reason_list(reason: str | list[str]) -> list[str]:
    """blocked_reasons 始终是 list，便于 shell/json.tool 和后续消费者断言。"""

    if isinstance(reason, list):
        return [str(item) for item in reason if str(item)]
    return [str(reason)] if str(reason) else []


def _default_target() -> str:
    """只在内存里拼出 OKR KR4 默认目标，artifact 不回显完整 URL。"""

    return DEFAULT_TARGET


def choose_target(env: dict[str, str] | None = None) -> tuple[str, str]:
    """环境变量可覆盖目标；artifact 只记录 target_source。"""

    source_env = env if env is not None else os.environ
    override = str(source_env.get(DEFAULT_ENV_VAR, "") or "").strip()
    if override:
        return override, "env_override"
    return _default_target(), "okr_kr4_default"


def _contains_sensitive_marker(text: str) -> bool:
    """输入里出现 secret/cookie/token 类 marker 时直接拒绝，不尝试脱敏后继续。"""

    lowered = text.lower()
    return any(marker in lowered for marker in SENSITIVE_INPUT_MARKERS)


def _host_is_external(hostname: str) -> bool:
    """外部 evidence 不能指向 localhost、私网 IP 或本地域名。"""

    lowered = hostname.lower().rstrip(".")
    if lowered in {"localhost", "127.0.0.1", "::1"}:
        return False
    if any(lowered.endswith(suffix) for suffix in LOCAL_HOST_SUFFIXES):
        return False
    try:
        address = ipaddress.ip_address(lowered.strip("[]"))
    except ValueError:
        # 公网域名在这里不做 DNS 解析；真实可达性交给后续 probe。
        return "." in lowered and HOST_ALLOWED.fullmatch(lowered) is not None
    return not (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )


def normalize_target(raw_url: str, source: str) -> SafeTarget:
    """校验 HTTPS/public target；返回值只供网络层使用，不写入 artifact。"""

    if not raw_url or CONTROL_CHARS.search(raw_url) or raw_url.strip() != raw_url:
        raise ProbeInputError("target_empty_or_control_char")
    if _contains_sensitive_marker(raw_url):
        raise ProbeInputError("target_contains_sensitive_marker")

    parsed = urlsplit(raw_url)
    if parsed.scheme.lower() != "https":
        raise ProbeInputError("target_non_https")
    if parsed.username or parsed.password or "@" in parsed.netloc:
        raise ProbeInputError("target_userinfo_present")
    if parsed.query or parsed.fragment:
        raise ProbeInputError("target_query_or_fragment_present")
    if parsed.port not in (None, 443):
        raise ProbeInputError("target_non_default_https_port")

    hostname = parsed.hostname or ""
    try:
        normalized_host = hostname.encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise ProbeInputError("target_host_invalid") from exc
    if not normalized_host or not _host_is_external(normalized_host):
        raise ProbeInputError("target_not_external_public_host")

    path = parsed.path or "/"
    if CONTROL_CHARS.search(path) or "\\" in path or "://" in path or ".." in path:
        raise ProbeInputError("target_path_unsafe")
    if _contains_sensitive_marker(path):
        raise ProbeInputError("target_path_contains_sensitive_marker")

    return SafeTarget(
        raw_url=raw_url,
        source=source,
        hostname=normalized_host,
        port=443,
        request_path=path,
    )


def host_hash_prefix(hostname: str) -> str:
    """host 只以 hash prefix 形式留档，避免 artifact 泄漏完整入口。"""

    return hashlib.sha256(hostname.encode("utf-8")).hexdigest()[:16]


def status_class(status_code: int | None) -> str:
    """HTTP 只保留类别，不保留完整状态说明、headers 或 body。"""

    if status_code is None:
        return "unavailable"
    return f"{int(status_code) // 100}xx"


def elapsed_bucket(elapsed_ms: int | None) -> str:
    """耗时只入桶，避免把底层网络路径细节误当 SLA。"""

    if elapsed_ms is None:
        return "unavailable"
    if elapsed_ms < 250:
        return "lt_250ms"
    if elapsed_ms < 1000:
        return "250ms_1s"
    if elapsed_ms < 3000:
        return "1s_3s"
    if elapsed_ms < 8000:
        return "3s_8s"
    return "gte_8s"


def content_length_bucket(content_length: int | None) -> str:
    """只根据 Content-Length 数值入桶，不持久化任何原始 header。"""

    if content_length is None:
        return "unknown"
    if content_length <= 0:
        return "zero"
    if content_length <= 1024:
        return "1b_1kb"
    if content_length <= 64 * 1024:
        return "1kb_64kb"
    if content_length <= 1024 * 1024:
        return "64kb_1mb"
    return "gt_1mb"


def _safe_int_header(value: str | None) -> int | None:
    """Content-Length 不可信；只接受非负整数，其他情况统一 unknown。"""

    if value is None:
        return None
    try:
        number = int(str(value).strip())
    except ValueError:
        return None
    return number if number >= 0 else None


def _classify_os_error(exc: OSError) -> str:
    """OSError 的 errno 只映射成安全类别，不把系统错误文本写入 artifact。"""

    if isinstance(exc, socket.gaierror):
        return "dns_failed"
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return "http_timeout"
    return "network_unavailable"


def single_https_request(target: SafeTarget, method: str, timeout_sec: float) -> HttpObservation:
    """执行一次 HTTPS 请求；不读取、不返回、不持久化响应体。"""

    started = time.monotonic()
    connection: http.client.HTTPSConnection | None = None
    try:
        context = ssl.create_default_context()
        connection = http.client.HTTPSConnection(
            target.hostname,
            target.port,
            timeout=timeout_sec,
            context=context,
        )
        # GET fallback 用 Range 限制服务端响应规模，但仍不保存 body。
        headers = {
            "Accept": "*/*",
            "Cache-Control": "no-cache",
            "User-Agent": "rober-o5-cdn-tls-probe/1",
        }
        if method == "GET":
            headers["Range"] = "bytes=0-0"
        connection.request(method, target.request_path, headers=headers)
        response = connection.getresponse()
        content_length = _safe_int_header(response.getheader("Content-Length"))
        # 不调用 read()，避免把 body 放进进程内 evidence 流程。
        response.close()
        elapsed_ms = int((time.monotonic() - started) * 1000)
        return HttpObservation(
            method=method,
            status_code=int(response.status),
            elapsed_ms=elapsed_ms,
            content_length=content_length,
            tls_handshake_observed=True,
            certificate_valid_for_host=True,
        )
    except ssl.SSLCertVerificationError as exc:
        raise ProbeRuntimeError(
            "tls_certificate_invalid",
            tls_handshake_observed=False,
            certificate_valid_for_host=False,
            elapsed_ms=int((time.monotonic() - started) * 1000),
        ) from exc
    except ssl.SSLError as exc:
        raise ProbeRuntimeError(
            "tls_failed",
            tls_handshake_observed=False,
            certificate_valid_for_host=False,
            elapsed_ms=int((time.monotonic() - started) * 1000),
        ) from exc
    except http.client.HTTPException as exc:
        raise ProbeRuntimeError(
            "http_protocol_failed",
            elapsed_ms=int((time.monotonic() - started) * 1000),
        ) from exc
    except OSError as exc:
        raise ProbeRuntimeError(
            _classify_os_error(exc),
            elapsed_ms=int((time.monotonic() - started) * 1000),
        ) from exc
    finally:
        if connection is not None:
            connection.close()


RequestOnce = Callable[[SafeTarget, str, float], HttpObservation]


def perform_https_probe(
    target: SafeTarget,
    *,
    timeout_sec: float,
    request_once: RequestOnce = single_https_request,
) -> HttpObservation:
    """优先 HEAD；仅在 HEAD 被明确拒绝时做 bounded GET fallback。"""

    head = request_once(target, "HEAD", timeout_sec)
    if int(head.status_code) not in {403, 405, 501}:
        return head

    # 某些 CDN 会拒绝 HEAD；GET 仍只看 status/length 桶，不保存 body。
    get = request_once(target, "GET", timeout_sec)
    return HttpObservation(
        method=get.method,
        status_code=get.status_code,
        elapsed_ms=get.elapsed_ms,
        content_length=get.content_length,
        tls_handshake_observed=get.tls_handshake_observed,
        certificate_valid_for_host=get.certificate_valid_for_host,
        head_rejected_get_fallback_attempted=True,
    )


def redaction_violations(value: Any) -> list[str]:
    """递归检查 artifact，确保没有 URL、secret、body、raw header 或本地绝对路径。"""

    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True)
    lowered = encoded.lower()
    violations: list[str] = []
    if FULL_URL_PATTERN.search(encoded):
        violations.append("full_url_present")
    if ABSOLUTE_PATH_PATTERN.search(encoded):
        violations.append("local_absolute_path_present")
    for marker in (
        "authorization",
        "bearer ",
        "set-cookie",
        "cookie:",
        "response_body",
        "raw_header",
        "raw_headers",
        "traceback",
        "access_key",
        "secret_key",
        "signature=",
    ):
        if marker in lowered:
            violations.append(f"unsafe_marker_{marker.strip().replace(' ', '_').replace(':', '')}")
    return sorted(set(violations))


def assert_artifact_safe(payload: dict[str, Any]) -> None:
    """写文件前做最终红线检查；失败时只暴露安全 reason code。"""

    violations = redaction_violations(payload)
    if violations:
        raise ProbeInputError("redaction_gate_failed")


def _base_payload(*, generated_at: str, target_source: str) -> dict[str, Any]:
    """所有路径共用固定 false 字段，防止成功路径和失败路径口径分叉。"""

    return {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "evidence_key": EVIDENCE_KEY,
        "proof_boundary": PROOF_BOUNDARY,
        "generated_at": generated_at,
        "target_source": target_source,
        "scheme": "https",
        "next_live_command": NEXT_LIVE_COMMAND,
        "fixed_false_invariants": list(FIXED_FALSE_INVARIANTS),
        "rejected_claims": list(REJECTED_CLAIMS),
        "delivery_success": False,
        "safe_to_control": False,
        "robot_control_executed": False,
        "route_execution_success": False,
        "hil_pass": False,
        "production_cloud_ready": False,
        "oss_object_upload": False,
        "cdn_origin_fetch": False,
        "production_db_queue": False,
        "production_worker_cutover": False,
        "four_g_sim": False,
        "real_phone_browser": False,
        "redaction_status": {
            "status": "pass",
            "url_omitted": True,
            "path_query_omitted": True,
            "sensitive_material_omitted": True,
            "payload_bytes_omitted": True,
            "header_lines_omitted": True,
            "exception_stack_omitted": True,
            "local_abs_path_omitted": True,
        },
    }


def blocked_payload(
    *,
    generated_at: str,
    target_source: str,
    reason: str | list[str],
    target_host_hash_prefix: str = "unavailable",
    probe_attempted: bool = False,
    external_request_attempted: bool = False,
    tls_handshake_observed: bool = False,
    certificate_valid_for_host: bool = False,
    method: str = "none",
    http_status_class: str = "unavailable",
    elapsed_ms_value: int | None = None,
    content_length_value: int | None = None,
) -> dict[str, Any]:
    """失败也必须写可复核 artifact，但只写安全 reason code。"""

    reasons = _reason_list(reason)
    payload = _base_payload(generated_at=generated_at, target_source=target_source)
    payload.update(
        {
            "cdn_tls_external_evidence_status": f"blocked_{reasons[0]}",
            "probe_attempted": bool(probe_attempted),
            "external_request_attempted": bool(external_request_attempted),
            "target_host_hash_prefix": target_host_hash_prefix,
            "tls_handshake_observed": bool(tls_handshake_observed),
            "certificate_valid_for_host": bool(certificate_valid_for_host),
            "http_method": method,
            "head_rejected_get_fallback_attempted": False,
            "http_status_class": http_status_class,
            "elapsed_ms_bucket": elapsed_bucket(elapsed_ms_value),
            "content_length_bucket": content_length_bucket(content_length_value),
            "blocked_reasons": reasons,
            "accepted_claim": "none",
        }
    )
    assert_artifact_safe(payload)
    return payload


def observation_payload(*, generated_at: str, target: SafeTarget, observation: HttpObservation) -> dict[str, Any]:
    """把网络观察结果收敛成 Product 可验收的 O5 CDN/TLS delta。"""

    http_class = status_class(observation.status_code)
    blocked_reasons: list[str] = []
    if not observation.tls_handshake_observed:
        blocked_reasons.append("tls_not_observed")
    if not observation.certificate_valid_for_host:
        blocked_reasons.append("certificate_not_valid_for_host")
    if http_class not in {"2xx", "3xx"}:
        blocked_reasons.append("http_status_not_success_class")

    status = "cdn_tls_external_evidence_observed" if not blocked_reasons else f"blocked_{blocked_reasons[0]}"
    payload = _base_payload(generated_at=generated_at, target_source=target.source)
    payload.update(
        {
            "cdn_tls_external_evidence_status": status,
            "probe_attempted": True,
            "external_request_attempted": True,
            "target_host_hash_prefix": host_hash_prefix(target.hostname),
            "tls_handshake_observed": bool(observation.tls_handshake_observed),
            "certificate_valid_for_host": bool(observation.certificate_valid_for_host),
            "http_method": observation.method,
            "head_rejected_get_fallback_attempted": bool(observation.head_rejected_get_fallback_attempted),
            "http_status_class": http_class,
            "elapsed_ms_bucket": elapsed_bucket(observation.elapsed_ms),
            "content_length_bucket": content_length_bucket(observation.content_length),
            "blocked_reasons": blocked_reasons,
            "accepted_claim": "o5_cdn_tls_external_evidence_delta" if not blocked_reasons else "none",
        }
    )
    assert_artifact_safe(payload)
    return payload


def build_probe_artifact(
    raw_target: str,
    target_source: str,
    *,
    generated_at: str | None = None,
    timeout_sec: float = 5.0,
    request_once: RequestOnce = single_https_request,
) -> dict[str, Any]:
    """主入口：unsafe input、网络失败和成功路径都返回 sanitized artifact。"""

    generated = generated_at or utc_now_iso()
    try:
        target = normalize_target(raw_target, target_source)
    except ProbeInputError as exc:
        return blocked_payload(
            generated_at=generated,
            target_source=target_source,
            reason=exc.reason_code,
            probe_attempted=False,
            external_request_attempted=False,
        )

    try:
        observation = perform_https_probe(target, timeout_sec=timeout_sec, request_once=request_once)
    except ProbeRuntimeError as exc:
        return blocked_payload(
            generated_at=generated,
            target_source=target_source,
            reason=exc.reason_code,
            target_host_hash_prefix=host_hash_prefix(target.hostname),
            probe_attempted=True,
            external_request_attempted=exc.external_request_attempted,
            tls_handshake_observed=exc.tls_handshake_observed,
            certificate_valid_for_host=exc.certificate_valid_for_host,
            elapsed_ms_value=exc.elapsed_ms,
        )

    return observation_payload(generated_at=generated, target=target, observation=observation)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """artifact 写入前已过 redaction gate；这里仅做稳定 JSON 格式化。"""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI 参数保持最小，避免把 probe 工具扩成生产控制入口。"""

    parser = argparse.ArgumentParser(description="Run sanitized O5 CDN/TLS external evidence probe.")
    parser.add_argument("--output", required=True, help="write sanitized JSON artifact to this path")
    parser.add_argument(
        "--timeout-sec",
        type=float,
        default=float(os.environ.get("ROBER_CDN_PROBE_TIMEOUT_SEC", "5.0")),
        help="bounded timeout per HTTPS request",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """运行 probe 并写 artifact；blocked 也返回 0，方便验收命令继续跑 redaction 检查。"""

    args = parse_args(argv)
    raw_target, target_source = choose_target()
    timeout_sec = max(1.0, min(float(args.timeout_sec), 15.0))
    artifact = build_probe_artifact(raw_target, target_source, timeout_sec=timeout_sec)
    write_json(Path(args.output), artifact)
    print(json.dumps(artifact, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
