#!/usr/bin/env python3
"""LAN-only WebRTC camera smoke for the Orange Pi upper computer."""

from __future__ import annotations

import argparse
import asyncio
import glob
import importlib.util
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


APP_NAME = "rober-local-webrtc-camera-smoke"
DEFAULT_PORT = 8088
DEFAULT_WIDTH = 640
DEFAULT_HEIGHT = 480
DEFAULT_FPS = 15
IMPORTS = ("aiohttp", "aiortc", "cv2", "av")


def import_state() -> dict[str, bool]:
    """用 find_spec 做轻量探测，缺依赖时仍可启动降级诊断页。"""
    return {name: importlib.util.find_spec(name) is not None for name in IMPORTS}


def list_video_devices() -> list[dict[str, Any]]:
    """只枚举设备节点，不默认打开摄像头，避免抢占 ROS2/调试进程。"""
    devices: list[dict[str, Any]] = []
    for name in sorted(glob.glob("/dev/video*")):
        path = Path(name)
        item: dict[str, Any] = {
            "path": str(path),
            "exists": path.exists(),
            "readable": os.access(path, os.R_OK),
            "writable": os.access(path, os.W_OK),
        }
        devices.append(item)
    return devices


def run_short_command(args: list[str], timeout_s: float = 2.0) -> dict[str, Any]:
    """外部探测都加短超时，避免异常板端命令把 smoke 卡死。"""
    try:
        completed = subprocess.run(
            args,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_s,
        )
    except FileNotFoundError:
        return {"available": False, "error": "command_not_found", "cmd": args}
    except subprocess.TimeoutExpired:
        return {"available": True, "error": "timeout", "cmd": args}
    return {
        "available": True,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "cmd": args,
    }


def print_json(payload: dict[str, Any]) -> None:
    """命令行 smoke 固定输出 JSON，方便远端脚本和 sprint 证据直接解析。"""
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def http_json(url: str, timeout_s: float, method: str = "GET", payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """自检客户端只访问 smoke HTTP 接口，不触碰 ROS2/串口/底盘控制链路。"""
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:  # noqa: S310 - 目标 URL 由本地 smoke 命令显式传入。
            data = response.read().decode("utf-8", errors="replace")
            return {
                "ok": True,
                "status": response.status,
                "json": json.loads(data) if data else None,
            }
    except urllib.error.HTTPError as exc:
        data = exc.read().decode("utf-8", errors="replace")
        try:
            parsed: Any = json.loads(data)
        except json.JSONDecodeError:
            parsed = data
        return {"ok": False, "status": exc.code, "json": parsed}
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__, "detail": str(exc)}


