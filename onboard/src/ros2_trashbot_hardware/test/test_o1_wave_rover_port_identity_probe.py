import importlib.util
import io
import json
import stat
from pathlib import Path
import unittest
from unittest import mock


# 测试边界说明：本文件锁定 no-motion 端口身份 readiness contract。
# 测试边界说明：fake inspector 不访问真实 /dev，避免 CI 误触硬件。
# 测试边界说明：probe 只允许 glob/readlink/stat/sysfs 文本读取。
# 测试边界说明：测试显式拒绝 open 串口和任何 serial.write 路径。
# 测试边界说明：STC/ttyACM 只能作为风险线索，不能当 WAVE ROVER 定论。
# 测试边界说明：LiDAR 线索来自 vendor README/udev 口径，不代表现场已验证。
# 测试边界说明：目标端口缺失必须输出机器字段，不能抛异常。
# 测试边界说明：fail-closed 字段必须在所有路径保持 false。
# 测试边界说明：CLI once-json 用 stdout，匹配远端 SSH stdin 运行方式。
# 测试边界说明：所有 fake sysfs 内容只是 contract fixture，不是硬件证据。
# 测试边界说明：candidate inventory 暴露 by-id/by-path，但不打开目标端口。
# 测试边界说明：next_required_checks 是现场检查清单，不替代 HIL。
# 测试边界说明：blocked_commands_not_sent 防止 T=130 被混入本 probe。
# 测试边界说明：WAVE ROVER ESP32 只允许 possible，不允许 proven。
# 测试边界说明：测试保持脚本单文件加载，不要求 scripts 变 Python package。
# 测试边界说明：如果未来补 HIL，也不应让本 readiness probe 发送命令。
# 测试边界说明：端口身份和串口反馈分开测试，是为了避免 probe 语义膨胀。
# 测试边界说明：T=130 在本文件中必须是 blocked，不是 allowed。
# 测试边界说明：LiDAR vendor/product fixture 只验证风险分类，不验证雷达功能。
# 测试边界说明：STC fixture 只验证信息不足，不验证 WAVE ROVER 身份。
# 测试边界说明：fake symlink 覆盖 by-id/by-path 同 realpath 场景。
# 测试边界说明：fake sysfs 覆盖 USB 文本读取，不覆盖真实内核拓扑。
# 测试边界说明：CLI 测试 patch inspector，防止读取开发机真实 /dev。
# 测试边界说明：所有断言都围绕机器字段，避免依赖人工 prose。
# 测试边界说明：缺口和 next checks 是交付内容，不是测试噪声。
# 测试边界说明：如果未来字段扩展，安全 false 字段仍必须优先锁定。
# 测试边界说明：注释保留中文，是项目硬件脚本审查要求的一部分。
# 测试边界说明：测试不创建 artifact，避免 fake 材料混入现场证据。
SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "o1_wave_rover_port_identity_probe.py"


