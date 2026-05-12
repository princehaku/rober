#!/usr/bin/env python3
"""Run the O5 local phone browser acceptance gate.

This script starts the dependency-free operator gateway HTML/API fixture and
uses a real Chromium-family browser through Chrome DevTools Protocol. It avoids
ROS2, hardware, cloud and 4G dependencies while still measuring rendered layout.
"""

import argparse
import base64
import hashlib
import json
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
from http.server import ThreadingHTTPServer
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BEHAVIOR_ROOT = REPO_ROOT / "src" / "ros2_trashbot_behavior"
sys.path.insert(0, str(BEHAVIOR_ROOT))

from ros2_trashbot_behavior.operator_gateway_http import make_handler, status_payload
from ros2_trashbot_behavior.remote_cloud_relay import (
    create_network_recovery_artifact,
    create_oss_cdn_manifest_artifact,
)


EVIDENCE_BOUNDARY = "software_proof_docker_phone_browser_acceptance_gate"
VIEWPORTS = ((390, 844), (768, 900))
PRIMARY_BUTTON_IDS = ("collectButton", "dropoffButton", "cancelButton")
BUTTON_IDS = PRIMARY_BUTTON_IDS + ("diagnosticsButton",)
PHONE_SAFE_FORBIDDEN_VISIBLE = (
    "{",
    "}",
    "/cmd_vel",
    "ros_topic",
    "serial_port",
    "baudrate",
    "bearer",
    "token",
    "cloud secret",
)


class FixtureGateway:
    """operator gateway fixture，只暴露手机需要的状态和诊断摘要。"""

    def __init__(self, evidence_dir):
        self.mock_cloud_bearer_token = ""
        self.network_recovery_artifact_ref = ""
        self.oss_cdn_manifest_artifact_ref = ""
        self._prepare_artifacts(Path(evidence_dir))

    def _prepare_artifacts(self, evidence_dir):
        # manifest 与 network recovery artifact 只用于让 readiness gate 进入可复查状态。
        manifest_path = evidence_dir / "fixture_oss_cdn_manifest.json"
        network_path = evidence_dir / "fixture_network_recovery.json"
        sqlite_path = evidence_dir / "fixture_network_recovery.sqlite"
        # acceptance gate 可能重复运行；先删除旧 fixture，避免 SQLite 状态污染本轮 proof。
        for path in (manifest_path, network_path, sqlite_path):
            if path.exists():
                path.unlink()
        create_oss_cdn_manifest_artifact(
            manifest_path,
            "robot-phone-browser",
            "task-phone-browser",
            date_text="2026-05-12",
        )
        create_network_recovery_artifact(network_path, sqlite_path, state_backend="sqlite")
        self.oss_cdn_manifest_artifact_ref = str(manifest_path)
        self.network_recovery_artifact_ref = str(network_path)

    def snapshot(self):
        # status_stale 来自 mock cloud 默认状态，本地 action 权限仍让脚本证明主操作被 command gate 阻断。
        return status_payload(
            "waiting_for_trash",
            "Waiting for trash.",
            can_collect=True,
            can_confirm_dropoff=True,
            can_cancel=True,
        )

    def diagnostics(self):
        # 诊断入口必须可打开，但 payload 只给 phone-safe 摘要，不暴露 raw ROS/hardware details。
        return {
            "api_version": "slice2.operator.v1",
            "state": "diagnostics_ready",
            "software_version": "fixture",
            "map_version": "local-browser-fixture",
            "route_version": "local-browser-fixture",
            "latest_status": self.snapshot(),
            "source": "software_proof",
            "failure": {},
            "log_refs": [],
            "vision_samples": {"integrity_summary": {"status": "unknown"}},
            "route_proof_summary": {},
            "route_proof_status": {"state": "not_run"},
            "hardware_proof": {
                "status": "needs_hil",
                "summary": "Software proof only; hardware-in-loop still required.",
                "next_step": "Run real robot validation before claiming hardware readiness.",
                "risk_flags": [],
            },
            "elevator_assist": {"enabled": False, "state": "disabled"},
            "elevator_assist_status": {"state": "disabled"},
            "oss_cdn_manifest": {
                "state": "ready",
                "safe_summary": "诊断对象引用已准备。",
                "retry_hint": "如手机无法查看诊断，请刷新状态或重新生成诊断引用。",
                "evidence_boundary": "software_proof_docker_phone_manifest_consumption",
            },
        }

    def start_collection(self, target, trash_type=0):
        return 409, status_payload("busy", "Fixture keeps command safety blocked.")

    def confirm_dropoff(self, accepted=True):
        return 409, status_payload("busy", "Fixture keeps command safety blocked.")

    def cancel_collection(self):
        return 409, status_payload("busy", "Fixture keeps command safety blocked.")

    def vision_review_queue(self):
        return {
            "ok": True,
            "review_queue_count": 0,
            "review_queue": [],
            "progress_summary": {"total": 0, "decided": 0, "pending": 0, "coverage_rate": 0},
            "decision_distribution": {},
            "next_pending_sample": None,
        }

    def submit_review_decision(self, payload):
        return 400, {"ok": False, "message": "fixture review queue is empty"}