def build_health(port: int, video_source: str) -> dict[str, Any]:
    """健康输出明确写 safe_to_control=false，避免被误接入控制链路。"""
    state = import_state()
    return {
        "schema": "trashbot.local_webrtc_camera_smoke.v1",
        "app": APP_NAME,
        "status": "ready" if all(state.values()) else "degraded",
        "host": socket.gethostname(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "port": port,
        "video_source": video_source,
        "imports": state,
        "lan_only": True,
        "cloud_relay": False,
        "turn_required": False,
        "sends_commands": False,
        "safe_to_control": False,
        "robot_control_executed": False,
        "diagnostics": {
            "offer_self_test": "/offer recvonly SDP client is available via --self-test-url",
            "frame_boundary": "first_frame_received proves aiortc answer plus one decoded video frame",
        },
        "vendor_reference": [
            "docs/vendor/VENDOR_INDEX.md",
            "docs/interfaces/o7_realtime_hardware_sources.md",
            "docs/vendor/waveshare_wave_rover/ugv_rpi/app.py",
        ],
    }


def build_devices() -> dict[str, Any]:
    """设备输出保留 v4l2 原始摘要，便于定位权限/格式/驱动问题。"""
    devices = list_video_devices()
    v4l2_path = shutil.which("v4l2-ctl")
    return {
        "schema": "trashbot.local_webrtc_camera_devices.v1",
        "devices": devices,
        "v4l2_ctl": v4l2_path or None,
        "v4l2_list_devices": run_short_command([v4l2_path, "--list-devices"]) if v4l2_path else None,
    }


def html_page(port: int, video_source: str) -> str:
    """页面只做接收视频和诊断展示，不渲染任何机器人控制入口。"""
    health = json.dumps(build_health(port, video_source), ensure_ascii=False, indent=2)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>rober LAN WebRTC Camera Smoke</title>
  <style>
    body {{ margin: 0; font-family: system-ui, sans-serif; background: #101418; color: #edf2f7; }}
    main {{ max-width: 960px; margin: 0 auto; padding: 24px; }}
    video {{ width: 100%; max-height: 70vh; background: #000; border: 1px solid #364152; }}
    button {{ padding: 10px 14px; margin: 12px 8px 12px 0; }}
    pre {{ overflow: auto; background: #18202a; padding: 12px; border: 1px solid #364152; }}
    .bad {{ color: #ffb4a8; }}
  </style>
</head>
<body>
  <main>
    <h1>rober LAN WebRTC Camera Smoke</h1>
    <p>Receive-only WebRTC video. LAN only. No cloud relay, no TURN, no robot control.</p>
    <video id="video" autoplay playsinline controls muted></video>
    <div>
      <button id="start">Start WebRTC video</button>
      <button id="health">Refresh health/devices</button>
    </div>
    <pre id="status">{health}</pre>
  </main>
  <script>
    const video = document.getElementById('video');
    const statusBox = document.getElementById('status');
    function show(value) {{
      statusBox.textContent = typeof value === 'string' ? value : JSON.stringify(value, null, 2);
    }}
    async function refresh() {{
      const [health, devices] = await Promise.all([
        fetch('/health').then(r => r.json()),
        fetch('/devices').then(r => r.json()),
      ]);
      show({{ health, devices }});
    }}
    async function start() {{
      const pc = new RTCPeerConnection({{ iceServers: [] }});
      pc.addTransceiver('video', {{ direction: 'recvonly' }});
      pc.ontrack = event => {{ video.srcObject = event.streams[0]; }};
      pc.onconnectionstatechange = () => show({{ connectionState: pc.connectionState }});
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);
      const response = await fetch('/offer', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify(pc.localDescription),
      }});
      const payload = await response.json();
      if (!response.ok) throw new Error(JSON.stringify(payload));
      await pc.setRemoteDescription(payload);
      show({{ connectionState: pc.connectionState, answerType: payload.type }});
    }}
    document.getElementById('start').onclick = () => start().catch(err => show(String(err)));
    document.getElementById('health').onclick = () => refresh().catch(err => show(String(err)));
    refresh().catch(err => show(String(err)));
  </script>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--video-source", default=os.getenv("ROBER_CAMERA_SOURCE", "0"))
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--fps", type=int, default=DEFAULT_FPS)
    parser.add_argument(
        "--self-test-url",
        default=None,
        help="Run recvonly WebRTC offer-level client against an already running smoke base URL.",
    )
    parser.add_argument("--self-test-timeout", type=float, default=8.0)
    parser.add_argument(
        "--require-frame",
        action="store_true",
        help="Return non-zero when the self-test cannot receive a first video frame.",
    )
    return parser.parse_args()


async def self_test_client(args: argparse.Namespace) -> int:
    """本地/远端自检只做 recvonly 观看证明，不产生任何机器人动作。"""
    base_url = str(args.self_test_url).rstrip("/")
    started_at = time.monotonic()
    health = http_json(f"{base_url}/health", args.self_test_timeout)
    devices = http_json(f"{base_url}/devices", args.self_test_timeout)
    result: dict[str, Any] = {
        "schema": "trashbot.local_webrtc_camera_offer_self_test.v1",
        "target": base_url,
        "status": "starting",
        "safe_to_control": False,
        "sends_commands": False,
        "robot_control_executed": False,
        "lan_only": True,
        "turn_required": False,
        "health": health,
        "devices": devices,
        "answer_received": False,
        "first_frame_received": False,
        "connection_state": None,
    }
    peer_id: str | None = None
    state = import_state()
    result["client_imports"] = state
    if not health.get("ok"):
        result.update({"status": "failed", "reason": "health_unreachable"})
        print_json(result)
        return 2 if args.require_frame else 0
    if not state.get("aiortc") or not state.get("aiohttp"):
        result.update({"status": "degraded", "reason": "webrtc_client_dependency_missing"})
        print_json(result)
        return 2 if args.require_frame else 0

    # aiortc 只在自检模式按需导入，避免缺依赖时影响诊断 HTTP 服务。
    from aiohttp import ClientSession, ClientTimeout
    from aiortc import RTCPeerConnection, RTCSessionDescription
    from aiortc.contrib.media import MediaStreamError

    pc = RTCPeerConnection(configuration=None)
    frame_event = asyncio.Event()
    track_error: dict[str, Any] = {}

    @pc.on("track")
    def on_track(track: Any) -> None:
        async def read_first_frame() -> None:
            try:
                frame = await asyncio.wait_for(track.recv(), timeout=args.self_test_timeout)
                result["first_frame_received"] = True
                result["first_frame"] = {
                    "width": getattr(frame, "width", None),
                    "height": getattr(frame, "height", None),
                    "pts": getattr(frame, "pts", None),
                }
            except (asyncio.TimeoutError, MediaStreamError) as exc:
                track_error.update({"error": type(exc).__name__, "detail": str(exc)})
            finally:
                frame_event.set()

        asyncio.create_task(read_first_frame())

    try:
        pc.addTransceiver("video", direction="recvonly")
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        async with ClientSession(timeout=ClientTimeout(total=args.self_test_timeout)) as session:
            async with session.post(
                f"{base_url}/offer",
                json={"sdp": pc.localDescription.sdp, "type": pc.localDescription.type},
            ) as response:
                answer_payload = await response.json(content_type=None)
                result["offer_http_status"] = response.status
                if response.status >= 400:
                    result.update({"status": "failed", "reason": "offer_rejected", "offer_response": answer_payload})
                    print_json(result)
                    return 2 if args.require_frame else 0
        peer_id = answer_payload.get("peer_id")
        result["peer_id"] = peer_id
        result["answer_received"] = answer_payload.get("type") == "answer" and bool(answer_payload.get("sdp"))
        await pc.setRemoteDescription(RTCSessionDescription(sdp=answer_payload["sdp"], type=answer_payload["type"]))
        await asyncio.wait_for(frame_event.wait(), timeout=args.self_test_timeout)
        result["connection_state"] = pc.connectionState
    except Exception as exc:
        result.update({"status": "failed", "reason": type(exc).__name__, "detail": str(exc)})
        if track_error:
            result["track_error"] = track_error
    finally:
        result["duration_ms"] = int((time.monotonic() - started_at) * 1000)
        await pc.close()
        if peer_id:
            # WebRTC close 不会自动走 HTTP signaling，显式释放服务端 peer 才能连续自检。
            result["server_peer_close"] = http_json(f"{base_url}/peers/{peer_id}/close", 2.0, method="POST")
    if track_error:
        result["track_error"] = track_error
    if result.get("answer_received") and result.get("first_frame_received"):
        result["status"] = "ok"
    elif result.get("status") == "starting":
        result["status"] = "failed"
        result["reason"] = "first_frame_not_received"
    print_json(result)
    return 0 if result["status"] == "ok" or not args.require_frame else 2


def fallback_server(args: argparse.Namespace) -> None:
    """aiohttp 不存在时仍给出诊断 HTTP，方便远端无网时定位缺口。"""

    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, content_type: str, data: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:  # noqa: N802 - 标准库回调名固定为驼峰。
            if self.path == "/health":
                payload = json.dumps(build_health(args.port, args.video_source), ensure_ascii=False).encode()
                self._send(HTTPStatus.OK, "application/json", payload)
            elif self.path == "/devices":
                payload = json.dumps(build_devices(), ensure_ascii=False).encode()
                self._send(HTTPStatus.OK, "application/json", payload)
            else:
                self._send(HTTPStatus.OK, "text/html; charset=utf-8", html_page(args.port, args.video_source).encode())

        def do_POST(self) -> None:  # noqa: N802 - 标准库回调名固定为驼峰。
            payload = {
                "error": "webrtc_dependency_missing",
                "message": "aiohttp/aiortc/cv2/av must be installed before /offer can create WebRTC answer",
                "imports": import_state(),
            }
            self._send(HTTPStatus.SERVICE_UNAVAILABLE, "application/json", json.dumps(payload).encode())

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(json.dumps({"event": "fallback_server_started", "health": build_health(args.port, args.video_source)}))
    server.serve_forever()


async def aiohttp_server(args: argparse.Namespace) -> None:
    """主服务路径：aiortc 生成 answer，OpenCV 读取真实摄像头帧。"""
    from aiohttp import web
    from aiortc import RTCPeerConnection, RTCSessionDescription
    from aiortc.contrib.media import MediaStreamError
    from aiortc.mediastreams import VideoStreamTrack
    import av
    import cv2

    pcs: dict[str, RTCPeerConnection] = {}

    class CameraTrack(VideoStreamTrack):
        """每个 peer 单独持有摄像头，第一版限制单连接来降低设备占用风险。"""

        def __init__(self) -> None:
            super().__init__()
            source: int | str = int(args.video_source) if str(args.video_source).isdigit() else args.video_source
            self.cap = cv2.VideoCapture(source)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
            self.cap.set(cv2.CAP_PROP_FPS, args.fps)
            if not self.cap.isOpened():
                raise RuntimeError(f"camera_open_failed:{args.video_source}")

        async def recv(self) -> av.VideoFrame:
            pts, time_base = await self.next_timestamp()
            ok, frame = await asyncio.to_thread(self.cap.read)
            if not ok or frame is None:
                raise MediaStreamError("camera_frame_read_failed")
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            video_frame = av.VideoFrame.from_ndarray(rgb, format="rgb24")
            video_frame.pts = pts
            video_frame.time_base = time_base
            return video_frame

        def stop(self) -> None:
            self.cap.release()
            super().stop()

    async def index(_: web.Request) -> web.Response:
        return web.Response(text=html_page(args.port, args.video_source), content_type="text/html")

    async def health(_: web.Request) -> web.Response:
        payload = build_health(args.port, args.video_source)
        payload["active_peer_connections"] = len(pcs)
        return web.json_response(payload)

    async def devices(_: web.Request) -> web.Response:
        return web.json_response(build_devices())

    async def offer(request: web.Request) -> web.Response:
        if not all(import_state().values()):
            return web.json_response({"error": "webrtc_dependency_missing", "imports": import_state()}, status=503)
        if len(pcs) >= 1:
            return web.json_response({"error": "camera_in_use", "active_peer_connections": len(pcs)}, status=409)
        params = await request.json()
        pc = RTCPeerConnection(configuration=None)
        peer_id = uuid.uuid4().hex
        pcs[peer_id] = pc

        @pc.on("connectionstatechange")
        async def on_connectionstatechange() -> None:
            if pc.connectionState in ("failed", "closed", "disconnected"):
                await pc.close()
                pcs.pop(peer_id, None)

        try:
            pc.addTrack(CameraTrack())
            await pc.setRemoteDescription(RTCSessionDescription(sdp=params["sdp"], type=params["type"]))
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)
        except Exception as exc:
            await pc.close()
            pcs.pop(peer_id, None)
            return web.json_response({"error": "offer_failed", "detail": str(exc)}, status=500)
        return web.json_response({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type, "peer_id": peer_id})

    async def close_peer(request: web.Request) -> web.Response:
        peer_id = request.match_info["peer_id"]
        pc = pcs.pop(peer_id, None)
        if pc is None:
            return web.json_response({"closed": False, "reason": "peer_not_found", "peer_id": peer_id}, status=404)
        # 只关闭调用方拿到的 peer_id，避免自检误杀正在人工查看的浏览器连接。
        await pc.close()
        return web.json_response({"closed": True, "peer_id": peer_id, "active_peer_connections": len(pcs)})

    async def on_shutdown(_: web.Application) -> None:
        await asyncio.gather(*(pc.close() for pc in list(pcs.values())), return_exceptions=True)
        pcs.clear()

    app = web.Application()
    app.on_shutdown.append(on_shutdown)
    app.router.add_get("/", index)
    app.router.add_get("/health", health)
    app.router.add_get("/devices", devices)
    app.router.add_post("/offer", offer)
    app.router.add_post("/peers/{peer_id}/close", close_peer)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, args.host, args.port)
    await site.start()
    print(json.dumps({"event": "aiohttp_server_started", "health": build_health(args.port, args.video_source)}))
    while True:
        await asyncio.sleep(3600)


def main() -> int:
    args = parse_args()
    if args.self_test_url:
        return asyncio.run(self_test_client(args))
    state = import_state()
    if not all(state.values()):
        # 依赖不完整时走标准库诊断服务，保证无网现场也能看到缺口。
        fallback_server(args)
        return 0
    try:
        asyncio.run(aiohttp_server(args))
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
