"""camera_usb_recovery_smoke 的 no-hardware 单元测试。"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "camera_usb_recovery_smoke.py"
SPEC = importlib.util.spec_from_file_location("camera_usb_recovery_smoke", MODULE_PATH)
recovery = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
sys.modules[SPEC.name] = recovery
SPEC.loader.exec_module(recovery)


class CameraUsbRecoverySmokeTests(unittest.TestCase):
    """锁住相机恢复脚本的现场动作分类，不碰真实 USB 设备。"""

    def test_topology_speed_uses_target_usb_device(self) -> None:
        """存在多个 Video 接口时，只能读取目标 USB 地址的速率。"""
        topology = """/:  Bus 06.Port 1: Dev 1, Class=root_hub, Driver=ohci-platform/1p, 12M
    |__ Port 1: Dev 2, If 0, Class=Video, Driver=uvcvideo, 12M
/:  Bus 03.Port 1: Dev 1, Class=root_hub, Driver=ehci-platform/1p, 480M
    |__ Port 1: Dev 19, If 0, Class=Video, Driver=uvcvideo, 480M
"""

        self.assertEqual("480M", recovery.usb_video_speed_from_topology(topology, "3-1"))
        self.assertEqual("12M", recovery.usb_video_speed_from_topology(topology, "6-1"))

    def test_high_speed_zero_byte_failure_points_to_known_good_uvc(self) -> None:
        """480M 高速口仍无帧时，下一步不应继续要求换高速口。"""
        action = recovery.camera_recovery_next_action(False, "480M")

        self.assertEqual("check_usb_cable_port_power_or_known_good_uvc", action["next_action"])
        self.assertEqual("high_speed_zero_byte_no_frame", action["stream_failure_class"])
        self.assertTrue(action["usb_high_speed_observed"])
        self.assertIn("known-good UVC", action["next_action_plain"])

    def test_full_speed_failure_still_points_to_high_speed_port(self) -> None:
        """12M/full-speed 仍是带宽硬 blocker，应该先换高速口/线。"""
        action = recovery.camera_recovery_next_action(False, "12M")

        self.assertEqual("move_camera_to_high_speed_usb_port_or_powered_hub", action["next_action"])
        self.assertEqual("full_speed_no_frame", action["stream_failure_class"])
        self.assertFalse(action["usb_high_speed_observed"])


if __name__ == "__main__":
    unittest.main()
