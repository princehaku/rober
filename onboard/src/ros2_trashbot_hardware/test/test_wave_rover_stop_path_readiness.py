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
    # 延迟 import 让每个测试都能拿到当前源码实现。
    # 这也让 CLI 测试和纯函数测试共享同一模块入口。
    return importlib.import_module("ros2_trashbot_hardware.wave_rover_stop_path_readiness")


class WaveRoverStopPathReadinessTest(unittest.TestCase):
    def test_builds_ready_artifact_with_fixed_false_safety_fields(self):
        readiness = _module()

        artifact = readiness.build_current_stop_path_readiness_artifact(generated_at="2026-07-13T09:11:00Z")

        # current_stop_path_readiness 只能证明离线 stop path 编码，不能升级成 HIL 或路线执行。
        # schema 和 proof_boundary 是 Product/OKR closeout 读取的主合同。
        self.assertEqual(artifact["schema"], "trashbot.o1.current_stop_path_readiness.v1")
        self.assertEqual(artifact["current_stop_path_readiness_status"], "ready_for_mock_stop_only_probe_not_hil")
        self.assertEqual(artifact["proof_boundary"], "software_proof_o1_o3_current_stop_path_readiness_probe_only")
        self.assertEqual(artifact["stop_endpoint"], "/api/base/stop")
        # 下列字段固定 false，避免 readiness 被误记为 safe-to-control 或 HIL。
        # manual_endpoint_called=false 是本轮 stop-only 合同的核心断言。
        self.assertFalse(artifact["manual_endpoint_called"])
        self.assertFalse(artifact["safe_to_control"])
        self.assertFalse(artifact["hil_pass"])
        self.assertFalse(artifact["route_execution_success"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["robot_control_executed"])
        self.assertFalse(artifact["nonzero_motion_command_sent"])
        self.assertFalse(artifact["uses_real_uart"])

        # zero-stop plan 必须覆盖 vendor 三条安全停车候选：T=1、T=11、T=13。
        # 使用字面 dict 断言，避免字段名或整数 0 在 artifact 中漂移。
        # 如果后续删除任一候选 stop 命令，这个测试会直接失败。
        self.assertIn({"T": 1, "L": 0, "R": 0}, artifact["zero_stop_command_plan"])
        self.assertIn({"T": 11, "L": 0, "R": 0}, artifact["zero_stop_command_plan"])
        self.assertIn({"T": 13, "X": 0, "Z": 0}, artifact["zero_stop_command_plan"])
        self.assertIn("T=1 speed control zero-stop {L=0,R=0}", artifact["zero_stop_command_plan_summary"])
        self.assertIn("T=11 PWM input zero-stop {L=0,R=0}", artifact["zero_stop_command_plan_summary"])
        self.assertIn("T=13 ROS control zero-stop {X=0,Z=0}", artifact["zero_stop_command_plan_summary"])

    def test_mock_virtual_serial_frames_are_newline_json_and_zero_only(self):
        readiness = _module()

        artifact = readiness.build_current_stop_path_readiness_artifact(generated_at="2026-07-13T09:11:00Z")
        validation = artifact["mock_virtual_serial_validation"]

        # 这里验证的是虚拟串口 bytes 合同，不是 WAVE ROVER 实机 ACK。
        # frame_count=3 对应 T=1/T=11/T=13 三条候选 stop frame。
        self.assertEqual(validation["frame_count"], 3)
        self.assertTrue(validation["all_frames_newline_terminated"])
        self.assertTrue(validation["all_frames_json_objects"])
        self.assertTrue(validation["all_motion_axes_zero"])
        for frame in validation["frames"]:
            # 循环逐帧检查，避免聚合字段掩盖某一条坏 frame。
            # frame_text 保留换行，证明协议层没有丢掉固件需要的终止符。
            self.assertTrue(frame["frame_text"].endswith("\n"))
            self.assertTrue(frame["all_motion_axes_zero"])
            # 回读 JSON 与 command 一致，证明 artifact 中的 frame 可机读。
            self.assertEqual(json.loads(frame["frame_text"]), frame["command"])

    def test_no_motion_guards_and_vendor_sources_are_machine_readable(self):
        readiness = _module()

        artifact = readiness.build_current_stop_path_readiness_artifact(generated_at="2026-07-13T09:11:00Z")
        guards = " ".join(artifact["no_motion_control_guard"])
        vendor_text = json.dumps(artifact["vendor_source_summary"], sort_keys=True)

        # guard 字符串给验收脚本和后续 Product closeout 直接做机器读取。
        # 三个禁止项分别覆盖 HTTP manual、ROS topic、Nav2 action 三类风险入口。
        self.assertIn("no /api/base/manual", guards)
        self.assertIn("no /cmd_vel", guards)
        self.assertIn("no NavigateToPose", guards)
        # vendor source 断言防止后续删掉硬件事实出处。
        # 这些路径必须留在 artifact 中，便于 reviewer 回查资料来源。
        self.assertIn("docs/vendor/VENDOR_INDEX.md", artifact["vendor_sources"])
        self.assertIn("docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py", artifact["vendor_sources"])
        self.assertIn("docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h", artifact["vendor_sources"])
        self.assertIn("docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h", artifact["vendor_sources"])
        self.assertIn("docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h", artifact["vendor_sources"])
        self.assertIn("docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_config.h", artifact["vendor_sources"])
        # heartbeat 只允许作为 source readback 摘要出现，不代表实测触发。
        self.assertIn("heartbeat", vendor_text)
        self.assertIn("HEART_BEAT_DELAY=3000", vendor_text)

    def test_nonzero_stop_plan_fails_closed(self):
        readiness = _module()

        # 故意传入 L=0.1，验证 helper 不接受任何非零 motion axis。
        # 这个负例覆盖的是安全边界，不是 vendor 支持范围。
        artifact = readiness.build_current_stop_path_readiness_artifact(
            generated_at="2026-07-13T09:11:00Z",
            commands=[{"T": 1, "L": 0.1, "R": 0}],
        )

        # 任何非零运动轴都必须把 readiness artifact 降级为 blocked。
        # 即使 blocked，安全字段也必须继续保持 false。
        self.assertEqual(artifact["current_stop_path_readiness_status"], "blocked_invalid_stop_path_readiness_probe")
        self.assertIn("nonzero_motion_axis_in_stop_plan", artifact["blocked_reasons"])
        self.assertIn("missing_zero_stop_T_11", artifact["blocked_reasons"])
        self.assertFalse(artifact["safe_to_control"])
        self.assertFalse(artifact["hil_pass"])

    def test_cli_writes_default_schema_artifact(self):
        readiness = _module()

        with tempfile.TemporaryDirectory() as tmpdir:
            # 临时目录避免测试覆盖 sprint 正式 artifact。
            # stdout 单独捕获，证明 CLI 对自动化日志友好。
            output = Path(tmpdir) / "stop_path_readiness.json"
            with redirect_stdout(io.StringIO()) as stdout:
                result = readiness.main(["--output", str(output)])
            artifact = json.loads(output.read_text(encoding="utf-8"))

        # CLI 成功只代表离线 readiness artifact 已写出。
        # route_execution_success 仍必须 false，防止 CLI exit 0 被误读成路线成功。
        # stop_endpoint 仍然固定为 /api/base/stop，不允许 CLI 参数覆盖。
        self.assertEqual(result, 0)
        self.assertIn("ready_for_mock_stop_only_probe_not_hil", stdout.getvalue())
        self.assertEqual(artifact["schema"], "trashbot.o1.current_stop_path_readiness.v1")
        self.assertEqual(artifact["stop_endpoint"], "/api/base/stop")
        self.assertFalse(artifact["route_execution_success"])


if __name__ == "__main__":
    unittest.main()
