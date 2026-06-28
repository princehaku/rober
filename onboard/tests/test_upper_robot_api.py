"""upper_robot_api 的底盘反馈 ACK 单元测试。

这些测试只覆盖非运动反馈链路，因为本轮任务禁止发送任何运动命令。
测试目标不是证明 HIL pass，而是防止 API status 再次退回硬编码 false。
`T=1001` 来自 WAVE ROVER vendor feedback，不能被包装成项目任务 ACK。
真实板上 yaw 可能不可用，所以 ACK 判定必须和 yaw 数值解析解耦。
fresh readback 的优先级高于 artifact，避免旧材料污染本轮证据。
artifact fallback 只接受 fresh 文件，stale 文件只能作为历史摘要。
status 允许发送 `T=130`，但必须持续关闭所有运动控制许可。
这些边界直接对应 sprint 的上车 evidence capture 缺口。
"""

import importlib.util
import asyncio
import json
import shlex
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "upper_robot_api.py"
# 脚本不在 Python package 中，测试必须按路径加载真实文件。
SPEC = importlib.util.spec_from_file_location("upper_robot_api", MODULE_PATH)
upper_robot_api = importlib.util.module_from_spec(SPEC)
# 这里显式断言 loader 存在，避免路径错误时测试静默跳过。
assert SPEC is not None and SPEC.loader is not None
SPEC.loader.exec_module(upper_robot_api)


