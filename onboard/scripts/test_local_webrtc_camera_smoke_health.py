#!/usr/bin/env python3
"""local_webrtc_camera_smoke health 当前状态优先级测试。"""

from __future__ import annotations

import importlib.util
import subprocess
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
    def install_single_uvc_candidate(self, module: Any) -> tuple[Any, Any]:
        """测试里固定一个 DV20 UVC 候选，避免依赖开发机真实 /dev/video。"""
        original_collect_video_candidates = module.collect_video_candidates
        original_collect_device_usage = module.collect_device_usage
        original_collect_uvc_kernel_diagnostics = module.collect_uvc_kernel_diagnostics
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
        module.collect_uvc_kernel_diagnostics = lambda selected_path, selected_candidate: {
            "status": "uvc_kernel_seen_without_recent_transport_errors",
            "selected_path": selected_path,
            "selected_name": "DV20 USB",
            "transport_error_count": 0,
            "opens_camera": False,
            **module.proof_flags(),
        }
        return original_collect_video_candidates, original_collect_device_usage, original_collect_uvc_kernel_diagnostics

    def test_current_first_frame_failure_overrides_stale_success(self) -> None:
        """当前同源首帧失败时，不允许历史成功帧把 health 标成 ready。"""
        module = load_camera_module()
        original_collect_video_candidates, original_collect_device_usage, original_collect_uvc_kernel_diagnostics = self.install_single_uvc_candidate(module)
        try:
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
            module.collect_uvc_kernel_diagnostics = original_collect_uvc_kernel_diagnostics

    def test_health_releases_stale_shared_capture_without_active_peer(self) -> None:
        """无人观看但共享 capture 残留时，health 要释放句柄，避免 8088 自己占用 UVC。"""
        module = load_camera_module()
        original_collect_video_candidates, original_collect_device_usage, original_collect_uvc_kernel_diagnostics = self.install_single_uvc_candidate(module)

        class FakeCapture:
            def __init__(self) -> None:
                self.released = False

            def release(self) -> None:
                self.released = True

        try:
            fake_capture = FakeCapture()
            state = module.CameraServiceState("auto", 640, 480, 15)
            shared = module.SharedCameraCapture(
                source="/dev/video1",
                capture=fake_capture,
                width=640,
                height=480,
                fps=15,
                fourcc="YUYV",
                created_ts_ms=module.now_ms() - module.STALE_SHARED_CAPTURE_NO_FRAME_MAX_AGE_MS - 1000,
            )
            # 模拟现场看到的异常：active peer 为 0，但 ref_count 残留导致 /dev/video1 busy。
            shared.ref_count = 1
            state.shared_captures["/dev/video1|/dev/video1|default"] = shared

            health: dict[str, Any] = state.health()

            self.assertTrue(fake_capture.released)
            self.assertEqual(state.shared_captures, {})
            released = health["stale_shared_captures_released"]
            self.assertEqual(len(released), 1)
            self.assertTrue(released[0]["stale_no_frame"])
            self.assertEqual(health["media_diagnostics"]["shared_captures"], {})
        finally:
            module.collect_video_candidates = original_collect_video_candidates
            module.collect_device_usage = original_collect_device_usage
            module.collect_uvc_kernel_diagnostics = original_collect_uvc_kernel_diagnostics

    def test_uvc_kernel_transport_error_refines_no_frame_diagnosis(self) -> None:
        """dmesg 已有 UVC/USB 传输错误时，health 要把根因说成链路错误而非单纯无帧。"""
        module = load_camera_module()
        original_collect_video_candidates, original_collect_device_usage, original_collect_uvc_kernel_diagnostics = self.install_single_uvc_candidate(module)
        module.collect_uvc_kernel_diagnostics = lambda selected_path, selected_candidate: {
            "status": "uvc_usb_transport_errors_observed",
            "selected_path": selected_path,
            "selected_name": "DV20 USB",
            "bus_info": "usb-5310000.usb-1",
            "transport_error_count": 2,
            "latest_transport_error": "uvcvideo 3-1:1.1: Failed to resubmit video URB (-1).",
            "opens_camera": False,
            **module.proof_flags(),
        }
        try:
            state = module.CameraServiceState("auto", 640, 480, 15)
            state.last_offer_error = {
                "video_source": "/dev/video1",
                "failure_reason": "first_frame_total_timeout",
            }

            health: dict[str, Any] = state.health()

            self.assertEqual(health["source_diagnosis"]["status"], "uvc_transport_error_not_exclusive")
            self.assertEqual(health["uvc_kernel_diagnostics"]["status"], "uvc_usb_transport_errors_observed")
            self.assertIn("UVC/USB", health["source_diagnosis"]["plain_hint"])
            self.assertEqual(health["source_diagnosis"]["uvc_kernel_diagnostics_status"], "uvc_usb_transport_errors_observed")
        finally:
            module.collect_video_candidates = original_collect_video_candidates
            module.collect_device_usage = original_collect_device_usage
            module.collect_uvc_kernel_diagnostics = original_collect_uvc_kernel_diagnostics

    def test_uvc_kernel_diagnostics_reads_dmesg_tail_errors(self) -> None:
        """dmesg 很长时也要看尾部近期 UVC 错误，不能只读开头。"""
        module = load_camera_module()
        original_which = module.shutil.which
        original_run = module.subprocess.run
        module.shutil.which = lambda command: "/bin/dmesg" if command == "dmesg" else original_which(command)

        def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
            text = "\n".join(["old line"] * 1000 + [
                "[1.0] usb 3-1: Found UVC 1.00 device USB Composite Device",
                "[2.0] uvcvideo 3-1:1.1: Failed to query (129) UVC probe control : -71 (exp. 26).",
                "[3.0] uvcvideo 3-1:1.1: Failed to resubmit video URB (-1).",
            ])
            return subprocess.CompletedProcess(args[0], 0, stdout=text, stderr="")

        module.subprocess.run = fake_run
        try:
            diagnostics = module.collect_uvc_kernel_diagnostics(
                "/dev/video1",
                {
                    "v4l2_name": "DV20 USB",
                    "readonly_probe": {
                        "v4l2_all": {
                            "stdout": "Bus info         : usb-5310400.usb-1\n",
                        },
                    },
                },
            )

            self.assertEqual(diagnostics["status"], "uvc_usb_transport_errors_observed")
            self.assertEqual(diagnostics["transport_error_count"], 2)
            self.assertIn("Failed to resubmit video URB", diagnostics["latest_transport_error"])
        finally:
            module.shutil.which = original_which
            module.subprocess.run = original_run

    def test_recent_first_frame_failure_cools_down_auto_mjpeg_retry(self) -> None:
        """自动 MJPEG 最近刚失败时不应马上重开 UVC，手动 probe 仍可另走独立入口。"""
        module = load_camera_module()
        state = module.CameraServiceState("auto", 640, 480, 15)
        state.last_offer_error = {
            "video_source": "/dev/video1",
            "failure_reason": "first_frame_total_timeout",
            "generated_at_ms": module.now_ms() - 1000,
        }

        recent = state.recent_first_frame_failure("/dev/video1", cooldown_ms=30_000)
        self.assertIsNotNone(recent)
        self.assertTrue(recent["cooldown_active"])
        self.assertGreater(recent["retry_after_ms"], 0)

        state.last_offer_error["generated_at_ms"] = module.now_ms() - 31_000
        self.assertIsNone(state.recent_first_frame_failure("/dev/video1", cooldown_ms=30_000))


if __name__ == "__main__":
    unittest.main()
