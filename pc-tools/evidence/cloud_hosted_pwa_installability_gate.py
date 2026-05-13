#!/usr/bin/env python3
"""Validate cloud-relay hosted mobile/web PWA installability software proof.

本 gate 必须访问 cloud-relay 托管 URL，而不是直接读取本地静态文件。
它只证明 Docker/local relay + 本机浏览器软件证据，不证明真实手机、
真实 PWA install prompt、真实公网 HTTPS/TLS、4G、HIL 或真实送达。
"""

import argparse
import hashlib
import importlib.util
import json
import os
import pathlib
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
MOBILE_WEB_ROOT = REPO_ROOT / "mobile" / "web"
PHONE_BROWSER_GATE = REPO_ROOT / "pc-tools" / "evidence" / "phone_browser_acceptance_gate.py"
EVIDENCE_BOUNDARY = "software_proof_docker_cloud_hosted_mobile_pwa_installability_gate"
HOSTED_WEB_BOUNDARY = "software_proof_docker_cloud_hosted_mobile_web_gate"
ENTRYPOINT_BOUNDARY = "software_proof_docker_mobile_web_entrypoint_gate"
VIEWPORTS = ((390, 844), (768, 900))
STATIC_ROUTES = (
    "/",
    "/index.html",
    "/app.js",
    "/styles.css",
    "/manifest.webmanifest",
    "/service-worker.js",
    "/offline.html",
    "/icon-192.svg",
    "/icon-512.svg",
)
CONTROL_ROUTES = (
    "/api/status",
    "/api/diagnostics",
    "/api/collect",
    "/robots/trashbot-001/commands",
    "/robots/trashbot-001/commands/next",
    "/robots/trashbot-001/commands/cmd-proof/ack",
)
NOT_PROVEN = (
    "真实 iPhone/Android device",
    "production app",
    "真实 PWA install prompt",
    "真实云/4G",
    "真实公网 HTTPS/TLS",
    "OSS/CDN live traffic",
    "production DB/queue",
    "Nav2/fixed-route",
    "WAVE ROVER",
    "HIL",
    "真实送达",
)


