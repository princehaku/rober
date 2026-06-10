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

    def test_base_status_reports_non_motion_readback_without_control_enable(self) -> None:
        """status 可以做只读反馈探测，但不能开启 safe_to_control。"""
        # /api/base/status 允许发送 T=130，但不得打开运动控制或交付成功标志。
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
        self.assertEqual(8.0, helper_kwargs["timeout_s"])
        self.assertTrue(helper_kwargs["managed_runtime_opt_in"])
        self.assertEqual(12.0, helper_kwargs["managed_timeout_s"])
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


if __name__ == "__main__":
    unittest.main()
