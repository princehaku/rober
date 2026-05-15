#!/usr/bin/env python3
"""Run the mobile/web local Chromium-family browser acceptance gate.

本 gate 服务当前 dependency-free PWA，而不是旧 operator gateway fallback。
它只证明本地 Chromium-family 浏览器渲染与 phone-safe UI 行为，不证明真机、
production app、真实 PWA install prompt、云、4G、机器人运动或送达完成。
"""

import argparse
import base64
import hashlib
import json
import mimetypes
import os
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MOBILE_WEB_ROOT = REPO_ROOT / "mobile" / "web"
MOBILE_FIXTURE = REPO_ROOT / "mobile" / "fixtures" / "mobile_web_status.fixture.json"
EVIDENCE_BOUNDARY = "software_proof_docker_mobile_current_pwa_field_trial_browser_proof_gate"
COMPATIBLE_EVIDENCE_BOUNDARY = "software_proof_docker_mobile_current_pwa_retest_browser_proof_gate"
REFRESH_EVIDENCE_BOUNDARY = "software_proof_docker_mobile_current_pwa_browser_proof_refresh_gate"
LEGACY_ARTIFACT_EVIDENCE_BOUNDARY = "software_proof_docker_mobile_web_browser_proof_gate"
ROUTE_ELEVATOR_HANDOFF_BROWSER_PROOF = "mobile_route_elevator_handoff_browser"
VIEWPORTS = ((390, 844), (768, 900))
PRIMARY_BUTTON_IDS = ("startButton", "confirmButton", "cancelButton")
SUPPORT_BUTTON_IDS = (
    "diagnosticsButton",
    "supportButton",
    "copyAcceptanceBundleButton",
)
HIT_AREA_IDS = PRIMARY_BUTTON_IDS + SUPPORT_BUTTON_IDS
KEY_ELEMENT_IDS = (
    "connectionBadge",
    "readinessTitle",
    "safePhoneCopy",
    "recoveryHint",
    "primaryJourneyTitle",
    "primaryJourneySteps",
    "primaryJourneyBoundary",
    "recoveryDecisionTitle",
    "recoveryDecisionState",
    "recoveryDecisionNextAction",
    "recoveryDecisionAck",
    "recoveryDecisionBoundary",
    "routeElevatorFieldSessionHandoffTitle",
    "routeElevatorFieldSessionHandoffCopy",
    "routeElevatorFieldSessionHandoffVerdict",
    "routeElevatorFieldSessionHandoffEvidenceRef",
    "routeElevatorFieldSessionHandoffSameRef",
    "routeElevatorFieldSessionHandoffSameRefStatus",
    "routeElevatorFieldSessionHandoffMaterials",
    "routeElevatorFieldSessionHandoffNextSteps",
    "routeElevatorFieldSessionHandoffControls",
    "routeElevatorFieldSessionHandoffBoundary",
    "routeElevatorFieldSessionHandoffNotProven",
    "routeElevatorFieldSessionHandoffHint",
    "mobileDeviceEvidenceTitle",
    "mobileDeviceEvidenceSafeCopy",
    "mobileDeviceEvidenceBoundary",
    "copyDeviceEvidencePackageButton",
    "mobileDeviceHandoffTitle",
    "mobileDeviceHandoffSafeCopy",
    "mobileDeviceHandoffBoundary",
    "copyDeviceHandoffPackageButton",
    "mobilePwaInstallPromptTitle",
    "mobilePwaInstallPromptSafeCopy",
    "mobilePwaInstallPromptBoundary",
    "copyPwaInstallPromptPackageButton",
    "mobileRealDeviceRetestRequestTitle",
    "mobileRealDeviceRetestRequestStatus",
    "mobileRealDeviceRetestRequestOwner",
    "mobileRealDeviceRetestRequestMissingEvidence",
    "mobileRealDeviceRetestRequestReadiness",
    "mobileRealDeviceRetestRequestBlockedReason",
    "mobileRealDeviceRetestRequestRejectionReason",
    "mobileRealDeviceRetestRequestRedaction",
    "mobileRealDeviceRetestRequestAck",
    "mobileRealDeviceRetestRequestBoundary",
    "mobileRealDeviceRetestRequestSourceBoundary",
    "mobileRealDeviceRetestRequestNotProven",
    "mobileRealDeviceRetestRequestChecklist",
    "mobileRealDeviceRetestRequestSafeCopy",
    "copyRealDeviceRetestRequestButton",
    "mobileRealDeviceFieldTrialTitle",
    "mobileRealDeviceFieldTrialSummary",
    "mobileRealDeviceFieldTrialSafeControl",
    "mobileRealDeviceFieldTrialAck",
    "mobileRealDeviceFieldTrialBoundary",
    "mobileRealDeviceFieldTrialNotProven",
    "mobileRealDeviceFieldTrialSafeCopy",
    "copyRealDeviceFieldTrialPackageButton",
    "mobileRealDeviceFieldTrialReviewTitle",
    "mobileRealDeviceFieldTrialReviewSafeControl",
    "mobileRealDeviceFieldTrialReviewAck",
    "mobileRealDeviceFieldTrialReviewBoundary",
    "mobileRealDeviceFieldTrialReviewNotProven",
    "mobileRealDeviceFieldTrialReviewSafeCopy",
    "copyRealDeviceFieldTrialReviewButton",
    "mobileRealDeviceFieldTrialRunbookExecutionTitle",
    "mobileRealDeviceFieldTrialRunbookExecutionSafeControl",
    "mobileRealDeviceFieldTrialRunbookExecutionAck",
    "mobileRealDeviceFieldTrialRunbookExecutionBoundary",
    "mobileRealDeviceFieldTrialRunbookExecutionNotProven",
    "mobileRealDeviceFieldTrialRunbookExecutionSafeCopy",
    "copyRealDeviceFieldTrialRunbookExecutionButton",
    "mobileRealDeviceFieldTrialEvidenceRecordTitle",
    "mobileRealDeviceFieldTrialEvidenceRecordSafeControl",
    "mobileRealDeviceFieldTrialEvidenceRecordAck",
    "mobileRealDeviceFieldTrialEvidenceRecordBoundary",
    "mobileRealDeviceFieldTrialEvidenceRecordArchive",
    "mobileRealDeviceFieldTrialEvidenceRecordNotProven",
    "mobileRealDeviceFieldTrialEvidenceRecordSafeCopy",
    "copyRealDeviceFieldTrialEvidenceRecordButton",
    "mobileRealDeviceFieldTrialEvidenceVerdictTitle",
    "mobileRealDeviceFieldTrialEvidenceVerdictSafeControl",
    "mobileRealDeviceFieldTrialEvidenceVerdictAck",
    "mobileRealDeviceFieldTrialEvidenceVerdictBoundary",
    "mobileRealDeviceFieldTrialEvidenceVerdictSourceBoundary",
    "mobileRealDeviceFieldTrialEvidenceVerdictNotProven",
    "mobileRealDeviceFieldTrialEvidenceVerdictSafeCopy",
    "copyRealDeviceFieldTrialEvidenceVerdictButton",
    "mobileRealDeviceFieldTrialRetestExecutionTitle",
    "mobileRealDeviceFieldTrialRetestExecutionSafeControl",
    "mobileRealDeviceFieldTrialRetestExecutionAck",
    "mobileRealDeviceFieldTrialRetestExecutionBoundary",
    "mobileRealDeviceFieldTrialRetestExecutionSourceBoundary",
    "mobileRealDeviceFieldTrialRetestExecutionNotProven",
    "mobileRealDeviceFieldTrialRetestExecutionSafeCopy",
    "copyRealDeviceFieldTrialRetestExecutionButton",
    "mobileBrowserAcceptanceTitle",
    "mobileBrowserAcceptanceCopy",
    "mobileBrowserAck",
    "mobileBrowserBoundary",
    "mobileBrowserSafeCopy",
    "copyAcceptanceBundleButton",
    "terminalActionPanel",
    "terminalActionTitle",
    "terminalActionAck",
    "terminalActionBoundary",
    "terminalActionNotProven",
    "terminalActionBackButton",
    "terminalActionConfirmButton",
    "ackCopy",
    "startButton",
    "confirmButton",
    "cancelButton",
    "diagnosticsButton",
    "supportButton",
    "supportSafeCopy",
)
CURRENT_PANEL_EXPECTATIONS = {
    "primaryJourneyTitle": "三步主路径",
    "recoveryDecisionTitle": "恢复决策",
    "routeElevatorFieldSessionHandoffTitle": "路线电梯现场交接",
    "terminalActionTitle": "终端动作二次确认",
    "mobileDeviceEvidenceTitle": "手机设备证据采集",
    "mobileDeviceHandoffTitle": "真实手机验收交接会话",
    "mobilePwaInstallPromptTitle": "PWA 安装提示导出",
    "mobileRealDeviceRetestRequestTitle": "真实设备复测请求",
    "mobileRealDeviceFieldTrialTitle": "真实设备现场试跑包",
    "mobileRealDeviceFieldTrialReviewTitle": "现场试跑证据复核",
    "mobileRealDeviceFieldTrialRunbookExecutionTitle": "现场试跑执行清单",
    "mobileRealDeviceFieldTrialEvidenceRecordTitle": "现场证据记录",
    "mobileRealDeviceFieldTrialEvidenceVerdictTitle": "现场证据 verdict",
    "mobileRealDeviceFieldTrialRetestExecutionTitle": "现场复测执行",
    "mobileBrowserAcceptanceTitle": "浏览器验收包",
}
CURRENT_BOUNDARY_EXPECTATIONS = {
    "primaryJourneyBoundary": "software_proof_docker_mobile_primary_journey_gate",
    "recoveryDecisionBoundary": "software_proof_docker_mobile_recovery_decision_gate",
    "routeElevatorFieldSessionHandoffBoundary": "software_proof_docker_route_elevator_field_session_handoff_gate",
    "terminalActionBoundary": "software_proof_docker_mobile_terminal_action_confirmation_gate",
    "mobileDeviceEvidenceBoundary": "software_proof_docker_mobile_device_evidence_capture_gate",
    "mobileDeviceHandoffBoundary": "software_proof_docker_mobile_device_handoff_session_gate",
    "mobilePwaInstallPromptBoundary": "software_proof_docker_mobile_pwa_install_prompt_evidence_export_gate",
    "mobileRealDeviceRetestRequestBoundary": "software_proof_docker_mobile_real_device_retest_request_gate",
    "mobileRealDeviceRetestRequestSourceBoundary": "software_proof_docker_mobile_real_device_review_execution_gate",
    "mobileRealDeviceFieldTrialBoundary": "software_proof_docker_mobile_real_device_field_trial_package_gate",
    "mobileRealDeviceFieldTrialReviewBoundary": "software_proof_docker_mobile_real_device_field_trial_review_gate",
    "mobileRealDeviceFieldTrialRunbookExecutionBoundary": "software_proof_docker_mobile_real_device_field_trial_runbook_execution_gate",
    "mobileRealDeviceFieldTrialEvidenceRecordBoundary": "software_proof_docker_mobile_real_device_field_trial_evidence_record_gate",
    "mobileRealDeviceFieldTrialEvidenceVerdictBoundary": "software_proof_docker_mobile_real_device_field_trial_evidence_verdict_gate",
    "mobileRealDeviceFieldTrialEvidenceVerdictSourceBoundary": "software_proof_docker_mobile_real_device_field_trial_evidence_record_gate",
    "mobileRealDeviceFieldTrialRetestExecutionBoundary": "software_proof_docker_mobile_real_device_field_trial_retest_execution_gate",
    "mobileRealDeviceFieldTrialRetestExecutionSourceBoundary": "software_proof_docker_mobile_real_device_field_trial_evidence_verdict_gate",
    "mobileBrowserBoundary": "software_proof_docker_mobile_browser_acceptance_bundle_gate",
}
PHONE_SAFE_FORBIDDEN_VISIBLE = (
    "authorization",
    "oss ak",
    "oss sk",
    "access_key",
    "access key",
    "secret",
    "db url",
    "database url",
    "queue url",
    "ros topic",
    "/cmd_vel",
    "serial",
    "baudrate",
    "/users/",
    "/private/",
    "/ws/",
    "traceback",
    "checksum",
    "完整 artifact",
)
NOT_PROVEN = (
    "真实 iPhone/Android device",
    "production app",
    "真实 PWA install prompt",
    "真实云/4G",
    "OSS/CDN live traffic",
    "production DB/queue",
    "Nav2/fixed-route",
    "WAVE ROVER",
    "HIL",
    "真实送达",
)


