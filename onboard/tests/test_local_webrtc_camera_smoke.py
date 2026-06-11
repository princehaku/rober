"""local_webrtc_camera_smoke 的 no-hardware 单元测试。

这些测试不打开真实摄像头、不读串口、不发送运动命令。
目标是锁住 8088 camera service 的只读诊断、auto 选源和 fail-closed offer。
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "local_webrtc_camera_smoke.py"
SPEC = importlib.util.spec_from_file_location("local_webrtc_camera_smoke", MODULE_PATH)
camera = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
# dataclass 在 Python 3.13 会回查 sys.modules，所以路径加载必须先注册模块。
sys.modules[SPEC.name] = camera
SPEC.loader.exec_module(camera)


class LocalWebrtcCameraSmokeTests(unittest.TestCase):
    """覆盖 camera service 的安全边界和设备选择。"""

    def test_success_endpoint_schemas_match_historical_contracts(self) -> None:
        """成功响应 schema 要兼容历史真实服务 artifacts 和 PC catalog。"""
        self.assertEqual("trashbot.local_webrtc_camera_smoke.v1", camera.SCHEMA)
        self.assertEqual("trashbot.local_webrtc_camera_devices.v1", camera.DEVICES_SCHEMA)
        self.assertEqual("trashbot.local_webrtc_camera_offer.v1", camera.OFFER_SCHEMA)
        self.assertEqual("trashbot.local_webrtc_camera_close.v1", camera.CLOSE_SCHEMA)

    def test_auto_source_skips_cedrus_and_metadata_prefers_uvc_capture(self) -> None:
        """auto 必须选真实 UVC capture，不能落到 decoder 或 metadata。"""
        candidates = [
            {
                "path": "/dev/video0",
                "exists": True,
                "v4l2_name": "cedrus (platform:cedrus)",
                "sysfs_name": "cedrus",
                "is_video_capture": False,
                "is_uvc_or_usb": False,
                "is_decoder": True,
                "is_metadata": False,
            },
            {
                "path": "/dev/video1",
                "exists": True,
                "v4l2_name": "USB Composite Device: DV20 USB",
                "sysfs_name": "DV20 USB",
                "is_video_capture": True,
                "is_uvc_or_usb": True,
                "is_decoder": False,
                "is_metadata": False,
            },
            {
                "path": "/dev/video2",
                "exists": True,
                "v4l2_name": "USB Composite Device: DV20 USB",
                "sysfs_name": "metadata",
                "is_video_capture": False,
                "is_uvc_or_usb": True,
                "is_decoder": False,
                "is_metadata": True,
            },
        ]

        selection = camera.choose_auto_source(candidates)

        self.assertEqual("/dev/video1", selection["selected_path"])
        self.assertEqual("auto", selection["mode"])
        self.assertLess(
            next(item for item in selection["ranked"] if item["path"] == "/dev/video0")["score"],
            0,
        )
        self.assertLess(
            next(item for item in selection["ranked"] if item["path"] == "/dev/video2")["score"],
            0,
        )

    def test_explicit_source_is_respected_without_auto_rerank(self) -> None:
        """显式指定源时必须尊重 operator 输入，便于现场排查枚举漂移。"""
        selection = camera.resolve_video_source("/dev/video9")

        self.assertEqual("explicit", selection["mode"])
        self.assertEqual("/dev/video9", selection["selected_path"])
        self.assertEqual("/dev/video9", selection["requested_source"])

    def test_invalid_offer_fails_before_dependency_or_camera_access(self) -> None:
        """坏 offer 不应触发依赖 import 或 VideoCapture 打开。"""
        valid, reason = camera.validate_offer_payload({"type": "answer", "sdp": ""})

        self.assertFalse(valid)
        self.assertEqual("type_must_be_offer", reason)

    def test_missing_webrtc_dependencies_return_structured_fail_closed(self) -> None:
        """缺 aiortc/cv2/av 时 /offer 必须结构化失败，不能伪造图像。"""
        state = camera.CameraServiceState(video_source="/dev/video1", width=640, height=480, fps=15)
        offer = {"type": "offer", "sdp": "v=0\r\n"}

        with mock.patch.object(camera, "import_state", return_value={"aiortc": False, "cv2": False, "av": False}):
            status, payload = camera.asyncio.run(state.create_answer(offer))

        self.assertEqual(503, status)
        self.assertEqual("dependency_missing", payload["error"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["robot_control_executed"])
        self.assertFalse(payload["delivery_success"])
        self.assertFalse(payload["primary_actions_enabled"])

    def test_devices_enumeration_uses_readonly_v4l2_commands(self) -> None:
        """设备枚举只能调用只读 v4l2 命令，不写 controls。"""
        calls: list[list[str]] = []

        def fake_command(args: list[str], timeout_s: float = 0.0) -> dict[str, object]:
            calls.append(args)
            if args == ["v4l2-ctl", "--list-devices"]:
                return {
                    "available": True,
                    "stdout": "USB Composite Device: DV20 USB:\n\t/dev/video1\n",
                    "stderr": "",
                    "returncode": 0,
                }
            return {"available": True, "stdout": "Video Capture\nMJPG", "stderr": "", "returncode": 0}

        with mock.patch.object(camera.glob, "glob", return_value=["/dev/video1"]):
            with mock.patch.object(camera, "run_readonly_command", side_effect=fake_command):
                with mock.patch.object(camera, "read_sysfs_video_name", return_value="DV20 USB"):
                    snapshot = camera.collect_video_candidates()

        self.assertEqual(["/dev/video1"], snapshot["paths"])
        self.assertFalse(snapshot["writes_controls"])
        self.assertFalse(snapshot["opens_serial"])
        self.assertFalse(snapshot["sends_motion_commands"])
        flattened = " ".join(" ".join(call) for call in calls)
        self.assertIn("--list-devices", flattened)
        self.assertIn("--all", flattened)
        self.assertIn("--list-formats-ext", flattened)
        self.assertNotIn("--set-ctrl", flattened)

    def test_uvc_capture_with_metadata_capability_still_counts_as_video(self) -> None:
        """DV20 这类 UVC 复合设备会列出 metadata capability，但 /dev/video1 仍是图像节点。"""

        def fake_command(args: list[str], timeout_s: float = 0.0) -> dict[str, object]:
            if "--all" in args:
                return {
                    "available": True,
                    "stdout": "\n".join(
                        [
                            "Driver name      : uvcvideo",
                            "Card type        : USB Composite Device: DV20 USB",
                            "Capabilities     : Video Capture Metadata Capture Streaming",
                            "Device Caps      : Video Capture Streaming",
                            "Format Video Capture:",
                            "Pixel Format      : 'YUYV' (YUYV 4:2:2)",
                        ]
                    ),
                    "stderr": "",
                    "returncode": 0,
                }
            return {
                "available": True,
                "stdout": "\n".join(
                    [
                        "ioctl: VIDIOC_ENUM_FMT",
                        "Type: Video Capture",
                        "[0]: 'MJPG' (Motion-JPEG, compressed)",
                        "[1]: 'YUYV' (YUYV 4:2:2)",
                    ]
                ),
                "stderr": "",
                "returncode": 0,
            }

        with mock.patch.object(camera.os.path, "exists", return_value=True):
            with mock.patch.object(camera, "run_readonly_command", side_effect=fake_command):
                with mock.patch.object(camera, "read_sysfs_video_name", return_value="USB Composite Device: DV20 USB"):
                    candidate = camera.build_device_candidate("/dev/video1", "USB Composite Device: DV20 USB")

        self.assertTrue(candidate["is_video_capture"])
        self.assertFalse(candidate["is_metadata"])
        self.assertTrue(candidate["is_uvc_or_usb"])

    def test_devices_success_schema_uses_historical_contract(self) -> None:
        """`/devices` 成功响应保持历史 schema，不从 health schema 派生。"""
        state = camera.CameraServiceState(video_source="auto", width=640, height=480, fps=15)
        snapshot = {
            "paths": ["/dev/video1"],
            "v4l2_list_devices": {"available": True},
            "candidates": [
                {
                    "path": "/dev/video1",
                    "exists": True,
                    "is_video_capture": True,
                    "is_uvc_or_usb": True,
                    "is_decoder": False,
                    "is_metadata": False,
                    "v4l2_name": "USB camera",
                    "sysfs_name": "USB camera",
                }
            ],
            "writes_controls": False,
            "opens_serial": False,
            "sends_motion_commands": False,
        }

        with mock.patch.object(camera, "collect_video_candidates", return_value=snapshot):
            payload = state.current_devices()

        self.assertEqual("trashbot.local_webrtc_camera_devices.v1", payload["schema"])
        self.assertEqual("/dev/video1", payload["video_source"])
        self.assertFalse(payload["safe_to_control"])

    def test_close_success_schema_uses_historical_contract(self) -> None:
        """`/peers/{peer_id}/close` 成功响应保持历史 close schema。"""
        class FakePc:
            async def close(self) -> None:
                self.closed = True

        class FakeTrack:
            def stop(self) -> None:
                self.stopped = True

        class FakeCapture:
            def release(self) -> None:
                self.released = True

        state = camera.CameraServiceState(video_source="/dev/video1", width=640, height=480, fps=15)
        peer = camera.PeerRecord(
            peer_id="abc123",
            pc=FakePc(),
            track=FakeTrack(),
            capture=FakeCapture(),
            source="/dev/video1",
        )
        peer.frames_read = 2
        state.peers[peer.peer_id] = peer

        status, payload = camera.asyncio.run(state.close_peer(peer.peer_id))

        self.assertEqual(200, status)
        self.assertEqual("trashbot.local_webrtc_camera_close.v1", payload["schema"])
        self.assertEqual("closed", payload["status"])
        self.assertEqual(0, payload["active_peer_count"])
        self.assertFalse(payload["safe_to_control"])

    def test_health_exposes_required_safety_and_selection_fields(self) -> None:
        """health 必须能被 PC 诊断消费，同时保持控制字段关闭。"""
        state = camera.CameraServiceState(video_source="auto", width=640, height=480, fps=15)
        snapshot = {
            "candidates": [
                {
                    "path": "/dev/video1",
                    "exists": True,
                    "is_video_capture": True,
                    "is_uvc_or_usb": True,
                    "is_decoder": False,
                    "is_metadata": False,
                    "v4l2_name": "USB camera",
                    "sysfs_name": "USB camera",
                }
            ]
        }

        with mock.patch.object(camera, "collect_video_candidates", return_value=snapshot):
            payload = state.health()

        self.assertEqual(camera.SCHEMA, payload["schema"])
        self.assertEqual(camera.APP_NAME, payload["app"])
        self.assertEqual("ready", payload["status"])
        self.assertEqual("/dev/video1", payload["video_source"])
        self.assertEqual("auto", payload["video_source_mode"])
        self.assertEqual(0, payload["active_peer_count"])
        self.assertEqual(0, payload["active_frames_read"])
        self.assertEqual(0, payload["active_camera_read_failures"])
        self.assertIn("system_diagnostics", payload)
        self.assertIn("media_diagnostics", payload)
        self.assertIn("source_candidates_summary", payload)
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["robot_control_executed"])


if __name__ == "__main__":
    unittest.main()
