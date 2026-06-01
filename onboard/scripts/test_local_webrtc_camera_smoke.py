#!/usr/bin/env python3
"""local_webrtc_camera_smoke.py 的轻量资源释放测试。"""

from __future__ import annotations

import asyncio
import importlib.util
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_PATH = Path(__file__).with_name("local_webrtc_camera_smoke.py")


def load_smoke_module():
    """按文件路径导入脚本，避免测试依赖 ROS2 包安装或 PYTHONPATH。"""
    spec = importlib.util.spec_from_file_location("local_webrtc_camera_smoke", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot_load:{SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeTrack:
    """fake track 只记录 stop 次数，用来证明 close path 真的释放本地 track。"""

    kind = "video"

    def __init__(self) -> None:
        self.stop_calls = 0

    def stop(self) -> None:
        # 真实 CameraTrack.stop 会 release OpenCV cap；单测只验证调用语义。
        self.stop_calls += 1


class FakeSender:
    """aiortc sender 的最小替身，只暴露 cleanup helper 需要的 track 字段。"""

    def __init__(self, track: FakeTrack) -> None:
        self.track = track


class FakePeerConnection:
    """fake peer 避免引入 aiortc/cv2，让资源释放测试在普通 Python 环境可跑。"""

    def __init__(self, track: FakeTrack) -> None:
        self.track = track
        self.close_calls = 0

    def getSenders(self) -> list[FakeSender]:
        return [FakeSender(self.track)]

    async def close(self) -> None:
        self.close_calls += 1


class LocalWebrtcCameraSmokeCleanupTest(unittest.TestCase):
    """资源释放测试必须可用 unittest 直接跑，贴合 sprint 验收命令。"""

    def test_health_fail_open_without_psutil_or_temperature_files(self) -> None:
        """缺 psutil/温度 sysfs 时，/health 仍必须返回结构化诊断而不是抛异常。"""
        module = load_smoke_module()
        original_find_spec = module.importlib.util.find_spec

        def fake_find_spec(name: str):
            # 只模拟 psutil 缺失，避免把 aiohttp/aiortc/cv2/av 依赖状态改成测试假象。
            if name == "psutil":
                return None
            return original_find_spec(name)

        with (
            mock.patch.object(module.importlib.util, "find_spec", side_effect=fake_find_spec),
            mock.patch.object(module, "TEMPERATURE_GLOBS", ("/tmp/rober-missing-temp-*",)),
        ):
            payload = module.build_health(8088, "0")

        diagnostics = payload["system_diagnostics"]
        system_metrics = payload["system_metrics"]
        self.assertFalse(diagnostics["cpu"]["process_cpu_percent"]["available"])
        self.assertEqual(diagnostics["cpu"]["process_cpu_percent"]["reason"], "psutil_not_installed")
        self.assertIn(diagnostics["memory"]["available"], (True, False))
        self.assertFalse(diagnostics["temperature"]["available"])
        self.assertEqual(diagnostics["temperature"]["reason"], "temperature_files_not_found")
        self.assertIn("process_uptime_s", system_metrics)
        self.assertIn("temperature_unavailable_reason", system_metrics)
        self.assertEqual(system_metrics["temperature_unavailable_reason"], "temperature_files_not_found")
        self.assertIn("monotonic_s", diagnostics["sample"])
        self.assertGreaterEqual(diagnostics["sample"]["process_uptime_s"], 0)
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["sends_commands"])
        self.assertFalse(payload["robot_control_executed"])

    def test_media_summary_keeps_stable_frame_fields(self) -> None:
        """PC 轮询需要稳定摘要，不应依赖 active_peers 里的原始内部字段名。"""
        module = load_smoke_module()
        stats = {
            "peer_id": "peer-1",
            "created_ts_ms": module.now_ms() - 1000,
            "frames_read": 15,
            "camera_read_failures": 1,
            "last_frame_ts_ms": module.now_ms() - 25,
            "last_frame_width": 640,
            "last_frame_height": 480,
            "connection_state": "connected",
            "ice_connection_state": "completed",
            "signaling_state": "stable",
            "track_stopped": False,
        }

        summary = module.build_media_summary({"peer-1": stats}, None)

        peer_summary = summary["active_peers"]["peer-1"]
        self.assertEqual(peer_summary["frames_read"], 15)
        self.assertEqual(peer_summary["camera_read_failures"], 1)
        self.assertEqual(peer_summary["last_frame_width"], 640)
        self.assertEqual(peer_summary["last_frame_height"], 480)
        self.assertGreater(peer_summary["fps_estimate"], 0)
        self.assertEqual(summary["totals"]["active_frames_read"], 15)

        stability_metrics = module.build_stability_metrics(
            1,
            {
                **summary,
                "last_closed_peer": {
                    "stats": {
                        "frames_read": 9,
                        "fps_estimate": 14.2,
                        "camera_read_failures": 0,
                        "track_stopped": True,
                    }
                },
            },
        )
        self.assertEqual(stability_metrics["active_peer_count"], 1)
        self.assertEqual(stability_metrics["active_frames_read"], 15)
        self.assertEqual(stability_metrics["active_camera_read_failures"], 1)
        self.assertEqual(stability_metrics["last_closed_frames_read"], 9)
        self.assertEqual(stability_metrics["last_closed_fps_estimate"], 14.2)
        self.assertTrue(stability_metrics["last_closed_track_stopped"])

    def test_close_peer_connection_stops_local_track(self) -> None:
        """close route/异常清理共用 helper 时，必须先 stop track 再 close peer。"""
        module = load_smoke_module()
        track = FakeTrack()
        pc = FakePeerConnection(track)
        pcs = {"peer-1": pc}

        result = asyncio.run(module.close_peer_connection("peer-1", pc, pcs))

        self.assertEqual(track.stop_calls, 1)
        self.assertEqual(pc.close_calls, 1)
        self.assertEqual(pcs, {})
        self.assertEqual(result["stopped_tracks"], ["video"])
        self.assertEqual(result["track_stop_errors"], [])
        self.assertIsNone(result["close_error"])

    def test_browser_page_closes_server_peer_on_page_exit(self) -> None:
        """浏览器刷新/关闭也要 POST peer close，避免 409 卡住下一轮 browser smoke。"""
        module = load_smoke_module()
        page = module.html_page(8088, "0")

        self.assertIn("let serverPeerId = null", page)
        self.assertIn("navigator.sendBeacon", page)
        self.assertIn("/peers/${serverPeerId}/close", page)
        self.assertIn("pagehide", page)
        self.assertIn("beforeunload", page)

    def test_browser_page_binds_streamless_track_to_video(self) -> None:
        """Chrome 收到 streamless track 时也必须给 video 设置 MediaStream。"""
        module = load_smoke_module()
        page = module.html_page(8088, "0")

        self.assertIn("new MediaStream([event.track])", page)
        self.assertIn("video.play().catch", page)

    def test_browser_page_waits_ice_gathering_before_offer(self) -> None:
        """无 trickle 信令时，浏览器必须等 ICE candidate 收齐再 POST /offer。"""
        module = load_smoke_module()
        page = module.html_page(8088, "0")

        self.assertIn("waitForIceGatheringComplete", page)
        self.assertIn("iceGatheringState === 'complete'", page)
        self.assertIn("await waitForIceGatheringComplete(pc)", page)


if __name__ == "__main__":
    unittest.main()