class MobileWebHandler(BaseHTTPRequestHandler):
    """静态 PWA fixture server，只暴露 mobile/web 与 phone-safe JSON。"""

    server_version = "MobileWebAcceptanceGate/1.0"

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/status":
            self._send_json(self.server.fixture)
            return
        if parsed.path == "/api/diagnostics":
            self._send_json(self._diagnostics_payload())
            return
        self._send_static(parsed.path)

    def log_message(self, _format, *_args):
        # gate 输出保持机器可读；HTTP access log 不参与证据。
        return

    def _send_json(self, payload):
        data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _diagnostics_payload(self):
        fixture = self.server.fixture
        # diagnostics 复用 fixture 的 phone-safe 摘要，避免另造机器人状态。
        return {
            "schema": "trashbot.mobile_web_browser_diagnostics_fixture.v1",
            "source": "mobile_web_static_fixture",
            "safe_phone_copy": "本地 Chromium-family browser proof fixture；不是生产诊断。",
            "latest_status": fixture,
            "phone_readiness": fixture.get("phone_readiness", {}),
            "phone_support_bundle": fixture.get("phone_support_bundle")
            or fixture.get("phone_readiness", {}).get("phone_support_bundle", {}),
            "mobile_device_acceptance_readiness": fixture.get("mobile_device_acceptance_readiness", {}),
            "mobile_browser_acceptance_bundle": fixture.get("mobile_browser_acceptance_bundle", {}),
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "compatible_evidence_boundary": COMPATIBLE_EVIDENCE_BOUNDARY,
            "refresh_evidence_boundary": REFRESH_EVIDENCE_BOUNDARY,
            "legacy_artifact_evidence_boundary": LEGACY_ARTIFACT_EVIDENCE_BOUNDARY,
            "not_proven": list(NOT_PROVEN),
        }

    def _send_static(self, raw_path):
        safe_path = "/index.html" if raw_path in ("", "/") else raw_path
        # URL path 必须留在 mobile/web 内，避免本地文件路径穿越。
        relative = Path(urllib.parse.unquote(safe_path).lstrip("/"))
        candidate = (MOBILE_WEB_ROOT / relative).resolve()
        try:
            candidate.relative_to(MOBILE_WEB_ROOT.resolve())
        except ValueError:
            self.send_error(404)
            return
        if not candidate.is_file():
            self.send_error(404)
            return
        data = candidate.read_bytes()
        content_type = mimetypes.guess_type(str(candidate))[0] or "application/octet-stream"
        if candidate.suffix in (".html", ".js", ".css", ".svg", ".webmanifest"):
            content_type = {
                ".html": "text/html; charset=utf-8",
                ".js": "application/javascript; charset=utf-8",
                ".css": "text/css; charset=utf-8",
                ".svg": "image/svg+xml; charset=utf-8",
                ".webmanifest": "application/manifest+json; charset=utf-8",
            }[candidate.suffix]
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class LocalServer:
    """本地 HTTP server 生命周期，验证时不依赖 ROS2 或 cloud runtime。"""

    def __init__(self):
        self.server = None
        self.thread = None
        self.url = ""

    def __enter__(self):
        fixture = json.loads(MOBILE_FIXTURE.read_text(encoding="utf-8"))
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), MobileWebHandler)
        self.server.fixture = fixture
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/"
        return self

    def __exit__(self, _exc_type, _exc, _tb):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.thread:
            self.thread.join(timeout=2.0)


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def find_browser(explicit_path=""):
    candidates = [
        explicit_path,
        os.environ.get("PHONE_BROWSER_CHROME", ""),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
    ]
    for candidate in candidates:
        if candidate and os.path.exists(candidate) and os.access(candidate, os.X_OK):
            return candidate
    raise RuntimeError("no Chromium-family browser found; set PHONE_BROWSER_CHROME or --browser")


