#!/usr/bin/env python3
"""camera_usb_recovery_smoke USB 地址识别测试。"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_PATH = SCRIPT_DIR / "camera_usb_recovery_smoke.py"


def load_recovery_module() -> Any:
    """按脚本路径加载模块，避免测试依赖真实 USB 设备。"""
    spec = importlib.util.spec_from_file_location("camera_usb_recovery_smoke_under_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("camera_usb_recovery_smoke.py module spec was not created")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CameraUsbRecoverySmokeTest(unittest.TestCase):
    def test_detect_usb_device_uses_video_sysfs_kernel_address(self) -> None:
        """Orange Pi v4l2 bus_info 是平台地址时，也要从 sysfs 找到真正的 `6-1`。"""
        module = load_recovery_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sys_video_root = root / "sys" / "class" / "video4linux"
            sys_usb_root = root / "sys" / "bus" / "usb" / "devices"
            real_video_device = root / "devices" / "platform" / "soc" / "5310400.usb" / "usb6" / "6-1" / "6-1:1.0"
            (sys_video_root / "video1").mkdir(parents=True)
            (sys_usb_root / "6-1").mkdir(parents=True)
            real_video_device.mkdir(parents=True)
            (sys_video_root / "video1" / "device").symlink_to(real_video_device)

            detected = module.detect_usb_device(
                "/dev/video1",
                "fallback",
                sys_video_root=sys_video_root,
                sys_usb_root=sys_usb_root,
            )

        self.assertEqual(detected, "6-1")

    def test_detect_usb_device_rejects_platform_bus_info_without_sysfs_device(self) -> None:
        """`5310400.usb-1` 不能写 authorized，找不到 sysfs 设备时必须回退。"""
        module = load_recovery_module()
        original_run_command = module.run_command
        module.run_command = lambda *args, **kwargs: {"stdout": "Bus info         : usb-5310400.usb-1\n", "stderr": ""}
        try:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                detected = module.detect_usb_device(
                    "/dev/video1",
                    "6-1",
                    sys_video_root=root / "missing-video",
                    sys_usb_root=root / "missing-usb",
                )
        finally:
            module.run_command = original_run_command

        self.assertEqual(detected, "6-1")

    def test_reset_uvc_quirks_records_before_after(self) -> None:
        """恢复脚本要把异常 quirks 复位证据写进 JSON，便于现场复盘。"""
        module = load_recovery_module()
        with tempfile.TemporaryDirectory() as tmp:
            parameters_root = Path(tmp) / "uvcvideo" / "parameters"
            parameters_root.mkdir(parents=True)
            (parameters_root / "quirks").write_text("4294967295", encoding="utf-8")
            (parameters_root / "nodrop").write_text("0", encoding="utf-8")
            (parameters_root / "timeout").write_text("5000", encoding="utf-8")

            before = module.read_uvc_module_parameters(parameters_root)
            reset = module.reset_uvc_quirks(parameters_root)
            after = module.read_uvc_module_parameters(parameters_root)

        self.assertEqual(before["quirks"], "4294967295")
        self.assertTrue(reset["ok"])
        self.assertEqual(reset["before"], "4294967295")
        self.assertEqual(reset["after"], "0")
        self.assertEqual(after["quirks"], "0")


if __name__ == "__main__":
    unittest.main()
