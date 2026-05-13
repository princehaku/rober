import json
import pathlib
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "ros2_trashbot_behavior"))

from ros2_trashbot_behavior.remote_cloud_relay import (  # noqa: E402
    build_server,
)
from ros2_trashbot_behavior.remote_bridge_protocol import (
    InvalidRemoteCommand,
    PROTOCOL_VERSION,
    RemoteCloudError,
    RemoteCloudClient,
    command_expired,
    make_status,
    parse_bool,
    validate_command,
)


class MockCloud:
    def __init__(self):
        self.commands = []
        self.statuses = []
        self.acks = []
        self.response_extras = {}

    def handler(self):
        cloud = self

        class Handler(BaseHTTPRequestHandler):
            def _send_json(self, status, payload):
                data = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                parts = urlparse(self.path).path.strip("/").split("/")
                if len(parts) == 4 and parts[0] == "robots" and parts[2:] == ["commands", "next"]:
                    if unquote(parts[1]) != "robot-1" and unquote(parts[1]) != "robot/with space":
                        self._send_json(404, {"error": "unknown robot"})
                        return
                    command = cloud.commands.pop(0) if cloud.commands else None
                    payload = {"command": command}
                    # command_response 只模拟云端 sidecar metadata，不能改变 command envelope 选择。
                    payload.update(cloud.response_extras.get("command_response", {}))
                    self._send_json(200, payload)
                    return
                self._send_json(404, {"error": "not found"})

            def do_POST(self):
                parts = urlparse(self.path).path.strip("/").split("/")
                length = int(self.headers.get("Content-Length") or 0)
                payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
                if len(parts) == 3 and parts[0] == "robots" and parts[2] == "status":
                    if unquote(parts[1]) != "robot-1" and unquote(parts[1]) != "robot/with space":
                        self._send_json(404, {"error": "unknown robot"})
                        return
                    cloud.statuses.append(payload)
                    response = {"ok": True}
                    # status_response 是云端回包元数据，不能反向污染 robot POST 的 status envelope。
                    response.update(cloud.response_extras.get("status_response", {}))
                    self._send_json(200, response)
                    return
                if len(parts) == 5 and parts[0] == "robots" and parts[2] == "commands" and parts[4] == "ack":
                    if unquote(parts[1]) != "robot-1" and unquote(parts[1]) != "robot/with space":
                        self._send_json(404, {"error": "unknown robot"})
                        return
                    cloud.acks.append(payload)
                    response = {"ok": True}
                    # ack_response 只能证明云端收包，不能把 ACK 升级成 delivery success。
                    response.update(cloud.response_extras.get("ack_response", {}))
                    self._send_json(200, response)
                    return
                self._send_json(404, {"error": "not found"})

            def log_message(self, _format, *_args):
                return

        return Handler