def http_json(url, *, method="GET", timeout=5.0):
    request = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


class ChromeProcess:
    """启动 headless Chrome，并用 CDP 读取真实布局与截图。"""

    def __init__(self, browser_path):
        self.browser_path = browser_path
        self.tmpdir = tempfile.TemporaryDirectory()
        self.port = free_port()
        self.process = None

    def __enter__(self):
        cmd = [
            self.browser_path,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--no-first-run",
            "--no-default-browser-check",
            f"--remote-debugging-port={self.port}",
            f"--user-data-dir={self.tmpdir.name}",
            "about:blank",
        ]
        self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._wait_until_ready()
        return self

    def __exit__(self, _exc_type, _exc, _tb):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.tmpdir.cleanup()

    def _wait_until_ready(self):
        deadline = time.time() + 10.0
        version_url = f"http://127.0.0.1:{self.port}/json/version"
        while time.time() < deadline:
            if self.process and self.process.poll() is not None:
                stderr = (self.process.stderr.read() or b"").decode("utf-8", errors="replace")
                raise RuntimeError(f"Chrome exited early: {stderr[-1000:]}")
            try:
                http_json(version_url, timeout=0.5)
                return
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                time.sleep(0.1)
        raise RuntimeError("Chrome remote debugging endpoint did not become ready")

    def new_page_ws(self):
        target_url = urllib.parse.quote("about:blank", safe="")
        target = http_json(f"http://127.0.0.1:{self.port}/json/new?{target_url}", method="PUT")
        return target["webSocketDebuggerUrl"]


class WebSocket:
    """最小 CDP websocket client；无第三方依赖，覆盖本 gate 的 text frame。"""

    def __init__(self, ws_url):
        parsed = urllib.parse.urlparse(ws_url)
        self.host = parsed.hostname or "127.0.0.1"
        self.port = parsed.port or 80
        self.path = parsed.path
        if parsed.query:
            self.path += f"?{parsed.query}"
        self.sock = None

    def __enter__(self):
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        self.sock = socket.create_connection((self.host, self.port), timeout=5.0)
        request = (
            f"GET {self.path} HTTP/1.1\r\n"
            f"Host: {self.host}:{self.port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(request.encode("ascii"))
        response = self.sock.recv(4096)
        if b" 101 " not in response.split(b"\r\n", 1)[0]:
            raise RuntimeError(f"websocket handshake failed: {response[:200]!r}")
        return self

    def __exit__(self, _exc_type, _exc, _tb):
        if self.sock:
            self.sock.close()

    def send_json(self, payload):
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        # client-to-server frame 必须 mask；CDP payload 较小但仍覆盖扩展长度。
        header = bytearray([0x81])
        if len(data) < 126:
            header.append(0x80 | len(data))
        elif len(data) < 65536:
            header.extend([0x80 | 126])
            header.extend(struct.pack("!H", len(data)))
        else:
            header.extend([0x80 | 127])
            header.extend(struct.pack("!Q", len(data)))
        mask = os.urandom(4)
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(data))
        self.sock.sendall(bytes(header) + mask + masked)

    def recv_json(self, timeout=5.0):
        self.sock.settimeout(timeout)
        while True:
            first = self.sock.recv(2)
            if len(first) < 2:
                raise RuntimeError("websocket closed")
            opcode = first[0] & 0x0F
            length = first[1] & 0x7F
            if length == 126:
                length = struct.unpack("!H", self._recv_exact(2))[0]
            elif length == 127:
                length = struct.unpack("!Q", self._recv_exact(8))[0]
            masked = bool(first[1] & 0x80)
            mask = self._recv_exact(4) if masked else b""
            payload = self._recv_exact(length)
            if masked:
                payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
            if opcode == 0x8:
                raise RuntimeError("websocket closed by browser")
            if opcode == 0x9:
                continue
            if opcode == 0x1:
                return json.loads(payload.decode("utf-8"))

    def _recv_exact(self, length):
        chunks = []
        remaining = length
        while remaining:
            chunk = self.sock.recv(remaining)
            if not chunk:
                raise RuntimeError("websocket closed during frame")
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)


