import importlib.util
import io
import json
import stat
from pathlib import Path
import unittest
from unittest import mock


# 测试边界说明：本文件锁定 O1 USB/串口 inventory 的只读 contract。
# 测试边界说明：fake inspector 不访问真实 /dev，避免 CI 误触现场硬件。
# 测试边界说明：inventory 只允许 glob/readlink/stat/sysfs 文本读取。
# 测试边界说明：测试显式拒绝 import/use pyserial 和 serial open 路径。
# 测试边界说明：STC 34bf:ff0a 与 LiDAR udev 一致时必须 fail-closed。
# 测试边界说明：/dev/lidar alias 命中只代表错口风险，不代表 LiDAR 已可用。
# 测试边界说明：by-id/by-path 同 realpath 是插拔对比材料，不是身份定论。
# 测试边界说明：recommended_physical_checks 是现场 SOP，不替代真实 HIL。
# 测试边界说明：blocked_commands_not_sent 必须包含 T=130，避免继续盲发。
# 测试边界说明：所有安全字段必须固定 false，不能随风险分类变化。
# 测试边界说明：fake sysfs fixture 只验证 contract，不构成硬件证据。
# 测试边界说明：CLI stdout JSON 是远端 stdin 运行入口，必须可 json.loads。
# 测试边界说明：如果未来扩展字段，schema 和 fail-closed 字段仍优先稳定。
# 测试边界说明：注释保留中文，满足硬件脚本审查约束。
# 测试边界说明：本测试不创建 artifact，避免 fake 材料混入现场证据。
SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "o1_usb_serial_inventory_probe.py"


