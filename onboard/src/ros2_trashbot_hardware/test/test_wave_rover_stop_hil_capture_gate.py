import importlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import redirect_stdout


PACKAGE_SRC = Path(__file__).resolve().parents[1]
if str(PACKAGE_SRC) not in sys.path:
    # 测试直接跑源码树，避免依赖本机是否已经 colcon build 或 pip install。
    sys.path.insert(0, str(PACKAGE_SRC))


def _module():
    # 延迟 import 让 CLI 测试和纯函数测试总是共享当前源码实现。
    return importlib.import_module("ros2_trashbot_hardware.wave_rover_stop_hil_capture_gate")


# 测试设计说明：
# 1. 所有测试都用临时 fixture，避免覆盖 sprint 正式 artifact。
# 2. helper 正例只验证 mock readiness，不声明 live HIL。
# 3. 缺 token 和错 token 分开测，是为了防止实现只处理 None 不处理错误字符串。
# 4. 非 mock mode 单独测，是为了证明当前自动化不会退化为 live attempt。
# 5. T=1001 非零负例单独测，是为了证明 fixture 解析不会把非零轮速写成 ready。
# 6. CLI 测试走 `main(args)`，确保 `python -m` 使用的入口逻辑与纯函数一致。
# 7. MockStopHttpClient 注入到 token 失败测试中，直接断言 calls 为空。
# 8. 每个安全字段都用 bool 断言，不依赖字符串 summary。
# 9. network_transport 必须是 mock_in_memory_no_socket，证明没有真实 HTTP。
# 10. fixture 的 phase 固定 after_stop，防止启动前静止样本被误当作 stop 后反馈。
# 11. 测试不导入 ROS2，也不打开串口，确保 macOS 本地可重复执行。
# 12. 临时文件只在测试目录内写入，不触碰仓库正式 artifact。
# 13. 这些测试只覆盖软件 gate，不替代现场 operator acceptance。
# 14. 若未来加入 live mode，应新增独立测试并保持本组 mock-only 测试不放宽。


def _write_fixture(directory: Path, *, left: float = 0, right: float = 0) -> Path:
    # fixture 明确是 after_stop mock T=1001，不代表真实 UART 或 ESP32 ACK。
    # L/R 参数用于构造正例和 fail-closed 负例。
    # 只写一条样本，便于每个测试精确定位 L/R 归零条件。
    # `y` 使用字符串 "null"，覆盖项目 parser 对现场 yaw 空值的兼容路径。
    # `v` 只用于满足 parser 必填字段，不代表电池标定通过。
    # JSON line 保留换行，贴合 vendor newline-delimited feedback 形态。
    fixture = directory / "mock_t1001_feedback.json"
    payload = {
        "schema": "trashbot.o1.mock_t1001_feedback_fixture.v1",
        "boundary": "mock_fixture_not_live_uart",
        "feedback_frames": [
            {
                "phase": "after_stop",
                "line": json.dumps(
                    {
                        "T": 1001,
                        "L": left,
                        "R": right,
                        "r": 0,
                        "p": 0,
                        "y": "null",
                        "v": 12.3,
                    },
                    separators=(",", ":"),
                )
                + "\n",
            }
        ],
    }
    fixture.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return fixture


