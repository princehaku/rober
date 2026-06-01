import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


# 测试文件跨包读取脚本，是为了保持 probe dependency-free 而不改包结构。
SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "o1_upper_computer_readiness_probe.py"


def _load_probe_module():
    # 从脚本文件直接加载，避免要求 onboard/scripts 变成 Python package。
    spec = importlib.util.spec_from_file_location("o1_upper_computer_readiness_probe", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    # 测试只执行模块定义，不触发 __main__，因此不会写文件或访问设备。
    spec.loader.exec_module(module)
    return module


class O1UpperComputerReadinessProbeTest(unittest.TestCase):
    def test_contract_contains_schema_vendor_sources_and_boundary(self):
        # contract 是 probe 的核心价值：任何环境都必须保持 fail-closed。
        probe = _load_probe_module()
        # 空 glob 代表没有候选设备，也必须生成完整 JSON 而不是失败。
        payload = probe.build_probe_payload(globber=lambda pattern: [])

        # schema/version 固定后，后续 sprint 可以稳定对比 readiness artifact。
        self.assertEqual(payload["schema"], "trashbot.o1.upper_computer_readiness.v1")
        self.assertEqual(payload["version"], 1)
        # vendor_sources 必须覆盖 WAVE ROVER 和 LiDAR 两条证据链入口。
        self.assertIn("docs/vendor/VENDOR_INDEX.md", payload["vendor_sources"])
        self.assertIn("docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py", payload["vendor_sources"])
        self.assertIn("docs/vendor/lidar_pkg_ros2-main/README.md", payload["vendor_sources"])
        self.assertIn("docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp", payload["vendor_sources"])
        self.assertIn("docs/vendor/lidar_pkg_ros2-main/config/lidar_params.yaml", payload["vendor_sources"])
        self.assertIn("docs/vendor/lidar_pkg_ros2-main/scripts/99-lidar.rules", payload["vendor_sources"])
        self.assertIn("docs/vendor/lidar_ros/README.md", payload["vendor_sources"])
        self.assertEqual(payload["source"]["mode"], "read_only_once")
        # 四个字段是 O1/O5/O6/O7 通用安全口径，必须全部为 false。
        self.assertFalse(payload["boundary"]["safe_to_control"])
        self.assertFalse(payload["boundary"]["sends_commands"])
        self.assertFalse(payload["boundary"]["robot_control_executed"])
        self.assertFalse(payload["boundary"]["delivery_success"])

    def test_serial_candidates_are_injectable_and_never_opened(self):
        # 注入 fake glob，证明函数只依赖路径枚举，不依赖真实 /dev 环境。
        probe = _load_probe_module()

        def fake_glob(pattern):
            # fake_glob 不模拟 open/read/write，测试只覆盖候选汇总 contract。
            return {
                "/dev/ttyUSB*": ["/dev/ttyUSB0"],
                "/dev/ttyAMA*": ["/dev/ttyAMA0", "/dev/ttyAMA1"],
            }.get(pattern, [])

        summary = probe.summarize_serial_candidates(globber=fake_glob)

        # status 明确写 listed_not_opened，避免把候选路径误读成设备已验证。
        self.assertEqual(summary["status"], "listed_not_opened")
        self.assertEqual(summary["total_count"], 3)
        self.assertEqual(summary["by_pattern"]["/dev/ttyUSB*"]["paths"], ["/dev/ttyUSB0"])
        self.assertEqual(summary["by_pattern"]["/dev/ttyAMA*"]["count"], 2)

    def test_lidar_reference_readiness_is_not_hil(self):
        # LiDAR 150000 只来自 ROS2 vendor reference，必须防止被写成实测通过。
        probe = _load_probe_module()
        # 不需要真实 LiDAR；本测试只锁住 software_reference_not_hil 文案。
        payload = probe.build_probe_payload(globber=lambda pattern: [])
        lidar = payload["lidar_reference_readiness"]

        self.assertEqual(lidar["status"], "software_reference_not_hil")
        self.assertEqual(lidar["source_of_truth"], "docs/vendor/lidar_pkg_ros2-main/")
        self.assertEqual(lidar["historical_protocol_reference"], "docs/vendor/lidar_ros/")
        self.assertEqual(lidar["reference_baudrate"], 150000)
        self.assertEqual(lidar["reference_start_command_hex"], "A5 60")
        self.assertEqual(lidar["reference_stop_command_hex"], "A5 00 A5 65 A5 65")
        self.assertEqual(lidar["reference_header"], "0xAA 0x55")
        self.assertEqual(lidar["reference_config_port_name"], "/dev/lidar")
        self.assertEqual(lidar["reference_scan_topic"], "/scan")
        self.assertEqual(lidar["reference_frame_id"], "laser")
        self.assertEqual(lidar["project_frame_id_override_allowed"], "laser_frame")
        self.assertEqual(lidar["reference_udev"]["idVendor"], "34bf")
        self.assertEqual(lidar["reference_udev"]["idProduct"], "ff0a")
        self.assertEqual(lidar["reference_udev"]["symlink"], "lidar")
        # 真实 target baud 稳定性必须留在 not_proven，不能被 reference 覆盖。
        self.assertIn("150000 baud stability on target hardware", lidar["not_proven"])

    def test_pyserial_detection_fails_closed_for_stub_or_broken_spec(self):
        # 远端 stdin 运行可能遇到半初始化 serial stub；probe 不能因此丢 JSON。
        probe = _load_probe_module()
        original_serial = sys.modules.get("serial")

        try:
            # __spec__ 为 None 时 find_spec 会抛 ValueError，必须按不可用处理。
            stub_serial = type(sys)("serial")
            stub_serial.__spec__ = None
            sys.modules["serial"] = stub_serial
            self.assertFalse(probe._is_pyserial_available())

            # 某些测试 stub 或 import hook 可能直接异常，同样必须 fail-closed。
            with mock.patch.object(probe.importlib.util, "find_spec", side_effect=RuntimeError("broken spec")):
                self.assertFalse(probe._is_pyserial_available())
        finally:
            # 恢复 sys.modules，避免污染同进程里后续测试的 import 视图。
            if original_serial is None:
                sys.modules.pop("serial", None)
            else:
                sys.modules["serial"] = original_serial

    def test_wave_rover_blocks_control_commands_and_hil_claims(self):
        # 控制类命令只允许出现在 blocked 列表中，不能由 probe 发送。
        probe = _load_probe_module()
        # build_probe_payload 不接收串口对象，因此测试可证明没有发送路径。
        payload = probe.build_probe_payload(globber=lambda pattern: [])
        wave_rover = payload["wave_rover_readiness"]

        # not_ready_for_control 是本轮 O1 材料边界，不能因 SSH 成功而变成 ready。
        self.assertEqual(wave_rover["status"], "not_ready_for_control")
        self.assertEqual(wave_rover["uart_json_reference"], "UTF-8 newline-delimited JSON")
        blocked_ids = {item["command"]["T"] for item in wave_rover["blocked_commands_not_sent"]}
        # 三个 ID 来自 vendor command reference，本轮只允许声明 blocked。
        self.assertEqual(blocked_ids, {1, 13, 131})
        self.assertIn("T=1001 feedback packet not captured from real chassis", wave_rover["hil_readiness_blockers"])

    def test_next_safe_commands_do_not_include_motion_or_control_words(self):
        # next_safe_commands 面向人工下一步复制，必须避免运动/控制歧义。
        probe = _load_probe_module()
        # 安全命令列表需要可审查，所以这里按字符串做保守黑名单测试。
        payload = probe.build_probe_payload(globber=lambda pattern: [])
        joined = "\n".join(payload["next_safe_commands"]).lower()

        # 同时屏蔽 cmd_vel 和 WAVE ROVER 控制 ID，防止文档建议误触发底盘。
        for forbidden in ("move", "turn", "control", "cmd_vel", "t=1", "t=13", "t=131"):
            self.assertNotIn(forbidden, joined)

    def test_cli_writes_json_artifact_without_changing_fail_closed_fields(self):
        # --output 只验证 JSON artifact，可写目录由 tempfile 隔离。
        probe = _load_probe_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            # 临时目录避免把测试 artifact 留在仓库或远端工作目录。
            output = Path(tmpdir) / "probe.json"
            result = probe.main(["--output", str(output)])
            payload = json.loads(output.read_text(encoding="utf-8"))

        # 写 artifact 不能改变安全边界，避免后续把文件输出当控制许可。
        self.assertEqual(result, 0)
        self.assertFalse(payload["boundary"]["safe_to_control"])
        self.assertFalse(payload["boundary"]["sends_commands"])
        self.assertFalse(payload["boundary"]["robot_control_executed"])
        self.assertFalse(payload["boundary"]["delivery_success"])


if __name__ == "__main__":
    unittest.main()
