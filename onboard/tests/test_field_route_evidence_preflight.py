import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import sys


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import field_route_evidence_preflight as preflight  # noqa: E402


class FieldRouteEvidencePreflightTest(unittest.TestCase):
    def test_dry_run_packet_is_not_proven_and_safe(self):
        # dry-run 必须可在无 ROS2/SSH 的开发机运行，且不能被误判为现场成功。
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "packet.json"
            rc = preflight.main(["--mode", "local", "--dry-run", "--output", str(output)])

            self.assertEqual(rc, 0)
            packet = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(packet["schema"], preflight.SCHEMA)
            self.assertEqual(packet["status"], "dry_run_template_only_not_proven")
            self.assertTrue(packet["not_proven"])
            self.assertFalse(packet["delivery_success"])
            self.assertFalse(packet["primary_actions_enabled"])
            self.assertFalse(packet["safe_to_control"])
            self.assertFalse(packet["robot_control_executed"])
            self.assertFalse(packet["route_execution_success"])
            self.assertFalse(packet["hil_pass"])
            rendered = json.dumps(packet, ensure_ascii=False)
            self.assertIn("learn.launch.py", rendered)
            self.assertIn("fixed_route_autonomy", rendered)
            self.assertIn("/amcl_pose", rendered)
            self.assertIn("/api/nav2/proof/refresh", rendered)
            self.assertNotIn("/cmd_vel", rendered)
            self.assertNotIn("/api/base/manual", rendered)

    def test_ssh_command_uses_argv_and_expected_port(self):
        # SSH 命令必须保持 argv 数组，避免把目标和端口拼进本地 shell 字符串。
        command = preflight.build_ssh_command("root@192.168.1.11", 37878, "true", 5)

        self.assertEqual(command[0], "ssh")
        self.assertIn("-p", command)
        self.assertEqual(command[command.index("-p") + 1], "37878")
        self.assertEqual(command[-2], "root@192.168.1.11")
        self.assertEqual(command[-1], "true")
        templates = preflight.topic_smoke_templates("root@192.168.1.11", 37878)
        self.assertIn("ssh -p 37878 root@192.168.1.11", templates[0]["command"])
        self.assertIn("bash -lc", templates[0]["command"])
        self.assertIn("source /opt/ros/humble/setup.bash", templates[0]["command"])
        self.assertIn("/root/rober/onboard/install/setup.bash", templates[0]["command"])

    def test_remote_ros_commands_source_ros_and_workspace_before_execution(self):
        # 远端 ROS2 命令必须在 bash -lc 下恢复环境，避免 SSH 非登录 shell 丢失 ros2。
        remote = preflight.build_remote_ros_command("ros2 topic list")

        self.assertIn("bash -lc", remote)
        self.assertIn("source /opt/ros/humble/setup.bash", remote)
        self.assertIn("/root/rober/onboard/install/setup.bash", remote)
        self.assertIn("ros2 topic list", remote)

    def test_ssh_unreachable_still_writes_evidence_packet(self):
        # SSH 不可达时也必须交付 JSON，不允许把本轮退化成纯网络 blocker。
        fake_result = {
            "command": ["ssh", "..."],
            "returncode": 255,
            "stdout": "",
            "stderr": "No route to host",
            "timed_out": False,
        }
        with mock.patch.object(preflight, "run_command", return_value=fake_result):
            with tempfile.TemporaryDirectory() as tmpdir:
                output = Path(tmpdir) / "ssh_packet.json"
                rc = preflight.main(
                    [
                        "--mode",
                        "ssh",
                        "--ssh-target",
                        "root@192.168.1.11",
                        "--ssh-port",
                        "37878",
                        "--timeout-s",
                        "5",
                        "--output",
                        str(output),
                    ]
                )
                packet = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(rc, 0)
        self.assertEqual(packet["status"], "blocked_ssh_unreachable")
        self.assertEqual(packet["blocked_reason"], "blocked_ssh_unreachable")
        self.assertTrue(packet["not_proven"])
        self.assertIn("topic_smoke", packet["commands"])
        self.assertIn("localization_smoke", packet["commands"])
        self.assertIn("nav2_proof_refresh", packet["commands"])

    def test_secret_redaction_covers_common_fields(self):
        # 安全摘要需要覆盖常见凭证字段，防止错误日志进入证据包后泄露。
        raw = "Bearer abc.def token=123 password:456 /Users/example/.ssh/id_rsa"
        redacted = preflight.redact_secret(raw)

        self.assertIn("Bearer <redacted>", redacted)
        self.assertIn("token=<redacted>", redacted)
        self.assertIn("password:<redacted>", redacted)

    def test_local_real_missing_setup_fails_closed_before_ros2(self):
        # 没有 setup.bash 时先报环境 blocker，避免继续执行可能误导的 ROS2 检查。
        args = preflight.parse_args(["--mode", "local", "--output", "/tmp/unused.json"])
        with mock.patch.object(preflight, "SETUP_CANDIDATES", ["/definitely/missing/setup.bash"]):
            checks, status = preflight.local_real_checks(args)

        self.assertEqual(status, "blocked_setup_missing")
        self.assertFalse(checks["setup_candidates"]["ok"])

    def test_package_detection_uses_full_stdout_not_truncated_summary(self):
        # ros2 pkg list 很长时，逻辑判断必须基于完整 stdout，而不是裁剪后的摘要。
        full_stdout = "\n".join(
            ["ament_index_python"] * 400
            + preflight.REQUIRED_PACKAGES
        )
        result = {
            "returncode": 0,
            "stdout": "ament_index_python\n<truncated>",
            "stderr": "",
            "_stdout_full": full_stdout,
            "_stderr_full": "",
            "timed_out": False,
            "command": ["ros2", "pkg", "list"],
        }
        with mock.patch.object(preflight, "run_command", return_value=result):
            args = preflight.parse_args(["--mode", "local", "--output", "/tmp/unused.json"])
            check, status = preflight.check_packages(args, remote=False)

        self.assertTrue(check["ok"])
        self.assertEqual(check["missing"], [])
        self.assertIsNone(status)

    def test_localization_smoke_templates_are_read_only(self):
        # live localization smoke 只能包含只读 topic/TF 与 refresh readback，不能夹带运动入口。
        templates = preflight.localization_smoke_templates("root@192.168.1.11", 37878)
        rendered = json.dumps(templates, ensure_ascii=False)
        self.assertIn("/scan", rendered)
        self.assertIn("/amcl_pose", rendered)
        self.assertIn("tf2_echo map odom", rendered)
        self.assertIn("tf2_echo map base_link", rendered)
        self.assertNotIn("/cmd_vel", rendered)
        self.assertNotIn("/api/base/manual", rendered)

    def test_nav2_refresh_template_is_fixed_readback_only(self):
        # refresh 模板必须固定 no-motion body，只做 proof readback，不接受 manual/cmd_vel。
        template = preflight.nav2_refresh_template("root@192.168.1.11", 37878)

        self.assertIn("/api/nav2/proof/refresh", template)
        self.assertIn("managed_runtime_opt_in", template)
        self.assertIn("path_generation_opt_in", template)
        self.assertNotIn("/cmd_vel", template)
        self.assertNotIn("/api/base/manual", template)

    def test_refresh_payload_with_dangerous_true_field_fails_closed(self):
        # 上位机 refresh 若回了危险 true，预检必须直接 fail-closed，不让 readback 混淆成安全。
        payload = {
            "endpoint": "/api/nav2/proof/refresh",
            "status": "unexpected_motion_state",
            "proof": {"path_generated": False, "root_causes": ["localization_not_ready_for_path_generation"]},
            "safe_to_control": True,
        }
        result = {
            "command": ["curl"],
            "returncode": 0,
            "stdout": json.dumps(payload),
            "stderr": "",
            "_stdout_full": json.dumps(payload),
            "_stderr_full": "",
            "timed_out": False,
        }
        args = preflight.parse_args(["--mode", "ssh", "--output", "/tmp/unused.json"])
        with mock.patch.object(preflight, "run_command", return_value=result):
            check, status = preflight.check_nav2_proof_refresh(args, remote=True)

        self.assertEqual(status, "blocked_refresh_invokes_motion_or_goal_execution")
        self.assertFalse(check["ok"])
        self.assertIn("safe_to_control", check["summary"]["dangerous_true_fields"][0])
        self.assertFalse(check["summary"]["safe_to_control"])

    def test_refresh_timeout_fails_closed_and_keeps_no_motion_flags_false(self):
        # refresh 超时必须自然返回 JSON 摘要，而不是继续卡住主进程等人工中断。
        result = {
            "command": ["curl"],
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "_stdout_full": "",
            "_stderr_full": "",
            "timed_out": True,
        }
        args = preflight.parse_args(["--mode", "ssh", "--timeout-s", "12", "--output", "/tmp/unused.json"])
        with mock.patch.object(preflight, "run_command", return_value=result) as mocked_run:
            check, status = preflight.check_nav2_proof_refresh(args, remote=True)

        self.assertEqual(status, "blocked_refresh_readback_failed")
        self.assertFalse(check["ok"])
        self.assertEqual(check["summary"]["status"], "refresh_readback_timed_out")
        self.assertTrue(check["summary"]["timed_out"])
        self.assertFalse(check["summary"]["naturally_returned"])
        self.assertFalse(check["summary"]["safe_to_control"])
        self.assertFalse(check["summary"]["delivery_success"])
        self.assertFalse(check["summary"]["robot_control_executed"])
        self.assertLess(check["summary"]["process_timeout_s"], args.timeout_s + 62)
        self.assertEqual(mocked_run.call_args.args[1], preflight.nav2_refresh_process_timeout_s(args.timeout_s, remote=True))

    def test_refresh_nonzero_exit_fails_closed_and_keeps_no_motion_flags_false(self):
        # refresh 非 0 返回也必须落结构化 summary，避免调用方再去猜 stderr 文本。
        result = {
            "command": ["curl"],
            "returncode": 28,
            "stdout": "",
            "stderr": "curl: (28) Operation timed out",
            "_stdout_full": "",
            "_stderr_full": "curl: (28) Operation timed out",
            "timed_out": False,
        }
        args = preflight.parse_args(["--mode", "ssh", "--output", "/tmp/unused.json"])
        with mock.patch.object(preflight, "run_command", return_value=result):
            check, status = preflight.check_nav2_proof_refresh(args, remote=True)

        self.assertEqual(status, "blocked_refresh_readback_failed")
        self.assertFalse(check["ok"])
        self.assertEqual(check["summary"]["status"], "refresh_command_failed")
        self.assertFalse(check["summary"]["timed_out"])
        self.assertTrue(check["summary"]["naturally_returned"])
        self.assertEqual(check["summary"]["returncode"], 28)
        self.assertFalse(check["summary"]["safe_to_control"])
        self.assertFalse(check["summary"]["route_execution_success"])

    def test_refresh_payload_with_starts_nav2_true_stays_allowed_in_no_motion_mode(self):
        # managed runtime/lifecycle start 属于 no-motion refresh 合同允许项，不能被误判成运动或 goal 执行。
        payload = {
            "endpoint": "/api/nav2/proof/refresh",
            "status": "ready_not_path_proof",
            "starts_nav2": True,
            "robot_control_executed": False,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "route_execution_success": False,
            "hil_pass": False,
            "proof": {
                "path_generated": False,
                "path_generation_succeeded": False,
                "path_point_count": 0,
                "root_causes": ["localization_not_ready_for_path_generation"],
                "blockers": ["map_frame_missing"],
            },
        }
        result = {
            "command": ["curl"],
            "returncode": 0,
            "stdout": json.dumps(payload),
            "stderr": "",
            "_stdout_full": json.dumps(payload),
            "_stderr_full": "",
            "timed_out": False,
        }
        args = preflight.parse_args(["--mode", "ssh", "--output", "/tmp/unused.json"])
        with mock.patch.object(preflight, "run_command", return_value=result):
            check, status = preflight.check_nav2_proof_refresh(args, remote=True)

        self.assertIsNone(status)
        self.assertTrue(check["ok"])
        self.assertEqual(check["summary"]["status"], "ready_not_path_proof")
        self.assertEqual(check["summary"]["dangerous_true_fields"], [])
        self.assertFalse(check["summary"]["safe_to_control"])
        self.assertFalse(check["summary"]["timed_out"])
        self.assertTrue(check["summary"]["naturally_returned"])

    def test_run_ros_command_recovers_from_daemon_fault_once(self):
        # graph 查询若命中 `!rclpy.ok()`，必须先 reset daemon 再重试，而不是直接记成 topic 缺失。
        args = preflight.parse_args(["--mode", "ssh", "--output", "/tmp/unused.json"])
        daemon_fault = {
            "command": ["ssh", "ros2 topic type /amcl_pose"],
            "returncode": 1,
            "stdout": "",
            "stderr": "xmlrpc.client.Fault: RuntimeError: !rclpy.ok()",
            "_stdout_full": "",
            "_stderr_full": "xmlrpc.client.Fault: RuntimeError: !rclpy.ok()",
            "timed_out": False,
        }
        stop_result = {
            "command": ["ssh", "ros2 daemon stop"],
            "returncode": 0,
            "stdout": "",
            "stderr": "",
            "_stdout_full": "",
            "_stderr_full": "",
            "timed_out": False,
        }
        start_result = {
            "command": ["ssh", "ros2 daemon start"],
            "returncode": 0,
            "stdout": "The daemon has been started",
            "stderr": "",
            "_stdout_full": "The daemon has been started",
            "_stderr_full": "",
            "timed_out": False,
        }
        health_result = {
            "command": ["ssh", "ros2 node list"],
            "returncode": 0,
            "stdout": "/amcl\n/map_server",
            "stderr": "",
            "_stdout_full": "/amcl\n/map_server",
            "_stderr_full": "",
            "timed_out": False,
        }
        retried = {
            "command": ["ssh", "ros2 topic type /amcl_pose"],
            "returncode": 0,
            "stdout": "geometry_msgs/msg/PoseWithCovarianceStamped",
            "stderr": "",
            "_stdout_full": "geometry_msgs/msg/PoseWithCovarianceStamped",
            "_stderr_full": "",
            "timed_out": False,
        }
        with mock.patch.object(
            preflight,
            "execute_ros_command_once",
            side_effect=[daemon_fault, stop_result, start_result, health_result, retried],
        ):
            result = preflight.run_ros_command(args, remote=True, command=["ros2", "topic", "type", "/amcl_pose"])

        self.assertTrue(result["daemon_fault_detected"])
        self.assertTrue(result["daemon_recovered"])
        self.assertEqual(result["retry_attempts"], 1)
        self.assertEqual(result["ros_cli_retry"]["target"], "/amcl_pose")
        self.assertTrue(result["ros_daemon_health"]["health_ok"])

    def test_amcl_warning_and_type_error_do_not_count_as_observed(self):
        # /amcl_pose 只有 warning/type error 时不能算 healthy observed，必须回到 blocker。
        results = [
            {
                "command": ["ssh", "true"],
                "returncode": 0,
                "stdout": "header:\nranges: [1.0]",
                "stderr": "",
                "_stdout_full": "header:\nranges: [1.0]",
                "_stderr_full": "",
                "timed_out": False,
            },
            {
                "command": ["ssh", "true"],
                "returncode": 1,
                "stdout": "WARNING: topic [/amcl_pose] does not appear to be published yet",
                "stderr": "Could not determine the type for the passed topic",
                "_stdout_full": "WARNING: topic [/amcl_pose] does not appear to be published yet",
                "_stderr_full": "Could not determine the type for the passed topic",
                "timed_out": False,
            },
            {
                "command": ["ssh", "true"],
                "returncode": 0,
                "stdout": "At time 1.0\n- Translation: [0.0, 0.0, 0.0]\n- Rotation: in Quaternion [0.0, 0.0, 0.0, 1.0]\nFrame: odom published by <no authority available>\nFrame: map published by <no authority available>",
                "stderr": "",
                "_stdout_full": "At time 1.0\n- Translation: [0.0, 0.0, 0.0]\n- Rotation: in Quaternion [0.0, 0.0, 0.0, 1.0]\nFrame: odom published by <no authority available>\nFrame: map published by <no authority available>",
                "_stderr_full": "",
                "timed_out": False,
            },
            {
                "command": ["ssh", "true"],
                "returncode": 0,
                "stdout": "At time 1.0\n- Translation: [0.0, 0.0, 0.0]\n- Rotation: in Quaternion [0.0, 0.0, 0.0, 1.0]\nFrame: base_link published by <no authority available>\nFrame: map published by <no authority available>",
                "stderr": "",
                "_stdout_full": "At time 1.0\n- Translation: [0.0, 0.0, 0.0]\n- Rotation: in Quaternion [0.0, 0.0, 0.0, 1.0]\nFrame: base_link published by <no authority available>\nFrame: map published by <no authority available>",
                "_stderr_full": "",
                "timed_out": False,
            },
        ]
        args = preflight.parse_args(["--mode", "ssh", "--output", "/tmp/unused.json"])
        with mock.patch.object(preflight, "run_ros_command", side_effect=results):
            check, status = preflight.check_localization_smoke(args, remote=True)

        self.assertEqual(status, "blocked_live_localization_chain_not_ready")
        self.assertFalse(check["ok"])
        blocked = {item["blocked_reason"] for item in check["results"] if item["blocked_reason"]}
        self.assertIn("blocked_amcl_pose_not_observed", blocked)
        amcl_item = next(item for item in check["results"] if item["name"] == "/amcl_pose")
        self.assertFalse(amcl_item["observed"])

    def test_localization_smoke_blocker_skips_refresh_and_keeps_flags_false(self):
        # localization smoke 没 ready 时，packet 也要给出 blocker 和固定 false 的 no-motion 字段。
        args = preflight.parse_args(["--mode", "ssh", "--output", "/tmp/unused.json"])
        checks = {
            "environment": {"ok": True},
            "localization_smoke": {
                "ok": False,
                "blocked_reasons": ["blocked_scan_not_observed"],
                "results": [],
                "templates": preflight.localization_smoke_templates("root@192.168.1.11", 37878),
            },
            "nav2_proof_refresh": {
                "ok": None,
                "template": preflight.nav2_refresh_template("root@192.168.1.11", 37878),
                "note": "skipped because live localization chain is not ready",
            },
            "amcl_map_tf_root_cause": {
                "ok": False,
                "map_topic": {"topic_type": None, "publisher_count": 0, "blocked_reasons": ["blocked_map_topic_type_missing"]},
                "amcl_pose_topic": {"topic_type": None, "publisher_count": 0, "blocked_reasons": ["blocked_amcl_pose_topic_type_missing"]},
                "managed_map_yaml": {"configured_basename": "trashbot_map.yaml", "summary": {"exists": False, "basename": "trashbot_map.yaml"}, "blocked_reasons": ["blocked_managed_map_yaml_missing"]},
                "lifecycle_states": {"results": [], "blocked_reasons": []},
            },
        }
        with mock.patch.object(preflight, "ssh_real_checks", return_value=(checks, "blocked_live_localization_chain_not_ready")):
            packet = preflight.build_packet(args)

        self.assertEqual(packet["status"], "blocked_live_localization_chain_not_ready")
        self.assertFalse(packet["safe_to_control"])
        self.assertFalse(packet["delivery_success"])
        self.assertFalse(packet["robot_control_executed"])
        self.assertFalse(packet["route_execution_success"])
        self.assertFalse(packet["hil_pass"])
        self.assertIn("root_cause_summary", packet)
        self.assertEqual(packet["root_cause_summary"]["managed_map_yaml"]["summary"]["exists"], False)
        self.assertEqual(packet["root_cause_summary"]["managed_map_yaml"]["configured_basename"], "trashbot_map.yaml")
        self.assertNotIn("/root/", json.dumps(packet["root_cause_summary"], ensure_ascii=False))

    def test_probe_topic_metadata_reports_missing_type_and_publishers(self):
        # map/amcl topic metadata 需要把未知类型和 0 publisher 明确拆开，不能只留 echo 现象。
        args = preflight.parse_args(["--mode", "local", "--output", "/tmp/unused.json"])
        side_effect = [
            {
                "command": ["ros2", "topic", "type", "/map"],
                "returncode": 1,
                "stdout": "",
                "stderr": "Unknown topic '/map'",
                "_stdout_full": "",
                "_stderr_full": "Unknown topic '/map'",
                "timed_out": False,
            },
            {
                "command": ["ros2", "topic", "info", "-v", "/map"],
                "returncode": 0,
                "stdout": "Type: unknown\nPublisher count: 0\nSubscription count: 1",
                "stderr": "",
                "_stdout_full": "Type: unknown\nPublisher count: 0\nSubscription count: 1",
                "_stderr_full": "",
                "timed_out": False,
            },
        ]
        with mock.patch.object(preflight, "run_ros_command", side_effect=side_effect):
            probe = preflight.probe_topic_metadata(args, remote=False, topic="/map", required_type="nav_msgs/msg/OccupancyGrid")

        self.assertFalse(probe["ok"])
        self.assertIn("blocked_map_topic_type_missing", probe["blocked_reasons"])
        self.assertIn("blocked_map_publisher_missing", probe["blocked_reasons"])
        self.assertEqual(probe["publisher_count"], 0)

    def test_probe_managed_map_yaml_extracts_safe_summary(self):
        # managed map yaml 只允许输出 basename 与 sha256 前缀，避免把完整文件内容打进 artifact。
        args = preflight.parse_args(["--mode", "local", "--output", "/tmp/unused.json"])
        payload = {"exists": True, "basename": "trashbot_map.yaml", "size_bytes": 42, "sha256_prefix": "abc123def456"}
        result = {
            "command": ["/bin/sh", "-lc", "python3 - <<'PY'"],
            "returncode": 0,
            "stdout": json.dumps(payload),
            "stderr": "",
            "_stdout_full": json.dumps(payload),
            "_stderr_full": "",
            "timed_out": False,
        }
        with mock.patch.object(preflight, "run_command", return_value=result):
            probe = preflight.probe_managed_map_yaml(args, remote=False)

        self.assertTrue(probe["ok"])
        self.assertEqual(probe["configured_basename"], "trashbot_map.yaml")
        self.assertEqual(probe["summary"]["basename"], "trashbot_map.yaml")
        self.assertEqual(probe["summary"]["sha256_prefix"], "abc123def456")
        rendered = json.dumps(probe, ensure_ascii=False)
        self.assertNotIn("/root/", rendered)
        self.assertNotIn(preflight.MANAGED_MAP_YAML, rendered)

    def test_root_cause_summary_compacts_high_value_fields(self):
        # 顶层 root-cause summary 要压缩成 sprint 可直接引用的字段，避免消费完整原始输出。
        checks = {
            "localization_smoke": {
                "blocked_reasons": ["blocked_amcl_pose_not_observed"],
                "results": [
                    {"name": "map->odom", "observed": False, "blocked_reason": "blocked_map_to_odom_not_observed", "failure_summary": "Invalid frame ID \"map\""},
                    {"name": "map->base_link", "observed": False, "blocked_reason": "blocked_map_to_base_link_not_observed", "failure_summary": "Invalid frame ID \"map\""},
                ],
            },
            "amcl_map_tf_root_cause": {
                "scan_topic": {"topic_type": None, "publisher_count": 0, "blocked_reasons": ["blocked_scan_publisher_missing"]},
                "map_topic": {"topic_type": "nav_msgs/msg/OccupancyGrid", "publisher_count": 0, "blocked_reasons": ["blocked_map_publisher_missing"]},
                "amcl_pose_topic": {"topic_type": None, "publisher_count": 0, "blocked_reasons": ["blocked_amcl_pose_topic_type_missing"]},
                "managed_map_yaml": {"configured_basename": "trashbot_map.yaml", "summary": {"exists": False, "basename": "trashbot_map.yaml"}, "blocked_reasons": ["blocked_managed_map_yaml_missing"]},
                "lifecycle_states": {
                    "results": [
                        {"node": "/map_server", "state": "inactive", "blocked_reasons": ["blocked_map_server_lifecycle_not_active"]},
                        {"node": "/amcl", "state": "inactive", "blocked_reasons": ["blocked_amcl_lifecycle_not_active"]},
                    ]
                },
            },
            "nav2_proof_refresh": {
                "summary": {
                    "status": "refresh_command_failed",
                    "timed_out": False,
                    "naturally_returned": True,
                    "returncode": 28,
                    "root_causes": [],
                    "blocked_reasons": [],
                    "path_generated": False,
                    "path_generation_succeeded": False,
                    "path_point_count": 0,
                    "curl_max_time_s": 38,
                    "process_timeout_s": 42,
                }
            },
            "topics": {
                "result": {
                    "daemon_fault_detected": True,
                    "daemon_recovered": True,
                    "retry_attempts": 1,
                    "ros_cli_retry": {
                        "eligible": True,
                        "attempted": True,
                        "target": "topic_list",
                        "initial_failure_summary": "xmlrpc.client.Fault: RuntimeError: !rclpy.ok()",
                        "retry_failure_summary": None,
                    },
                    "ros_daemon_health": {"health_ok": True, "reset_failed": False},
                }
            },
        }

        summary = preflight.root_cause_from_checks(checks)

        self.assertEqual(summary["scan_topic"]["publisher_count"], 0)
        self.assertEqual(summary["map_topic"]["publisher_count"], 0)
        self.assertEqual(summary["amcl_pose_topic"]["blocked_reasons"], ["blocked_amcl_pose_topic_type_missing"])
        self.assertEqual(summary["managed_map_yaml"]["summary"]["exists"], False)
        self.assertEqual(summary["managed_map_yaml"]["configured_basename"], "trashbot_map.yaml")
        self.assertNotIn("/root/", json.dumps(summary, ensure_ascii=False))
        self.assertEqual(summary["lifecycle_states"][0]["state"], "inactive")
        self.assertEqual(summary["nav2_refresh"]["status"], "refresh_command_failed")
        self.assertEqual(summary["nav2_refresh"]["returncode"], 28)
        self.assertTrue(summary["nav2_refresh"]["naturally_returned"])
        self.assertTrue(summary["daemon_fault_detected"])
        self.assertTrue(summary["daemon_recovered"])
        self.assertEqual(summary["retry_attempts"], 1)
        self.assertIn("topic_list", summary["recovered_targets"])
        self.assertIn("lidar_missing", summary["root_cause_layers"])
        self.assertIn("map_server_not_active", summary["root_cause_layers"])
        self.assertIn("amcl_not_active", summary["root_cause_layers"])
        self.assertIn("tf_missing", summary["root_cause_layers"])


if __name__ == "__main__":
    unittest.main()
