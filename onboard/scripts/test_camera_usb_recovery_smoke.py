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

    def test_reload_uvc_module_uses_fixed_modprobe_arguments(self) -> None:
        """模块重载必须固定 argv，不能把 PC 请求内容拼进 root 命令。"""
        module = load_recovery_module()
        original_run_command = module.run_command
        original_read_uvc_module_parameters = module.read_uvc_module_parameters
        original_list_video_nodes = module.list_video_nodes
        original_sleep = module.time.sleep
        calls: list[list[str]] = []

        def fake_run_command(argv: list[str], **_kwargs: object) -> dict[str, object]:
            calls.append(argv)
            return {"stdout": "", "stderr": "", "returncode": 0, "timed_out": False}

        module.run_command = fake_run_command
        module.read_uvc_module_parameters = lambda *args, **kwargs: {
            "quirks": "0",
            "nodrop": "0",
            "timeout": "5000",
        }
        module.list_video_nodes = lambda *args, **kwargs: ["/dev/video1", "/dev/video2"]
        module.time.sleep = lambda *_args, **_kwargs: None
        try:
            result = module.reload_uvc_module("/dev/video1", "3-1")
        finally:
            module.run_command = original_run_command
            module.read_uvc_module_parameters = original_read_uvc_module_parameters
            module.list_video_nodes = original_list_video_nodes
            module.time.sleep = original_sleep

        self.assertTrue(result["ok"])
        self.assertEqual(result["module"], "uvcvideo")
        self.assertEqual(calls[0], ["lsof", "/dev/video1"])
        self.assertEqual(calls[1], ["modprobe", "-r", "uvcvideo"])
        self.assertEqual(calls[2], ["modprobe", "uvcvideo", "quirks=0", "nodrop=0", "timeout=5000"])
        self.assertEqual(result["parameters_after_load"]["timeout"], "5000")

    def test_usbreset_uses_sysfs_bus_device_target(self) -> None:
        """usbreset 目标必须来自 sysfs busnum/devnum，避免 PC body 注入 USB 目标。"""
        module = load_recovery_module()
        original_run_command = module.run_command
        original_sleep = module.time.sleep
        calls: list[list[str]] = []

        def fake_run_command(argv: list[str], **_kwargs: object) -> dict[str, object]:
            calls.append(argv)
            return {"stdout": "Resetting USB Composite Device ... ok\n", "stderr": "", "returncode": 0, "timed_out": False}

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sys_usb_root = root / "sys" / "bus" / "usb" / "devices"
            sys_video_root = root / "sys" / "class" / "video4linux"
            dev_root = root / "dev"
            usb_root = sys_usb_root / "3-1"
            usb_root.mkdir(parents=True)
            sys_video_root.joinpath("video1").mkdir(parents=True)
            dev_root.mkdir(parents=True)
            (usb_root / "busnum").write_text("3", encoding="utf-8")
            (usb_root / "devnum").write_text("4", encoding="utf-8")
            module.run_command = fake_run_command
            module.time.sleep = lambda *_args, **_kwargs: None
            try:
                result = module.reset_usb_device_with_usbreset(
                    "/dev/video1",
                    "3-1",
                    sys_usb_root=sys_usb_root,
                    sys_video_root=sys_video_root,
                    dev_root=dev_root,
                )
            finally:
                module.run_command = original_run_command
                module.time.sleep = original_sleep

        self.assertTrue(result["ok"])
        self.assertEqual(result["target"]["target"], "003/004")
        self.assertEqual(calls[0], ["lsof", "/dev/video1"])
        self.assertEqual(calls[1], ["usbreset", "003/004"])

    def test_reset_v4l2_controls_only_writes_advertised_defaults(self) -> None:
        """恢复脚本应重置 DV20 常见控制项，但不能把未公开控制硬塞给设备。"""
        module = load_recovery_module()
        original_run_command = module.run_command
        calls: list[list[str]] = []

        def fake_run_command(argv: list[str], **_kwargs: object) -> dict[str, object]:
            calls.append(argv)
            if argv[-1] == "-L":
                return {
                    "stdout": "\n".join([
                        "brightness 0x00980900 (int)",
                        "contrast 0x00980901 (int)",
                        "auto_exposure 0x009a0901 (menu)",
                    ]),
                    "stderr": "",
                    "returncode": 0,
                }
            return {"stdout": "", "stderr": "", "returncode": 0}

        module.run_command = fake_run_command
        try:
            result = module.reset_v4l2_controls("/dev/video1")
        finally:
            module.run_command = original_run_command

        written_controls = [argv[-1].split("=", 1)[0] for argv in calls if "--set-ctrl" in argv]
        skipped_controls = [action["control"] for action in result["actions"] if action.get("skipped")]

        self.assertEqual(written_controls, ["brightness", "contrast", "auto_exposure"])
        self.assertIn("saturation", skipped_controls)
        self.assertTrue(result["ok"])
        self.assertEqual(result["attempted_count"], 3)
        self.assertEqual(result["applied_count"], 3)

    def test_set_usb_power_on_disables_device_and_root_hub_autosuspend(self) -> None:
        """恢复脚本必须真的写 autosuspend，不能只把 control 置为 on。"""
        module = load_recovery_module()
        with tempfile.TemporaryDirectory() as tmp:
            sys_usb_root = Path(tmp) / "sys" / "bus" / "usb" / "devices"
            for name in ("3-1", "usb3"):
                power = sys_usb_root / name / "power"
                power.mkdir(parents=True)
                (power / "control").write_text("auto", encoding="utf-8")
                (power / "autosuspend").write_text("2", encoding="utf-8")
                (power / "autosuspend_delay_ms").write_text("2000", encoding="utf-8")

            actions = module.set_usb_power_on("3-1", sys_usb_root=sys_usb_root)

        written = {(Path(action["target"]).name, action["setting"]): action for action in actions}
        for target_name in ("3-1", "usb3"):
            self.assertEqual("on", written[(target_name, "power/control")]["after"])
            self.assertEqual("-1", written[(target_name, "power/autosuspend")]["after"])
            self.assertEqual("-1", written[(target_name, "power/autosuspend_delay_ms")]["after"])
            self.assertTrue(written[(target_name, "power/control")]["ok"])

    def test_stream_once_classifies_streamon_success_zero_byte_timeout(self) -> None:
        """STREAMON 成功但 select timeout/0 字节时，要和真正 STREAMON 失败区分开。"""
        module = load_recovery_module()
        original_run_command = module.run_command
        module.run_command = lambda *args, **kwargs: {
            "stdout": "VIDIOC_STREAMON returned 0 (Success)\nselect timeout\n",
            "stderr": "",
            "returncode": 0,
            "timed_out": False,
        }
        try:
            with tempfile.TemporaryDirectory() as tmp:
                result = module.stream_once(
                    "/dev/video1",
                    640,
                    480,
                    "MJPG",
                    30,
                    Path(tmp) / "frame.raw",
                )
        finally:
            module.run_command = original_run_command

        self.assertEqual(result["status"], "streamon_success_zero_byte_no_frame")
        self.assertTrue(result["streamon_observed"])
        self.assertTrue(result["streamon_success"])
        self.assertTrue(result["select_timeout"])
        self.assertTrue(result["zero_byte_no_frame"])
        self.assertFalse(result["streamon_error"])
        self.assertFalse(result["ok"])

    def test_high_speed_no_frame_requires_known_good_uvc_comparison(self) -> None:
        """高速 USB 仍零帧时，下一步要转向输入信号/供电/known-good UVC，而不是继续调端口。"""
        module = load_recovery_module()

        action = module.camera_recovery_next_action(False, "480M")

        self.assertEqual(action["stream_failure_class"], "high_speed_zero_byte_no_frame")
        self.assertTrue(action["usb_high_speed_observed"])
        self.assertTrue(action["software_capture_exhausted"])
        self.assertTrue(action["known_good_uvc_required"])
        self.assertTrue(action["camera_input_signal_check_required"])
        self.assertIn("STREAMON 成功", action["next_action_plain"])

    def test_audio_unbind_actions_are_rebound_after_stream_probe(self) -> None:
        """临时解绑 USB audio 后必须按本次记录恢复，避免 recovery smoke 改变现场设备状态。"""
        module = load_recovery_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sys_usb_root = root / "sys" / "bus" / "usb" / "devices"
            audio_driver = root / "sys" / "bus" / "usb" / "drivers" / "snd-usb-audio"
            iface = sys_usb_root / "3-1:1.2"
            iface.mkdir(parents=True)
            audio_driver.mkdir(parents=True)
            (audio_driver / "unbind").write_text("", encoding="utf-8")
            (audio_driver / "bind").write_text("", encoding="utf-8")
            (iface / "driver").symlink_to(audio_driver)

            unbind_actions = module.unbind_audio_interfaces(
                "3-1",
                sys_usb_root=sys_usb_root,
                driver_unbind=audio_driver / "unbind",
            )
            rebind_actions = module.rebind_audio_interfaces(
                unbind_actions,
                driver_bind=audio_driver / "bind",
            )
            driver_status = module.audio_interface_driver_status(
                {"3-1:1.2"},
                sys_usb_root=sys_usb_root,
            )

        self.assertEqual([action["value"] for action in unbind_actions], ["3-1:1.2"])
        self.assertTrue(all(action["ok"] for action in unbind_actions))
        self.assertEqual([action["value"] for action in rebind_actions], ["3-1:1.2"])
        self.assertTrue(all(action["ok"] for action in rebind_actions))
        self.assertTrue(driver_status["3-1:1.2"]["bound_to_snd_usb_audio"])


if __name__ == "__main__":
    unittest.main()
