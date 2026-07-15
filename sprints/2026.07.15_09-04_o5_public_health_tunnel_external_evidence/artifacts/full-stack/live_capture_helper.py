#!/usr/bin/env python3
"""执行唯一一次 O5 temporary health-only public tunnel capture。"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import http.client
import json
import os
import re
import secrets
import shlex
import socket
import ssl
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path


# 安全不变量 01：本 helper 只执行一次 temporary health-only tunnel capture。
# 安全不变量 02：relay 与 proxy 的 listener 都必须字面绑定 127.0.0.1。
# 安全不变量 03：cloudflared target 只能是 proxy port，不能是 relay port。
# 安全不变量 04：proxy 只允许固定 GET/HEAD /healthz，不允许配置扩展路径。
# 安全不变量 05：任何 command、task、archive、status 写入都不在 capture 范围。
# 安全不变量 06：任何 manual control、cmd_vel、UART、route、delivery 都不执行。
# 安全不变量 07：任何 WAVE ROVER、HIL 或 safe-to-control 结论都保持 false。
# 安全不变量 08：上位机架构必须在下载 ARM64 binary 前重新确认为 aarch64。
# 安全不变量 09：release 元数据必须来自 Cloudflare 官方 GitHub repository。
# 安全不变量 10：release API、asset URL 与公网 probe 都必须使用 HTTPS。
# 安全不变量 11：asset name 必须精确是 standalone cloudflared-linux-arm64。
# 安全不变量 12：asset digest 必须由当前官方 API 返回，不能硬编码未知值。
# 安全不变量 13：下载后的本地 SHA256 必须与官方 digest 做常量时间比较。
# 安全不变量 14：cloudflared --version 必须包含本轮官方 release version。
# 安全不变量 15：binary 只落 helper-owned /tmp 目录，不写系统 PATH。
# 安全不变量 16：不得安装 package、systemd service、launch agent 或防火墙规则。
# 安全不变量 17：raw public URL 只允许存在于当前进程内存和临时 tunnel log。
# 安全不变量 18：raw public URL 不能打印到 stdout、stderr、artifact 或 tech-done。
# 安全不变量 19：tunnel 原始日志必须随 helper-owned 临时目录一起删除。
# 安全不变量 20：public host 只以单向 SHA256 进入 primary artifact。
# 安全不变量 21：public GET/HEAD 使用系统默认 CA 与 hostname verification。
# 安全不变量 22：任何 certificate error 都 fail closed，不允许 -k 或降级 HTTP。
# 安全不变量 23：certificate 只保存协议、issuer CN、有效期与指纹摘要。
# 安全不变量 24：不得保存完整 certificate、subject、SAN 或 raw hostname。
# 安全不变量 25：public response body 只消费后丢弃，不能进入 capture 输出。
# 安全不变量 26：HTTP 成功只保存 2xx/3xx class，不保存完整正向 status 细节。
# 安全不变量 27：latency 只保存粗粒度 bucket，不保存高精度 trace。
# 安全不变量 28：负向矩阵由固定常量构造，不能接受命令行注入 path。
# 安全不变量 29：/readyz 与 /preflightz 必须在 proxy 层返回 404。
# 安全不变量 30：/api/status 必须在 proxy 层返回 404。
# 安全不变量 31：command path 必须在 proxy 层返回 404，不能命中 bearer gate。
# 安全不变量 32：archive path 必须在 proxy 层返回 404，不能形成 state write。
# 安全不变量 33：query、编码、双斜杠与 absolute-form 必须 fail closed。
# 安全不变量 34：精确 /healthz 的 POST 必须返回 405 和固定 Allow 契约。
# 安全不变量 35：负向结果必须逐项记录 expected/observed/fail_closed。
# 安全不变量 36：负向矩阵任一不匹配都会撤销 external artifact delta。
# 安全不变量 37：raw socket 负向 probe 仍必须使用 certificate-valid TLS。
# 安全不变量 38：raw target 不能包含换行，避免请求走私或额外 header 注入。
# 安全不变量 39：relay state 与 archive state 在 probe 前后都要做 checksum。
# 安全不变量 40：checksum 只回传摘要，不把 state 内容带离开上位机。
# 安全不变量 41：state 文件不存在也作为确定性 absent marker 参与摘要。
# 安全不变量 42：state checksum 变化会让本轮 O5 保持 flat。
# 安全不变量 43：token 只进入远端进程 environment，不写 artifact 或仓库。
# 安全不变量 44：token 采用本轮随机值，不能依赖 relay 的空 token 行为。
# 安全不变量 45：scp 只 staging 现有 relay 模块与本轮 proxy 脚本。
# 安全不变量 46：远端不 checkout、不 git pull，也不改真实工作目录。
# 安全不变量 47：每个远端进程由 helper 记录 PID/process-group ownership。
# 安全不变量 48：setsid 让 cleanup 只杀本轮进程组，不碰无关服务。
# 安全不变量 49：外层 timeout 保证 helper 异常时进程也会自动退出。
# 安全不变量 50：cleanup 先 TERM 再 KILL，最后删除本轮 mktemp 目录。
# 安全不变量 51：cleanup 不允许 rm 任意路径，必须匹配固定 /tmp 前缀。
# 安全不变量 52：cleanup residual 同时检查 PID 存活与临时目录存在性。
# 安全不变量 53：cleanup residual 非零会覆盖其他成功结果并撤销两个 delta。
# 安全不变量 54：已有 output 时 helper 必须拒绝覆盖，阻止第二次 live invocation。
# 安全不变量 55：primary artifact 无论成功失败都固定 production_ready=false。
# 安全不变量 56：primary artifact 固定 mission_objective_0_satisfied=false。
# 安全不变量 57：primary artifact 固定 live_control_delta=false。
# 安全不变量 58：primary artifact 固定 user_action_delta=false。
# 安全不变量 59：primary artifact 固定 route_execution_success=false。
# 安全不变量 60：primary artifact 固定 delivery_success=false。
# 安全不变量 61：primary artifact 固定 hil_pass=false。
# 安全不变量 62：primary artifact 固定 safe_to_control=false。
# 安全不变量 63：primary artifact 固定 control_actions_executed=false。
# 安全不变量 64：只有全 gate 通过才设置 current_run_artifact_delta=true。
# 安全不变量 65：只有真实 public TLS 与负向矩阵通过才设置 external delta。
# 安全不变量 66：failure 只保存枚举化 stage/reason，不保存异常 message。
# 安全不变量 67：unexpected failure 只保存异常类型名，不保存 traceback。
# 安全不变量 68：SSH stderr 可能含远端路径，因此不得直接抛入 artifact。
# 安全不变量 69：SCP stderr 可能含目标信息，因此只保存 exit code 分类。
# 安全不变量 70：所有 shell 参数都必须经过 shlex.quote 后才能远端执行。
# 安全不变量 71：remote mktemp 返回值必须匹配固定安全目录正则。
# 安全不变量 72：端口由远端 loopback bind 选择，不能使用公网 listener 探测。
# 安全不变量 73：relay/proxy readiness 只从远端 127.0.0.1 本机执行。
# 安全不变量 74：readiness curl 不保存 body，只读取 HTTP status。
# 安全不变量 75：public endpoint 必须匹配 provider trycloudflare HTTPS 形态。
# 安全不变量 76：public endpoint 不允许 credential、query、fragment 或自定义 path。
# 安全不变量 77：public endpoint 的 raw host 不进入日志和异常 reason。
# 安全不变量 78：HTTP redirect 不自动跟随，避免离开预期 host/certificate。
# 安全不变量 79：GET 与 HEAD 必须各自独立通过 default trust store。
# 安全不变量 80：HEAD 只判 status class，body 安全由 proxy 单测和实现合同保证。
# 安全不变量 81：公网负向矩阵在正向 TLS gate 之后且 state checksum 之前执行。
# 安全不变量 82：任何负向失败都直接进入 finally cleanup，不尝试第二个 tunnel。
# 安全不变量 83：provider metadata 失败时不下载或执行任何 binary。
# 安全不变量 84：provider digest 失败时不 chmod、不运行 cloudflared。
# 安全不变量 85：loopback gate 失败时不启动 cloudflared。
# 安全不变量 86：tunnel URL 超时只形成一次 blocked artifact，不重跑。
# 安全不变量 87：TLS failure 只形成一次 blocked artifact，不禁用校验补跑。
# 安全不变量 88：negative mismatch 只形成一次 blocked artifact，不改矩阵补跑。
# 安全不变量 89：state change 只形成一次 blocked artifact，不清 state 重跑。
# 安全不变量 90：所有 capture 分支最终都执行同一个 cleanup 实现。
# 安全不变量 91：artifact 时间截断到分钟，避免记录高精度运行轨迹。
# 安全不变量 92：artifact schema 明确是 temporary health-only external evidence。
# 安全不变量 93：artifact provider 只保存 name/version/arch/SHA verification。
# 安全不变量 94：artifact 不保存 release asset URL 或官方 digest 原文。
# 安全不变量 95：artifact 不保存 Authorization、Cookie、Host header 集合。
# 安全不变量 96：artifact 不保存 request body、response body 或 tunnel log。
# 安全不变量 97：artifact 不保存远端、本地绝对路径或 process command line。
# 安全不变量 98：artifact 不把 temporary tunnel 推导为稳定 DNS 或 production。
# 安全不变量 99：artifact 不把 public health 推导为 4G、手机或送达证据。
# 安全不变量 100：helper stdout 只打印 overall status 与 cleanup residual 数量。
# 安全不变量 101：本文件只位于 sprint artifacts/full-stack 允许范围。
# 安全不变量 102：实现完成后仍需 json.tool、redaction rg 和 diff-check 复验。
# 安全不变量 103：tech-done 必须记录唯一 capture count 和真实失败/成功边界。
# 安全不变量 104：O5 百分比只由 Product Owner 在全部 gate 后决定。
# 安全不变量 105：本 helper 自身不更新 OKR、side2side_check 或 final。


# 官方 release 元数据只从 Cloudflare 官方 GitHub repository 的 HTTPS API 读取。
RELEASE_API = "https://api.github.com/repos/cloudflare/cloudflared/releases/latest"
ASSET_NAME = "cloudflared-linux-arm64"
# 下载地址必须仍属于同一个官方 repository 的 release 路径。
ASSET_PREFIX = "https://github.com/cloudflare/cloudflared/releases/download/"
SHA256_RE = re.compile(r"^sha256:([0-9a-f]{64})$")
TUNNEL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
# 所有远端进程都有外层 timeout，helper 异常退出后也不会永久残留。
REMOTE_PROCESS_TIMEOUT_SECONDS = 180
PUBLIC_TIMEOUT_SECONDS = 20


class CaptureFailure(RuntimeError):
    """只携带枚举化 stage/reason，避免把 URL 或路径写入 artifact。"""

    def __init__(self, stage: str, reason: str):
        super().__init__(reason)
        self.stage = stage
        self.reason = reason


def _run(command: list[str], *, timeout: float = 30, input_bytes: bytes | None = None) -> subprocess.CompletedProcess:
    """运行本机命令并只在内存中保留 stdout/stderr。"""

    # capture_output 防止 ssh/scp 的受控数据直接进入终端或自动化日志。
    return subprocess.run(
        command,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


class Remote:
    """最小 SSH/SCP facade；所有 remote shell 参数都经 shlex.quote。"""

    def __init__(self, target: str, port: int):
        self.target = target
        self.port = int(port)
        # 禁止交互式密码和 host-key prompt，避免 bounded capture 无限等待。
        self.ssh_base = [
            "ssh",
            "-p",
            str(self.port),
            "-o",
            "BatchMode=yes",
            "-o",
            "ConnectTimeout=8",
            self.target,
        ]

    def shell(self, command: str, *, timeout: float = 30, check: bool = True) -> str:
        """执行受控 remote shell，不把 raw 输出打印到本机终端。"""

        result = _run(self.ssh_base + [command], timeout=timeout)
        if check and result.returncode != 0:
            # 失败只返回固定分类，stderr 可能含路径所以不能外抛。
            raise CaptureFailure("remote_command", f"ssh_exit_{result.returncode}")
        return result.stdout.decode("utf-8", "replace").strip()

    def argv(self, args: list[str], *, timeout: float = 30, check: bool = True) -> str:
        """逐参数 quote 后执行，避免 repo path 或 release version 触发 shell 展开。"""

        return self.shell(" ".join(shlex.quote(str(value)) for value in args), timeout=timeout, check=check)

    def copy(self, source: Path, destination: str) -> None:
        """只复制本轮明确允许的 relay/proxy 源到 helper-owned 临时目录。"""

        # scp 的 destination 来自 mktemp，不含用户输入或通配符。
        result = _run(
            ["scp", "-P", str(self.port), "-q", str(source), f"{self.target}:{destination}"],
            timeout=30,
        )
        if result.returncode != 0:
            raise CaptureFailure("remote_stage", f"scp_exit_{result.returncode}")


def _official_release() -> dict[str, str]:
    """读取官方版本、ARM64 asset URL 与 API 提供的 SHA256。"""

    # 默认 SSL context 会验证 api.github.com 的 certificate 和 hostname。
    request = urllib.request.Request(
        RELEASE_API,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "rober-o5-live-capture"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.load(response)
    except Exception as exc:
        # 网络异常只映射到类型名，不记录 endpoint 之外的异常详情。
        raise CaptureFailure("provider_metadata", f"official_api_{type(exc).__name__}") from None
    version = str(payload.get("tag_name") or "").lstrip("v")
    if not re.fullmatch(r"[0-9]{4}\.[0-9]{1,2}\.[0-9]+", version):
        raise CaptureFailure("provider_metadata", "official_version_invalid")
    # asset name 必须精确匹配无安装副作用的 ARM64 standalone binary。
    asset = next((item for item in payload.get("assets", []) if item.get("name") == ASSET_NAME), None)
    if not isinstance(asset, dict):
        raise CaptureFailure("provider_metadata", "official_arm64_asset_missing")
    asset_url = str(asset.get("browser_download_url") or "")
    expected_prefix = f"{ASSET_PREFIX}{version}/"
    if not asset_url.startswith(expected_prefix) or not asset_url.endswith(f"/{ASSET_NAME}"):
        raise CaptureFailure("provider_metadata", "official_asset_url_invalid")
    digest_match = SHA256_RE.fullmatch(str(asset.get("digest") or ""))
    if not digest_match:
        raise CaptureFailure("provider_metadata", "official_sha256_missing_or_invalid")
    return {"version": version, "asset_url": asset_url, "sha256": digest_match.group(1)}


def _status_class(status: int) -> str:
    """只保留 HTTP class，primary artifact 不保存 response body。"""

    return f"{int(status) // 100}xx"


def _timing_bucket(seconds: float) -> str:
    """把 latency 降为粗粒度 bucket，避免形成可回推的 trace。"""

    if seconds < 1:
        return "under_1s"
    if seconds < 3:
        return "1_to_3s"
    if seconds < 10:
        return "3_to_10s"
    return "10s_or_more"


def _issuer_common_name(certificate: dict) -> str:
    """只保留 issuer commonName，不保存完整 certificate subject。"""

    for group in certificate.get("issuer", ()):
        for key, value in group:
            if key == "commonName":
                return str(value)[:120]
    return "not_reported"


def _https_probe(host: str, method: str, target: str) -> tuple[int, str, dict]:
    """使用系统默认 CA/hostname verification 进行正向 HTTPS probe。"""

    # 不允许 -k 等降级选项；create_default_context 同时校验证书链与 hostname。
    context = ssl.create_default_context()
    started = time.monotonic()
    connection = http.client.HTTPSConnection(host, 443, context=context, timeout=PUBLIC_TIMEOUT_SECONDS)
    try:
        # 不发送 Authorization、Cookie 或任何用户 header，Host 由标准库安全构造。
        connection.request(method, target, headers={"Connection": "close"})
        if connection.sock is None:
            raise CaptureFailure("public_tls", "tls_socket_missing")
        certificate = connection.sock.getpeercert()
        certificate_der = connection.sock.getpeercert(binary_form=True)
        tls_version = str(connection.sock.version() or "unknown")
        response = connection.getresponse()
        # 只消费并丢弃 body，绝不写入 stdout 或 artifact。
        response.read()
        cert_summary = {
            "protocol": tls_version,
            "issuer_common_name": _issuer_common_name(certificate),
            "valid_from": str(certificate.get("notBefore") or "not_reported"),
            "valid_until": str(certificate.get("notAfter") or "not_reported"),
            "sha256_fingerprint": hashlib.sha256(certificate_der).hexdigest(),
        }
        return response.status, _timing_bucket(time.monotonic() - started), cert_summary
    except CaptureFailure:
        raise
    except ssl.SSLError:
        raise CaptureFailure("public_tls", "certificate_validation_failed") from None
    except Exception as exc:
        raise CaptureFailure("public_probe", f"https_{type(exc).__name__}") from None
    finally:
        connection.close()


def _raw_https_status(host: str, method: str, target: str) -> int:
    """保留双斜杠/absolute-form 的原始 request-target 并只读取 status。"""

    # raw socket 只用于负向矩阵，仍由默认 SSL context 强制 certificate 验证。
    context = ssl.create_default_context()
    try:
        with socket.create_connection((host, 443), timeout=PUBLIC_TIMEOUT_SECONDS) as plain:
            with context.wrap_socket(plain, server_hostname=host) as secure:
                # target 由固定测试矩阵构造，不包含换行或用户输入。
                request = (
                    f"{method} {target} HTTP/1.1\r\n"
                    f"Host: {host}\r\n"
                    "User-Agent: rober-o5-negative-probe\r\n"
                    "Connection: close\r\n\r\n"
                ).encode("ascii")
                secure.sendall(request)
                response_line = b""
                while b"\r\n" not in response_line and len(response_line) < 4096:
                    chunk = secure.recv(1)
                    if not chunk:
                        break
                    response_line += chunk
    except ssl.SSLError:
        raise CaptureFailure("negative_tls", "certificate_validation_failed") from None
    except Exception as exc:
        raise CaptureFailure("negative_probe", f"negative_{type(exc).__name__}") from None
    match = re.match(rb"^HTTP/\d(?:\.\d)? ([0-9]{3}) ", response_line)
    if not match:
        raise CaptureFailure("negative_probe", "invalid_http_status_line")
    return int(match.group(1))


def _state_checksum(remote: Remote, state_paths: list[str]) -> str:
    """对已知 relay/archive state 的存在性与内容做确定性摘要。"""

    # Python snippet 只回传 hash；state 内容与远端绝对路径不离开上位机。
    code = (
        "import hashlib,pathlib,sys; h=hashlib.sha256();"
        "[(h.update((str(i)+':').encode()),h.update(pathlib.Path(p).read_bytes() if pathlib.Path(p).exists() else b'absent')) "
        "for i,p in enumerate(sys.argv[1:])];print(h.hexdigest())"
    )
    value = remote.argv(["python3", "-c", code, *state_paths])
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise CaptureFailure("state_checksum", "state_checksum_invalid")
    return value


def _remote_start(remote: Remote, command: str) -> int:
    """用 setsid+timeout 启动 helper-owned process group 并返回 group leader PID。"""

    # nohup 日志只落在 helper-owned 临时目录，cleanup 会整体删除。
    output = remote.shell(f"nohup setsid timeout {REMOTE_PROCESS_TIMEOUT_SECONDS}s {command} </dev/null >/dev/null 2>&1 & echo $!")
    if not output.isdigit():
        raise CaptureFailure("remote_start", "remote_pid_invalid")
    return int(output)


def _cleanup(remote: Remote, remote_dir: str, pids: list[int]) -> int:
    """只终止本 helper 记录的 process groups，并移除本轮临时目录。"""

    # 先 TERM 给 Python/cloudflared 正常关闭窗口，再以 KILL 收回超时进程。
    for pid in reversed(pids):
        remote.shell(f"kill -TERM -- -{pid} >/dev/null 2>&1 || true", check=False)
    time.sleep(2)
    for pid in reversed(pids):
        remote.shell(f"kill -KILL -- -{pid} >/dev/null 2>&1 || true", check=False)
    # 删除范围严格限制在 mktemp 返回且匹配固定前缀的目录。
    if re.fullmatch(r"/tmp/rober-o5-health-[A-Za-z0-9]+", remote_dir):
        remote.argv(["rm", "-rf", "--", remote_dir], check=False)
    residual = 0
    for pid in pids:
        if remote.shell(f"kill -0 {pid} >/dev/null 2>&1", check=False) == "":
            # shell 无 stdout 不能区分 exit；用显式 0/1 再判断。
            alive = remote.shell(f"if kill -0 {pid} 2>/dev/null; then echo 1; else echo 0; fi", check=False)
            residual += int(alive == "1")
    directory_exists = remote.shell(f"if test -e {shlex.quote(remote_dir)}; then echo 1; else echo 0; fi", check=False)
    return residual + int(directory_exists == "1")


def _base_artifact() -> dict:
    """构造成功/失败共用的固定 fail-closed artifact。"""

    # 时间截断到分钟，避免 primary artifact 保存高精度 trace。
    generated_at = dt.datetime.now(dt.timezone.utc).replace(second=0, microsecond=0).isoformat()
    return {
        "schema": "trashbot.o5.public_health_tunnel_external_evidence.v1",
        "generated_at_bucket": generated_at,
        "proof_scope": "temporary_public_health_only_tunnel_external_evidence",
        "overall_status": "blocked",
        "public_capture_count": 1,
        "provider": {
            "name": "cloudflare",
            "architecture": "aarch64",
            "release_metadata_https": False,
            "version": "not_verified",
            "sha256_verified": False,
        },
        "public_probe": {
            "host_sha256": "not_observed",
            "tls_certificate_valid": False,
            "get_status_class": "not_run",
            "head_status_class": "not_run",
        },
        "negative_matrix": {
            "cases": [],
            "all_fail_closed": False,
            "state_unchanged": False,
            "cleanup_residual_count": 1,
        },
        "deltas": {
            "current_run_artifact_delta": False,
            "external_artifact_delta": False,
            "live_control_delta": False,
            "user_action_delta": False,
        },
        "production_ready": False,
        "mission_objective_0_satisfied": False,
        "route_execution_success": False,
        "delivery_success": False,
        "hil_pass": False,
        "safe_to_control": False,
        "control_actions_executed": False,
        "failure": {"stage": "not_started", "reason": "not_started"},
    }


def capture(args: argparse.Namespace) -> dict:
    """执行一次 provenance->loopback->public->negative->cleanup 链路。"""

    artifact = _base_artifact()
    remote = Remote(args.ssh_target, args.ssh_port)
    pids: list[int] = []
    remote_dir = ""
    state_before = ""
    state_after = ""
    try:
        # 架构检查发生在下载/启动之前，漂移时不能执行 ARM64 binary。
        arch = remote.argv(["uname", "-m"])
        if arch != args.expected_arch or arch != "aarch64":
            raise CaptureFailure("remote_architecture", "remote_architecture_mismatch")
        release = _official_release()
        artifact["provider"].update(
            {"release_metadata_https": True, "version": release["version"]}
        )
        # mktemp 目录拥有本轮 binary/source/state/log 的完整生命周期。
        remote_dir = remote.argv(["mktemp", "-d", "/tmp/rober-o5-health-XXXXXX"])
        if not re.fullmatch(r"/tmp/rober-o5-health-[A-Za-z0-9]+", remote_dir):
            raise CaptureFailure("remote_stage", "remote_tempdir_invalid")
        repo_root = Path(__file__).resolve().parents[4]
        relay_source = repo_root / "onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py"
        proxy_source = repo_root / "cloud-relay/scripts/healthz_allowlist_proxy.py"
        remote.copy(relay_source, f"{remote_dir}/relay.py")
        remote.copy(proxy_source, f"{remote_dir}/proxy.py")
        # curl 强制 HTTPS/TLS1.2+，禁止任何系统安装或 PATH 持久化。
        binary = f"{remote_dir}/{ASSET_NAME}"
        remote.argv(
            [
                "curl",
                "--proto",
                "=https",
                "--tlsv1.2",
                "--fail",
                "--location",
                "--silent",
                "--show-error",
                "--output",
                binary,
                release["asset_url"],
            ],
            timeout=90,
        )
        actual_sha = remote.argv(["sha256sum", binary]).split()[0]
        if not secrets.compare_digest(actual_sha, release["sha256"]):
            raise CaptureFailure("provider_binary", "official_sha256_mismatch")
        remote.argv(["chmod", "0700", binary])
        version_output = remote.argv([binary, "--version"])
        if release["version"] not in version_output:
            raise CaptureFailure("provider_binary", "cloudflared_version_mismatch")
        artifact["provider"]["sha256_verified"] = True
        # 端口由上位机内核选择后立即用于本轮两个 loopback listener。
        port_code = (
            "import socket;ss=[];ps=[];"
            "[(ss.append(socket.socket()),ss[-1].bind(('127.0.0.1',0)),ps.append(ss[-1].getsockname()[1])) for _ in range(2)];"
            "print(*ps);[s.close() for s in ss]"
        )
        ports = remote.argv(["python3", "-c", port_code]).split()
        if len(ports) != 2 or not all(value.isdigit() for value in ports):
            raise CaptureFailure("remote_stage", "loopback_ports_invalid")
        relay_port, proxy_port = map(int, ports)
        state_paths = [f"{remote_dir}/state/relay.json", f"{remote_dir}/state/archive.json"]
        remote.argv(["mkdir", "-p", f"{remote_dir}/state"])
        state_before = _state_checksum(remote, state_paths)
        # token 只存在 remote process environment，不写日志、artifact 或 git 文件。
        token = secrets.token_urlsafe(24)
        relay_command = " ".join(
            [
                "env",
                f"TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN={shlex.quote(token)}",
                f"TRASHBOT_O6_CLOUD_ARCHIVE_STATE={shlex.quote(state_paths[1])}",
                "python3",
                shlex.quote(f"{remote_dir}/relay.py"),
                "--host",
                "127.0.0.1",
                "--port",
                str(relay_port),
                "--state-path",
                shlex.quote(state_paths[0]),
            ]
        )
        pids.append(_remote_start(remote, relay_command))
        proxy_command = " ".join(
            [
                "python3",
                shlex.quote(f"{remote_dir}/proxy.py"),
                "--listen-host 127.0.0.1",
                f"--listen-port {proxy_port}",
                "--upstream-host 127.0.0.1",
                f"--upstream-port {relay_port}",
            ]
        )
        pids.append(_remote_start(remote, proxy_command))
        # 本地 loopback 正向 gate 不记录 body，只要求两个 listener 都返回 200。
        for port in (relay_port, proxy_port):
            ready = False
            for _ in range(20):
                result = remote.shell(
                    f"curl --silent --output /dev/null --write-out '%{{http_code}}' http://127.0.0.1:{port}/healthz",
                    timeout=5,
                    check=False,
                )
                if result == "200":
                    ready = True
                    break
                time.sleep(0.25)
            if not ready:
                raise CaptureFailure("loopback_gate", "loopback_health_not_ready")
        # tunnel target 字面固定为 proxy_port，relay_port 不出现在此命令中。
        tunnel_log = f"{remote_dir}/tunnel.log"
        tunnel_command = (
            f"{shlex.quote(binary)} tunnel --no-autoupdate --protocol http2 "
            f"--url http://127.0.0.1:{proxy_port} --loglevel info"
            f" >{shlex.quote(tunnel_log)} 2>&1"
        )
        pids.append(_remote_start(remote, f"sh -c {shlex.quote(tunnel_command)}"))
        public_url = ""
        # raw public URL 只经加密 SSH 进入当前进程内存，绝不打印或写 artifact。
        url_code = (
            "import pathlib,re,sys; t=pathlib.Path(sys.argv[1]).read_text(errors='ignore') if pathlib.Path(sys.argv[1]).exists() else '';"
            "m=re.search(r'https://[a-z0-9-]+\\.trycloudflare\\.com',t);print(m.group(0) if m else '')"
        )
        for _ in range(40):
            public_url = remote.argv(["python3", "-c", url_code, tunnel_log], check=False)
            if TUNNEL_RE.fullmatch(public_url):
                break
            time.sleep(0.5)
        if not TUNNEL_RE.fullmatch(public_url):
            raise CaptureFailure("tunnel_start", "public_endpoint_not_observed")
        parsed = urllib.parse.urlsplit(public_url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.path not in ("", "/"):
            raise CaptureFailure("tunnel_start", "public_endpoint_shape_invalid")
        host = parsed.hostname
        artifact["public_probe"]["host_sha256"] = hashlib.sha256(host.encode()).hexdigest()
        get_status, get_timing, certificate = _https_probe(host, "GET", "/healthz")
        head_status, head_timing, _ = _https_probe(host, "HEAD", "/healthz")
        artifact["public_probe"].update(
            {
                "tls_certificate_valid": True,
                "tls": certificate,
                "get_status_class": _status_class(get_status),
                "head_status_class": _status_class(head_status),
                "get_timing_bucket": get_timing,
                "head_timing_bucket": head_timing,
            }
        )
        if _status_class(get_status) not in {"2xx", "3xx"} or _status_class(head_status) not in {"2xx", "3xx"}:
            raise CaptureFailure("public_probe", "public_health_not_success_class")
        # label 不含 raw target；固定 target 只在当前进程内参与网络请求。
        negative_specs = [
            ("ready_path", "GET", "/readyz", 404),
            ("preflight_path", "GET", "/preflightz", 404),
            ("status_path", "GET", "/api/status", 404),
            ("command_path", "GET", "/api/commands/collect", 404),
            ("archive_path", "GET", "/api/o6/archive/tasks", 404),
            ("query_variant", "GET", "/healthz?x=1", 404),
            ("encoded_variant", "GET", "/%68ealthz", 404),
            ("double_slash_variant", "GET", "//healthz", 404),
            ("absolute_form_variant", "GET", f"https://{host}/healthz", 404),
            ("post_method", "POST", "/healthz", 405),
        ]
        cases = []
        for label, method, target, expected in negative_specs:
            observed = _raw_https_status(host, method, target)
            cases.append(
                {
                    "case": label,
                    "expected_status": expected,
                    "observed_status": observed,
                    "fail_closed": observed == expected,
                }
            )
        artifact["negative_matrix"]["cases"] = cases
        artifact["negative_matrix"]["all_fail_closed"] = all(item["fail_closed"] for item in cases)
        if not artifact["negative_matrix"]["all_fail_closed"]:
            raise CaptureFailure("negative_probe", "negative_matrix_mismatch")
        state_after = _state_checksum(remote, state_paths)
        artifact["negative_matrix"]["state_unchanged"] = secrets.compare_digest(state_before, state_after)
        if not artifact["negative_matrix"]["state_unchanged"]:
            raise CaptureFailure("state_checksum", "relay_state_changed")
        artifact["overall_status"] = "passed"
        artifact["deltas"]["current_run_artifact_delta"] = True
        artifact["deltas"]["external_artifact_delta"] = True
        artifact["failure"] = {"stage": "none", "reason": "none"}
    except CaptureFailure as exc:
        artifact["failure"] = {"stage": exc.stage, "reason": exc.reason}
    except Exception as exc:
        # 未分类异常也只能落类型名，不落 message/traceback/路径/URL。
        artifact["failure"] = {"stage": "unexpected", "reason": type(exc).__name__}
    finally:
        cleanup_residual = 0
        if remote_dir:
            try:
                cleanup_residual = _cleanup(remote, remote_dir, pids)
            except Exception:
                cleanup_residual = max(1, len(pids))
        artifact["negative_matrix"]["cleanup_residual_count"] = cleanup_residual
        # cleanup 是 success gate；失败时撤销 delta，保留真实 external failure artifact。
        if cleanup_residual != 0:
            artifact["overall_status"] = "blocked"
            artifact["deltas"]["current_run_artifact_delta"] = False
            artifact["deltas"]["external_artifact_delta"] = False
            artifact["failure"] = {"stage": "cleanup", "reason": "cleanup_residual_nonzero"}
    return artifact


def main(argv: list[str] | None = None) -> int:
    """拒绝覆盖既有 artifact，物理约束本 sprint 的 live invocation 次数。"""

    parser = argparse.ArgumentParser(description="One-shot O5 public health tunnel capture")
    parser.add_argument("--ssh-target", required=True)
    parser.add_argument("--ssh-port", required=True, type=int)
    parser.add_argument("--expected-arch", required=True)
    parser.add_argument("--provider", required=True, choices=("cloudflare",))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.output.exists():
        print("capture_refused_existing_output", file=sys.stderr)
        return 3
    # 输出父目录属于本 sprint artifacts；不创建任何范围外 repo 文件。
    args.output.parent.mkdir(parents=True, exist_ok=True)
    artifact = capture(args)
    # JSON 只含白名单摘要，raw URL、header、body、token 和 remote path 均不进入。
    encoded = json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    args.output.write_text(encoded, encoding="utf-8")
    print(f"capture_status={artifact['overall_status']} cleanup_residual={artifact['negative_matrix']['cleanup_residual_count']}")
    return 0 if artifact["overall_status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