def _load_probe_module():
    # spec 加载只执行模块定义；不会触发 __main__ 或访问真实设备。
    spec = importlib.util.spec_from_file_location("o1_wave_rover_port_identity_probe", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeInspector:
    """fake 文件系统只提供只读元数据，用于证明 probe 不碰真实串口。"""

    def __init__(self, *, paths=None, symlinks=None, text=None, globs=None):
        # paths 表示真实存在的目标；symlinks 表示 by-id/by-path 映射。
        self.paths = set(paths or [])
        self.symlinks = dict(symlinks or {})
        self.text = dict(text or {})
        self.globs = dict(globs or {})
        self.calls = []

    def glob(self, pattern):
        # glob 调用被记录，是为了证明候选枚举可被单测审计。
        self.calls.append(("glob", pattern))
        return list(self.globs.get(pattern, []))

    def lexists(self, path):
        self.calls.append(("lexists", path))
        return path in self.paths or path in self.symlinks

    def exists(self, path):
        self.calls.append(("exists", path))
        if path in self.text:
            return True
        if path in self.paths:
            return True
        if path in self.symlinks:
            return self.symlinks[path] in self.paths
        return False

    def islink(self, path):
        self.calls.append(("islink", path))
        return path in self.symlinks

    def realpath(self, path):
        self.calls.append(("realpath", path))
        return self.symlinks.get(path, path)

    def readlink(self, path):
        self.calls.append(("readlink", path))
        return self.symlinks[path]

    def stat(self, path):
        self.calls.append(("stat", path))
        if not self.exists(path):
            raise FileNotFoundError(path)
        # 字符设备 mode 用于验证 metadata-only，不代表串口已打开。
        return type("FakeStat", (), {"st_mode": stat.S_IFCHR | 0o660, "st_uid": 0, "st_gid": 20})()

    def read_text(self, path, max_bytes=4096):
        self.calls.append(("read_text", path))
        return self.text[path][:max_bytes]


class O1WaveRoverPortIdentityProbeTest(unittest.TestCase):
    def _stc_inspector(self):
        # STC by-id + ttyACM 是上一轮现场线索，但仍不足以证明底盘身份。
        return FakeInspector(
            paths={"/dev/ttyACM0"},
            symlinks={
                "/dev/serial/by-id/usb-STC_STC_USB_Serial-if00": "/dev/ttyACM0",
                "/dev/serial/by-path/platform-5200400.usb-usb-0:1:1.0": "/dev/ttyACM0",
            },
            text={
                "/sys/class/tty/ttyACM0/device/../idVendor": "0483\n",
                "/sys/class/tty/ttyACM0/device/../idProduct": "5740\n",
                "/sys/class/tty/ttyACM0/device/../manufacturer": "STC\n",
                "/sys/class/tty/ttyACM0/device/../product": "STC USB Serial\n",
            },
            globs={
                "/dev/serial/by-id/*": ["/dev/serial/by-id/usb-STC_STC_USB_Serial-if00"],
                "/dev/serial/by-path/*": ["/dev/serial/by-path/platform-5200400.usb-usb-0:1:1.0"],
                "/dev/ttyACM*": ["/dev/ttyACM0"],
            },
        )

    def test_by_id_realpath_and_candidate_links_are_reported(self):
        # by-id realpath 是 automation 需要的核心字段，但不能升级成身份定论。
        probe = _load_probe_module()
        payload = probe.build_probe_payload(
            "/dev/serial/by-id/usb-STC_STC_USB_Serial-if00",
            argv=["--once-json"],
            inspector=self._stc_inspector(),
        )

        self.assertEqual(payload["target"]["realpath"], "/dev/ttyACM0")
        self.assertTrue(payload["target"]["is_symlink"])
        related_paths = {item["path"] for item in payload["serial_candidates"]["related_to_target_realpath"]}
        self.assertIn("/dev/serial/by-id/usb-STC_STC_USB_Serial-if00", related_paths)
        self.assertIn("/dev/serial/by-path/platform-5200400.usb-usb-0:1:1.0", related_paths)
        self.assertIn("/dev/ttyACM0", related_paths)
        self.assertEqual(payload["sysfs_usb_tty_description"]["tty_name"], "ttyACM0")

    def test_missing_target_port_fails_closed_with_next_checks(self):
        # 端口缺失必须是机器可读状态，不能让现场误以为可以 fallback 控制。
        probe = _load_probe_module()
        payload = probe.build_probe_payload("/dev/serial/by-id/missing", inspector=FakeInspector())

        self.assertEqual(payload["identity_assessment"]["status"], "port_missing")
        self.assertEqual(payload["identity_assessment"]["possible_role"], "port_absent")
        self.assertIn("target_port_missing", payload["identity_assessment"]["risk_flags"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["sends_commands"])
        self.assertFalse(payload["opens_serial_devices"])
        self.assertFalse(payload["robot_control_executed"])
        self.assertFalse(payload["delivery_success"])

    def test_stc_ttyacm_identity_remains_insufficient(self):
        # STC/ttyACM 线索同时可能被 LiDAR 使用，所以只能输出信息不足。
        probe = _load_probe_module()
        payload = probe.build_probe_payload(
            "/dev/serial/by-id/usb-STC_STC_USB_Serial-if00",
            inspector=self._stc_inspector(),
        )

        assessment = payload["identity_assessment"]
        self.assertEqual(assessment["status"], "identity_insufficient")
        self.assertEqual(assessment["possible_role"], "unknown_serial_device")
        self.assertIn("stc_or_ttyacm_is_not_unique", assessment["risk_flags"])
        self.assertIn("compare by-id/by-path before and after unplugging LiDAR and base controller separately", assessment["next_required_checks"])

    def test_lidar_clues_are_classified_as_possible_lidar_or_other_stc(self):
        # LiDAR udev vendor/product 或 /dev/lidar 线索必须优先暴露错口风险。
        probe = _load_probe_module()
        inspector = FakeInspector(
            paths={"/dev/ttyACM0", "/dev/lidar"},
            symlinks={"/dev/serial/by-id/usb-STC_STC_USB_Serial-if00": "/dev/ttyACM0"},
            text={
                "/sys/class/tty/ttyACM0/device/../idVendor": "34bf\n",
                "/sys/class/tty/ttyACM0/device/../idProduct": "ff0a\n",
                "/sys/class/tty/ttyACM0/device/../product": "low cost lidar\n",
            },
            globs={
                "/dev/lidar": ["/dev/lidar"],
                "/dev/serial/by-id/*": ["/dev/serial/by-id/usb-STC_STC_USB_Serial-if00"],
                "/dev/ttyACM*": ["/dev/ttyACM0"],
            },
        )

        payload = probe.build_probe_payload("/dev/serial/by-id/usb-STC_STC_USB_Serial-if00", inspector=inspector)

        self.assertEqual(payload["identity_assessment"]["status"], "possible_lidar_or_other_stc")
        self.assertIn("lidar_clue_present", payload["identity_assessment"]["risk_flags"])
        self.assertEqual(payload["identity_assessment"]["confidence"], "medium_for_risk_only")

    def test_fail_closed_fields_and_blocked_commands_are_fixed(self):
        # 本 probe 连 T=130 都不发；字段必须固定为 no-motion readiness。
        probe = _load_probe_module()
        payload = probe.build_probe_payload("/dev/serial/by-id/usb-STC_STC_USB_Serial-if00", inspector=self._stc_inspector())

        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["sends_commands"])
        self.assertFalse(payload["opens_serial_devices"])
        self.assertFalse(payload["robot_control_executed"])
        self.assertFalse(payload["delivery_success"])
        blocked_ids = {
            item["command"]["T"]
            for item in payload["blocked_commands_not_sent"]
            if isinstance(item["command"], dict)
        }
        self.assertEqual(blocked_ids, {1, 13, 130, 131})
        self.assertIn("open_serial_device", payload["forbidden_actions"])
        self.assertIn("sysfs_text_read", payload["readonly_actions"])

    def test_cli_once_json_outputs_parseable_payload(self):
        # CLI stdout JSON 是远端 automation 的入口，必须可直接 json.loads。
        probe = _load_probe_module()
        stdout = io.StringIO()
        with mock.patch.object(probe, "ReadOnlyDeviceInspector", return_value=self._stc_inspector()):
            with mock.patch("sys.stdout", stdout):
                result = probe.main(["--once-json", "--port", "/dev/serial/by-id/usb-STC_STC_USB_Serial-if00"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["schema"], "trashbot.o1.wave_rover_port_identity_probe.v1")
        self.assertEqual(payload["source"]["mode"], "read_only_once")
        self.assertFalse(payload["opens_serial_devices"])
        self.assertEqual(payload["target"]["realpath"], "/dev/ttyACM0")


if __name__ == "__main__":
    unittest.main()