class LocalServer:
    """本地 HTTP fixture 生命周期，确保验收不依赖真实 ROS2 runtime。"""

    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.server = None
        self.thread = None
        self.url = ""

    def __enter__(self):
        gateway = FixtureGateway(self.output_dir)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(gateway))
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
    """启动 headless Chrome，并暴露 page websocket 地址。"""

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
    """最小 CDP websocket client；只实现本验收需要的 text frame。"""

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
        # client-to-server frame 必须 mask；payload 很小，126/127 两种长度也一并覆盖。
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
    """Chrome DevTools Protocol helper，用同步 id 等待命令结果。"""

    def __init__(self, ws):
        self.ws = ws
        self.next_id = 1

    def call(self, method, params=None, timeout=5.0):
        command_id = self.next_id
        self.next_id += 1
        self.ws.send_json({"id": command_id, "method": method, "params": params or {}})
        deadline = time.time() + timeout
        while time.time() < deadline:
            message = self.ws.recv_json(timeout=max(0.1, min(1.0, deadline - time.time())))
            if message.get("id") == command_id:
                if "error" in message:
                    raise RuntimeError(f"CDP {method} failed: {message['error']}")
                return message.get("result", {})
        raise RuntimeError(f"CDP {method} timed out")

    def evaluate(self, expression, timeout=5.0):
        result = self.call(
            "Runtime.evaluate",
            {
                "expression": expression,
                "awaitPromise": True,
                "returnByValue": True,
            },
            timeout=timeout,
        )
        remote = result.get("result", {})
        if "exceptionDetails" in result:
            raise RuntimeError(f"Runtime.evaluate failed: {result['exceptionDetails']}")
        return remote.get("value")


