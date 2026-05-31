#!/usr/bin/env python3
"""local_webrtc_camera_smoke.py 的轻量资源释放测试。"""

from __future__ import annotations

import asyncio
import importlib.util
import unittest
from pathlib import Path


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