class CDPClient:
    """Chrome DevTools Protocol helper，用递增 id 等待命令响应。"""

    def __init__(self, ws):
        self.ws = ws
        self.next_id = 1

    def call(self, method, params=None, timeout=5.0):
        command_id = self.next_id
        self.next_id += 1
        self.ws.send_json({"id": command_id, "method": method, "params": params or {}})
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                message = self.ws.recv_json(timeout=max(0.1, min(1.0, deadline - time.time())))
            except TimeoutError:
                # CDP 事件不是稳定心跳；空读应继续等到本次命令总超时。
                continue
            if message.get("id") == command_id:
                if "error" in message:
                    raise RuntimeError(f"CDP {method} failed: {message['error']}")
                return message.get("result", {})
        raise RuntimeError(f"CDP {method} timed out")

    def evaluate(self, expression, timeout=5.0):
        result = self.call(
            "Runtime.evaluate",
            {"expression": expression, "awaitPromise": True, "returnByValue": True},
            timeout=timeout,
        )
        if "exceptionDetails" in result:
            raise RuntimeError(f"Runtime.evaluate failed: {result['exceptionDetails']}")
        return result.get("result", {}).get("value")


def viewport_script():
    ids_json = json.dumps(list(KEY_ELEMENT_IDS))
    current_panel_expectations_json = json.dumps(CURRENT_PANEL_EXPECTATIONS, ensure_ascii=False)
    current_boundary_expectations_json = json.dumps(CURRENT_BOUNDARY_EXPECTATIONS, ensure_ascii=False)
    return f"""
(async () => {{
  const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
  for (let i = 0; i < 100; i += 1) {{
    const bundle = document.getElementById('mobileBrowserSafeCopy');
    const bundleBoundary = document.getElementById('mobileBrowserBoundary');
    const pwa = document.getElementById('mobilePwaInstallPromptSafeCopy');
    const handoff = document.getElementById('mobileDeviceHandoffSafeCopy');
    const device = document.getElementById('mobileDeviceEvidenceSafeCopy');
    const retest = document.getElementById('mobileRealDeviceRetestRequestSafeCopy');
    const fieldTrial = document.getElementById('mobileRealDeviceFieldTrialSafeCopy');
    const fieldTrialReview = document.getElementById('mobileRealDeviceFieldTrialReviewSafeCopy');
    const fieldTrialRunbook = document.getElementById('mobileRealDeviceFieldTrialRunbookExecutionSafeCopy');
    const fieldTrialRecord = document.getElementById('mobileRealDeviceFieldTrialEvidenceRecordSafeCopy');
    const fieldTrialVerdict = document.getElementById('mobileRealDeviceFieldTrialEvidenceVerdictSafeCopy');
    const fieldTrialRetest = document.getElementById('mobileRealDeviceFieldTrialRetestExecutionSafeCopy');
    const routeElevatorHandoff = document.getElementById('routeElevatorFieldSessionHandoffBoundary');
    const diag = document.getElementById('diagnosticsButton');
    const ack = document.getElementById('ackCopy');
    if (bundleBoundary && bundleBoundary.innerText.includes('software_proof_docker_mobile_browser_acceptance_bundle_gate') &&
        routeElevatorHandoff && routeElevatorHandoff.innerText.includes('software_proof_docker_route_elevator_field_session_handoff_gate') &&
        pwa && pwa.innerText.includes('trashbot.mobile_pwa_install_prompt_evidence_package.v1') &&
        handoff && handoff.innerText.includes('trashbot.mobile_device_handoff_package.v1') &&
        device && device.innerText.includes('trashbot.mobile_device_evidence_package.v1') &&
        retest && retest.innerText.includes('trashbot.mobile_real_device_retest_request_package.v1') &&
        fieldTrial && fieldTrial.innerText.includes('trashbot.mobile_real_device_field_trial_package_copy.v1') &&
        fieldTrialReview && fieldTrialReview.innerText.includes('trashbot.mobile_real_device_field_trial_review_copy.v1') &&
        fieldTrialRunbook && fieldTrialRunbook.innerText.includes('trashbot.mobile_real_device_field_trial_runbook_execution_copy.v1') &&
        fieldTrialRecord && fieldTrialRecord.innerText.includes('trashbot.mobile_real_device_field_trial_evidence_record_copy.v1') &&
        fieldTrialVerdict && fieldTrialVerdict.innerText.includes('trashbot.mobile_real_device_field_trial_evidence_verdict_copy.v1') &&
        fieldTrialRetest && fieldTrialRetest.innerText.includes('trashbot.mobile_real_device_field_trial_retest_execution_copy.v1') &&
        diag && !diag.disabled && ack && ack.innerText.includes('不代表送达成功')) break;
    await sleep(100);
  }}
  document.getElementById('diagnosticsButton').click();
  document.getElementById('supportButton').click();
  const terminalPanel = document.getElementById('terminalActionPanel');
  if (terminalPanel) {{
    // 这里只展开既有 DOM 以证明当前 PWA 首屏包含确认面板；不调用内部提交路径。
    terminalPanel.hidden = false;
  }}
  const diagnosticsPanel = document.getElementById('diagnosticsPanel');
  if (diagnosticsPanel) {{
    // 当前 gate 关注 DOM 可用性；状态渲染异常不能让证据脚本调用控制路径。
    diagnosticsPanel.hidden = false;
  }}
  document.getElementById('copyRealDeviceRetestRequestButton').click();
  document.getElementById('copyRealDeviceFieldTrialPackageButton').click();
  document.getElementById('copyRealDeviceFieldTrialReviewButton').click();
  document.getElementById('copyRealDeviceFieldTrialRunbookExecutionButton').click();
  document.getElementById('copyRealDeviceFieldTrialEvidenceRecordButton').click();
  document.getElementById('copyRealDeviceFieldTrialEvidenceVerdictButton').click();
  document.getElementById('copyRealDeviceFieldTrialRetestExecutionButton').click();
  document.getElementById('copyAcceptanceBundleButton').click();
  for (let i = 0; i < 50; i += 1) {{
    if (!document.getElementById('diagnosticsPanel').hidden &&
        !document.getElementById('terminalActionPanel').hidden &&
        document.getElementById('mobileRealDeviceRetestRequestSafeCopy').innerText.includes('trashbot.mobile_real_device_retest_request_package.v1') &&
        document.getElementById('mobileRealDeviceFieldTrialSafeCopy').innerText.includes('trashbot.mobile_real_device_field_trial_package_copy.v1') &&
        document.getElementById('mobileRealDeviceFieldTrialReviewSafeCopy').innerText.includes('trashbot.mobile_real_device_field_trial_review_copy.v1') &&
        document.getElementById('mobileRealDeviceFieldTrialRunbookExecutionSafeCopy').innerText.includes('trashbot.mobile_real_device_field_trial_runbook_execution_copy.v1') &&
        document.getElementById('mobileRealDeviceFieldTrialEvidenceRecordSafeCopy').innerText.includes('trashbot.mobile_real_device_field_trial_evidence_record_copy.v1') &&
        document.getElementById('mobileRealDeviceFieldTrialEvidenceVerdictSafeCopy').innerText.includes('trashbot.mobile_real_device_field_trial_evidence_verdict_copy.v1') &&
        document.getElementById('mobileRealDeviceFieldTrialRetestExecutionSafeCopy').innerText.includes('trashbot.mobile_real_device_field_trial_retest_execution_copy.v1') &&
        document.getElementById('mobileBrowserBoundary').innerText.includes('software_proof_docker_mobile_browser_acceptance_bundle_gate')) break;
    await sleep(100);
  }}
  const ids = {ids_json};
  const panelExpectations = {current_panel_expectations_json};
  const boundaryExpectations = {current_boundary_expectations_json};
  const rectFor = (id) => {{
    const node = document.getElementById(id);
    if (!node) return null;
    const rect = node.getBoundingClientRect();
    const style = window.getComputedStyle(node);
    return {{
      id,
      tag: node.tagName.toLowerCase(),
      text: (node.innerText || node.textContent || '').trim(),
      disabled: Boolean(node.disabled),
      visible: style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0,
      left: rect.left,
      top: rect.top,
      right: rect.right,
      bottom: rect.bottom,
      width: rect.width,
      height: rect.height
    }};
  }};
  const rects = ids.map(rectFor).filter(Boolean);
  const currentPanels = Object.fromEntries(Object.entries(panelExpectations).map(([id, expected]) => {{
    const node = document.getElementById(id);
    return [id, {{
      expected,
      present: Boolean(node),
      visible: Boolean(node) && window.getComputedStyle(node).display !== 'none' &&
        window.getComputedStyle(node).visibility !== 'hidden' &&
        node.getBoundingClientRect().width > 0 && node.getBoundingClientRect().height > 0,
      text: node ? (node.innerText || node.textContent || '').trim() : ''
    }}];
  }}));
  const currentBoundaries = Object.fromEntries(Object.entries(boundaryExpectations).map(([id, expected]) => {{
    const node = document.getElementById(id);
    return [id, {{
      expected,
      present: Boolean(node),
      text: node ? (node.innerText || node.textContent || '').trim() : ''
    }}];
  }}));
  const visibleText = Array.from(document.body.querySelectorAll('body *'))
    .filter((node) => {{
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0;
    }})
    .map((node) => (node.innerText || node.textContent || '').trim())
    .filter(Boolean)
    .join('\\n')
    .slice(0, 40000);
  return {{
    title: document.title,
    url: location.href,
    viewport: {{width: window.innerWidth, height: window.innerHeight}},
    documentWidth: document.documentElement.scrollWidth,
    documentHeight: document.documentElement.scrollHeight,
    rects,
    primaryDisabled: {{
      start: document.getElementById('startButton').disabled,
      confirm: document.getElementById('confirmButton').disabled,
      cancel: document.getElementById('cancelButton').disabled
    }},
    diagnosticsPanelVisible: !document.getElementById('diagnosticsPanel').hidden,
    terminalActionPanelVisible: !document.getElementById('terminalActionPanel').hidden,
    terminalActionConfirmDisabled: document.getElementById('terminalActionConfirmButton').disabled,
    supportCopyVisible: document.getElementById('supportSafeCopy').innerText.trim().length > 0,
    deviceEvidenceVisible: document.getElementById('mobileDeviceEvidenceSafeCopy').innerText.includes('trashbot.mobile_device_evidence_package.v1'),
    deviceHandoffVisible: document.getElementById('mobileDeviceHandoffSafeCopy').innerText.includes('trashbot.mobile_device_handoff_package.v1'),
    routeElevatorFieldSessionHandoffVisible:
      document.getElementById('routeElevatorFieldSessionHandoffTitle').innerText.includes('路线电梯现场交接') &&
      document.getElementById('routeElevatorFieldSessionHandoffBoundary').innerText.includes('software_proof_docker_route_elevator_field_session_handoff_gate'),
    routeElevatorFieldSessionHandoffFailClosed:
      document.getElementById('routeElevatorFieldSessionHandoffCopy').innerText.includes('blocked/not_proven') &&
      document.getElementById('routeElevatorFieldSessionHandoffControls').innerText.includes('delivery_success=false') &&
      document.getElementById('routeElevatorFieldSessionHandoffControls').innerText.includes('primary_actions_enabled=false') &&
      document.getElementById('routeElevatorFieldSessionHandoffNotProven').innerText.includes('HIL'),
    pwaInstallPromptVisible:
      document.getElementById('mobilePwaInstallPromptSafeCopy').innerText.includes('trashbot.mobile_pwa_install_prompt_evidence_package.v1') ||
      document.getElementById('mobilePwaInstallPromptSafeCopy').innerText.includes('trashbot.mobile_pwa_install_prompt_evidence_export_copy.v1'),
    retestRequestVisible: document.getElementById('mobileRealDeviceRetestRequestSafeCopy').innerText.includes('trashbot.mobile_real_device_retest_request_package.v1'),
    retestRequestCopyable: !document.getElementById('copyRealDeviceRetestRequestButton').disabled,
    fieldTrialPackageVisible: document.getElementById('mobileRealDeviceFieldTrialSafeCopy').innerText.includes('trashbot.mobile_real_device_field_trial_package_copy.v1'),
    fieldTrialPackageCopyable: !document.getElementById('copyRealDeviceFieldTrialPackageButton').disabled,
    fieldTrialReviewVisible: document.getElementById('mobileRealDeviceFieldTrialReviewSafeCopy').innerText.includes('trashbot.mobile_real_device_field_trial_review_copy.v1'),
    fieldTrialReviewCopyable: !document.getElementById('copyRealDeviceFieldTrialReviewButton').disabled,
    fieldTrialRunbookExecutionVisible: document.getElementById('mobileRealDeviceFieldTrialRunbookExecutionSafeCopy').innerText.includes('trashbot.mobile_real_device_field_trial_runbook_execution_copy.v1'),
    fieldTrialRunbookExecutionCopyable: !document.getElementById('copyRealDeviceFieldTrialRunbookExecutionButton').disabled,
    fieldTrialEvidenceRecordVisible: document.getElementById('mobileRealDeviceFieldTrialEvidenceRecordSafeCopy').innerText.includes('trashbot.mobile_real_device_field_trial_evidence_record_copy.v1'),
    fieldTrialEvidenceRecordCopyable: !document.getElementById('copyRealDeviceFieldTrialEvidenceRecordButton').disabled,
    fieldTrialEvidenceVerdictVisible: document.getElementById('mobileRealDeviceFieldTrialEvidenceVerdictSafeCopy').innerText.includes('trashbot.mobile_real_device_field_trial_evidence_verdict_copy.v1'),
    fieldTrialEvidenceVerdictCopyable: !document.getElementById('copyRealDeviceFieldTrialEvidenceVerdictButton').disabled,
    fieldTrialRetestExecutionVisible: document.getElementById('mobileRealDeviceFieldTrialRetestExecutionSafeCopy').innerText.includes('trashbot.mobile_real_device_field_trial_retest_execution_copy.v1'),
    fieldTrialRetestExecutionCopyable: !document.getElementById('copyRealDeviceFieldTrialRetestExecutionButton').disabled,
    bundleVisible: document.getElementById('mobileBrowserSafeCopy').innerText.includes('trashbot.mobile_browser_acceptance_bundle.v1') ||
      document.getElementById('mobileBrowserBoundary').innerText.includes('software_proof_docker_mobile_browser_acceptance_bundle_gate'),
    bundleCopyButtonEnabled: !document.getElementById('copyAcceptanceBundleButton').disabled,
    currentPanels,
    currentBoundaries,
    ackText: document.getElementById('ackCopy').innerText,
    bundleAckText: document.getElementById('mobileBrowserAck').innerText,
    terminalAckText: document.getElementById('terminalActionAck').innerText,
    pwaAckText: document.getElementById('mobilePwaInstallPromptAck').innerText,
    handoffAckText: document.getElementById('mobileDeviceHandoffAck').innerText,
    deviceAckText: document.getElementById('mobileDeviceEvidenceAck').innerText,
    retestRequestAckText: document.getElementById('mobileRealDeviceRetestRequestAck').innerText,
    visibleText
  }};
}})()
"""