def viewport_script():
    return r"""
(async () => {
  const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
  for (let i = 0; i < 80; i += 1) {
    const ack = document.getElementById('commandSafetyAck');
    const diag = document.getElementById('diagnosticsButton');
    if (ack && ack.innerText.includes('不能代表送达成功') && diag && !diag.disabled) break;
    await sleep(100);
  }
  const ids = [
    'phoneReadinessPanel',
    'phoneReadinessCopy',
    'phoneReadinessNext',
    'commandSafetyCopy',
    'commandSafetyAck',
    'diagnosticsGateCopy',
    'collectButton',
    'dropoffButton',
    'cancelButton',
    'diagnosticsButton'
  ];
  const rectFor = (id) => {
    const node = document.getElementById(id);
    if (!node) return null;
    const rect = node.getBoundingClientRect();
    const style = window.getComputedStyle(node);
    return {
      id,
      text: (node.innerText || node.textContent || '').trim(),
      disabled: Boolean(node.disabled),
      visible: style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0,
      left: rect.left,
      top: rect.top,
      right: rect.right,
      bottom: rect.bottom,
      width: rect.width,
      height: rect.height
    };
  };
  const rects = ids.map(rectFor).filter(Boolean);
  document.getElementById('diagnosticsButton').click();
  for (let i = 0; i < 40; i += 1) {
    if (!document.getElementById('diagnosticsPanel').hidden) break;
    await sleep(100);
  }
  const visibleText = Array.from(document.body.querySelectorAll('body *'))
    .filter((node) => {
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0;
    })
    .map((node) => (node.innerText || node.textContent || '').trim())
    .filter(Boolean)
    .join('\n')
    .slice(0, 12000);
  return {
    title: document.title,
    url: location.href,
    viewport: {width: window.innerWidth, height: window.innerHeight},
    rects,
    ackText: document.getElementById('commandSafetyAck').innerText,
    commandCopy: document.getElementById('commandSafetyCopy').innerText,
    diagnosticsCopy: document.getElementById('diagnosticsGateCopy').innerText,
    readinessCopy: document.getElementById('phoneReadinessCopy').innerText,
    diagnosticsPanelVisible: !document.getElementById('diagnosticsPanel').hidden,
    visibleText
  };
})()
"""


def intersects(a, b):
    left = max(float(a["left"]), float(b["left"]))
    top = max(float(a["top"]), float(b["top"]))
    right = min(float(a["right"]), float(b["right"]))
    bottom = min(float(a["bottom"]), float(b["bottom"]))
    return (right - left) > 1.0 and (bottom - top) > 1.0


def judge_viewport(result):
    rects = {item["id"]: item for item in result["rects"]}
    button_failures = [
        button_id
        for button_id in BUTTON_IDS
        if rects.get(button_id, {}).get("width", 0) < 44 or rects.get(button_id, {}).get("height", 0) < 44
    ]
    primary_enabled = [button_id for button_id in PRIMARY_BUTTON_IDS if not rects.get(button_id, {}).get("disabled")]
    diagnostics_accessible = bool(
        not rects.get("diagnosticsButton", {}).get("disabled")
        and result.get("diagnosticsPanelVisible")
    )
    key_rects = [
        rects[item_id]
        for item_id in (
            "phoneReadinessCopy",
            "phoneReadinessNext",
            "commandSafetyCopy",
            "commandSafetyAck",
            "diagnosticsGateCopy",
            "collectButton",
            "dropoffButton",
            "cancelButton",
            "diagnosticsButton",
        )
        if rects.get(item_id, {}).get("visible")
    ]
    overlaps = []
    viewport_width = float(result.get("viewport", {}).get("width") or 0)
    viewport_height = float(result.get("viewport", {}).get("height") or 0)
    for index, first in enumerate(key_rects):
        for second in key_rects[index + 1:]:
            if intersects(first, second):
                overlaps.append(f"{first['id']}->{second['id']}")
    overflow = [
        item["id"]
        for item in key_rects
        if item.get("left", 0) < -1.0 or item.get("right", 0) > viewport_width + 1.0
    ]
    first_screen_buttons = [
        button_id
        for button_id in BUTTON_IDS
        if rects.get(button_id, {}).get("bottom", viewport_height + 1) <= viewport_height
    ]
    visible_lower = result.get("visibleText", "").lower()
    phone_safe_failures = [
        token for token in PHONE_SAFE_FORBIDDEN_VISIBLE if token.lower() in visible_lower
    ]
    ack_visible = "ACK" in result.get("ackText", "") and "不能代表送达成功" in result.get("ackText", "")
    return {
        "hit_area_status": "passed" if not button_failures else "failed",
        "overlap_status": "passed" if not overlaps else "failed",
        "overflow_status": "passed" if not overflow else "failed",
        "ack_copy_visible": bool(ack_visible),
        "diagnostics_accessible": diagnostics_accessible,
        "primary_actions_disabled": not primary_enabled,
        "first_screen_buttons_visible": len(first_screen_buttons) == len(BUTTON_IDS),
        "phone_safe_status": "passed" if not phone_safe_failures else "failed",
        "button_failures": button_failures,
        "primary_enabled": primary_enabled,
        "overlaps": overlaps,
        "overflow": overflow,
        "phone_safe_failures": phone_safe_failures,
    }