class UpperRobotApiFeedbackAckTests(unittest.TestCase):
    """锁定 `/api/base/status.feedback_ack` 的新鲜证据和安全字段。"""

    def test_t1001_frame_allows_null_yaw(self) -> None:
        """ACK 只证明底盘反馈帧到达，不要求 yaw 可用于姿态发布。"""
        # 真实板上 yaw 可能是字符串 "null"，ACK 只证明 T=1001 到达。
        frame = {"T": 1001, "L": 0, "R": 0, "r": 0, "p": 0, "y": "null", "v": 10.5}

        # `y` 不参与 ACK，避免姿态不可用时把电压/轮速反馈一起丢掉。
        self.assertTrue(upper_robot_api.t1001_feedback_observed_in_frame(frame))
        # 部分 JSON 来源可能把 `T` 序列化成字符串，status 也要容错。
        self.assertEqual(1001, upper_robot_api.feedback_type_from_frame({"T": "1001", "y": None}))

    def test_serial_feedback_parser_salvages_t1001_before_noisy_tail(self) -> None:
        """现场 UART 会把合法 JSON 和损坏碎片粘一行，不能因此丢掉 T1001。"""
        raw_line = (
            b'{"T":1001,"L":0,"R":0,"r":-1.675361514,"p":0.726515055,'
            b'"y":"null","v":12.4262495}\r{""10,L:,R:,r:172667""078468""ul"""1.29}\n'
        )

        frames = upper_robot_api.parse_serial_json_objects(raw_line)

        self.assertEqual(1, len(frames))
        self.assertTrue(upper_robot_api.t1001_feedback_observed_in_frame(frames[0]))
        self.assertEqual(0, frames[0]["L"])
        self.assertEqual("null", frames[0]["y"])

    def test_feedback_status_keeps_observed_t1001_when_late_read_error_happens(self) -> None:
        """读到 T1001 后的串口读空错误要保留部分成功状态，不能退回全失败。"""
        status = upper_robot_api.feedback_request_status(
            serial_open_ok=True,
            serial_write_ok=True,
            t1001_observed=True,
            import_error=None,
            read_error={
                "type": "SerialException",
                "message": "device reports readiness to read but returned no data",
            },
        )

        self.assertEqual("observed_with_read_error", status)

    def test_feedback_payload_keeps_partial_observed_status_with_read_error(self) -> None:
        """payload 层也必须保留 observed_with_read_error，避免 PC 看到互相矛盾的字段。"""
        payload = upper_robot_api.build_base_feedback_payload(
            port="/dev/ttyS5",
            baudrate=115200,
            read_timeout_s=0.2,
            read_window_s=1.2,
            serial_open={"ok": True},
            serial_write={"ok": True, "command": {"T": 130}},
            serial_read={
                "ok": False,
                "window_s": 1.2,
                "error": {"type": "SerialException", "message": "late read error"},
            },
            read_line_count=2,
            parsed_json_count=1,
            invalid_json_count=1,
            observed_feedback_types=[1001],
            t1001_feedback_frames=[{"T": 1001, "L": 0, "R": 0, "y": "null"}],
            t1001_feedback_status=upper_robot_api.feedback_request_status(
                serial_open_ok=True,
                serial_write_ok=True,
                t1001_observed=True,
                import_error=None,
                read_error={"type": "SerialException", "message": "late read error"},
            ),
        )

        self.assertEqual("observed_with_read_error", payload["t1001_feedback_status"])
        self.assertTrue(payload["feedback_ack"]["t1001_observed"])
        self.assertEqual([1001], payload["observed_feedback_types"])

    def test_feedback_ack_prefers_fresh_readback(self) -> None:
        """本次 readback 已观测 T=1001 时，stale artifact 不能改变来源。"""
        # status 必须优先使用本轮 readback，不能依赖旧 artifact 伪造新鲜 ACK。
        readback = {
            "feedback_ack": {
                "t1001_observed": True,
                "reason": "observed in test",
            }
        }
        stale_artifact = {
            "freshness": {"status": "stale"},
            "latest_t1001_observed_count": 3,
        }

        ack = upper_robot_api.feedback_ack_from_fresh_evidence(readback, stale_artifact)

        # stale artifact 仍可展示历史摘要，但不能覆盖 fresh_readback 来源。
        self.assertTrue(ack["t1001_observed"])
        self.assertEqual("fresh_readback", ack["source"])
        self.assertFalse(ack["robot_ack_connected"])

    def test_feedback_ack_accepts_only_fresh_artifact_fallback(self) -> None:
        """artifact 兜底必须受 freshness 限制，避免复用历史上车材料。"""
        # artifact 只有在 fresh 且包含 T=1001 计数时，才能作为 status ACK 兜底。
        readback = {"feedback_ack": {"t1001_observed": False, "reason": "not observed"}}
        fresh_artifact = {
            "freshness": {"status": "fresh"},
            "latest_t1001_observed_count": 1,
        }
        stale_artifact = {
            "freshness": {"status": "stale"},
            "latest_t1001_observed_count": 1,
        }

        fresh_ack = upper_robot_api.feedback_ack_from_fresh_evidence(readback, fresh_artifact)
        stale_ack = upper_robot_api.feedback_ack_from_fresh_evidence(readback, stale_artifact)

        # 只有 fresh artifact 能作为兜底，stale artifact 必须继续返回 false。
        self.assertTrue(fresh_ack["t1001_observed"])
        self.assertEqual("fresh_artifact", fresh_ack["source"])
        self.assertFalse(stale_ack["t1001_observed"])

    def test_feedback_samples_payload_summarizes_lr_nonzero_t1001_frames(self) -> None:
        """多样本反馈必须把同一 T1001 帧内的 L/R 非零材料结构化保留。"""
        # 第一帧是零轮速，只能证明反馈链路；第二帧同帧 L/R 非零才算 wheel material。
        payload = upper_robot_api.build_base_feedback_samples_payload(
            port="/dev/ttyS5",
            baudrate=115200,
            sample_count=2,
            sample_interval_s=0.0,
            read_timeout_s=0.2,
            read_window_s=1.2,
            samples=[
                {
                    "schema": "trashbot.upper_robot_api.v1.base_feedback_request_result",
                    "observed_feedback_types": [1001],
                    "t1001_feedback_frames": [{"T": 1001, "L": 0, "R": 0, "r": 0, "p": 0, "y": "null", "v": 10.5}],
                    "feedback_ack": {"t1001_observed": True},
                    "wheel_feedback_summary": {"lr_nonzero_observed": False},
                },
                {
                    "schema": "trashbot.upper_robot_api.v1.base_feedback_request_result",
                    "observed_feedback_types": [1001],
                    "t1001_feedback_frames": [{"T": 1001, "L": 0.08, "R": 0.08, "r": 0, "p": 0, "y": None, "v": 10.6}],
                    "feedback_ack": {"t1001_observed": True},
                    "wheel_feedback_summary": {"lr_nonzero_observed": True},
                },
            ],
        )

        # wheel proof 只来自同一帧 L/R 同时非零，不会打开任何控制或 HIL 标志。
        self.assertEqual(2, payload["t1001_observed_count"])
        self.assertTrue(payload["wheel_feedback_nonzero_observed"])
        self.assertTrue(payload["wheel_feedback_lr_nonzero_proven"])
        self.assertEqual(1, payload["wheel_feedback_summary"]["nonzero_frame_count"])
        self.assertEqual(0.08, payload["wheel_feedback_summary"]["latest_pair"]["left_speed"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["hil_pass"])
        self.assertFalse(payload["sends_motion_commands"])

    def test_bridge_feedback_debug_log_summarizes_latest_wheel_raw(self) -> None:
        """bridge 已持有 UART 时，API 必须能从 debug JSONL 只读恢复 wheel raw。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "wave_rover_feedback_debug.jsonl"
            log_path.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "schema": "trashbot.wave_rover.feedback_debug.v1",
                                "source": "wave_rover_uart_t1001",
                                "left_speed": 0,
                                "right_speed": 0,
                                "roll": 0.0,
                                "pitch": 0.0,
                                "yaw": None,
                                "yaw_available": False,
                                "voltage": 12.2,
                            }
                        ),
                        json.dumps(
                            {
                                "schema": "trashbot.wave_rover.feedback_debug.v1",
                                "source": "wave_rover_uart_t1001",
                                "left_speed": 0.08,
                                "right_speed": 0.07,
                                "roll": 1.2,
                                "pitch": 0.4,
                                "yaw": 3.0,
                                "yaw_available": True,
                                "voltage": 12.1,
                            }
                        ),
                    ]
                ),
                encoding="utf-8",
            )

            summary = upper_robot_api.summarize_bridge_feedback_debug_log(str(log_path))

        self.assertEqual("loaded", summary["artifact"]["status"])
        self.assertEqual("fresh", summary["freshness"]["status"])
        self.assertEqual(2, summary["t1001_observed_count"])
        self.assertTrue(summary["wheel_feedback_lr_nonzero_proven"])
        self.assertEqual(0.08, summary["wheel_feedback_summary"]["latest_pair"]["left_speed"])
        self.assertEqual(0.07, summary["wheel_feedback_summary"]["latest_pair"]["right_speed"])
        self.assertFalse(summary["sends_motion_commands"])
        self.assertFalse(summary["safe_to_control"])

    def test_feedback_latest_readback_lifts_wheel_summary_without_commands(self) -> None:
        """latest GET 必须把 wheel material 提到顶层，且保持只读回放边界。"""
        latest = {
            "schema": "trashbot.upper_robot_api.v1.base_feedback_samples_result",
            "wheel_feedback_summary": {
                "lr_nonzero_observed": True,
                "nonzero_frame_count": 1,
                "latest_pair": {"left_speed": 0.08, "right_speed": 0.08},
            },
            "wheel_feedback_lr_nonzero_proven": True,
        }

        payload = upper_robot_api.build_latest_readback_payload(
            "/tmp/base_feedback_samples_latest.json",
            {"ok": True, "status": "loaded"},
            latest,
        )

        # PC evidence capture 只压缩顶层 key，所以 latest readback 必须显式提升该字段。
        self.assertTrue(payload["wheel_feedback_lr_nonzero_proven"])
        self.assertTrue(payload["wheel_feedback_nonzero_observed"])
        self.assertFalse(payload["readback_sends_commands"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["robot_control_executed"])

    def test_feedback_samples_tracks_imu_motion_signal_without_wheel_claim(self) -> None:
        """IMU 姿态变化只能证明运动迹象，不能冒充 L/R 轮速非零。"""
        payload = upper_robot_api.build_base_feedback_samples_payload(
            port="/dev/ttyS5",
            baudrate=115200,
            sample_count=2,
            sample_interval_s=0.0,
            read_timeout_s=0.2,
            read_window_s=0.5,
            samples=[
                {
                    "observed_feedback_types": [1001],
                    "t1001_feedback_frames": [{"T": 1001, "L": 0, "R": 0, "r": -1.6, "p": 0.3, "y": "null", "v": 12.4}],
                    "feedback_ack": {"t1001_observed": True},
                },
                {
                    "observed_feedback_types": [1001],
                    "t1001_feedback_frames": [{"T": 1001, "L": 0, "R": 0, "r": -9.4, "p": 4.5, "y": "null", "v": 12.4}],
                    "feedback_ack": {"t1001_observed": True},
                },
            ],
        )

        self.assertFalse(payload["wheel_feedback_lr_nonzero_proven"])
        self.assertTrue(payload["imu_attitude_delta_observed"])
        self.assertTrue(payload["motion_signal_observed"])
        self.assertEqual("imu_attitude_delta", payload["motion_signal_source"])
        self.assertFalse(payload["safe_to_control"])

    def test_base_status_reports_non_motion_readback_without_control_enable(self) -> None:
        """bridge feedback 不新鲜时，status fallback 可做 T=130 探测但不能开启控制。"""
        # 只有 bridge JSONL 不 fresh 时才允许旧 T=130 fallback，避免正常刷新抢 bridge UART。
        with tempfile.TemporaryDirectory() as temp_dir:
            api = upper_robot_api.UpperRobotApi(
                camera_base_url="http://127.0.0.1:8088",
                base_port="/dev/ttyS5",
                base_baudrate=115200,
                max_speed=0.12,
                feedback_samples_artifact_path=str(Path(temp_dir) / "missing.json"),
            )
            fake_readback = {
                "feedback_ack": {"t1001_observed": True},
                "sends_commands": True,
                "sends_motion_commands": False,
            }

            # mock readback 可以验证 status 汇总，不需要在单元测试中打开串口。
            with mock.patch.object(upper_robot_api, "request_base_feedback_once", return_value=fake_readback):
                with mock.patch.object(
                    upper_robot_api,
                    "summarize_bridge_feedback_debug_log",
                    return_value={"freshness": {"status": "missing"}},
                ):
                    # 设备存在性和 pyserial 可用性也 mock，避免本地开发机依赖 `/dev/ttyS5`。
                    with mock.patch.object(upper_robot_api, "describe_path", return_value={"exists": True}):
                        with mock.patch.object(upper_robot_api, "load_serial_module", return_value=(object(), None)):
                            status = api.base_status()

        # ACK 为 true 不能外溢成任何运动许可或任务完成结论。
        self.assertTrue(status["feedback_ack"]["t1001_observed"])
        self.assertEqual("fresh_readback", status["feedback_ack"]["source"])
        self.assertTrue(status["readback_sends_commands"])
        self.assertTrue(status["sends_commands"])
        # T=130 属于反馈请求；只要运动字段保持 false，就不会误导现场操作。
        self.assertFalse(status["sends_motion_commands"])
        self.assertFalse(status["safe_to_control"])
        self.assertFalse(status["primary_actions_enabled"])
        self.assertFalse(status["robot_control_executed"])

    def test_base_status_ignores_stale_wheel_nonzero_artifact(self) -> None:
        """当前 L/R 证明必须来自本次 readback 或 fresh artifact，不能复用旧非零材料。"""
        api = upper_robot_api.UpperRobotApi(
            camera_base_url="http://127.0.0.1:8088",
            base_port="/dev/ttyS5",
            base_baudrate=115200,
            max_speed=0.12,
        )
        zero_readback = {
            "feedback_ack": {"t1001_observed": True},
            "wheel_feedback_lr_nonzero_proven": False,
            "wheel_feedback_nonzero_observed": False,
            "sends_commands": True,
            "sends_motion_commands": False,
        }
        stale_nonzero_artifact = {
            "freshness": {"status": "stale"},
            "latest_t1001_observed_count": 2,
            "wheel_feedback_lr_nonzero_proven": True,
            "wheel_feedback_nonzero_observed": True,
        }

        with mock.patch.object(upper_robot_api, "request_base_feedback_once", return_value=zero_readback):
            with mock.patch.object(upper_robot_api, "summarize_feedback_samples_latest_artifact", return_value=stale_nonzero_artifact):
                with mock.patch.object(
                    upper_robot_api,
                    "summarize_bridge_feedback_debug_log",
                    return_value={"freshness": {"status": "missing"}},
                ):
                    with mock.patch.object(upper_robot_api, "describe_path", return_value={"exists": True}):
                        with mock.patch.object(upper_robot_api, "load_serial_module", return_value=(object(), None)):
                            status = api.base_status()

        self.assertFalse(status["wheel_feedback_nonzero_observed"])
        self.assertFalse(status["wheel_feedback_lr_nonzero_proven"])
        self.assertTrue(status["feedback_samples_latest"]["wheel_feedback_lr_nonzero_proven"])
        self.assertEqual("stale", status["feedback_samples_latest"]["freshness"]["status"])
        self.assertFalse(status["safe_to_control"])

    def test_base_status_lifts_fresh_bridge_feedback_without_uart_claim(self) -> None:
        """bridge debug log fresh 时，base status 只读日志，不再打开 UART。"""
        api = upper_robot_api.UpperRobotApi(
            camera_base_url="http://127.0.0.1:8088",
            base_port="/dev/ttyS5",
            base_baudrate=115200,
            max_speed=0.12,
        )
        bridge_summary = {
            "freshness": {"status": "fresh"},
            "t1001_observed_count": 3,
            "wheel_feedback_lr_nonzero_proven": True,
            "wheel_feedback_nonzero_observed": True,
            "wheel_feedback_summary": {
                "latest_pair": {"source": "vendor_t1001_L_R", "left_speed": 0.08, "right_speed": 0.07},
                "lr_nonzero_observed": True,
            },
            "motion_signal_observed": True,
            "motion_signal_source": "wheel_feedback_lr",
            "sends_motion_commands": False,
            "safe_to_control": False,
        }

        with mock.patch.object(upper_robot_api, "request_base_feedback_once") as request_feedback:
            with mock.patch.object(upper_robot_api, "summarize_feedback_samples_latest_artifact", return_value={"freshness": {"status": "missing"}}):
                with mock.patch.object(upper_robot_api, "summarize_bridge_feedback_debug_log", return_value=bridge_summary):
                    with mock.patch.object(upper_robot_api, "describe_path", return_value={"exists": True}):
                        with mock.patch.object(upper_robot_api, "load_serial_module", return_value=(object(), None)):
                            status = api.base_status()

        request_feedback.assert_not_called()
        self.assertEqual("fresh_bridge_feedback_debug_log", status["feedback_ack"]["source"])
        self.assertFalse(status["readback_sends_commands"])
        self.assertFalse(status["sends_commands"])
        self.assertFalse(status["feedback_readback"]["request"]["attempted"])
        self.assertTrue(status["wheel_feedback_lr_nonzero_proven"])
        self.assertEqual(0.08, status["wheel_feedback_summary"]["latest_pair"]["left_speed"])
        self.assertEqual(bridge_summary, status["bridge_feedback_debug"])
        self.assertEqual("wheel_feedback_lr", status["motion_signal_source"])
        self.assertFalse(status["safe_to_control"])

    def test_manual_control_pwm_diagnostic_samples_wheel_feedback_during_motion_window(self) -> None:
        """PWM 诊断点动必须在停车前采样轮速，避免动作后 0/0 覆盖真实运动材料。"""
        api = upper_robot_api.UpperRobotApi(
            camera_base_url="http://127.0.0.1:8088",
            base_port="/dev/ttyS5",
            base_baudrate=115200,
            max_speed=0.12,
        )
        during_feedback = {
            "t1001_feedback_status": "observed",
            "t1001_feedback_frames": [{"T": 1001, "L": 0.04, "R": 0.04, "y": "null"}],
            "feedback_ack": {"t1001_observed": True},
        }
        after_feedback = {
            "t1001_feedback_status": "observed",
            "t1001_feedback_frames": [{"T": 1001, "L": 0, "R": 0, "y": "null"}],
            "feedback_ack": {"t1001_observed": True},
        }

        transaction = {
            "command_result": {"ok": True, "bytes_written": 26, "command": {"T": 1, "L": 0.04, "R": 0.04}},
            "stop_result": {"ok": True, "bytes_written": 20, "command": {"T": 1, "L": 0, "R": 0}},
            "feedback_during_motion": during_feedback,
            "feedback_after_stop": after_feedback,
            "serial_session_error": None,
        }

        with mock.patch.object(upper_robot_api, "persist_feedback_samples_artifact", side_effect=lambda _path, payload: {**payload, "artifact": {"write": {"ok": True}}}):
            with mock.patch.object(upper_robot_api, "manual_motion_serial_transaction", return_value=transaction) as mocked_transaction:
                payload = asyncio.run(
                    api.manual_control(
                        {
                            "direction": "forward",
                            "speed": 0.04,
                            "duration_ms": 300,
                            "command_mode": "pwm",
                            "motion_read_window_s": 0.05,
                        }
                    )
                )

        self.assertTrue(payload["manual_command_executed"])
        self.assertTrue(payload["auto_stop_executed"])
        self.assertTrue(payload["feedback_during_motion_attempted"])
        mocked_transaction.assert_called_once()
        self.assertEqual({"T": 11, "L": 164, "R": 164}, mocked_transaction.call_args.kwargs["command"])
        self.assertEqual(
            [{"T": 11, "L": 0, "R": 0}, {"T": 1, "L": 0, "R": 0}, {"T": 13, "X": 0, "Z": 0}],
            mocked_transaction.call_args.kwargs["stop_commands"],
        )
        self.assertEqual(transaction, payload["serial_motion_transaction"])
        self.assertIsNone(payload["ros_cmd_vel_transaction"])
        self.assertEqual("pwm", payload["base_command_mode"])
        self.assertTrue(payload["manual_feedback_samples_latest"]["wheel_feedback_lr_nonzero_proven"])
        self.assertTrue(payload["wheel_feedback_lr_nonzero_proven"])
        self.assertEqual(1, payload["manual_wheel_feedback_summary"]["nonzero_frame_count"])
        self.assertEqual(0.04, payload["manual_wheel_feedback_summary"]["latest_nonzero_pair"]["left_speed"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["delivery_success"])
        self.assertFalse(payload["primary_actions_enabled"])

    def test_manual_control_default_motion_window_tracks_pulse_duration(self) -> None:
        """默认 ROS 手控必须走 /cmd_vel bridge，不再抢 esp32_bridge 持有的 UART。"""
        api = upper_robot_api.UpperRobotApi(
            camera_base_url="http://127.0.0.1:8088",
            base_port="/dev/ttyS5",
            base_baudrate=115200,
            max_speed=0.12,
        )
        transaction = {
            "mode": "ros_cmd_vel_bridge",
            "command_result": {"ok": True, "mode": "ros_cmd_vel_once", "linear_x": 0.08, "angular_z": 0.0},
            "stop_result": {"ok": True, "mode": "ros_cmd_vel_once", "linear_x": 0.0, "angular_z": 0.0},
            "feedback_during_motion": upper_robot_api.skipped_manual_feedback_payload("/dev/ttyS5", 115200, "ros_cmd_vel_path_uses_bridge_feedback_not_direct_uart"),
            "feedback_after_stop": upper_robot_api.skipped_manual_feedback_payload("/dev/ttyS5", 115200, "ros_cmd_vel_path_uses_bridge_feedback_not_direct_uart"),
            "serial_session_error": None,
        }

        with mock.patch.object(upper_robot_api, "manual_motion_serial_transaction") as mocked_serial_transaction:
            with mock.patch.object(upper_robot_api, "manual_motion_ros_cmd_vel_transaction", return_value=transaction) as mocked_transaction:
                payload = asyncio.run(api.manual_control({"direction": "forward", "speed": 0.08, "duration_ms": 500}))

        kwargs = mocked_transaction.call_args.kwargs
        mocked_serial_transaction.assert_not_called()
        self.assertEqual(500, kwargs["pulse_ms"])
        self.assertEqual({"T": 13, "X": 0.08, "Z": 0.0}, kwargs["command"])
        self.assertEqual(transaction, payload["ros_cmd_vel_transaction"])
        self.assertIsNone(payload["serial_motion_transaction"])
        self.assertIsNone(payload["manual_feedback_samples_latest"])
        self.assertTrue(payload["manual_command_executed"])

    def test_manual_control_keyboard_pulse_keeps_short_motion_window(self) -> None:
        """键盘连续手控 240ms pulse 走短 /cmd_vel 事务，避免串口读阻塞续发。"""
        api = upper_robot_api.UpperRobotApi(
            camera_base_url="http://127.0.0.1:8088",
            base_port="/dev/ttyS5",
            base_baudrate=115200,
            max_speed=0.12,
        )
        transaction = {
            "mode": "ros_cmd_vel_bridge",
            "command_result": {"ok": True, "mode": "ros_cmd_vel_once", "linear_x": 0.08, "angular_z": 0.0},
            "stop_result": {"ok": True, "mode": "ros_cmd_vel_once", "linear_x": 0.0, "angular_z": 0.0},
            "feedback_during_motion": upper_robot_api.skipped_manual_feedback_payload("/dev/ttyS5", 115200, "ros_cmd_vel_path_uses_bridge_feedback_not_direct_uart"),
            "feedback_after_stop": upper_robot_api.skipped_manual_feedback_payload("/dev/ttyS5", 115200, "ros_cmd_vel_path_uses_bridge_feedback_not_direct_uart"),
            "serial_session_error": None,
        }

        with mock.patch.object(upper_robot_api, "manual_motion_serial_transaction") as mocked_serial_transaction:
            with mock.patch.object(upper_robot_api, "manual_motion_ros_cmd_vel_transaction", return_value=transaction) as mocked_transaction:
                payload = asyncio.run(api.manual_control({"direction": "forward", "speed": 0.08, "duration_ms": 240}))

        kwargs = mocked_transaction.call_args.kwargs
        mocked_serial_transaction.assert_not_called()
        self.assertEqual(240, kwargs["pulse_ms"])
        self.assertEqual({"T": 13, "X": 0.08, "Z": 0.0}, kwargs["command"])
        self.assertEqual(transaction, payload["ros_cmd_vel_transaction"])
        self.assertIsNone(payload["manual_feedback_samples_latest"])
        self.assertTrue(payload["manual_command_executed"])

    def test_manual_control_allows_explicit_pwm_diagnostic_override(self) -> None:
        """PWM 只作为显式诊断模式保留，普通手控默认不再走旧 PWM 控制入口。"""
        api = upper_robot_api.UpperRobotApi(
            camera_base_url="http://127.0.0.1:8088",
            base_port="/dev/ttyS5",
            base_baudrate=115200,
            max_speed=0.12,
        )
        transaction = {
            "command_result": {"ok": True, "bytes_written": 22, "command": {"T": 11, "L": 164, "R": 164}},
            "stop_result": {"ok": True, "bytes_written": 20, "command": {"T": 11, "L": 0, "R": 0}},
            "feedback_during_motion": {
                "t1001_feedback_status": "observed",
                "t1001_feedback_frames": [{"T": 1001, "L": 0, "R": 0, "y": "null"}],
                "feedback_ack": {"t1001_observed": True},
            },
            "feedback_after_stop": {
                "t1001_feedback_status": "observed",
                "t1001_feedback_frames": [{"T": 1001, "L": 0, "R": 0, "y": "null"}],
                "feedback_ack": {"t1001_observed": True},
            },
            "serial_session_error": None,
        }

        with mock.patch.object(upper_robot_api, "persist_feedback_samples_artifact", side_effect=lambda _path, payload: {**payload, "artifact": {"write": {"ok": True}}}):
            with mock.patch.object(upper_robot_api, "manual_motion_serial_transaction", return_value=transaction) as mocked_transaction:
                payload = asyncio.run(api.manual_control({"direction": "forward", "speed": 0.08, "duration_ms": 240, "command_mode": "pwm"}))

        self.assertEqual({"T": 11, "L": 164, "R": 164}, mocked_transaction.call_args.kwargs["command"])
        self.assertEqual("pwm", payload["base_command_mode"])
        self.assertTrue(payload["manual_command_executed"])
        self.assertFalse(payload["safe_to_control"])

    def test_operator_report_persists_structured_hil_claims_without_hil_pass(self) -> None:
        """结构化 HIL 字段必须可机器回读，但 report 本身仍不是 HIL pass。"""
        # 这些字段来自人工现场材料；即使全部声明为 true，也只能作为 claim 保存。
        report = {
            "operator_present": True,
            "evidence_ref": "field-hil-structured-test",
            "physical_clearance_confirmed": True,
            "emergency_stop_ready": True,
            "observed_motion": True,
            "observed_stop": True,
            "operator_notes": "structured material claim only",
            "reported_at": "2026-06-11T05:45:00+08:00",
            "external_video_recorded": "true",
            "external_video_ref": "sprints/test/artifacts/external.mp4",
            "visible_content_proven": True,
            "camera_artifacts_ref": "runtime/camera_visibility/latest_metrics.json",
            "wheel_feedback_lr_nonzero_proven": "false",
            "wheel_feedback_ref": "runtime/wave_rover_feedback_debug.jsonl",
            "physical_motion_lidar_delta_proven": False,
            "scan_delta_ref": "runtime/scan_delta/latest_metrics.json",
            "real_route_map_proven": False,
            "route_map_ref": "runtime/maps/field_route_manifest.json",
            "delivery_success": True,
            "site_state": "bench_no_motion_report_smoke",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = Path(temp_dir) / "operator_report_latest.json"
            api = upper_robot_api.UpperRobotApi(
                camera_base_url="http://127.0.0.1:8088",
                base_port="/dev/ttyS5",
                base_baudrate=115200,
                max_speed=0.12,
                operator_report_artifact_path=str(artifact_path),
            )

            payload = api.operator_report(report)
            http_status, latest = api.operator_report_latest()
            persisted = json.loads(artifact_path.read_text(encoding="utf-8"))

        claims = payload["structured_hil_claims"]
        # POST、artifact、GET 三处都要回显同一份机器字段，避免只能塞 notes 文本。
        self.assertEqual(200, http_status)
        self.assertEqual(claims, persisted["structured_hil_claims"])
        self.assertEqual(claims, latest["structured_hil_claims"])
        self.assertTrue(claims["external_video_recorded"])
        self.assertEqual("sprints/test/artifacts/external.mp4", claims["external_video_ref"])
        self.assertTrue(claims["visible_content_proven"])
        self.assertFalse(claims["wheel_feedback_lr_nonzero_proven"])
        self.assertFalse(claims["physical_motion_lidar_delta_proven"])
        self.assertFalse(claims["real_route_map_proven"])
        self.assertTrue(claims["delivery_success"])
        self.assertEqual("bench_no_motion_report_smoke", claims["site_state"])

        # 顶层安全字段必须保持 fail-closed，delivery claim 不能升级成交付或 HIL 通过。
        for candidate in (payload, persisted, latest):
            self.assertTrue(candidate["operator_report_material_only"])
            self.assertFalse(candidate["hil_pass"])
            self.assertFalse(candidate["delivery_success"])
            self.assertFalse(candidate["sends_motion_commands"])
            self.assertFalse(candidate["opens_serial"])
            self.assertFalse(candidate["report_replaces_stop_status_ack_or_hil"])

    def test_operator_report_accepts_nested_structured_hil_claims(self) -> None:
        """PC/上位机可直接提交 nested claims，顶层 delivery_success 仍被固定关闭。"""
        report = {
            "operator_present": True,
            "evidence_ref": "field-hil-nested-claims-test",
            "physical_clearance_confirmed": True,
            "emergency_stop_ready": True,
            "observed_motion": False,
            "observed_stop": True,
            "operator_notes": "nested structured claim only",
            "reported_at": "2026-06-11T05:46:00+08:00",
            "structured_hil_claims": {
                "external_video_recorded": False,
                "external_video_ref": "none",
                "visible_content_proven": "true",
                "camera_artifacts_ref": "camera-visible.json",
                "wheel_feedback_lr_nonzero_proven": False,
                "wheel_feedback_ref": "feedback.jsonl",
                "physical_motion_lidar_delta_proven": False,
                "scan_delta_ref": "scan-delta.json",
                "real_route_map_proven": False,
                "route_map_ref": "route-map.json",
                "delivery_success": True,
                "site_state": "floor_stationary",
            },
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            payload = upper_robot_api.build_operator_report_payload(
                str(Path(temp_dir) / "operator_report_latest.json"),
                report,
            )

        claims = payload["operator_report"]["structured_hil_claims"]
        self.assertTrue(claims["visible_content_proven"])
        self.assertTrue(claims["delivery_success"])
        self.assertFalse(payload["delivery_success"])
        self.assertFalse(payload["hil_pass"])
        self.assertFalse(payload["sends_motion_commands"])

    def test_delivery_completion_gate_blocks_missing_operator_material(self) -> None:
        """Nav2 成功不能单独推出送达成功，缺现场材料时必须 fail closed。"""
        # 最近 Nav2 goal 已成功，但 operator latest 缺失时只能生成 blocked artifact。
        nav2_latest = {
            "latest_result": {
                "status": "goal_succeeded",
                "evidence_ref": "o11-nav2-goal-execution-test",
                "goal_accepted": True,
                "result_received": True,
                "result_status": "succeeded",
                "feedback_sample_count": 8,
            }
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            payload = upper_robot_api.build_delivery_completion_payload(
                path=str(Path(temp_dir) / "delivery_completion_latest.json"),
                request={"confirm_delivery_completion": True, "delivery_evidence_ref": "delivery-test"},
                nav2_http_status=200,
                nav2_latest=nav2_latest,
                operator_http_status=404,
                operator_latest={},
            )

        self.assertEqual("blocked_missing_delivery_material", payload["status"])
        self.assertFalse(payload["delivery_success"])
        self.assertIn("operator_report_latest_http_200", payload["missing_required_material"])
        self.assertIn("structured_hil_claims.delivery_success", payload["missing_required_material"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["primary_actions_enabled"])
        self.assertFalse(payload["robot_control_executed"])

    def test_delivery_completion_gate_confirms_only_with_full_material(self) -> None:
        """送达成功只能由 delivery gate 在 Nav2 与现场材料齐备时合成。"""
        # 这里模拟已经由独立 endpoint 写好的 latest artifact，gate 本身不发任何运动命令。
        nav2_latest = {
            "latest_result": {
                "status": "goal_succeeded",
                "evidence_ref": "o11-nav2-goal-execution-test",
                "goal_accepted": True,
                "result_received": True,
                "result_status": "succeeded",
                "feedback_sample_count": 8,
            }
        }
        claims = {
            "external_video_recorded": True,
            "external_video_ref": "field-video-ref",
            "visible_content_proven": False,
            "camera_artifacts_ref": "",
            "wheel_feedback_lr_nonzero_proven": True,
            "wheel_feedback_ref": "wheel-ref",
            "physical_motion_lidar_delta_proven": True,
            "scan_delta_ref": "scan-ref",
            "real_route_map_proven": True,
            "route_map_ref": "route-map-ref",
            "delivery_success": True,
            "site_state": "operator_confirmed_delivery_complete",
        }
        operator_latest = {
            "latest_result": {
                "operator_report_status": "ready_for_review",
                "operator_report": {
                    "evidence_ref": "operator-report-ref",
                    "observed_motion": True,
                    "observed_stop": True,
                    "structured_hil_claims": claims,
                },
            }
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = Path(temp_dir) / "delivery_completion_latest.json"
            payload = upper_robot_api.build_delivery_completion_payload(
                path=str(artifact_path),
                request={"confirm_delivery_completion": True, "delivery_evidence_ref": "delivery-test"},
                nav2_http_status=200,
                nav2_latest=nav2_latest,
                operator_http_status=200,
                operator_latest=operator_latest,
            )
            persisted = json.loads(artifact_path.read_text(encoding="utf-8"))

        self.assertEqual("delivery_success_confirmed", payload["status"])
        self.assertTrue(payload["delivery_success"])
        self.assertEqual([], payload["missing_required_material"])
        self.assertEqual(payload["delivery_success"], persisted["delivery_success"])
        self.assertEqual("route-map-ref", payload["operator_report"]["structured_hil_claims"]["route_map_ref"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["primary_actions_enabled"])
        self.assertFalse(payload["hil_pass"])
        self.assertFalse(payload["robot_control_executed"])
        self.assertFalse(payload["sends_motion_commands"])

    def test_camera_probe_request_is_whitelisted(self) -> None:
        """camera probe HTTP body 只能影响白名单参数，不能注入任意 argv。"""
        request = upper_robot_api.safe_camera_probe_request(
            {
                "device": "/tmp/not-video;rm -rf /",
                "fourcc": "H264",
                "width": 99999,
                "height": 1,
                "fps": 999,
                "timeout_s": 99,
                "read_call_timeout_s": 99,
                "include_backend_smoke": "yes please",
            }
        )

        self.assertEqual("/dev/video1", request["device"])
        self.assertEqual("MJPG", request["fourcc"])
        self.assertEqual(1920, request["width"])
        self.assertEqual(120, request["height"])
        self.assertEqual(30.0, request["fps"])
        self.assertEqual(8.0, request["timeout_s"])
        self.assertEqual(8.0, request["read_call_timeout_s"])
        self.assertFalse(request["include_backend_smoke"])
        self.assertFalse(request["auto_format_fallback"])

    def test_camera_probe_missing_script_fails_closed_without_serial_or_motion(self) -> None:
        """首帧探针脚本不存在时也必须结构化失败，且不触碰底盘。"""
        with mock.patch.object(upper_robot_api.Path, "exists", return_value=False):
            http_status, payload = asyncio.run(upper_robot_api.run_camera_first_frame_probe({"device": "/dev/video1"}))

        self.assertEqual(503, http_status)
        self.assertEqual("probe_script_missing", payload["status"])
        self.assertFalse(payload["opens_serial"])
        self.assertFalse(payload["sends_motion_commands"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["robot_control_executed"])

    def test_camera_probe_parses_subprocess_json_without_control_enable(self) -> None:
        """首帧探针成功执行时只回传 camera JSON，不提升控制许可。"""

        class FakeProcess:
            returncode = 0

            async def communicate(self):
                payload = {
                    "schema": "trashbot.camera_first_frame_probe.v1",
                    "status": "first_frame_timeout",
                    "open_ok": True,
                    "read_ok": False,
                    "first_frame_timeout": True,
                    "visible_content_proven": False,
                }
                return json.dumps(payload).encode("utf-8"), b""

            def kill(self) -> None:
                self.killed = True

        with mock.patch.object(upper_robot_api.Path, "exists", return_value=True):
            with mock.patch.object(upper_robot_api.asyncio, "create_subprocess_exec", return_value=FakeProcess()) as process_mock:
                http_status, payload = asyncio.run(
                    upper_robot_api.run_camera_first_frame_probe({"fourcc": "MJPG", "include_backend_smoke": True})
                )

        self.assertEqual(503, http_status)
        self.assertEqual("first_frame_timeout", payload["status"])
        self.assertTrue(payload["probe_payload"]["open_ok"])
        self.assertFalse(payload["probe_payload"]["read_ok"])
        self.assertFalse(payload["probe_payload"]["visible_content_proven"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["robot_control_executed"])
        self.assertFalse(payload["sends_motion_commands"])
        self.assertFalse(payload["opens_serial"])
        command = process_mock.call_args.args
        self.assertIn("--sample-path", command)
        sample_path = command[command.index("--sample-path") + 1]
        self.assertIn("/runtime/camera/first_frame_probe_", sample_path)
        self.assertIn("--include-backend-smoke", process_mock.call_args.args)

    def test_camera_probe_auto_format_fallback_stops_after_first_frame(self) -> None:
        """自动格式 fallback 只读相机；前一个格式失败后尝试下一组，读到帧就停止。"""

        class FakeProcess:
            def __init__(self, payload: dict[str, object]) -> None:
                self.returncode = 0
                self.payload = payload

            async def communicate(self):
                return json.dumps(self.payload).encode("utf-8"), b""

            def kill(self) -> None:
                self.killed = True

        payloads = [
            {
                "schema": "trashbot.camera_first_frame_probe.v1",
                "status": "first_frame_timeout",
                "requested_fourcc": "MJPG",
                "requested_width": 640,
                "requested_height": 480,
                "requested_fps": 15.0,
                "open_ok": True,
                "read_ok": False,
                "failure_reason": "capture_read_call_timeout",
                "visible_content_proven": False,
            },
            {
                "schema": "trashbot.camera_first_frame_probe.v1",
                "status": "first_frame_timeout",
                "requested_fourcc": "MJPG",
                "requested_width": 640,
                "requested_height": 480,
                "requested_fps": 30.0,
                "open_ok": True,
                "read_ok": False,
                "failure_reason": "capture_read_returned_false",
                "visible_content_proven": False,
            },
            {
                "schema": "trashbot.camera_first_frame_probe.v1",
                "status": "first_frame_timeout",
                "requested_fourcc": "MJPG",
                "requested_width": 1280,
                "requested_height": 720,
                "requested_fps": 30.0,
                "open_ok": True,
                "read_ok": False,
                "failure_reason": "capture_read_returned_false",
                "visible_content_proven": False,
            },
            {
                "schema": "trashbot.camera_first_frame_probe.v1",
                "status": "first_frame_timeout",
                "requested_fourcc": "MJPG",
                "requested_width": 480,
                "requested_height": 320,
                "requested_fps": 30.0,
                "open_ok": True,
                "read_ok": False,
                "failure_reason": "capture_read_returned_false",
                "visible_content_proven": False,
            },
            {
                "schema": "trashbot.camera_first_frame_probe.v1",
                "status": "frame_read",
                "requested_fourcc": "YUYV",
                "requested_width": 640,
                "requested_height": 480,
                "requested_fps": 22.0,
                "open_ok": True,
                "read_ok": True,
                "visible_content_proven": True,
            },
        ]
        processes = [FakeProcess(payload) for payload in payloads]

        with mock.patch.object(upper_robot_api.Path, "exists", return_value=True):
            with mock.patch.object(upper_robot_api.asyncio, "create_subprocess_exec", side_effect=processes) as process_mock:
                http_status, payload = asyncio.run(
                    upper_robot_api.run_camera_first_frame_probe(
                        {"fourcc": "MJPG", "auto_format_fallback": True, "include_backend_smoke": False}
                    )
                )

        self.assertEqual(200, http_status)
        self.assertEqual("frame_read", payload["status"])
        self.assertTrue(payload["auto_format_fallback"])
        self.assertEqual(5, len(payload["fallback_attempts"]))
        self.assertEqual("MJPG", payload["fallback_attempts"][0]["fourcc"])
        self.assertEqual(15.0, payload["fallback_attempts"][0]["fps"])
        self.assertEqual("MJPG", payload["fallback_attempts"][1]["fourcc"])
        self.assertEqual(30.0, payload["fallback_attempts"][1]["fps"])
        self.assertEqual("MJPG", payload["fallback_attempts"][2]["fourcc"])
        self.assertEqual(1280, payload["fallback_attempts"][2]["width"])
        self.assertEqual("MJPG", payload["fallback_attempts"][3]["fourcc"])
        self.assertEqual(480, payload["fallback_attempts"][3]["width"])
        self.assertEqual("YUYV", payload["fallback_attempts"][4]["fourcc"])
        self.assertEqual(22.0, payload["fallback_attempts"][4]["fps"])
        self.assertEqual(5, process_mock.call_count)
        self.assertIn("30.0", process_mock.call_args_list[1].args)
        self.assertIn("22.0", process_mock.call_args_list[4].args)
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["robot_control_executed"])

    def test_map_proof_latest_promotes_clean_runtime_material(self) -> None:
        """map proof 观测齐全时，readback 顶层应直接暴露可消费状态。"""
        # 这里用最小可读 artifact 模拟真实 no-motion helper 产物，避免依赖远端硬件。
        clean_artifact = {
            "schema": "trashbot.upper_robot_api.v1.map_lifecycle_runtime_proof",
            "status": "map_once_artifact_metadata_observed",
            "proof_state": "map_once_artifact_metadata_observed",
            "evidence_type": "robot_runtime_material",
            "not_proven": False,
            "proof": {
                "status": "map_once_artifact_metadata_observed",
                "scan_once_observed": True,
                "map_once_observed": True,
                "map_file_observed": True,
                "map_metadata_observed": True,
                "evidence_ref": "map-proof-clean",
                "slam_toolbox_state": "runtime_attempted",
                "slam_map_quality": {
                    "navigation_quality": "has_free_cells",
                    "has_free_cells": True,
                    "cell_counts": {"free": 7, "unknown": 2, "occupied": 1, "other": 0},
                },
                "algorithm_boundary": {
                    "slam_map_quality_evaluated": True,
                    "map_usable_for_navigation": True,
                },
            },
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = Path(temp_dir) / "map_lifecycle_latest.json"
            artifact_path.write_text(json.dumps(clean_artifact), encoding="utf-8")
            api = upper_robot_api.UpperRobotApi(
                camera_base_url="http://127.0.0.1:8088",
                base_port="/dev/ttyS5",
                base_baudrate=115200,
                max_speed=0.12,
                map_lifecycle_proof_artifact_path=str(artifact_path),
            )

            http_status, payload = api.map_proof_latest()
            status = api.map_status()

        # 观测链条齐全时，顶层状态必须和 artifact proof 一致，而不是继续卡在 not_proven。
        self.assertEqual(200, http_status)
        self.assertEqual("map_once_artifact_metadata_observed", payload["status"])
        self.assertEqual("map_once_artifact_metadata_observed", payload["proof_state"])
        self.assertTrue(payload["ros2_runtime_proven"])
        self.assertTrue(payload["map_artifact_proven"])
        self.assertTrue(payload["latest_map_usable_for_navigation"])
        self.assertEqual("has_free_cells", payload["latest_map_quality_status"])
        self.assertEqual(7, payload["latest_map_free_cell_count"])
        self.assertFalse(payload["not_proven"])
        self.assertFalse(payload["software_guard"])
        # 安全面仍然必须关闭，证明地图材料可消费不等于可发车。
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["delivery_success"])
        self.assertFalse(payload["primary_actions_enabled"])
        self.assertFalse(payload["robot_control_executed"])
        self.assertFalse(payload["sends_motion_commands"])
        self.assertFalse(payload["sends_base_motion_commands"])
        self.assertFalse(payload["uses_base_uart"])

        # status 页面要把同一份 proof 摘要抬给 PC 点灯。
        proof_latest = status["proof_latest"]
        self.assertEqual("map_once_artifact_metadata_observed", proof_latest["status"])
        self.assertEqual("map_once_artifact_metadata_observed", proof_latest["proof_state"])
        self.assertTrue(proof_latest["ros2_runtime_proven"])
        self.assertTrue(proof_latest["map_artifact_proven"])
        self.assertFalse(proof_latest["not_proven"])
        self.assertFalse(proof_latest["software_guard"])
        self.assertTrue(proof_latest["latest_map_once_observed"])
        self.assertTrue(proof_latest["latest_map_file_observed"])
        self.assertTrue(proof_latest["latest_map_metadata_observed"])

    def test_map_proof_latest_fails_closed_on_bad_json(self) -> None:
        """坏 JSON 仍必须 fail closed，不能把地图材料误判成已证明。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = Path(temp_dir) / "map_lifecycle_latest.json"
            artifact_path.write_text("{bad json", encoding="utf-8")
            api = upper_robot_api.UpperRobotApi(
                camera_base_url="http://127.0.0.1:8088",
                base_port="/dev/ttyS5",
                base_baudrate=115200,
                max_speed=0.12,
                map_lifecycle_proof_artifact_path=str(artifact_path),
            )

            http_status, payload = api.map_proof_latest()

        # 解析失败时，接口继续按 software guard 处理，安全字段不能被翻开。
        self.assertEqual(422, http_status)
        self.assertEqual("not_proven", payload["status"])
        self.assertEqual("not_proven", payload["proof_state"])
        self.assertTrue(payload["software_guard"])
        self.assertTrue(payload["not_proven"])
        self.assertFalse(payload["ros2_runtime_proven"])
        self.assertFalse(payload["map_artifact_proven"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["delivery_success"])
        self.assertFalse(payload["primary_actions_enabled"])

    def test_map_proof_refresh_attaches_readback_contract(self) -> None:
        """refresh 成功时应把 readback contract 抬到顶层，不再保留 not attached 话术。"""
        clean_artifact = {
            "schema": "trashbot.upper_robot_api.v1.map_lifecycle_runtime_proof",
            "status": "map_once_artifact_metadata_observed",
            "proof_state": "map_once_artifact_metadata_observed",
            "evidence_type": "robot_runtime_material",
            "not_proven": False,
            "proof": {
                "status": "map_once_artifact_metadata_observed",
                "scan_once_observed": True,
                "map_once_observed": True,
                "map_file_observed": True,
                "map_metadata_observed": True,
                "evidence_ref": "map-proof-refresh-clean",
                "slam_toolbox_state": "runtime_attempted",
            },
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = Path(temp_dir) / "map_lifecycle_latest.json"
            artifact_path.write_text(json.dumps(clean_artifact), encoding="utf-8")
            api = upper_robot_api.UpperRobotApi(
                camera_base_url="http://127.0.0.1:8088",
                base_port="/dev/ttyS5",
                base_baudrate=115200,
                max_speed=0.12,
                map_lifecycle_proof_artifact_path=str(artifact_path),
            )

            with mock.patch.object(
                upper_robot_api,
                "run_map_lifecycle_proof_helper",
                return_value={"ok": True, "executed": True, "returncode": 0, "elapsed_ms": 1},
            ):
                payload = asyncio.run(api.map_proof_refresh({"timeout_s": 60}))

        # command ok + proof ok 时，顶层必须显示 observed，而不是继续保守成未证明。
        self.assertEqual("map_once_artifact_metadata_observed", payload["status"])
        self.assertEqual("map_once_artifact_metadata_observed", payload["proof_state"])
        self.assertFalse(payload["not_proven"])
        self.assertFalse(payload["software_guard"])
        self.assertTrue(payload["ros2_runtime_proven"])
        self.assertTrue(payload["map_artifact_proven"])
        self.assertIsNone(payload["failure_reason"])
        self.assertEqual(
            "map lifecycle proof attached and ready for read-only consumption",
            payload["operator_message"],
        )
        self.assertEqual(200, payload["latest_readback_http_status"])
        self.assertEqual("map_once_artifact_metadata_observed", payload["latest_result"]["status"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["delivery_success"])
        self.assertFalse(payload["sends_motion_commands"])

    def test_map_start_uses_no_motion_helper_with_safe_map_name(self) -> None:
        """`/api/map/start` 直连 helper，不能再退回 command_not_configured。"""
        clean_artifact = {
            "schema": "trashbot.upper_robot_api.v1.map_lifecycle_runtime_proof",
            "status": "map_once_artifact_metadata_observed",
            "proof": {
                "status": "map_once_artifact_metadata_observed",
                "scan_once_observed": True,
                "map_once_observed": True,
                "map_file_observed": True,
                "map_metadata_observed": True,
                "evidence_ref": "map-start-control-clean",
            },
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = Path(temp_dir) / "map_lifecycle_latest.json"
            artifact_path.write_text(json.dumps(clean_artifact), encoding="utf-8")
            map_dir = Path(temp_dir) / "maps"
            api = upper_robot_api.UpperRobotApi(
                camera_base_url="http://127.0.0.1:8088",
                base_port="/dev/ttyS5",
                base_baudrate=115200,
                max_speed=0.12,
                map_artifact_dir=str(map_dir),
                map_lifecycle_proof_artifact_path=str(artifact_path),
            )

            with mock.patch.object(
                upper_robot_api,
                "run_map_lifecycle_proof_helper",
                return_value={"mode": "map_lifecycle_proof_helper", "ok": True, "executed": True, "returncode": 0},
            ) as helper_mock:
                payload = api.map_control("start", {"map_name": "floor_1", "artifact_path": "/tmp/ignored.yaml"})

        helper_mock.assert_called_once()
        helper_kwargs = helper_mock.call_args.kwargs
        self.assertEqual("floor_1", helper_kwargs["map_name"])
        self.assertEqual(str(map_dir), helper_kwargs["map_artifact_dir"])
        self.assertEqual(str(artifact_path), helper_kwargs["artifact_path"])
        self.assertTrue(payload["command_result"]["executed"])
        self.assertTrue(payload["command_result"]["ok"])
        self.assertNotEqual("command_not_configured", payload["failure_reason"])
        self.assertIsNone(payload["failure_reason"])
        self.assertTrue(payload["artifact_path_ignored"])
        self.assertEqual("/tmp/ignored.yaml", payload["requested_artifact_path"])
        self.assertEqual("map_once_artifact_metadata_observed", payload["status"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["sends_motion_commands"])
        self.assertFalse(payload["publishes_cmd_vel"])
        self.assertFalse(payload["calls_base_manual"])
        self.assertFalse(payload["uses_base_uart"])

    def test_map_save_rejects_unsafe_map_name_without_helper_execution(self) -> None:
        """非法 map_name 必须在 subprocess 前失败，避免路径或 shell 片段进入 argv。"""
        api = upper_robot_api.UpperRobotApi(
            camera_base_url="http://127.0.0.1:8088",
            base_port="/dev/ttyS5",
            base_baudrate=115200,
            max_speed=0.12,
        )

        with mock.patch.object(upper_robot_api, "run_map_lifecycle_proof_helper") as helper_mock:
            payload = api.map_control("save", {"map_name": "../bad"})

        helper_mock.assert_not_called()
        self.assertEqual("invalid_map_name", payload["failure_reason"])
        self.assertEqual(["invalid_map_name"], payload["blocked_reasons"])
        self.assertFalse(payload["command_result"]["executed"])
        self.assertFalse(payload["safe_to_control"])

    def test_map_list_reports_no_free_cell_quality(self) -> None:
        """map list 必须把 free=0 的 YAML/PGM 标成需重新建图，而不是只说文件存在。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            map_dir = Path(temp_dir) / "maps"
            map_dir.mkdir()
            # PGM 像素全部 unknown/occupied，模拟真实板端当前不可导航地图。
            (map_dir / "floor_1.pgm").write_bytes(b"P5\n3 2\n255\n" + bytes([205, 205, 205, 0, 205, 205]))
            (map_dir / "floor_1.yaml").write_text(
                "image: floor_1.pgm\nresolution: 0.05\norigin: [0.0, -1.0, 0.0]\n",
                encoding="utf-8",
            )
            api = upper_robot_api.UpperRobotApi(
                camera_base_url="http://127.0.0.1:8088",
                base_port="/dev/ttyS5",
                base_baudrate=115200,
                max_speed=0.12,
                map_artifact_dir=str(map_dir),
            )

            payload = api.map_list()

        self.assertEqual(2, payload["map_count"])
        self.assertFalse(payload["map_usable_for_navigation"])
        self.assertTrue(payload["map_needs_rebuild"])
        self.assertEqual("no_free_cells", payload["map_quality_summary"]["status"])
        self.assertEqual(1, payload["map_quality_summary"]["no_free_cell_map_count"])
        yaml_entry = next(entry for entry in payload["maps"] if entry["name"] == "floor_1.yaml")
        self.assertTrue(yaml_entry["quality"]["ok"])
        self.assertFalse(yaml_entry["quality"]["has_free_cells"])
        self.assertEqual(0, yaml_entry["quality"]["cell_counts"]["free"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["robot_control_executed"])

    def test_radar_lifecycle_validation_accepts_lidar_only_start_stop(self) -> None:
        """start/stop 只接受受管 LiDAR lifecycle 脚本和 LiDAR 串口。"""
        start = (
            "bash /root/rober/onboard/scripts/o1_lidar_lifecycle.sh start "
            "--serial-port /dev/ttyACM0 --serial-baudrate 150000 --frame-id laser_frame"
        )
        stop = "bash /root/rober/onboard/scripts/o1_lidar_lifecycle.sh stop"

        start_argv, start_error = upper_robot_api.validate_radar_lifecycle_command(start, "start")
        stop_argv, stop_error = upper_robot_api.validate_radar_lifecycle_command(stop, "stop")

        self.assertIsNone(start_error)
        self.assertIsNone(stop_error)
        self.assertIn("o1_lidar_lifecycle.sh", start_argv[1])
        self.assertEqual("stop", stop_argv[2])

    def test_radar_status_defaults_to_managed_lifecycle_commands(self) -> None:
        """默认上位机应可启动 LiDAR lifecycle，不再要求现场额外设置环境变量。"""
        api = upper_robot_api.UpperRobotApi(
            camera_base_url="http://127.0.0.1:8088",
            base_port="/dev/ttyS5",
            base_baudrate=115200,
            max_speed=0.12,
        )

        status = api.radar_status()

        start_command = status["controls"]["start"]["command"]
        stop_command = status["controls"]["stop"]["command"]
        self.assertTrue(start_command["configured"])
        self.assertEqual("command", start_command["mode"])
        self.assertIn("o1_lidar_lifecycle.sh", start_command["argv"][1])
        self.assertIn("/dev/ttyACM0", start_command["argv"])
        self.assertEqual("150000", start_command["argv"][start_command["argv"].index("--serial-baudrate") + 1])
        self.assertTrue(stop_command["configured"])
        self.assertEqual("command", stop_command["mode"])
        self.assertFalse(status["sends_motion_commands"])
        self.assertFalse(status["calls_base_manual"])
        self.assertFalse(status["safe_to_control"])

    def test_radar_control_uses_default_managed_lifecycle_command(self) -> None:
        """未显式传入命令时，start 使用默认 LiDAR-only lifecycle 脚本。"""
        api = upper_robot_api.UpperRobotApi(
            camera_base_url="http://127.0.0.1:8088",
            base_port="/dev/ttyS5",
            base_baudrate=115200,
            max_speed=0.12,
        )

        with mock.patch.object(
            upper_robot_api,
            "run_configured_command",
            return_value={"mode": "command", "executed": True, "ok": True, "returncode": 0},
        ) as run_mock:
            payload = api.radar_control("start")

        run_mock.assert_called_once_with(upper_robot_api.DEFAULT_RADAR_START_COMMAND)
        self.assertTrue(payload["command_result"]["executed"])
        self.assertTrue(payload["command_result"]["ok"])
        self.assertEqual(
            shlex.split(upper_robot_api.DEFAULT_RADAR_START_COMMAND),
            payload["configured_command"]["argv"],
        )
        self.assertFalse(payload["base_uart_touched"])
        self.assertFalse(payload["sends_base_motion_commands"])
        self.assertFalse(payload["safe_to_control"])

    def test_radar_lifecycle_validation_rejects_base_uart_and_motion_tokens(self) -> None:
        """雷达命令不能指向 WAVE ROVER UART，也不能夹带底盘控制 token。"""
        unsafe_port = (
            "bash /root/rober/onboard/scripts/o1_lidar_lifecycle.sh start "
            "--serial-port /dev/ttyS5 --serial-baudrate 150000"
        )
        unsafe_token = "bash /root/rober/onboard/scripts/o1_lidar_lifecycle.sh start --serial-port /dev/ttyACM0 T=1"

        _, port_error = upper_robot_api.validate_radar_lifecycle_command(unsafe_port, "start")
        _, token_error = upper_robot_api.validate_radar_lifecycle_command(unsafe_token, "start")

        self.assertIsNotNone(port_error)
        self.assertEqual("unsafe_runtime_command", port_error["type"])
        self.assertIsNotNone(token_error)
        self.assertEqual("unsafe_runtime_command", token_error["type"])

    def test_radar_control_uses_validated_lifecycle_command_contract(self) -> None:
        """API radar start 成功只代表 lifecycle 命令执行，不打开运动许可。"""
        command = (
            "bash /root/rober/onboard/scripts/o1_lidar_lifecycle.sh start "
            "--serial-port /dev/ttyACM0 --serial-baudrate 150000 --frame-id laser_frame"
        )
        api = upper_robot_api.UpperRobotApi(
            camera_base_url="http://127.0.0.1:8088",
            base_port="/dev/ttyS5",
            base_baudrate=115200,
            max_speed=0.12,
            radar_start_command=command,
        )

        with mock.patch.object(
            upper_robot_api,
            "run_configured_command",
            return_value={"mode": "command", "executed": True, "ok": True, "returncode": 0},
        ) as run_mock:
            payload = api.radar_control("start")

        run_mock.assert_called_once_with(command)
        self.assertTrue(payload["command_result"]["executed"])
        self.assertTrue(payload["command_result"]["ok"])
        self.assertIsNone(payload["failure_reason"])
        self.assertEqual("lidar_ros2_driver_only", payload["scope"])
        self.assertFalse(payload["base_uart_touched"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["sends_base_motion_commands"])
        self.assertIn("T=130", payload["blocked_commands_not_sent"])

    def test_radar_control_rejects_unsafe_lifecycle_command_without_execution(self) -> None:
        """危险 radar 命令必须在 subprocess 前失败。"""
        command = (
            "bash /root/rober/onboard/scripts/o1_lidar_lifecycle.sh start "
            "--serial-port /dev/ttyS5 --serial-baudrate 150000"
        )
        api = upper_robot_api.UpperRobotApi(
            camera_base_url="http://127.0.0.1:8088",
            base_port="/dev/ttyS5",
            base_baudrate=115200,
            max_speed=0.12,
            radar_start_command=command,
        )

        with mock.patch.object(upper_robot_api, "run_configured_command") as run_mock:
            payload = api.radar_control("start")

        run_mock.assert_not_called()
        self.assertFalse(payload["command_result"]["executed"])
        self.assertFalse(payload["command_result"]["ok"])
        self.assertEqual("unsafe_runtime_command", payload["command_result"]["error"]["type"])
        self.assertEqual("configured_command_failed", payload["failure_reason"])
        self.assertFalse(payload["base_uart_touched"])
        self.assertFalse(payload["safe_to_control"])

    def test_nav2_status_defaults_to_managed_lifecycle_commands(self) -> None:
        """默认上位机应暴露受管 Nav2 stack-only start/stop，不再是 dry-run stub。"""
        api = upper_robot_api.UpperRobotApi(
            camera_base_url="http://127.0.0.1:8088",
            base_port="/dev/ttyS5",
            base_baudrate=115200,
            max_speed=0.12,
        )

        status = api.nav2_status()

        start_command = status["commands"]["start"]
        stop_command = status["commands"]["stop"]
        status_command = status["commands"]["status"]
        self.assertTrue(start_command["configured"])
        self.assertEqual("command", start_command["mode"])
        self.assertIn("o11_nav2_lifecycle.sh", start_command["argv"][1])
        self.assertIn("/dev/ttyS5", start_command["argv"])
        self.assertIn("ros", start_command["argv"])
        self.assertIn("--base-enabled", start_command["argv"])
        self.assertIn("auto", start_command["argv"])
        self.assertIn("--lidar-enabled", start_command["argv"])
        self.assertIn("--lidar-serial-port", start_command["argv"])
        self.assertIn("/dev/ttyACM0", start_command["argv"])
        self.assertIn("--static-laser-tf-enabled", start_command["argv"])
        self.assertTrue(stop_command["configured"])
        self.assertEqual("command", stop_command["mode"])
        self.assertTrue(status_command["configured"])
        self.assertEqual("status", status_command["argv"][2])
        self.assertIn("lifecycle_manager", status)
        self.assertFalse(status["lifecycle_manager"]["sends_motion_commands"])
        self.assertFalse(status["sends_motion_commands"])
        self.assertFalse(status["sends_base_motion_commands"])
        self.assertFalse(status["safe_to_control"])

    def test_nav2_lifecycle_status_parse_failure_is_not_stopped(self) -> None:
        """status 脚本读不到 JSON 时不能把未知状态误报成 stopped。"""
        parsed = upper_robot_api.parse_nav2_lifecycle_status_result(
            {"mode": "command", "executed": True, "ok": False, "stdout": "", "reason": "script_missing"}
        )

        self.assertEqual("not_loaded", parsed["status"])
        self.assertEqual("not_loaded", parsed["running"])
        self.assertEqual("not_loaded", parsed["state"])
        self.assertFalse(parsed["sends_motion_commands"])

    def test_nav2_lifecycle_status_parses_stdout_preview(self) -> None:
        """run_configured_command 只保存 stdout_preview，status 解析必须消费这个字段。"""
        parsed = upper_robot_api.parse_nav2_lifecycle_status_result(
            {
                "mode": "command",
                "executed": True,
                "ok": True,
                "stdout_preview": json.dumps({"running": False, "state": "stopped", "message": "Nav2 lifecycle not running"}),
            }
        )

        self.assertEqual("loaded", parsed["status"])
        self.assertFalse(parsed["running"])
        self.assertEqual("stopped", parsed["state"])

    def test_nav2_control_uses_default_managed_lifecycle_command(self) -> None:
        """Nav2 start 默认只调用受管 stack-only 脚本，不执行 NavigateToPose。"""
        api = upper_robot_api.UpperRobotApi(
            camera_base_url="http://127.0.0.1:8088",
            base_port="/dev/ttyS5",
            base_baudrate=115200,
            max_speed=0.12,
        )

        with mock.patch.object(
            upper_robot_api,
            "run_configured_command",
            return_value={"mode": "command", "executed": True, "ok": True, "returncode": 0},
        ) as run_mock:
            payload = api.nav2_control("start")

        self.assertEqual(run_mock.call_args_list[0], mock.call(upper_robot_api.DEFAULT_NAV2_START_COMMAND, timeout_s=20.0))
        self.assertEqual(run_mock.call_args_list[1], mock.call(upper_robot_api.DEFAULT_NAV2_STATUS_COMMAND, timeout_s=20.0))
        self.assertEqual(run_mock.call_count, 2)
        self.assertTrue(payload["command_result"]["executed"])
        self.assertTrue(payload["command_result"]["ok"])
        self.assertEqual(
            shlex.split(upper_robot_api.DEFAULT_NAV2_START_COMMAND),
            payload["configured_command"]["argv"],
        )
        self.assertFalse(payload["sends_base_motion_commands"])
        self.assertFalse(payload["safe_to_control"])

    def test_nav2_lifecycle_validation_rejects_unsafe_command_without_execution(self) -> None:
        """Nav2 lifecycle 命令不能夹带 shell、直接 /cmd_vel 或错误底盘串口。"""
        unsafe_shell = "bash /root/rober/onboard/scripts/o11_nav2_lifecycle.sh start; ros2 topic pub /cmd_vel"
        unsafe_token = "bash /root/rober/onboard/scripts/o11_nav2_lifecycle.sh start /cmd_vel"
        unsafe_port = (
            "bash /root/rober/onboard/scripts/o11_nav2_lifecycle.sh start "
            "--base-port /dev/ttyACM0 --command-mode ros"
        )
        unsafe_lidar_port = (
            "bash /root/rober/onboard/scripts/o11_nav2_lifecycle.sh start "
            "--base-port /dev/ttyS5 --command-mode ros --lidar-serial-port /dev/ttyS5"
        )
        unsafe_lidar_flag = (
            "bash /root/rober/onboard/scripts/o11_nav2_lifecycle.sh start "
            "--base-port /dev/ttyS5 --command-mode ros --lidar-enabled maybe"
        )

        _, shell_error = upper_robot_api.validate_nav2_lifecycle_command(unsafe_shell, "start")
        _, token_error = upper_robot_api.validate_nav2_lifecycle_command(unsafe_token, "start")
        _, port_error = upper_robot_api.validate_nav2_lifecycle_command(unsafe_port, "start")
        _, lidar_port_error = upper_robot_api.validate_nav2_lifecycle_command(unsafe_lidar_port, "start")
        _, lidar_flag_error = upper_robot_api.validate_nav2_lifecycle_command(unsafe_lidar_flag, "start")

        self.assertIsNotNone(shell_error)
        self.assertEqual("unsafe_runtime_command", shell_error["type"])
        self.assertIsNotNone(token_error)
        self.assertEqual("unsafe_runtime_command", token_error["type"])
        self.assertIsNotNone(port_error)
        self.assertEqual("unsafe_base_serial_path", port_error["type"])
        self.assertIsNotNone(lidar_port_error)
        self.assertEqual("unsafe_lidar_serial_path", lidar_port_error["type"])
        self.assertIsNotNone(lidar_flag_error)
        self.assertEqual("unsupported_nav2_lifecycle_flag", lidar_flag_error["type"])

    def test_nav2_control_rejects_unmanaged_lifecycle_command_without_execution(self) -> None:
        """API nav2 start 只能走 o11_nav2_lifecycle.sh，不能直接执行 ros2 launch 字符串。"""
        api = upper_robot_api.UpperRobotApi(
            camera_base_url="http://127.0.0.1:8088",
            base_port="/dev/ttyS5",
            base_baudrate=115200,
            max_speed=0.12,
            nav2_start_command="ros2 launch ros2_trashbot_bringup autonomous.launch.py",
        )

        with mock.patch.object(upper_robot_api, "run_configured_command") as run_mock:
            payload = api.nav2_control("start")

        run_mock.assert_called_once_with(upper_robot_api.DEFAULT_NAV2_STATUS_COMMAND, timeout_s=20.0)
        self.assertFalse(payload["command_result"]["executed"])
        self.assertFalse(payload["command_result"]["ok"])
        self.assertEqual("unsupported_runtime_command", payload["command_result"]["error"]["type"])
        self.assertFalse(payload["sends_base_motion_commands"])
        self.assertFalse(payload["safe_to_control"])

    def test_free_roam_start_requires_operator_confirmation(self) -> None:
        """自动扫图 start 必须来自普通首屏安全确认，裸 POST 不能放开状态机。"""
        api = upper_robot_api.UpperRobotApi(
            camera_base_url="http://127.0.0.1:8088",
            base_port="/dev/ttyS5",
            base_baudrate=115200,
            max_speed=0.12,
        )

        with mock.patch.object(upper_robot_api, "run_free_roam_param_sequence") as run_mock:
            payload = api.free_roam_autonomy_control("start", {})

        run_mock.assert_not_called()
        self.assertEqual("blocked_missing_confirmation", payload["status"])
        self.assertIn("confirm_operator_safety", payload["missing_confirmations"])
        self.assertNotIn("confirm_mapping_active", payload["missing_confirmations"])
        self.assertFalse(payload["command_result"]["executed"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["publishes_cmd_vel"])

    def test_free_roam_latest_marks_runtime_artifact_as_state_machine_observed(self) -> None:
        """runtime artifact 来自 free_roam_autonomy_node，应证明状态机存在但不提升控制权限。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = Path(temp_dir) / "free_roam_autonomy_latest.json"
            artifact_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.free_roam_autonomy.runtime.v1",
                        "artifact_only": True,
                        "cmd_vel_publish_enabled": False,
                        "decision": {
                            "schema": "trashbot.free_roam_autonomy.decision.v1",
                            "state": "stopping",
                            "reason": "现场请求停止",
                            "stop_required": True,
                            "gates": [],
                        },
                        "snapshot": {"operator_confirmed": False},
                        "map_metrics": {"free_cells": 1},
                    }
                ),
                encoding="utf-8",
            )
            api = upper_robot_api.UpperRobotApi(
                camera_base_url="http://127.0.0.1:8088",
                base_port="/dev/ttyS5",
                base_baudrate=115200,
                max_speed=0.12,
                free_roam_autonomy_artifact_path=str(artifact_path),
            )

            latest_status, latest = api.free_roam_autonomy_latest()
            status = api.free_roam_autonomy_status()

        self.assertEqual(200, latest_status)
        self.assertTrue(latest["free_roam_runtime_artifact_proven"])
        self.assertTrue(latest["free_roam_state_machine_observed"])
        self.assertTrue(latest["ros2_runtime_proven"])
        self.assertEqual("stopping", latest["decision_state"])
        self.assertFalse(latest["safe_to_control"])
        self.assertFalse(latest["publishes_cmd_vel"])
        self.assertTrue(status["free_roam_state_machine_observed"])
        self.assertTrue(status["ros2_runtime_proven"])
        self.assertFalse(status["safe_to_control"])

    def test_free_roam_param_sequence_unlocks_motion_only_when_requested(self) -> None:
        """参数序列默认不解锁；只有 readiness 通过后的 start 才写运动发布双锁。"""
        calls: list[list[str]] = []
        timeouts: list[float] = []
        yaml_payloads: list[str] = []

        def fake_run(argv, timeout_s=8.0):  # noqa: ANN001 - 测试 stub 保持签名宽松。
            calls.append(argv)
            timeouts.append(timeout_s)
            yaml_payloads.append(Path(argv[-1]).read_text(encoding="utf-8"))
            return {"mode": "fixed_argv", "executed": True, "ok": True, "argv": argv, "returncode": 0}

        with mock.patch.object(upper_robot_api, "run_fixed_argv_command", side_effect=fake_run):
            locked_result = upper_robot_api.run_free_roam_param_sequence("start")
            unlocked_result = upper_robot_api.run_free_roam_param_sequence("start", enable_motion=True)
            stop_result = upper_robot_api.run_free_roam_param_sequence("stop")

        flattened = "\n".join(yaml_payloads)
        self.assertEqual(3, len(calls))
        self.assertTrue(all(argv[:4] == ["ros2", "param", "load", "/free_roam_autonomy"] for argv in calls))
        self.assertTrue(locked_result["ok"])
        self.assertTrue(unlocked_result["ok"])
        self.assertTrue(stop_result["ok"])
        self.assertIn("operator_confirmed", flattened)
        self.assertIn("mapping_active", flattened)
        self.assertIn("external_stop_requested", flattened)
        self.assertFalse(locked_result["motion_unlock_requested"])
        self.assertTrue(unlocked_result["motion_unlock_requested"])
        self.assertEqual(unlocked_result["blocked_parameters_not_touched"], ["cmd_vel_topic"])
        self.assertIn("motion_hil_unlocked: true", flattened)
        self.assertIn("enable_cmd_vel_publish: true", flattened)
        self.assertIn("motion_hil_unlocked: false", flattened)
        self.assertIn("enable_cmd_vel_publish: false", flattened)
        self.assertTrue(timeouts)
        self.assertTrue(all(timeout == upper_robot_api.FREE_ROAM_PARAM_LOAD_TIMEOUT_S for timeout in timeouts))
        self.assertEqual(
            ["operator_confirmed", "mapping_active", "stop_available", "external_stop_requested"],
            locked_result["touched_parameters"],
        )

    def test_free_roam_param_sequence_stops_after_first_param_timeout(self) -> None:
        """ROS 参数服务不响应时必须快速返回结构化失败，不能让 PC start 长时间卡住。"""
        calls: list[list[str]] = []

        def fake_run(argv, timeout_s=8.0):  # noqa: ANN001 - 测试 stub 保持签名宽松。
            calls.append(argv)
            return {
                "mode": "fixed_argv",
                "executed": True,
                "ok": False,
                "argv": argv,
                "returncode": None,
                "error": "TimeoutExpired",
                "timeout_s": timeout_s,
            }

        with mock.patch.object(upper_robot_api, "run_fixed_argv_command", side_effect=fake_run):
            result = upper_robot_api.run_free_roam_param_sequence("start", enable_motion=True)

        self.assertFalse(result["ok"])
        self.assertEqual([], result["touched_parameters"])
        self.assertEqual(1, len(calls))
        self.assertEqual(["ros2", "param", "load", "/free_roam_autonomy"], calls[0][:4])
        self.assertEqual(upper_robot_api.FREE_ROAM_PARAM_LOAD_TIMEOUT_S, result["results"][0]["timeout_s"])
        self.assertEqual(
            ["motion_hil_unlocked", "enable_cmd_vel_publish", "cmd_vel_topic"],
            result["blocked_parameters_not_touched"],
        )

    def test_fixed_ros2_argv_sources_ros_environment(self) -> None:
        """裸 python 启动上位机 API 时，固定 ros2 argv 也必须先 source ROS 环境。"""
        class FakeProcess:
            """测试用假进程，只验证 argv 包装，不启动真实 ROS2。"""

            pid = 12345
            returncode = 0

            def communicate(self, timeout=None):  # noqa: ANN001 - 模拟 Popen.communicate 签名。
                return ("ok", "")

        with mock.patch.object(upper_robot_api.Path, "exists", return_value=True):
            with mock.patch.object(upper_robot_api.subprocess, "Popen", return_value=FakeProcess()) as popen_mock:
                result = upper_robot_api.run_fixed_argv_command(
                    ["ros2", "param", "set", "/free_roam_autonomy", "operator_confirmed", "true"]
                )

        popen_mock.assert_called_once()
        resolved_argv = popen_mock.call_args.args[0]
        self.assertEqual(["bash", "-lc"], resolved_argv[:2])
        self.assertIn("source /opt/ros/humble/setup.bash", resolved_argv[2])
        self.assertIn("source /root/rober/onboard/install/setup.bash", resolved_argv[2])
        self.assertIn("exec ros2 param set /free_roam_autonomy operator_confirmed true", resolved_argv[2])
        self.assertTrue(result["ok"])
        self.assertTrue(result["ros2_setup_used"])
        self.assertEqual(result["argv"], ["ros2", "param", "set", "/free_roam_autonomy", "operator_confirmed", "true"])

    def test_free_roam_start_unlocks_motion_when_camera_ready_even_if_radar_stale(self) -> None:
        """start 只把相机作为运动硬门禁；雷达 stale 时允许低速降级自移动。"""
        api = upper_robot_api.UpperRobotApi(
            camera_base_url="http://127.0.0.1:8088",
            base_port="/dev/ttyS5",
            base_baudrate=115200,
            max_speed=0.12,
        )
        command_result = {
            "mode": "free_roam_param_sequence",
            "action": "start",
            "executed": True,
            "ok": True,
            "results": [],
            "motion_unlock_requested": True,
            "blocked_parameters_not_touched": ["cmd_vel_topic"],
        }
        readiness = {
            "ready": True,
            "missing": [],
            "camera": {"ready": True},
            "mapping_readiness": {
                "ready": False,
                "missing": ["radar_scan_proof_not_fresh"],
                "free_move_allowed_when_mapping_not_ready": True,
            },
            "motion_without_radar_allowed": True,
            "degraded_without_radar": True,
            "radar": {"ready": False, "optional": True, "blocking": False},
        }

        with mock.patch.object(upper_robot_api, "run_free_roam_param_sequence", return_value=command_result) as run_mock:
            with mock.patch.object(api, "free_roam_motion_readiness", return_value=readiness):
                with mock.patch.object(api, "free_roam_autonomy_latest", return_value=(200, {"decision_state": "ready"})):
                    payload = api.free_roam_autonomy_control(
                        "start",
                        {"confirm_operator_safety": True, "confirm_mapping_active": True},
                    )

        run_mock.assert_called_once_with("start", enable_motion=True, mapping_active=False)
        self.assertEqual("requested", payload["status"])
        self.assertTrue(payload["sets_state_machine_parameters"])
        self.assertFalse(payload["does_not_set_motion_unlock"])
        self.assertTrue(payload["motion_unlock_requested"])
        self.assertTrue(payload["mapping_active_requested"])
        self.assertFalse(payload["mapping_active_applied"])
        self.assertFalse(payload["direct_cmd_vel_publish"])
        self.assertEqual(payload["blocked_parameters_not_touched"], ["cmd_vel_topic"])
        self.assertEqual(payload["sensor_readiness"], readiness)
        self.assertFalse(payload["safe_to_control"])
        self.assertTrue(payload["publishes_cmd_vel"])
        self.assertFalse(payload["uses_base_uart"])

    def test_free_roam_start_allows_motion_when_camera_not_ready_but_mapping_degrades(self) -> None:
        """相机不 ready 只降级建图验收；自由移动仍应写入运动双锁。"""
        api = upper_robot_api.UpperRobotApi(
            camera_base_url="http://127.0.0.1:8088",
            base_port="/dev/ttyS5",
            base_baudrate=115200,
            max_speed=0.12,
        )
        readiness = {
            "ready": True,
            "missing": [],
            "free_move_ready": True,
            "free_move_without_camera_allowed": True,
            "camera": {"ready": False, "missing": ["camera_not_ready"]},
            "mapping_readiness": {
                "ready": False,
                "missing": ["camera_not_ready"],
                "free_move_allowed_when_mapping_not_ready": True,
            },
            "motion_without_radar_allowed": True,
            "degraded_without_radar": False,
            "radar": {"ready": True, "optional": True, "blocking": False},
        }
        command_result = {
            "mode": "free_roam_param_sequence",
            "action": "start",
            "executed": True,
            "ok": True,
            "results": [],
            "motion_unlock_requested": True,
            "blocked_parameters_not_touched": ["cmd_vel_topic"],
        }

        with mock.patch.object(upper_robot_api, "run_free_roam_param_sequence", return_value=command_result) as run_mock:
            with mock.patch.object(api, "free_roam_motion_readiness", return_value=readiness):
                with mock.patch.object(api, "free_roam_autonomy_latest", return_value=(200, {"decision_state": "ready"})):
                    payload = api.free_roam_autonomy_control(
                        "start",
                        {"confirm_operator_safety": True, "confirm_mapping_active": True},
                    )

        run_mock.assert_called_once_with("start", enable_motion=True, mapping_active=False)
        self.assertEqual("requested", payload["status"])
        self.assertEqual([], payload["blocked_reasons"])
        self.assertEqual(readiness, payload["sensor_readiness"])
        self.assertTrue(payload["free_move_start_ready"])
        self.assertEqual([], payload["free_move_blocked_reasons"])
        self.assertFalse(payload["mapping_readiness_ready"])
        self.assertEqual(["camera_not_ready"], payload["mapping_blocked_reasons"])
        self.assertTrue(payload["command_result"]["executed"])
        self.assertFalse(payload["does_not_set_motion_unlock"])
        self.assertTrue(payload["publishes_cmd_vel"])

    def test_camera_motion_readiness_requires_observed_first_frame(self) -> None:
        """相机服务只选中设备但未读到首帧时，不能解锁自动扫图 start。"""
        api = upper_robot_api.UpperRobotApi(
            camera_base_url="http://127.0.0.1:8088",
            base_port="/dev/ttyS5",
            base_baudrate=115200,
            max_speed=0.12,
        )

        class FakeResponse:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self, _limit):
                return json.dumps(
                    {
                        "status": "ready",
                        "video_source": "/dev/video1",
                        "source_readiness": "source_selected_not_probed",
                        "source_failure_reason": "",
                    }
                ).encode("utf-8")

        with mock.patch("urllib.request.urlopen", return_value=FakeResponse()):
            readiness = api.camera_motion_readiness()

        self.assertFalse(readiness["ready"])
        self.assertEqual(["camera_first_frame_not_observed"], readiness["missing"])
        self.assertEqual("source_selected_not_probed", readiness["source_readiness"])

    def test_camera_motion_readiness_accepts_observed_first_frame(self) -> None:
        """相机服务读到真实首帧后，自动扫图 readiness 才能通过 camera gate。"""
        api = upper_robot_api.UpperRobotApi(
            camera_base_url="http://127.0.0.1:8088",
            base_port="/dev/ttyS5",
            base_baudrate=115200,
            max_speed=0.12,
        )

        class FakeResponse:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self, _limit):
                return json.dumps(
                    {
                        "status": "ready",
                        "video_source": "/dev/video1",
                        "source_readiness": "first_frame_observed",
                        "source_failure_reason": "",
                        "last_successful_frame": {
                            "source": "/dev/video1",
                            "channel": "mjpeg",
                            "observed_at_ms": 1782475000000,
                        },
                    }
                ).encode("utf-8")

        with mock.patch("urllib.request.urlopen", return_value=FakeResponse()):
            readiness = api.camera_motion_readiness()

        self.assertTrue(readiness["ready"])
        self.assertEqual([], readiness["missing"])
        self.assertEqual("first_frame_observed", readiness["source_readiness"])
        self.assertEqual("/dev/video1", readiness["last_successful_frame"]["source"])

    def test_shared_camera_mjpeg_relay_broadcasts_one_upstream_to_multiple_clients(self) -> None:
        """多人预览必须复用一条上游 MJPEG，避免每个浏览器都独占打开摄像头。"""

        async def scenario() -> None:
            relay = upper_robot_api.SharedCameraMjpegRelay("http://127.0.0.1:8088/mjpeg")
            starts = 0

            async def fake_upstream() -> None:
                nonlocal starts
                starts += 1
                relay.content_type = "multipart/x-mixed-replace; boundary=roberframe"
                relay.content_type_loaded.set()
                await relay._broadcast(b"--roberframe\r\nContent-Type: image/jpeg\r\n\r\nreal\r\n")
                await asyncio.sleep(0)

            relay._run_upstream = fake_upstream
            first = relay.register()
            second = relay.register()
            await asyncio.wait_for(relay.content_type_loaded.wait(), timeout=1)

            self.assertEqual(1, starts)
            self.assertEqual(2, relay.snapshot()["client_count"])
            self.assertTrue(relay.snapshot()["shared_capture"])
            self.assertFalse(relay.snapshot()["exclusive_camera_claim"])
            self.assertEqual(b"--roberframe\r\nContent-Type: image/jpeg\r\n\r\nreal\r\n", await asyncio.wait_for(first.get(), timeout=1))
            self.assertEqual(b"--roberframe\r\nContent-Type: image/jpeg\r\n\r\nreal\r\n", await asyncio.wait_for(second.get(), timeout=1))

            relay.unregister(first)
            relay.unregister(second)

        asyncio.run(scenario())

    def test_shared_camera_mjpeg_relay_preserves_upstream_first_frame_error_body(self) -> None:
        """8088 无首帧的 JSON 失败体必须透出，否则 PC 只会看到泛化 502。"""
        relay = upper_robot_api.SharedCameraMjpegRelay("http://127.0.0.1:8088/mjpeg")
        relay.mark_upstream_failure(
            503,
            {
                "error": "first_frame_unreadable",
                "failure_reason": "first_frame_total_timeout",
                "first_frame_format_attempts": [
                    {"label": "MJPG@640x480@15", "status": "first_frame_unreadable"},
                    {"label": "YUYV@640x480@22", "status": "first_frame_unreadable"},
                    {"label": "default@current", "status": "first_frame_unreadable"},
                ],
            },
        )

        snapshot = relay.snapshot()
        self.assertEqual(503, snapshot["last_remote_http_status"])
        self.assertEqual("first_frame_total_timeout", snapshot["last_failure_reason"])
        self.assertEqual("first_frame_total_timeout", snapshot["last_error_payload"]["failure_reason"])
        self.assertEqual(
            ["MJPG@640x480@15", "YUYV@640x480@22", "default@current"],
            [item["label"] for item in snapshot["last_error_payload"]["first_frame_format_attempts"]],
        )

    def test_free_roam_readiness_allows_optional_camera_and_stale_radar_for_motion(self) -> None:
        """自由移动只看安全双锁；相机/雷达缺口进入 mapping_readiness，不阻止低速启动。"""
        api = upper_robot_api.UpperRobotApi(
            camera_base_url="http://127.0.0.1:8088",
            base_port="/dev/ttyS5",
            base_baudrate=115200,
            max_speed=0.12,
        )

        with mock.patch.object(api, "camera_motion_readiness", return_value={"ready": False, "missing": ["camera_first_frame_not_observed"]}):
            with mock.patch.object(
                api,
                "radar_status",
                return_value={
                    "lifecycle_running": True,
                    "latest_scan_proof_fresh": False,
                    "lifecycle_state": "running",
                    "continuous_window_observed": False,
                    "continuity_blocked_reasons": ["latest_proof_stale"],
                },
            ):
                readiness = api.free_roam_motion_readiness()

        self.assertTrue(readiness["ready"])
        self.assertEqual([], readiness["missing"])
        self.assertTrue(readiness["free_move_ready"])
        self.assertTrue(readiness["free_move_without_camera_allowed"])
        self.assertFalse(readiness["radar"]["ready"])
        self.assertTrue(readiness["radar"]["optional"])
        self.assertFalse(readiness["radar"]["blocking"])
        self.assertTrue(readiness["motion_without_radar_allowed"])
        self.assertTrue(readiness["degraded_without_radar"])
        self.assertFalse(readiness["mapping_readiness"]["ready"])
        self.assertEqual(
            ["camera_first_frame_not_observed", "radar_scan_proof_not_fresh"],
            readiness["mapping_readiness"]["missing"],
        )

    def test_free_roam_start_unlocks_motion_even_when_mapping_readiness_is_not_ready(self) -> None:
        """start 要能让车自由低速移动；建图不可用性必须作为只读 mapping_readiness 返回。"""
        api = upper_robot_api.UpperRobotApi(
            camera_base_url="http://127.0.0.1:8088",
            base_port="/dev/ttyS5",
            base_baudrate=115200,
            max_speed=0.12,
        )
        command_result = {
            "mode": "free_roam_param_sequence",
            "action": "start",
            "executed": True,
            "ok": True,
            "results": [],
            "motion_unlock_requested": True,
            "blocked_parameters_not_touched": ["cmd_vel_topic"],
        }
        sensor_readiness = {
            "ready": True,
            "missing": [],
            "free_move_ready": True,
            "mapping_readiness": {
                "ready": False,
                "missing": ["camera_first_frame_not_observed"],
                "free_move_allowed_when_mapping_not_ready": True,
            },
        }

        with mock.patch.object(api, "free_roam_motion_readiness", return_value=sensor_readiness):
            with mock.patch.object(upper_robot_api, "run_free_roam_param_sequence", return_value=command_result) as run_mock:
                with mock.patch.object(api, "free_roam_autonomy_latest", return_value=(200, {"decision_state": "ready"})):
                    payload = api.free_roam_autonomy_control(
                        "start",
                        {
                            "confirm_operator_safety": True,
                            "confirm_mapping_active": True,
                        },
                    )

        run_mock.assert_called_once_with("start", enable_motion=True, mapping_active=False)
        self.assertEqual("requested", payload["status"])
        self.assertEqual([], payload["blocked_reasons"])
        self.assertTrue(payload["sets_state_machine_parameters"])
        self.assertTrue(payload["motion_unlock_requested"])
        self.assertFalse(payload["does_not_set_motion_unlock"])
        self.assertTrue(payload["publishes_cmd_vel"])
        self.assertEqual(sensor_readiness, payload["sensor_readiness"])
        self.assertFalse(payload["sensor_readiness"]["mapping_readiness"]["ready"])
        self.assertTrue(payload["mapping_active_requested"])
        self.assertFalse(payload["mapping_active_applied"])
        self.assertFalse(payload["safe_to_control"])

    def test_free_roam_start_applies_mapping_active_only_when_mapping_readiness_ready(self) -> None:
        """相机和雷达建图质量都 ready 时，start 才能把状态机切入建图会话。"""
        api = upper_robot_api.UpperRobotApi(
            camera_base_url="http://127.0.0.1:8088",
            base_port="/dev/ttyS5",
            base_baudrate=115200,
            max_speed=0.12,
        )
        command_result = {
            "mode": "free_roam_param_sequence",
            "action": "start",
            "executed": True,
            "ok": True,
            "results": [],
            "motion_unlock_requested": True,
            "blocked_parameters_not_touched": ["cmd_vel_topic"],
        }
        sensor_readiness = {
            "ready": True,
            "missing": [],
            "free_move_ready": True,
            "mapping_readiness": {
                "ready": True,
                "missing": [],
                "free_move_allowed_when_mapping_not_ready": True,
            },
        }

        with mock.patch.object(api, "free_roam_motion_readiness", return_value=sensor_readiness):
            with mock.patch.object(upper_robot_api, "run_free_roam_param_sequence", return_value=command_result) as run_mock:
                with mock.patch.object(api, "free_roam_autonomy_latest", return_value=(200, {"decision_state": "ready"})):
                    payload = api.free_roam_autonomy_control(
                        "start",
                        {
                            "confirm_operator_safety": True,
                            "confirm_mapping_active": True,
                        },
                    )

        run_mock.assert_called_once_with("start", enable_motion=True, mapping_active=True)
        self.assertEqual("requested", payload["status"])
        self.assertTrue(payload["motion_unlock_requested"])
        self.assertTrue(payload["mapping_active_requested"])
        self.assertTrue(payload["mapping_active_applied"])
        self.assertTrue(payload["sensor_readiness"]["mapping_readiness"]["ready"])
        self.assertFalse(payload["safe_to_control"])

    def test_free_roam_start_allows_free_move_without_mapping_confirmation(self) -> None:
        """未确认建图记录时也能启动自由移动，但状态机 mapping_active 必须写 false。"""
        api = upper_robot_api.UpperRobotApi(
            camera_base_url="http://127.0.0.1:8088",
            base_port="/dev/ttyS5",
            base_baudrate=115200,
            max_speed=0.12,
        )
        command_result = {
            "mode": "free_roam_param_sequence",
            "action": "start",
            "executed": True,
            "ok": True,
            "results": [],
            "motion_unlock_requested": True,
            "blocked_parameters_not_touched": ["cmd_vel_topic"],
        }
        sensor_readiness = {
            "ready": True,
            "missing": [],
            "free_move_ready": True,
            "mapping_readiness": {
                "ready": False,
                "missing": ["mapping_active_not_confirmed"],
                "free_move_allowed_when_mapping_not_ready": True,
            },
        }

        with mock.patch.object(api, "free_roam_motion_readiness", return_value=sensor_readiness):
            with mock.patch.object(upper_robot_api, "run_free_roam_param_sequence", return_value=command_result) as run_mock:
                with mock.patch.object(api, "free_roam_autonomy_latest", return_value=(200, {"decision_state": "ready"})):
                    payload = api.free_roam_autonomy_control(
                        "start",
                        {
                            "confirm_operator_safety": True,
                            "confirm_mapping_active": False,
                        },
                    )

        run_mock.assert_called_once_with("start", enable_motion=True, mapping_active=False)
        self.assertEqual("requested", payload["status"])
        self.assertTrue(payload["motion_unlock_requested"])
        self.assertFalse(payload["mapping_active_requested"])
        self.assertFalse(payload["mapping_active_applied"])
        self.assertFalse(payload["sensor_readiness"]["mapping_readiness"]["ready"])
        self.assertFalse(payload["safe_to_control"])

    def test_free_roam_stop_relocks_motion_without_confirmation(self) -> None:
        """stop 必须随时可用，并通过参数序列关闭运动发布双锁。"""
        api = upper_robot_api.UpperRobotApi(
            camera_base_url="http://127.0.0.1:8088",
            base_port="/dev/ttyS5",
            base_baudrate=115200,
            max_speed=0.12,
        )
        command_result = {
            "mode": "free_roam_param_sequence",
            "action": "stop",
            "executed": True,
            "ok": True,
            "results": [],
            "motion_unlock_requested": False,
            "blocked_parameters_not_touched": ["cmd_vel_topic"],
        }

        with mock.patch.object(upper_robot_api, "run_free_roam_param_sequence", return_value=command_result) as run_mock:
            with mock.patch.object(api, "free_roam_autonomy_latest", return_value=(200, {"decision_state": "ready"})):
                payload = api.free_roam_autonomy_control("stop", {})

        run_mock.assert_called_once_with("stop", enable_motion=False)
        self.assertEqual("requested", payload["status"])
        self.assertTrue(payload["sets_state_machine_parameters"])
        self.assertTrue(payload["does_not_set_motion_unlock"])
        self.assertFalse(payload["direct_cmd_vel_publish"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["publishes_cmd_vel"])

    def test_free_roam_stop_sets_external_stop_without_confirmation(self) -> None:
        """stop 必须随时可用，但仍只通过状态机参数请求停止。"""
        api = upper_robot_api.UpperRobotApi(
            camera_base_url="http://127.0.0.1:8088",
            base_port="/dev/ttyS5",
            base_baudrate=115200,
            max_speed=0.12,
        )
        command_result = {
            "mode": "free_roam_param_sequence",
            "action": "stop",
            "executed": True,
            "ok": True,
            "results": [],
            "motion_unlock_requested": False,
            "blocked_parameters_not_touched": ["cmd_vel_topic"],
        }

        with mock.patch.object(upper_robot_api, "run_free_roam_param_sequence", return_value=command_result) as run_mock:
            with mock.patch.object(api, "free_roam_autonomy_latest", return_value=(200, {"decision_state": "stopping"})):
                payload = api.free_roam_autonomy_control("stop", {})

        run_mock.assert_called_once_with("stop", enable_motion=False)
        self.assertEqual("requested", payload["status"])
        self.assertTrue(payload["sets_state_machine_parameters"])
        self.assertFalse(payload["direct_cmd_vel_publish"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["publishes_cmd_vel"])

    def test_radar_scan_proof_latest_preserves_explicit_evidence_ref(self) -> None:
        """LiDAR artifact 已有 evidence_ref 时，API 必须保持 producer 原值。"""
        artifact = {
            "schema": "trashbot.o1.lidar_scan_proof.v1",
            "evidence_ref": "field-lidar-proof-explicit",
            "generated_at_ms": 1781154494512,
            "proof": {
                "status": "scan_once_hz_raw_packet_tf_observed",
                "scan_once_observed": True,
                "scan_hz_observed": True,
                "raw_packet_once_observed": True,
                "tf_observed": True,
                "all_required_observations_observed": True,
            },
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = Path(temp_dir) / "lidar_scan_proof_latest.json"
            artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
            api = upper_robot_api.UpperRobotApi(
                camera_base_url="http://127.0.0.1:8088",
                base_port="/dev/ttyS5",
                base_baudrate=115200,
                max_speed=0.12,
                lidar_scan_proof_artifact_path=str(artifact_path),
            )

            http_status, latest = api.radar_scan_proof_latest()
            status = api.radar_status()

        self.assertEqual(200, http_status)
        self.assertEqual("field-lidar-proof-explicit", latest["evidence_ref"])
        self.assertEqual("field-lidar-proof-explicit", latest["latest_evidence_ref"])
        self.assertEqual("field-lidar-proof-explicit", status["evidence_ref"])
        self.assertEqual("field-lidar-proof-explicit", status["scan_proof_latest"]["latest_evidence_ref"])
        self.assertEqual("field-lidar-proof-explicit", status["latest_scan_proof"]["latest_evidence_ref"])
        self.assertTrue(status["fresh_scan_proof_observed"])
        self.assertFalse(status["safe_to_control"])
        self.assertFalse(status["sends_motion_commands"])

    def test_radar_scan_proof_latest_derives_evidence_ref_from_generated_at_ms(self) -> None:
        """缺显式 ref 时，用 generated_at_ms 派生稳定 LiDAR evidence id。"""
        artifact = {
            "schema": "trashbot.o1.lidar_scan_proof.v1",
            "generated_at_ms": 1781154494512,
            "proof": {
                "status": "scan_once_hz_raw_packet_tf_observed",
                "scan_once_observed": True,
                "scan_hz_observed": True,
                "raw_packet_once_observed": True,
                "tf_observed": True,
                "all_required_observations_observed": True,
            },
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = Path(temp_dir) / "lidar_scan_proof_latest.json"
            artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
            api = upper_robot_api.UpperRobotApi(
                camera_base_url="http://127.0.0.1:8088",
                base_port="/dev/ttyS5",
                base_baudrate=115200,
                max_speed=0.12,
                lidar_scan_proof_artifact_path=str(artifact_path),
            )

            http_status, latest = api.radar_scan_proof_latest()
            summary = upper_robot_api.summarize_lidar_scan_proof_latest_artifact(str(artifact_path))

        self.assertEqual(200, http_status)
        self.assertEqual("o1-lidar-scan-proof-1781154494512", latest["latest_evidence_ref"])
        self.assertEqual("o1-lidar-scan-proof-1781154494512", summary["latest_evidence_ref"])
        self.assertFalse(latest["safe_to_control"])
        self.assertFalse(latest["robot_control_executed"])

    def test_radar_scan_proof_latest_lifts_scan_preview_points_from_stdout_preview(self) -> None:
        """latest readback 必须把已有 LaserScan 文本转成地图可叠加的只读点位。"""
        artifact = {
            "schema": "trashbot.o1.lidar_scan_proof.v1",
            "generated_at_ms": 1781154494512,
            "proof": {
                "status": "scan_once_hz_raw_packet_tf_observed",
                "scan_once_observed": True,
                "scan_hz_observed": True,
                "raw_packet_once_observed": True,
                "tf_observed": True,
                "all_required_observations_observed": True,
            },
            "topic_reads": {
                "results": {
                    "scan_once": {
                        "stdout_preview": "\n".join(
                            [
                                "header:",
                                "  frame_id: laser_frame",
                                "angle_min: 0.0",
                                "angle_increment: 1.57079632679",
                                "range_min: 0.05",
                                "range_max: 8.0",
                                "ranges:",
                                "- 0.03",
                                "- 1.0",
                                "- 9.0",
                                "- 0.5",
                                "intensities: []",
                            ]
                        ),
                    }
                }
            },
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = Path(temp_dir) / "lidar_scan_proof_latest.json"
            artifact_path.write_text(json.dumps(artifact), encoding="utf-8")

            http_status, latest = upper_robot_api.read_lidar_scan_proof_latest_artifact(str(artifact_path))
            summary = upper_robot_api.summarize_lidar_scan_proof_latest_artifact(str(artifact_path))

        # 低于 range_min 和高于 range_max 的读数会被过滤，但 source_count 保留原始槽位数量。
        self.assertEqual(200, http_status)
        self.assertEqual(2, latest["scan_preview_point_count"])
        self.assertEqual(4, latest["scan_preview_source_point_count"])
        self.assertEqual("laser_frame", latest["scan_preview_frame_id"])
        self.assertEqual("topic_reads.results.scan_once.stdout_preview", latest["scan_preview_source"])
        self.assertEqual(1, latest["scan_preview_points"][0]["source_index"])
        self.assertAlmostEqual(1.0, latest["scan_preview_points"][0]["range_m"])
        self.assertEqual(2, summary["scan_preview_point_count"])
        self.assertEqual("laser_frame", summary["scan_preview_frame_id"])
        self.assertFalse(latest["safe_to_control"])
        self.assertFalse(latest["robot_control_executed"])

    def test_radar_scan_proof_latest_derives_safe_evidence_ref_from_iso_generated_at(self) -> None:
        """旧 artifact 只有 ISO generated_at 时，也要派生安全可读 ref。"""
        artifact = {
            "schema": "trashbot.o1.lidar_scan_proof.v1",
            "generated_at": "2026-06-11T05:06:46.418393Z",
            "proof": {
                "status": "scan_once_hz_raw_packet_tf_observed",
                "scan_once_observed": True,
                "scan_hz_observed": True,
                "raw_packet_once_observed": True,
                "tf_observed": True,
                "all_required_observations_observed": True,
            },
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = Path(temp_dir) / "lidar_scan_proof_latest.json"
            artifact_path.write_text(json.dumps(artifact), encoding="utf-8")

            http_status, latest = upper_robot_api.read_lidar_scan_proof_latest_artifact(str(artifact_path))

        self.assertEqual(200, http_status)
        self.assertEqual("o1-lidar-scan-proof-2026-06-11T05-06-46-418393Z", latest["evidence_ref"])
        self.assertEqual(latest["evidence_ref"], latest["latest_evidence_ref"])

    def test_radar_status_reports_lifecycle_running_with_fresh_latest_proof(self) -> None:
        """lifecycle running 且 latest proof 新鲜时，status 必须明确表达当前连续窗口已观察到。"""
        artifact = {
            "schema": "trashbot.o1.lidar_scan_proof.v1",
            "generated_at_ms": 1781154494512,
            "proof": {
                "status": "scan_once_hz_raw_packet_tf_observed",
                "scan_once_observed": True,
                "scan_hz_observed": True,
                "raw_packet_once_observed": True,
                "tf_observed": True,
                "all_required_observations_observed": True,
            },
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = Path(temp_dir) / "lidar_scan_proof_latest.json"
            artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
            api = upper_robot_api.UpperRobotApi(
                camera_base_url="http://127.0.0.1:8088",
                base_port="/dev/ttyS5",
                base_baudrate=115200,
                max_speed=0.12,
                lidar_scan_proof_artifact_path=str(artifact_path),
            )

            with mock.patch.object(
                upper_robot_api,
                "read_radar_lifecycle_status",
                return_value={
                    "status": "loaded",
                    "running": True,
                    "state": "running",
                    "pid": 4321,
                    "latest_result": {"running": True, "state": "running", "pid": 4321},
                },
            ):
                status = api.radar_status()

        self.assertEqual("latest_proof_fresh_while_lifecycle_running", status["continuous_scan_status"])
        self.assertEqual("latest_proof_fresh_while_lifecycle_running", status["continuity_window_status"])
        self.assertEqual("latest_proof_fresh_while_lifecycle_running", status["lifecycle_status"])
        self.assertTrue(status["continuous_window_observed"])
        self.assertTrue(status["lifecycle_running"])
        self.assertEqual("running", status["lifecycle_state"])
        self.assertEqual(4321, status["lifecycle_pid"])
        self.assertEqual([], status["continuous_blocked_reasons"])
        self.assertNotIn("scan_continuity_not_observed", status["blocked_reasons"])
        self.assertFalse(status["safe_to_control"])
        self.assertFalse(status["robot_control_executed"])

    def test_radar_status_keeps_blocker_when_latest_proof_present_but_lifecycle_stopped(self) -> None:
        """latest proof 仍在时，如果 lifecycle 已停，status 必须继续 fail-closed。"""
        artifact = {
            "schema": "trashbot.o1.lidar_scan_proof.v1",
            "generated_at_ms": 1781154494512,
            "proof": {
                "status": "scan_once_hz_raw_packet_tf_observed",
                "scan_once_observed": True,
                "scan_hz_observed": True,
                "raw_packet_once_observed": True,
                "tf_observed": True,
                "all_required_observations_observed": True,
            },
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = Path(temp_dir) / "lidar_scan_proof_latest.json"
            artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
            api = upper_robot_api.UpperRobotApi(
                camera_base_url="http://127.0.0.1:8088",
                base_port="/dev/ttyS5",
                base_baudrate=115200,
                max_speed=0.12,
                lidar_scan_proof_artifact_path=str(artifact_path),
            )

            with mock.patch.object(
                upper_robot_api,
                "read_radar_lifecycle_status",
                return_value={
                    "status": "loaded",
                    "running": False,
                    "state": "stopped",
                    "pid": None,
                    "latest_result": {"running": False, "state": "stopped", "pid": None},
                },
            ):
                status = api.radar_status()

        self.assertEqual("latest_proof_present_but_lifecycle_not_running", status["continuous_scan_status"])
        self.assertFalse(status["continuous_window_observed"])
        self.assertIn("lidar_lifecycle_not_running", status["continuous_blocked_reasons"])
        self.assertIn("lidar_lifecycle_not_running", status["blocked_reasons"])
        self.assertFalse(status["safe_to_control"])

    def test_radar_status_fail_closed_when_lifecycle_status_readback_fails(self) -> None:
        """脚本缺失或坏 JSON 时，status 只能报告 readback 失败，不能伪造 continuity 成功。"""
        artifact = {
            "schema": "trashbot.o1.lidar_scan_proof.v1",
            "generated_at_ms": 1781154494512,
            "proof": {
                "status": "scan_once_hz_raw_packet_tf_observed",
                "scan_once_observed": True,
                "scan_hz_observed": True,
                "raw_packet_once_observed": True,
                "tf_observed": True,
                "all_required_observations_observed": True,
            },
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = Path(temp_dir) / "lidar_scan_proof_latest.json"
            artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
            api = upper_robot_api.UpperRobotApi(
                camera_base_url="http://127.0.0.1:8088",
                base_port="/dev/ttyS5",
                base_baudrate=115200,
                max_speed=0.12,
                lidar_scan_proof_artifact_path=str(artifact_path),
            )

            with mock.patch.object(
                upper_robot_api,
                "read_radar_lifecycle_status",
                return_value={
                    "status": "read_failed",
                    "running": False,
                    "state": "unknown",
                    "pid": None,
                    "failure_reason": "bad_json",
                    "attempts": [{"source": "managed_runtime_absolute", "status": "bad_json"}],
                },
            ):
                status = api.radar_status()

        self.assertEqual("lifecycle_status_unavailable", status["continuous_scan_status"])
        self.assertEqual("status_read_failed", status["lifecycle_status"])
        self.assertIn("lifecycle_status_read_failed", status["continuous_blocked_reasons"])
        self.assertFalse(status["continuous_window_observed"])
        self.assertFalse(status["safe_to_control"])

    def test_radar_scan_proof_latest_bad_json_does_not_forge_evidence_ref(self) -> None:
        """坏 JSON 必须 fail closed，不能用 artifact path 伪造 evidence_ref。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = Path(temp_dir) / "lidar_scan_proof_latest.json"
            artifact_path.write_text("{bad json", encoding="utf-8")

            http_status, latest = upper_robot_api.read_lidar_scan_proof_latest_artifact(str(artifact_path))
            summary = upper_robot_api.summarize_lidar_scan_proof_latest_artifact(str(artifact_path))

        self.assertEqual(422, http_status)
        self.assertIsNone(latest["evidence_ref"])
        self.assertIsNone(latest["latest_evidence_ref"])
        self.assertIsNone(summary["latest_evidence_ref"])
        self.assertEqual("bad_json", latest["artifact"]["status"])
        self.assertFalse(latest["safe_to_control"])
        self.assertFalse(latest["primary_actions_enabled"])

    def test_radar_scan_proof_refresh_attaches_latest_evidence_ref(self) -> None:
        """refresh 回包要带 latest evidence ref，供 PC last_result_evidence_ref 直接读取。"""
        artifact = {
            "schema": "trashbot.o1.lidar_scan_proof.v1",
            "generated_at_ms": 1781154494512,
            "proof": {
                "status": "scan_once_hz_raw_packet_tf_observed",
                "scan_once_observed": True,
                "scan_hz_observed": True,
                "raw_packet_once_observed": True,
                "tf_observed": True,
                "all_required_observations_observed": True,
            },
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = Path(temp_dir) / "lidar_scan_proof_latest.json"
            artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
            api = upper_robot_api.UpperRobotApi(
                camera_base_url="http://127.0.0.1:8088",
                base_port="/dev/ttyS5",
                base_baudrate=115200,
                max_speed=0.12,
                lidar_scan_proof_artifact_path=str(artifact_path),
            )

            with mock.patch.object(
                upper_robot_api,
                "run_lidar_scan_proof_collector",
                return_value={
                    "command_result": {"ok": True, "reason": "ok"},
                    "collector_payload": artifact,
                    "parse_error": None,
                },
            ):
                payload = asyncio.run(api.radar_scan_proof_refresh({"timeout_s": 1, "start_runtime": False}))

        self.assertEqual("refreshed", payload["status"])
        self.assertEqual("o1-lidar-scan-proof-1781154494512", payload["evidence_ref"])
        self.assertEqual("o1-lidar-scan-proof-1781154494512", payload["latest_evidence_ref"])
        self.assertEqual(200, payload["latest_readback_http_status"])
        self.assertTrue(payload["ros2_runtime_proven"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["uses_base_uart"])

    def test_localize_reset_uses_builtin_no_motion_helper_defaults(self) -> None:
        """定位 reset 默认调用 O10 helper 写 localization artifact，且禁止路径/运动。"""
        clean_artifact = {
            "schema": "trashbot.upper_robot_api.v1.nav2_lifecycle_runtime_proof",
            "status": "nav2_no_motion_localization_runtime_observed",
            "evidence_type": "robot_runtime_material",
            "proof": {
                "status": "nav2_no_motion_localization_runtime_observed",
                "evidence_type": "robot_runtime_material",
                "initialpose_published": True,
                "amcl_pose_observed": True,
                "localization_tf_observed": {"map_to_odom": True, "map_to_base_link": True},
                "tf_chain_observed": {
                    "map_to_odom": True,
                    "odom_to_base_link": True,
                    "base_link_to_laser_frame": True,
                    "map_to_base_link": True,
                },
                "tf_chain_diagnostics": {
                    "pairs": {
                        "odom_to_base_link": {
                            "source_frame": "odom",
                            "target_frame": "base_link",
                            "observed": True,
                        }
                    }
                },
                "tf_topics_observed": {"/tf": True, "/tf_static": True},
                "tf_static_observed": True,
                "tf_frame_inventory": {
                    "frames": ["base_link", "laser_frame", "map", "odom"],
                    "edges": [{"parent": "map", "child": "odom", "topic": "/tf"}],
                    "dynamic_edges": [{"parent": "map", "child": "odom", "topic": "/tf"}],
                    "static_edges": [{"parent": "odom", "child": "base_link", "topic": "/tf_static"}],
                },
                "amcl_pose_frame_id": "map",
                "amcl_pose": {"frame_id": "map", "x": 0.25, "y": 0.75, "yaw": 1.57, "source": "/amcl_pose"},
                "base_link_to_laser_frame_transform": {
                    "parent_frame_id": "base_link",
                    "child_frame_id": "laser_frame",
                    "translation": {"x": 0.1, "y": 0.0},
                    "rotation": {"yaw": 0.0},
                    "source": "tf2_echo base_link laser_frame",
                },
                "amcl_node_publishers": [{"topic": "/amcl_pose", "type": "geometry_msgs/msg/PoseWithCovarianceStamped"}],
                "amcl_node_subscribers": [{"topic": "/scan", "type": "sensor_msgs/msg/LaserScan"}],
                "amcl_tf_broadcast_param": "True",
                "amcl_frame_params": {"global_frame_id": "map", "odom_frame_id": "odom", "base_frame_id": "base_link"},
                "map_frame_observed": True,
                "odom_frame_observed": True,
                "amcl_tf_root_cause": "source_inventory_observed",
                "tf_failure_classification": {
                    "map_to_base_link": "observed",
                    "frame_naming_consistent": True,
                    "reason": "complete_chain_observed",
                },
                "managed_runtime_requested": True,
                "managed_runtime_started": True,
                "managed_runtime_cleanup_ok": True,
                "path_generation_requested": False,
                "path_generation_attempted": False,
                "path_generated": False,
                "root_causes": [],
                "blocked_commands_not_sent": ["/cmd_vel", "/api/base/manual", "/api/nav2/start", "/api/nav2/stop"],
                "blocked_devices_not_opened": ["/dev/ttyS5"],
            },
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            localization_path = Path(temp_dir) / "localization_reset_latest.json"
            localization_path.write_text(json.dumps(clean_artifact), encoding="utf-8")
            api = upper_robot_api.UpperRobotApi(
                camera_base_url="http://127.0.0.1:8088",
                base_port="/dev/ttyS5",
                base_baudrate=115200,
                max_speed=0.12,
                localization_artifact_path=str(localization_path),
                map_lifecycle_proof_artifact_path=str(Path(temp_dir) / "map_lifecycle_latest.json"),
                map_artifact_dir=str(Path(temp_dir) / "maps"),
            )

            with mock.patch.object(
                upper_robot_api,
                "run_nav2_runtime_proof_helper",
                return_value={"mode": "o10_amcl_nav2_runtime_proof_helper", "executed": True, "ok": True},
            ) as helper_mock:
                payload = asyncio.run(api.localize_reset({}))
            http_status, latest = api.localize_proof_latest()

        helper_mock.assert_called_once()
        helper_kwargs = helper_mock.call_args.kwargs
        self.assertEqual(str(localization_path), helper_kwargs["artifact_path"])
        self.assertEqual(30.0, helper_kwargs["timeout_s"])
        self.assertTrue(helper_kwargs["managed_runtime_opt_in"])
        self.assertEqual(30.0, helper_kwargs["managed_timeout_s"])
        self.assertTrue(helper_kwargs["initialpose_opt_in"])
        self.assertEqual("map", helper_kwargs["initialpose_frame_id"])
        self.assertFalse(helper_kwargs["path_generation_opt_in"])
        self.assertEqual("refreshed", payload["status"])
        self.assertEqual("localization_reset_observed", payload["proof_state"])
        self.assertTrue(payload["initialpose_published"])
        self.assertTrue(payload["amcl_pose_observed"])
        self.assertTrue(payload["localization_tf_observed"]["map_to_odom"])
        self.assertTrue(payload["localization_tf_observed"]["map_to_base_link"])
        self.assertTrue(payload["tf_chain_observed"]["odom_to_base_link"])
        self.assertTrue(payload["tf_chain_observed"]["base_link_to_laser_frame"])
        self.assertTrue(payload["tf_topics_observed"]["/tf"])
        self.assertTrue(payload["tf_static_observed"])
        self.assertEqual("map", payload["amcl_pose_frame_id"])
        self.assertEqual({"frame_id": "map", "x": 0.25, "y": 0.75, "yaw": 1.57, "source": "/amcl_pose"}, payload["amcl_pose"])
        self.assertEqual("laser_frame", payload["base_link_to_laser_frame_transform"]["child_frame_id"])
        self.assertEqual("True", payload["amcl_tf_broadcast_param"])
        self.assertEqual("source_inventory_observed", payload["amcl_tf_root_cause"])
        self.assertEqual("observed", payload["tf_failure_classification"]["map_to_base_link"])
        self.assertTrue(payload["managed_runtime_started"])
        self.assertFalse(payload["path_generation_opt_in"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["sends_motion_commands"])
        self.assertFalse(payload["publishes_cmd_vel"])
        self.assertFalse(payload["calls_base_manual"])
        self.assertFalse(payload["uses_base_uart"])
        self.assertIn("/dev/ttyS5", payload["blocked_devices_not_opened"])
        self.assertIn("/cmd_vel", payload["blocked_commands_not_sent"])
        self.assertIn("/api/nav2/start", payload["blocked_commands_not_sent"])
        self.assertEqual(200, http_status)
        self.assertEqual("localization_reset_observed", latest["status"])
        self.assertTrue(latest["initialpose_published"])
        self.assertTrue(latest["amcl_pose_observed"])
        self.assertTrue(latest["latest_localization_tf_observed"])
        self.assertTrue(latest["tf_chain_observed"]["map_to_base_link"])
        self.assertTrue(latest["tf_topics_observed"]["/tf_static"])
        self.assertEqual("map", latest["amcl_frame_params"]["global_frame_id"])
        self.assertEqual({"frame_id": "map", "x": 0.25, "y": 0.75, "yaw": 1.57, "source": "/amcl_pose"}, latest["amcl_pose"])
        self.assertEqual("tf2_echo base_link laser_frame", latest["base_link_to_laser_frame_transform"]["source"])
        self.assertFalse(latest["safe_to_control"])

    def test_localize_proof_latest_exposes_phase_partial_fields(self) -> None:
        """partial artifact 也要在 latest 顶层暴露阶段链，便于 PC/现场定位 timeout blocker。"""
        partial_artifact = {
            "schema": "trashbot.upper_robot_api.v1.nav2_lifecycle_runtime_proof",
            "status": "blocked_with_root_cause",
            "proof": {
                "status": "blocked_with_root_cause",
                "last_phase": "amcl_pose_probe",
                "last_successful_phase": "initialpose",
                "phase_history": [{"phase": "initialpose", "ok": True}],
                "current_command": {"command": "timeout 8 ros2 topic echo --once /amcl_pose"},
                "recent_commands": [{"command": "ros2 topic pub --once /initialpose", "ok": True}],
                "partial_artifact_preserved": True,
                "package_availability": {"nav2_amcl": True, "nav2_map_server": True},
                "package_check_mode": "single_sourced_pkg_list_diagnostic",
                "package_checks_batch_ok": True,
                "initialpose_published": True,
                "amcl_pose_observed": False,
                "localization_tf_observed": {"map_to_odom": False, "map_to_base_link": False},
                "tf_chain_observed": {
                    "map_to_odom": True,
                    "odom_to_base_link": False,
                    "base_link_to_laser_frame": True,
                    "map_to_base_link": False,
                },
                "tf_chain_diagnostics": {
                    "pairs": {
                        "odom_to_base_link": {
                            "source_frame": "odom",
                            "target_frame": "base_link",
                            "observed": False,
                            "failure_reason": "tf2_timeout_or_timing",
                        }
                    }
                },
                "tf_topics_observed": {"/tf": True, "/tf_static": True},
                "tf_static_observed": True,
                "tf_frame_inventory": {
                    "frames": ["base_link", "laser_frame", "odom"],
                    "edges": [{"parent": "odom", "child": "base_link", "topic": "/tf_static"}],
                    "dynamic_edges": [],
                    "static_edges": [{"parent": "odom", "child": "base_link", "topic": "/tf_static"}],
                    "static_transforms": [
                        {
                            "parent_frame_id": "base_link",
                            "child_frame_id": "laser_frame",
                            "translation": {"x": 0.0, "y": 0.0, "z": 0.0},
                            "rotation": {"yaw": 0.0, "quaternion": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}},
                            "source": "/tf_static",
                        }
                    ],
                },
                "amcl_pose_frame_id": "map",
                "amcl_node_publishers": [{"topic": "/amcl_pose", "type": "geometry_msgs/msg/PoseWithCovarianceStamped"}],
                "amcl_node_subscribers": [{"topic": "/initialpose", "type": "geometry_msgs/msg/PoseWithCovarianceStamped"}],
                "amcl_tf_broadcast_param": "True",
                "amcl_frame_params": {"global_frame_id": "map", "odom_frame_id": "odom", "base_frame_id": "base_link"},
                "tf_source_root_cause_detail": {
                    "base_link_to_laser_frame_source_transform": {
                        "parent_frame_id": "base_link",
                        "child_frame_id": "laser_frame",
                        "translation": {"x": 0.0, "y": 0.0, "z": 0.0},
                        "rotation": {"yaw": 0.0, "quaternion": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}},
                        "source": "/tf_static",
                    }
                },
                "map_frame_observed": False,
                "odom_frame_observed": True,
                "amcl_tf_root_cause": "amcl_map_to_odom_tf_not_observed_on_tf",
                "tf_failure_classification": {
                    "map_to_base_link": "blocked_by_missing_odom_to_base_link",
                    "blocking_segment": "odom_to_base_link",
                    "frame_naming_consistent": True,
                },
                "managed_runtime_requested": True,
                "managed_runtime_started": True,
                "managed_runtime_cleanup_ok": False,
                "root_causes": [{"layer": "upper API helper process", "reason": "helper_process_timeout_after_partial_artifact"}],
            },
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            localization_path = Path(temp_dir) / "localization_reset_latest.json"
            localization_path.write_text(json.dumps(partial_artifact), encoding="utf-8")
            api = upper_robot_api.UpperRobotApi(
                camera_base_url="http://127.0.0.1:8088",
                base_port="/dev/ttyS5",
                base_baudrate=115200,
                max_speed=0.12,
                localization_artifact_path=str(localization_path),
            )

            http_status, latest = api.localize_proof_latest()

        self.assertEqual(200, http_status)
        self.assertEqual("blocked_with_root_cause", latest["status"])
        self.assertEqual("amcl_pose_probe", latest["last_phase"])
        self.assertEqual("initialpose", latest["last_successful_phase"])
        self.assertEqual("timeout 8 ros2 topic echo --once /amcl_pose", latest["current_command"]["command"])
        self.assertTrue(latest["partial_artifact_preserved"])
        self.assertEqual("single_sourced_pkg_list_diagnostic", latest["package_check_mode"])
        self.assertTrue(latest["package_availability"]["nav2_amcl"])
        self.assertTrue(latest["package_checks_batch_ok"])
        self.assertTrue(latest["initialpose_published"])
        self.assertFalse(latest["amcl_pose_observed"])
        self.assertTrue(latest["tf_chain_observed"]["map_to_odom"])
        self.assertFalse(latest["tf_chain_observed"]["odom_to_base_link"])
        self.assertEqual("blocked_by_missing_odom_to_base_link", latest["tf_failure_classification"]["map_to_base_link"])
        self.assertTrue(latest["tf_topics_observed"]["/tf"])
        self.assertEqual("map", latest["amcl_pose_frame_id"])
        self.assertEqual("/tf_static", latest["base_link_to_laser_frame_transform"]["source"])
        self.assertEqual("laser_frame", latest["base_link_to_laser_frame_transform"]["child_frame_id"])
        self.assertEqual("amcl_map_to_odom_tf_not_observed_on_tf", latest["amcl_tf_root_cause"])
        self.assertFalse(latest["map_frame_observed"])
        self.assertTrue(latest["odom_frame_observed"])
        self.assertFalse(latest["safe_to_control"])

    def test_default_localization_artifact_resolves_to_onboard_runtime(self) -> None:
        """默认 localization artifact 必须和 helper 工作目录一致，避免上下层读写两条路径。"""
        api = upper_robot_api.UpperRobotApi(
            camera_base_url="http://127.0.0.1:8088",
            base_port="/dev/ttyS5",
            base_baudrate=115200,
            max_speed=0.12,
        )

        self.assertEqual(
            upper_robot_api.resolve_onboard_runtime_path(upper_robot_api.DEFAULT_LOCALIZATION_ARTIFACT_PATH),
            api.localization_artifact_path,
        )

    def test_nav2_goal_execute_lifts_base_motion_flags_from_latest_result(self) -> None:
        """Nav2 执行外层返回必须跟随 latest_result，不能保留 no-motion 默认 blocked 字段。"""
        api = upper_robot_api.UpperRobotApi(
            camera_base_url="http://127.0.0.1:8088",
            base_port="/dev/ttyS5",
            base_baudrate=115200,
            max_speed=0.12,
        )
        latest_result = {
            "status": "goal_succeeded",
            "goal_accepted": True,
            "result_received": True,
            "result_status": "succeeded",
            "feedback_sample_count": 8,
            "robot_control_executed": True,
            "sends_motion_commands": True,
            "sends_base_motion_commands": True,
            "uses_base_uart": True,
            "publishes_cmd_vel": "nav2_controller_may_publish_cmd_vel_when_goal_is_active",
            "calls_base_manual": False,
            "base_feedback_summary": {"wheel_feedback_lr_nonzero_proven": True},
            "hil_pass": True,
        }

        with mock.patch.object(api, "nav2_proof_latest", return_value=(200, {"latest_result": {"proof": {"managed_runtime_map_yaml": "/tmp/map.yaml"}}})):
            with mock.patch.object(upper_robot_api, "run_nav2_goal_execution_helper", return_value={"mode": "o11", "executed": True, "ok": True}) as helper_mock:
                with mock.patch.object(api, "nav2_goal_execution_latest", return_value=(200, {"latest_result": latest_result})):
                    payload = asyncio.run(api.nav2_goal_execute({"confirm_navigation_execution": True}))

        self.assertEqual("goal_succeeded", payload["status"])
        self.assertEqual("ros", payload["goal_request"]["base_command_mode"])
        self.assertEqual("ros", helper_mock.call_args.kwargs["base_command_mode"])
        self.assertTrue(payload["nav2_goal_execution_proven"])
        self.assertTrue(payload["hil_pass"])
        self.assertTrue(payload["sends_motion_commands"])
        self.assertTrue(payload["sends_base_motion_commands"])
        self.assertTrue(payload["uses_base_uart"])
        self.assertEqual([], payload["blocked_devices_not_touched"])
        self.assertEqual([], payload["blocked_commands_not_sent"])
        self.assertTrue(payload["robot_control_executed"])
        self.assertFalse(payload["delivery_success"])

    def test_nav2_goal_execute_does_not_prove_route_without_wheel_lr(self) -> None:
        """NavigateToPose 成功但同窗口 L/R 未非零时，上车外层回包也必须保持未证明。"""
        api = upper_robot_api.UpperRobotApi(
            camera_base_url="http://127.0.0.1:8088",
            base_port="/dev/ttyS5",
            base_baudrate=115200,
            max_speed=0.12,
        )
        latest_result = {
            "status": "goal_succeeded",
            "goal_accepted": True,
            "result_received": True,
            "result_status": "succeeded",
            "feedback_sample_count": 8,
            "robot_control_executed": True,
            "sends_motion_commands": True,
            "sends_base_motion_commands": True,
            "uses_base_uart": True,
            "nav2_goal_execution_proven": True,
            "hil_pass": True,
            "base_feedback_summary": {"wheel_feedback_lr_nonzero_proven": False},
        }

        with mock.patch.object(api, "nav2_proof_latest", return_value=(200, {"latest_result": {"proof": {"managed_runtime_map_yaml": "/tmp/map.yaml"}}})):
            with mock.patch.object(upper_robot_api, "run_nav2_goal_execution_helper", return_value={"mode": "o11", "executed": True, "ok": True}):
                with mock.patch.object(api, "nav2_goal_execution_latest", return_value=(200, {"latest_result": latest_result})):
                    payload = asyncio.run(api.nav2_goal_execute({"confirm_navigation_execution": True}))

        self.assertEqual("goal_succeeded", payload["status"])
        self.assertFalse(payload["nav2_goal_execution_proven"])
        self.assertFalse(payload["hil_pass"])
        self.assertIn("wheel_feedback_lr_nonzero", payload["not_proven"])
        self.assertTrue(payload["robot_control_executed"])
        self.assertTrue(payload["sends_base_motion_commands"])
        self.assertFalse(payload["delivery_success"])

    def test_nav2_goal_execute_allows_explicit_base_command_mode_override(self) -> None:
        """Nav2 执行可按白名单切回 PWM 复验，但不影响普通手控默认命令模式。"""
        api = upper_robot_api.UpperRobotApi(
            camera_base_url="http://127.0.0.1:8088",
            base_port="/dev/ttyS5",
            base_baudrate=115200,
            max_speed=0.12,
        )
        latest_result = {
            "status": "goal_succeeded",
            "goal_accepted": True,
            "result_received": True,
            "result_status": "succeeded",
            "robot_control_executed": True,
            "sends_motion_commands": True,
        }

        with mock.patch.object(api, "nav2_proof_latest", return_value=(200, {"latest_result": {"proof": {"managed_runtime_map_yaml": "/tmp/map.yaml"}}})):
            with mock.patch.object(upper_robot_api, "run_nav2_goal_execution_helper", return_value={"mode": "o11", "executed": True, "ok": True}) as helper_mock:
                with mock.patch.object(api, "nav2_goal_execution_latest", return_value=(200, {"latest_result": latest_result})):
                    payload = asyncio.run(api.nav2_goal_execute({"confirm_navigation_execution": True, "base_command_mode": "pwm"}))

        self.assertEqual("pwm", helper_mock.call_args.kwargs["base_command_mode"])
        self.assertEqual("pwm", payload["goal_request"]["base_command_mode"])
        self.assertEqual("ros", api.base_command_mode)
        self.assertEqual("ros", api.nav2_base_command_mode)

    def test_nav2_goal_execution_latest_derives_wheel_lr_gap_from_old_artifact(self) -> None:
        """旧 Nav2 artifact 被只读读取时，也必须补出 wheel raw L/R 未非零根因。"""
        latest_result = {
            "schema": "trashbot.upper_robot_api.v1.nav2_goal_execution_proof",
            "status": "goal_succeeded",
            "goal_accepted": True,
            "result_received": True,
            "result_status": "succeeded",
            "robot_control_executed": True,
            "sends_motion_commands": True,
            "sends_base_motion_commands": True,
            "uses_base_uart": True,
            "nav2_goal_execution_proven": True,
            "hil_pass": True,
            "not_proven": ["delivery_success", "operator_dropoff_confirmation"],
            "base_feedback_summary": {"wheel_feedback_lr_nonzero_proven": False},
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            latest_path = Path(temp_dir) / "nav2_goal_execution_latest.json"
            latest_path.write_text(json.dumps(latest_result), encoding="utf-8")
            api = upper_robot_api.UpperRobotApi(
                camera_base_url="http://127.0.0.1:8088",
                base_port="/dev/ttyS5",
                base_baudrate=115200,
                max_speed=0.12,
                nav2_goal_execution_artifact_path=str(latest_path),
            )

            http_status, payload = api.nav2_goal_execution_latest()

        self.assertEqual(200, http_status)
        self.assertFalse(payload["nav2_goal_execution_proven"])
        self.assertFalse(payload["hil_pass"])
        self.assertIn("wheel_feedback_lr_nonzero", payload["nav2_goal_execution_not_proven"])
        self.assertFalse(payload["latest_result"]["nav2_goal_execution_proven"])
        self.assertFalse(payload["latest_result"]["hil_pass"])
        self.assertIn("wheel_feedback_lr_nonzero", payload["latest_result"]["not_proven"])
        self.assertFalse(payload["delivery_success"])
        self.assertFalse(payload["robot_control_executed"])

    def test_nav2_proof_refresh_managed_path_generation_stays_no_motion(self) -> None:
        """PC 检查路径使用 managed runtime，但不能被包装成 Nav2 start 或底盘控制。"""
        clean_artifact = {
            "schema": "trashbot.upper_robot_api.v1.nav2_lifecycle_runtime_proof",
            "status": "nav2_no_motion_path_generation_runtime_observed",
            "evidence_type": "robot_runtime_material",
            "not_proven": False,
            "proof": {
                "status": "nav2_no_motion_path_generation_runtime_observed",
                "evidence_type": "robot_runtime_material",
                "managed_runtime_requested": True,
                "managed_runtime_started": True,
                "managed_runtime_cleanup_ok": True,
                "initialpose_published": True,
                "amcl_pose_observed": True,
                "localization_tf_observed": {"map_to_odom": True, "map_to_base_link": True},
                "path_generation_requested": True,
                "path_generation_attempted": True,
                "path_generation_service_name": "/compute_path_to_pose",
                "path_generation_service_available": True,
                "path_generation_succeeded": True,
                "path_generated": True,
                "path_point_count": 31,
                "planner_server_active": True,
                "controller_server_active": False,
                "controller_server_requested": False,
                "planner_readiness_summary": {"path_generation_succeeded": True},
                "blocked_commands_not_sent": ["/cmd_vel", "/api/base/manual", "/api/nav2/start", "/api/nav2/stop"],
                "blocked_devices_not_opened": ["/dev/ttyS5"],
                "safe_to_control": False,
                "delivery_success": False,
                "publishes_cmd_vel": False,
                "calls_base_manual": False,
                "uses_base_uart": False,
                "robot_control_executed": False,
            },
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            nav2_path = Path(temp_dir) / "nav2_lifecycle_latest.json"
            nav2_path.write_text(json.dumps(clean_artifact), encoding="utf-8")
            api = upper_robot_api.UpperRobotApi(
                camera_base_url="http://127.0.0.1:8088",
                base_port="/dev/ttyS5",
                base_baudrate=115200,
                max_speed=0.12,
                nav2_lifecycle_artifact_path=str(nav2_path),
                map_lifecycle_proof_artifact_path=str(Path(temp_dir) / "map_lifecycle_latest.json"),
                map_artifact_dir=str(Path(temp_dir) / "maps"),
            )

            with mock.patch.object(
                upper_robot_api,
                "run_nav2_runtime_proof_helper",
                return_value={"mode": "o10_amcl_nav2_runtime_proof_helper", "executed": True, "ok": True},
            ) as helper_mock:
                payload = asyncio.run(
                    api.nav2_proof_refresh(
                        {
                            "timeout_s": 20,
                            "managed_runtime_opt_in": True,
                            "managed_timeout_s": 20,
                            "managed_map_yaml": "/root/rober/onboard/runtime/maps/trashbot_map.yaml",
                            "initialpose_opt_in": True,
                            "initialpose_x": 0.0,
                            "initialpose_y": 0.0,
                            "initialpose_yaw": 0.0,
                            "path_generation_opt_in": True,
                            "path_generation_timeout_s": 20,
                            "path_goal_frame_id": "map",
                            "path_goal_x": 0.8,
                            "path_goal_y": 0.0,
                            "path_goal_yaw": 0.0,
                        }
                    )
                )

        helper_mock.assert_called_once()
        helper_kwargs = helper_mock.call_args.kwargs
        self.assertTrue(helper_kwargs["managed_runtime_opt_in"])
        self.assertEqual(20.0, helper_kwargs["managed_timeout_s"])
        self.assertTrue(helper_kwargs["initialpose_opt_in"])
        self.assertTrue(helper_kwargs["path_generation_opt_in"])
        self.assertEqual(20.0, helper_kwargs["path_generation_timeout_s"])
        self.assertEqual("refreshed", payload["status"])
        self.assertEqual("nav2_no_motion_path_generation_runtime_observed", payload["proof_state"])
        self.assertTrue(payload["starts_ros2"])
        self.assertFalse(payload["starts_nav2"])
        self.assertTrue(payload["managed_runtime_opt_in"])
        self.assertTrue(payload["initialpose_opt_in"])
        self.assertTrue(payload["path_generation_opt_in"])
        self.assertTrue(payload["path_generated"])
        self.assertEqual(31, payload["path_point_count"])
        self.assertTrue(payload["planner_server_active"])
        self.assertFalse(payload["controller_server_active"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["delivery_success"])
        self.assertFalse(payload["publishes_cmd_vel"])
        self.assertFalse(payload["calls_base_manual"])
        self.assertFalse(payload["uses_base_uart"])
        self.assertFalse(payload["robot_control_executed"])


if __name__ == "__main__":
    unittest.main()