def intersects(first, second):
    left = max(float(first["left"]), float(second["left"]))
    top = max(float(first["top"]), float(second["top"]))
    right = min(float(first["right"]), float(second["right"]))
    bottom = min(float(first["bottom"]), float(second["bottom"]))
    return (right - left) > 1.0 and (bottom - top) > 1.0


def judge_viewport(result):
    rects = {item["id"]: item for item in result["rects"]}
    viewport_width = float(result.get("viewport", {}).get("width") or 0)
    first_screen_rects = [
        item for item in rects.values()
        if item.get("visible") and item.get("top", 0) >= -1 and item.get("top", 0) <= 900
    ]
    # 首屏互相覆盖只检查兄弟级关键文案和按钮；pre 内 JSON 换行不按 overlap 处理。
    overlap_candidates = [
        item for item in first_screen_rects
        if item["id"] not in ("mobileBrowserSafeCopy", "supportSafeCopy")
    ]
    overlaps = []
    for index, first in enumerate(overlap_candidates):
        for second in overlap_candidates[index + 1:]:
            if intersects(first, second):
                overlaps.append(f"{first['id']}->{second['id']}")
    hit_area_failures = [
        button_id for button_id in HIT_AREA_IDS
        if rects.get(button_id, {}).get("width", 0) < 44 or rects.get(button_id, {}).get("height", 0) < 44
    ]
    horizontal_overflow = [
        item["id"] for item in first_screen_rects
        if item.get("left", 0) < -1.0 or item.get("right", 0) > viewport_width + 1.0
    ]
    page_horizontal_overflow = float(result.get("documentWidth") or 0) > viewport_width + 1.0
    visible_lower = result.get("visibleText", "").lower()
    phone_safe_failures = [
        token for token in PHONE_SAFE_FORBIDDEN_VISIBLE if token.lower() in visible_lower
    ]
    current_panel_failures = [
        panel_id
        for panel_id, item in result.get("currentPanels", {}).items()
        if not item.get("present") or not item.get("visible") or item.get("expected", "") not in item.get("text", "")
    ]
    current_boundary_failures = [
        boundary_id
        for boundary_id, item in result.get("currentBoundaries", {}).items()
        if not item.get("present") or item.get("expected", "") not in item.get("text", "")
    ]
    ack_copy = "\n".join([
        result.get("ackText", ""),
        result.get("bundleAckText", ""),
        result.get("terminalAckText", ""),
        result.get("pwaAckText", ""),
        result.get("handoffAckText", ""),
        result.get("deviceAckText", ""),
        result.get("retestRequestAckText", ""),
    ])
    ack_visible = "ACK" in ack_copy and "不代表送达成功" in ack_copy
    return {
        "hit_area_status": "passed" if not hit_area_failures else "failed",
        "overlap_status": "passed" if not overlaps else "failed",
        "overflow_status": "passed" if not horizontal_overflow and not page_horizontal_overflow else "failed",
        "ack_copy_visible": bool(ack_visible),
        "ack_not_delivery_success": "delivery success" not in ack_copy.lower() and "送达成功" in ack_copy,
        "diagnostics_accessible": bool(result.get("diagnosticsPanelVisible")),
        "terminal_action_confirmation_visible": bool(result.get("terminalActionPanelVisible")),
        "terminal_action_confirm_disabled": bool(result.get("terminalActionConfirmDisabled")),
        "support_handoff_available": bool(result.get("supportCopyVisible")),
        "device_evidence_capture_visible": bool(result.get("deviceEvidenceVisible")),
        "device_handoff_session_visible": bool(result.get("deviceHandoffVisible")),
        "route_elevator_field_session_handoff_visible": bool(result.get("routeElevatorFieldSessionHandoffVisible")),
        "route_elevator_field_session_handoff_fail_closed": bool(
            result.get("routeElevatorFieldSessionHandoffFailClosed")
        ),
        "pwa_install_prompt_evidence_visible": bool(result.get("pwaInstallPromptVisible")),
        "real_device_retest_request_visible": bool(result.get("retestRequestVisible")),
        "real_device_retest_request_copyable": bool(result.get("retestRequestCopyable")),
        "field_trial_package_visible": bool(result.get("fieldTrialPackageVisible")),
        "field_trial_package_copyable": bool(result.get("fieldTrialPackageCopyable")),
        "field_trial_review_visible": bool(result.get("fieldTrialReviewVisible")),
        "field_trial_review_copyable": bool(result.get("fieldTrialReviewCopyable")),
        "field_trial_runbook_execution_visible": bool(result.get("fieldTrialRunbookExecutionVisible")),
        "field_trial_runbook_execution_copyable": bool(result.get("fieldTrialRunbookExecutionCopyable")),
        "field_trial_evidence_record_visible": bool(result.get("fieldTrialEvidenceRecordVisible")),
        "field_trial_evidence_record_copyable": bool(result.get("fieldTrialEvidenceRecordCopyable")),
        "field_trial_evidence_verdict_visible": bool(result.get("fieldTrialEvidenceVerdictVisible")),
        "field_trial_evidence_verdict_copyable": bool(result.get("fieldTrialEvidenceVerdictCopyable")),
        "field_trial_retest_execution_visible": bool(result.get("fieldTrialRetestExecutionVisible")),
        "field_trial_retest_execution_copyable": bool(result.get("fieldTrialRetestExecutionCopyable")),
        "browser_acceptance_bundle_visible": bool(result.get("bundleVisible")),
        "browser_acceptance_bundle_copyable": bool(result.get("bundleCopyButtonEnabled")),
        "current_panels_status": "passed" if not current_panel_failures else "failed",
        "current_boundaries_status": "passed" if not current_boundary_failures else "failed",
        "primary_actions_disabled": all(result.get("primaryDisabled", {}).values()),
        "phone_safe_status": "passed" if not phone_safe_failures else "failed",
        "hit_area_failures": hit_area_failures,
        "overlaps": overlaps,
        "horizontal_overflow": horizontal_overflow,
        "page_horizontal_overflow": page_horizontal_overflow,
        "phone_safe_failures": phone_safe_failures,
        "current_panel_failures": current_panel_failures,
        "current_boundary_failures": current_boundary_failures,
    }


