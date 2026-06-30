#!/usr/bin/env python3
"""local_webrtc_camera_smoke health 当前状态优先级测试。"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_PATH = SCRIPT_DIR / "local_webrtc_camera_smoke.py"


def load_camera_module():
    """按脚本路径加载模块，避免测试依赖上车端服务已经启动。"""
    spec = importlib.util.spec_from_file_location("local_webrtc_camera_smoke_under_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("local_webrtc_camera_smoke.py module spec was not created")
    module = importlib.util.module_from_spec(spec)
    # dataclass 在 Python 3.13 会读取 sys.modules[__module__]，文件路径加载时要先注册。
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class LocalWebrtcCameraSmokeHealthTest(unittest.TestCase):
    def test_current_first_frame_failure_overrides_stale_success(self) -> None:
        """当前同源首帧失败时，不允许历史成功帧把 health 标成 ready。"""
        module = load_camera_module()
        original_collect_video_candidates = module.collect_video_candidates
        original_collect_device_usage = module.collect_device_usage
        try:
            module.collect_video_candidates = lambda: {
                "generated_at_ms": 1,
                "paths": ["/dev/video1"],
                "candidates": [
                    {
                        "path": "/dev/video1",
                        "exists": True,
                        "v4l2_name": "DV20 USB",
                        "sysfs_name": "USB Composite Device: DV20 USB",
                        "is_video_capture": True,
                        "is_uvc_or_usb": True,
                        "is_decoder": False,
                        "is_metadata": False,
                        "formats_summary": "MJPG 640x480",
                    }
                ],
            }
            module.collect_device_usage = lambda path: {
                "checked": True,
                "device": path,
                "status": "not_in_use",
                "owner_count": 0,
                "other_owner_count": 0,
                "owners": [],
                "opens_camera": False,
            }
            state = module.CameraServiceState("auto", 640, 480, 15)
            # 历史成功帧只证明过去读到过画面，不能覆盖当前首帧失败。
            state.last_successful_frame = {
                "source": "/dev/video1",
                "channel": "mjpeg",
                "observed_at_ms": 1,
                "width": 640,
                "height": 480,
            }
            state.last_offer_error = {
                "video_source": "/dev/video1",
                "failure_reason": "first_frame_total_timeout",
            }

            health: dict[str, Any] = state.health()

            self.assertEqual(health["status"], "source_first_frame_failed")
            self.assertEqual(health["source_readiness"], "first_frame_failed")
            self.assertEqual(health["source_diagnosis"]["status"], "uvc_no_frame_not_exclusive")
            self.assertNotEqual(health["source_diagnosis"]["status"], "first_frame_observed")
        finally:
            module.collect_video_candidates = original_collect_video_candidates
            module.collect_device_usage = original_collect_device_usage


if __name__ == "__main__":
    unittest.main()