def run_viewport(cdp, url, width, height, output_dir):
    # 每个 viewport 都重新导航，避免上一个 diagnostics 展开状态影响首屏判断。
    cdp.call("Emulation.setDeviceMetricsOverride", {
        "width": width,
        "height": height,
        "deviceScaleFactor": 2 if width <= 430 else 1,
        "mobile": width <= 430,
    })
    cdp.call("Page.navigate", {"url": url})
    time.sleep(0.5)
    result = cdp.evaluate(viewport_script(), timeout=12.0)
    judgment = judge_viewport(result)
    screenshot = cdp.call("Page.captureScreenshot", {"format": "png", "fromSurface": True}, timeout=8.0)
    screenshot_path = output_dir / f"phone_browser_{width}x{height}.png"
    screenshot_path.write_bytes(base64.b64decode(screenshot["data"]))
    evidence = {
        "viewport": f"{width}x{height}",
        "url": result.get("url", ""),
        "title": result.get("title", ""),
        "judgment": judgment,
        "rects": result.get("rects", []),
        "copy": {
            "readiness": result.get("readinessCopy", ""),
            "command": result.get("commandCopy", ""),
            "ack": result.get("ackText", ""),
            "diagnostics": result.get("diagnosticsCopy", ""),
        },
        "screenshot": str(screenshot_path),
        "evidence_boundary": EVIDENCE_BOUNDARY,
    }
    evidence_path = output_dir / f"phone_browser_{width}x{height}.json"
    evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return evidence_path, screenshot_path, judgment


def parse_args():
    parser = argparse.ArgumentParser(description="Run local phone browser layout acceptance gate.")
    parser.add_argument("--output-dir", required=True, help="Directory for screenshots and JSON evidence.")
    parser.add_argument("--browser", default="", help="Optional Chromium-family executable path.")
    return parser.parse_args()


def main():
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    browser = find_browser(args.browser)
    all_passed = True
    with LocalServer(output_dir) as server, ChromeProcess(browser) as chrome:
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
                    and judgment["diagnostics_accessible"]
                    and judgment["primary_actions_disabled"]
                    and judgment["first_screen_buttons_visible"]
                    and judgment["phone_safe_status"] == "passed"
                )
                all_passed = all_passed and passed
                print(
                    f"viewport={width}x{height} "
                    f"hit_area_status={judgment['hit_area_status']} "
                    f"overlap_status={judgment['overlap_status']} "
                    f"overflow_status={judgment['overflow_status']} "
                    f"ack_copy_visible={str(judgment['ack_copy_visible']).lower()} "
                    f"diagnostics_accessible={str(judgment['diagnostics_accessible']).lower()} "
                    f"primary_actions_disabled={str(judgment['primary_actions_disabled']).lower()} "
                    f"first_screen_buttons_visible={str(judgment['first_screen_buttons_visible']).lower()} "
                    f"phone_safe_status={judgment['phone_safe_status']} "
                    f"evidence_boundary={EVIDENCE_BOUNDARY} "
                    f"evidence_json={evidence_path} screenshot={screenshot_path}"
                )
                if not passed:
                    print(f"failure_detail={json.dumps(judgment, ensure_ascii=False, sort_keys=True)}")
    summary_path = output_dir / "phone_browser_acceptance_summary.json"
    summary = {
        "ok": bool(all_passed),
        "browser": browser,
        "viewports": [f"{width}x{height}" for width, height in VIEWPORTS],
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "artifact_sha256": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(output_dir.glob("phone_browser_*.*"))
            if path.is_file()
        },
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"summary={summary_path} ok={str(all_passed).lower()} evidence_boundary={EVIDENCE_BOUNDARY}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