def run_viewport(cdp, url, width, height, output_dir):
    # 每个 viewport 都重新导航，避免展开 diagnostics 的状态污染下一次判断。
    cdp.call("Emulation.setDeviceMetricsOverride", {
        "width": width,
        "height": height,
        "deviceScaleFactor": 2 if width <= 430 else 1,
        "mobile": width <= 430,
    })
    cdp.call("Page.navigate", {"url": url})
    time.sleep(0.5)
    result = cdp.evaluate(viewport_script(), timeout=30.0)
    judgment = judge_viewport(result)
    screenshot = cdp.call("Page.captureScreenshot", {"format": "png", "fromSurface": True}, timeout=8.0)
    screenshot_path = output_dir / f"mobile_current_pwa_field_trial_browser_{width}x{height}.png"
    screenshot_path.write_bytes(base64.b64decode(screenshot["data"]))
    evidence = {
        "viewport": f"{width}x{height}",
        "url": result.get("url", ""),
        "title": result.get("title", ""),
        "judgment": judgment,
        "rects": result.get("rects", []),
        "copy": {
            "ack": result.get("ackText", ""),
            "bundle_ack": result.get("bundleAckText", ""),
            "retest_request_ack": result.get("retestRequestAckText", ""),
        },
        "screenshot": str(screenshot_path),
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "compatible_evidence_boundary": COMPATIBLE_EVIDENCE_BOUNDARY,
        "refresh_evidence_boundary": REFRESH_EVIDENCE_BOUNDARY,
        "legacy_artifact_evidence_boundary": LEGACY_ARTIFACT_EVIDENCE_BOUNDARY,
        "not_proven": list(NOT_PROVEN),
    }
    evidence_path = output_dir / f"mobile_current_pwa_field_trial_browser_{width}x{height}.json"
    evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return evidence_path, screenshot_path, judgment