class RemoteBridgeProtocolTest(unittest.TestCase):
    def setUp(self):
        self.cloud = MockCloud()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), self.cloud.handler())
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=1.0)

    def test_validate_command_rejects_bad_shape(self):
        self.assertIsNone(validate_command(None))
        with self.assertRaises(ValueError):
            validate_command([])
        with self.assertRaises(ValueError):
            validate_command({"id": "1", "type": "dance"})
        with self.assertRaises(ValueError):
            validate_command({"id": "1", "type": "collect", "payload": []})

    def test_validate_command_ignores_queue_ordering_metadata_outside_envelope(self):
        command = validate_command({
            "id": "cmd-queue-metadata",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
            "queue_ordering_drill": {
                "schema": "trashbot.queue_ordering_drill",
                "status": "ready",
                "delivery_success": True,
            },
            "ordering_status": "cmd_9_before_cmd_10_verified",
        })

        self.assertEqual(command["id"], "cmd-queue-metadata")
        self.assertEqual(command["type"], "collect")
        self.assertEqual(command["payload"]["target"], "trash_station")
        # protocol helper 只返回 trashbot.remote.v1 command envelope，不把 drill 元数据转给 robot 执行层。
        self.assertNotIn("queue_ordering_drill", command)
        self.assertNotIn("ordering_status", command)

    def test_validate_command_ignores_phone_offline_resume_metadata_outside_envelope(self):
        command = validate_command({
            "id": "cmd-offline-resume-metadata",
            "type": "cancel",
            "payload": {},
            "phone_offline_resume_readiness": {
                "schema": "trashbot.phone_offline_resume_readiness.v1",
                "connection_state": "offline",
                "trigger_robot_action": "collect",
                "cursor_override": "cmd-future",
                "delivery_success": True,
            },
        })

        self.assertEqual(command["id"], "cmd-offline-resume-metadata")
        self.assertEqual(command["type"], "cancel")
        # phone offline/resume 是手机元数据，validate_command 只返回 robot command envelope。
        self.assertNotIn("phone_offline_resume_readiness", command)
        self.assertNotIn("trigger_robot_action", json.dumps(command))
        self.assertNotIn("delivery_success", json.dumps(command))

    def test_validate_command_ignores_mobile_web_entrypoint_metadata_outside_envelope(self):
        command = validate_command({
            "id": "cmd-mobile-entrypoint-metadata",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
            "mobile_web_entrypoint": {
                "schema": "trashbot.mobile_web_entrypoint.v1",
                "entrypoint_url": "/mobile/",
                "trigger_robot_action": "cancel",
                "cursor_override": "cmd-future",
                "delivery_success": True,
            },
            "mobile_web_entrypoint_readiness": {
                "schema": "trashbot.mobile_web_entrypoint_readiness.v1",
                "overall_status": "ready",
                "ack_semantics": "delivery_success",
            },
            "pwa_entrypoint": {
                "schema": "trashbot.pwa_entrypoint.v1",
                "offline_shell": "ready",
            },
        })

        self.assertEqual(command["id"], "cmd-mobile-entrypoint-metadata")
        self.assertEqual(command["type"], "collect")
        self.assertEqual(command["payload"]["target"], "trash_station")
        encoded_command = json.dumps(command, ensure_ascii=False)
        # mobile web/PWA 字段只服务手机入口展示，不能进入 robot command envelope。
        self.assertNotIn("mobile_web_entrypoint", encoded_command)
        self.assertNotIn("mobile_web_entrypoint_readiness", encoded_command)
        self.assertNotIn("pwa_entrypoint", encoded_command)
        self.assertNotIn("trigger_robot_action", encoded_command)
        self.assertNotIn("cursor_override", encoded_command)
        self.assertNotIn("delivery_success", encoded_command)

    def test_validate_command_ignores_mobile_device_acceptance_metadata_outside_envelope(self):
        command = validate_command({
            "id": "cmd-mobile-device-acceptance-metadata",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
            "mobile_device_acceptance_readiness": {
                "schema": "trashbot.mobile_device_acceptance_readiness.v1",
                "overall_status": "ready",
                "trigger_robot_action": "confirm_dropoff",
                "cursor_override": "cmd-future",
                "ack_semantics": "delivery_success",
                "delivery_success": True,
                "raw_ros_topic": "/trashbot/collect_trash",
            },
            "phone_device_acceptance_readiness": {
                "schema": "trashbot.phone_device_acceptance_readiness.v1",
                "support_entry_enabled": True,
                "next_action": "cancel",
                "serial_device": "/dev/ttyUSB0",
            },
            "mobile_browser_acceptance_readiness": {
                "schema": "trashbot.mobile_browser_acceptance_readiness.v1",
                "browser_acceptance_ready": True,
                "Authorization": "Bearer must-not-leak",
            },
        })

        self.assertEqual(command["id"], "cmd-mobile-device-acceptance-metadata")
        self.assertEqual(command["type"], "collect")
        self.assertEqual(command["payload"], {"target": "trash_station", "trash_type": 0})
        encoded_command = json.dumps(command, ensure_ascii=False)
        # 设备/浏览器验收 readiness 只服务手机验收面板，不能扩展 robot command envelope。
        self.assertNotIn("mobile_device_acceptance_readiness", encoded_command)
        self.assertNotIn("phone_device_acceptance_readiness", encoded_command)
        self.assertNotIn("mobile_browser_acceptance_readiness", encoded_command)
        self.assertNotIn("trigger_robot_action", encoded_command)
        self.assertNotIn("cursor_override", encoded_command)
        self.assertNotIn("delivery_success", encoded_command)
        self.assertNotIn("/trashbot/collect_trash", encoded_command)
        self.assertNotIn("/dev/ttyUSB0", encoded_command)
        self.assertNotIn("Authorization", encoded_command)

    def test_validate_command_ignores_mobile_browser_acceptance_bundle_metadata_outside_envelope(self):
        command = validate_command({
            "id": "cmd-mobile-browser-acceptance-bundle",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
            "mobile_browser_acceptance_bundle": {
                "schema": "trashbot.mobile_browser_acceptance_bundle.v1",
                "overall_status": "blocked",
                "safe_to_control": False,
                "trigger_robot_action": "cancel",
                "cursor_override": "cmd-future",
                "ack_semantics": "delivery_success",
                "delivery_success": True,
                "raw_ros_topic": "/cmd_vel",
            },
            "phone_browser_acceptance_bundle": {
                "schema": "trashbot.phone_browser_acceptance_bundle.v1",
                "safe_phone_copy": "ACK 仅代表命令已接收或处理中，不代表送达成功。",
                "support_handoff": {"next_action": "confirm_dropoff"},
                "serial_device": "/dev/ttyUSB0",
            },
            "mobile_acceptance_evidence_bundle": {
                "schema": "trashbot.mobile_acceptance_evidence_bundle.v1",
                "evidence_boundary": "software_proof_docker_mobile_browser_acceptance_bundle_gate",
                "Authorization": "Bearer must-not-leak",
            },
        })

        self.assertEqual(command["id"], "cmd-mobile-browser-acceptance-bundle")
        self.assertEqual(command["type"], "collect")
        self.assertEqual(command["payload"], {"target": "trash_station", "trash_type": 0})
        encoded_command = json.dumps(command, ensure_ascii=False)
        # 浏览器验收 bundle 是 phone/support metadata，normalization 只能保留 command envelope。
        self.assertNotIn("mobile_browser_acceptance_bundle", encoded_command)
        self.assertNotIn("phone_browser_acceptance_bundle", encoded_command)
        self.assertNotIn("mobile_acceptance_evidence_bundle", encoded_command)
        self.assertNotIn("trigger_robot_action", encoded_command)
        self.assertNotIn("cursor_override", encoded_command)
        self.assertNotIn("delivery_success", encoded_command)
        self.assertNotIn("/cmd_vel", encoded_command)
        self.assertNotIn("/dev/ttyUSB0", encoded_command)
        self.assertNotIn("Authorization", encoded_command)

    def test_mobile_browser_acceptance_bundle_response_metadata_does_not_create_command_or_ack(self):
        self.cloud.response_extras.update({
            "command_response": {
                "mobile_browser_acceptance_bundle": {
                    "schema": "trashbot.mobile_browser_acceptance_bundle.v1",
                    "overall_status": "blocked",
                    "safe_to_control": False,
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-future",
                    "delivery_success": True,
                },
                "phone_browser_acceptance_bundle": {
                    "schema": "trashbot.phone_browser_acceptance_bundle.v1",
                    "safe_phone_copy": "仅供手机诊断展示。",
                    "next_action": "confirm_dropoff",
                },
                "mobile_acceptance_evidence_bundle": {
                    "schema": "trashbot.mobile_acceptance_evidence_bundle.v1",
                    "evidence_boundary": "software_proof_docker_mobile_browser_acceptance_bundle_gate",
                },
            },
            "status_response": {
                "mobile_browser_acceptance_bundle": {"delivery_success": True},
            },
            "ack_response": {
                "mobile_acceptance_evidence_bundle": {
                    "ack_semantics": "delivery_success",
                    "delivery_success": True,
                },
            },
        })
        client = RemoteCloudClient(self.base_url, "robot-1", timeout_sec=2)

        status_response = client.post_status(make_status("robot-1", "waiting_for_trash", "ready"))
        command = client.get_next_command()

        self.assertIsNone(command)
        self.assertEqual(self.cloud.acks, [])
        encoded_status = json.dumps(self.cloud.statuses[0], ensure_ascii=False)
        self.assertNotIn("mobile_browser_acceptance_bundle", encoded_status)
        self.assertNotIn("phone_browser_acceptance_bundle", encoded_status)
        self.assertNotIn("mobile_acceptance_evidence_bundle", encoded_status)
        self.assertNotIn("delivery_success", encoded_status)
        self.assertTrue(status_response["ok"])
        # protocol client 不会从 metadata-only response 合成 command id 或 terminal ACK。
        self.assertNotIn("command_id", json.dumps(command, ensure_ascii=False))

    def test_validate_command_ignores_mobile_task_start_confirmation_metadata_outside_envelope(self):
        command = validate_command({
            "id": "cmd-mobile-task-start-confirmation",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
            "mobile_task_start_confirmation": {
                "schema": "trashbot.mobile_task_start_confirmation.v1",
                "trash_loaded_confirmed": True,
                "selected_destination": "trash_station",
                "trigger_robot_action": "confirm_dropoff",
                "delivery_success": True,
            },
            "mobile_task_start_confirmation_readiness": {
                "schema": "trashbot.mobile_task_start_confirmation_readiness.v1",
                "overall_status": "ready",
                "ack_semantics": "delivery_success",
                "cursor_override": "cmd-future",
            },
            "task_start_confirmation_payload": {
                "source": "mobile/web",
                "destination": "trash_station",
                "trash_loaded_confirmed": True,
                "raw_ros_topic": "/trashbot/collect_trash",
            },
        })

        self.assertEqual(command["id"], "cmd-mobile-task-start-confirmation")
        self.assertEqual(command["type"], "collect")
        self.assertEqual(command["payload"], {"target": "trash_station", "trash_type": 0})
        encoded_command = json.dumps(command, ensure_ascii=False)
        # 手机确认 payload 不是 robot command envelope，parser 只保留既有 id/type/payload 语义。
        self.assertNotIn("mobile_task_start_confirmation", encoded_command)
        self.assertNotIn("mobile_task_start_confirmation_readiness", encoded_command)
        self.assertNotIn("task_start_confirmation_payload", encoded_command)
        self.assertNotIn("trigger_robot_action", encoded_command)
        self.assertNotIn("cursor_override", encoded_command)
        self.assertNotIn("delivery_success", encoded_command)
        self.assertNotIn("/trashbot/collect_trash", encoded_command)

    def test_validate_command_ignores_mobile_action_feedback_metadata_outside_envelope(self):
        command = validate_command({
            "id": "cmd-mobile-action-feedback",
            "type": "confirm_dropoff",
            "payload": {"accepted": True},
            "mobile_action_confirmation": {
                "schema": "trashbot.mobile_action_confirmation.v1",
                "source": "mobile_web",
                "action": "confirm_dropoff",
                "user_confirmed": True,
                "trigger_robot_action": "cancel",
                "cursor_override": "cmd-future",
                "ack_semantics": "delivery_success",
                "delivery_success": True,
            },
            "mobile_action_receipt": {
                "schema": "trashbot.mobile_action_receipt.v1",
                "action": "cancel",
                "receipt_state": "accepted",
                "serial_device": "/dev/ttyUSB0",
                "raw_ros_topic": "/trashbot/cancel",
            },
            "phone_action_feedback": {
                "schema": "trashbot.phone_action_feedback.v1",
                "safe_phone_copy": "命令已提交，等待机器人处理。",
                "recovery_hint": "继续观察状态。",
                "raw_ros_topic": "/cmd_vel",
            },
        })

        self.assertEqual(command["id"], "cmd-mobile-action-feedback")
        self.assertEqual(command["type"], "confirm_dropoff")
        self.assertEqual(command["payload"], {"accepted": True})
        encoded_command = json.dumps(command, ensure_ascii=False)
        # 动作回执是 phone-safe metadata，不能扩展或覆盖 robot command envelope。
        self.assertNotIn("mobile_action_confirmation", encoded_command)
        self.assertNotIn("mobile_action_receipt", encoded_command)
        self.assertNotIn("phone_action_feedback", encoded_command)
        self.assertNotIn("trigger_robot_action", encoded_command)
        self.assertNotIn("cursor_override", encoded_command)
        self.assertNotIn("delivery_success", encoded_command)
        self.assertNotIn("/cmd_vel", encoded_command)
        self.assertNotIn("/dev/ttyUSB0", encoded_command)

    def test_validate_command_ignores_operation_log_metadata_outside_envelope(self):
        command = validate_command({
            "id": "cmd-operation-log-metadata",
            "type": "cancel",
            "payload": {},
            "operation_log": {
                "schema": "trashbot.phone_operation_log.v1",
                "events": [
                    {
                        "kind": "pending_ack",
                        "safe_phone_copy": "命令已提交，正在等待机器人处理。",
                    },
                ],
                "trigger_robot_action": "collect",
                "cursor_override": "cmd-future",
                "ack_semantics": "delivery_success",
                "delivery_success": True,
                "raw_ros_topic": "/cmd_vel",
            },
            "phone_operation_log": {
                "schema": "trashbot.phone_operation_log.v1",
                "support_handoff": {"next_action": "confirm_dropoff"},
            },
        })

        self.assertEqual(command["id"], "cmd-operation-log-metadata")
        self.assertEqual(command["type"], "cancel")
        self.assertEqual(command["payload"], {})
        encoded_command = json.dumps(command, ensure_ascii=False)
        # operation log 是手机/支持元数据，parser 只能保留 command envelope 的既有字段。
        self.assertNotIn("operation_log", encoded_command)
        self.assertNotIn("phone_operation_log", encoded_command)
        self.assertNotIn("trigger_robot_action", encoded_command)
        self.assertNotIn("cursor_override", encoded_command)
        self.assertNotIn("delivery_success", encoded_command)
        self.assertNotIn("/cmd_vel", encoded_command)

    def test_validate_command_ignores_deployment_readiness_metadata_outside_envelope(self):
        command = validate_command({
            "id": "cmd-deployment-readiness-metadata",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
            "deployment_readiness": {
                "schema": "trashbot.cloud_deployment_readiness",
                "schema_version": 1,
                "production_ready": False,
                "evidence_boundary": "software_proof_docker_cloud_deployment_readiness_gate",
                "trigger_robot_action": "cancel",
                "raw_ros_topic": "/cmd_vel",
                "delivery_success": True,
            },
            "cloud_deployment_readiness": {
                "schema": "trashbot.cloud_deployment_readiness",
                "overall_status": "blocked",
                "credential_url": "https://user:secret@example.invalid",
            },
            "preflight": {
                "production_ready": False,
                "Authorization": "Bearer must-not-leak",
            },
        })

        self.assertEqual(command["id"], "cmd-deployment-readiness-metadata")
        self.assertEqual(command["type"], "collect")
        self.assertEqual(command["payload"]["target"], "trash_station")
        encoded_command = json.dumps(command, ensure_ascii=False)
        # deployment readiness 只是云部署诊断元数据，不能扩展 robot command envelope。
        self.assertNotIn("deployment_readiness", encoded_command)
        self.assertNotIn("cloud_deployment_readiness", encoded_command)
        self.assertNotIn("preflight", encoded_command)
        self.assertNotIn("trigger_robot_action", encoded_command)
        self.assertNotIn("delivery_success", encoded_command)
        self.assertNotIn("/cmd_vel", encoded_command)
        self.assertNotIn("Authorization", encoded_command)
        self.assertNotIn("credential_url", encoded_command)

    def test_validate_command_ignores_cloud_external_probe_metadata_outside_envelope(self):
        command = validate_command({
            "id": "cmd-cloud-external-probe-metadata",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
            "cloud_external_probe": {
                "schema": "trashbot.cloud_external_probe_bundle",
                "schema_version": 1,
                "endpoint_results": {
                    "/healthz": {"status": "ok"},
                    "/readyz": {"status": "blocked"},
                    "/preflightz": {"status": "blocked"},
                },
                "production_ready": False,
                "trigger_robot_action": "cancel",
                "cursor_override": "cmd-future",
                "delivery_success": True,
            },
            "cloud_external_probe_bundle": {
                "schema": "trashbot.cloud_external_probe_bundle",
                "overall_status": "blocked",
                "Authorization": "Bearer must-not-leak",
            },
        })

        self.assertEqual(command["id"], "cmd-cloud-external-probe-metadata")
        self.assertEqual(command["type"], "collect")
        self.assertEqual(command["payload"], {"target": "trash_station", "trash_type": 0})
        encoded_command = json.dumps(command, ensure_ascii=False)
        # cloud external probe 只描述云端探测摘要，不能进入 robot command envelope。
        self.assertNotIn("cloud_external_probe", encoded_command)
        self.assertNotIn("cloud_external_probe_bundle", encoded_command)
        self.assertNotIn("trigger_robot_action", encoded_command)
        self.assertNotIn("cursor_override", encoded_command)
        self.assertNotIn("delivery_success", encoded_command)
        self.assertNotIn("Authorization", encoded_command)

    def test_validate_command_ignores_public_ingress_tls_metadata_outside_envelope(self):
        command = validate_command({
            "id": "cmd-public-ingress-tls-metadata",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
            "cloud_public_ingress_tls": {
                "schema": "trashbot.cloud_public_ingress_tls.v1",
                "production_ready": False,
                "overall_status": "blocked",
                "trigger_robot_action": "cancel",
                "cursor_override": "cmd-future",
                "delivery_success": True,
                "Authorization": "Bearer must-not-leak",
                "raw_ros_topic": "/cmd_vel",
            },
            "public_ingress_tls": {
                "schema": "trashbot.public_ingress_tls.v1",
                "tls_config_present": True,
                "external_probe_proven": False,
                "credential_url": "https://user:secret@example.invalid",
            },
            "cloud_public_ingress_tls_gate": {
                "schema": "trashbot.cloud_public_ingress_tls_gate.v1",
                "ack_semantics": "delivery_success",
            },
            "deployment_readiness": {
                "schema": "trashbot.cloud_deployment_readiness",
                "production_ready": False,
            },
        })

        self.assertEqual(command["id"], "cmd-public-ingress-tls-metadata")
        self.assertEqual(command["type"], "collect")
        self.assertEqual(command["payload"], {"target": "trash_station", "trash_type": 0})
        encoded_command = json.dumps(command, ensure_ascii=False)
        # 公网入口/TLS readiness 是部署诊断元数据，parser 只能保留 robot command envelope。
        self.assertNotIn("cloud_public_ingress_tls", encoded_command)
        self.assertNotIn("public_ingress_tls", encoded_command)
        self.assertNotIn("cloud_public_ingress_tls_gate", encoded_command)
        self.assertNotIn("deployment_readiness", encoded_command)
        self.assertNotIn("trigger_robot_action", encoded_command)
        self.assertNotIn("cursor_override", encoded_command)
        self.assertNotIn("delivery_success", encoded_command)
        self.assertNotIn("Authorization", encoded_command)
        self.assertNotIn("credential_url", encoded_command)
        self.assertNotIn("/cmd_vel", encoded_command)

    def test_validate_command_ignores_cloud_db_queue_config_metadata_outside_envelope(self):
        command = validate_command({
            "id": "cmd-cloud-db-queue-config-metadata",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
            "cloud_db_queue_config": {
                "schema": "trashbot.cloud_db_queue_config.v1",
                "overall_status": "blocked",
                "trigger_robot_action": "cancel",
                "cursor_override": "cmd-future",
                "delivery_success": True,
                "db_url": "postgres://user:secret@example.invalid/db",
                "queue_url": "amqp://user:secret@example.invalid/q",
            },
            "cloud_db_queue_config_gate": {
                "schema": "trashbot.cloud_db_queue_config_gate.v1",
                "production_ready": False,
                "next_action": "confirm_dropoff",
                "Authorization": "Bearer must-not-leak",
            },
            "db_queue_config": {
                "schema": "trashbot.db_queue_config.v1",
                "queue_contract_status": "configured_in_cloud_only",
                "raw_ros_topic": "/cmd_vel",
            },
        })

        self.assertEqual(command["id"], "cmd-cloud-db-queue-config-metadata")
        self.assertEqual(command["type"], "collect")
        self.assertEqual(command["payload"], {"target": "trash_station", "trash_type": 0})
        encoded_command = json.dumps(command, ensure_ascii=False)
        # DB/queue readiness 是云控制面配置证明，parser 只能保留 robot command envelope。
        self.assertNotIn("cloud_db_queue_config", encoded_command)
        self.assertNotIn("cloud_db_queue_config_gate", encoded_command)
        self.assertNotIn("db_queue_config", encoded_command)
        self.assertNotIn("trigger_robot_action", encoded_command)
        self.assertNotIn("cursor_override", encoded_command)
        self.assertNotIn("delivery_success", encoded_command)
        self.assertNotIn("postgres://", encoded_command)
        self.assertNotIn("amqp://", encoded_command)
        self.assertNotIn("Authorization", encoded_command)
        self.assertNotIn("/cmd_vel", encoded_command)

    def test_validate_command_ignores_cloud_db_queue_external_probe_metadata_outside_envelope(self):
        command = validate_command({
            "id": "cmd-cloud-db-queue-external-probe-metadata",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
            "cloud_db_queue_external_probe": {
                "schema": "trashbot.cloud_db_queue_external_probe.v1",
                "overall_status": "blocked",
                "production_ready": False,
                "trigger_robot_action": "cancel",
                "cursor_override": "cmd-future",
                "delivery_success": True,
                "db_probe_url": "postgres://user:secret@example.invalid/db",
                "queue_probe_url": "amqp://user:secret@example.invalid/q",
            },
            "cloud_db_queue_external_probe_bundle": {
                "schema": "trashbot.cloud_db_queue_external_probe_bundle",
                "schema_version": 1,
                "evidence_boundary": "software_proof_docker_cloud_db_queue_external_probe_gate",
                "endpoint_results": {"db": {"status": "blocked"}, "queue": {"status": "blocked"}},
                "Authorization": "Bearer must-not-leak",
            },
            "db_queue_external_probe": {
                "schema": "trashbot.db_queue_external_probe.v1",
                "external_probe_status": "not_proven",
                "raw_ros_topic": "/cmd_vel",
            },
        })

        self.assertEqual(command["id"], "cmd-cloud-db-queue-external-probe-metadata")
        self.assertEqual(command["type"], "collect")
        self.assertEqual(command["payload"], {"target": "trash_station", "trash_type": 0})
        encoded_command = json.dumps(command, ensure_ascii=False)
        # DB/queue external probe 只证明云端探测元数据，normalization 只能留下 command envelope。
        self.assertNotIn("cloud_db_queue_external_probe", encoded_command)
        self.assertNotIn("cloud_db_queue_external_probe_bundle", encoded_command)
        self.assertNotIn("db_queue_external_probe", encoded_command)
        self.assertNotIn("trigger_robot_action", encoded_command)
        self.assertNotIn("cursor_override", encoded_command)
        self.assertNotIn("delivery_success", encoded_command)
        self.assertNotIn("postgres://", encoded_command)
        self.assertNotIn("amqp://", encoded_command)
        self.assertNotIn("Authorization", encoded_command)
        self.assertNotIn("/cmd_vel", encoded_command)

    def test_validate_command_ignores_oss_cdn_live_probe_metadata_outside_envelope(self):
        command = validate_command({
            "id": "cmd-oss-cdn-live-probe-metadata",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
            "oss_cdn_live_probe": {
                "schema": "trashbot.oss_cdn_live_probe.v1",
                "overall_status": "blocked",
                "production_ready": False,
                "live_probe_complete": False,
                "trigger_robot_action": "cancel",
                "cursor_override": "cmd-future",
                "delivery_success": True,
                "credential_url": "https://user:secret@cdn.example.invalid/rober/private",
            },
            "oss_cdn_live_probe_artifact": {
                "schema": "trashbot.oss_cdn_live_probe_artifact.v1",
                "evidence_boundary": "software_proof_docker_oss_cdn_live_probe_gate",
                "object_key_hash": "sha256:redacted",
                "Authorization": "Bearer must-not-leak",
            },
            "cdn_live_probe": {
                "schema": "trashbot.cdn_live_probe.v1",
                "probe_status": "not_proven",
                "raw_ros_topic": "/cmd_vel",
            },
        })

        self.assertEqual(command["id"], "cmd-oss-cdn-live-probe-metadata")
        self.assertEqual(command["type"], "collect")
        self.assertEqual(command["payload"], {"target": "trash_station", "trash_type": 0})
        encoded_command = json.dumps(command, ensure_ascii=False)
        # OSS/CDN live probe 只是手机/支持侧 readiness 元数据，不能扩展 robot command envelope。
        self.assertNotIn("oss_cdn_live_probe", encoded_command)
        self.assertNotIn("oss_cdn_live_probe_artifact", encoded_command)
        self.assertNotIn("cdn_live_probe", encoded_command)
        self.assertNotIn("trigger_robot_action", encoded_command)
        self.assertNotIn("cursor_override", encoded_command)
        self.assertNotIn("delivery_success", encoded_command)
        self.assertNotIn("credential_url", encoded_command)
        self.assertNotIn("Authorization", encoded_command)
        self.assertNotIn("/cmd_vel", encoded_command)

    def test_validate_command_ignores_cloud_readiness_summary_metadata_outside_envelope(self):
        command = validate_command({
            "id": "cmd-cloud-readiness-summary-metadata",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
            "phone_cloud_readiness_summary": {
                "schema": "trashbot.phone_cloud_readiness_summary.v1",
                "overall_status": "blocked",
                "safe_phone_copy": "云端配置还未完成，先保持本地等待。",
                "trigger_robot_action": "cancel",
                "cursor_override": "cmd-future",
                "delivery_success": True,
                "credential_url": "https://user:secret@example.invalid/creds",
            },
            "mobile_cloud_readiness_summary": {
                "schema": "trashbot.mobile_cloud_readiness_summary.v1",
                "production_ready": True,
                "next_action": "confirm_dropoff",
                "cloud_url": "https://token@example.invalid/mobile",
            },
            "cloud_readiness_summary": {
                "schema": "trashbot.cloud_readiness_summary.v1",
                "production_ready": False,
                "ack_semantics": "delivery_success",
                "Authorization": "Bearer must-not-leak",
                "raw_ros_topic": "/cmd_vel",
            },
        })

        self.assertEqual(command["id"], "cmd-cloud-readiness-summary-metadata")
        self.assertEqual(command["type"], "collect")
        self.assertEqual(command["payload"], {"target": "trash_station", "trash_type": 0})
        encoded_command = json.dumps(command, ensure_ascii=False)
        # 云 readiness summary 是手机/支持摘要，parser 只能保留 robot command envelope。
        self.assertNotIn("phone_cloud_readiness_summary", encoded_command)
        self.assertNotIn("mobile_cloud_readiness_summary", encoded_command)
        self.assertNotIn("cloud_readiness_summary", encoded_command)
        self.assertNotIn("trigger_robot_action", encoded_command)
        self.assertNotIn("cursor_override", encoded_command)
        self.assertNotIn("delivery_success", encoded_command)
        self.assertNotIn("credential_url", encoded_command)
        self.assertNotIn("cloud_url", encoded_command)
        self.assertNotIn("Authorization", encoded_command)
        self.assertNotIn("/cmd_vel", encoded_command)

    def test_validate_command_keeps_command_id_order_as_supplied(self):
        command = validate_command({
            "id": "cmd-10",
            "type": "cancel",
            "payload": {},
            "queue_ordering_drill": {"candidate_command_ids": ["cmd-9", "cmd-10"]},
        })

        # command id 是 relay 已选中的游标标识，helper 不做字符串排序或队列推断。
        self.assertEqual(command["id"], "cmd-10")

    def test_expired_command_detection(self):
        self.assertTrue(command_expired({"expires_at": 1.0}, now=2.0))
        self.assertFalse(command_expired({"expires_at": 3.0}, now=2.0))
        self.assertFalse(command_expired({}, now=2.0))

    def test_parse_bool_accepts_explicit_strings_and_rejects_ambiguous_values(self):
        self.assertTrue(parse_bool("true"))
        self.assertTrue(parse_bool("1"))
        self.assertFalse(parse_bool("false"))
        self.assertFalse(parse_bool("0"))
        self.assertTrue(parse_bool(None, default=True))
        self.assertFalse(parse_bool(None, default=False))
        with self.assertRaises(ValueError):
            parse_bool("maybe")

    def test_status_and_command_ack_round_trip(self):
        self.cloud.commands.append({
            "id": "cmd-1",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
        })
        client = RemoteCloudClient(self.base_url, "robot-1", timeout_sec=2)

        status = make_status("robot-1", "waiting_for_trash", "ready")
        client.post_status(status)
        command = client.get_next_command()
        client.post_ack(command["id"], "acked", "submitted")

        self.assertEqual(self.cloud.statuses[0]["protocol_version"], PROTOCOL_VERSION)
        self.assertEqual(command["type"], "collect")
        self.assertEqual(self.cloud.acks[0]["command_id"], "cmd-1")
        self.assertEqual(self.cloud.acks[0]["state"], "acked")

    def test_cloud_client_url_encodes_robot_and_command_ids(self):
        self.cloud.commands.append({
            "id": "cmd/with space",
            "type": "cancel",
            "payload": {},
        })
        client = RemoteCloudClient(self.base_url, "robot/with space", timeout_sec=2)

        command = client.get_next_command("ack/old")
        client.post_status(make_status("robot/with space", "waiting_for_trash"))
        client.post_ack(command["id"], "acked", "submitted")

        self.assertEqual(command["id"], "cmd/with space")
        self.assertEqual(self.cloud.statuses[0]["robot_id"], "robot/with space")
        self.assertEqual(self.cloud.acks[0]["command_id"], "cmd/with space")

    def test_invalid_remote_command_preserves_raw_command_for_failed_ack(self):
        self.cloud.commands.append({
            "id": "cmd-bad-type",
            "type": "drive",
            "payload": {},
        })
        client = RemoteCloudClient(self.base_url, "robot-1", timeout_sec=2)

        with self.assertRaises(InvalidRemoteCommand) as raised:
            client.get_next_command()

        self.assertEqual(raised.exception.command["id"], "cmd-bad-type")
        self.assertIn("unsupported command.type", str(raised.exception))


class RemoteCloudRelayCompatibilityTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state_path = pathlib.Path(self.tmp.name) / "relay_state.json"
        self.server = build_server("127.0.0.1", 0, self.state_path, "robot-token")
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=1.0)
        self.tmp.cleanup()

    def _seed_collect_command(self, command_id="cmd-relay-1"):
        phone_client = RemoteCloudClient(self.base_url, "trashbot-001", token="robot-token", timeout_sec=2)
        phone_client._request_json(  # noqa: SLF001 - 这里按 relay HTTP 契约种入命令，避免绕过真实 shape。
            "POST",
            "/robots/trashbot-001/commands",
            {
                "protocol_version": PROTOCOL_VERSION,
                "id": command_id,
                "type": "collect",
                "expires_at": time.time() + 300.0,
                "payload": {"target": "trash_station", "trash_type": 1},
            },
        )

    def test_client_round_trips_status_command_and_ack_with_independent_relay(self):
        self._seed_collect_command()
        robot_client = RemoteCloudClient(self.base_url, "trashbot-001", token="robot-token", timeout_sec=2)

        status_response = robot_client.post_status(make_status("trashbot-001", "waiting_for_trash", "ready"))
        command = robot_client.get_next_command()
        ack_response = robot_client.post_ack(
            command["id"],
            "acked",
            "command envelope accepted",
            {"operator_status": {"state": "loaded_and_ready"}},
        )
        next_command = robot_client.get_next_command("cmd-relay-1")

        self.assertTrue(status_response["ok"])
        self.assertEqual(status_response["status"]["state"], "waiting_for_trash")
        self.assertEqual(command["type"], "collect")
        self.assertEqual(command["payload"]["target"], "trash_station")
        self.assertTrue(ack_response["ok"])
        self.assertEqual(ack_response["ack"]["command_id"], "cmd-relay-1")
        self.assertEqual(ack_response["ack"]["state"], "acked")
        # ACK 只证明 command envelope 已处理，真实送达结果仍必须继续看 status/task record。
        self.assertEqual(ack_response["ack"]["result"]["operator_status"]["state"], "loaded_and_ready")
        self.assertIsNone(next_command)

    def test_bearer_auth_failure_maps_to_phone_safe_cloud_error(self):
        client = RemoteCloudClient(self.base_url, "trashbot-001", token="wrong-token", timeout_sec=2)

        with self.assertRaises(RemoteCloudError) as raised:
            client.get_next_command()

        self.assertEqual(raised.exception.reason, "auth_failed")
        self.assertEqual(raised.exception.retry_hint, "check_auth")
        self.assertTrue(raised.exception.cloud_reachable)


if __name__ == "__main__":
    unittest.main()