def _load_probe_module():
    # spec 加载只执行模块定义；不会触发 __main__ 或访问真实设备。
    spec = importlib.util.spec_from_file_location("o1_usb_serial_inventory_probe", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeInspector:
    """fake 文件系统只提供只读元数据，用于证明 probe 不碰真实串口。"""

    def __init__(self, *, paths=None, symlinks=None, text=None, globs=None):
        # paths 表示真实存在的 /dev 节点；symlinks 表示 udev alias 映射。
        self.paths = set(paths or [])
        self.symlinks = dict(symlinks or {})
        self.text = dict(text or {})
        self.globs = dict(globs or {})
        self.calls = []

    def glob(self, pattern):
        # 记录 glob 调用，确保 inventory 来源可审计。
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

    def readlink(self, path):
        self.calls.append(("readlink", path))
        return self.symlinks[path]

    def realpath(self, path):
        self.calls.append(("realpath", path))
        return self.symlinks.get(path, path)

    def stat(self, path):
        self.calls.append(("stat", path))
        if not self.exists(path):
            raise FileNotFoundError(path)
        # 字符设备 mode 只证明 metadata contract，不代表串口可打开。
        return type("FakeStat", (), {"st_mode": stat.S_IFCHR | 0o660, "st_uid": 0, "st_gid": 20})()

    def read_text(self, path, max_bytes=4096):
        self.calls.append(("read_text", path))
        if path.startswith("/dev/"):
            raise AssertionError("inventory must not read /dev device content")
        return self.text[path][:max_bytes]


class O1UsbSerialInventoryProbeTest(unittest.TestCase):
    def _mixed_inventory(self):
        # LiDAR 与另一个 ttyUSB 候选同时存在，覆盖现场需要的插拔对比摘要。
        return FakeInspector(
            paths={"/dev/ttyACM0", "/dev/ttyUSB0", "/dev/lidar"},
            symlinks={
                "/dev/serial/by-id/usb-STC_STC_USB_Serial-if00": "/dev/ttyACM0",
                "/dev/serial/by-path/platform-5200400.usb-usb-0:1:1.0": "/dev/ttyACM0",
                "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0": "/dev/ttyUSB0",
            },
            text={
                "/sys/class/tty/ttyACM0/device/../idVendor": "34bf\n",
                "/sys/class/tty/ttyACM0/device/../idProduct": "ff0a\n",
                "/sys/class/tty/ttyACM0/device/../manufacturer": "STC\n",
                "/sys/class/tty/ttyACM0/device/../product": "STC USB Serial\n",
                "/sys/class/tty/ttyUSB0/device/../manufacturer": "Waveshare ESP32\n",
                "/sys/class/tty/ttyUSB0/device/../product": "USB Serial\n",
            },
            globs={
                "/dev/ttyACM*": ["/dev/ttyACM0"],
                "/dev/ttyUSB*": ["/dev/ttyUSB0"],
                "/dev/serial/by-id/*": [
                    "/dev/serial/by-id/usb-STC_STC_USB_Serial-if00",
                    "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0",
                ],
                "/dev/serial/by-path/*": ["/dev/serial/by-path/platform-5200400.usb-usb-0:1:1.0"],
                "/dev/lidar": ["/dev/lidar"],
            },
        )

    def test_inventory_schema_and_fail_closed_fields_are_fixed(self):
        # schema 和安全 false 字段是本 probe 的首要验收面。
        probe = _load_probe_module()
        payload = probe.build_inventory_payload(inspector=self._mixed_inventory())

        self.assertEqual(payload["schema"], "trashbot.o1.usb_serial_inventory.v1")
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["sends_commands"])
        self.assertFalse(payload["opens_serial_devices"])
        self.assertFalse(payload["robot_control_executed"])
        self.assertFalse(payload["delivery_success"])
        self.assertIn("send_T130", payload["forbidden_actions"])
        self.assertIn("sysfs_text_read", payload["readonly_actions"])

    def test_inventory_summary_groups_aliases_by_realpath(self):
        # 同一 realpath 的 by-id/by-path/lidar 关系是现场插拔对比核心。
        probe = _load_probe_module()
        payload = probe.build_inventory_payload(inspector=self._mixed_inventory())

        summary = payload["inventory_summary"]
        self.assertIn("/dev/ttyACM0", summary["realpath_to_aliases"])
        self.assertIn("/dev/serial/by-id/usb-STC_STC_USB_Serial-if00", summary["realpath_to_aliases"]["/dev/ttyACM0"])
        self.assertIn("/dev/serial/by-path/platform-5200400.usb-usb-0:1:1.0", summary["realpath_to_aliases"]["/dev/ttyACM0"])
        self.assertIn("/dev/ttyUSB0", summary["tty_realpaths"])
        self.assertIn("/dev/ttyACM0", summary["stc_or_ttyacm_realpaths"])

    def test_lidar_vendor_product_creates_high_risk_without_control_permission(self):
        # STC 34bf:ff0a 来自 LiDAR udev 规则，必须提示错口风险。
        probe = _load_probe_module()
        payload = probe.build_inventory_payload(inspector=self._mixed_inventory())

        risk_ids = {risk["risk_id"] for risk in payload["identity_risks"]}
        self.assertIn("possible_lidar_or_other_stc", risk_ids)
        lidar_risk = next(risk for risk in payload["identity_risks"] if risk["risk_id"] == "possible_lidar_or_other_stc")
        self.assertEqual(lidar_risk["severity"], "high")
        self.assertEqual(lidar_risk["affected_realpath"], "/dev/ttyACM0")
        self.assertFalse(payload["safe_to_control"])

    def test_recommended_checks_require_separate_unplug_compare(self):
        # 下一步必须是分别拔插 LiDAR 和底盘控制器，而不是继续盲发 T=130。
        probe = _load_probe_module()
        payload = probe.build_inventory_payload(inspector=self._mixed_inventory())

        check_ids = {item["check_id"] for item in payload["recommended_physical_checks"]}
        self.assertIn("unplug_lidar_only", check_ids)
        self.assertIn("replug_lidar_unplug_base_controller_only", check_ids)
        self.assertIn("trace_cables_before_feedback_probe", check_ids)
        blocked_ids = {
            item["command"]["T"]
            for item in payload["blocked_commands_not_sent"]
            if isinstance(item["command"], dict)
        }
        self.assertEqual(blocked_ids, {1, 13, 130, 131})

    def test_no_candidates_is_machine_readable_and_still_safe(self):
        # 没有任何候选设备时也要输出风险，而不是 fallback 到默认串口。
        probe = _load_probe_module()
        payload = probe.build_inventory_payload(inspector=FakeInspector())

        self.assertEqual(payload["inventory_summary"]["total_candidate_paths"], 0)
        self.assertEqual(payload["identity_risks"][0]["risk_id"], "no_serial_candidates_visible")
        self.assertFalse(payload["opens_serial_devices"])

    def test_script_source_does_not_import_pyserial(self):
        # 静态检查避免后续把 pyserial 悄悄接进 inventory。
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("import serial", source)
        self.assertNotIn("serial.Serial", source)

    def test_cli_once_json_outputs_parseable_payload(self):
        # 远端 ssh stdin 运行依赖 stdout 单个 JSON。
        probe = _load_probe_module()
        stdout = io.StringIO()
        with mock.patch.object(probe, "ReadOnlyInventoryInspector", return_value=self._mixed_inventory()):
            with mock.patch("sys.stdout", stdout):
                result = probe.main(["--once-json"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["schema"], "trashbot.o1.usb_serial_inventory.v1")
        self.assertEqual(payload["source"]["mode"], "read_only_once")
        self.assertFalse(payload["sends_commands"])


if __name__ == "__main__":
    unittest.main()