class WaveRoverStopHilCaptureGateTest(unittest.TestCase):
    def test_mock_token_happy_path_builds_ready_artifact_with_false_guards(self):
        gate = _module()

        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = _write_fixture(Path(tmpdir))
            # 正例必须显式给 mock 和 token；缺任一条件都应被其它测试拦住。
            # generated_at 固定，避免测试输出依赖当前系统时间。
            artifact = gate.build_stop_hil_capture_gate_artifact(
                mock=True,
                operator_approval_token="MOCK_APPROVED_STOP_ONLY",
                feedback_fixture=fixture,
                generated_at="2026-07-13T10:12:00Z",
            )

        # ready 只表示 mock gate 可用，不等于 HIL、safe-to-control 或实车控制。
        # schema/status 是 Product 验收脚本读取的主锚点。
        self.assertEqual(artifact["schema"], "trashbot.o1.current_stop_hil_capture_gate.v1")
        self.assertEqual(artifact["capture_gate_status"], "ready_for_mock_stop_hil_capture_gate_not_hil")
        self.assertEqual(artifact["proof_boundary"], "software_proof_o1_live_stop_hil_capture_gate_mock_only")
        self.assertEqual(artifact["stop_endpoint"], "/api/base/stop")
        # 下列字段固定 false，防止 mock stop 成功被升级成 live HIL。
        for key in (
            "hil_pass",
            "safe_to_control",
            "route_execution_success",
            "delivery_success",
            "robot_control_executed",
            "nonzero_motion_command_sent",
            "uses_real_uart",
        ):
            self.assertFalse(artifact[key], key)

        # mock HTTP 只证明 POST /api/base/stop 的本地调用形状。
        # network_transport 必须是 mock_in_memory_no_socket，不能出现真实网络请求。
        self.assertTrue(artifact["mock_http_stop_called"])
        self.assertTrue(artifact["mock_http_stop_call_shape_valid"])
        self.assertEqual(artifact["mock_http_stop_call"]["method"], "POST")
        self.assertEqual(artifact["mock_http_stop_call"]["path"], "/api/base/stop")
        self.assertEqual(artifact["mock_http_stop_call"]["network_transport"], "mock_in_memory_no_socket")
        self.assertTrue(artifact["mock_t1001_feedback_fixture_used"])
        self.assertTrue(artifact["t1001_feedback_zero_after_stop_fixture"])
        self.assertEqual(artifact["mock_t1001_feedback"]["observed_t1001_count"], 1)

    def test_missing_token_fails_closed_and_does_not_call_mock_stop(self):
        gate = _module()

        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = _write_fixture(Path(tmpdir))
            # client 注入后可以直接检查 calls，证明 token gate 在 stop 前执行。
            client = gate.MockStopHttpClient()
            artifact = gate.build_stop_hil_capture_gate_artifact(
                mock=True,
                operator_approval_token=None,
                feedback_fixture=fixture,
                generated_at="2026-07-13T10:12:00Z",
                http_client=client,
            )

        # token gate 在最前面；缺 token 时连 mock stop 都不能调用。
        # fixture 也不能被写成已消费 stop 后反馈。
        self.assertEqual(artifact["capture_gate_status"], "blocked_stop_hil_capture_gate_fail_closed")
        self.assertIn("operator_approval_token_missing_or_invalid", artifact["blocked_reasons"])
        self.assertFalse(artifact["mock_http_stop_called"])
        self.assertFalse(artifact["mock_t1001_feedback_fixture_used"])
        self.assertEqual(client.calls, [])
        self.assertFalse(artifact["robot_control_executed"])

    def test_wrong_token_fails_closed_and_does_not_call_mock_stop(self):
        gate = _module()

        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = _write_fixture(Path(tmpdir))
            # 错 token 不是弱警告，而是与缺 token 一样的 fail-closed blocker。
            client = gate.MockStopHttpClient()
            artifact = gate.build_stop_hil_capture_gate_artifact(
                mock=True,
                operator_approval_token="WRONG",
                feedback_fixture=fixture,
                generated_at="2026-07-13T10:12:00Z",
                http_client=client,
            )

        # 错 token 与缺 token 等价，必须 fail-closed 且不触发 stop。
        self.assertEqual(artifact["capture_gate_status"], "blocked_stop_hil_capture_gate_fail_closed")
        self.assertIn("operator_approval_token_missing_or_invalid", artifact["blocked_reasons"])
        self.assertFalse(artifact["mock_http_stop_called"])
        self.assertEqual(client.calls, [])

    def test_non_mock_mode_fails_closed_without_real_stop_or_uart(self):
        gate = _module()

        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = _write_fixture(Path(tmpdir))
            # 即使 token 正确，mock=false 在当前自动化中也不能触发 live 行为。
            artifact = gate.build_stop_hil_capture_gate_artifact(
                mock=False,
                operator_approval_token="MOCK_APPROVED_STOP_ONLY",
                feedback_fixture=fixture,
                generated_at="2026-07-13T10:12:00Z",
            )

        # 当前自动化没有现场 operator approval；mock=false 不能降级成 live attempt。
        # 真实 endpoint、UART、cmd_vel、NavigateToPose 都必须保持 false。
        self.assertEqual(artifact["capture_gate_status"], "blocked_stop_hil_capture_gate_fail_closed")
        self.assertIn("mock_mode_required_current_automation_has_no_live_operator", artifact["blocked_reasons"])
        self.assertFalse(artifact["real_stop_endpoint_called"])
        self.assertFalse(artifact["uses_real_uart"])
        self.assertFalse(artifact["cmd_vel_published"])
        self.assertFalse(artifact["navigate_to_pose_sent"])

    def test_nonzero_t1001_after_stop_fails_closed(self):
        gate = _module()

        with tempfile.TemporaryDirectory() as tmpdir:
            # left=1.0 构造 stop 后仍有轮速的危险 fixture，必须让 artifact 降级。
            fixture = _write_fixture(Path(tmpdir), left=1.0, right=0)
            artifact = gate.build_stop_hil_capture_gate_artifact(
                mock=True,
                operator_approval_token="MOCK_APPROVED_STOP_ONLY",
                feedback_fixture=fixture,
                generated_at="2026-07-13T10:12:00Z",
            )

        # fixture 里只要 after_stop L/R 没归零，就不能保持 ready。
        # 即便 mock stop shape 正确，HIL/safety/control 字段也必须继续 false。
        self.assertEqual(artifact["capture_gate_status"], "blocked_stop_hil_capture_gate_fail_closed")
        self.assertIn("t1001_after_stop_lr_not_zero", artifact["blocked_reasons"])
        self.assertFalse(artifact["t1001_feedback_zero_after_stop_fixture"])
        self.assertFalse(artifact["hil_pass"])
        self.assertFalse(artifact["safe_to_control"])

    def test_cli_writes_mock_only_artifact(self):
        gate = _module()

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_dir = Path(tmpdir)
            # CLI 使用临时 output，避免测试污染 sprint 正式 stop_hil_capture_gate.json。
            fixture = _write_fixture(temp_dir)
            output = temp_dir / "stop_hil_capture_gate.json"
            args = [
                "--mock",
                "--operator-approval-token",
                "MOCK_APPROVED_STOP_ONLY",
                "--feedback-fixture",
                str(fixture),
                "--output",
                str(output),
            ]
            # stdout 捕获证明 CLI 对自动化日志只输出短 JSON。
            with redirect_stdout(io.StringIO()) as stdout:
                result = gate.main(args)
            artifact = json.loads(output.read_text(encoding="utf-8"))

        # CLI exit 0 只代表 mock-only artifact ready；route execution 仍必须 false。
        self.assertEqual(result, 0)
        self.assertIn("ready_for_mock_stop_hil_capture_gate_not_hil", stdout.getvalue())
        self.assertEqual(artifact["schema"], "trashbot.o1.current_stop_hil_capture_gate.v1")
        self.assertTrue(artifact["mock_http_stop_called"])
        self.assertTrue(artifact["t1001_feedback_zero_after_stop_fixture"])
        self.assertFalse(artifact["route_execution_success"])


if __name__ == "__main__":
    unittest.main()
