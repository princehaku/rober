import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest import mock


# 测试边界说明：这些测试锁定 serial-open/read-only contract。
# 测试边界说明：fake serial 提供 readline，但 write 只记录不应被调用。
# 测试边界说明：测试不访问真实 /dev，避免 CI 或开发机误触硬件。
# 测试边界说明：测试不 import ROS2，避免把硬件材料采集绑到 ROS runtime。
# 测试边界说明：测试覆盖 pyserial 缺失，保证远端 blocker 结构化输出。
# 测试边界说明：测试覆盖 open 失败，保证缺设备也不会破坏 fail-closed。
# 测试边界说明：测试覆盖坏 JSON 行，保证真实串口噪声不会中断采集。
# 测试边界说明：测试覆盖 T=1001/T=1002 分类，但不验证单位和标定。
# 测试边界说明：测试覆盖 blocked commands，防止未来误加 T=130 查询。
# 测试边界说明：测试覆盖 cmd_vel 文案，防止误导人工执行 ROS 控制。
# 测试边界说明：测试覆盖 CLI stdout JSON，匹配 SSH stdin 运行方式。
# 测试边界说明：测试保持脚本单文件加载，不要求 onboard/scripts 变包。
# 测试边界说明：测试中的 115200 只锁 vendor reference，不锁 Orange Pi 路径。
# 测试边界说明：测试不保存 artifact，避免把 fake material 混入仓库。
# 测试边界说明：测试断言四个安全字段在成功和失败路径都为 false。
# 测试边界说明：测试断言 close 被调用，避免短探测长期占用串口。
# 测试边界说明：测试不尝试 monkeypatch time，真实超时窗口保持很短。
# 测试边界说明：测试的 fake 行只用于 contract，不代表真实 WAVE ROVER 输出。
# 测试边界说明：测试目标是防回归，不替代远端串口打开证据。
# 测试边界说明：如果后续新增主动查询，必须新增默认关闭和不写串口测试。
# 测试边界说明：如果后续接入 HIL，本文件仍只应覆盖 read-only probe。
# 测试边界说明：任何新增断言都不能要求真实硬件存在。
# 测试边界说明：错误类型保留原异常类名，方便 sprint 文档定位。
# 测试边界说明：raw preview 只验证存在性，不鼓励保存长串口日志。
# 测试边界说明：vendor source 断言防止资料链被后续重构删掉。
# 测试边界说明：串口打开成功不代表 safe_to_control 可以变为 true。
# 测试边界说明：读取不到行也必须视为有效材料，而不是测试失败。
# 直接加载脚本，保持 probe 可通过 SSH stdin 单文件运行，不要求改成包。
SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "o1_wave_rover_serial_feedback_probe.py"