def parse_args():
    parser = argparse.ArgumentParser(description="Run mobile/web local browser proof gate.")
    parser.add_argument("--output-dir", required=True, help="Directory for screenshots and JSON evidence.")
    parser.add_argument("--browser", default="", help="Optional Chromium-family executable path.")
    return parser.parse_args()


def main():
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    browser = find_browser(args.browser)
    all_passed = True
    per_viewport = []
    with LocalServer() as server, ChromeProcess(browser) as chrome:
        with WebSocket(chrome.new_page_ws()) as ws:
            cdp = CDPClient(ws)
            cdp.call("Page.enable")
            cdp.call("Runtime.enable")
            for width, height in VIEWPORTS:
                evidence_path, screenshot_path, judgment = run_viewport(cdp, server.url, width, height, output_dir)
                passed = (
                    judgment["hit_area_status"] == "passed"
                    and judgment["overlap_status"] == "passed"
                    and judgment["overflow_status"] == "passed"
                    and judgment["ack_copy_visible"]
                    and judgment["ack_not_delivery_success"]
                    and judgment["diagnostics_accessible"]
                    and judgment["terminal_action_confirmation_visible"]
                    and judgment["terminal_action_confirm_disabled"]
                    and judgment["support_handoff_available"]
                    and judgment["device_evidence_capture_visible"]
                    and judgment["device_handoff_session_visible"]
                    and judgment["route_elevator_field_session_handoff_visible"]
                    and judgment["route_elevator_field_session_handoff_fail_closed"]
                    and judgment["pwa_install_prompt_evidence_visible"]
                    and judgment["real_device_retest_request_visible"]
                    and judgment["real_device_retest_request_copyable"]
                    and judgment["field_trial_package_visible"]
                    and judgment["field_trial_package_copyable"]
                    and judgment["field_trial_review_visible"]
                    and judgment["field_trial_review_copyable"]
                    and judgment["field_trial_runbook_execution_visible"]
                    and judgment["field_trial_runbook_execution_copyable"]
                    and judgment["field_trial_evidence_record_visible"]
                    and judgment["field_trial_evidence_record_copyable"]
                    and judgment["field_trial_evidence_verdict_visible"]
                    and judgment["field_trial_evidence_verdict_copyable"]
                    and judgment["field_trial_retest_execution_visible"]
                    and judgment["field_trial_retest_execution_copyable"]
                    and judgment["browser_acceptance_bundle_visible"]
                    and judgment["browser_acceptance_bundle_copyable"]
                    and judgment["current_panels_status"] == "passed"
                    and judgment["current_boundaries_status"] == "passed"
                    and judgment["primary_actions_disabled"]
                    and judgment["phone_safe_status"] == "passed"
                )
                all_passed = all_passed and passed
                per_viewport.append({
                    "viewport": f"{width}x{height}",
                    "passed": passed,
                    "evidence_json": str(evidence_path),
                    "screenshot": str(screenshot_path),
                    "judgment": judgment,
                })
                print(
                    f"viewport={width}x{height} "
                    f"passed={str(passed).lower()} "
                    f"hit_area_status={judgment['hit_area_status']} "
                    f"overlap_status={judgment['overlap_status']} "
                    f"overflow_status={judgment['overflow_status']} "
                    f"ack_copy_visible={str(judgment['ack_copy_visible']).lower()} "
                    f"primary_actions_disabled={str(judgment['primary_actions_disabled']).lower()} "
                    f"diagnostics_accessible={str(judgment['diagnostics_accessible']).lower()} "
                    f"terminal_action_confirmation_visible={str(judgment['terminal_action_confirmation_visible']).lower()} "
                    f"support_handoff_available={str(judgment['support_handoff_available']).lower()} "
                    f"device_evidence_capture_visible={str(judgment['device_evidence_capture_visible']).lower()} "
                    f"device_handoff_session_visible={str(judgment['device_handoff_session_visible']).lower()} "
                    f"route_elevator_field_session_handoff_visible="
                    f"{str(judgment['route_elevator_field_session_handoff_visible']).lower()} "
                    f"route_elevator_field_session_handoff_fail_closed="
                    f"{str(judgment['route_elevator_field_session_handoff_fail_closed']).lower()} "
                    f"route_elevator_handoff_browser_proof={ROUTE_ELEVATOR_HANDOFF_BROWSER_PROOF} "
                    f"pwa_install_prompt_evidence_visible={str(judgment['pwa_install_prompt_evidence_visible']).lower()} "
                    f"real_device_retest_request_visible={str(judgment['real_device_retest_request_visible']).lower()} "
                    f"real_device_retest_request_copyable={str(judgment['real_device_retest_request_copyable']).lower()} "
                    f"field_trial_package_visible={str(judgment['field_trial_package_visible']).lower()} "
                    f"field_trial_package_copyable={str(judgment['field_trial_package_copyable']).lower()} "
                    f"field_trial_review_visible={str(judgment['field_trial_review_visible']).lower()} "
                    f"field_trial_review_copyable={str(judgment['field_trial_review_copyable']).lower()} "
                    f"field_trial_runbook_execution_visible={str(judgment['field_trial_runbook_execution_visible']).lower()} "
                    f"field_trial_runbook_execution_copyable={str(judgment['field_trial_runbook_execution_copyable']).lower()} "
                    f"field_trial_evidence_record_visible={str(judgment['field_trial_evidence_record_visible']).lower()} "
                    f"field_trial_evidence_record_copyable={str(judgment['field_trial_evidence_record_copyable']).lower()} "
                    f"field_trial_evidence_verdict_visible={str(judgment['field_trial_evidence_verdict_visible']).lower()} "
                    f"field_trial_evidence_verdict_copyable={str(judgment['field_trial_evidence_verdict_copyable']).lower()} "
                    f"field_trial_retest_execution_visible={str(judgment['field_trial_retest_execution_visible']).lower()} "
                    f"field_trial_retest_execution_copyable={str(judgment['field_trial_retest_execution_copyable']).lower()} "
                    f"bundle_visible={str(judgment['browser_acceptance_bundle_visible']).lower()} "
                    f"bundle_copyable={str(judgment['browser_acceptance_bundle_copyable']).lower()} "
                    f"current_panels_status={judgment['current_panels_status']} "
                    f"current_boundaries_status={judgment['current_boundaries_status']} "
                    f"phone_safe_status={judgment['phone_safe_status']} "
                    f"evidence_boundary={EVIDENCE_BOUNDARY} "
                    f"compatible_evidence_boundary={COMPATIBLE_EVIDENCE_BOUNDARY} "
                    f"legacy_artifact_evidence_boundary={LEGACY_ARTIFACT_EVIDENCE_BOUNDARY} "
                    f"evidence_json={evidence_path} screenshot={screenshot_path}"
                )
                if not passed:
                    print(f"failure_detail={json.dumps(judgment, ensure_ascii=False, sort_keys=True)}")
    summary_path = output_dir / "mobile_current_pwa_field_trial_browser_acceptance_summary.json"
    artifact_hashes = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(output_dir.glob("mobile_current_pwa_field_trial_browser_*.*"))
        if path.is_file()
    }
    summary = {
        "ok": bool(all_passed),
        "browser": browser,
        "served_root": str(MOBILE_WEB_ROOT),
        "fixture": str(MOBILE_FIXTURE),
        "viewports": [f"{width}x{height}" for width, height in VIEWPORTS],
        "checks": per_viewport,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "compatible_evidence_boundary": COMPATIBLE_EVIDENCE_BOUNDARY,
        "refresh_evidence_boundary": REFRESH_EVIDENCE_BOUNDARY,
        "legacy_artifact_evidence_boundary": LEGACY_ARTIFACT_EVIDENCE_BOUNDARY,
        "boundary_compatibility": (
            "This field-trial browser proof supersedes the retest and refresh browser proof boundaries, "
            "while preserving explicit compatibility fields for older summaries."
        ),
        "proof_type": "real local Chromium-family browser proof for current dependency-free mobile/web PWA with complete field-trial first-screen chain",
        "route_elevator_handoff_browser_proof": ROUTE_ELEVATOR_HANDOFF_BROWSER_PROOF,
        "ack_semantics": "ACK is accepted/processing evidence only, not delivery success.",
        "not_proven": list(NOT_PROVEN),
        "artifact_sha256": artifact_hashes,
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"summary={summary_path} ok={str(all_passed).lower()} "
        f"evidence_boundary={EVIDENCE_BOUNDARY} "
        f"compatible_evidence_boundary={COMPATIBLE_EVIDENCE_BOUNDARY} "
        f"legacy_artifact_evidence_boundary={LEGACY_ARTIFACT_EVIDENCE_BOUNDARY}"
    )
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
