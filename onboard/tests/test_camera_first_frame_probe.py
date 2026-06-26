"""camera_first_frame_probe 的 no-hardware 单元测试。"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "camera_first_frame_probe.py"
SPEC = importlib.util.spec_from_file_location("camera_first_frame_probe", MODULE_PATH)
probe = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
sys.modules[SPEC.name] = probe
SPEC.loader.exec_module(probe)


class FakeCapture:
    """模拟 OpenCV capture，避免单元测试打开开发机真实摄像头。"""

    def __init__(self, device: str, opened: bool = True, frames: list[object] | None = None) -> None:
        self.device = device
        self.opened = opened
        self.frames = frames or []
        self.set_calls: list[tuple[int, object]] = []
        self.released = False

    def isOpened(self) -> bool:
        return self.opened

    def set(self, prop: int, value: object) -> bool:
        self.set_calls.append((prop, value))
        return True

    def read(self) -> tuple[bool, object | None]:
        if self.frames:
            return True, self.frames.pop(0)
        return False, None

    def release(self) -> None:
        self.released = True


class FakeCv2:
    """提供探针所需的最小 cv2 接口。"""

    CAP_PROP_FRAME_WIDTH = 3
    CAP_PROP_FRAME_HEIGHT = 4
    CAP_PROP_FPS = 5
    CAP_PROP_FOURCC = 6

    def __init__(self, capture: FakeCapture) -> None:
        self.capture = capture
        self.imwrite_calls: list[tuple[str, object]] = []

    def VideoCapture(self, device: str) -> FakeCapture:
        self.capture.device = device
        return self.capture

    def VideoWriter_fourcc(self, *letters: str) -> int:
        return sum(ord(letter) for letter in letters)

    def imwrite(self, path: str, frame: object) -> bool:
        self.imwrite_calls.append((path, frame))
        return True


class CameraFirstFrameProbeTests(unittest.TestCase):
    """锁住首帧探针的安全字段、指标和失败语义。"""

    def make_args(self, **overrides: object) -> SimpleNamespace:
        """构造默认参数，测试只覆盖关心的字段。"""
        values = {
            "device": "/dev/video1",
            "width": 640,
            "height": 480,
            "fps": 15.0,
            "fourcc": None,
            "timeout_s": 0.01,
            "read_call_timeout_s": 0.0,
            "interval_s": 0.001,
            "dark_threshold": 8.0,
            "sample_path": None,
            "include_backend_smoke": False,
        }
        values.update(overrides)
        return SimpleNamespace(**values)

    def test_missing_cv2_is_structured_fail_closed(self) -> None:
        """缺 OpenCV 时输出 JSON 失败，不发送运动、不打开串口。"""
        with mock.patch.object(probe, "import_cv2", side_effect=ImportError("missing cv2")):
            result = probe.probe_device(self.make_args())

        self.assertEqual("dependency_missing", result["status"])
        self.assertFalse(result["safe_to_control"])
        self.assertFalse(result["robot_control_executed"])
        self.assertFalse(result["opens_serial"])
        self.assertFalse(result["sends_motion_commands"])

    def test_open_failed_releases_capture(self) -> None:
        """设备打不开也必须释放 capture，避免后续现场复测被占用。"""
        capture = FakeCapture("/dev/video1", opened=False)
        fake_cv2 = FakeCv2(capture)

        with mock.patch.object(probe, "import_cv2", return_value=fake_cv2):
            result = probe.probe_device(self.make_args())

        self.assertEqual("open_failed", result["status"])
        self.assertFalse(result["open_ok"])
        self.assertTrue(capture.released)

    def test_first_frame_timeout_is_not_visible_content(self) -> None:
        """首帧超时不能升级可见内容证明。"""
        capture = FakeCapture("/dev/video1", opened=True, frames=[])
        fake_cv2 = FakeCv2(capture)

        with mock.patch.object(probe, "import_cv2", return_value=fake_cv2):
            result = probe.probe_device(self.make_args(fourcc="MJPG"))

        self.assertEqual("first_frame_timeout", result["status"])
        self.assertTrue(result["open_ok"])
        self.assertFalse(result["read_ok"])
        self.assertTrue(result["first_frame_timeout"])
        self.assertFalse(result["visible_content_proven"])
        self.assertTrue(capture.released)
        self.assertGreaterEqual(len(capture.set_calls), 4)

    def test_backend_smoke_runs_only_when_requested_after_timeout(self) -> None:
        """高级后端矩阵只在显式请求且 OpenCV 首帧失败后执行。"""
        capture = FakeCapture("/dev/video1", opened=True, frames=[])
        fake_cv2 = FakeCv2(capture)
        backend_result = {"executed": True, "status": "backend_no_frame_observed", "frame_observed": False}

        with mock.patch.object(probe, "import_cv2", return_value=fake_cv2):
            def backend_after_release(_args: object) -> dict[str, object]:
                self.assertTrue(capture.released)
                return backend_result

            with mock.patch.object(probe, "backend_smoke_probe", side_effect=backend_after_release) as backend_mock:
                result = probe.probe_device(self.make_args(fourcc="MJPG", include_backend_smoke=True))

        self.assertEqual("first_frame_timeout", result["status"])
        self.assertEqual(backend_result, result["backend_smoke"])
        backend_mock.assert_called_once()

    def test_backend_command_missing_tool_is_structured(self) -> None:
        """底层工具缺失时要结构化返回，而不是抛异常或影响安全字段。"""
        with mock.patch.object(probe.shutil, "which", return_value=None):
            result = probe.run_backend_command("v4l2_mjpg_mmap", ["v4l2-ctl", "--version"])

        self.assertFalse(result["available"])
        self.assertFalse(result["executed"])
        self.assertFalse(result["ok"])
        self.assertEqual(0, result["output_bytes"])

    def test_frame_read_with_visible_sample_proves_visual_material(self) -> None:
        """读到可见帧且写出样张后，才升级为可追溯视觉材料。"""
        frame = [
            [[0, 0, 0], [20, 40, 60]],
            [[80, 100, 120], [200, 210, 220]],
        ]
        capture = FakeCapture("/dev/video1", opened=True, frames=[frame])
        fake_cv2 = FakeCv2(capture)

        with mock.patch.object(probe, "import_cv2", return_value=fake_cv2):
            result = probe.probe_device(self.make_args(sample_path=Path("/tmp/sample.jpg")))

        self.assertEqual("frame_read", result["status"])
        self.assertTrue(result["read_ok"])
        self.assertEqual([2, 2, 3], result["frame_metrics"]["shape"])
        self.assertEqual(4, result["frame_metrics"]["pixel_count"])
        self.assertTrue(result["frame_metrics"]["visible_content_candidate"])
        self.assertTrue(result["sample_write_ok"])
        self.assertTrue(result["visible_content_proven"])
        self.assertEqual("/tmp/sample.jpg", fake_cv2.imwrite_calls[0][0])

    def test_main_prints_json(self) -> None:
        """CLI 入口保持机器可读输出，便于 SSH artifact 重定向。"""
        with mock.patch.object(probe, "probe_device", return_value={"schema": probe.SCHEMA, "status": "frame_read"}):
            with mock.patch("builtins.print") as print_mock:
                exit_code = probe.main(["--device", "/dev/video9", "--timeout-s", "0.01"])

        self.assertEqual(0, exit_code)
        printed = print_mock.call_args.args[0]
        self.assertIn('"schema": "trashbot.camera_first_frame_probe.v1"', printed)
        self.assertIn('"status": "frame_read"', printed)


if __name__ == "__main__":
    unittest.main()