def load_browser_gate():
    # 复用现有 CDP/viewport 代码，避免维护第二套浏览器判断逻辑。
    spec = importlib.util.spec_from_file_location("phone_browser_acceptance_gate", PHONE_BROWSER_GATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.EVIDENCE_BOUNDARY = EVIDENCE_BOUNDARY
    module.NOT_PROVEN = NOT_PROVEN
    return module


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def request_bytes(url, *, method="GET", timeout=5.0):
    request = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read()


def request_json(url, *, method="GET", timeout=5.0):
    status, headers, body = request_bytes(url, method=method, timeout=timeout)
    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        payload = {"decode_error": body[:200].decode("utf-8", errors="replace")}
    return status, headers, payload


class RelayProcess:
    """启动 cloud-relay HTTP runtime，确保 gate 访问的是 hosted surface。"""

    def __init__(self):
        self.port = free_port()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.process = None
        self.url = f"http://127.0.0.1:{self.port}/"

    def __enter__(self):
        env = os.environ.copy()
        env.update(
            {
                "PYTHONPATH": f"{REPO_ROOT / 'cloud-relay' / 'src'}:{REPO_ROOT / 'onboard' / 'src' / 'ros2_trashbot_behavior'}",
                "TRASHBOT_REMOTE_CLOUD_MOBILE_WEB_ROOT": str(MOBILE_WEB_ROOT),
                "TRASHBOT_REMOTE_CLOUD_DEFAULT_ROBOT_ID": "trashbot-001",
            }
        )
        state_path = pathlib.Path(self.tmpdir.name) / "relay-state.json"
        cmd = [
            sys.executable,
            "-m",
            "ros2_trashbot_cloud_relay.remote_cloud_relay",
            "--host",
            "127.0.0.1",
            "--port",
            str(self.port),
            "--state-path",
            str(state_path),
            "--bearer-token",
            "dev-token",
        ]
        self.process = subprocess.Popen(cmd, cwd=str(REPO_ROOT), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._wait_ready()
        return self

    def __exit__(self, _exc_type, _exc, _tb):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.tmpdir.cleanup()

    def _wait_ready(self):
        deadline = time.time() + 15.0
        while time.time() < deadline:
            if self.process and self.process.poll() is not None:
                stderr = (self.process.stderr.read() or b"").decode("utf-8", errors="replace")
                raise RuntimeError(f"cloud relay exited early: {stderr[-1200:]}")
            try:
                status, _headers, _body = request_bytes(f"{self.url}healthz", timeout=0.5)
                if status == 200:
                    return
            except urllib.error.URLError:
                # relay 进程已启动但 socket 尚未监听时会短暂拒绝连接，继续轮询。
                pass
            time.sleep(0.1)
        raise RuntimeError("cloud relay did not become ready")


def validate_manifest(base_url):
    status, headers, payload = request_json(base_url + "manifest.webmanifest")
    icons = payload.get("icons", []) if isinstance(payload, dict) else []
    icon_checks = []
    for icon in icons:
        src = str(icon.get("src") or "").lstrip("./")
        route_status, route_headers, route_body = request_bytes(base_url + src)
        icon_checks.append(
            {
                "src": icon.get("src"),
                "sizes": icon.get("sizes"),
                "type": icon.get("type"),
                "purpose": icon.get("purpose"),
                "route_status": route_status,
                "content_type": route_headers.get("Content-Type", ""),
                "sha256": hashlib.sha256(route_body).hexdigest() if route_status == 200 else "",
            }
        )
    required = {
        "name": payload.get("name") == "rober 手机送垃圾入口",
        "short_name": payload.get("short_name") == "rober",
        "start_url": payload.get("start_url") == "./index.html",
        "scope": payload.get("scope") == "./",
        "display": payload.get("display") == "standalone",
        "theme_color": bool(payload.get("theme_color")),
        "background_color": bool(payload.get("background_color")),
        "icons": len(icon_checks) >= 2 and all(item["route_status"] == 200 for item in icon_checks),
        "entrypoint_evidence_boundary": payload.get("evidence_boundary") == ENTRYPOINT_BOUNDARY,
        "installability_evidence_boundary": payload.get("installability_evidence_boundary") == EVIDENCE_BOUNDARY,
        "hosted_header_boundary": headers.get("X-Trashbot-Evidence-Boundary") == HOSTED_WEB_BOUNDARY,
    }
    return {
        "ok": status == 200 and all(required.values()),
        "status": status,
        "content_type": headers.get("Content-Type", ""),
        "required": required,
        "manifest": payload,
        "icons": icon_checks,
    }


def validate_service_worker(base_url):
    status, headers, body = request_bytes(base_url + "service-worker.js")
    text = body.decode("utf-8", errors="replace")
    checks = {
        "status_200": status == 200,
        "content_type_js": "application/javascript" in headers.get("Content-Type", ""),
        "shell_cache_only": all(name in text for name in ("./index.html", "./styles.css", "./app.js", "./offline.html", "./manifest.webmanifest")),
        "api_bypassed": 'path.startsWith("/api/")' in text,
        "robots_bypassed": 'path.startsWith("/robots/")' in text,
        "commands_bypassed": 'path.includes("/commands")' in text and 'path === "/api/collect"' in text,
        "ack_bypassed": 'path.includes("/ack")' in text,
        "diagnostics_bypassed": 'path.includes("/diagnostics")' in text,
        "non_get_bypassed": 'request.method !== "GET"' in text,
        "no_store_dynamic": 'fetch(event.request, { cache: "no-store" })' in text,
        "no_queue_or_replay_api": all(token not in text for token in ("sync", "periodicSync", "indexedDB", "localStorage", "postMessage")),
        "hosted_header_boundary": headers.get("X-Trashbot-Evidence-Boundary") == HOSTED_WEB_BOUNDARY,
    }
    route_checks = {}
    for route in CONTROL_ROUTES:
        method = "POST" if route in ("/api/collect", "/robots/trashbot-001/commands", "/robots/trashbot-001/commands/cmd-proof/ack") else "GET"
        route_status, route_headers, route_body = request_bytes(base_url.rstrip("/") + route, method=method)
        content_type = route_headers.get("Content-Type", "")
        route_checks[route] = {
            "method": method,
            "status": route_status,
            "content_type": content_type,
            "static_shell_returned": b"<!doctype html>" in route_body.lower() or b"app-shell" in route_body,
        }
    return {
        "ok": all(checks.values()) and not any(item["static_shell_returned"] for item in route_checks.values()),
        "checks": checks,
        "control_route_checks": route_checks,
        "sha256": hashlib.sha256(body).hexdigest(),
    }


def validate_offline_shell(base_url):
    status, headers, body = request_bytes(base_url + "offline.html")
    text = body.decode("utf-8", errors="replace")
    checks = {
        "status_200": status == 200,
        "content_type_html": "text/html" in headers.get("Content-Type", ""),
        "primary_actions_disabled": text.count("disabled") >= 3,
        "no_cache_queue_replay_copy": "不会发送、缓存、排队或重放" in text,
        "ack_not_success": "ACK" in text and "送达成功" not in text,
        "entrypoint_boundary": ENTRYPOINT_BOUNDARY in text,
        "hosted_header_boundary": headers.get("X-Trashbot-Evidence-Boundary") == HOSTED_WEB_BOUNDARY,
    }
    return {"ok": all(checks.values()), "checks": checks, "sha256": hashlib.sha256(body).hexdigest()}


def validate_static_routes(base_url):
    assets = {}
    for route in STATIC_ROUTES:
        status, headers, body = request_bytes(base_url.rstrip("/") + route)
        assets[route] = {
            "status": status,
            "content_type": headers.get("Content-Type", ""),
            "hosted_header_boundary": headers.get("X-Trashbot-Evidence-Boundary"),
            "sha256": hashlib.sha256(body).hexdigest() if status == 200 else "",
        }
    ok = all(item["status"] == 200 and item["hosted_header_boundary"] == HOSTED_WEB_BOUNDARY for item in assets.values())
    return {"ok": ok, "assets": assets}


def run_browser_acceptance(browser_gate, base_url, output_dir, browser_path):
    browser = browser_gate.find_browser(browser_path)
    all_passed = True
    per_viewport = []
    with browser_gate.ChromeProcess(browser) as chrome:
        with browser_gate.WebSocket(chrome.new_page_ws()) as ws:
            cdp = browser_gate.CDPClient(ws)
            cdp.call("Page.enable")
            cdp.call("Runtime.enable")
            for width, height in VIEWPORTS:
                # Hosted relay 启动后首次页面还会注册 service worker 和拉取同源 API，给 CDP 更宽窗口。
                evidence_path, screenshot_path, judgment = browser_gate.run_viewport(cdp, base_url, width, height, output_dir)
                passed = (
                    judgment["hit_area_status"] == "passed"
                    and judgment["overlap_status"] == "passed"
                    and judgment["overflow_status"] == "passed"
                    and judgment["ack_copy_visible"]
                    and judgment["ack_not_delivery_success"]
                    and judgment["diagnostics_accessible"]
                    and judgment["support_handoff_available"]
                    and judgment["browser_acceptance_bundle_visible"]
                    and judgment["browser_acceptance_bundle_copyable"]
                    and judgment["primary_actions_disabled"]
                    and judgment["phone_safe_status"] == "passed"
                )
                all_passed = all_passed and passed
                per_viewport.append(
                    {
                        "viewport": f"{width}x{height}",
                        "passed": passed,
                        "evidence_json": str(evidence_path),
                        "screenshot": str(screenshot_path),
                        "judgment": judgment,
                    }
                )
                print(
                    f"viewport={width}x{height} passed={str(passed).lower()} "
                    f"hit_area_status={judgment['hit_area_status']} "
                    f"overflow_status={judgment['overflow_status']} "
                    f"primary_actions_disabled={str(judgment['primary_actions_disabled']).lower()} "
                    f"diagnostics_accessible={str(judgment['diagnostics_accessible']).lower()} "
                    f"support_handoff_available={str(judgment['support_handoff_available']).lower()} "
                    f"bundle_visible={str(judgment['browser_acceptance_bundle_visible']).lower()} "
                    f"evidence_boundary={EVIDENCE_BOUNDARY}"
                )
    return {"ok": all_passed, "browser": browser, "viewports": per_viewport}


def parse_args():
    parser = argparse.ArgumentParser(description="Run cloud-hosted mobile PWA installability gate.")
    parser.add_argument("--output-dir", required=True, help="Directory for JSON and browser evidence.")
    parser.add_argument("--browser", default="", help="Optional Chromium-family executable path.")
    return parser.parse_args()


def main():
    args = parse_args()
    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    browser_gate = load_browser_gate()
    with RelayProcess() as relay:
        hosted_url = relay.url
        manifest = validate_manifest(hosted_url)
        service_worker = validate_service_worker(hosted_url)
        offline_shell = validate_offline_shell(hosted_url)
        static_routes = validate_static_routes(hosted_url)
        browser = run_browser_acceptance(browser_gate, hosted_url, output_dir, args.browser)
    artifact_hashes = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(output_dir.glob("mobile_web_browser_*.*"))
        if path.is_file()
    }
    ok = all(item["ok"] for item in (manifest, service_worker, offline_shell, static_routes, browser))
    summary = {
        "ok": ok,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "hosted_url": hosted_url,
        "hosted_surface_boundary": HOSTED_WEB_BOUNDARY,
        "manifest": manifest,
        "service_worker": service_worker,
        "offline_shell": offline_shell,
        "static_routes": static_routes,
        "browser_acceptance": browser,
        "ack_semantics": "ACK is accepted/processing evidence only, not delivery success.",
        "not_proven": list(NOT_PROVEN),
        "artifact_sha256": artifact_hashes,
    }
    summary_path = output_dir / "cloud_hosted_pwa_installability_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"summary={summary_path} ok={str(ok).lower()} "
        f"hosted_url={hosted_url} evidence_boundary={EVIDENCE_BOUNDARY}"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