def _load_probe_module():
    # spec 加载只执行函数定义；不会触发 __main__ 或打开真实串口。
    spec = importlib.util.spec_from_file_location("o1_wave_rover_serial_feedback_probe", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeSerial:
    # fake 串口保留 write_calls，是为了证明 probe 默认没有写路径被调用。
    write_calls = []
    instances = []

    def __init__(self, port, baudrate, timeout):
        # 记录初始化参数，锁定 port/baudrate 都来自 CLI 或调用方。
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.closed = False
        self.lines = [
            b'{"T":1001,"bat":12.1}\n',
            b"not-json\n",
            b'{"T":1002,"r":1}\n',
        ]
        FakeSerial.instances.append(self)

    def readline(self):
        # 没有更多行时返回空 bytes，模拟 pyserial timeout。
        if self.lines:
            return self.lines.pop(0)
        return b""

    def write(self, data):
        # 如果未来误加写串口，测试会看到 write_calls 非空。
        FakeSerial.write_calls.append(data)

    def close(self):
        self.closed = True


class FakeSerialModule:
    Serial = FakeSerial


class O1WaveRoverSerialFeedbackProbeTest(unittest.TestCase):
    def setUp(self):
        # 每个测试重置假串口全局记录，避免跨测试污染写入断言。
        FakeSerial.write_calls = []
        FakeSerial.instances = []

    def test_contract_defaults_are_fail_closed_and_vendor_sourced(self):
        # contract 是安全入口的核心：打开串口也不能暗示可控制。
        probe = _load_probe_module()
        payload = probe.run_probe(
            "/dev/fake",
            115200,
            0.01,
            argv=["--once-json", "--port", "/dev/fake"],
            serial_module=FakeSerialModule,
        )

        self.assertEqual(payload["schema"], "trashbot.o1.wave_rover_serial_feedback_probe.v1")
        self.assertEqual(payload["evidence_boundary"], "serial_open_read_only_not_hil")
        self.assertIn("docs/vendor/VENDOR_INDEX.md", payload["vendor_sources"])
        self.assertIn("docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py", payload["vendor_sources"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["sends_commands"])
        self.assertFalse(payload["robot_control_executed"])
        self.assertFalse(payload["delivery_success"])

    def test_probe_reads_existing_lines_and_never_writes_serial(self):
        # fake 串口提供两条 JSON 和一条坏行，用来覆盖解析与坏帧容错。
        probe = _load_probe_module()
        payload = probe.run_probe(
            "/dev/serial/by-id/fake",
            115200,
            0.05,
            argv=[],
            serial_module=FakeSerialModule,
        )

        self.assertTrue(payload["pyserial"]["available"])
        self.assertTrue(payload["serial_opened"])
        self.assertGreaterEqual(payload["read_line_count"], 3)
        self.assertEqual(payload["parsed_json_count"], 2)
        self.assertEqual(payload["invalid_json_count"], 1)
        self.assertEqual(payload["observed_feedback_types"], ["T=1001", "T=1002"])
        self.assertEqual(FakeSerial.write_calls, [])
        self.assertTrue(FakeSerial.instances[0].closed)

    def test_pyserial_missing_returns_structured_error(self):
        # 远端缺 pyserial 时必须输出 JSON blocker，不能抛异常中断 SSH 证据。
        probe = _load_probe_module()
        with mock.patch.object(probe, "_load_pyserial", return_value=(False, None, "No module named serial")):
            payload = probe.run_probe("/dev/fake", 115200, 0.01, argv=[])

        self.assertFalse(payload["pyserial"]["available"])
        self.assertFalse(payload["serial_opened"])
        self.assertEqual(payload["error"]["type"], "pyserial_unavailable")
        self.assertEqual(payload["read_line_count"], 0)
        self.assertEqual(payload["parsed_json_count"], 0)

    def test_missing_port_error_stays_fail_closed(self):
        # open 失败是常见本地 dry-run 结果，也必须保留完整安全字段。
        probe = _load_probe_module()

        class RaisingModule:
            class Serial:
                def __init__(self, port, baudrate, timeout):
                    raise OSError("missing port")

        payload = probe.run_probe("/dev/missing", 115200, 0.01, argv=[], serial_module=RaisingModule)

        self.assertFalse(payload["serial_opened"])
        self.assertEqual(payload["error"]["type"], "OSError")
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["sends_commands"])
        self.assertFalse(payload["robot_control_executed"])
        self.assertFalse(payload["delivery_success"])

    def test_blocked_commands_include_feedback_query_and_motion_paths(self):
        # T=130 也保持默认不发送，避免本轮 read-only 被升级成查询动作。
        probe = _load_probe_module()
        payload = probe.run_probe("/dev/fake", 115200, 0.01, argv=[], serial_module=FakeSerialModule)
        blocked = payload["blocked_commands_not_sent"]
        blocked_ids = {
            item["command"]["T"]
            for item in blocked
            if isinstance(item["command"], dict) and "T" in item["command"]
        }
        blocked_names = {item["command"] for item in blocked if isinstance(item["command"], str)}

        self.assertEqual(blocked_ids, {1, 13, 130, 131})
        self.assertIn("cmd_vel", blocked_names)
        self.assertEqual(FakeSerial.write_calls, [])

    def test_cli_prints_once_json(self):
        # CLI 路径验证 stdout JSON，保持远端 stdin 运行方式可用。
        probe = _load_probe_module()
        stdout = io.StringIO()
        with mock.patch.object(probe, "_load_pyserial", return_value=(False, None, "No module named serial")):
            with mock.patch("sys.stdout", stdout):
                result = probe.main(["--once-json", "--port", "/dev/fake"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["port"], "/dev/fake")
        self.assertEqual(payload["baudrate"], 115200)
        self.assertEqual(payload["error"]["type"], "pyserial_unavailable")


if __name__ == "__main__":
    unittest.main()
