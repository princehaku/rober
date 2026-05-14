import json
import pathlib
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "ros2_trashbot_behavior"))

from ros2_trashbot_behavior.remote_bridge import RemoteBridge, RemoteBridgeWorker
from ros2_trashbot_behavior.remote_bridge_protocol import RemoteCloudClient


class MockCloud:
    def __init__(self):
        self.commands = []
        self.status_posts = []
        self.ack_posts = []
        self.auth_headers = []
        self.get_paths = []
        self.fail_status_count = 0
        self.fail_get_count = 0
        self.fail_ack_count = 0
        self.malformed_status_count = 0
        self.malformed_get_count = 0
        self.malformed_ack_count = 0
        self.auth_fail_get_count = 0
        self.response_extras = {}
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), self._make_handler())
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def base_url(self):
        return f"http://127.0.0.1:{self.server.server_address[1]}"

    def start(self):
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=1.0)

    def _make_handler(self):
        cloud = self

        class Handler(BaseHTTPRequestHandler):
            def _json(self, status, payload):
                data = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _body(self):
                length = int(self.headers.get("Content-Length") or 0)
                if length <= 0:
                    return {}
                return json.loads(self.rfile.read(length).decode("utf-8"))

            def do_GET(self):
                if self.path.startswith("/robots/robot-1/commands/next"):
                    cloud.get_paths.append(self.path)
                    cloud.auth_headers.append(self.headers.get("Authorization"))
                    if cloud.auth_fail_get_count > 0:
                        cloud.auth_fail_get_count -= 1
                        self._json(401, {"error": "unauthorized", "Authorization": "Bearer hidden"})
                        return
                    if cloud.fail_get_count > 0:
                        cloud.fail_get_count -= 1
                        self._json(503, {"error": "temporary command outage"})
                        return
                    if cloud.malformed_get_count > 0:
                        cloud.malformed_get_count -= 1
                        data = b"{not-json"
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Content-Length", str(len(data)))
                        self.end_headers()
                        self.wfile.write(data)
                        return
                    command = cloud.commands.pop(0) if cloud.commands else None
                    payload = {"command": command}
                    # 未来 relay/preflight 字段只能作为云端诊断元数据，不能改变 robot bridge 的 envelope 解析。
                    payload.update(cloud.response_extras.get("command_response", {}))
                    self._json(200, payload)
                    return
                self._json(404, {"error": self.path})

            def do_POST(self):
                if self.path == "/robots/robot-1/status":
                    cloud.auth_headers.append(self.headers.get("Authorization"))
                    if cloud.fail_status_count > 0:
                        cloud.fail_status_count -= 1
                        self._json(503, {"error": "temporary status outage"})
                        return
                    if cloud.malformed_status_count > 0:
                        cloud.malformed_status_count -= 1
                        data = b"{not-json"
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Content-Length", str(len(data)))
                        self.end_headers()
                        self.wfile.write(data)
                        return
                    cloud.status_posts.append(self._body())
                    payload = {"ok": True}
                    # status response 的诊断扩展不属于 robot 命令契约，worker 不应消费它们。
                    payload.update(cloud.response_extras.get("status_response", {}))
                    self._json(200, payload)
                    return
                if self.path.startswith("/robots/robot-1/commands/") and self.path.endswith("/ack"):
                    cloud.auth_headers.append(self.headers.get("Authorization"))
                    if cloud.fail_ack_count > 0:
                        cloud.fail_ack_count -= 1
                        self._json(503, {"error": "temporary ack outage"})
                        return
                    if cloud.malformed_ack_count > 0:
                        cloud.malformed_ack_count -= 1
                        data = b"{not-json"
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Content-Length", str(len(data)))
                        self.end_headers()
                        self.wfile.write(data)
                        return
                    cloud.ack_posts.append(self._body())
                    payload = {"ok": True}
                    # ACK response 只能证明云端收到了 ACK envelope，不能升级为 delivery success。
                    payload.update(cloud.response_extras.get("ack_response", {}))
                    self._json(200, payload)
                    return
                self._json(404, {"error": self.path})

            def log_message(self, _format, *_args):
                return

        return Handler


class FakeOperatorBackend:
    def __init__(self, busy=False):
        self.calls = []
        self.busy = busy
        self.last_status = {}

    def snapshot(self):
        return {"state": "waiting_for_trash", "message": "ready"}

    def start_collection(self, target, trash_type=0):
        self.calls.append(("collect", target, trash_type))
        if self.busy:
            return 409, {"state": "busy", "message": "collect command ignored because a task is active"}
        return 202, {"state": "loaded_and_ready", "target": target}

    def confirm_dropoff(self, accepted=True):
        self.calls.append(("confirm_dropoff", accepted))
        return 200, {"state": "returning"}

    def cancel_collection(self):
        self.calls.append(("cancel",))
        return 202, {"state": "canceling"}


class RemoteBridgeWorkerTest(unittest.TestCase):
    def setUp(self):
        self.cloud = MockCloud()
        self.cloud.start()
        self.backend = FakeOperatorBackend()
        self.client = RemoteCloudClient(self.cloud.base_url, "robot-1", timeout_sec=2.0)
        self.worker = RemoteBridgeWorker(self.client, self.backend, "robot-1")

    def tearDown(self):
        self.cloud.stop()

    def test_poll_posts_status_then_collects_and_acks(self):
        self.cloud.commands.append({
            "id": "cmd-1",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 2},
        })

        handled = self.worker.poll_once()

        self.assertTrue(handled)
        self.assertEqual(self.backend.calls, [("collect", "trash_station", 2)])
        self.assertEqual(self.cloud.status_posts[0]["state"], "waiting_for_trash")
        self.assertEqual(self.cloud.status_posts[0]["robot_id"], "robot-1")
        self.assertEqual(self.cloud.ack_posts[0]["command_id"], "cmd-1")
        self.assertEqual(self.cloud.ack_posts[0]["state"], "acked")
        self.assertEqual(self.cloud.ack_posts[0]["result"]["http_status"], 202)
        self.assertEqual(self.cloud.status_posts[-1]["state"], "loaded_and_ready")

    def test_poll_fails_collect_without_target(self):
        self.cloud.commands.append({
            "id": "cmd-missing-target",
            "type": "collect",
            "payload": {},
        })

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.cloud.ack_posts[0]["command_id"], "cmd-missing-target")
        self.assertEqual(self.cloud.ack_posts[0]["state"], "failed")
        self.assertIn("target", self.cloud.ack_posts[0]["message"])

    def test_poll_handles_confirm_dropoff_and_cancel_commands(self):
        self.cloud.commands.extend([
            {"id": "cmd-2", "type": "confirm_dropoff", "payload": {"accepted": False}},
            {"id": "cmd-3", "type": "cancel", "payload": {}},
        ])

        self.assertTrue(self.worker.poll_once())
        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [("confirm_dropoff", False), ("cancel",)])
        self.assertEqual([ack["command_id"] for ack in self.cloud.ack_posts], ["cmd-2", "cmd-3"])
        self.assertEqual([ack["state"] for ack in self.cloud.ack_posts], ["acked", "acked"])

    def test_poll_parses_string_false_dropoff_rejection(self):
        self.cloud.commands.append({
            "id": "cmd-4",
            "type": "confirm_dropoff",
            "payload": {"accepted": "false"},
        })

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [("confirm_dropoff", False)])
        self.assertEqual(self.cloud.ack_posts[0]["command_id"], "cmd-4")
        self.assertEqual(self.cloud.ack_posts[0]["state"], "acked")

    def test_poll_fails_invalid_dropoff_boolean(self):
        self.cloud.commands.append({
            "id": "cmd-5",
            "type": "confirm_dropoff",
            "payload": {"accepted": "maybe"},
        })

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.cloud.ack_posts[0]["command_id"], "cmd-5")
        self.assertEqual(self.cloud.ack_posts[0]["state"], "failed")

    def test_poll_acks_invalid_command_type_when_id_is_present(self):
        self.cloud.commands.append({
            "id": "cmd-bad-type",
            "type": "drive",
            "payload": {"linear": 1.0},
        })

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.cloud.ack_posts[0]["command_id"], "cmd-bad-type")
        self.assertEqual(self.cloud.ack_posts[0]["state"], "failed")
        self.assertIn("malformed command", self.cloud.ack_posts[0]["message"])
        self.assertIn("unsupported command.type", self.cloud.ack_posts[0]["message"])

    def test_poll_acks_malformed_payload_when_id_is_present(self):
        self.cloud.commands.append({
            "id": "cmd-bad-payload",
            "type": "collect",
            "payload": "raw cmd_vel must not pass",
        })

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.cloud.ack_posts[0]["command_id"], "cmd-bad-payload")
        self.assertEqual(self.cloud.ack_posts[0]["state"], "failed")
        self.assertIn("malformed command", self.cloud.ack_posts[0]["message"])

    def test_expired_command_is_ignored_without_backend_submission(self):
        self.cloud.commands.append({
            "id": "cmd-expired",
            "type": "collect",
            "expires_at": time.time() - 1,
            "payload": {"target": "trash_station"},
        })

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.cloud.ack_posts[0]["command_id"], "cmd-expired")
        self.assertEqual(self.cloud.ack_posts[0]["state"], "ignored")
        self.assertIn("expired", self.cloud.ack_posts[0]["message"])

    def test_duplicate_command_reuses_cached_ack_without_resubmitting_action(self):
        command = {
            "id": "cmd-duplicate",
            "type": "collect",
            "payload": {"target": "trash_station"},
        }
        self.cloud.commands.append(command)
        self.assertTrue(self.worker.poll_once())

        self.cloud.commands.append(command)
        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
        self.assertEqual([ack["command_id"] for ack in self.cloud.ack_posts], ["cmd-duplicate", "cmd-duplicate"])
        self.assertEqual([ack["state"] for ack in self.cloud.ack_posts], ["acked", "acked"])

    def test_busy_collect_is_ignored_not_failed(self):
        busy_backend = FakeOperatorBackend(busy=True)
        worker = RemoteBridgeWorker(self.client, busy_backend, "robot-1")
        self.cloud.commands.append({
            "id": "cmd-busy",
            "type": "collect",
            "payload": {"target": "trash_station"},
        })

        self.assertTrue(worker.poll_once())

        self.assertEqual(busy_backend.calls, [("collect", "trash_station", 0)])
        self.assertEqual(self.cloud.ack_posts[0]["command_id"], "cmd-busy")
        self.assertEqual(self.cloud.ack_posts[0]["state"], "ignored")
        self.assertEqual(self.cloud.ack_posts[0]["result"]["http_status"], 409)

    def test_last_ack_id_and_bearer_token_are_used_for_outbound_polling(self):
        client = RemoteCloudClient(self.cloud.base_url, "robot-1", token="secret-token", timeout_sec=2.0)
        worker = RemoteBridgeWorker(client, self.backend, "robot-1", last_ack_id="cmd-old")

        self.assertFalse(worker.poll_once())

        self.assertIn("last_ack_id=cmd-old", self.cloud.get_paths[0])
        self.assertIn("Bearer secret-token", self.cloud.auth_headers)

    def test_cursor_state_path_restores_last_terminal_ack_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            state_path.write_text(
                json.dumps({
                    "robot_id": "robot-1",
                    "last_terminal_ack_id": "cmd-restored",
                    "updated_at": time.time(),
                }),
                encoding="utf-8",
            )
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                last_ack_id="cmd-fallback",
                cursor_state_path=state_path,
            )

            self.assertFalse(worker.poll_once())

            self.assertEqual(worker.last_ack_id, "cmd-restored")
            self.assertIn("last_ack_id=cmd-restored", self.cloud.get_paths[-1])

    def test_terminal_ack_persists_cursor_without_sensitive_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                cursor_state_path=state_path,
            )
            self.cloud.commands.append({
                "id": "cmd-persisted",
                "type": "collect",
                "payload": {"target": "trash_station"},
            })

            self.assertTrue(worker.poll_once())

            payload = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["last_terminal_ack_id"], "cmd-persisted")
            self.assertEqual(payload["robot_id"], "robot-1")
            self.assertIn("updated_at", payload)
            self.assertNotIn("token", json.dumps(payload).lower())
            self.assertNotIn("secret", json.dumps(payload).lower())

    def test_status_cloud_outage_does_not_poll_command_or_advance_cursor(self):
        self.cloud.commands.append({
            "id": "cmd-outage",
            "type": "collect",
            "payload": {"target": "trash_station"},
        })
        self.cloud.fail_status_count = 1

        handled = self.worker.poll_once()

        self.assertFalse(handled)
        self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.cloud.ack_posts, [])
        self.assertEqual(self.worker.last_ack_id, "")
        self.assertEqual(self.cloud.get_paths, [])
        self.assertEqual(self.backend.last_status["degradation_state"], "cloud_unreachable")
        self.assertEqual(self.backend.last_status["retry_hint"], "retry_cloud")
        self.assertFalse(self.backend.last_status["remote_ready"])

    def test_malformed_status_response_does_not_poll_command_or_advance_cursor(self):
        self.cloud.commands.append({
            "id": "cmd-bad-status-response",
            "type": "collect",
            "payload": {"target": "trash_station"},
        })
        self.cloud.malformed_status_count = 1

        handled = self.worker.poll_once()

        self.assertFalse(handled)
        self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.cloud.ack_posts, [])
        self.assertEqual(self.worker.last_ack_id, "")
        self.assertEqual(self.cloud.get_paths, [])
        self.assertEqual(self.backend.last_status["degradation_state"], "malformed_response")
        self.assertEqual(self.backend.last_status["retry_hint"], "contact_support")
        self.assertFalse(self.backend.last_status["remote_ready"])

    def test_auth_failed_get_posts_phone_safe_status_without_cursor_advance(self):
        self.cloud.commands.append({
            "id": "cmd-auth",
            "type": "collect",
            "payload": {"target": "trash_station"},
        })
        self.cloud.auth_fail_get_count = 1

        handled = self.worker.poll_once()

        self.assertFalse(handled)
        self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.cloud.ack_posts, [])
        self.assertEqual(self.worker.last_ack_id, "")
        self.assertEqual(self.backend.last_status["auth_state"], "auth_failed")
        self.assertEqual(self.backend.last_status["degradation_state"], "auth_failed")
        self.assertEqual(self.backend.last_status["retry_hint"], "check_auth")
        self.assertNotIn("Authorization", json.dumps(self.backend.last_status))
        self.assertNotIn("Bearer", json.dumps(self.backend.last_status))
        self.assertEqual(self.cloud.status_posts[-1]["degradation_state"], "auth_failed")

    def test_malformed_cloud_response_does_not_start_action_or_advance_cursor(self):
        self.cloud.commands.append({
            "id": "cmd-malformed",
            "type": "collect",
            "payload": {"target": "trash_station"},
        })
        self.cloud.malformed_get_count = 1

        handled = self.worker.poll_once()

        self.assertFalse(handled)
        self.assertEqual(self.backend.calls, [])
        self.assertEqual(self.cloud.ack_posts, [])
        self.assertEqual(self.worker.last_ack_id, "")
        self.assertEqual(self.backend.last_status["degradation_state"], "malformed_response")
        self.assertEqual(self.backend.last_status["retry_hint"], "contact_support")
        self.assertTrue(self.backend.last_status["cloud_reachable"])
        self.assertNotIn("/cmd_vel", json.dumps(self.backend.last_status))

    def test_command_cloud_outage_with_credential_metadata_does_not_start_or_advance_cursor(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                last_ack_id="cmd-before-outage",
                cursor_state_path=state_path,
            )
            self.cloud.commands.append({
                "id": "cmd-hidden-by-outage",
                "type": "collect",
                "payload": {"target": "trash_station"},
            })
            self.cloud.fail_get_count = 1
            self.cloud.response_extras["command_response"] = {
                "credential_rotation": {"status": "passed"},
                "preflight": {"production_ready": True},
                "diagnostics": {"delivery_success": True},
            }

            handled = worker.poll_once()

            self.assertFalse(handled)
            self.assertEqual(self.backend.calls, [])
            self.assertEqual(self.cloud.ack_posts, [])
            self.assertEqual(worker.last_ack_id, "cmd-before-outage")
            self.assertFalse(state_path.exists())
            self.assertEqual(self.backend.last_status["degradation_state"], "cloud_unreachable")

    def test_credential_rotation_fields_are_ignored_by_command_status_ack_envelope(self):
        self.cloud.response_extras.update({
            "status_response": {
                "credential_rotation": {"status": "passed"},
                "preflight": {"production_ready": True},
            },
            "command_response": {
                "credential_rotation": {"status": "passed"},
                "artifact": {"evidence_boundary": "software_proof_docker_credential_rotation_gate"},
            },
            "ack_response": {
                "delivery_success": True,
                "diagnostics": {"final_state": "DELIVERED"},
            },
        })
        self.cloud.commands.append({
            "id": "cmd-credential-extra",
            "type": "collect",
            "payload": {"target": "trash_station"},
        })

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
        self.assertEqual(self.worker.last_ack_id, "cmd-credential-extra")
        self.assertEqual(self.cloud.ack_posts[0]["state"], "acked")
        self.assertEqual(self.cloud.ack_posts[0]["message"], "collect")
        self.assertNotIn("delivery_success", json.dumps(self.cloud.ack_posts[0]))
        self.assertNotIn("credential_rotation", json.dumps(self.cloud.ack_posts[0]))
        self.assertEqual(self.cloud.status_posts[-1]["state"], "loaded_and_ready")
        self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_provisioning_sts_audit_fields_are_ignored_by_command_status_ack_envelope(self):
        self.cloud.response_extras.update({
            "status_response": {
                "provisioning": {"status": "passed", "robot_id": "robot-1"},
                "sts": {"status": "issued", "not_proven": True},
                "audit": {"status": "recorded", "delivery_success": True},
            },
            "command_response": {
                "provisioning": {"status": "passed", "raw_action": "collect"},
                "sts": {"status": "issued", "credential_url": "must-not-be-used"},
                "audit": {"status": "recorded", "next_action": "confirm_dropoff"},
            },
            "ack_response": {
                "provisioning": {"status": "passed"},
                "sts": {"status": "issued"},
                "audit": {"status": "recorded", "delivery_success": True},
            },
        })
        self.cloud.commands.append({
            "id": "cmd-provisioning-extra",
            "type": "collect",
            "payload": {"target": "trash_station"},
        })

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
        self.assertEqual(self.worker.last_ack_id, "cmd-provisioning-extra")
        ack_payload = self.cloud.ack_posts[0]
        self.assertEqual(ack_payload["command_id"], "cmd-provisioning-extra")
        self.assertEqual(ack_payload["state"], "acked")
        self.assertNotIn("provisioning", ack_payload)
        self.assertNotIn("sts", ack_payload)
        self.assertNotIn("audit", ack_payload)
        self.assertNotIn("credential_url", json.dumps(ack_payload["result"]))
        self.assertNotIn("delivery_success", json.dumps(ack_payload["result"]))
        self.assertEqual(self.cloud.status_posts[-1]["state"], "loaded_and_ready")
        self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_production_store_queue_fields_are_ignored_by_command_status_ack_envelope(self):
        self.cloud.response_extras.update({
            "status_response": {
                "production_store_queue": {
                    "state": "ready",
                    "production_ready": False,
                    "overall_status": "blocked",
                },
            },
            "command_response": {
                "production_store_queue": {
                    "state": "ready",
                    "queue_contract_status": "local_queue_contract_artifact_present",
                    "next_action": "confirm_dropoff",
                },
                "preflight": {"production_ready": False, "overall_status": "blocked"},
            },
            "ack_response": {
                "production_store_queue": {"state": "ready"},
                "delivery_success": True,
                "diagnostics": {"final_state": "DELIVERED"},
            },
        })
        self.cloud.commands.append({
            "id": "cmd-production-store-queue-extra",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
        })

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
        self.assertEqual(self.worker.last_ack_id, "cmd-production-store-queue-extra")
        ack_payload = self.cloud.ack_posts[0]
        self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
        self.assertEqual(ack_payload["command_id"], "cmd-production-store-queue-extra")
        self.assertEqual(ack_payload["state"], "acked")
        # production store/queue 只是云端 preflight/status 诊断元数据，不能污染 robot ACK envelope。
        self.assertNotIn("production_store_queue", ack_payload)
        self.assertNotIn("production_store_queue", json.dumps(ack_payload["result"]))
        self.assertNotIn("queue_contract_status", json.dumps(ack_payload["result"]))
        self.assertNotIn("delivery_success", json.dumps(ack_payload["result"]))
        self.assertEqual(self.cloud.status_posts[-1]["state"], "loaded_and_ready")
        self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_queue_ordering_fields_are_ignored_by_command_status_ack_envelope(self):
        self.cloud.response_extras.update({
            "status_response": {
                "queue_ordering_drill": {
                    "schema": "trashbot.queue_ordering_drill",
                    "status": "ready",
                    "delivery_success": True,
                },
            },
            "command_response": {
                "queue_ordering_drill": {
                    "schema": "trashbot.queue_ordering_drill",
                    "status": "ready",
                    "ordering_status": "cmd_9_before_cmd_10_verified",
                    "next_action": "confirm_dropoff",
                    "delivery_success": True,
                },
                "preflight": {"overall_status": "blocked", "production_ready": False},
            },
            "ack_response": {
                "queue_ordering_drill": {
                    "schema": "trashbot.queue_ordering_drill",
                    "delivery_success": True,
                    "final_state": "DELIVERED",
                },
            },
        })
        self.cloud.commands.append({
            "id": "cmd-queue-ordering-extra",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
        })

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
        self.assertEqual(self.worker.last_ack_id, "cmd-queue-ordering-extra")
        ack_payload = self.cloud.ack_posts[0]
        self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
        self.assertEqual(ack_payload["command_id"], "cmd-queue-ordering-extra")
        self.assertEqual(ack_payload["state"], "acked")
        # queue ordering drill 只是云端/手机诊断元数据，ACK 不能变成送达成功或队列证明。
        self.assertNotIn("queue_ordering_drill", ack_payload)
        self.assertNotIn("queue_ordering_drill", json.dumps(ack_payload["result"]))
        self.assertNotIn("ordering_status", json.dumps(ack_payload["result"]))
        self.assertNotIn("delivery_success", json.dumps(ack_payload["result"]))
        self.assertEqual(self.cloud.status_posts[-1]["state"], "loaded_and_ready")
        self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_queue_ordering_metadata_does_not_force_robot_side_string_sorting(self):
        self.cloud.response_extras["command_response"] = {
            "queue_ordering_drill": {
                "schema": "trashbot.queue_ordering_drill",
                "status": "ready",
                "ordering_status": "server_supplied_order_only",
                "candidate_command_ids": ["cmd-9", "cmd-10"],
            },
        }
        self.cloud.commands.extend([
            {
                "id": "cmd-10",
                "type": "collect",
                "payload": {"target": "trash_station", "trash_type": 10},
            },
            {
                "id": "cmd-9",
                "type": "collect",
                "payload": {"target": "trash_station", "trash_type": 9},
            },
        ])

        self.assertTrue(self.worker.poll_once())
        self.assertTrue(self.worker.poll_once())

        # robot bridge 只消费 relay 给出的下一条 command envelope，不按字符串重排 command id。
        self.assertEqual(self.backend.calls, [
            ("collect", "trash_station", 10),
            ("collect", "trash_station", 9),
        ])
        self.assertEqual([ack["command_id"] for ack in self.cloud.ack_posts], ["cmd-10", "cmd-9"])
        self.assertIn("last_ack_id=cmd-10", self.cloud.get_paths[1])
        self.assertEqual(self.worker.last_ack_id, "cmd-9")

    def test_cloud_db_queue_config_metadata_only_response_does_not_move_robot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                last_ack_id="cmd-before-db-queue-config",
                cursor_state_path=state_path,
            )
            self.cloud.response_extras["command_response"] = {
                "cloud_db_queue_config": {
                    "schema": "trashbot.cloud_db_queue_config.v1",
                    "overall_status": "blocked",
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-config-override",
                    "delivery_success": True,
                    "db_url": "postgres://user:secret@example.invalid/db",
                    "queue_url": "amqp://user:secret@example.invalid/q",
                },
                "cloud_db_queue_config_gate": {
                    "schema": "trashbot.cloud_db_queue_config_gate.v1",
                    "evidence_boundary": "software_proof_docker_cloud_db_queue_config_gate",
                    "production_ready": False,
                    "next_action": "confirm_dropoff",
                },
                "db_queue_config": {
                    "schema": "trashbot.db_queue_config.v1",
                    "raw_ros_topic": "/cmd_vel",
                    "Authorization": "Bearer must-not-leak",
                },
            }

            handled = worker.poll_once()

            self.assertFalse(handled)
            self.assertEqual(self.backend.calls, [])
            self.assertEqual(self.cloud.ack_posts, [])
            self.assertEqual(worker.last_ack_id, "cmd-before-db-queue-config")
            self.assertFalse(state_path.exists())
            self.assertIn("last_ack_id=cmd-before-db-queue-config", self.cloud.get_paths[-1])
            encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
            # DB/queue config gate 是云 readiness 元数据；没有 command envelope 时不能触发动作或 ACK。
            self.assertNotIn("cloud_db_queue_config", encoded_status)
            self.assertNotIn("cloud_db_queue_config_gate", encoded_status)
            self.assertNotIn("db_queue_config", encoded_status)
            self.assertNotIn("trigger_robot_action", encoded_status)
            self.assertNotIn("cursor_override", encoded_status)
            self.assertNotIn("delivery_success", encoded_status)
            self.assertNotIn("postgres://", encoded_status)
            self.assertNotIn("amqp://", encoded_status)
            self.assertNotIn("/cmd_vel", encoded_status)
            self.assertNotIn("Authorization", encoded_status)

    def test_cloud_db_queue_config_fields_are_ignored_by_command_status_ack_envelope(self):
        self.cloud.response_extras.update({
            "status_response": {
                "cloud_db_queue_config": {
                    "schema": "trashbot.cloud_db_queue_config.v1",
                    "overall_status": "blocked",
                    "delivery_success": True,
                },
            },
            "command_response": {
                "cloud_db_queue_config_gate": {
                    "schema": "trashbot.cloud_db_queue_config_gate.v1",
                    "production_ready": False,
                    "next_action": "cancel",
                    "cursor_override": "cmd-future",
                },
                "db_queue_config": {
                    "schema": "trashbot.db_queue_config.v1",
                    "queue_contract_status": "configured_in_cloud_only",
                    "trigger_robot_action": "confirm_dropoff",
                },
            },
            "ack_response": {
                "cloud_db_queue_config": {
                    "schema": "trashbot.cloud_db_queue_config.v1",
                    "delivery_success": True,
                    "final_state": "DELIVERED",
                },
                "db_queue_config": {"queue_ready": True},
            },
        })
        self.cloud.commands.append({
            "id": "cmd-db-queue-config-extra",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
        })

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
        self.assertEqual(self.worker.last_ack_id, "cmd-db-queue-config-extra")
        ack_payload = self.cloud.ack_posts[0]
        self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
        self.assertEqual(ack_payload["command_id"], "cmd-db-queue-config-extra")
        self.assertEqual(ack_payload["state"], "acked")
        encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
        # ACK 只回传本地 command 处理结果，不能带回 DB/queue readiness 证明或送达语义。
        self.assertNotIn("cloud_db_queue_config", encoded_ack)
        self.assertNotIn("cloud_db_queue_config_gate", encoded_ack)
        self.assertNotIn("db_queue_config", encoded_ack)
        self.assertNotIn("queue_contract_status", encoded_ack)
        self.assertNotIn("trigger_robot_action", encoded_ack)
        self.assertNotIn("cursor_override", encoded_ack)
        self.assertNotIn("delivery_success", encoded_ack)
        self.assertNotIn("DELIVERED", encoded_ack)
        encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
        self.assertNotIn("cloud_db_queue_config", encoded_status)
        self.assertNotIn("db_queue_config", encoded_status)
        self.assertNotIn("delivery_success", encoded_status)
        self.assertEqual(self.cloud.status_posts[-1]["state"], "loaded_and_ready")
        self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_cloud_db_queue_external_probe_fields_are_ignored_by_command_status_ack_envelope(self):
        self.cloud.response_extras.update({
            "status_response": {
                "cloud_db_queue_external_probe": {
                    "schema": "trashbot.cloud_db_queue_external_probe.v1",
                    "overall_status": "blocked",
                    "production_ready": False,
                    "delivery_success": True,
                },
            },
            "command_response": {
                "cloud_db_queue_external_probe_bundle": {
                    "schema": "trashbot.cloud_db_queue_external_probe_bundle",
                    "evidence_boundary": "software_proof_docker_cloud_db_queue_external_probe_gate",
                    "production_ready": False,
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-future",
                },
                "db_queue_external_probe": {
                    "schema": "trashbot.db_queue_external_probe.v1",
                    "external_probe_status": "not_proven",
                    "next_action": "confirm_dropoff",
                },
            },
            "ack_response": {
                "cloud_db_queue_external_probe": {
                    "schema": "trashbot.cloud_db_queue_external_probe.v1",
                    "delivery_success": True,
                    "final_state": "DELIVERED",
                },
                "db_queue_external_probe": {"queue_probe_ready": True},
            },
        })
        self.cloud.commands.append({
            "id": "cmd-db-queue-external-probe-extra",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
        })

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
        self.assertEqual(self.worker.last_ack_id, "cmd-db-queue-external-probe-extra")
        ack_payload = self.cloud.ack_posts[0]
        self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
        self.assertEqual(ack_payload["command_id"], "cmd-db-queue-external-probe-extra")
        self.assertEqual(ack_payload["state"], "acked")
        encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
        # ACK 只表达本地 command envelope 处理结果，不能夹带 DB/queue 外部探测或送达语义。
        self.assertNotIn("cloud_db_queue_external_probe", encoded_ack)
        self.assertNotIn("cloud_db_queue_external_probe_bundle", encoded_ack)
        self.assertNotIn("db_queue_external_probe", encoded_ack)
        self.assertNotIn("external_probe_status", encoded_ack)
        self.assertNotIn("trigger_robot_action", encoded_ack)
        self.assertNotIn("cursor_override", encoded_ack)
        self.assertNotIn("delivery_success", encoded_ack)
        self.assertNotIn("DELIVERED", encoded_ack)
        encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
        self.assertNotIn("cloud_db_queue_external_probe", encoded_status)
        self.assertNotIn("cloud_db_queue_external_probe_bundle", encoded_status)
        self.assertNotIn("db_queue_external_probe", encoded_status)
        self.assertNotIn("delivery_success", encoded_status)
        self.assertEqual(self.cloud.status_posts[-1]["state"], "loaded_and_ready")
        self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_oss_cdn_live_probe_fields_are_ignored_by_command_status_ack_envelope(self):
        self.cloud.response_extras.update({
            "status_response": {
                "oss_cdn_live_probe": {
                    "schema": "trashbot.oss_cdn_live_probe.v1",
                    "overall_status": "blocked",
                    "production_ready": False,
                    "delivery_success": True,
                },
            },
            "command_response": {
                "oss_cdn_live_probe_artifact": {
                    "schema": "trashbot.oss_cdn_live_probe_artifact.v1",
                    "evidence_boundary": "software_proof_docker_oss_cdn_live_probe_gate",
                    "live_probe_complete": False,
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-future",
                    "credential_url": "https://user:secret@cdn.example.invalid/rober/private",
                },
                "cdn_live_probe": {
                    "schema": "trashbot.cdn_live_probe.v1",
                    "probe_status": "not_proven",
                    "next_action": "confirm_dropoff",
                    "raw_ros_topic": "/cmd_vel",
                },
            },
            "ack_response": {
                "oss_cdn_live_probe": {
                    "schema": "trashbot.oss_cdn_live_probe.v1",
                    "delivery_success": True,
                    "final_state": "DELIVERED",
                },
                "cdn_live_probe": {"probe_status": "ready"},
            },
        })
        self.cloud.commands.append({
            "id": "cmd-oss-cdn-live-probe-extra",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
        })

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
        self.assertEqual(self.worker.last_ack_id, "cmd-oss-cdn-live-probe-extra")
        ack_payload = self.cloud.ack_posts[0]
        self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
        self.assertEqual(ack_payload["command_id"], "cmd-oss-cdn-live-probe-extra")
        self.assertEqual(ack_payload["state"], "acked")
        encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
        # ACK 只表达 command envelope 处理结果，不能夹带 OSS/CDN live probe 或送达语义。
        self.assertNotIn("oss_cdn_live_probe", encoded_ack)
        self.assertNotIn("oss_cdn_live_probe_artifact", encoded_ack)
        self.assertNotIn("cdn_live_probe", encoded_ack)
        self.assertNotIn("trigger_robot_action", encoded_ack)
        self.assertNotIn("cursor_override", encoded_ack)
        self.assertNotIn("delivery_success", encoded_ack)
        self.assertNotIn("credential_url", encoded_ack)
        self.assertNotIn("/cmd_vel", encoded_ack)
        self.assertNotIn("DELIVERED", encoded_ack)
        encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
        self.assertNotIn("oss_cdn_live_probe", encoded_status)
        self.assertNotIn("oss_cdn_live_probe_artifact", encoded_status)
        self.assertNotIn("cdn_live_probe", encoded_status)
        self.assertNotIn("delivery_success", encoded_status)
        self.assertEqual(self.cloud.status_posts[-1]["state"], "loaded_and_ready")
        self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_external_evidence_intake_fields_are_ignored_by_command_status_ack_envelope(self):
        self.cloud.response_extras.update({
            "status_response": {
                "external_evidence_intake": {
                    "schema": "trashbot.external_evidence_intake.v1",
                    "overall_status": "blocked",
                    "production_ready": False,
                    "delivery_success": True,
                },
            },
            "command_response": {
                "external_evidence_intake_artifact": {
                    "schema": "trashbot.external_evidence_intake_artifact.v1",
                    "evidence_boundary": "software_proof_docker_external_evidence_intake_gate",
                    "external_evidence_complete": False,
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-future",
                    "credential_url": "https://user:secret@example.invalid/proof",
                },
                "cloud_external_evidence": {
                    "schema": "trashbot.cloud_external_evidence.v1",
                    "public_ingress_tls": "not_proven",
                    "oss_cdn": "not_proven",
                    "production_db_queue": "not_proven",
                    "four_g_sim": "not_proven",
                    "next_action": "confirm_dropoff",
                    "raw_ros_topic": "/cmd_vel",
                },
            },
            "ack_response": {
                "external_evidence_intake": {
                    "schema": "trashbot.external_evidence_intake.v1",
                    "ack_semantics": "delivery_success",
                    "delivery_success": True,
                    "final_state": "DELIVERED",
                },
            },
        })
        self.cloud.commands.append({
            "id": "cmd-external-evidence-intake-extra",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
        })

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
        self.assertEqual(self.worker.last_ack_id, "cmd-external-evidence-intake-extra")
        ack_payload = self.cloud.ack_posts[0]
        self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
        self.assertEqual(ack_payload["command_id"], "cmd-external-evidence-intake-extra")
        self.assertEqual(ack_payload["state"], "acked")
        encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
        # external evidence intake 只是云 readiness proof，ACK 只能表达 command envelope 的本地处理结果。
        self.assertNotIn("external_evidence_intake", encoded_ack)
        self.assertNotIn("external_evidence_intake_artifact", encoded_ack)
        self.assertNotIn("cloud_external_evidence", encoded_ack)
        self.assertNotIn("trigger_robot_action", encoded_ack)
        self.assertNotIn("cursor_override", encoded_ack)
        self.assertNotIn("delivery_success", encoded_ack)
        self.assertNotIn("DELIVERED", encoded_ack)
        self.assertNotIn("credential_url", encoded_ack)
        self.assertNotIn("/cmd_vel", encoded_ack)
        encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
        self.assertNotIn("external_evidence_intake", encoded_status)
        self.assertNotIn("external_evidence_intake_artifact", encoded_status)
        self.assertNotIn("cloud_external_evidence", encoded_status)
        self.assertNotIn("delivery_success", encoded_status)
        self.assertEqual(self.cloud.status_posts[-1]["state"], "loaded_and_ready")
        self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_cloud_readiness_summary_metadata_only_response_does_not_move_robot(self):
        metadata_cases = (
            (
                "phone_cloud_readiness_summary",
                {
                    "schema": "trashbot.phone_cloud_readiness_summary.v1",
                    "overall_status": "blocked",
                    "safe_phone_copy": "云端配置还未完成，先保持本地等待。",
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-summary-override",
                    "delivery_success": True,
                    "credential_url": "https://user:secret@example.invalid/creds",
                },
            ),
            (
                "mobile_cloud_readiness_summary",
                {
                    "schema": "trashbot.mobile_cloud_readiness_summary.v1",
                    "production_ready": True,
                    "next_action": "confirm_dropoff",
                    "cursor_override": "cmd-summary-override",
                    "delivery_success": True,
                    "cloud_url": "https://token@example.invalid/mobile",
                },
            ),
            (
                "cloud_readiness_summary",
                {
                    "schema": "trashbot.cloud_readiness_summary.v1",
                    "production_ready": False,
                    "trigger_robot_action": "cancel",
                    "delivery_success": True,
                    "Authorization": "Bearer must-not-leak",
                },
            ),
        )
        for metadata_name, metadata in metadata_cases:
            with self.subTest(metadata_name=metadata_name):
                self.cloud.status_posts.clear()
                self.cloud.ack_posts.clear()
                self.backend.calls.clear()
                with tempfile.TemporaryDirectory() as tmpdir:
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-{metadata_name}",
                        cursor_state_path=state_path,
                    )
                    self.cloud.response_extras["command_response"] = {
                        metadata_name: metadata,
                        "preflight": {"overall_status": "blocked", "production_ready": False},
                    }

                    handled = worker.poll_once()

                    # readiness summary 是手机/支持摘要；没有 command envelope 时不能驱动 robot 侧副作用。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-{metadata_name}")
                    self.assertFalse(state_path.exists())
                    self.assertIn(f"last_ack_id=cmd-before-{metadata_name}", self.cloud.get_paths[-1])
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn(metadata_name, encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)
                    self.assertNotIn("credential_url", encoded_status)
                    self.assertNotIn("cloud_url", encoded_status)
                    self.assertNotIn("Authorization", encoded_status)
                    self.cloud.response_extras["command_response"] = {}

    def test_cloud_readiness_summary_fields_are_ignored_by_command_status_ack_envelope(self):
        self.cloud.response_extras.update({
            "status_response": {
                "phone_cloud_readiness_summary": {
                    "schema": "trashbot.phone_cloud_readiness_summary.v1",
                    "overall_status": "blocked",
                    "delivery_success": True,
                },
            },
            "command_response": {
                "mobile_cloud_readiness_summary": {
                    "schema": "trashbot.mobile_cloud_readiness_summary.v1",
                    "production_ready": False,
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-future",
                    "cloud_url": "https://token@example.invalid/mobile",
                },
                "cloud_readiness_summary": {
                    "schema": "trashbot.cloud_readiness_summary.v1",
                    "next_action": "confirm_dropoff",
                    "delivery_success": True,
                    "credential_url": "https://user:secret@example.invalid/creds",
                },
            },
            "ack_response": {
                "cloud_readiness_summary": {
                    "schema": "trashbot.cloud_readiness_summary.v1",
                    "ack_semantics": "delivery_success",
                    "delivery_success": True,
                    "final_state": "DELIVERED",
                },
            },
        })
        self.cloud.commands.append({
            "id": "cmd-cloud-readiness-summary-extra",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
        })

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
        self.assertEqual(self.worker.last_ack_id, "cmd-cloud-readiness-summary-extra")
        ack_payload = self.cloud.ack_posts[0]
        self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
        self.assertEqual(ack_payload["command_id"], "cmd-cloud-readiness-summary-extra")
        self.assertEqual(ack_payload["state"], "acked")
        encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
        # ACK 只能表达 command envelope 被本地处理，不能吸收手机云 readiness 或送达语义。
        self.assertNotIn("phone_cloud_readiness_summary", encoded_ack)
        self.assertNotIn("mobile_cloud_readiness_summary", encoded_ack)
        self.assertNotIn("cloud_readiness_summary", encoded_ack)
        self.assertNotIn("trigger_robot_action", encoded_ack)
        self.assertNotIn("cursor_override", encoded_ack)
        self.assertNotIn("delivery_success", encoded_ack)
        self.assertNotIn("DELIVERED", encoded_ack)
        encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
        self.assertNotIn("phone_cloud_readiness_summary", encoded_status)
        self.assertNotIn("mobile_cloud_readiness_summary", encoded_status)
        self.assertNotIn("cloud_readiness_summary", encoded_status)
        self.assertNotIn("delivery_success", encoded_status)
        self.assertNotIn("https://token@", encoded_status)
        self.assertNotIn("https://user:secret@", encoded_status)
        self.assertEqual(self.cloud.status_posts[-1]["state"], "loaded_and_ready")
        self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_phone_task_flow_fields_are_ignored_by_command_status_ack_envelope(self):
        self.cloud.response_extras.update({
            "status_response": {
                "phone_task_flow_readiness": {
                    "schema": "trashbot.phone_task_flow_readiness.v1",
                    "current_step": "start_delivery",
                    "delivery_success": True,
                },
            },
            "command_response": {
                "phone_task_flow_readiness": {
                    "schema": "trashbot.phone_task_flow_readiness.v1",
                    "next_action": "confirm_dropoff",
                    "trigger_robot_action": "cancel",
                },
            },
            "ack_response": {
                "phone_task_flow_readiness": {
                    "schema": "trashbot.phone_task_flow_readiness.v1",
                    "delivery_success": True,
                    "final_state": "DELIVERED",
                },
            },
        })
        self.cloud.commands.append({
            "id": "cmd-phone-task-flow-extra",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
        })

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
        self.assertEqual(self.worker.last_ack_id, "cmd-phone-task-flow-extra")
        ack_payload = self.cloud.ack_posts[0]
        self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
        self.assertEqual(ack_payload["command_id"], "cmd-phone-task-flow-extra")
        self.assertEqual(ack_payload["state"], "acked")
        # phone task-flow 是手机/诊断元数据，robot ACK envelope 只能回传本地命令处理结果。
        self.assertNotIn("phone_task_flow_readiness", ack_payload)
        self.assertNotIn("phone_task_flow_readiness", json.dumps(ack_payload["result"]))
        self.assertNotIn("trigger_robot_action", json.dumps(ack_payload["result"]))
        self.assertNotIn("delivery_success", json.dumps(ack_payload["result"]))
        self.assertEqual(self.cloud.status_posts[-1]["state"], "loaded_and_ready")
        self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_mobile_task_start_confirmation_metadata_only_response_does_not_move_robot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                last_ack_id="cmd-before-confirmation-metadata",
                cursor_state_path=state_path,
            )
            self.cloud.response_extras["command_response"] = {
                "mobile_task_start_confirmation": {
                    "schema": "trashbot.mobile_task_start_confirmation.v1",
                    "trash_loaded_confirmed": True,
                    "selected_destination": "trash_station",
                    "trigger_robot_action": "collect",
                    "delivery_success": True,
                },
                "mobile_task_start_confirmation_readiness": {
                    "schema": "trashbot.mobile_task_start_confirmation_readiness.v1",
                    "overall_status": "ready",
                    "ack_semantics": "delivery_success",
                    "cursor_override": "cmd-confirmed",
                },
                "task_start_confirmation_payload": {
                    "source": "mobile/web",
                    "target": "trash_station",
                    "trash_loaded_confirmed": True,
                    "raw_ros_topic": "/trashbot/collect_trash",
                },
            }

            handled = worker.poll_once()

            self.assertFalse(handled)
            self.assertEqual(self.backend.calls, [])
            self.assertEqual(self.cloud.ack_posts, [])
            self.assertEqual(worker.last_ack_id, "cmd-before-confirmation-metadata")
            self.assertFalse(state_path.exists())
            self.assertIn("last_ack_id=cmd-before-confirmation-metadata", self.cloud.get_paths[-1])
            encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
            # 手机端确认字段只是 UI/API 层元数据；没有 command envelope 时不能触发 ACK 或游标推进。
            self.assertNotIn("mobile_task_start_confirmation", encoded_status)
            self.assertNotIn("task_start_confirmation_payload", encoded_status)
            self.assertNotIn("delivery_success", encoded_status)
            self.assertNotIn("/trashbot/collect_trash", encoded_status)

    def test_mobile_action_feedback_metadata_only_response_does_not_move_robot(self):
        metadata_cases = (
            (
                "mobile_action_confirmation",
                {
                    "schema": "trashbot.mobile_action_confirmation.v1",
                    "source": "mobile_web",
                    "action": "confirm_dropoff",
                    "user_confirmed": True,
                    "trigger_robot_action": "confirm_dropoff",
                    "cursor_override": "cmd-future",
                    "ack_semantics": "delivery_success",
                    "delivery_success": True,
                    "raw_ros_topic": "/trashbot/confirm_dropoff",
                },
            ),
            (
                "mobile_action_receipt",
                {
                    "schema": "trashbot.mobile_action_receipt.v1",
                    "action": "cancel",
                    "receipt_state": "accepted",
                    "next_action": "cancel",
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-future",
                    "delivery_success": True,
                    "serial_device": "/dev/ttyUSB0",
                },
            ),
            (
                "phone_action_feedback",
                {
                    "schema": "trashbot.phone_action_feedback.v1",
                    "safe_phone_copy": "命令已提交，等待机器人处理。",
                    "recovery_hint": "继续观察状态。",
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-future",
                    "ack_semantics": "delivery_success",
                    "delivery_success": True,
                    "raw_ros_topic": "/cmd_vel",
                },
            ),
        )
        for metadata_name, metadata in metadata_cases:
            with self.subTest(metadata_name=metadata_name):
                self.cloud.status_posts.clear()
                self.cloud.ack_posts.clear()
                self.backend.calls.clear()
                with tempfile.TemporaryDirectory() as tmpdir:
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-{metadata_name}",
                        cursor_state_path=state_path,
                    )
                    self.cloud.response_extras["command_response"] = {
                        metadata_name: metadata,
                        "preflight": {"overall_status": "blocked", "production_ready": False},
                    }

                    handled = worker.poll_once()

                    # 动作反馈是手机端回执/支持摘要；没有 command envelope 时不能触发机器人动作。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-{metadata_name}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    self.assertIn(f"last_ack_id=cmd-before-{metadata_name}", self.cloud.get_paths[-1])
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn(metadata_name, encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)
                    self.assertNotIn("/cmd_vel", encoded_status)
                    self.assertNotIn("/dev/ttyUSB0", encoded_status)
                    self.cloud.response_extras["command_response"] = {}

    def test_operation_log_fields_are_ignored_by_command_status_ack_envelope(self):
        self.cloud.response_extras.update({
            "status_response": {
                "operation_log": {
                    "schema": "trashbot.phone_operation_log.v1",
                    "latest_event": "pending_ack",
                    "delivery_success": True,
                },
            },
            "command_response": {
                "operation_log": {
                    "schema": "trashbot.phone_operation_log.v1",
                    "events": [{"kind": "blocked", "safe_phone_copy": "等待机器人状态。"}],
                    "trigger_robot_action": "confirm_dropoff",
                    "cursor_override": "cmd-future",
                    "ack_semantics": "delivery_success",
                    "delivery_success": True,
                },
                "phone_operation_log": {
                    "schema": "trashbot.phone_operation_log.v1",
                    "support_handoff": {"next_action": "cancel"},
                },
            },
            "ack_response": {
                "operation_log": {
                    "schema": "trashbot.phone_operation_log.v1",
                    "ack_semantics": "delivery_success",
                    "delivery_success": True,
                    "final_state": "DELIVERED",
                },
            },
        })
        self.cloud.commands.append({
            "id": "cmd-operation-log-extra",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
        })

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
        self.assertEqual(self.worker.last_ack_id, "cmd-operation-log-extra")
        ack_payload = self.cloud.ack_posts[0]
        self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
        self.assertEqual(ack_payload["command_id"], "cmd-operation-log-extra")
        self.assertEqual(ack_payload["state"], "acked")
        self.assertEqual(ack_payload["message"], "collect")
        encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
        # operation log 是手机/支持摘要，ACK 只能表达 command envelope 的本地处理结果。
        self.assertNotIn("operation_log", encoded_ack)
        self.assertNotIn("phone_operation_log", encoded_ack)
        self.assertNotIn("trigger_robot_action", encoded_ack)
        self.assertNotIn("cursor_override", encoded_ack)
        self.assertNotIn("delivery_success", encoded_ack)
        self.assertNotIn("DELIVERED", encoded_ack)
        encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
        self.assertNotIn("operation_log", encoded_status)
        self.assertNotIn("phone_operation_log", encoded_status)
        self.assertNotIn("delivery_success", encoded_status)
        self.assertEqual(self.cloud.status_posts[-1]["state"], "loaded_and_ready")
        self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_phone_offline_resume_fields_are_ignored_by_command_status_ack_envelope(self):
        self.cloud.response_extras.update({
            "status_response": {
                "phone_offline_resume_readiness": {
                    "schema": "trashbot.phone_offline_resume_readiness.v1",
                    "connection_state": "offline",
                    "can_resume": False,
                    "delivery_success": True,
                },
            },
            "command_response": {
                "phone_offline_resume_readiness": {
                    "schema": "trashbot.phone_offline_resume_readiness.v1",
                    "next_action": "confirm_dropoff",
                    "trigger_robot_action": "cancel",
                    "ack_semantics": "delivery_success",
                    "cursor_override": "cmd-future",
                    "delivery_success": True,
                },
            },
            "ack_response": {
                "phone_offline_resume_readiness": {
                    "schema": "trashbot.phone_offline_resume_readiness.v1",
                    "ack_semantics": "delivery_success",
                    "delivery_success": True,
                    "final_state": "DELIVERED",
                },
            },
        })
        self.cloud.commands.append({
            "id": "cmd-phone-offline-resume-extra",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
        })

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
        self.assertEqual(self.worker.last_ack_id, "cmd-phone-offline-resume-extra")
        ack_payload = self.cloud.ack_posts[0]
        self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
        self.assertEqual(ack_payload["command_id"], "cmd-phone-offline-resume-extra")
        self.assertEqual(ack_payload["state"], "acked")
        self.assertEqual(ack_payload["message"], "collect")
        encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
        # offline/resume readiness 是手机端恢复摘要，不能让 robot ACK 变成送达成功或游标控制。
        self.assertNotIn("phone_offline_resume_readiness", encoded_ack)
        self.assertNotIn("trigger_robot_action", encoded_ack)
        self.assertNotIn("cursor_override", encoded_ack)
        self.assertNotIn("delivery_success", encoded_ack)
        self.assertNotIn("DELIVERED", encoded_ack)
        encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
        self.assertNotIn("phone_offline_resume_readiness", encoded_status)
        self.assertNotIn("delivery_success", encoded_status)
        self.assertEqual(self.cloud.status_posts[-1]["state"], "loaded_and_ready")
        self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_phone_support_bundle_fields_are_ignored_by_command_status_ack_envelope(self):
        self.cloud.response_extras.update({
            "status_response": {
                "phone_support_bundle": {
                    "schema": "trashbot.phone_support_bundle.v1",
                    "support_level": "support_required",
                    "delivery_success": True,
                },
            },
            "command_response": {
                "phone_support_bundle": {
                    "schema": "trashbot.phone_support_bundle.v1",
                    "safe_copy": "支持摘要只能给手机端展示，不能触发机器人动作。",
                    "trigger_robot_action": "confirm_dropoff",
                    "next_action": "cancel",
                    "delivery_success": True,
                },
            },
            "ack_response": {
                "phone_support_bundle": {
                    "schema": "trashbot.phone_support_bundle.v1",
                    "ack_semantics": "delivery_success",
                    "delivery_success": True,
                    "final_state": "DELIVERED",
                },
            },
        })
        self.cloud.commands.append({
            "id": "cmd-phone-support-bundle-extra",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
        })

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
        self.assertEqual(self.worker.last_ack_id, "cmd-phone-support-bundle-extra")
        ack_payload = self.cloud.ack_posts[0]
        self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
        self.assertEqual(ack_payload["command_id"], "cmd-phone-support-bundle-extra")
        self.assertEqual(ack_payload["state"], "acked")
        self.assertEqual(ack_payload["message"], "collect")
        encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
        # support bundle 是手机支持元数据，robot ACK 只保留本地命令处理结果，不能升级为送达成功。
        self.assertNotIn("phone_support_bundle", encoded_ack)
        self.assertNotIn("trigger_robot_action", encoded_ack)
        self.assertNotIn("delivery_success", encoded_ack)
        self.assertNotIn("DELIVERED", encoded_ack)
        self.assertEqual(self.cloud.status_posts[-1]["state"], "loaded_and_ready")
        self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_mobile_browser_acceptance_bundle_fields_are_ignored_by_command_status_ack_envelope(self):
        self.cloud.response_extras.update({
            "status_response": {
                "mobile_browser_acceptance_bundle": {
                    "schema": "trashbot.mobile_browser_acceptance_bundle.v1",
                    "overall_status": "blocked",
                    "delivery_success": True,
                },
            },
            "command_response": {
                "phone_browser_acceptance_bundle": {
                    "schema": "trashbot.phone_browser_acceptance_bundle.v1",
                    "safe_phone_copy": "手机浏览器验收摘要只能给 UI/diagnostics 展示。",
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-future",
                    "ack_semantics": "delivery_success",
                    "delivery_success": True,
                },
                "mobile_acceptance_evidence_bundle": {
                    "schema": "trashbot.mobile_acceptance_evidence_bundle.v1",
                    "evidence_boundary": "software_proof_docker_mobile_browser_acceptance_bundle_gate",
                    "next_action": "confirm_dropoff",
                    "raw_ros_topic": "/cmd_vel",
                },
            },
            "ack_response": {
                "mobile_browser_acceptance_bundle": {
                    "schema": "trashbot.mobile_browser_acceptance_bundle.v1",
                    "ack_semantics": "delivery_success",
                    "delivery_success": True,
                    "final_state": "DELIVERED",
                },
            },
        })
        self.cloud.commands.append({
            "id": "cmd-mobile-browser-acceptance-bundle-extra",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
        })

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
        self.assertEqual(self.worker.last_ack_id, "cmd-mobile-browser-acceptance-bundle-extra")
        ack_payload = self.cloud.ack_posts[0]
        self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
        self.assertEqual(ack_payload["command_id"], "cmd-mobile-browser-acceptance-bundle-extra")
        self.assertEqual(ack_payload["state"], "acked")
        self.assertEqual(ack_payload["message"], "collect")
        encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
        # ACK 只表达 command envelope 被本地接收/处理，不能吸收手机浏览器验收 bundle。
        self.assertNotIn("mobile_browser_acceptance_bundle", encoded_ack)
        self.assertNotIn("phone_browser_acceptance_bundle", encoded_ack)
        self.assertNotIn("mobile_acceptance_evidence_bundle", encoded_ack)
        self.assertNotIn("trigger_robot_action", encoded_ack)
        self.assertNotIn("cursor_override", encoded_ack)
        self.assertNotIn("delivery_success", encoded_ack)
        self.assertNotIn("DELIVERED", encoded_ack)
        self.assertNotIn("/cmd_vel", encoded_ack)
        encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
        self.assertNotIn("mobile_browser_acceptance_bundle", encoded_status)
        self.assertNotIn("phone_browser_acceptance_bundle", encoded_status)
        self.assertNotIn("mobile_acceptance_evidence_bundle", encoded_status)
        self.assertNotIn("delivery_success", encoded_status)
        self.assertEqual(self.cloud.status_posts[-1]["state"], "loaded_and_ready")
        self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_mobile_web_browser_proof_fields_are_ignored_by_command_status_ack_envelope(self):
        self.cloud.response_extras.update({
            "status_response": {
                "mobile_web_browser_proof": {
                    "schema": "trashbot.mobile_web_browser_proof.v1",
                    "evidence_boundary": "software_proof_docker_mobile_web_browser_proof_gate",
                    "delivery_success": True,
                },
            },
            "command_response": {
                "phone_browser_proof": {
                    "schema": "trashbot.phone_browser_proof.v1",
                    "safe_phone_copy": "浏览器 proof 只说明本地页面证据，不能触发机器人动作。",
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-future",
                    "ack_semantics": "delivery_success",
                    "delivery_success": True,
                },
                "mobile_browser_proof_summary": {
                    "schema": "trashbot.mobile_browser_proof_summary.v1",
                    "evidence_boundary": "software_proof_docker_mobile_web_browser_proof_gate",
                    "next_action": "confirm_dropoff",
                    "raw_ros_topic": "/cmd_vel",
                },
            },
            "ack_response": {
                "mobile_web_browser_proof": {
                    "schema": "trashbot.mobile_web_browser_proof.v1",
                    "ack_semantics": "delivery_success",
                    "delivery_success": True,
                    "final_state": "DELIVERED",
                },
            },
        })
        self.cloud.commands.append({
            "id": "cmd-mobile-web-browser-proof-extra",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
        })

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
        self.assertEqual(self.worker.last_ack_id, "cmd-mobile-web-browser-proof-extra")
        ack_payload = self.cloud.ack_posts[0]
        self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
        self.assertEqual(ack_payload["command_id"], "cmd-mobile-web-browser-proof-extra")
        self.assertEqual(ack_payload["state"], "acked")
        self.assertEqual(ack_payload["message"], "collect")
        encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
        # browser proof 元数据不能污染 ACK；ACK 仍只是命令 accepted/processing 证据。
        self.assertNotIn("mobile_web_browser_proof", encoded_ack)
        self.assertNotIn("phone_browser_proof", encoded_ack)
        self.assertNotIn("mobile_browser_proof_summary", encoded_ack)
        self.assertNotIn("software_proof_docker_mobile_web_browser_proof_gate", encoded_ack)
        self.assertNotIn("trigger_robot_action", encoded_ack)
        self.assertNotIn("cursor_override", encoded_ack)
        self.assertNotIn("delivery_success", encoded_ack)
        self.assertNotIn("DELIVERED", encoded_ack)
        self.assertNotIn("/cmd_vel", encoded_ack)
        encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
        self.assertNotIn("mobile_web_browser_proof", encoded_status)
        self.assertNotIn("phone_browser_proof", encoded_status)
        self.assertNotIn("mobile_browser_proof_summary", encoded_status)
        self.assertNotIn("delivery_success", encoded_status)
        self.assertEqual(self.cloud.status_posts[-1]["state"], "loaded_and_ready")
        self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_mobile_current_pwa_browser_proof_refresh_metadata_only_response_does_not_move_robot(self):
        metadata_cases = (
            (
                "mobile_current_pwa_browser_proof_refresh",
                {
                    "schema": "trashbot.mobile_current_pwa_browser_proof_refresh.v1",
                    "evidence_boundary": "software_proof_docker_mobile_current_pwa_browser_proof_refresh_gate",
                    "viewport_results": {"390x844": "passed", "768x900": "passed"},
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-current-pwa-refresh",
                    "ack_semantics": "delivery_success",
                    "delivery_success": True,
                    "production_ready": True,
                    "hil_pass": True,
                    "raw_ros_topic": "/cmd_vel",
                },
            ),
            (
                "mobile_current_pwa_browser_proof_refresh_summary",
                {
                    "schema": "trashbot.mobile_current_pwa_browser_proof_refresh_summary.v1",
                    "safe_phone_copy": "本地 Chromium proof 只说明当前 PWA 首屏软件证据。",
                    "next_action": "confirm_dropoff",
                    "cursor_override": "cmd-current-pwa-summary",
                    "delivery_success": True,
                    "real_device_proof": True,
                },
            ),
            (
                "phone_current_pwa_browser_proof_refresh",
                {
                    "schema": "trashbot.phone_current_pwa_browser_proof_refresh.v1",
                    "evidence_boundary": "software_proof_docker_mobile_current_pwa_browser_proof_refresh_gate",
                    "safe_to_control": True,
                    "trigger_robot_action": "cancel",
                    "production_ready": True,
                    "Authorization": "Bearer must-not-leak",
                },
            ),
        )
        for metadata_name, metadata in metadata_cases:
            with self.subTest(metadata_name=metadata_name):
                self.cloud.status_posts.clear()
                self.cloud.ack_posts.clear()
                self.backend.calls.clear()
                self.cloud.response_extras["command_response"] = {
                    metadata_name: metadata,
                    "preflight": {"overall_status": "blocked", "production_ready": False},
                }
                with tempfile.TemporaryDirectory() as tmpdir:
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-{metadata_name}",
                        cursor_state_path=state_path,
                    )

                    handled = worker.poll_once()

                    # current PWA browser proof refresh 只是手机证据元数据；没有 command envelope 不能动机器人。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-{metadata_name}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    self.assertIn(f"last_ack_id=cmd-before-{metadata_name}", self.cloud.get_paths[-1])
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn(metadata_name, encoded_status)
                    self.assertNotIn("software_proof_docker_mobile_current_pwa_browser_proof_refresh_gate", encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)
                    self.assertNotIn("production_ready", encoded_status)
                    self.assertNotIn("hil_pass", encoded_status)
                    self.assertNotIn("/cmd_vel", encoded_status)
                    self.assertNotIn("Authorization", encoded_status)
                    self.cloud.response_extras["command_response"] = {}

    def test_mobile_current_pwa_browser_proof_refresh_fields_are_ignored_by_command_status_ack_envelope(self):
        self.cloud.response_extras.update({
            "status_response": {
                "mobile_current_pwa_browser_proof_refresh_summary": {
                    "schema": "trashbot.mobile_current_pwa_browser_proof_refresh_summary.v1",
                    "evidence_boundary": "software_proof_docker_mobile_current_pwa_browser_proof_refresh_gate",
                    "delivery_success": True,
                    "production_ready": True,
                },
            },
            "command_response": {
                "mobile_current_pwa_browser_proof_refresh": {
                    "schema": "trashbot.mobile_current_pwa_browser_proof_refresh.v1",
                    "evidence_boundary": "software_proof_docker_mobile_current_pwa_browser_proof_refresh_gate",
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-future",
                    "ack_semantics": "delivery_success",
                    "delivery_success": True,
                    "raw_ros_topic": "/cmd_vel",
                },
                "phone_current_pwa_browser_proof_refresh": {
                    "schema": "trashbot.phone_current_pwa_browser_proof_refresh.v1",
                    "safe_phone_copy": "ACK 只代表 accepted/processing，不代表送达成功。",
                    "next_action": "confirm_dropoff",
                    "production_ready": True,
                    "real_device_proof": True,
                    "hil_pass": True,
                },
            },
            "ack_response": {
                "mobile_current_pwa_browser_proof_refresh_summary": {
                    "schema": "trashbot.mobile_current_pwa_browser_proof_refresh_summary.v1",
                    "ack_semantics": "delivery_success",
                    "delivery_success": True,
                    "final_state": "DELIVERED",
                },
            },
        })
        self.cloud.commands.append({
            "id": "cmd-current-pwa-browser-proof-refresh-extra",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
            "mobile_current_pwa_browser_proof_refresh": {
                "trigger_robot_action": "cancel",
                "cursor_override": "cmd-future",
                "delivery_success": True,
            },
        })

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
        self.assertEqual(self.worker.last_ack_id, "cmd-current-pwa-browser-proof-refresh-extra")
        ack_payload = self.cloud.ack_posts[0]
        self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
        self.assertEqual(ack_payload["command_id"], "cmd-current-pwa-browser-proof-refresh-extra")
        self.assertEqual(ack_payload["state"], "acked")
        self.assertEqual(ack_payload["message"], "collect")
        encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
        # ACK 仍只描述 command envelope 的本地处理结果，不能吸收 current PWA 浏览器刷新 proof。
        self.assertNotIn("mobile_current_pwa_browser_proof_refresh", encoded_ack)
        self.assertNotIn("mobile_current_pwa_browser_proof_refresh_summary", encoded_ack)
        self.assertNotIn("phone_current_pwa_browser_proof_refresh", encoded_ack)
        self.assertNotIn("software_proof_docker_mobile_current_pwa_browser_proof_refresh_gate", encoded_ack)
        self.assertNotIn("trigger_robot_action", encoded_ack)
        self.assertNotIn("cursor_override", encoded_ack)
        self.assertNotIn("delivery_success", encoded_ack)
        self.assertNotIn("production_ready", encoded_ack)
        self.assertNotIn("real_device_proof", encoded_ack)
        self.assertNotIn("hil_pass", encoded_ack)
        self.assertNotIn("DELIVERED", encoded_ack)
        self.assertNotIn("/cmd_vel", encoded_ack)
        encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
        self.assertNotIn("mobile_current_pwa_browser_proof_refresh", encoded_status)
        self.assertNotIn("mobile_current_pwa_browser_proof_refresh_summary", encoded_status)
        self.assertNotIn("phone_current_pwa_browser_proof_refresh", encoded_status)
        self.assertNotIn("delivery_success", encoded_status)
        self.assertEqual(self.cloud.status_posts[-1]["state"], "loaded_and_ready")
        self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_mobile_current_pwa_retest_browser_proof_metadata_only_response_does_not_move_robot(self):
        metadata_cases = (
            (
                "mobile_current_pwa_retest_browser_proof",
                {
                    "schema": "trashbot.mobile_current_pwa_retest_browser_proof.v1",
                    "evidence_boundary": "software_proof_docker_mobile_current_pwa_retest_browser_proof_gate",
                    "viewport_results": {"390x844": "passed", "768x900": "passed"},
                    "retest_request_panel_visible": True,
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-current-pwa-retest",
                    "terminal_ack": "delivered",
                    "ack_semantics": "delivery_success",
                    "delivery_success": True,
                    "dropoff_success": True,
                    "cancel_completed": True,
                    "production_ready": True,
                    "hil_pass": True,
                    "raw_ros_topic": "/cmd_vel",
                },
            ),
            (
                "mobile_current_pwa_retest_browser_proof_summary",
                {
                    "schema": "trashbot.mobile_current_pwa_retest_browser_proof_summary.v1",
                    "safe_phone_copy": "当前 PWA retest browser proof 只供手机和支持侧复查。",
                    "next_action": "confirm_dropoff",
                    "cursor_override": "cmd-current-pwa-retest-summary",
                    "delivery_success": True,
                    "real_device_proof": True,
                    "ready_for_retest": True,
                    "production_ready": True,
                },
            ),
            (
                "phone_current_pwa_retest_browser_proof",
                {
                    "schema": "trashbot.phone_current_pwa_retest_browser_proof.v1",
                    "evidence_boundary": "software_proof_docker_mobile_current_pwa_retest_browser_proof_gate",
                    "safe_to_control": True,
                    "trigger_robot_action": "cancel",
                    "production_ready": True,
                    "Authorization": "Bearer must-not-leak",
                    "serial_device": "/dev/ttyUSB0",
                },
            ),
        )
        for metadata_name, metadata in metadata_cases:
            with self.subTest(metadata_name=metadata_name):
                self.cloud.status_posts.clear()
                self.cloud.ack_posts.clear()
                self.cloud.get_paths.clear()
                self.backend.calls.clear()
                self.cloud.response_extras["command_response"] = {metadata_name: metadata}
                with tempfile.TemporaryDirectory() as tmpdir:
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-{metadata_name}",
                        cursor_state_path=state_path,
                    )

                    handled = worker.poll_once()

                    # current PWA retest browser proof 只是浏览器证据元数据；没有 command envelope 不能动机器人。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-{metadata_name}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    self.assertEqual(self.cloud.status_posts[-1]["state"], "waiting_for_trash")
                    self.assertNotIn(self.cloud.status_posts[-1]["state"], ("loaded_and_ready", "returning", "canceling", "completed"))
                    self.assertIn(f"last_ack_id=cmd-before-{metadata_name}", self.cloud.get_paths[-1])
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn(metadata_name, encoded_status)
                    self.assertNotIn("software_proof_docker_mobile_current_pwa_retest_browser_proof_gate", encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("terminal_ack", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)
                    self.assertNotIn("dropoff_success", encoded_status)
                    self.assertNotIn("cancel_completed", encoded_status)
                    self.assertNotIn("production_ready", encoded_status)
                    self.assertNotIn("hil_pass", encoded_status)
                    self.assertNotIn("real_device_proof", encoded_status)
                    self.assertNotIn("ready_for_retest", encoded_status)
                    self.assertNotIn("/cmd_vel", encoded_status)
                    self.assertNotIn("/dev/ttyUSB0", encoded_status)
                    self.assertNotIn("Authorization", encoded_status)
                    self.cloud.response_extras["command_response"] = {}

    def test_current_pwa_retest_and_real_device_retest_metadata_are_ignored_by_valid_command_envelope(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                last_ack_id="cmd-before-current-pwa-retest",
                cursor_state_path=state_path,
            )
            self.cloud.response_extras.update({
                "status_response": {
                    "mobile_current_pwa_retest_browser_proof_summary": {
                        "schema": "trashbot.mobile_current_pwa_retest_browser_proof_summary.v1",
                        "evidence_boundary": "software_proof_docker_mobile_current_pwa_retest_browser_proof_gate",
                        "delivery_success": True,
                        "trigger_robot_action": "collect",
                    },
                    "mobile_real_device_retest_request_summary": {
                        "schema": "trashbot.mobile_real_device_retest_request_summary.v1",
                        "evidence_boundary": "software_proof_docker_mobile_real_device_retest_request_gate",
                        "delivery_success": True,
                    },
                },
                "command_response": {
                    "mobile_current_pwa_retest_browser_proof": {
                        "schema": "trashbot.mobile_current_pwa_retest_browser_proof.v1",
                        "evidence_boundary": "software_proof_docker_mobile_current_pwa_retest_browser_proof_gate",
                        "trigger_robot_action": "collect",
                        "cursor_override": "cmd-current-pwa-retest-override",
                        "terminal_ack": "delivered",
                        "delivery_success": True,
                        "dropoff_success": True,
                        "raw_ros_topic": "/cmd_vel",
                    },
                    "phone_current_pwa_retest_browser_proof": {
                        "schema": "trashbot.phone_current_pwa_retest_browser_proof.v1",
                        "safe_phone_copy": "ACK 只代表 accepted/processing，不代表浏览器复测通过或送达成功。",
                        "next_action": "confirm_dropoff",
                        "production_ready": True,
                        "real_device_proof": True,
                        "hil_pass": True,
                    },
                    "mobile_real_device_retest_request": {
                        "schema": "trashbot.mobile_real_device_retest_request.v1",
                        "evidence_boundary": "software_proof_docker_mobile_real_device_retest_request_gate",
                        "trigger_robot_action": "confirm_dropoff",
                        "cursor_override": "cmd-real-device-retest-request-override",
                        "terminal_ack": "delivered",
                        "delivery_success": True,
                        "cancel_completed": True,
                    },
                    "mobile_real_device_retest_request_package": {
                        "schema": "trashbot.mobile_real_device_retest_request_package.v1",
                        "support_refs": [{"kind": "retest_request", "url": "https://user:secret@example.invalid/retest"}],
                        "Authorization": "Bearer must-not-leak",
                        "serial_device": "/dev/ttyUSB0",
                        "ready_for_retest": True,
                    },
                },
                "ack_response": {
                    "mobile_current_pwa_retest_browser_proof_summary": {
                        "schema": "trashbot.mobile_current_pwa_retest_browser_proof_summary.v1",
                        "ack_semantics": "delivery_success",
                        "delivery_success": True,
                        "final_state": "DELIVERED",
                    },
                    "mobile_real_device_retest_request_package": {
                        "schema": "trashbot.mobile_real_device_retest_request_package.v1",
                        "ready_for_retest": True,
                    },
                },
            })
            self.cloud.commands.append({
                "id": "cmd-current-pwa-retest-cancel",
                "type": "cancel",
                "payload": {},
                "mobile_current_pwa_retest_browser_proof": {
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-future",
                    "delivery_success": True,
                },
                "mobile_real_device_retest_request": {
                    "trigger_robot_action": "confirm_dropoff",
                    "terminal_ack": "delivered",
                    "cancel_completed": True,
                },
            })

            self.assertTrue(worker.poll_once())

            self.assertEqual(self.backend.calls, [("cancel",)])
            self.assertEqual(worker.last_ack_id, "cmd-current-pwa-retest-cancel")
            self.assertIn("last_ack_id=cmd-before-current-pwa-retest", self.cloud.get_paths[-1])
            cursor_payload = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(cursor_payload["last_terminal_ack_id"], "cmd-current-pwa-retest-cancel")
            encoded_cursor = json.dumps(cursor_payload, ensure_ascii=False)
            self.assertNotIn("mobile_current_pwa_retest_browser_proof", encoded_cursor)
            self.assertNotIn("mobile_real_device_retest_request", encoded_cursor)
            self.assertNotIn("delivery_success", encoded_cursor)
            ack_payload = self.cloud.ack_posts[0]
            self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
            self.assertEqual(ack_payload["command_id"], "cmd-current-pwa-retest-cancel")
            self.assertEqual(ack_payload["state"], "acked")
            self.assertEqual(ack_payload["message"], "cancel")
            encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
            # 有效 cancel command 混入两类 retest metadata 时，执行、ACK、cursor 仍只跟随 command envelope。
            self.assertNotIn("mobile_current_pwa_retest_browser_proof", encoded_ack)
            self.assertNotIn("mobile_current_pwa_retest_browser_proof_summary", encoded_ack)
            self.assertNotIn("phone_current_pwa_retest_browser_proof", encoded_ack)
            self.assertNotIn("mobile_real_device_retest_request", encoded_ack)
            self.assertNotIn("mobile_real_device_retest_request_summary", encoded_ack)
            self.assertNotIn("mobile_real_device_retest_request_package", encoded_ack)
            self.assertNotIn("software_proof_docker_mobile_current_pwa_retest_browser_proof_gate", encoded_ack)
            self.assertNotIn("software_proof_docker_mobile_real_device_retest_request_gate", encoded_ack)
            self.assertNotIn("trigger_robot_action", encoded_ack)
            self.assertNotIn("cursor_override", encoded_ack)
            self.assertNotIn("terminal_ack", encoded_ack)
            self.assertNotIn("delivery_success", encoded_ack)
            self.assertNotIn("dropoff_success", encoded_ack)
            self.assertNotIn("cancel_completed", encoded_ack)
            self.assertNotIn("production_ready", encoded_ack)
            self.assertNotIn("real_device_proof", encoded_ack)
            self.assertNotIn("ready_for_retest", encoded_ack)
            self.assertNotIn("hil_pass", encoded_ack)
            self.assertNotIn("/cmd_vel", encoded_ack)
            self.assertNotIn("/dev/ttyUSB0", encoded_ack)
            self.assertNotIn("Authorization", encoded_ack)
            self.assertNotIn("secret", encoded_ack)
            self.assertNotIn("DELIVERED", encoded_ack)
            encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
            self.assertNotIn("mobile_current_pwa_retest_browser_proof", encoded_status)
            self.assertNotIn("mobile_real_device_retest_request", encoded_status)
            self.assertNotIn("delivery_success", encoded_status)
            self.assertEqual(self.cloud.status_posts[-1]["state"], "canceling")
            self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_mobile_current_pwa_field_trial_browser_proof_metadata_only_response_does_not_move_robot(self):
        metadata_cases = (
            (
                "mobile_current_pwa_field_trial_browser_proof",
                {
                    "schema": "trashbot.mobile_current_pwa_field_trial_browser_proof.v1",
                    "evidence_boundary": "software_proof_docker_mobile_current_pwa_field_trial_browser_proof_gate",
                    "viewport_results": {"390x844": "passed", "768x900": "passed"},
                    "field_trial_panels_visible": True,
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-current-pwa-field-trial",
                    "terminal_ack": "delivered",
                    "ack_semantics": "delivery_success",
                    "delivery_success": True,
                    "dropoff_success": True,
                    "cancel_completed": True,
                    "production_ready": True,
                    "hil_pass": True,
                    "raw_ros_topic": "/cmd_vel",
                },
            ),
            (
                "mobile_current_pwa_field_trial_browser_proof_summary",
                {
                    "schema": "trashbot.mobile_current_pwa_field_trial_browser_proof_summary.v1",
                    "safe_phone_copy": "当前 PWA field-trial browser proof 只是本地 Chromium 软件证明。",
                    "next_action": "confirm_dropoff",
                    "cursor_override": "cmd-current-pwa-field-trial-summary",
                    "delivery_success": True,
                    "real_device_proof": True,
                    "production_ready": True,
                    "field_trial_browser_proof_ready": True,
                },
            ),
            (
                "mobile_current_pwa_field_trial_browser_proof_copy",
                {
                    "schema": "trashbot.mobile_current_pwa_field_trial_browser_proof_copy.v1",
                    "evidence_boundary": "software_proof_docker_mobile_current_pwa_field_trial_browser_proof_gate",
                    "safe_to_control": True,
                    "trigger_robot_action": "cancel",
                    "Authorization": "Bearer must-not-leak",
                    "serial_device": "/dev/ttyUSB0",
                },
            ),
        )
        for metadata_name, metadata in metadata_cases:
            with self.subTest(metadata_name=metadata_name):
                # 每个 family 成员单独跑，避免某个 metadata 名称被隐式当作 command 信号。
                self.cloud.status_posts.clear()
                self.cloud.ack_posts.clear()
                self.cloud.get_paths.clear()
                self.backend.calls.clear()
                # metadata 被放在 command_response sidecar，模拟云端只返回证明材料、没有 command envelope。
                self.cloud.response_extras["command_response"] = {metadata_name: metadata}
                with tempfile.TemporaryDirectory() as tmpdir:
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-{metadata_name}",
                        cursor_state_path=state_path,
                    )

                    handled = worker.poll_once()

                    # current PWA field-trial browser proof 是 metadata-only；没有 command envelope 不能触发机器人副作用。
                    self.assertFalse(handled)
                    # 本地 collect/dropoff/cancel 后端调用必须保持为空，证明没有控制动作被合成。
                    self.assertEqual(self.backend.calls, [])
                    # 没有合法 command id 时不能 POST ACK，否则会把 proof metadata 误当远程命令处理。
                    self.assertEqual(self.cloud.ack_posts, [])
                    # cursor 只能由 terminal ACK 推进；metadata-only 响应必须保留原 last_ack_id。
                    self.assertEqual(worker.last_ack_id, f"cmd-before-{metadata_name}")
                    self.assertFalse(state_path.exists())
                    # status POST 只允许发送机器人当前状态快照，不能夹带 browser proof sidecar。
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    self.assertEqual(self.cloud.status_posts[-1]["state"], "waiting_for_trash")
                    self.assertNotIn(self.cloud.status_posts[-1]["state"], ("loaded_and_ready", "returning", "canceling", "completed"))
                    self.assertIn(f"last_ack_id=cmd-before-{metadata_name}", self.cloud.get_paths[-1])
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    # 以下字段覆盖本轮禁止语义：控制、ACK/cursor、terminal ACK、成功、production/HIL 和敏感材料。
                    self.assertNotIn(metadata_name, encoded_status)
                    self.assertNotIn("software_proof_docker_mobile_current_pwa_field_trial_browser_proof_gate", encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("terminal_ack", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)
                    self.assertNotIn("dropoff_success", encoded_status)
                    self.assertNotIn("cancel_completed", encoded_status)
                    self.assertNotIn("production_ready", encoded_status)
                    self.assertNotIn("hil_pass", encoded_status)
                    self.assertNotIn("real_device_proof", encoded_status)
                    self.assertNotIn("field_trial_browser_proof_ready", encoded_status)
                    self.assertNotIn("/cmd_vel", encoded_status)
                    self.assertNotIn("/dev/ttyUSB0", encoded_status)
                    self.assertNotIn("Authorization", encoded_status)
                    # 清空 sidecar，避免 subTest 之间的云端 mock 状态串扰。
                    self.cloud.response_extras["command_response"] = {}

    def test_mobile_current_pwa_field_trial_browser_proof_metadata_does_not_change_valid_command_envelope(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                last_ack_id="cmd-before-current-pwa-field-trial",
                cursor_state_path=state_path,
            )
            self.cloud.response_extras.update({
                "status_response": {
                    # status/ACK/command 三类 response 都带危险 metadata，用来证明 worker 只消费 command envelope。
                    "mobile_current_pwa_field_trial_browser_proof_summary": {
                        "schema": "trashbot.mobile_current_pwa_field_trial_browser_proof_summary.v1",
                        "evidence_boundary": "software_proof_docker_mobile_current_pwa_field_trial_browser_proof_gate",
                        "delivery_success": True,
                        "trigger_robot_action": "cancel",
                    },
                },
                "command_response": {
                    "mobile_current_pwa_field_trial_browser_proof": {
                        "schema": "trashbot.mobile_current_pwa_field_trial_browser_proof.v1",
                        "evidence_boundary": "software_proof_docker_mobile_current_pwa_field_trial_browser_proof_gate",
                        "trigger_robot_action": "cancel",
                        "cursor_override": "cmd-current-pwa-field-trial-override",
                        "terminal_ack": "delivered",
                        "delivery_success": True,
                        "dropoff_success": True,
                        "raw_ros_topic": "/cmd_vel",
                    },
                    "mobile_current_pwa_field_trial_browser_proof_copy": {
                        "schema": "trashbot.mobile_current_pwa_field_trial_browser_proof_copy.v1",
                        "safe_phone_copy": "ACK 只代表 accepted/processing，不代表 field-trial browser proof 或送达成功。",
                        "next_action": "confirm_dropoff",
                        "production_ready": True,
                        "real_device_proof": True,
                        "hil_pass": True,
                    },
                },
                "ack_response": {
                    "mobile_current_pwa_field_trial_browser_proof_summary": {
                        "schema": "trashbot.mobile_current_pwa_field_trial_browser_proof_summary.v1",
                        "ack_semantics": "delivery_success",
                        "delivery_success": True,
                        "final_state": "DELIVERED",
                    },
                },
            })
            self.cloud.commands.append({
                "id": "cmd-current-pwa-field-trial-collect",
                "type": "collect",
                "idempotency_key": "idem-current-pwa-field-trial",
                "payload": {"target": "trash_station", "trash_type": 7},
                "mobile_current_pwa_field_trial_browser_proof": {
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-future",
                    "delivery_success": True,
                },
            })

            self.assertTrue(worker.poll_once())

            self.assertEqual(self.backend.calls, [("collect", "trash_station", 7)])
            self.assertEqual(worker.last_ack_id, "cmd-current-pwa-field-trial-collect")
            # 第一次 GET 仍携带旧 cursor，说明 metadata 没有提前改写 poll cursor。
            self.assertIn("last_ack_id=cmd-before-current-pwa-field-trial", self.cloud.get_paths[-1])
            cursor_payload = json.loads(state_path.read_text(encoding="utf-8"))
            # cursor 持久化只记录 terminal ACK 的 command id，不保存 proof metadata 或 delivery 语义。
            self.assertEqual(cursor_payload["last_terminal_ack_id"], "cmd-current-pwa-field-trial-collect")
            encoded_cursor = json.dumps(cursor_payload, ensure_ascii=False)
            self.assertNotIn("mobile_current_pwa_field_trial_browser_proof", encoded_cursor)
            self.assertNotIn("delivery_success", encoded_cursor)
            ack_payload = self.cloud.ack_posts[0]
            self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
            self.assertEqual(ack_payload["command_id"], "cmd-current-pwa-field-trial-collect")
            self.assertEqual(ack_payload["state"], "acked")
            self.assertEqual(ack_payload["message"], "collect")
            encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
            # 混入 browser proof metadata 时，action、target、ACK、cursor 仍只跟随合法 trashbot.remote.v1 envelope。
            # idempotency_key 不进入 ACK payload，避免 metadata 或 command 去重字段被误当处理结果回传。
            self.assertNotIn("mobile_current_pwa_field_trial_browser_proof", encoded_ack)
            self.assertNotIn("mobile_current_pwa_field_trial_browser_proof_summary", encoded_ack)
            self.assertNotIn("mobile_current_pwa_field_trial_browser_proof_copy", encoded_ack)
            self.assertNotIn("software_proof_docker_mobile_current_pwa_field_trial_browser_proof_gate", encoded_ack)
            self.assertNotIn("idempotency_key", encoded_ack)
            self.assertNotIn("trigger_robot_action", encoded_ack)
            self.assertNotIn("cursor_override", encoded_ack)
            self.assertNotIn("terminal_ack", encoded_ack)
            self.assertNotIn("delivery_success", encoded_ack)
            self.assertNotIn("dropoff_success", encoded_ack)
            self.assertNotIn("cancel_completed", encoded_ack)
            self.assertNotIn("production_ready", encoded_ack)
            self.assertNotIn("real_device_proof", encoded_ack)
            self.assertNotIn("hil_pass", encoded_ack)
            self.assertNotIn("/cmd_vel", encoded_ack)
            self.assertNotIn("DELIVERED", encoded_ack)
            encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
            self.assertNotIn("mobile_current_pwa_field_trial_browser_proof", encoded_status)
            self.assertNotIn("delivery_success", encoded_status)
            # 唯一允许的状态变化来自合法 collect command，不是 browser proof 的成功语义。
            self.assertEqual(self.cloud.status_posts[-1]["state"], "loaded_and_ready")
            self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_mobile_real_device_evidence_intake_metadata_only_response_does_not_move_robot(self):
        metadata_cases = (
            (
                "mobile_real_device_evidence_intake",
                {
                    "schema": "trashbot.mobile_real_device_evidence_intake.v1",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_evidence_intake_gate",
                    "device": {"platform": "ios", "model_summary": "redacted"},
                    "browser": {"family": "Safari", "viewport_css": {"width": 390, "height": 844}},
                    "pwa": {"install_prompt_status": "not_observed"},
                    "production_app": {"ready": True},
                    "safe_to_control": True,
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-real-device-intake",
                    "ack_semantics": "delivery_success",
                    "delivery_success": True,
                    "dropoff_success": True,
                    "cancel_completed": True,
                    "production_ready": True,
                    "hil_pass": True,
                    "raw_ros_topic": "/cmd_vel",
                },
            ),
            (
                "mobile_real_device_evidence_intake_summary",
                {
                    "schema": "trashbot.mobile_real_device_evidence_intake_summary.v1",
                    "safe_phone_copy": "真实设备材料导入只供验收和支持侧判断。",
                    "next_action": "confirm_dropoff",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_evidence_intake_gate",
                    "real_device_proof": True,
                    "production_app_ready": True,
                    "pwa_install_prompt_proof": True,
                    "cursor_override": "cmd-real-device-summary",
                    "delivery_success": True,
                    "dropoff_success": True,
                },
            ),
            (
                "mobile_real_device_evidence_package",
                {
                    "schema": "trashbot.mobile_real_device_evidence_package.v1",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_evidence_intake_gate",
                    "support_refs": [{"kind": "screenshot", "url": "https://user:secret@example.invalid/real-device.png"}],
                    "not_proven": ["real_delivery", "hil_pass"],
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-real-device-package",
                    "Authorization": "Bearer must-not-leak",
                    "serial_device": "/dev/ttyUSB0",
                    "wave_rover_feedback": True,
                    "cancel_completed": True,
                },
            ),
        )
        for metadata_name, metadata in metadata_cases:
            with self.subTest(metadata_name=metadata_name):
                self.cloud.status_posts.clear()
                self.cloud.ack_posts.clear()
                self.backend.calls.clear()
                self.cloud.response_extras["command_response"] = {
                    metadata_name: metadata,
                    "preflight": {"overall_status": "blocked", "production_ready": False},
                }
                with tempfile.TemporaryDirectory() as tmpdir:
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-{metadata_name}",
                        cursor_state_path=state_path,
                    )

                    handled = worker.poll_once()

                    # 真实设备材料 intake 只是验收/支持元数据；没有 command envelope 不能触发控制副作用。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-{metadata_name}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    self.assertIn(f"last_ack_id=cmd-before-{metadata_name}", self.cloud.get_paths[-1])
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn(metadata_name, encoded_status)
                    self.assertNotIn("software_proof_docker_mobile_real_device_evidence_intake_gate", encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)
                    self.assertNotIn("dropoff_success", encoded_status)
                    self.assertNotIn("cancel_completed", encoded_status)
                    self.assertNotIn("production_ready", encoded_status)
                    self.assertNotIn("production_app_ready", encoded_status)
                    self.assertNotIn("hil_pass", encoded_status)
                    self.assertNotIn("real_device_proof", encoded_status)
                    self.assertNotIn("pwa_install_prompt_proof", encoded_status)
                    self.assertNotIn("wave_rover_feedback", encoded_status)
                    self.assertNotIn("/cmd_vel", encoded_status)
                    self.assertNotIn("/dev/ttyUSB0", encoded_status)
                    self.assertNotIn("Authorization", encoded_status)
                    self.assertNotIn("secret", encoded_status)
                    self.cloud.response_extras["command_response"] = {}

    def test_mobile_real_device_evidence_intake_metadata_is_ignored_by_valid_command_envelope(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                last_ack_id="cmd-before-real-device-intake",
                cursor_state_path=state_path,
            )
            self.cloud.response_extras.update({
                "status_response": {
                    "mobile_real_device_evidence_intake_summary": {
                        "schema": "trashbot.mobile_real_device_evidence_intake_summary.v1",
                        "evidence_boundary": "software_proof_docker_mobile_real_device_evidence_intake_gate",
                        "delivery_success": True,
                        "trigger_robot_action": "collect",
                    },
                },
                "command_response": {
                    "mobile_real_device_evidence_intake": {
                        "schema": "trashbot.mobile_real_device_evidence_intake.v1",
                        "evidence_boundary": "software_proof_docker_mobile_real_device_evidence_intake_gate",
                        "trigger_robot_action": "cancel",
                        "cursor_override": "cmd-real-device-override",
                        "ack_semantics": "delivery_success",
                        "delivery_success": True,
                        "dropoff_success": True,
                        "raw_ros_topic": "/cmd_vel",
                    },
                    "mobile_real_device_evidence_intake_summary": {
                        "schema": "trashbot.mobile_real_device_evidence_intake_summary.v1",
                        "safe_phone_copy": "ACK 只代表 accepted/processing，不代表真实手机验收通过。",
                        "next_action": "confirm_dropoff",
                        "production_app_ready": True,
                        "real_device_proof": True,
                        "pwa_install_prompt_proof": True,
                        "hil_pass": True,
                    },
                    "mobile_real_device_evidence_package": {
                        "schema": "trashbot.mobile_real_device_evidence_package.v1",
                        "support_refs": [{"kind": "screenshot", "url": "https://user:secret@example.invalid/real-device.png"}],
                        "Authorization": "Bearer must-not-leak",
                        "serial_device": "/dev/ttyUSB0",
                        "cancel_completed": True,
                    },
                },
                "ack_response": {
                    "mobile_real_device_evidence_package": {
                        "schema": "trashbot.mobile_real_device_evidence_package.v1",
                        "ack_semantics": "delivery_success",
                        "delivery_success": True,
                        "final_state": "DELIVERED",
                    },
                },
            })
            self.cloud.commands.append({
                "id": "cmd-real-device-intake-confirm",
                "type": "confirm_dropoff",
                "payload": {"accepted": True},
                "mobile_real_device_evidence_intake": {
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-future",
                    "delivery_success": True,
                },
            })

            self.assertTrue(worker.poll_once())

            self.assertEqual(self.backend.calls, [("confirm_dropoff", True)])
            self.assertEqual(worker.last_ack_id, "cmd-real-device-intake-confirm")
            self.assertIn("last_ack_id=cmd-before-real-device-intake", self.cloud.get_paths[-1])
            cursor_payload = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(cursor_payload["last_terminal_ack_id"], "cmd-real-device-intake-confirm")
            ack_payload = self.cloud.ack_posts[0]
            self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
            self.assertEqual(ack_payload["command_id"], "cmd-real-device-intake-confirm")
            self.assertEqual(ack_payload["state"], "acked")
            self.assertEqual(ack_payload["message"], "confirm_dropoff")
            encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
            # 有效 command 混入真实设备 intake metadata 时，执行、ACK、cursor 仍只跟随 command envelope。
            self.assertNotIn("mobile_real_device_evidence_intake", encoded_ack)
            self.assertNotIn("mobile_real_device_evidence_intake_summary", encoded_ack)
            self.assertNotIn("mobile_real_device_evidence_package", encoded_ack)
            self.assertNotIn("software_proof_docker_mobile_real_device_evidence_intake_gate", encoded_ack)
            self.assertNotIn("trigger_robot_action", encoded_ack)
            self.assertNotIn("cursor_override", encoded_ack)
            self.assertNotIn("delivery_success", encoded_ack)
            self.assertNotIn("dropoff_success", encoded_ack)
            self.assertNotIn("cancel_completed", encoded_ack)
            self.assertNotIn("production_app_ready", encoded_ack)
            self.assertNotIn("real_device_proof", encoded_ack)
            self.assertNotIn("pwa_install_prompt_proof", encoded_ack)
            self.assertNotIn("hil_pass", encoded_ack)
            self.assertNotIn("/cmd_vel", encoded_ack)
            self.assertNotIn("/dev/ttyUSB0", encoded_ack)
            self.assertNotIn("Authorization", encoded_ack)
            self.assertNotIn("secret", encoded_ack)
            self.assertNotIn("DELIVERED", encoded_ack)
            encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
            self.assertNotIn("mobile_real_device_evidence_intake", encoded_status)
            self.assertNotIn("mobile_real_device_evidence_intake_summary", encoded_status)
            self.assertNotIn("mobile_real_device_evidence_package", encoded_status)
            self.assertNotIn("software_proof_docker_mobile_real_device_evidence_intake_gate", encoded_status)
            self.assertNotIn("delivery_success", encoded_status)
            self.assertEqual(self.cloud.status_posts[-1]["state"], "returning")
            self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_mobile_real_device_acceptance_decision_metadata_only_response_does_not_move_robot(self):
        metadata_cases = (
            (
                "mobile_real_device_acceptance_decision",
                {
                    "schema": "trashbot.mobile_real_device_acceptance_decision.v1",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_acceptance_decision_gate",
                    "decision": "accepted",
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-real-device-decision",
                    "ack_semantics": "delivery_success",
                    "terminal_ack": "delivered",
                    "delivery_success": True,
                    "dropoff_success": True,
                    "cancel_completed": True,
                    "production_ready": True,
                    "hil_pass": True,
                    "raw_ros_topic": "/cmd_vel",
                },
            ),
            (
                "mobile_real_device_acceptance_decision_summary",
                {
                    "schema": "trashbot.mobile_real_device_acceptance_decision_summary.v1",
                    "safe_phone_copy": "真实设备验收决策只供产品和支持侧判断。",
                    "next_action": "confirm_dropoff",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_acceptance_decision_gate",
                    "real_device_acceptance": True,
                    "production_app_ready": True,
                    "cursor_override": "cmd-real-device-decision-summary",
                    "terminal_ack": "delivered",
                    "delivery_success": True,
                    "dropoff_success": True,
                },
            ),
            (
                "mobile_real_device_acceptance_decision_package",
                {
                    "schema": "trashbot.mobile_real_device_acceptance_decision_package.v1",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_acceptance_decision_gate",
                    "support_refs": [{"kind": "screenshot", "url": "https://user:secret@example.invalid/decision.png"}],
                    "not_proven": ["production_readiness", "hil_pass", "delivery_success"],
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-real-device-decision-package",
                    "terminal_ack": "delivered",
                    "Authorization": "Bearer must-not-leak",
                    "serial_device": "/dev/ttyUSB0",
                    "cancel_completed": True,
                },
            ),
        )
        for metadata_name, metadata in metadata_cases:
            with self.subTest(metadata_name=metadata_name):
                self.cloud.status_posts.clear()
                self.cloud.ack_posts.clear()
                self.cloud.get_paths.clear()
                self.backend.calls.clear()
                self.cloud.response_extras["command_response"] = {metadata_name: metadata}
                with tempfile.TemporaryDirectory() as tmpdir:
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-{metadata_name}",
                        cursor_state_path=state_path,
                    )

                    handled = worker.poll_once()

                    # 真实设备验收决策 metadata-only 不能驱动 robot action、ACK 或 cursor 持久化。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-{metadata_name}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    self.assertIn(f"last_ack_id=cmd-before-{metadata_name}", self.cloud.get_paths[-1])
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn(metadata_name, encoded_status)
                    self.assertNotIn("software_proof_docker_mobile_real_device_acceptance_decision_gate", encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("terminal_ack", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)
                    self.assertNotIn("dropoff_success", encoded_status)
                    self.assertNotIn("cancel_completed", encoded_status)
                    self.assertNotIn("production_ready", encoded_status)
                    self.assertNotIn("production_app_ready", encoded_status)
                    self.assertNotIn("hil_pass", encoded_status)
                    self.assertNotIn("real_device_acceptance", encoded_status)
                    self.assertNotIn("/cmd_vel", encoded_status)
                    self.assertNotIn("/dev/ttyUSB0", encoded_status)
                    self.assertNotIn("Authorization", encoded_status)
                    self.assertNotIn("secret", encoded_status)
                    self.cloud.response_extras["command_response"] = {}

    def test_mobile_real_device_acceptance_decision_metadata_is_ignored_by_valid_command_envelope(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                last_ack_id="cmd-before-real-device-decision",
                cursor_state_path=state_path,
            )
            self.cloud.response_extras.update({
                "status_response": {
                    "mobile_real_device_acceptance_decision_summary": {
                        "schema": "trashbot.mobile_real_device_acceptance_decision_summary.v1",
                        "evidence_boundary": "software_proof_docker_mobile_real_device_acceptance_decision_gate",
                        "delivery_success": True,
                        "trigger_robot_action": "collect",
                    },
                },
                "command_response": {
                    "mobile_real_device_acceptance_decision": {
                        "schema": "trashbot.mobile_real_device_acceptance_decision.v1",
                        "evidence_boundary": "software_proof_docker_mobile_real_device_acceptance_decision_gate",
                        "trigger_robot_action": "cancel",
                        "cursor_override": "cmd-real-device-decision-override",
                        "ack_semantics": "delivery_success",
                        "terminal_ack": "delivered",
                        "delivery_success": True,
                        "dropoff_success": True,
                        "raw_ros_topic": "/cmd_vel",
                    },
                    "mobile_real_device_acceptance_decision_summary": {
                        "schema": "trashbot.mobile_real_device_acceptance_decision_summary.v1",
                        "safe_phone_copy": "ACK 只代表 accepted/processing，不代表真实设备验收决策完成。",
                        "next_action": "confirm_dropoff",
                        "production_app_ready": True,
                        "real_device_acceptance": True,
                        "hil_pass": True,
                    },
                    "mobile_real_device_acceptance_decision_package": {
                        "schema": "trashbot.mobile_real_device_acceptance_decision_package.v1",
                        "support_refs": [{"kind": "screenshot", "url": "https://user:secret@example.invalid/decision.png"}],
                        "Authorization": "Bearer must-not-leak",
                        "serial_device": "/dev/ttyUSB0",
                        "cancel_completed": True,
                    },
                },
                "ack_response": {
                    "mobile_real_device_acceptance_decision_package": {
                        "schema": "trashbot.mobile_real_device_acceptance_decision_package.v1",
                        "ack_semantics": "delivery_success",
                        "delivery_success": True,
                        "final_state": "DELIVERED",
                    },
                },
            })
            self.cloud.commands.append({
                "id": "cmd-real-device-decision-cancel",
                "type": "cancel",
                "payload": {},
                "mobile_real_device_acceptance_decision": {
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-future",
                    "delivery_success": True,
                },
            })

            self.assertTrue(worker.poll_once())

            self.assertEqual(self.backend.calls, [("cancel",)])
            self.assertEqual(worker.last_ack_id, "cmd-real-device-decision-cancel")
            self.assertIn("last_ack_id=cmd-before-real-device-decision", self.cloud.get_paths[-1])
            cursor_payload = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(cursor_payload["last_terminal_ack_id"], "cmd-real-device-decision-cancel")
            ack_payload = self.cloud.ack_posts[0]
            self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
            self.assertEqual(ack_payload["command_id"], "cmd-real-device-decision-cancel")
            self.assertEqual(ack_payload["state"], "acked")
            self.assertEqual(ack_payload["message"], "cancel")
            encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
            # 有效 command 混入验收决策 metadata 时，执行、ACK、cursor 仍只跟随 command envelope。
            self.assertNotIn("mobile_real_device_acceptance_decision", encoded_ack)
            self.assertNotIn("mobile_real_device_acceptance_decision_summary", encoded_ack)
            self.assertNotIn("mobile_real_device_acceptance_decision_package", encoded_ack)
            self.assertNotIn("software_proof_docker_mobile_real_device_acceptance_decision_gate", encoded_ack)
            self.assertNotIn("trigger_robot_action", encoded_ack)
            self.assertNotIn("cursor_override", encoded_ack)
            self.assertNotIn("terminal_ack", encoded_ack)
            self.assertNotIn("delivery_success", encoded_ack)
            self.assertNotIn("dropoff_success", encoded_ack)
            self.assertNotIn("cancel_completed", encoded_ack)
            self.assertNotIn("production_app_ready", encoded_ack)
            self.assertNotIn("real_device_acceptance", encoded_ack)
            self.assertNotIn("hil_pass", encoded_ack)
            self.assertNotIn("/cmd_vel", encoded_ack)
            self.assertNotIn("/dev/ttyUSB0", encoded_ack)
            self.assertNotIn("Authorization", encoded_ack)
            self.assertNotIn("secret", encoded_ack)
            self.assertNotIn("DELIVERED", encoded_ack)
            encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
            self.assertNotIn("mobile_real_device_acceptance_decision", encoded_status)
            self.assertNotIn("mobile_real_device_acceptance_decision_summary", encoded_status)
            self.assertNotIn("mobile_real_device_acceptance_decision_package", encoded_status)
            self.assertNotIn("software_proof_docker_mobile_real_device_acceptance_decision_gate", encoded_status)
            self.assertNotIn("delivery_success", encoded_status)
            self.assertEqual(self.cloud.status_posts[-1]["state"], "canceling")
            self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_mobile_real_device_review_handoff_metadata_only_response_does_not_move_robot(self):
        metadata_cases = (
            (
                "mobile_real_device_review_handoff",
                {
                    "schema": "trashbot.mobile_real_device_review_handoff.v1",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_review_handoff_gate",
                    "review_state": "ready_for_product_review",
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-real-device-review-handoff",
                    "ack_semantics": "delivery_success",
                    "terminal_ack": "delivered",
                    "delivery_success": True,
                    "dropoff_success": True,
                    "cancel_completed": True,
                    "production_ready": True,
                    "hil_pass": True,
                    "raw_ros_topic": "/cmd_vel",
                },
            ),
            (
                "mobile_real_device_review_handoff_summary",
                {
                    "schema": "trashbot.mobile_real_device_review_handoff_summary.v1",
                    "safe_phone_copy": "真实设备评审交接只供产品和支持侧人工判断。",
                    "next_action": "confirm_dropoff",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_review_handoff_gate",
                    "real_device_review_complete": True,
                    "production_app_ready": True,
                    "cursor_override": "cmd-real-device-review-summary",
                    "terminal_ack": "delivered",
                    "delivery_success": True,
                    "dropoff_success": True,
                },
            ),
            (
                "mobile_real_device_review_handoff_package",
                {
                    "schema": "trashbot.mobile_real_device_review_handoff_package.v1",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_review_handoff_gate",
                    "support_refs": [{"kind": "review", "url": "https://user:secret@example.invalid/review"}],
                    "not_proven": ["production_readiness", "hil_pass", "delivery_success"],
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-real-device-review-package",
                    "terminal_ack": "delivered",
                    "Authorization": "Bearer must-not-leak",
                    "serial_device": "/dev/ttyUSB0",
                    "cancel_completed": True,
                },
            ),
        )
        for metadata_name, metadata in metadata_cases:
            with self.subTest(metadata_name=metadata_name):
                self.cloud.status_posts.clear()
                self.cloud.ack_posts.clear()
                self.cloud.get_paths.clear()
                self.backend.calls.clear()
                self.cloud.response_extras["command_response"] = {metadata_name: metadata}
                with tempfile.TemporaryDirectory() as tmpdir:
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-{metadata_name}",
                        cursor_state_path=state_path,
                    )

                    handled = worker.poll_once()

                    # 评审交接 metadata-only 不能驱动 robot action、ACK 或 cursor 持久化。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-{metadata_name}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    self.assertIn(f"last_ack_id=cmd-before-{metadata_name}", self.cloud.get_paths[-1])
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn(metadata_name, encoded_status)
                    self.assertNotIn("software_proof_docker_mobile_real_device_review_handoff_gate", encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("terminal_ack", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)
                    self.assertNotIn("dropoff_success", encoded_status)
                    self.assertNotIn("cancel_completed", encoded_status)
                    self.assertNotIn("production_ready", encoded_status)
                    self.assertNotIn("production_app_ready", encoded_status)
                    self.assertNotIn("hil_pass", encoded_status)
                    self.assertNotIn("real_device_review_complete", encoded_status)
                    self.assertNotIn("/cmd_vel", encoded_status)
                    self.assertNotIn("/dev/ttyUSB0", encoded_status)
                    self.assertNotIn("Authorization", encoded_status)
                    self.assertNotIn("secret", encoded_status)
                    self.cloud.response_extras["command_response"] = {}

    def test_mobile_real_device_review_handoff_metadata_is_ignored_by_valid_command_envelope(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                last_ack_id="cmd-before-real-device-review-handoff",
                cursor_state_path=state_path,
            )
            self.cloud.response_extras.update({
                "status_response": {
                    "mobile_real_device_review_handoff_summary": {
                        "schema": "trashbot.mobile_real_device_review_handoff_summary.v1",
                        "evidence_boundary": "software_proof_docker_mobile_real_device_review_handoff_gate",
                        "delivery_success": True,
                        "trigger_robot_action": "collect",
                    },
                },
                "command_response": {
                    "mobile_real_device_review_handoff": {
                        "schema": "trashbot.mobile_real_device_review_handoff.v1",
                        "evidence_boundary": "software_proof_docker_mobile_real_device_review_handoff_gate",
                        "trigger_robot_action": "cancel",
                        "cursor_override": "cmd-real-device-review-override",
                        "ack_semantics": "delivery_success",
                        "terminal_ack": "delivered",
                        "delivery_success": True,
                        "dropoff_success": True,
                        "raw_ros_topic": "/cmd_vel",
                    },
                    "mobile_real_device_review_handoff_summary": {
                        "schema": "trashbot.mobile_real_device_review_handoff_summary.v1",
                        "safe_phone_copy": "ACK 只代表 accepted/processing，不代表真实设备评审交接完成。",
                        "next_action": "confirm_dropoff",
                        "production_app_ready": True,
                        "real_device_review_complete": True,
                        "hil_pass": True,
                    },
                    "mobile_real_device_review_handoff_package": {
                        "schema": "trashbot.mobile_real_device_review_handoff_package.v1",
                        "support_refs": [{"kind": "review", "url": "https://user:secret@example.invalid/review"}],
                        "Authorization": "Bearer must-not-leak",
                        "serial_device": "/dev/ttyUSB0",
                        "cancel_completed": True,
                    },
                },
                "ack_response": {
                    "mobile_real_device_review_handoff_package": {
                        "schema": "trashbot.mobile_real_device_review_handoff_package.v1",
                        "ack_semantics": "delivery_success",
                        "delivery_success": True,
                        "final_state": "DELIVERED",
                    },
                },
            })
            self.cloud.commands.append({
                "id": "cmd-real-device-review-confirm",
                "type": "confirm_dropoff",
                "payload": {"accepted": True},
                "mobile_real_device_review_handoff": {
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-future",
                    "delivery_success": True,
                },
            })

            self.assertTrue(worker.poll_once())

            self.assertEqual(self.backend.calls, [("confirm_dropoff", True)])
            self.assertEqual(worker.last_ack_id, "cmd-real-device-review-confirm")
            self.assertIn("last_ack_id=cmd-before-real-device-review-handoff", self.cloud.get_paths[-1])
            cursor_payload = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(cursor_payload["last_terminal_ack_id"], "cmd-real-device-review-confirm")
            ack_payload = self.cloud.ack_posts[0]
            self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
            self.assertEqual(ack_payload["command_id"], "cmd-real-device-review-confirm")
            self.assertEqual(ack_payload["state"], "acked")
            self.assertEqual(ack_payload["message"], "confirm_dropoff")
            encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
            # 有效 command 混入评审交接 metadata 时，执行、ACK、cursor 仍只跟随 command envelope。
            self.assertNotIn("mobile_real_device_review_handoff", encoded_ack)
            self.assertNotIn("mobile_real_device_review_handoff_summary", encoded_ack)
            self.assertNotIn("mobile_real_device_review_handoff_package", encoded_ack)
            self.assertNotIn("software_proof_docker_mobile_real_device_review_handoff_gate", encoded_ack)
            self.assertNotIn("trigger_robot_action", encoded_ack)
            self.assertNotIn("cursor_override", encoded_ack)
            self.assertNotIn("terminal_ack", encoded_ack)
            self.assertNotIn("delivery_success", encoded_ack)
            self.assertNotIn("dropoff_success", encoded_ack)
            self.assertNotIn("cancel_completed", encoded_ack)
            self.assertNotIn("production_app_ready", encoded_ack)
            self.assertNotIn("real_device_review_complete", encoded_ack)
            self.assertNotIn("hil_pass", encoded_ack)
            self.assertNotIn("/cmd_vel", encoded_ack)
            self.assertNotIn("/dev/ttyUSB0", encoded_ack)
            self.assertNotIn("Authorization", encoded_ack)
            self.assertNotIn("secret", encoded_ack)
            self.assertNotIn("DELIVERED", encoded_ack)
            encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
            self.assertNotIn("mobile_real_device_review_handoff", encoded_status)
            self.assertNotIn("mobile_real_device_review_handoff_summary", encoded_status)
            self.assertNotIn("mobile_real_device_review_handoff_package", encoded_status)
            self.assertNotIn("software_proof_docker_mobile_real_device_review_handoff_gate", encoded_status)
            self.assertNotIn("delivery_success", encoded_status)
            self.assertEqual(self.cloud.status_posts[-1]["state"], "returning")
            self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_mobile_real_device_review_execution_metadata_only_response_does_not_move_robot(self):
        metadata_cases = (
            (
                "mobile_real_device_review_execution",
                {
                    "schema": "trashbot.mobile_real_device_review_execution.v1",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_review_execution_gate",
                    "review_result": "blocked_no_real_device_materials",
                    "operator_notes": "review execution metadata must stay outside robot control",
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-real-device-review-execution",
                    "ack_semantics": "delivery_success",
                    "terminal_ack": "delivered",
                    "delivery_success": True,
                    "dropoff_success": True,
                    "cancel_completed": True,
                    "production_ready": True,
                    "hil_pass": True,
                    "raw_ros_topic": "/cmd_vel",
                },
            ),
            (
                "mobile_real_device_review_execution_summary",
                {
                    "schema": "trashbot.mobile_real_device_review_execution_summary.v1",
                    "safe_phone_copy": "真实设备评审执行只供产品和支持侧人工复核。",
                    "next_action": "confirm_dropoff",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_review_execution_gate",
                    "real_device_review_executed": True,
                    "production_app_ready": True,
                    "cursor_override": "cmd-real-device-review-execution-summary",
                    "terminal_ack": "delivered",
                    "delivery_success": True,
                    "dropoff_success": True,
                },
            ),
            (
                "mobile_real_device_review_execution_package",
                {
                    "schema": "trashbot.mobile_real_device_review_execution_package.v1",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_review_execution_gate",
                    "support_refs": [{"kind": "review_execution", "url": "https://user:secret@example.invalid/review"}],
                    "not_proven": ["production readiness", "HIL", "delivery success"],
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-real-device-review-execution-package",
                    "terminal_ack": "delivered",
                    "Authorization": "Bearer must-not-leak",
                    "serial_device": "/dev/ttyUSB0",
                    "cancel_completed": True,
                },
            ),
        )
        for metadata_name, metadata in metadata_cases:
            with self.subTest(metadata_name=metadata_name):
                self.cloud.status_posts.clear()
                self.cloud.ack_posts.clear()
                self.cloud.get_paths.clear()
                self.backend.calls.clear()
                self.cloud.response_extras["command_response"] = {metadata_name: metadata}
                with tempfile.TemporaryDirectory() as tmpdir:
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-{metadata_name}",
                        cursor_state_path=state_path,
                    )

                    handled = worker.poll_once()

                    # 评审执行 metadata-only 不能驱动 robot action、ACK、terminal ACK 或 cursor 持久化。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-{metadata_name}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    self.assertIn(f"last_ack_id=cmd-before-{metadata_name}", self.cloud.get_paths[-1])
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn(metadata_name, encoded_status)
                    self.assertNotIn("software_proof_docker_mobile_real_device_review_execution_gate", encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("terminal_ack", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)
                    self.assertNotIn("dropoff_success", encoded_status)
                    self.assertNotIn("cancel_completed", encoded_status)
                    self.assertNotIn("production_ready", encoded_status)
                    self.assertNotIn("production_app_ready", encoded_status)
                    self.assertNotIn("hil_pass", encoded_status)
                    self.assertNotIn("real_device_review_executed", encoded_status)
                    self.assertNotIn("/cmd_vel", encoded_status)
                    self.assertNotIn("/dev/ttyUSB0", encoded_status)
                    self.assertNotIn("Authorization", encoded_status)
                    self.assertNotIn("secret", encoded_status)
                    self.cloud.response_extras["command_response"] = {}

    def test_mobile_real_device_review_execution_metadata_is_ignored_by_valid_command_envelope(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                last_ack_id="cmd-before-real-device-review-execution",
                cursor_state_path=state_path,
            )
            self.cloud.response_extras.update({
                "status_response": {
                    "mobile_real_device_review_execution_summary": {
                        "schema": "trashbot.mobile_real_device_review_execution_summary.v1",
                        "evidence_boundary": "software_proof_docker_mobile_real_device_review_execution_gate",
                        "delivery_success": True,
                        "trigger_robot_action": "collect",
                    },
                },
                "command_response": {
                    "mobile_real_device_review_execution": {
                        "schema": "trashbot.mobile_real_device_review_execution.v1",
                        "evidence_boundary": "software_proof_docker_mobile_real_device_review_execution_gate",
                        "trigger_robot_action": "cancel",
                        "cursor_override": "cmd-real-device-review-execution-override",
                        "ack_semantics": "delivery_success",
                        "terminal_ack": "delivered",
                        "delivery_success": True,
                        "dropoff_success": True,
                        "raw_ros_topic": "/cmd_vel",
                    },
                    "mobile_real_device_review_execution_summary": {
                        "schema": "trashbot.mobile_real_device_review_execution_summary.v1",
                        "safe_phone_copy": "ACK 只代表 accepted/processing，不代表真实设备评审执行完成。",
                        "next_action": "confirm_dropoff",
                        "production_app_ready": True,
                        "real_device_review_executed": True,
                        "hil_pass": True,
                    },
                    "mobile_real_device_review_execution_package": {
                        "schema": "trashbot.mobile_real_device_review_execution_package.v1",
                        "support_refs": [{"kind": "review_execution", "url": "https://user:secret@example.invalid/review"}],
                        "Authorization": "Bearer must-not-leak",
                        "serial_device": "/dev/ttyUSB0",
                        "cancel_completed": True,
                    },
                },
                "ack_response": {
                    "mobile_real_device_review_execution_package": {
                        "schema": "trashbot.mobile_real_device_review_execution_package.v1",
                        "ack_semantics": "delivery_success",
                        "delivery_success": True,
                        "final_state": "DELIVERED",
                    },
                },
            })
            self.cloud.commands.append({
                "id": "cmd-real-device-review-execution-confirm",
                "type": "confirm_dropoff",
                "payload": {"accepted": True},
                "mobile_real_device_review_execution": {
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-future",
                    "delivery_success": True,
                },
            })

            self.assertTrue(worker.poll_once())

            self.assertEqual(self.backend.calls, [("confirm_dropoff", True)])
            self.assertEqual(worker.last_ack_id, "cmd-real-device-review-execution-confirm")
            self.assertIn("last_ack_id=cmd-before-real-device-review-execution", self.cloud.get_paths[-1])
            cursor_payload = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(cursor_payload["last_terminal_ack_id"], "cmd-real-device-review-execution-confirm")
            ack_payload = self.cloud.ack_posts[0]
            self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
            self.assertEqual(ack_payload["command_id"], "cmd-real-device-review-execution-confirm")
            self.assertEqual(ack_payload["state"], "acked")
            self.assertEqual(ack_payload["message"], "confirm_dropoff")
            encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
            # 有效 command 混入评审执行 metadata 时，执行、ACK、cursor 仍只跟随 command envelope。
            self.assertNotIn("mobile_real_device_review_execution", encoded_ack)
            self.assertNotIn("mobile_real_device_review_execution_summary", encoded_ack)
            self.assertNotIn("mobile_real_device_review_execution_package", encoded_ack)
            self.assertNotIn("software_proof_docker_mobile_real_device_review_execution_gate", encoded_ack)
            self.assertNotIn("trigger_robot_action", encoded_ack)
            self.assertNotIn("cursor_override", encoded_ack)
            self.assertNotIn("terminal_ack", encoded_ack)
            self.assertNotIn("delivery_success", encoded_ack)
            self.assertNotIn("dropoff_success", encoded_ack)
            self.assertNotIn("cancel_completed", encoded_ack)
            self.assertNotIn("production_app_ready", encoded_ack)
            self.assertNotIn("real_device_review_executed", encoded_ack)
            self.assertNotIn("hil_pass", encoded_ack)
            self.assertNotIn("/cmd_vel", encoded_ack)
            self.assertNotIn("/dev/ttyUSB0", encoded_ack)
            self.assertNotIn("Authorization", encoded_ack)
            self.assertNotIn("secret", encoded_ack)
            self.assertNotIn("DELIVERED", encoded_ack)
            encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
            self.assertNotIn("mobile_real_device_review_execution", encoded_status)
            self.assertNotIn("mobile_real_device_review_execution_summary", encoded_status)
            self.assertNotIn("mobile_real_device_review_execution_package", encoded_status)
            self.assertNotIn("software_proof_docker_mobile_real_device_review_execution_gate", encoded_status)
            self.assertNotIn("delivery_success", encoded_status)
            self.assertEqual(self.cloud.status_posts[-1]["state"], "returning")
            self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_mobile_real_device_retest_request_metadata_only_response_does_not_move_robot(self):
        metadata_cases = (
            (
                "mobile_real_device_retest_request",
                {
                    "schema": "trashbot.mobile_real_device_retest_request.v1",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_retest_request_gate",
                    "blocked_reason": "missing_real_device_materials",
                    "next_evidence_request": ["real_phone_video", "production_app_trace"],
                    "operator_notes": "retest request metadata must stay outside robot control",
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-real-device-retest-request",
                    "ack_semantics": "delivery_success",
                    "terminal_ack": "delivered",
                    "delivery_success": True,
                    "dropoff_success": True,
                    "cancel_completed": True,
                    "production_ready": True,
                    "hil_pass": True,
                    "raw_ros_topic": "/cmd_vel",
                },
            ),
            (
                "mobile_real_device_retest_request_summary",
                {
                    "schema": "trashbot.mobile_real_device_retest_request_summary.v1",
                    "safe_phone_copy": "复测请求只供产品和支持侧准备下一轮真实设备材料。",
                    "next_action": "confirm_dropoff",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_retest_request_gate",
                    "ready_for_retest": True,
                    "production_app_ready": True,
                    "cursor_override": "cmd-real-device-retest-request-summary",
                    "terminal_ack": "delivered",
                    "delivery_success": True,
                    "dropoff_success": True,
                },
            ),
            (
                "mobile_real_device_retest_request_package",
                {
                    "schema": "trashbot.mobile_real_device_retest_request_package.v1",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_retest_request_gate",
                    "support_refs": [{"kind": "retest_request", "url": "https://user:secret@example.invalid/retest"}],
                    "not_proven": ["production readiness", "HIL", "delivery success"],
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-real-device-retest-request-package",
                    "terminal_ack": "delivered",
                    "Authorization": "Bearer must-not-leak",
                    "serial_device": "/dev/ttyUSB0",
                    "cancel_completed": True,
                },
            ),
        )
        for metadata_name, metadata in metadata_cases:
            with self.subTest(metadata_name=metadata_name):
                self.cloud.status_posts.clear()
                self.cloud.ack_posts.clear()
                self.cloud.get_paths.clear()
                self.backend.calls.clear()
                self.cloud.response_extras["command_response"] = {metadata_name: metadata}
                with tempfile.TemporaryDirectory() as tmpdir:
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-{metadata_name}",
                        cursor_state_path=state_path,
                    )

                    handled = worker.poll_once()

                    # 复测请求 metadata-only 不能驱动 collect/dropoff/cancel、ACK、terminal ACK 或 cursor 持久化。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-{metadata_name}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    self.assertEqual(self.cloud.status_posts[-1]["state"], "waiting_for_trash")
                    self.assertNotIn(self.cloud.status_posts[-1]["state"], ("loaded_and_ready", "returning", "canceling", "completed"))
                    self.assertIn(f"last_ack_id=cmd-before-{metadata_name}", self.cloud.get_paths[-1])
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn(metadata_name, encoded_status)
                    self.assertNotIn("software_proof_docker_mobile_real_device_retest_request_gate", encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("terminal_ack", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)
                    self.assertNotIn("dropoff_success", encoded_status)
                    self.assertNotIn("cancel_completed", encoded_status)
                    self.assertNotIn("production_ready", encoded_status)
                    self.assertNotIn("production_app_ready", encoded_status)
                    self.assertNotIn("hil_pass", encoded_status)
                    self.assertNotIn("ready_for_retest", encoded_status)
                    self.assertNotIn("/cmd_vel", encoded_status)
                    self.assertNotIn("/dev/ttyUSB0", encoded_status)
                    self.assertNotIn("Authorization", encoded_status)
                    self.assertNotIn("secret", encoded_status)
                    self.cloud.response_extras["command_response"] = {}

    def test_mobile_real_device_retest_request_metadata_is_ignored_by_valid_command_envelope(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                last_ack_id="cmd-before-real-device-retest-request",
                cursor_state_path=state_path,
            )
            self.cloud.response_extras.update({
                "status_response": {
                    "mobile_real_device_retest_request_summary": {
                        "schema": "trashbot.mobile_real_device_retest_request_summary.v1",
                        "evidence_boundary": "software_proof_docker_mobile_real_device_retest_request_gate",
                        "delivery_success": True,
                        "trigger_robot_action": "collect",
                    },
                },
                "command_response": {
                    "mobile_real_device_retest_request": {
                        "schema": "trashbot.mobile_real_device_retest_request.v1",
                        "evidence_boundary": "software_proof_docker_mobile_real_device_retest_request_gate",
                        "trigger_robot_action": "cancel",
                        "cursor_override": "cmd-real-device-retest-request-override",
                        "ack_semantics": "delivery_success",
                        "terminal_ack": "delivered",
                        "delivery_success": True,
                        "dropoff_success": True,
                        "raw_ros_topic": "/cmd_vel",
                    },
                    "mobile_real_device_retest_request_summary": {
                        "schema": "trashbot.mobile_real_device_retest_request_summary.v1",
                        "safe_phone_copy": "ACK 只代表 accepted/processing，不代表复测请求完成真实送达。",
                        "next_action": "confirm_dropoff",
                        "production_app_ready": True,
                        "ready_for_retest": True,
                        "hil_pass": True,
                    },
                    "mobile_real_device_retest_request_package": {
                        "schema": "trashbot.mobile_real_device_retest_request_package.v1",
                        "support_refs": [{"kind": "retest_request", "url": "https://user:secret@example.invalid/retest"}],
                        "Authorization": "Bearer must-not-leak",
                        "serial_device": "/dev/ttyUSB0",
                        "cancel_completed": True,
                    },
                },
                "ack_response": {
                    "mobile_real_device_retest_request_package": {
                        "schema": "trashbot.mobile_real_device_retest_request_package.v1",
                        "ack_semantics": "delivery_success",
                        "delivery_success": True,
                        "final_state": "DELIVERED",
                    },
                },
            })
            self.cloud.commands.append({
                "id": "cmd-real-device-retest-request-cancel",
                "type": "cancel",
                "payload": {},
                "mobile_real_device_retest_request": {
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-future",
                    "delivery_success": True,
                },
            })

            self.assertTrue(worker.poll_once())

            self.assertEqual(self.backend.calls, [("cancel",)])
            self.assertEqual(worker.last_ack_id, "cmd-real-device-retest-request-cancel")
            self.assertIn("last_ack_id=cmd-before-real-device-retest-request", self.cloud.get_paths[-1])
            cursor_payload = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(cursor_payload["last_terminal_ack_id"], "cmd-real-device-retest-request-cancel")
            encoded_cursor = json.dumps(cursor_payload, ensure_ascii=False)
            self.assertNotIn("mobile_real_device_retest_request", encoded_cursor)
            self.assertNotIn("software_proof_docker_mobile_real_device_retest_request_gate", encoded_cursor)
            self.assertNotIn("delivery_success", encoded_cursor)
            ack_payload = self.cloud.ack_posts[0]
            self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
            self.assertEqual(ack_payload["command_id"], "cmd-real-device-retest-request-cancel")
            self.assertEqual(ack_payload["state"], "acked")
            self.assertEqual(ack_payload["message"], "cancel")
            encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
            # 有效 command 混入复测请求 metadata 时，执行、ACK、cursor 仍只跟随 command envelope。
            self.assertNotIn("mobile_real_device_retest_request", encoded_ack)
            self.assertNotIn("mobile_real_device_retest_request_summary", encoded_ack)
            self.assertNotIn("mobile_real_device_retest_request_package", encoded_ack)
            self.assertNotIn("software_proof_docker_mobile_real_device_retest_request_gate", encoded_ack)
            self.assertNotIn("trigger_robot_action", encoded_ack)
            self.assertNotIn("cursor_override", encoded_ack)
            self.assertNotIn("terminal_ack", encoded_ack)
            self.assertNotIn("delivery_success", encoded_ack)
            self.assertNotIn("dropoff_success", encoded_ack)
            self.assertNotIn("cancel_completed", encoded_ack)
            self.assertNotIn("production_app_ready", encoded_ack)
            self.assertNotIn("ready_for_retest", encoded_ack)
            self.assertNotIn("hil_pass", encoded_ack)
            self.assertNotIn("/cmd_vel", encoded_ack)
            self.assertNotIn("/dev/ttyUSB0", encoded_ack)
            self.assertNotIn("Authorization", encoded_ack)
            self.assertNotIn("secret", encoded_ack)
            self.assertNotIn("DELIVERED", encoded_ack)
            encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
            self.assertNotIn("mobile_real_device_retest_request", encoded_status)
            self.assertNotIn("mobile_real_device_retest_request_summary", encoded_status)
            self.assertNotIn("mobile_real_device_retest_request_package", encoded_status)
            self.assertNotIn("software_proof_docker_mobile_real_device_retest_request_gate", encoded_status)
            self.assertNotIn("delivery_success", encoded_status)
            self.assertEqual(self.cloud.status_posts[-1]["state"], "canceling")
            self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_mobile_real_device_field_trial_package_metadata_only_response_does_not_move_robot(self):
        metadata_cases = (
            (
                "mobile_real_device_field_trial_package",
                {
                    "schema": "trashbot.mobile_real_device_field_trial_package.v1",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_field_trial_package_gate",
                    "field_trial_state": "ready_for_handoff",
                    "operator_notes": "field trial package metadata must stay outside robot control",
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-real-device-field-trial-package",
                    "ack_semantics": "delivery_success",
                    "terminal_ack": "delivered",
                    "delivery_success": True,
                    "dropoff_success": True,
                    "cancel_completed": True,
                    "production_ready": True,
                    "hil_pass": True,
                    "raw_ros_topic": "/cmd_vel",
                },
            ),
            (
                "mobile_real_device_field_trial_package_summary",
                {
                    "schema": "trashbot.mobile_real_device_field_trial_package_summary.v1",
                    "safe_phone_copy": "现场试用包只供产品和支持侧准备真实设备试用。",
                    "next_action": "confirm_dropoff",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_field_trial_package_gate",
                    "real_device_field_trial_ready": True,
                    "production_app_ready": True,
                    "cursor_override": "cmd-real-device-field-trial-summary",
                    "terminal_ack": "delivered",
                    "delivery_success": True,
                    "dropoff_success": True,
                },
            ),
            (
                "mobile_real_device_field_trial_package_copy",
                {
                    "schema": "trashbot.mobile_real_device_field_trial_package_copy.v1",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_field_trial_package_gate",
                    "support_refs": [{"kind": "field_trial", "url": "https://user:secret@example.invalid/field-trial"}],
                    "not_proven": ["production readiness", "HIL", "delivery success"],
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-real-device-field-trial-copy",
                    "terminal_ack": "delivered",
                    "Authorization": "Bearer must-not-leak",
                    "serial_device": "/dev/ttyUSB0",
                    "cancel_completed": True,
                },
            ),
        )
        for metadata_name, metadata in metadata_cases:
            with self.subTest(metadata_name=metadata_name):
                self.cloud.status_posts.clear()
                self.cloud.ack_posts.clear()
                self.cloud.get_paths.clear()
                self.backend.calls.clear()
                self.cloud.response_extras["command_response"] = {metadata_name: metadata}
                with tempfile.TemporaryDirectory() as tmpdir:
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-{metadata_name}",
                        cursor_state_path=state_path,
                    )

                    handled = worker.poll_once()

                    # 现场试用包 metadata-only 不能驱动 collect/dropoff/cancel、ACK、terminal ACK 或 cursor 持久化。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-{metadata_name}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    self.assertEqual(self.cloud.status_posts[-1]["state"], "waiting_for_trash")
                    self.assertNotIn(self.cloud.status_posts[-1]["state"], ("loaded_and_ready", "returning", "canceling", "completed"))
                    self.assertIn(f"last_ack_id=cmd-before-{metadata_name}", self.cloud.get_paths[-1])
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn(metadata_name, encoded_status)
                    self.assertNotIn("software_proof_docker_mobile_real_device_field_trial_package_gate", encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("terminal_ack", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)
                    self.assertNotIn("dropoff_success", encoded_status)
                    self.assertNotIn("cancel_completed", encoded_status)
                    self.assertNotIn("production_ready", encoded_status)
                    self.assertNotIn("production_app_ready", encoded_status)
                    self.assertNotIn("hil_pass", encoded_status)
                    self.assertNotIn("real_device_field_trial_ready", encoded_status)
                    self.assertNotIn("/cmd_vel", encoded_status)
                    self.assertNotIn("/dev/ttyUSB0", encoded_status)
                    self.assertNotIn("Authorization", encoded_status)
                    self.assertNotIn("secret", encoded_status)
                    self.cloud.response_extras["command_response"] = {}

    def test_mobile_real_device_field_trial_package_metadata_is_ignored_by_valid_command_envelope(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                last_ack_id="cmd-before-real-device-field-trial",
                cursor_state_path=state_path,
            )
            self.cloud.response_extras.update({
                "status_response": {
                    "mobile_real_device_field_trial_package_summary": {
                        "schema": "trashbot.mobile_real_device_field_trial_package_summary.v1",
                        "evidence_boundary": "software_proof_docker_mobile_real_device_field_trial_package_gate",
                        "delivery_success": True,
                        "trigger_robot_action": "collect",
                    },
                },
                "command_response": {
                    "mobile_real_device_field_trial_package": {
                        "schema": "trashbot.mobile_real_device_field_trial_package.v1",
                        "evidence_boundary": "software_proof_docker_mobile_real_device_field_trial_package_gate",
                        "trigger_robot_action": "cancel",
                        "cursor_override": "cmd-real-device-field-trial-override",
                        "ack_semantics": "delivery_success",
                        "terminal_ack": "delivered",
                        "delivery_success": True,
                        "dropoff_success": True,
                        "raw_ros_topic": "/cmd_vel",
                    },
                    "mobile_real_device_field_trial_package_summary": {
                        "schema": "trashbot.mobile_real_device_field_trial_package_summary.v1",
                        "safe_phone_copy": "ACK 只代表 accepted/processing，不代表现场试用完成真实送达。",
                        "next_action": "confirm_dropoff",
                        "production_app_ready": True,
                        "real_device_field_trial_ready": True,
                        "hil_pass": True,
                    },
                    "mobile_real_device_field_trial_package_copy": {
                        "schema": "trashbot.mobile_real_device_field_trial_package_copy.v1",
                        "support_refs": [{"kind": "field_trial", "url": "https://user:secret@example.invalid/field-trial"}],
                        "Authorization": "Bearer must-not-leak",
                        "serial_device": "/dev/ttyUSB0",
                        "cancel_completed": True,
                    },
                },
                "ack_response": {
                    "mobile_real_device_field_trial_package_copy": {
                        "schema": "trashbot.mobile_real_device_field_trial_package_copy.v1",
                        "ack_semantics": "delivery_success",
                        "delivery_success": True,
                        "final_state": "DELIVERED",
                    },
                },
            })
            self.cloud.commands.append({
                "id": "cmd-real-device-field-trial-confirm",
                "type": "confirm_dropoff",
                "payload": {"accepted": False},
                "mobile_real_device_field_trial_package": {
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-future",
                    "delivery_success": True,
                },
            })

            self.assertTrue(worker.poll_once())

            self.assertEqual(self.backend.calls, [("confirm_dropoff", False)])
            self.assertEqual(worker.last_ack_id, "cmd-real-device-field-trial-confirm")
            self.assertIn("last_ack_id=cmd-before-real-device-field-trial", self.cloud.get_paths[-1])
            cursor_payload = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(cursor_payload["last_terminal_ack_id"], "cmd-real-device-field-trial-confirm")
            encoded_cursor = json.dumps(cursor_payload, ensure_ascii=False)
            self.assertNotIn("mobile_real_device_field_trial_package", encoded_cursor)
            self.assertNotIn("software_proof_docker_mobile_real_device_field_trial_package_gate", encoded_cursor)
            self.assertNotIn("delivery_success", encoded_cursor)
            ack_payload = self.cloud.ack_posts[0]
            self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
            self.assertEqual(ack_payload["command_id"], "cmd-real-device-field-trial-confirm")
            self.assertEqual(ack_payload["state"], "acked")
            self.assertEqual(ack_payload["message"], "confirm_dropoff")
            encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
            # 有效 command 混入现场试用包 metadata 时，执行、ACK、cursor 仍只跟随 command envelope。
            self.assertNotIn("mobile_real_device_field_trial_package", encoded_ack)
            self.assertNotIn("mobile_real_device_field_trial_package_summary", encoded_ack)
            self.assertNotIn("mobile_real_device_field_trial_package_copy", encoded_ack)
            self.assertNotIn("software_proof_docker_mobile_real_device_field_trial_package_gate", encoded_ack)
            self.assertNotIn("trigger_robot_action", encoded_ack)
            self.assertNotIn("cursor_override", encoded_ack)
            self.assertNotIn("terminal_ack", encoded_ack)
            self.assertNotIn("delivery_success", encoded_ack)
            self.assertNotIn("dropoff_success", encoded_ack)
            self.assertNotIn("cancel_completed", encoded_ack)
            self.assertNotIn("production_app_ready", encoded_ack)
            self.assertNotIn("real_device_field_trial_ready", encoded_ack)
            self.assertNotIn("hil_pass", encoded_ack)
            self.assertNotIn("/cmd_vel", encoded_ack)
            self.assertNotIn("/dev/ttyUSB0", encoded_ack)
            self.assertNotIn("Authorization", encoded_ack)
            self.assertNotIn("secret", encoded_ack)
            self.assertNotIn("DELIVERED", encoded_ack)
            encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
            self.assertNotIn("mobile_real_device_field_trial_package", encoded_status)
            self.assertNotIn("mobile_real_device_field_trial_package_summary", encoded_status)
            self.assertNotIn("mobile_real_device_field_trial_package_copy", encoded_status)
            self.assertNotIn("software_proof_docker_mobile_real_device_field_trial_package_gate", encoded_status)
            self.assertNotIn("delivery_success", encoded_status)
            self.assertEqual(self.cloud.status_posts[-1]["state"], "returning")
            self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_mobile_real_device_field_trial_review_metadata_only_response_does_not_move_robot(self):
        metadata_cases = (
            (
                "mobile_real_device_field_trial_review",
                {
                    "schema": "trashbot.mobile_real_device_field_trial_review.v1",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_field_trial_review_gate",
                    "review_status": "blocked_missing_materials",
                    "safe_to_control": False,
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-real-device-field-trial-review",
                    "ack_semantics": "delivery_success",
                    "terminal_ack": "delivered",
                    "delivery_success": True,
                    "dropoff_success": True,
                    "cancel_completed": True,
                    "production_ready": True,
                    "hil_pass": True,
                    "raw_ros_topic": "/cmd_vel",
                },
            ),
            (
                "mobile_real_device_field_trial_review_summary",
                {
                    "schema": "trashbot.mobile_real_device_field_trial_review_summary.v1",
                    "safe_phone_copy": "现场试跑复核只供产品和支持确认材料状态。",
                    "next_action": "confirm_dropoff",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_field_trial_review_gate",
                    "real_device_field_trial_reviewed": True,
                    "production_app_ready": True,
                    "cursor_override": "cmd-real-device-field-trial-review-summary",
                    "terminal_ack": "delivered",
                    "delivery_success": True,
                    "dropoff_success": True,
                },
            ),
            (
                "mobile_real_device_field_trial_review_copy",
                {
                    "schema": "trashbot.mobile_real_device_field_trial_review_copy.v1",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_field_trial_review_gate",
                    "support_refs": [{"kind": "field_trial_review", "url": "https://user:secret@example.invalid/review"}],
                    "not_proven": ["production readiness", "HIL", "delivery success"],
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-real-device-field-trial-review-copy",
                    "terminal_ack": "delivered",
                    "Authorization": "Bearer must-not-leak",
                    "serial_device": "/dev/ttyUSB0",
                    "cancel_completed": True,
                },
            ),
        )
        for metadata_name, metadata in metadata_cases:
            with self.subTest(metadata_name=metadata_name):
                self.cloud.status_posts.clear()
                self.cloud.ack_posts.clear()
                self.cloud.get_paths.clear()
                self.backend.calls.clear()
                self.cloud.response_extras["command_response"] = {metadata_name: metadata}
                with tempfile.TemporaryDirectory() as tmpdir:
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-{metadata_name}",
                        cursor_state_path=state_path,
                    )

                    handled = worker.poll_once()

                    # 现场试跑复核 metadata-only 不能驱动 collect/dropoff/cancel、ACK、terminal ACK 或 cursor 持久化。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-{metadata_name}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    self.assertEqual(self.cloud.status_posts[-1]["state"], "waiting_for_trash")
                    self.assertNotIn(self.cloud.status_posts[-1]["state"], ("loaded_and_ready", "returning", "canceling", "completed"))
                    self.assertIn(f"last_ack_id=cmd-before-{metadata_name}", self.cloud.get_paths[-1])
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn(metadata_name, encoded_status)
                    self.assertNotIn("software_proof_docker_mobile_real_device_field_trial_review_gate", encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("terminal_ack", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)
                    self.assertNotIn("dropoff_success", encoded_status)
                    self.assertNotIn("cancel_completed", encoded_status)
                    self.assertNotIn("production_ready", encoded_status)
                    self.assertNotIn("production_app_ready", encoded_status)
                    self.assertNotIn("hil_pass", encoded_status)
                    self.assertNotIn("real_device_field_trial_reviewed", encoded_status)
                    self.assertNotIn("/cmd_vel", encoded_status)
                    self.assertNotIn("/dev/ttyUSB0", encoded_status)
                    self.assertNotIn("Authorization", encoded_status)
                    self.assertNotIn("secret", encoded_status)
                    self.cloud.response_extras["command_response"] = {}

    def test_mobile_real_device_field_trial_review_metadata_is_ignored_by_valid_command_envelope(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                last_ack_id="cmd-before-real-device-field-trial-review",
                cursor_state_path=state_path,
            )
            self.cloud.response_extras.update({
                "status_response": {
                    "mobile_real_device_field_trial_review_summary": {
                        "schema": "trashbot.mobile_real_device_field_trial_review_summary.v1",
                        "evidence_boundary": "software_proof_docker_mobile_real_device_field_trial_review_gate",
                        "delivery_success": True,
                        "trigger_robot_action": "collect",
                    },
                },
                "command_response": {
                    "mobile_real_device_field_trial_review": {
                        "schema": "trashbot.mobile_real_device_field_trial_review.v1",
                        "evidence_boundary": "software_proof_docker_mobile_real_device_field_trial_review_gate",
                        "trigger_robot_action": "cancel",
                        "cursor_override": "cmd-real-device-field-trial-review-override",
                        "ack_semantics": "delivery_success",
                        "terminal_ack": "delivered",
                        "delivery_success": True,
                        "dropoff_success": True,
                        "raw_ros_topic": "/cmd_vel",
                    },
                    "mobile_real_device_field_trial_review_summary": {
                        "schema": "trashbot.mobile_real_device_field_trial_review_summary.v1",
                        "safe_phone_copy": "ACK 只代表 accepted/processing，不代表现场试跑复核完成真实送达。",
                        "next_action": "confirm_dropoff",
                        "production_app_ready": True,
                        "real_device_field_trial_reviewed": True,
                        "hil_pass": True,
                    },
                    "mobile_real_device_field_trial_review_copy": {
                        "schema": "trashbot.mobile_real_device_field_trial_review_copy.v1",
                        "support_refs": [{"kind": "field_trial_review", "url": "https://user:secret@example.invalid/review"}],
                        "Authorization": "Bearer must-not-leak",
                        "serial_device": "/dev/ttyUSB0",
                        "cancel_completed": True,
                    },
                },
                "ack_response": {
                    "mobile_real_device_field_trial_review_copy": {
                        "schema": "trashbot.mobile_real_device_field_trial_review_copy.v1",
                        "ack_semantics": "delivery_success",
                        "delivery_success": True,
                        "final_state": "DELIVERED",
                    },
                },
            })
            self.cloud.commands.append({
                "id": "cmd-real-device-field-trial-review-collect",
                "type": "collect",
                "payload": {"target": "trash_station", "trash_type": 0},
                "mobile_real_device_field_trial_review": {
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-future",
                    "delivery_success": True,
                },
            })

            self.assertTrue(worker.poll_once())

            self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
            self.assertEqual(worker.last_ack_id, "cmd-real-device-field-trial-review-collect")
            self.assertIn("last_ack_id=cmd-before-real-device-field-trial-review", self.cloud.get_paths[-1])
            cursor_payload = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(cursor_payload["last_terminal_ack_id"], "cmd-real-device-field-trial-review-collect")
            encoded_cursor = json.dumps(cursor_payload, ensure_ascii=False)
            self.assertNotIn("mobile_real_device_field_trial_review", encoded_cursor)
            self.assertNotIn("software_proof_docker_mobile_real_device_field_trial_review_gate", encoded_cursor)
            self.assertNotIn("delivery_success", encoded_cursor)
            ack_payload = self.cloud.ack_posts[0]
            self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
            self.assertEqual(ack_payload["command_id"], "cmd-real-device-field-trial-review-collect")
            self.assertEqual(ack_payload["state"], "acked")
            self.assertEqual(ack_payload["message"], "collect")
            encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
            # 有效 command 混入现场试跑复核 metadata 时，执行、ACK、cursor 仍只跟随 command envelope。
            self.assertNotIn("mobile_real_device_field_trial_review", encoded_ack)
            self.assertNotIn("mobile_real_device_field_trial_review_summary", encoded_ack)
            self.assertNotIn("mobile_real_device_field_trial_review_copy", encoded_ack)
            self.assertNotIn("software_proof_docker_mobile_real_device_field_trial_review_gate", encoded_ack)
            self.assertNotIn("trigger_robot_action", encoded_ack)
            self.assertNotIn("cursor_override", encoded_ack)
            self.assertNotIn("terminal_ack", encoded_ack)
            self.assertNotIn("delivery_success", encoded_ack)
            self.assertNotIn("dropoff_success", encoded_ack)
            self.assertNotIn("cancel_completed", encoded_ack)
            self.assertNotIn("production_app_ready", encoded_ack)
            self.assertNotIn("real_device_field_trial_reviewed", encoded_ack)
            self.assertNotIn("hil_pass", encoded_ack)
            self.assertNotIn("/cmd_vel", encoded_ack)
            self.assertNotIn("/dev/ttyUSB0", encoded_ack)
            self.assertNotIn("Authorization", encoded_ack)
            self.assertNotIn("secret", encoded_ack)
            self.assertNotIn("DELIVERED", encoded_ack)
            encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
            self.assertNotIn("mobile_real_device_field_trial_review", encoded_status)
            self.assertNotIn("mobile_real_device_field_trial_review_summary", encoded_status)
            self.assertNotIn("mobile_real_device_field_trial_review_copy", encoded_status)
            self.assertNotIn("software_proof_docker_mobile_real_device_field_trial_review_gate", encoded_status)
            self.assertNotIn("delivery_success", encoded_status)
            self.assertEqual(self.cloud.status_posts[-1]["state"], "loaded_and_ready")
            self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_mobile_real_device_field_trial_runbook_execution_metadata_only_response_does_not_move_robot(self):
        metadata_cases = (
            (
                "mobile_real_device_field_trial_runbook_execution",
                {
                    "schema": "trashbot.mobile_real_device_field_trial_runbook_execution.v1",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_field_trial_runbook_execution_gate",
                    "runbook_step": "operator_start_check",
                    "safe_to_control": False,
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-runbook-execution",
                    "ack_semantics": "delivery_success",
                    "terminal_ack": "delivered",
                    "delivery_success": True,
                    "dropoff_success": True,
                    "cancel_completed": True,
                    "production_ready": True,
                    "hil_pass": True,
                    "raw_ros_topic": "/cmd_vel",
                },
            ),
            (
                "mobile_real_device_field_trial_runbook_execution_summary",
                {
                    "schema": "trashbot.mobile_real_device_field_trial_runbook_execution_summary.v1",
                    "safe_phone_copy": "现场试跑 runbook 执行记录只供支持侧复盘。",
                    "next_action": "confirm_dropoff",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_field_trial_runbook_execution_gate",
                    "runbook_execution_recorded": True,
                    "production_app_ready": True,
                    "cursor_override": "cmd-runbook-execution-summary",
                    "terminal_ack": "delivered",
                    "delivery_success": True,
                    "dropoff_success": True,
                },
            ),
            (
                "mobile_real_device_field_trial_runbook_execution_copy",
                {
                    "schema": "trashbot.mobile_real_device_field_trial_runbook_execution_copy.v1",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_field_trial_runbook_execution_gate",
                    "support_refs": [{"kind": "runbook_execution", "url": "https://user:secret@example.invalid/runbook"}],
                    "not_proven": ["production readiness", "HIL", "delivery success"],
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-runbook-execution-copy",
                    "terminal_ack": "delivered",
                    "Authorization": "Bearer must-not-leak",
                    "serial_device": "/dev/ttyUSB0",
                    "cancel_completed": True,
                },
            ),
        )
        for metadata_name, metadata in metadata_cases:
            with self.subTest(metadata_name=metadata_name):
                self.cloud.status_posts.clear()
                self.cloud.ack_posts.clear()
                self.cloud.get_paths.clear()
                self.backend.calls.clear()
                self.cloud.response_extras["command_response"] = {metadata_name: metadata}
                with tempfile.TemporaryDirectory() as tmpdir:
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-{metadata_name}",
                        cursor_state_path=state_path,
                    )

                    handled = worker.poll_once()

                    # runbook 执行 metadata-only 只能作为手机/支持证据，不能驱动 command、ACK 或 cursor。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-{metadata_name}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    self.assertEqual(self.cloud.status_posts[-1]["state"], "waiting_for_trash")
                    self.assertNotIn(self.cloud.status_posts[-1]["state"], ("loaded_and_ready", "returning", "canceling", "completed"))
                    self.assertIn(f"last_ack_id=cmd-before-{metadata_name}", self.cloud.get_paths[-1])
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn(metadata_name, encoded_status)
                    self.assertNotIn("software_proof_docker_mobile_real_device_field_trial_runbook_execution_gate", encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("terminal_ack", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)
                    self.assertNotIn("dropoff_success", encoded_status)
                    self.assertNotIn("cancel_completed", encoded_status)
                    self.assertNotIn("production_ready", encoded_status)
                    self.assertNotIn("production_app_ready", encoded_status)
                    self.assertNotIn("hil_pass", encoded_status)
                    self.assertNotIn("runbook_execution_recorded", encoded_status)
                    self.assertNotIn("/cmd_vel", encoded_status)
                    self.assertNotIn("/dev/ttyUSB0", encoded_status)
                    self.assertNotIn("Authorization", encoded_status)
                    self.assertNotIn("secret", encoded_status)
                    self.cloud.response_extras["command_response"] = {}

    def test_mobile_real_device_field_trial_runbook_execution_metadata_is_ignored_by_valid_command_envelope(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                last_ack_id="cmd-before-real-device-field-trial-runbook-execution",
                cursor_state_path=state_path,
            )
            self.cloud.response_extras.update({
                "status_response": {
                    "mobile_real_device_field_trial_runbook_execution_summary": {
                        "schema": "trashbot.mobile_real_device_field_trial_runbook_execution_summary.v1",
                        "evidence_boundary": "software_proof_docker_mobile_real_device_field_trial_runbook_execution_gate",
                        "delivery_success": True,
                        "trigger_robot_action": "collect",
                    },
                },
                "command_response": {
                    "mobile_real_device_field_trial_runbook_execution": {
                        "schema": "trashbot.mobile_real_device_field_trial_runbook_execution.v1",
                        "evidence_boundary": "software_proof_docker_mobile_real_device_field_trial_runbook_execution_gate",
                        "trigger_robot_action": "cancel",
                        "cursor_override": "cmd-runbook-execution-override",
                        "ack_semantics": "delivery_success",
                        "terminal_ack": "delivered",
                        "delivery_success": True,
                        "dropoff_success": True,
                        "raw_ros_topic": "/cmd_vel",
                    },
                    "mobile_real_device_field_trial_runbook_execution_summary": {
                        "schema": "trashbot.mobile_real_device_field_trial_runbook_execution_summary.v1",
                        "safe_phone_copy": "ACK 只代表 accepted_processing_only_not_delivery_success，不代表 runbook 执行完成真实送达。",
                        "next_action": "confirm_dropoff",
                        "production_app_ready": True,
                        "runbook_execution_recorded": True,
                        "hil_pass": True,
                    },
                    "mobile_real_device_field_trial_runbook_execution_copy": {
                        "schema": "trashbot.mobile_real_device_field_trial_runbook_execution_copy.v1",
                        "support_refs": [{"kind": "runbook_execution", "url": "https://user:secret@example.invalid/runbook"}],
                        "Authorization": "Bearer must-not-leak",
                        "serial_device": "/dev/ttyUSB0",
                        "cancel_completed": True,
                    },
                },
                "ack_response": {
                    "mobile_real_device_field_trial_runbook_execution_copy": {
                        "schema": "trashbot.mobile_real_device_field_trial_runbook_execution_copy.v1",
                        "ack_semantics": "delivery_success",
                        "delivery_success": True,
                        "final_state": "DELIVERED",
                    },
                },
            })
            self.cloud.commands.append({
                "id": "cmd-real-device-field-trial-runbook-execution-cancel",
                "type": "cancel",
                "payload": {},
                "mobile_real_device_field_trial_runbook_execution": {
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-future",
                    "delivery_success": True,
                },
            })

            self.assertTrue(worker.poll_once())

            self.assertEqual(self.backend.calls, [("cancel",)])
            self.assertEqual(worker.last_ack_id, "cmd-real-device-field-trial-runbook-execution-cancel")
            self.assertIn("last_ack_id=cmd-before-real-device-field-trial-runbook-execution", self.cloud.get_paths[-1])
            cursor_payload = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(cursor_payload["last_terminal_ack_id"], "cmd-real-device-field-trial-runbook-execution-cancel")
            encoded_cursor = json.dumps(cursor_payload, ensure_ascii=False)
            self.assertNotIn("mobile_real_device_field_trial_runbook_execution", encoded_cursor)
            self.assertNotIn("software_proof_docker_mobile_real_device_field_trial_runbook_execution_gate", encoded_cursor)
            self.assertNotIn("delivery_success", encoded_cursor)
            ack_payload = self.cloud.ack_posts[0]
            self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
            self.assertEqual(ack_payload["command_id"], "cmd-real-device-field-trial-runbook-execution-cancel")
            self.assertEqual(ack_payload["state"], "acked")
            self.assertEqual(ack_payload["message"], "cancel")
            encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
            # 有效 command 混入 runbook 执行 metadata 时，执行、ACK、cursor 仍只跟随 command envelope。
            self.assertNotIn("mobile_real_device_field_trial_runbook_execution", encoded_ack)
            self.assertNotIn("mobile_real_device_field_trial_runbook_execution_summary", encoded_ack)
            self.assertNotIn("mobile_real_device_field_trial_runbook_execution_copy", encoded_ack)
            self.assertNotIn("software_proof_docker_mobile_real_device_field_trial_runbook_execution_gate", encoded_ack)
            self.assertNotIn("trigger_robot_action", encoded_ack)
            self.assertNotIn("cursor_override", encoded_ack)
            self.assertNotIn("terminal_ack", encoded_ack)
            self.assertNotIn("delivery_success", encoded_ack)
            self.assertNotIn("dropoff_success", encoded_ack)
            self.assertNotIn("cancel_completed", encoded_ack)
            self.assertNotIn("production_app_ready", encoded_ack)
            self.assertNotIn("runbook_execution_recorded", encoded_ack)
            self.assertNotIn("hil_pass", encoded_ack)
            self.assertNotIn("/cmd_vel", encoded_ack)
            self.assertNotIn("/dev/ttyUSB0", encoded_ack)
            self.assertNotIn("Authorization", encoded_ack)
            self.assertNotIn("secret", encoded_ack)
            self.assertNotIn("DELIVERED", encoded_ack)
            encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
            self.assertNotIn("mobile_real_device_field_trial_runbook_execution", encoded_status)
            self.assertNotIn("mobile_real_device_field_trial_runbook_execution_summary", encoded_status)
            self.assertNotIn("mobile_real_device_field_trial_runbook_execution_copy", encoded_status)
            self.assertNotIn("software_proof_docker_mobile_real_device_field_trial_runbook_execution_gate", encoded_status)
            self.assertNotIn("delivery_success", encoded_status)
            self.assertEqual(self.cloud.status_posts[-1]["state"], "canceling")
            self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_mobile_real_device_field_trial_retest_execution_metadata_only_response_does_not_move_robot(self):
        metadata_cases = (
            (
                "mobile_real_device_field_trial_retest_execution",
                {
                    "schema": "trashbot.mobile_real_device_field_trial_retest_execution.v1",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_field_trial_retest_execution_gate",
                    "retest_step": "operator_repeat_start_check",
                    "safe_to_control": False,
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-field-trial-retest-execution",
                    "ack_semantics": "delivery_success",
                    "terminal_ack": "delivered",
                    "delivery_success": True,
                    "dropoff_success": True,
                    "cancel_completed": True,
                    "production_ready": True,
                    "hil_pass": True,
                    "raw_ros_topic": "/cmd_vel",
                },
            ),
            (
                "mobile_real_device_field_trial_retest_execution_summary",
                {
                    "schema": "trashbot.mobile_real_device_field_trial_retest_execution_summary.v1",
                    "safe_phone_copy": "现场复测执行记录只供手机和支持侧复核。",
                    "next_action": "confirm_dropoff",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_field_trial_retest_execution_gate",
                    "field_trial_retest_executed": True,
                    "production_app_ready": True,
                    "cursor_override": "cmd-field-trial-retest-summary",
                    "terminal_ack": "delivered",
                    "delivery_success": True,
                    "dropoff_success": True,
                },
            ),
            (
                "mobile_real_device_field_trial_retest_execution_copy",
                {
                    "schema": "trashbot.mobile_real_device_field_trial_retest_execution_copy.v1",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_field_trial_retest_execution_gate",
                    "support_refs": [{"kind": "field_trial_retest", "url": "https://user:secret@example.invalid/retest"}],
                    "not_proven": ["production readiness", "HIL", "delivery success"],
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-field-trial-retest-copy",
                    "terminal_ack": "delivered",
                    "Authorization": "Bearer must-not-leak",
                    "serial_device": "/dev/ttyUSB0",
                    "cancel_completed": True,
                },
            ),
        )
        for metadata_name, metadata in metadata_cases:
            with self.subTest(metadata_name=metadata_name):
                self.cloud.status_posts.clear()
                self.cloud.ack_posts.clear()
                self.cloud.get_paths.clear()
                self.backend.calls.clear()
                self.cloud.response_extras["command_response"] = {metadata_name: metadata}
                with tempfile.TemporaryDirectory() as tmpdir:
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-{metadata_name}",
                        cursor_state_path=state_path,
                    )

                    handled = worker.poll_once()

                    # 现场复测执行 metadata-only 只做手机/支持留痕，不能触发控制、ACK 或游标推进。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-{metadata_name}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    self.assertEqual(self.cloud.status_posts[-1]["state"], "waiting_for_trash")
                    self.assertNotIn(self.cloud.status_posts[-1]["state"], ("loaded_and_ready", "returning", "canceling", "completed"))
                    self.assertIn(f"last_ack_id=cmd-before-{metadata_name}", self.cloud.get_paths[-1])
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn(metadata_name, encoded_status)
                    self.assertNotIn("software_proof_docker_mobile_real_device_field_trial_retest_execution_gate", encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("terminal_ack", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)
                    self.assertNotIn("dropoff_success", encoded_status)
                    self.assertNotIn("cancel_completed", encoded_status)
                    self.assertNotIn("production_ready", encoded_status)
                    self.assertNotIn("production_app_ready", encoded_status)
                    self.assertNotIn("hil_pass", encoded_status)
                    self.assertNotIn("field_trial_retest_executed", encoded_status)
                    self.assertNotIn("/cmd_vel", encoded_status)
                    self.assertNotIn("/dev/ttyUSB0", encoded_status)
                    self.assertNotIn("Authorization", encoded_status)
                    self.assertNotIn("secret", encoded_status)
                    self.cloud.response_extras["command_response"] = {}

    def test_mobile_real_device_field_trial_evidence_record_metadata_only_response_does_not_move_robot(self):
        metadata_cases = (
            (
                "mobile_real_device_field_trial_evidence_record",
                {
                    "schema": "trashbot.mobile_real_device_field_trial_evidence_record.v1",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_field_trial_evidence_record_gate",
                    "record_state": "drafted",
                    "safe_to_control": False,
                    "ack_semantics": "accepted_processing_only_not_delivery_success",
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-field-trial-record",
                    "terminal_ack": "delivered",
                    "delivery_success": True,
                    "dropoff_success": True,
                    "cancel_completed": True,
                    "production_ready": True,
                    "hil_pass": True,
                    "raw_ros_topic": "/cmd_vel",
                },
            ),
            (
                "mobile_real_device_field_trial_evidence_record_summary",
                {
                    "schema": "trashbot.mobile_real_device_field_trial_evidence_record_summary.v1",
                    "safe_phone_copy": "现场证据记录只供支持侧留痕，ACK 不是送达成功。",
                    "next_action": "confirm_dropoff",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_field_trial_evidence_record_gate",
                    "field_trial_evidence_recorded": True,
                    "production_app_ready": True,
                    "cursor_override": "cmd-field-trial-record-summary",
                    "terminal_ack": "delivered",
                    "delivery_success": True,
                    "dropoff_success": True,
                },
            ),
            (
                "mobile_real_device_field_trial_evidence_record_copy",
                {
                    "schema": "trashbot.mobile_real_device_field_trial_evidence_record_copy.v1",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_field_trial_evidence_record_gate",
                    "support_refs": [{"kind": "field_trial_record", "url": "https://user:secret@example.invalid/record"}],
                    "not_proven": ["production readiness", "HIL", "delivery success"],
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-field-trial-record-copy",
                    "terminal_ack": "delivered",
                    "Authorization": "Bearer must-not-leak",
                    "serial_device": "/dev/ttyUSB0",
                    "cancel_completed": True,
                },
            ),
            (
                "mobile_real_device_field_trial_evidence_record_archive",
                {
                    "schema": "trashbot.mobile_real_device_field_trial_evidence_record_archive.v1",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_field_trial_evidence_record_gate",
                    "archive_status": "saved",
                    "trigger_robot_action": "confirm_dropoff",
                    "cursor_override": "cmd-field-trial-record-archive",
                    "delivery_success": True,
                    "production_ready": True,
                    "hil_pass": True,
                },
            ),
        )
        for metadata_name, metadata in metadata_cases:
            with self.subTest(metadata_name=metadata_name):
                self.cloud.status_posts.clear()
                self.cloud.ack_posts.clear()
                self.cloud.get_paths.clear()
                self.backend.calls.clear()
                self.cloud.response_extras["command_response"] = {metadata_name: metadata}
                with tempfile.TemporaryDirectory() as tmpdir:
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-{metadata_name}",
                        cursor_state_path=state_path,
                    )

                    handled = worker.poll_once()

                    # 现场证据记录 metadata-only 只能作为手机/支持留痕，不能驱动 command、ACK、terminal ACK 或 cursor。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-{metadata_name}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    self.assertEqual(self.cloud.status_posts[-1]["state"], "waiting_for_trash")
                    self.assertNotIn(self.cloud.status_posts[-1]["state"], ("loaded_and_ready", "returning", "canceling", "completed"))
                    self.assertIn(f"last_ack_id=cmd-before-{metadata_name}", self.cloud.get_paths[-1])
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn(metadata_name, encoded_status)
                    self.assertNotIn("software_proof_docker_mobile_real_device_field_trial_evidence_record_gate", encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("terminal_ack", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)
                    self.assertNotIn("dropoff_success", encoded_status)
                    self.assertNotIn("cancel_completed", encoded_status)
                    self.assertNotIn("production_ready", encoded_status)
                    self.assertNotIn("production_app_ready", encoded_status)
                    self.assertNotIn("hil_pass", encoded_status)
                    self.assertNotIn("field_trial_evidence_recorded", encoded_status)
                    self.assertNotIn("/cmd_vel", encoded_status)
                    self.assertNotIn("/dev/ttyUSB0", encoded_status)
                    self.assertNotIn("Authorization", encoded_status)
                    self.assertNotIn("secret", encoded_status)
                    self.cloud.response_extras["command_response"] = {}

    def test_mobile_real_device_field_trial_evidence_record_metadata_is_ignored_by_valid_command_envelope(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                last_ack_id="cmd-before-real-device-field-trial-evidence-record",
                cursor_state_path=state_path,
            )
            self.cloud.response_extras.update({
                "status_response": {
                    "mobile_real_device_field_trial_evidence_record_summary": {
                        "schema": "trashbot.mobile_real_device_field_trial_evidence_record_summary.v1",
                        "evidence_boundary": "software_proof_docker_mobile_real_device_field_trial_evidence_record_gate",
                        "delivery_success": True,
                        "trigger_robot_action": "collect",
                    },
                },
                "command_response": {
                    "mobile_real_device_field_trial_evidence_record": {
                        "schema": "trashbot.mobile_real_device_field_trial_evidence_record.v1",
                        "evidence_boundary": "software_proof_docker_mobile_real_device_field_trial_evidence_record_gate",
                        "trigger_robot_action": "cancel",
                        "cursor_override": "cmd-field-trial-record-override",
                        "ack_semantics": "delivery_success",
                        "terminal_ack": "delivered",
                        "delivery_success": True,
                        "dropoff_success": True,
                        "raw_ros_topic": "/cmd_vel",
                    },
                    "mobile_real_device_field_trial_evidence_record_summary": {
                        "schema": "trashbot.mobile_real_device_field_trial_evidence_record_summary.v1",
                        "safe_phone_copy": "ACK 只代表 accepted_processing_only_not_delivery_success，不代表现场证据记录完成真实送达。",
                        "next_action": "confirm_dropoff",
                        "production_app_ready": True,
                        "field_trial_evidence_recorded": True,
                        "hil_pass": True,
                    },
                    "mobile_real_device_field_trial_evidence_record_copy": {
                        "schema": "trashbot.mobile_real_device_field_trial_evidence_record_copy.v1",
                        "support_refs": [{"kind": "field_trial_record", "url": "https://user:secret@example.invalid/record"}],
                        "Authorization": "Bearer must-not-leak",
                        "serial_device": "/dev/ttyUSB0",
                        "cancel_completed": True,
                    },
                    "mobile_real_device_field_trial_evidence_record_archive": {
                        "schema": "trashbot.mobile_real_device_field_trial_evidence_record_archive.v1",
                        "archive_status": "saved",
                        "delivery_success": True,
                    },
                },
                "ack_response": {
                    "mobile_real_device_field_trial_evidence_record_archive": {
                        "schema": "trashbot.mobile_real_device_field_trial_evidence_record_archive.v1",
                        "ack_semantics": "delivery_success",
                        "delivery_success": True,
                        "final_state": "DELIVERED",
                    },
                },
            })
            self.cloud.commands.append({
                "id": "cmd-real-device-field-trial-evidence-record-collect",
                "type": "collect",
                "payload": {"target": "trash_station", "trash_type": 0},
                "mobile_real_device_field_trial_evidence_record": {
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-future",
                    "delivery_success": True,
                },
            })

            self.assertTrue(worker.poll_once())

            self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
            self.assertEqual(worker.last_ack_id, "cmd-real-device-field-trial-evidence-record-collect")
            self.assertIn("last_ack_id=cmd-before-real-device-field-trial-evidence-record", self.cloud.get_paths[-1])
            cursor_payload = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(cursor_payload["last_terminal_ack_id"], "cmd-real-device-field-trial-evidence-record-collect")
            encoded_cursor = json.dumps(cursor_payload, ensure_ascii=False)
            self.assertNotIn("mobile_real_device_field_trial_evidence_record", encoded_cursor)
            self.assertNotIn("software_proof_docker_mobile_real_device_field_trial_evidence_record_gate", encoded_cursor)
            self.assertNotIn("delivery_success", encoded_cursor)
            ack_payload = self.cloud.ack_posts[0]
            self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
            self.assertEqual(ack_payload["command_id"], "cmd-real-device-field-trial-evidence-record-collect")
            self.assertEqual(ack_payload["state"], "acked")
            self.assertEqual(ack_payload["message"], "collect")
            encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
            # 有效 command 混入现场证据记录 metadata 时，执行、ACK、cursor 仍只跟随 command envelope。
            self.assertNotIn("mobile_real_device_field_trial_evidence_record", encoded_ack)
            self.assertNotIn("mobile_real_device_field_trial_evidence_record_summary", encoded_ack)
            self.assertNotIn("mobile_real_device_field_trial_evidence_record_copy", encoded_ack)
            self.assertNotIn("mobile_real_device_field_trial_evidence_record_archive", encoded_ack)
            self.assertNotIn("software_proof_docker_mobile_real_device_field_trial_evidence_record_gate", encoded_ack)
            self.assertNotIn("trigger_robot_action", encoded_ack)
            self.assertNotIn("cursor_override", encoded_ack)
            self.assertNotIn("terminal_ack", encoded_ack)
            self.assertNotIn("delivery_success", encoded_ack)
            self.assertNotIn("dropoff_success", encoded_ack)
            self.assertNotIn("cancel_completed", encoded_ack)
            self.assertNotIn("production_ready", encoded_ack)
            self.assertNotIn("production_app_ready", encoded_ack)
            self.assertNotIn("field_trial_evidence_recorded", encoded_ack)
            self.assertNotIn("hil_pass", encoded_ack)
            self.assertNotIn("/cmd_vel", encoded_ack)
            self.assertNotIn("/dev/ttyUSB0", encoded_ack)
            self.assertNotIn("Authorization", encoded_ack)
            self.assertNotIn("secret", encoded_ack)
            self.assertNotIn("DELIVERED", encoded_ack)
            encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
            self.assertNotIn("mobile_real_device_field_trial_evidence_record", encoded_status)
            self.assertNotIn("mobile_real_device_field_trial_evidence_record_summary", encoded_status)
            self.assertNotIn("mobile_real_device_field_trial_evidence_record_copy", encoded_status)
            self.assertNotIn("mobile_real_device_field_trial_evidence_record_archive", encoded_status)
            self.assertNotIn("software_proof_docker_mobile_real_device_field_trial_evidence_record_gate", encoded_status)
            self.assertNotIn("delivery_success", encoded_status)
            self.assertEqual(self.cloud.status_posts[-1]["state"], "loaded_and_ready")
            self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_mobile_real_device_field_trial_evidence_verdict_metadata_only_response_does_not_move_robot(self):
        metadata_cases = (
            (
                "mobile_real_device_field_trial_evidence_verdict",
                {
                    "schema": "trashbot.mobile_real_device_field_trial_evidence_verdict.v1",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_field_trial_evidence_verdict_gate",
                    "verdict_state": "needs_retest",
                    "safe_to_control": False,
                    "ack_semantics": "accepted_processing_only_not_delivery_success",
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-field-trial-verdict",
                    "terminal_ack": "delivered",
                    "delivery_success": True,
                    "dropoff_success": True,
                    "cancel_completed": True,
                    "production_ready": True,
                    "hil_pass": True,
                    "raw_ros_topic": "/cmd_vel",
                },
            ),
            (
                "mobile_real_device_field_trial_evidence_verdict_summary",
                {
                    "schema": "trashbot.mobile_real_device_field_trial_evidence_verdict_summary.v1",
                    "safe_phone_copy": "现场证据 verdict 只说明材料复核结果，ACK 不是 delivery success。",
                    "next_action": "confirm_dropoff",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_field_trial_evidence_verdict_gate",
                    "field_trial_evidence_verdict": "needs_retest",
                    "production_app_ready": True,
                    "cursor_override": "cmd-field-trial-verdict-summary",
                    "terminal_ack": "delivered",
                    "delivery_success": True,
                    "dropoff_success": True,
                },
            ),
            (
                "mobile_real_device_field_trial_evidence_verdict_copy",
                {
                    "schema": "trashbot.mobile_real_device_field_trial_evidence_verdict_copy.v1",
                    "evidence_boundary": "software_proof_docker_mobile_real_device_field_trial_evidence_verdict_gate",
                    "support_refs": [{"kind": "field_trial_verdict", "url": "https://user:secret@example.invalid/verdict"}],
                    "not_proven": ["production readiness", "HIL", "delivery success"],
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-field-trial-verdict-copy",
                    "terminal_ack": "delivered",
                    "Authorization": "Bearer must-not-leak",
                    "serial_device": "/dev/ttyUSB0",
                    "cancel_completed": True,
                },
            ),
        )
        for metadata_name, metadata in metadata_cases:
            with self.subTest(metadata_name=metadata_name):
                self.cloud.status_posts.clear()
                self.cloud.ack_posts.clear()
                self.cloud.get_paths.clear()
                self.backend.calls.clear()
                self.cloud.response_extras["command_response"] = {metadata_name: metadata}
                with tempfile.TemporaryDirectory() as tmpdir:
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-{metadata_name}",
                        cursor_state_path=state_path,
                    )

                    handled = worker.poll_once()

                    # verdict 只是材料复核 metadata-only，不能驱动 command、ACK、terminal ACK 或 cursor。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-{metadata_name}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    self.assertEqual(self.cloud.status_posts[-1]["state"], "waiting_for_trash")
                    self.assertNotIn(self.cloud.status_posts[-1]["state"], ("loaded_and_ready", "returning", "canceling", "completed"))
                    self.assertIn(f"last_ack_id=cmd-before-{metadata_name}", self.cloud.get_paths[-1])
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn(metadata_name, encoded_status)
                    self.assertNotIn("software_proof_docker_mobile_real_device_field_trial_evidence_verdict_gate", encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("terminal_ack", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)
                    self.assertNotIn("dropoff_success", encoded_status)
                    self.assertNotIn("cancel_completed", encoded_status)
                    self.assertNotIn("production_ready", encoded_status)
                    self.assertNotIn("production_app_ready", encoded_status)
                    self.assertNotIn("hil_pass", encoded_status)
                    self.assertNotIn("field_trial_evidence_verdict", encoded_status)
                    self.assertNotIn("/cmd_vel", encoded_status)
                    self.assertNotIn("/dev/ttyUSB0", encoded_status)
                    self.assertNotIn("Authorization", encoded_status)
                    self.assertNotIn("secret", encoded_status)
                    self.cloud.response_extras["command_response"] = {}

    def test_mobile_real_device_field_trial_evidence_verdict_metadata_is_ignored_by_valid_command_envelope(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                last_ack_id="cmd-before-real-device-field-trial-evidence-verdict",
                cursor_state_path=state_path,
            )
            self.cloud.response_extras.update({
                "status_response": {
                    "mobile_real_device_field_trial_evidence_verdict_summary": {
                        "schema": "trashbot.mobile_real_device_field_trial_evidence_verdict_summary.v1",
                        "evidence_boundary": "software_proof_docker_mobile_real_device_field_trial_evidence_verdict_gate",
                        "delivery_success": True,
                        "trigger_robot_action": "collect",
                    },
                },
                "command_response": {
                    "mobile_real_device_field_trial_evidence_verdict": {
                        "schema": "trashbot.mobile_real_device_field_trial_evidence_verdict.v1",
                        "evidence_boundary": "software_proof_docker_mobile_real_device_field_trial_evidence_verdict_gate",
                        "trigger_robot_action": "cancel",
                        "cursor_override": "cmd-field-trial-verdict-override",
                        "ack_semantics": "delivery_success",
                        "terminal_ack": "delivered",
                        "delivery_success": True,
                        "dropoff_success": True,
                        "raw_ros_topic": "/cmd_vel",
                    },
                    "mobile_real_device_field_trial_evidence_verdict_summary": {
                        "schema": "trashbot.mobile_real_device_field_trial_evidence_verdict_summary.v1",
                        "safe_phone_copy": "ACK 只代表 accepted_processing_only_not_delivery_success，不代表现场证据 verdict 通过。",
                        "next_action": "confirm_dropoff",
                        "production_app_ready": True,
                        "field_trial_evidence_verdict": "accepted",
                        "hil_pass": True,
                    },
                    "mobile_real_device_field_trial_evidence_verdict_copy": {
                        "schema": "trashbot.mobile_real_device_field_trial_evidence_verdict_copy.v1",
                        "support_refs": [{"kind": "field_trial_verdict", "url": "https://user:secret@example.invalid/verdict"}],
                        "Authorization": "Bearer must-not-leak",
                        "serial_device": "/dev/ttyUSB0",
                        "cancel_completed": True,
                    },
                },
                "ack_response": {
                    "mobile_real_device_field_trial_evidence_verdict_copy": {
                        "schema": "trashbot.mobile_real_device_field_trial_evidence_verdict_copy.v1",
                        "ack_semantics": "delivery_success",
                        "delivery_success": True,
                        "final_state": "DELIVERED",
                    },
                },
            })
            self.cloud.commands.append({
                "id": "cmd-real-device-field-trial-evidence-verdict-confirm",
                "type": "confirm_dropoff",
                "payload": {"accepted": False},
                "mobile_real_device_field_trial_evidence_verdict": {
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-future",
                    "delivery_success": True,
                },
            })

            self.assertTrue(worker.poll_once())

            self.assertEqual(self.backend.calls, [("confirm_dropoff", False)])
            self.assertEqual(worker.last_ack_id, "cmd-real-device-field-trial-evidence-verdict-confirm")
            self.assertIn("last_ack_id=cmd-before-real-device-field-trial-evidence-verdict", self.cloud.get_paths[-1])
            cursor_payload = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(cursor_payload["last_terminal_ack_id"], "cmd-real-device-field-trial-evidence-verdict-confirm")
            encoded_cursor = json.dumps(cursor_payload, ensure_ascii=False)
            self.assertNotIn("mobile_real_device_field_trial_evidence_verdict", encoded_cursor)
            self.assertNotIn("software_proof_docker_mobile_real_device_field_trial_evidence_verdict_gate", encoded_cursor)
            self.assertNotIn("delivery_success", encoded_cursor)
            ack_payload = self.cloud.ack_posts[0]
            self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
            self.assertEqual(ack_payload["command_id"], "cmd-real-device-field-trial-evidence-verdict-confirm")
            self.assertEqual(ack_payload["state"], "acked")
            self.assertEqual(ack_payload["message"], "confirm_dropoff")
            encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
            # 有效 command 混入 verdict metadata 时，执行、ACK、cursor 仍只跟随 command envelope。
            self.assertNotIn("mobile_real_device_field_trial_evidence_verdict", encoded_ack)
            self.assertNotIn("mobile_real_device_field_trial_evidence_verdict_summary", encoded_ack)
            self.assertNotIn("mobile_real_device_field_trial_evidence_verdict_copy", encoded_ack)
            self.assertNotIn("software_proof_docker_mobile_real_device_field_trial_evidence_verdict_gate", encoded_ack)
            self.assertNotIn("trigger_robot_action", encoded_ack)
            self.assertNotIn("cursor_override", encoded_ack)
            self.assertNotIn("terminal_ack", encoded_ack)
            self.assertNotIn("delivery_success", encoded_ack)
            self.assertNotIn("dropoff_success", encoded_ack)
            self.assertNotIn("cancel_completed", encoded_ack)
            self.assertNotIn("production_ready", encoded_ack)
            self.assertNotIn("production_app_ready", encoded_ack)
            self.assertNotIn("field_trial_evidence_verdict", encoded_ack)
            self.assertNotIn("hil_pass", encoded_ack)
            self.assertNotIn("/cmd_vel", encoded_ack)
            self.assertNotIn("/dev/ttyUSB0", encoded_ack)
            self.assertNotIn("Authorization", encoded_ack)
            self.assertNotIn("secret", encoded_ack)
            self.assertNotIn("DELIVERED", encoded_ack)
            encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
            self.assertNotIn("mobile_real_device_field_trial_evidence_verdict", encoded_status)
            self.assertNotIn("mobile_real_device_field_trial_evidence_verdict_summary", encoded_status)
            self.assertNotIn("mobile_real_device_field_trial_evidence_verdict_copy", encoded_status)
            self.assertNotIn("software_proof_docker_mobile_real_device_field_trial_evidence_verdict_gate", encoded_status)
            self.assertNotIn("delivery_success", encoded_status)
            self.assertEqual(self.cloud.status_posts[-1]["state"], "returning")
            self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_mobile_pwa_install_prompt_evidence_metadata_only_response_does_not_move_robot(self):
        metadata_cases = (
            (
                "mobile_pwa_install_prompt_evidence",
                {
                    "schema": "trashbot.mobile_pwa_install_prompt_evidence.v1",
                    "install_prompt_capture_status": "blocked_no_real_device",
                    "install_prompt_user_outcome": "not_proven",
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-install-prompt-override",
                    "ack_semantics": "delivery_success",
                    "delivery_success": True,
                    "production_ready": True,
                    "hil_pass": True,
                    "raw_ros_topic": "/cmd_vel",
                },
            ),
            (
                "mobile_pwa_install_prompt_evidence_summary",
                {
                    "schema": "trashbot.mobile_pwa_install_prompt_evidence_summary.v1",
                    "display_mode": "browser",
                    "manifest_present": True,
                    "service_worker_status": "registered",
                    "next_action": "confirm_dropoff",
                    "cursor_override": "cmd-install-prompt-summary",
                    "delivery_success": True,
                    "real_device_proof": True,
                },
            ),
            (
                "mobile_pwa_install_prompt_evidence_package",
                {
                    "schema": "trashbot.mobile_pwa_install_prompt_evidence_package.v1",
                    "evidence_boundary": "software_proof_docker_mobile_pwa_install_prompt_evidence_gate",
                    "safe_to_control": True,
                    "linked_handoff_session": "handoff-123",
                    "trigger_robot_action": "cancel",
                    "production_ready": True,
                    "Authorization": "Bearer must-not-leak",
                },
            ),
        )
        for metadata_name, metadata in metadata_cases:
            with self.subTest(metadata_name=metadata_name):
                self.cloud.status_posts.clear()
                self.cloud.ack_posts.clear()
                self.backend.calls.clear()
                self.cloud.response_extras["command_response"] = {
                    metadata_name: metadata,
                    "preflight": {"overall_status": "blocked", "production_ready": False},
                }
                with tempfile.TemporaryDirectory() as tmpdir:
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-{metadata_name}",
                        cursor_state_path=state_path,
                    )

                    handled = worker.poll_once()

                    # PWA 安装提示证据只给手机/支持侧展示；缺少 command envelope 时不能产生机器人副作用。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-{metadata_name}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    self.assertIn(f"last_ack_id=cmd-before-{metadata_name}", self.cloud.get_paths[-1])
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn(metadata_name, encoded_status)
                    self.assertNotIn("install_prompt_capture_status", encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)
                    self.assertNotIn("production_ready", encoded_status)
                    self.assertNotIn("hil_pass", encoded_status)
                    self.assertNotIn("/cmd_vel", encoded_status)
                    self.assertNotIn("Authorization", encoded_status)
                    self.cloud.response_extras["command_response"] = {}

    def test_mobile_pwa_install_prompt_evidence_fields_are_ignored_by_command_status_ack_envelope(self):
        self.cloud.response_extras.update({
            "status_response": {
                "mobile_pwa_install_prompt_evidence_summary": {
                    "schema": "trashbot.mobile_pwa_install_prompt_evidence_summary.v1",
                    "install_prompt_user_outcome": "accepted",
                    "delivery_success": True,
                    "production_ready": True,
                },
            },
            "command_response": {
                "mobile_pwa_install_prompt_evidence": {
                    "schema": "trashbot.mobile_pwa_install_prompt_evidence.v1",
                    "install_prompt_capture_status": "captured",
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-future",
                    "ack_semantics": "delivery_success",
                    "delivery_success": True,
                    "raw_ros_topic": "/cmd_vel",
                },
                "mobile_pwa_install_prompt_evidence_package": {
                    "schema": "trashbot.mobile_pwa_install_prompt_evidence_package.v1",
                    "evidence_boundary": "software_proof_docker_mobile_pwa_install_prompt_evidence_gate",
                    "next_action": "confirm_dropoff",
                    "production_ready": True,
                    "real_device_proof": True,
                    "hil_pass": True,
                },
            },
            "ack_response": {
                "mobile_pwa_install_prompt_evidence_summary": {
                    "schema": "trashbot.mobile_pwa_install_prompt_evidence_summary.v1",
                    "ack_semantics": "delivery_success",
                    "delivery_success": True,
                    "final_state": "DELIVERED",
                },
            },
        })
        self.cloud.commands.append({
            "id": "cmd-install-prompt-extra",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
            "mobile_pwa_install_prompt_evidence": {
                "trigger_robot_action": "cancel",
                "cursor_override": "cmd-future",
                "delivery_success": True,
            },
        })

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
        self.assertEqual(self.worker.last_ack_id, "cmd-install-prompt-extra")
        ack_payload = self.cloud.ack_posts[0]
        self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
        self.assertEqual(ack_payload["command_id"], "cmd-install-prompt-extra")
        self.assertEqual(ack_payload["state"], "acked")
        self.assertEqual(ack_payload["message"], "collect")
        encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
        # ACK 只能描述 command envelope 的本地处理结果，不能吸收安装提示证据或送达语义。
        self.assertNotIn("mobile_pwa_install_prompt_evidence", encoded_ack)
        self.assertNotIn("mobile_pwa_install_prompt_evidence_summary", encoded_ack)
        self.assertNotIn("mobile_pwa_install_prompt_evidence_package", encoded_ack)
        self.assertNotIn("software_proof_docker_mobile_pwa_install_prompt_evidence_gate", encoded_ack)
        self.assertNotIn("install_prompt_capture_status", encoded_ack)
        self.assertNotIn("trigger_robot_action", encoded_ack)
        self.assertNotIn("cursor_override", encoded_ack)
        self.assertNotIn("delivery_success", encoded_ack)
        self.assertNotIn("production_ready", encoded_ack)
        self.assertNotIn("real_device_proof", encoded_ack)
        self.assertNotIn("hil_pass", encoded_ack)
        self.assertNotIn("DELIVERED", encoded_ack)
        self.assertNotIn("/cmd_vel", encoded_ack)
        encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
        self.assertNotIn("mobile_pwa_install_prompt_evidence", encoded_status)
        self.assertNotIn("mobile_pwa_install_prompt_evidence_summary", encoded_status)
        self.assertNotIn("mobile_pwa_install_prompt_evidence_package", encoded_status)
        self.assertNotIn("delivery_success", encoded_status)
        self.assertEqual(self.cloud.status_posts[-1]["state"], "loaded_and_ready")
        self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_voice_prompt_readiness_fields_are_ignored_by_command_status_ack_envelope(self):
        self.cloud.response_extras.update({
            "status_response": {
                "voice_prompt_readiness": {
                    "schema": "trashbot.voice_prompt_readiness.v1",
                    "playback_ready": True,
                    "delivery_success": True,
                },
            },
            "command_response": {
                "voice_prompt_readiness": {
                    "schema": "trashbot.voice_prompt_readiness.v1",
                    "current_prompt": "你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯,",
                    "trigger_robot_action": "confirm_dropoff",
                    "next_action": "cancel",
                    "playback_ready": True,
                    "delivery_success": True,
                },
            },
            "ack_response": {
                "voice_prompt_readiness": {
                    "schema": "trashbot.voice_prompt_readiness.v1",
                    "ack_semantics": "delivery_success",
                    "playback_ready": True,
                    "delivery_success": True,
                    "final_state": "DELIVERED",
                },
            },
        })
        self.cloud.commands.append({
            "id": "cmd-voice-prompt-extra",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
        })

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
        self.assertEqual(self.worker.last_ack_id, "cmd-voice-prompt-extra")
        ack_payload = self.cloud.ack_posts[0]
        self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
        self.assertEqual(ack_payload["command_id"], "cmd-voice-prompt-extra")
        self.assertEqual(ack_payload["state"], "acked")
        self.assertEqual(ack_payload["message"], "collect")
        encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
        # voice prompt readiness 是手机提示元数据，ACK 只能表达 command envelope 的本地处理结果。
        self.assertNotIn("voice_prompt_readiness", encoded_ack)
        self.assertNotIn("trigger_robot_action", encoded_ack)
        self.assertNotIn("playback_ready", encoded_ack)
        self.assertNotIn("delivery_success", encoded_ack)
        self.assertNotIn("DELIVERED", encoded_ack)
        self.assertEqual(self.cloud.status_posts[-1]["state"], "loaded_and_ready")
        self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_production_recovery_fields_are_ignored_by_command_status_ack_envelope(self):
        self.cloud.response_extras.update({
            "status_response": {
                "production_recovery": {
                    "schema": "trashbot.production_recovery_gate",
                    "evidence_boundary": "software_proof_docker_production_recovery_gate",
                    "production_ready": False,
                    "overall_status": "blocked",
                    "delivery_success": True,
                },
            },
            "command_response": {
                "production_recovery": {
                    "schema": "trashbot.production_recovery_gate",
                    "safe_summary": "本地恢复演练可读摘要只能给手机或支持同学展示。",
                    "next_action": "confirm_dropoff",
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-future",
                    "production_ready": False,
                    "overall_status": "blocked",
                    "delivery_success": True,
                },
            },
            "ack_response": {
                "production_recovery": {
                    "schema": "trashbot.production_recovery_gate",
                    "ack_semantics": "delivery_success",
                    "production_ready": True,
                    "overall_status": "ready",
                    "delivery_success": True,
                    "final_state": "DELIVERED",
                },
            },
        })
        self.cloud.commands.append({
            "id": "cmd-production-recovery-extra",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
        })

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
        self.assertEqual(self.worker.last_ack_id, "cmd-production-recovery-extra")
        ack_payload = self.cloud.ack_posts[0]
        self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
        self.assertEqual(ack_payload["command_id"], "cmd-production-recovery-extra")
        self.assertEqual(ack_payload["state"], "acked")
        self.assertEqual(ack_payload["message"], "collect")
        encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
        # production recovery 是手机/支持元数据，ACK 只能表达 command envelope 的本地处理结果。
        self.assertNotIn("production_recovery", encoded_ack)
        self.assertNotIn("production_recovery_gate", encoded_ack)
        self.assertNotIn("trigger_robot_action", encoded_ack)
        self.assertNotIn("cursor_override", encoded_ack)
        self.assertNotIn("delivery_success", encoded_ack)
        self.assertNotIn("DELIVERED", encoded_ack)
        self.assertEqual(self.cloud.status_posts[-1]["state"], "loaded_and_ready")
        self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_metadata_only_preflight_blocked_response_does_not_start_ack_or_persist_cursor(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                last_ack_id="cmd-before-blocked",
                cursor_state_path=state_path,
            )
            self.cloud.response_extras["command_response"] = {
                "provisioning": {"status": "invalid", "raw_action": "collect"},
                "sts": {"status": "blocked", "secret_access_key": "must-not-be-used"},
                "audit": {"status": "blocked", "delivery_success": True},
                "preflight": {"overall_status": "blocked", "production_ready": False},
            }

            handled = worker.poll_once()

            # metadata-only 响应没有 command envelope，不能被解释成本地任务或 ACK 成功。
            self.assertFalse(handled)
            self.assertEqual(self.backend.calls, [])
            self.assertEqual(self.cloud.ack_posts, [])
            self.assertEqual(worker.last_ack_id, "cmd-before-blocked")
            self.assertFalse(state_path.exists())
            self.assertEqual(len(self.cloud.status_posts), 1)
            self.assertNotIn("secret_access_key", json.dumps(self.cloud.status_posts))

    def test_metadata_only_production_store_queue_response_does_not_start_ack_or_persist_cursor(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                last_ack_id="cmd-before-production-store-queue",
                cursor_state_path=state_path,
            )
            self.cloud.response_extras["command_response"] = {
                "production_store_queue": {
                    "state": "ready",
                    "store_contract_status": "local_store_contract_artifact_present",
                    "queue_contract_status": "local_queue_contract_artifact_present",
                    "ordering_status": "local_ordering_contract_artifact_present",
                    "consistency_status": "single_instance_only",
                    "production_ready": False,
                    "overall_status": "blocked",
                    "delivery_success": True,
                },
                "preflight": {"overall_status": "blocked", "production_ready": False},
            }

            handled = worker.poll_once()

            # 只有 metadata、没有 command envelope 时，robot 侧必须保持 fail-closed。
            self.assertFalse(handled)
            self.assertEqual(self.backend.calls, [])
            self.assertEqual(self.cloud.ack_posts, [])
            self.assertEqual(worker.last_ack_id, "cmd-before-production-store-queue")
            self.assertFalse(state_path.exists())
            self.assertEqual(len(self.cloud.status_posts), 1)
            self.assertNotIn("production_store_queue", json.dumps(self.cloud.status_posts))

    def test_metadata_only_queue_ordering_responses_do_not_start_ack_or_persist_cursor(self):
        for drill_status in ("blocked", "invalid", "stale"):
            with self.subTest(drill_status=drill_status):
                self.cloud.status_posts.clear()
                self.cloud.ack_posts.clear()
                self.backend.calls.clear()
                with tempfile.TemporaryDirectory() as tmpdir:
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-queue-{drill_status}",
                        cursor_state_path=state_path,
                    )
                    self.cloud.response_extras["command_response"] = {
                        "queue_ordering_drill": {
                            "schema": "trashbot.queue_ordering_drill",
                            "status": drill_status,
                            "ordering_status": "metadata_only",
                            "cursor_status": "must_not_advance",
                            "delivery_success": True,
                            "next_action": "collect",
                        },
                        "preflight": {"overall_status": "blocked", "production_ready": False},
                    }

                    handled = worker.poll_once()

                    # metadata-only blocked/invalid/stale 响应没有 command envelope，必须保持本地 fail-closed。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-queue-{drill_status}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    self.assertNotIn("queue_ordering_drill", json.dumps(self.cloud.status_posts))
                    self.assertNotIn("next_action", json.dumps(self.cloud.status_posts))
                    self.assertNotIn("delivery_success", json.dumps(self.cloud.status_posts))

    def test_metadata_only_phone_task_flow_response_does_not_start_ack_or_persist_cursor(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                last_ack_id="cmd-before-phone-task-flow",
                cursor_state_path=state_path,
            )
            self.cloud.response_extras["command_response"] = {
                "phone_task_flow_readiness": {
                    "schema": "trashbot.phone_task_flow_readiness.v1",
                    "current_step": "start_delivery",
                    "next_action": "confirm_dropoff",
                    "trigger_robot_action": "collect",
                    "delivery_success": True,
                    "blocking_reasons": ["status_waiting"],
                },
                "preflight": {"overall_status": "blocked", "production_ready": False},
            }

            handled = worker.poll_once()

            # 只有 task-flow metadata、没有 command envelope 时，不能推进 robot 侧任务或游标。
            self.assertFalse(handled)
            self.assertEqual(self.backend.calls, [])
            self.assertEqual(self.cloud.ack_posts, [])
            self.assertEqual(worker.last_ack_id, "cmd-before-phone-task-flow")
            self.assertFalse(state_path.exists())
            self.assertEqual(len(self.cloud.status_posts), 1)
            self.assertNotIn("phone_task_flow_readiness", json.dumps(self.cloud.status_posts))

    def test_metadata_only_mobile_web_entrypoint_response_does_not_start_ack_or_persist_cursor(self):
        metadata_cases = (
            (
                "mobile_web_entrypoint",
                {
                    "schema": "trashbot.mobile_web_entrypoint.v1",
                    "entrypoint_url": "/mobile/",
                    "static_contract": "phone_safe_consumer_only",
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-future",
                    "delivery_success": True,
                    "raw_ros_topic": "/cmd_vel",
                },
            ),
            (
                "mobile_web_entrypoint_readiness",
                {
                    "schema": "trashbot.mobile_web_entrypoint_readiness.v1",
                    "overall_status": "ready",
                    "next_action": "confirm_dropoff",
                    "trigger_robot_action": "confirm_dropoff",
                    "ack_semantics": "delivery_success",
                    "delivery_success": True,
                },
            ),
            (
                "pwa_entrypoint",
                {
                    "schema": "trashbot.pwa_entrypoint.v1",
                    "offline_shell": "ready",
                    "next_action": "cancel",
                    "trigger_robot_action": "cancel",
                    "delivery_success": True,
                },
            ),
        )
        for metadata_name, metadata in metadata_cases:
            with self.subTest(metadata_name=metadata_name):
                self.cloud.status_posts.clear()
                self.cloud.ack_posts.clear()
                self.backend.calls.clear()
                with tempfile.TemporaryDirectory() as tmpdir:
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-{metadata_name}",
                        cursor_state_path=state_path,
                    )
                    self.cloud.response_extras["command_response"] = {
                        metadata_name: metadata,
                        "preflight": {"overall_status": "blocked", "production_ready": False},
                    }

                    handled = worker.poll_once()

                    # mobile web/PWA 入口是手机端 consumer metadata，不是 robot command。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-{metadata_name}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn(metadata_name, encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)
                    self.assertNotIn("/cmd_vel", encoded_status)
                    self.cloud.response_extras["command_response"] = {}

    def test_metadata_only_mobile_device_acceptance_response_does_not_start_ack_or_persist_cursor(self):
        metadata_cases = (
            (
                "mobile_device_acceptance_readiness",
                {
                    "schema": "trashbot.mobile_device_acceptance_readiness.v1",
                    "overall_status": "ready",
                    "device_acceptance_ready": True,
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-device-override",
                    "ack_semantics": "delivery_success",
                    "delivery_success": True,
                    "raw_ros_topic": "/trashbot/collect_trash",
                },
            ),
            (
                "phone_device_acceptance_readiness",
                {
                    "schema": "trashbot.phone_device_acceptance_readiness.v1",
                    "support_entry_enabled": True,
                    "next_action": "confirm_dropoff",
                    "trigger_robot_action": "confirm_dropoff",
                    "cursor_override": "cmd-phone-override",
                    "delivery_success": True,
                    "serial_device": "/dev/ttyUSB0",
                },
            ),
            (
                "mobile_browser_acceptance_readiness",
                {
                    "schema": "trashbot.mobile_browser_acceptance_readiness.v1",
                    "browser_acceptance_ready": True,
                    "next_action": "cancel",
                    "trigger_robot_action": "cancel",
                    "ack_semantics": "delivery_success",
                    "delivery_success": True,
                    "Authorization": "Bearer must-not-leak",
                },
            ),
        )
        for metadata_name, metadata in metadata_cases:
            with self.subTest(metadata_name=metadata_name):
                self.cloud.status_posts.clear()
                self.cloud.ack_posts.clear()
                self.backend.calls.clear()
                with tempfile.TemporaryDirectory() as tmpdir:
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-{metadata_name}",
                        cursor_state_path=state_path,
                    )
                    self.cloud.response_extras["command_response"] = {
                        metadata_name: metadata,
                        "preflight": {"overall_status": "blocked", "production_ready": False},
                    }

                    handled = worker.poll_once()

                    # 手机设备/浏览器验收 readiness 是展示元数据；没有 command envelope 时必须 no-op。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-{metadata_name}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    self.assertIn(f"last_ack_id=cmd-before-{metadata_name}", self.cloud.get_paths[-1])
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn(metadata_name, encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)
                    self.assertNotIn("/trashbot/collect_trash", encoded_status)
                    self.assertNotIn("/dev/ttyUSB0", encoded_status)
                    self.assertNotIn("Authorization", encoded_status)
                    self.cloud.response_extras["command_response"] = {}

    def test_metadata_only_mobile_browser_acceptance_bundle_response_does_not_start_ack_or_persist_cursor(self):
        metadata_cases = (
            (
                "mobile_browser_acceptance_bundle",
                {
                    "schema": "trashbot.mobile_browser_acceptance_bundle.v1",
                    "schema_version": 1,
                    "overall_status": "blocked",
                    "production_app_ready": False,
                    "safe_to_control": False,
                    "viewport": {"status": "not_proven", "sample": "390x844"},
                    "touch_target": {"status": "software_checked", "min_px": 44},
                    "pwa_install_prompt": {"status": "not_proven"},
                    "offline_shell": {"status": "software_checked"},
                    "diagnostics": {"status": "available_without_control"},
                    "cloud_gate": {"status": "blocked"},
                    "action_gate": {"start": "fail_closed", "confirm": "fail_closed", "cancel": "fail_closed"},
                    "ack_semantics": "accepted_or_processing_only",
                    "client_timestamp": "2026-05-13T15:16:00+08:00",
                    "safe_phone_copy": "浏览器验收包仅供手机端展示，不能触发机器人动作。",
                    "recovery_hint": "使用真实手机浏览器复测后再开放控制。",
                    "not_proven": ["real_phone_browser", "production_app", "delivery_success"],
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-mobile-browser-bundle",
                    "delivery_success": True,
                    "raw_ros_topic": "/cmd_vel",
                },
            ),
            (
                "phone_browser_acceptance_bundle",
                {
                    "schema": "trashbot.phone_browser_acceptance_bundle.v1",
                    "schema_version": 1,
                    "overall_status": "blocked",
                    "safe_to_control": False,
                    "support_handoff": {"available": True, "next_action": "confirm_dropoff"},
                    "ack_semantics": "delivery_success",
                    "safe_phone_copy": "ACK 仅代表命令已接收或处理中，不代表送达成功。",
                    "trigger_robot_action": "confirm_dropoff",
                    "cursor_override": "cmd-phone-browser-bundle",
                    "delivery_success": True,
                    "serial_device": "/dev/ttyUSB0",
                },
            ),
            (
                "mobile_acceptance_evidence_bundle",
                {
                    "schema": "trashbot.mobile_acceptance_evidence_bundle.v1",
                    "schema_version": 1,
                    "evidence_boundary": "software_proof_docker_mobile_browser_acceptance_bundle_gate",
                    "overall_status": "blocked",
                    "safe_to_control": False,
                    "redacted_artifacts": ["viewport_summary", "diagnostics_summary"],
                    "not_proven": ["real_pwa_install_prompt", "real_cloud_4g", "wave_rover_hil"],
                    "next_action": "cancel",
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-mobile-evidence-bundle",
                    "delivery_success": True,
                    "Authorization": "Bearer must-not-leak",
                },
            ),
            (
                "mobile_web_browser_proof",
                {
                    "schema": "trashbot.mobile_web_browser_proof.v1",
                    "schema_version": 1,
                    "evidence_boundary": "software_proof_docker_mobile_web_browser_proof_gate",
                    "browser_family": "chromium",
                    "screenshot_ref": "evidence/mobile_web_browser.png",
                    "summary_ref": "evidence/summary.json",
                    "ack_semantics": "accepted_or_processing_only",
                    "not_proven": ["real_phone_device", "production_app", "delivery_success"],
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-mobile-web-browser-proof",
                    "delivery_success": True,
                    "raw_ros_topic": "/cmd_vel",
                },
            ),
            (
                "phone_browser_proof",
                {
                    "schema": "trashbot.phone_browser_proof.v1",
                    "schema_version": 1,
                    "evidence_boundary": "software_proof_docker_mobile_web_browser_proof_gate",
                    "safe_phone_copy": "本地浏览器 proof 不是手机真机或送达成功证明。",
                    "ack_semantics": "delivery_success",
                    "next_action": "confirm_dropoff",
                    "trigger_robot_action": "confirm_dropoff",
                    "cursor_override": "cmd-phone-browser-proof",
                    "delivery_success": True,
                    "serial_device": "/dev/ttyUSB0",
                },
            ),
            (
                "mobile_browser_proof_summary",
                {
                    "schema": "trashbot.mobile_browser_proof_summary.v1",
                    "schema_version": 1,
                    "evidence_boundary": "software_proof_docker_mobile_web_browser_proof_gate",
                    "overall_status": "passed",
                    "not_proven": ["hil_pass", "dropoff_success", "cancel_complete"],
                    "next_action": "cancel",
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-mobile-browser-proof-summary",
                    "delivery_success": True,
                    "Authorization": "Bearer must-not-leak",
                },
            ),
        )
        for metadata_name, metadata in metadata_cases:
            with self.subTest(metadata_name=metadata_name):
                self.cloud.status_posts.clear()
                self.cloud.ack_posts.clear()
                self.backend.calls.clear()
                with tempfile.TemporaryDirectory() as tmpdir:
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-{metadata_name}",
                        cursor_state_path=state_path,
                    )
                    self.cloud.response_extras["command_response"] = {
                        metadata_name: metadata,
                        "preflight": {"overall_status": "blocked", "production_ready": False},
                    }

                    handled = worker.poll_once()

                    # 浏览器验收 bundle 只属于 phone/support metadata；没有 command envelope 时必须保持 no-op。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-{metadata_name}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    self.assertIn(f"last_ack_id=cmd-before-{metadata_name}", self.cloud.get_paths[-1])
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn(metadata_name, encoded_status)
                    self.assertNotIn("preflight", encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)
                    self.assertNotIn("/cmd_vel", encoded_status)
                    self.assertNotIn("/dev/ttyUSB0", encoded_status)
                    self.assertNotIn("Authorization", encoded_status)
                    self.cloud.response_extras["command_response"] = {}

    def test_metadata_only_phone_offline_resume_response_does_not_start_ack_or_persist_cursor(self):
        for connection_state in ("offline", "recovering", "stale"):
            with self.subTest(connection_state=connection_state):
                self.cloud.status_posts.clear()
                self.cloud.ack_posts.clear()
                self.backend.calls.clear()
                with tempfile.TemporaryDirectory() as tmpdir:
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-offline-resume-{connection_state}",
                        cursor_state_path=state_path,
                    )
                    self.cloud.response_extras["command_response"] = {
                        "phone_offline_resume_readiness": {
                            "schema": "trashbot.phone_offline_resume_readiness.v1",
                            "connection_state": connection_state,
                            "can_resume": False,
                            "primary_actions_enabled": False,
                            "next_action": "collect",
                            "trigger_robot_action": "collect",
                            "ack_semantics": "delivery_success",
                            "cursor_override": "cmd-future",
                            "delivery_success": True,
                        },
                        "preflight": {"overall_status": "blocked", "production_ready": False},
                    }

                    handled = worker.poll_once()

                    # 只有 offline/resume metadata、没有 command envelope 时，不能执行动作、ACK 或推进游标。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-offline-resume-{connection_state}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn("phone_offline_resume_readiness", encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)

    def test_metadata_only_phone_support_bundle_response_does_not_start_ack_or_persist_cursor(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                last_ack_id="cmd-before-phone-support-bundle",
                cursor_state_path=state_path,
            )
            self.cloud.response_extras["command_response"] = {
                "phone_support_bundle": {
                    "schema": "trashbot.phone_support_bundle.v1",
                    "support_level": "support_required",
                    "safe_copy": "远程状态阻塞，请联系支持。",
                    "next_action": "collect",
                    "trigger_robot_action": "collect",
                    "ack_semantics": "accepted_or_processing_only",
                    "delivery_success": True,
                    "support_refs": {"raw_ros_topic": "/cmd_vel"},
                },
                "preflight": {"overall_status": "blocked", "production_ready": False},
            }

            handled = worker.poll_once()

            # 只有 support bundle metadata、没有 command envelope 时，不能执行动作、ACK 或推进游标。
            self.assertFalse(handled)
            self.assertEqual(self.backend.calls, [])
            self.assertEqual(self.cloud.ack_posts, [])
            self.assertEqual(worker.last_ack_id, "cmd-before-phone-support-bundle")
            self.assertFalse(state_path.exists())
            self.assertEqual(len(self.cloud.status_posts), 1)
            encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
            self.assertNotIn("phone_support_bundle", encoded_status)
            self.assertNotIn("trigger_robot_action", encoded_status)
            self.assertNotIn("delivery_success", encoded_status)
            self.assertNotIn("/cmd_vel", encoded_status)

    def test_metadata_only_voice_prompt_response_does_not_start_ack_or_persist_cursor(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                last_ack_id="cmd-before-voice-prompt",
                cursor_state_path=state_path,
            )
            self.cloud.response_extras["command_response"] = {
                "voice_prompt_readiness": {
                    "schema": "trashbot.voice_prompt_readiness.v1",
                    "current_prompt": "你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯,",
                    "trigger_state": "requesting_floor_help",
                    "requires_human_help": True,
                    "playback_ready": True,
                    "next_action": "collect",
                    "trigger_robot_action": "collect",
                    "ack_semantics": "delivery_success",
                    "delivery_success": True,
                    "support_refs": {
                        "raw_ros_topic": "/cmd_vel",
                        "serial": "/dev/ttyUSB0",
                        "token": "secret-token",
                    },
                },
                "preflight": {"overall_status": "blocked", "production_ready": False},
            }

            handled = worker.poll_once()

            # 只有 voice prompt metadata、没有 command envelope 时，不能执行动作、ACK 或推进游标。
            self.assertFalse(handled)
            self.assertEqual(self.backend.calls, [])
            self.assertEqual(self.cloud.ack_posts, [])
            self.assertEqual(worker.last_ack_id, "cmd-before-voice-prompt")
            self.assertFalse(state_path.exists())
            self.assertEqual(len(self.cloud.status_posts), 1)
            encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
            self.assertNotIn("voice_prompt_readiness", encoded_status)
            self.assertNotIn("trigger_robot_action", encoded_status)
            self.assertNotIn("delivery_success", encoded_status)
            self.assertNotIn("playback_ready", encoded_status)
            self.assertNotIn("/cmd_vel", encoded_status)
            self.assertNotIn("/dev/ttyUSB0", encoded_status)
            self.assertNotIn("secret-token", encoded_status)

    def test_metadata_only_production_recovery_response_does_not_start_ack_or_persist_cursor(self):
        for recovery_state in ("blocked", "invalid", "stale"):
            with self.subTest(recovery_state=recovery_state):
                self.cloud.status_posts.clear()
                self.cloud.ack_posts.clear()
                self.backend.calls.clear()
                with tempfile.TemporaryDirectory() as tmpdir:
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-recovery-{recovery_state}",
                        cursor_state_path=state_path,
                    )
                    self.cloud.response_extras["command_response"] = {
                        "production_recovery": {
                            "schema": "trashbot.production_recovery_gate",
                            "schema_version": 1,
                            "state": recovery_state,
                            "evidence_boundary": "software_proof_docker_production_recovery_gate",
                            "safe_summary": "生产恢复 gate 当前阻塞。",
                            "retry_hint": "contact_support",
                            "next_action": "collect",
                            "trigger_robot_action": "collect",
                            "cursor_override": "cmd-future",
                            "production_ready": False,
                            "overall_status": "blocked",
                            "delivery_success": True,
                            "not_proven": [
                                "real_production_backup_policy",
                                "real_disaster_recovery",
                                "wave_rover_hil",
                            ],
                        },
                        "preflight": {"overall_status": "blocked", "production_ready": False},
                    }

                    handled = worker.poll_once()

                    # 只有 production recovery metadata、没有 command envelope 时，不能执行动作、ACK 或推进游标。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-recovery-{recovery_state}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn("production_recovery", encoded_status)
                    self.assertNotIn("production_recovery_gate", encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)

    def test_metadata_only_deployment_readiness_response_does_not_start_ack_or_persist_cursor(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                last_ack_id="cmd-before-deployment-readiness",
                cursor_state_path=state_path,
            )
            self.cloud.response_extras["command_response"] = {
                "deployment_readiness": {
                    "schema": "trashbot.cloud_deployment_readiness",
                    "schema_version": 1,
                    "production_ready": False,
                    "overall_status": "blocked",
                    "evidence_boundary": "software_proof_docker_cloud_deployment_readiness_gate",
                    "safe_summary": "云部署就绪检查仍是 blocked-by-design。",
                    "not_proven": ["real_cloud", "https_tls", "4g_sim", "wave_rover_hil"],
                    "trigger_robot_action": "collect",
                    "raw_ros_topic": "/cmd_vel",
                    "delivery_success": True,
                    "raw_credential": "secret-token",
                },
                "cloud_deployment_readiness": {
                    "schema": "trashbot.cloud_deployment_readiness",
                    "production_ready": False,
                    "credential_url": "https://user:secret@example.invalid",
                    "Authorization": "Bearer must-not-leak",
                },
                "preflight": {
                    "production_ready": False,
                    "evidence_boundary": "software_proof_docker_cloud_deployment_readiness_gate",
                },
            }

            handled = worker.poll_once()

            # deployment metadata 是云部署诊断，不是 robot command；没有 command envelope 时必须 fail-closed。
            self.assertFalse(handled)
            self.assertEqual(self.backend.calls, [])
            self.assertEqual(self.cloud.ack_posts, [])
            self.assertEqual(worker.last_ack_id, "cmd-before-deployment-readiness")
            self.assertFalse(state_path.exists())
            self.assertEqual(len(self.cloud.status_posts), 1)
            encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
            self.assertNotIn("deployment_readiness", encoded_status)
            self.assertNotIn("cloud_deployment_readiness", encoded_status)
            self.assertNotIn("trigger_robot_action", encoded_status)
            self.assertNotIn("delivery_success", encoded_status)
            self.assertNotIn("/cmd_vel", encoded_status)
            self.assertNotIn("raw_credential", encoded_status)
            self.assertNotIn("secret-token", encoded_status)
            self.assertNotIn("Authorization", encoded_status)
            self.assertNotIn("credential_url", encoded_status)

    def test_metadata_only_operation_log_response_does_not_start_ack_or_persist_cursor(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                last_ack_id="cmd-before-operation-log",
                cursor_state_path=state_path,
            )
            self.cloud.response_extras["command_response"] = {
                "operation_log": {
                    "schema": "trashbot.phone_operation_log.v1",
                    "events": [
                        {
                            "kind": "manual_takeover",
                            "safe_phone_copy": "需要人工接管，已准备支持摘要。",
                        },
                    ],
                    "support_handoff": {"enabled": True, "next_action": "collect"},
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-operation-log",
                    "ack_semantics": "delivery_success",
                    "delivery_success": True,
                    "raw_ros_topic": "/cmd_vel",
                    "Authorization": "Bearer must-not-leak",
                },
                "phone_operation_log": {
                    "schema": "trashbot.phone_operation_log.v1",
                    "support_handoff": {"next_action": "cancel"},
                    "delivery_success": True,
                },
                "preflight": {"production_ready": False, "overall_status": "blocked"},
            }

            handled = worker.poll_once()

            # 只有 operation log metadata、没有 command envelope 时，不能驱动本地 action/ACK/cursor。
            self.assertFalse(handled)
            self.assertEqual(self.backend.calls, [])
            self.assertEqual(self.cloud.ack_posts, [])
            self.assertEqual(worker.last_ack_id, "cmd-before-operation-log")
            self.assertFalse(state_path.exists())
            self.assertEqual(len(self.cloud.status_posts), 1)
            self.assertIn("last_ack_id=cmd-before-operation-log", self.cloud.get_paths[-1])
            encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
            self.assertNotIn("operation_log", encoded_status)
            self.assertNotIn("phone_operation_log", encoded_status)
            self.assertNotIn("support_handoff", encoded_status)
            self.assertNotIn("trigger_robot_action", encoded_status)
            self.assertNotIn("cursor_override", encoded_status)
            self.assertNotIn("delivery_success", encoded_status)
            self.assertNotIn("/cmd_vel", encoded_status)
            self.assertNotIn("Authorization", encoded_status)

    def test_metadata_only_mobile_primary_journey_response_does_not_start_ack_or_persist_cursor(self):
        metadata_cases = (
            (
                "mobile_primary_journey_gate",
                {
                    "schema": "trashbot.mobile_primary_journey_gate.v1",
                    "destination": "trash_station",
                    "load_confirmation_required": True,
                    "command_safety_summary": {"start_enabled": True, "cancel_enabled": True},
                    "browser_gate": "software_proof_only",
                    "device_gate": "not_proven",
                    "cloud_gate": "not_proven",
                    "operation_log": {"pending_ack": True},
                    "action_feedback": {"receipt_state": "accepted"},
                    "not_proven": ["delivery_success", "dropoff_success", "hil_pass"],
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-primary-journey-gate",
                    "delivery_success": True,
                },
            ),
            (
                "mobile_primary_journey_summary",
                {
                    "schema": "trashbot.mobile_primary_journey_summary.v1",
                    "safe_phone_copy": "主路径摘要只说明手机下一步，不是机器人执行结果。",
                    "ack_semantics": "accepted_processing_only",
                    "browser_gate": "software_proof_only",
                    "device_gate": "not_proven",
                    "cloud_gate": "not_proven",
                    "not_proven": [
                        "robot_command",
                        "ack",
                        "cursor",
                        "delivery_success",
                        "dropoff_success",
                        "cancel_completion",
                        "production_readiness",
                        "hil_pass",
                    ],
                    "next_action": "confirm_dropoff",
                    "dropoff_success": True,
                    "cancel_completed": True,
                    "production_ready": True,
                    "hil_pass": True,
                    "raw_ros_topic": "/cmd_vel",
                    "Authorization": "Bearer must-not-leak",
                },
            ),
        )
        for metadata_name, metadata in metadata_cases:
            with self.subTest(metadata_name=metadata_name):
                with tempfile.TemporaryDirectory() as tmpdir:
                    self.backend.calls.clear()
                    self.cloud.status_posts.clear()
                    self.cloud.ack_posts.clear()
                    self.cloud.get_paths.clear()
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-{metadata_name}",
                        cursor_state_path=state_path,
                    )
                    self.cloud.response_extras["command_response"] = {metadata_name: metadata}

                    handled = worker.poll_once()

                    # 主路径摘要只服务手机/支持面；没有 command envelope 时不能驱动 action/ACK/cursor。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-{metadata_name}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    self.assertIn(f"last_ack_id=cmd-before-{metadata_name}", self.cloud.get_paths[-1])
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn(metadata_name, encoded_status)
                    self.assertNotIn("operation_log", encoded_status)
                    self.assertNotIn("action_feedback", encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)
                    self.assertNotIn("dropoff_success", encoded_status)
                    self.assertNotIn("cancel_completed", encoded_status)
                    self.assertNotIn("production_ready", encoded_status)
                    self.assertNotIn("hil_pass", encoded_status)
                    self.assertNotIn("/cmd_vel", encoded_status)
                    self.assertNotIn("Authorization", encoded_status)
                    self.cloud.response_extras["command_response"] = {}

    def test_mobile_primary_journey_metadata_is_ignored_by_valid_collect_envelope(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                last_ack_id="cmd-before-primary-journey",
                cursor_state_path=state_path,
            )
            self.cloud.response_extras.update({
                "status_response": {
                    "mobile_primary_journey_summary": {
                        "schema": "trashbot.mobile_primary_journey_summary.v1",
                        "delivery_success": True,
                        "trigger_robot_action": "cancel",
                    },
                },
                "command_response": {
                    "mobile_primary_journey_gate": {
                        "schema": "trashbot.mobile_primary_journey_gate.v1",
                        "destination": "trash_station",
                        "load_confirmation_required": True,
                        "command_safety_summary": {"start_enabled": True},
                        "browser_gate": "software_proof_only",
                        "device_gate": "not_proven",
                        "cloud_gate": "not_proven",
                        "operation_log": {"pending_ack": True},
                        "action_feedback": {"receipt_state": "accepted"},
                        "trigger_robot_action": "cancel",
                        "cursor_override": "cmd-primary-journey-override",
                        "delivery_success": True,
                    },
                    "mobile_primary_journey_summary": {
                        "schema": "trashbot.mobile_primary_journey_summary.v1",
                        "ack_semantics": "delivery_success",
                        "next_action": "confirm_dropoff",
                        "dropoff_success": True,
                        "cancel_completed": True,
                        "production_ready": True,
                        "hil_pass": True,
                        "raw_ros_topic": "/cmd_vel",
                    },
                },
                "ack_response": {
                    "mobile_primary_journey_summary": {
                        "schema": "trashbot.mobile_primary_journey_summary.v1",
                        "delivery_success": True,
                        "final_state": "DELIVERED",
                    },
                },
            })
            self.cloud.commands.append({
                "id": "cmd-primary-journey-collect",
                "type": "collect",
                "payload": {"target": "trash_station", "trash_type": 0},
            })

            self.assertTrue(worker.poll_once())

            self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
            self.assertEqual(worker.last_ack_id, "cmd-primary-journey-collect")
            self.assertIn("last_ack_id=cmd-before-primary-journey", self.cloud.get_paths[-1])
            cursor_payload = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(cursor_payload["last_terminal_ack_id"], "cmd-primary-journey-collect")
            ack_payload = self.cloud.ack_posts[0]
            self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
            self.assertEqual(ack_payload["command_id"], "cmd-primary-journey-collect")
            self.assertEqual(ack_payload["state"], "acked")
            self.assertEqual(ack_payload["message"], "collect")
            encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
            # 有效 collect 混入主路径 metadata 时，执行、ACK、cursor 仍只跟随 command envelope。
            self.assertNotIn("mobile_primary_journey_gate", encoded_ack)
            self.assertNotIn("mobile_primary_journey_summary", encoded_ack)
            self.assertNotIn("operation_log", encoded_ack)
            self.assertNotIn("action_feedback", encoded_ack)
            self.assertNotIn("trigger_robot_action", encoded_ack)
            self.assertNotIn("cursor_override", encoded_ack)
            self.assertNotIn("delivery_success", encoded_ack)
            self.assertNotIn("dropoff_success", encoded_ack)
            self.assertNotIn("cancel_completed", encoded_ack)
            self.assertNotIn("production_ready", encoded_ack)
            self.assertNotIn("hil_pass", encoded_ack)
            self.assertNotIn("/cmd_vel", encoded_ack)
            self.assertNotIn("DELIVERED", encoded_ack)

    def test_metadata_only_mobile_recovery_decision_response_does_not_start_ack_or_persist_cursor(self):
        metadata_cases = (
            (
                "mobile_recovery_decision_gate",
                {
                    "schema": "trashbot.mobile_recovery_decision_gate.v1",
                    "recovery_state": "pending_ack",
                    "next_action": "wait_for_command_ack",
                    "blocking_reason": "cloud_ack_pending",
                    "support_entry": {"available": True, "reason": "pending_ack_timeout"},
                    "ack_semantics": "accepted_processing_only",
                    "evidence_boundary": "software_proof_docker_mobile_recovery_decision_gate",
                    "not_proven": [
                        "robot_command",
                        "ack",
                        "cursor",
                        "delivery_success",
                        "dropoff_success",
                        "cancel_completion",
                        "production_readiness",
                        "hil_pass",
                    ],
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-recovery-decision-gate",
                    "delivery_success": True,
                },
            ),
            (
                "mobile_recovery_decision_summary",
                {
                    "schema": "trashbot.mobile_recovery_decision_summary.v1",
                    "recovery_state": "manual_takeover",
                    "safe_phone_copy": "恢复决策只说明下一步，不是机器人执行结果。",
                    "next_action": "manual_takeover",
                    "blocking_reason": "operator_intervention_required",
                    "support_entry": {"label": "联系支持", "next_action": "contact_support"},
                    "ack_semantics": "accepted_processing_only",
                    "evidence_boundary": "software_proof_docker_mobile_recovery_decision_gate",
                    "not_proven": [
                        "real_phone_device",
                        "robot_command",
                        "delivery_success",
                        "dropoff_success",
                        "cancel_completion",
                        "production_readiness",
                        "hil_pass",
                    ],
                    "dropoff_success": True,
                    "cancel_completed": True,
                    "production_ready": True,
                    "hil_pass": True,
                    "raw_ros_topic": "/cmd_vel",
                    "Authorization": "Bearer must-not-leak",
                },
            ),
        )
        for metadata_name, metadata in metadata_cases:
            with self.subTest(metadata_name=metadata_name):
                with tempfile.TemporaryDirectory() as tmpdir:
                    self.backend.calls.clear()
                    self.cloud.status_posts.clear()
                    self.cloud.ack_posts.clear()
                    self.cloud.get_paths.clear()
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-{metadata_name}",
                        cursor_state_path=state_path,
                    )
                    self.cloud.response_extras["command_response"] = {metadata_name: metadata}

                    handled = worker.poll_once()

                    # 恢复决策摘要只服务手机/支持面；没有 command envelope 时不能驱动 action/ACK/cursor。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-{metadata_name}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    self.assertIn(f"last_ack_id=cmd-before-{metadata_name}", self.cloud.get_paths[-1])
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn(metadata_name, encoded_status)
                    self.assertNotIn("support_entry", encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)
                    self.assertNotIn("dropoff_success", encoded_status)
                    self.assertNotIn("cancel_completed", encoded_status)
                    self.assertNotIn("production_ready", encoded_status)
                    self.assertNotIn("hil_pass", encoded_status)
                    self.assertNotIn("/cmd_vel", encoded_status)
                    self.assertNotIn("Authorization", encoded_status)
                    self.cloud.response_extras["command_response"] = {}

    def test_mobile_recovery_decision_metadata_is_ignored_by_valid_collect_envelope(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                last_ack_id="cmd-before-recovery-decision",
                cursor_state_path=state_path,
            )
            self.cloud.response_extras.update({
                "status_response": {
                    "mobile_recovery_decision_summary": {
                        "schema": "trashbot.mobile_recovery_decision_summary.v1",
                        "recovery_state": "pending_ack",
                        "delivery_success": True,
                        "trigger_robot_action": "cancel",
                    },
                },
                "command_response": {
                    "mobile_recovery_decision_gate": {
                        "schema": "trashbot.mobile_recovery_decision_gate.v1",
                        "recovery_state": "offline",
                        "next_action": "wait_reconnect",
                        "blocking_reason": "status_stale",
                        "support_entry": {"available": True},
                        "ack_semantics": "accepted_processing_only",
                        "evidence_boundary": "software_proof_docker_mobile_recovery_decision_gate",
                        "not_proven": ["delivery_success", "cancel_completion", "hil_pass"],
                        "trigger_robot_action": "cancel",
                        "cursor_override": "cmd-recovery-decision-override",
                        "delivery_success": True,
                    },
                    "mobile_recovery_decision_summary": {
                        "schema": "trashbot.mobile_recovery_decision_summary.v1",
                        "recovery_state": "blocked",
                        "next_action": "manual_takeover",
                        "blocking_reason": "manual_takeover_required",
                        "support_entry": {"next_action": "contact_support"},
                        "ack_semantics": "delivery_success",
                        "dropoff_success": True,
                        "cancel_completed": True,
                        "production_ready": True,
                        "hil_pass": True,
                        "raw_ros_topic": "/cmd_vel",
                    },
                },
                "ack_response": {
                    "mobile_recovery_decision_summary": {
                        "schema": "trashbot.mobile_recovery_decision_summary.v1",
                        "delivery_success": True,
                        "final_state": "DELIVERED",
                    },
                },
            })
            self.cloud.commands.append({
                "id": "cmd-recovery-decision-collect",
                "type": "collect",
                "payload": {"target": "trash_station", "trash_type": 0},
            })

            self.assertTrue(worker.poll_once())

            self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
            self.assertEqual(worker.last_ack_id, "cmd-recovery-decision-collect")
            self.assertIn("last_ack_id=cmd-before-recovery-decision", self.cloud.get_paths[-1])
            cursor_payload = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(cursor_payload["last_terminal_ack_id"], "cmd-recovery-decision-collect")
            ack_payload = self.cloud.ack_posts[0]
            self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
            self.assertEqual(ack_payload["command_id"], "cmd-recovery-decision-collect")
            self.assertEqual(ack_payload["state"], "acked")
            self.assertEqual(ack_payload["message"], "collect")
            encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
            # 有效 collect 混入恢复决策 metadata 时，执行、ACK、cursor 仍只跟随 command envelope。
            self.assertNotIn("mobile_recovery_decision_gate", encoded_ack)
            self.assertNotIn("mobile_recovery_decision_summary", encoded_ack)
            self.assertNotIn("support_entry", encoded_ack)
            self.assertNotIn("trigger_robot_action", encoded_ack)
            self.assertNotIn("cursor_override", encoded_ack)
            self.assertNotIn("delivery_success", encoded_ack)
            self.assertNotIn("dropoff_success", encoded_ack)
            self.assertNotIn("cancel_completed", encoded_ack)
            self.assertNotIn("production_ready", encoded_ack)
            self.assertNotIn("hil_pass", encoded_ack)
            self.assertNotIn("/cmd_vel", encoded_ack)
            self.assertNotIn("DELIVERED", encoded_ack)

    def test_metadata_only_mobile_terminal_action_confirmation_response_does_not_start_ack_or_persist_cursor(self):
        metadata_cases = (
            (
                "mobile_terminal_action_confirmation_gate",
                {
                    "schema": "trashbot.mobile_terminal_action_confirmation_gate.v1",
                    "action": "confirm_dropoff",
                    "risk_copy": "确认投放会通知机器人处理，但不代表投放完成。",
                    "ack_semantics": "accepted_processing_only",
                    "client_reference": "terminal-action-gate-001",
                    "evidence_boundary": "software_proof_docker_mobile_terminal_action_confirmation_gate",
                    "not_proven": [
                        "robot_command",
                        "ack",
                        "cursor",
                        "delivery_success",
                        "dropoff_success",
                        "cancel_completion",
                        "production_readiness",
                        "hil_pass",
                    ],
                    "safe_phone_copy": "二次确认面板只供手机显示，不会直接控制机器人。",
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-terminal-action-gate",
                    "delivery_success": True,
                },
            ),
            (
                "mobile_terminal_action_confirmation_summary",
                {
                    "schema": "trashbot.mobile_terminal_action_confirmation_summary.v1",
                    "action": "cancel",
                    "risk_copy": "取消提交后仍需等待状态回传，不能视为取消完成。",
                    "ack_semantics": "accepted_processing_only",
                    "client_reference": "terminal-action-summary-001",
                    "evidence_boundary": "software_proof_docker_mobile_terminal_action_confirmation_gate",
                    "not_proven": [
                        "robot_command",
                        "ack",
                        "cursor",
                        "delivery_success",
                        "dropoff_success",
                        "cancel_completion",
                        "production_readiness",
                        "hil_pass",
                    ],
                    "safe_phone_copy": "终端动作摘要是手机/支持信息，不是 ACK 或 cursor。",
                    "dropoff_success": True,
                    "cancel_completed": True,
                    "production_ready": True,
                    "hil_pass": True,
                    "raw_ros_topic": "/cmd_vel",
                    "Authorization": "Bearer must-not-leak",
                },
            ),
        )
        for metadata_name, metadata in metadata_cases:
            with self.subTest(metadata_name=metadata_name):
                with tempfile.TemporaryDirectory() as tmpdir:
                    self.backend.calls.clear()
                    self.cloud.status_posts.clear()
                    self.cloud.ack_posts.clear()
                    self.cloud.get_paths.clear()
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-{metadata_name}",
                        cursor_state_path=state_path,
                    )
                    self.cloud.response_extras["command_response"] = {metadata_name: metadata}

                    handled = worker.poll_once()

                    # 终端动作二次确认只服务手机面板；没有 command envelope 时不能有副作用。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-{metadata_name}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    self.assertIn(f"last_ack_id=cmd-before-{metadata_name}", self.cloud.get_paths[-1])
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn(metadata_name, encoded_status)
                    self.assertNotIn("risk_copy", encoded_status)
                    self.assertNotIn("client_reference", encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)
                    self.assertNotIn("dropoff_success", encoded_status)
                    self.assertNotIn("cancel_completed", encoded_status)
                    self.assertNotIn("production_ready", encoded_status)
                    self.assertNotIn("hil_pass", encoded_status)
                    self.assertNotIn("/cmd_vel", encoded_status)
                    self.assertNotIn("Authorization", encoded_status)
                    self.cloud.response_extras["command_response"] = {}

    def test_mobile_terminal_action_confirmation_metadata_is_ignored_by_valid_command_envelope(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                last_ack_id="cmd-before-terminal-action",
                cursor_state_path=state_path,
            )
            self.cloud.response_extras.update({
                "status_response": {
                    "mobile_terminal_action_confirmation_summary": {
                        "schema": "trashbot.mobile_terminal_action_confirmation_summary.v1",
                        "delivery_success": True,
                        "trigger_robot_action": "collect",
                    },
                },
                "command_response": {
                    "mobile_terminal_action_confirmation_gate": {
                        "schema": "trashbot.mobile_terminal_action_confirmation_gate.v1",
                        "action": "confirm_dropoff",
                        "risk_copy": "确认投放需要用户二次确认。",
                        "ack_semantics": "delivery_success",
                        "client_reference": "terminal-action-gate-002",
                        "evidence_boundary": "software_proof_docker_mobile_terminal_action_confirmation_gate",
                        "not_proven": ["delivery_success", "dropoff_success", "hil_pass"],
                        "safe_phone_copy": "ACK 只代表 accepted/processing。",
                        "trigger_robot_action": "collect",
                        "cursor_override": "cmd-terminal-action-override",
                        "delivery_success": True,
                    },
                    "mobile_terminal_action_confirmation_summary": {
                        "schema": "trashbot.mobile_terminal_action_confirmation_summary.v1",
                        "action": "cancel",
                        "risk_copy": "取消完成需要后续状态证明。",
                        "ack_semantics": "delivery_success",
                        "client_reference": "terminal-action-summary-002",
                        "evidence_boundary": "software_proof_docker_mobile_terminal_action_confirmation_gate",
                        "dropoff_success": True,
                        "cancel_completed": True,
                        "production_ready": True,
                        "hil_pass": True,
                        "raw_ros_topic": "/cmd_vel",
                    },
                },
                "ack_response": {
                    "mobile_terminal_action_confirmation_summary": {
                        "schema": "trashbot.mobile_terminal_action_confirmation_summary.v1",
                        "delivery_success": True,
                        "final_state": "DELIVERED",
                    },
                },
            })
            self.cloud.commands.append({
                "id": "cmd-terminal-action-confirm-dropoff",
                "type": "confirm_dropoff",
                "payload": {"accepted": True},
            })

            self.assertTrue(worker.poll_once())

            self.assertEqual(self.backend.calls, [("confirm_dropoff", True)])
            self.assertEqual(worker.last_ack_id, "cmd-terminal-action-confirm-dropoff")
            self.assertIn("last_ack_id=cmd-before-terminal-action", self.cloud.get_paths[-1])
            cursor_payload = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(cursor_payload["last_terminal_ack_id"], "cmd-terminal-action-confirm-dropoff")
            ack_payload = self.cloud.ack_posts[0]
            self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
            self.assertEqual(ack_payload["command_id"], "cmd-terminal-action-confirm-dropoff")
            self.assertEqual(ack_payload["state"], "acked")
            self.assertEqual(ack_payload["message"], "confirm_dropoff")
            encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
            # 有效 command 混入终端动作 metadata 时，执行、ACK、cursor 仍只跟随 command envelope。
            self.assertNotIn("mobile_terminal_action_confirmation_gate", encoded_ack)
            self.assertNotIn("mobile_terminal_action_confirmation_summary", encoded_ack)
            self.assertNotIn("risk_copy", encoded_ack)
            self.assertNotIn("client_reference", encoded_ack)
            self.assertNotIn("trigger_robot_action", encoded_ack)
            self.assertNotIn("cursor_override", encoded_ack)
            self.assertNotIn("delivery_success", encoded_ack)
            self.assertNotIn("dropoff_success", encoded_ack)
            self.assertNotIn("cancel_completed", encoded_ack)
            self.assertNotIn("production_ready", encoded_ack)
            self.assertNotIn("hil_pass", encoded_ack)
            self.assertNotIn("/cmd_vel", encoded_ack)
            self.assertNotIn("DELIVERED", encoded_ack)

    def test_metadata_only_mobile_device_evidence_capture_response_does_not_start_ack_or_persist_cursor(self):
        metadata_cases = (
            (
                "mobile_device_evidence_capture",
                {
                    "schema": "trashbot.mobile_device_evidence_capture.v1",
                    "capture_state": "ready_for_upload",
                    "device_label": "phone-camera",
                    "evidence_boundary": "software_proof_docker_mobile_device_evidence_capture_gate",
                    "not_proven": [
                        "robot_command",
                        "ack",
                        "cursor",
                        "delivery_success",
                        "real_phone_device",
                        "hil_pass",
                    ],
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-device-capture",
                    "delivery_success": True,
                },
            ),
            (
                "mobile_device_evidence_capture_summary",
                {
                    "schema": "trashbot.mobile_device_evidence_capture_summary.v1",
                    "safe_phone_copy": "设备取证摘要只供手机和支持侧查看。",
                    "ack_semantics": "accepted_processing_only",
                    "next_action": "confirm_dropoff",
                    "evidence_boundary": "software_proof_docker_mobile_device_evidence_capture_gate",
                    "delivery_success": True,
                    "production_ready": True,
                    "hil_pass": True,
                    "raw_ros_topic": "/cmd_vel",
                },
            ),
            (
                "mobile_device_evidence_package",
                {
                    "schema": "trashbot.mobile_device_evidence_package.v1",
                    "attachments": [{"kind": "photo", "url": "https://user:secret@example.invalid/photo.jpg"}],
                    "device_capture_status": "uploaded_to_support",
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-device-package",
                    "real_device_proof": True,
                    "wave_rover_feedback": True,
                    "Authorization": "Bearer must-not-leak",
                    "serial_device": "/dev/ttyUSB0",
                },
            ),
        )
        for metadata_name, metadata in metadata_cases:
            with self.subTest(metadata_name=metadata_name):
                with tempfile.TemporaryDirectory() as tmpdir:
                    self.backend.calls.clear()
                    self.cloud.status_posts.clear()
                    self.cloud.ack_posts.clear()
                    self.cloud.get_paths.clear()
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-{metadata_name}",
                        cursor_state_path=state_path,
                    )
                    self.cloud.response_extras["command_response"] = {metadata_name: metadata}

                    handled = worker.poll_once()

                    # 设备取证 metadata 只服务手机/支持侧；没有 command envelope 时不能有 robot 副作用。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-{metadata_name}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    self.assertIn(f"last_ack_id=cmd-before-{metadata_name}", self.cloud.get_paths[-1])
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn(metadata_name, encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)
                    self.assertNotIn("production_ready", encoded_status)
                    self.assertNotIn("hil_pass", encoded_status)
                    self.assertNotIn("real_device_proof", encoded_status)
                    self.assertNotIn("wave_rover_feedback", encoded_status)
                    self.assertNotIn("/cmd_vel", encoded_status)
                    self.assertNotIn("/dev/ttyUSB0", encoded_status)
                    self.assertNotIn("Authorization", encoded_status)
                    self.assertNotIn("secret", encoded_status)
                    self.cloud.response_extras["command_response"] = {}

    def test_mobile_device_evidence_capture_metadata_is_ignored_by_valid_command_envelope(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                last_ack_id="cmd-before-device-evidence",
                cursor_state_path=state_path,
            )
            self.cloud.response_extras.update({
                "status_response": {
                    "mobile_device_evidence_capture_summary": {
                        "schema": "trashbot.mobile_device_evidence_capture_summary.v1",
                        "delivery_success": True,
                        "trigger_robot_action": "collect",
                    },
                },
                "command_response": {
                    "mobile_device_evidence_capture": {
                        "schema": "trashbot.mobile_device_evidence_capture.v1",
                        "capture_state": "ready_for_upload",
                        "evidence_boundary": "software_proof_docker_mobile_device_evidence_capture_gate",
                        "trigger_robot_action": "collect",
                        "cursor_override": "cmd-device-evidence-override",
                        "delivery_success": True,
                    },
                    "mobile_device_evidence_capture_summary": {
                        "schema": "trashbot.mobile_device_evidence_capture_summary.v1",
                        "ack_semantics": "delivery_success",
                        "next_action": "confirm_dropoff",
                        "production_ready": True,
                        "hil_pass": True,
                        "raw_ros_topic": "/cmd_vel",
                    },
                    "mobile_device_evidence_package": {
                        "schema": "trashbot.mobile_device_evidence_package.v1",
                        "attachments": [{"kind": "photo", "url": "https://user:secret@example.invalid/photo.jpg"}],
                        "real_device_proof": True,
                        "wave_rover_feedback": True,
                        "Authorization": "Bearer must-not-leak",
                        "serial_device": "/dev/ttyUSB0",
                    },
                },
                "ack_response": {
                    "mobile_device_evidence_package": {
                        "schema": "trashbot.mobile_device_evidence_package.v1",
                        "delivery_success": True,
                        "final_state": "DELIVERED",
                    },
                },
            })
            self.cloud.commands.append({
                "id": "cmd-device-evidence-cancel",
                "type": "cancel",
                "payload": {},
            })

            self.assertTrue(worker.poll_once())

            self.assertEqual(self.backend.calls, [("cancel",)])
            self.assertEqual(worker.last_ack_id, "cmd-device-evidence-cancel")
            self.assertIn("last_ack_id=cmd-before-device-evidence", self.cloud.get_paths[-1])
            cursor_payload = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(cursor_payload["last_terminal_ack_id"], "cmd-device-evidence-cancel")
            ack_payload = self.cloud.ack_posts[0]
            self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
            self.assertEqual(ack_payload["command_id"], "cmd-device-evidence-cancel")
            self.assertEqual(ack_payload["state"], "acked")
            self.assertEqual(ack_payload["message"], "cancel")
            encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
            # 有效 command 混入设备取证 metadata 时，执行、ACK、cursor 仍只跟随 command envelope。
            self.assertNotIn("mobile_device_evidence_capture", encoded_ack)
            self.assertNotIn("mobile_device_evidence_capture_summary", encoded_ack)
            self.assertNotIn("mobile_device_evidence_package", encoded_ack)
            self.assertNotIn("trigger_robot_action", encoded_ack)
            self.assertNotIn("cursor_override", encoded_ack)
            self.assertNotIn("delivery_success", encoded_ack)
            self.assertNotIn("production_ready", encoded_ack)
            self.assertNotIn("hil_pass", encoded_ack)
            self.assertNotIn("real_device_proof", encoded_ack)
            self.assertNotIn("wave_rover_feedback", encoded_ack)
            self.assertNotIn("/cmd_vel", encoded_ack)
            self.assertNotIn("/dev/ttyUSB0", encoded_ack)
            self.assertNotIn("Authorization", encoded_ack)
            self.assertNotIn("secret", encoded_ack)
            self.assertNotIn("DELIVERED", encoded_ack)
            encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
            self.assertNotIn("mobile_device_evidence_capture", encoded_status)
            self.assertNotIn("mobile_device_evidence_package", encoded_status)
            self.assertNotIn("delivery_success", encoded_status)

    def test_metadata_only_mobile_device_handoff_session_response_does_not_start_ack_or_persist_cursor(self):
        metadata_cases = (
            (
                "mobile_device_handoff_session",
                {
                    "schema": "trashbot.mobile_device_handoff_session.v1",
                    "session_state": "support_ready",
                    "handoff_target": "family_support",
                    "evidence_boundary": "software_proof_docker_mobile_device_handoff_session_gate",
                    "not_proven": [
                        "robot_command",
                        "ack",
                        "cursor",
                        "delivery_success",
                        "real_phone_device",
                        "hil_pass",
                    ],
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-handoff-session",
                    "delivery_success": True,
                },
            ),
            (
                "mobile_device_handoff_session_summary",
                {
                    "schema": "trashbot.mobile_device_handoff_session_summary.v1",
                    "safe_phone_copy": "设备交接会话只供手机和支持侧查看。",
                    "ack_semantics": "accepted_processing_only",
                    "next_action": "confirm_dropoff",
                    "evidence_boundary": "software_proof_docker_mobile_device_handoff_session_gate",
                    "delivery_success": True,
                    "production_ready": True,
                    "hil_pass": True,
                    "raw_ros_topic": "/cmd_vel",
                },
            ),
            (
                "mobile_device_handoff_package",
                {
                    "schema": "trashbot.mobile_device_handoff_package.v1",
                    "support_refs": [{"kind": "session", "url": "https://user:secret@example.invalid/session"}],
                    "handoff_status": "ready_for_support",
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-handoff-package",
                    "real_device_proof": True,
                    "wave_rover_feedback": True,
                    "Authorization": "Bearer must-not-leak",
                    "serial_device": "/dev/ttyUSB0",
                },
            ),
        )
        for metadata_name, metadata in metadata_cases:
            with self.subTest(metadata_name=metadata_name):
                with tempfile.TemporaryDirectory() as tmpdir:
                    self.backend.calls.clear()
                    self.cloud.status_posts.clear()
                    self.cloud.ack_posts.clear()
                    self.cloud.get_paths.clear()
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-{metadata_name}",
                        cursor_state_path=state_path,
                    )
                    self.cloud.response_extras["command_response"] = {metadata_name: metadata}

                    handled = worker.poll_once()

                    # 设备交接 metadata 只服务手机/支持侧；没有 command envelope 时不能有 robot 副作用。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-{metadata_name}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    self.assertIn(f"last_ack_id=cmd-before-{metadata_name}", self.cloud.get_paths[-1])
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn(metadata_name, encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)
                    self.assertNotIn("production_ready", encoded_status)
                    self.assertNotIn("hil_pass", encoded_status)
                    self.assertNotIn("real_device_proof", encoded_status)
                    self.assertNotIn("wave_rover_feedback", encoded_status)
                    self.assertNotIn("/cmd_vel", encoded_status)
                    self.assertNotIn("/dev/ttyUSB0", encoded_status)
                    self.assertNotIn("Authorization", encoded_status)
                    self.assertNotIn("secret", encoded_status)
                    self.cloud.response_extras["command_response"] = {}

    def test_mobile_device_handoff_session_metadata_is_ignored_by_valid_command_envelope(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                last_ack_id="cmd-before-handoff-session",
                cursor_state_path=state_path,
            )
            self.cloud.response_extras.update({
                "status_response": {
                    "mobile_device_handoff_session_summary": {
                        "schema": "trashbot.mobile_device_handoff_session_summary.v1",
                        "delivery_success": True,
                        "trigger_robot_action": "collect",
                    },
                },
                "command_response": {
                    "mobile_device_handoff_session": {
                        "schema": "trashbot.mobile_device_handoff_session.v1",
                        "session_state": "support_ready",
                        "evidence_boundary": "software_proof_docker_mobile_device_handoff_session_gate",
                        "trigger_robot_action": "collect",
                        "cursor_override": "cmd-handoff-session-override",
                        "delivery_success": True,
                    },
                    "mobile_device_handoff_session_summary": {
                        "schema": "trashbot.mobile_device_handoff_session_summary.v1",
                        "ack_semantics": "delivery_success",
                        "next_action": "confirm_dropoff",
                        "production_ready": True,
                        "hil_pass": True,
                        "raw_ros_topic": "/cmd_vel",
                    },
                    "mobile_device_handoff_package": {
                        "schema": "trashbot.mobile_device_handoff_package.v1",
                        "support_refs": [{"kind": "session", "url": "https://user:secret@example.invalid/session"}],
                        "real_device_proof": True,
                        "wave_rover_feedback": True,
                        "Authorization": "Bearer must-not-leak",
                        "serial_device": "/dev/ttyUSB0",
                    },
                },
                "ack_response": {
                    "mobile_device_handoff_package": {
                        "schema": "trashbot.mobile_device_handoff_package.v1",
                        "delivery_success": True,
                        "final_state": "DELIVERED",
                    },
                },
            })
            self.cloud.commands.append({
                "id": "cmd-handoff-session-confirm",
                "type": "confirm_dropoff",
                "payload": {"accepted": True},
            })

            self.assertTrue(worker.poll_once())

            self.assertEqual(self.backend.calls, [("confirm_dropoff", True)])
            self.assertEqual(worker.last_ack_id, "cmd-handoff-session-confirm")
            self.assertIn("last_ack_id=cmd-before-handoff-session", self.cloud.get_paths[-1])
            cursor_payload = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(cursor_payload["last_terminal_ack_id"], "cmd-handoff-session-confirm")
            ack_payload = self.cloud.ack_posts[0]
            self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
            self.assertEqual(ack_payload["command_id"], "cmd-handoff-session-confirm")
            self.assertEqual(ack_payload["state"], "acked")
            self.assertEqual(ack_payload["message"], "confirm_dropoff")
            encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
            # 有效 command 混入设备交接 metadata 时，执行、ACK、cursor 仍只跟随 command envelope。
            self.assertNotIn("mobile_device_handoff_session", encoded_ack)
            self.assertNotIn("mobile_device_handoff_session_summary", encoded_ack)
            self.assertNotIn("mobile_device_handoff_package", encoded_ack)
            self.assertNotIn("trigger_robot_action", encoded_ack)
            self.assertNotIn("cursor_override", encoded_ack)
            self.assertNotIn("delivery_success", encoded_ack)
            self.assertNotIn("production_ready", encoded_ack)
            self.assertNotIn("hil_pass", encoded_ack)
            self.assertNotIn("real_device_proof", encoded_ack)
            self.assertNotIn("wave_rover_feedback", encoded_ack)
            self.assertNotIn("/cmd_vel", encoded_ack)
            self.assertNotIn("/dev/ttyUSB0", encoded_ack)
            self.assertNotIn("Authorization", encoded_ack)
            self.assertNotIn("secret", encoded_ack)
            self.assertNotIn("DELIVERED", encoded_ack)
            encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
            self.assertNotIn("mobile_device_handoff_session", encoded_status)
            self.assertNotIn("mobile_device_handoff_package", encoded_status)
            self.assertNotIn("delivery_success", encoded_status)

    def test_metadata_only_cloud_external_probe_response_does_not_start_ack_or_persist_cursor(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                last_ack_id="cmd-before-cloud-external-probe",
                cursor_state_path=state_path,
            )
            self.cloud.response_extras["command_response"] = {
                "cloud_external_probe": {
                    "schema": "trashbot.cloud_external_probe_bundle",
                    "schema_version": 1,
                    "evidence_boundary": "software_proof_docker_cloud_external_probe_bundle_gate",
                    "endpoint_results": {
                        "/healthz": {"status": "ok", "delivery_success": True},
                        "/readyz": {"status": "blocked", "next_action": "collect"},
                        "/preflightz": {"status": "blocked", "trigger_robot_action": "cancel"},
                    },
                    "production_ready": False,
                    "overall_status": "blocked",
                    "cursor_override": "cmd-external-probe",
                    "delivery_success": True,
                    "Authorization": "Bearer must-not-leak",
                },
                "cloud_external_probe_bundle": {
                    "schema": "trashbot.cloud_external_probe_bundle",
                    "safe_summary": "external probe 只是部署诊断摘要。",
                    "retry_hint": "configure_public_url",
                    "trigger_robot_action": "collect",
                    "delivery_success": True,
                },
                "deployment_readiness": {
                    "schema": "trashbot.cloud_deployment_readiness",
                    "production_ready": False,
                    "overall_status": "blocked",
                },
                "cloud_deployment_readiness": {
                    "schema": "trashbot.cloud_deployment_readiness",
                    "production_ready": False,
                    "overall_status": "blocked",
                },
                "preflight": {"production_ready": False, "overall_status": "blocked"},
            }

            handled = worker.poll_once()

            # external probe bundle 是云部署诊断，不是 command；没有 envelope 时不能有 action/ACK/cursor 副作用。
            self.assertFalse(handled)
            self.assertEqual(self.backend.calls, [])
            self.assertEqual(self.cloud.ack_posts, [])
            self.assertEqual(worker.last_ack_id, "cmd-before-cloud-external-probe")
            self.assertFalse(state_path.exists())
            self.assertEqual(len(self.cloud.status_posts), 1)
            self.assertIn("last_ack_id=cmd-before-cloud-external-probe", self.cloud.get_paths[-1])
            encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
            self.assertNotIn("cloud_external_probe", encoded_status)
            self.assertNotIn("cloud_external_probe_bundle", encoded_status)
            self.assertNotIn("deployment_readiness", encoded_status)
            self.assertNotIn("cloud_deployment_readiness", encoded_status)
            self.assertNotIn("preflight", encoded_status)
            self.assertNotIn("trigger_robot_action", encoded_status)
            self.assertNotIn("cursor_override", encoded_status)
            self.assertNotIn("delivery_success", encoded_status)
            self.assertNotIn("Authorization", encoded_status)

    def test_metadata_only_cloud_db_queue_external_probe_response_does_not_start_ack_or_persist_cursor(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                last_ack_id="cmd-before-db-queue-external-probe",
                cursor_state_path=state_path,
            )
            self.cloud.response_extras["command_response"] = {
                "cloud_db_queue_external_probe": {
                    "schema": "trashbot.cloud_db_queue_external_probe.v1",
                    "schema_version": 1,
                    "evidence_boundary": "software_proof_docker_cloud_db_queue_external_probe_gate",
                    "overall_status": "blocked",
                    "production_ready": False,
                    "db_probe_status": "not_proven",
                    "queue_probe_status": "not_proven",
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-db-queue-external-probe",
                    "delivery_success": True,
                    "db_probe_url": "postgres://user:secret@example.invalid/db",
                    "queue_probe_url": "amqp://user:secret@example.invalid/q",
                },
                "cloud_db_queue_external_probe_bundle": {
                    "schema": "trashbot.cloud_db_queue_external_probe_bundle",
                    "safe_summary": "DB/queue external probe 只是云端 readiness 元数据。",
                    "retry_hint": "configure_external_db_queue_probe",
                    "trigger_robot_action": "cancel",
                    "delivery_success": True,
                    "Authorization": "Bearer must-not-leak",
                },
                "db_queue_external_probe": {
                    "schema": "trashbot.db_queue_external_probe.v1",
                    "external_probe_status": "blocked",
                    "raw_ros_topic": "/cmd_vel",
                },
                "preflight": {"production_ready": False, "overall_status": "blocked"},
            }

            handled = worker.poll_once()

            # 只有 DB/queue external probe metadata 时，robot 侧必须保持 command/cursor fail-closed。
            self.assertFalse(handled)
            self.assertEqual(self.backend.calls, [])
            self.assertEqual(self.cloud.ack_posts, [])
            self.assertEqual(worker.last_ack_id, "cmd-before-db-queue-external-probe")
            self.assertFalse(state_path.exists())
            self.assertEqual(len(self.cloud.status_posts), 1)
            self.assertIn("last_ack_id=cmd-before-db-queue-external-probe", self.cloud.get_paths[-1])
            encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
            self.assertNotIn("cloud_db_queue_external_probe", encoded_status)
            self.assertNotIn("cloud_db_queue_external_probe_bundle", encoded_status)
            self.assertNotIn("db_queue_external_probe", encoded_status)
            self.assertNotIn("preflight", encoded_status)
            self.assertNotIn("trigger_robot_action", encoded_status)
            self.assertNotIn("cursor_override", encoded_status)
            self.assertNotIn("delivery_success", encoded_status)
            self.assertNotIn("postgres://", encoded_status)
            self.assertNotIn("amqp://", encoded_status)
            self.assertNotIn("/cmd_vel", encoded_status)
            self.assertNotIn("Authorization", encoded_status)

    def test_metadata_only_oss_cdn_live_probe_response_does_not_start_ack_or_persist_cursor(self):
        metadata_cases = (
            (
                "oss_cdn_live_probe",
                {
                    "schema": "trashbot.oss_cdn_live_probe.v1",
                    "schema_version": 1,
                    "evidence_boundary": "software_proof_docker_oss_cdn_live_probe_gate",
                    "overall_status": "blocked",
                    "production_ready": False,
                    "live_probe_complete": False,
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-oss-cdn-live-probe",
                    "delivery_success": True,
                    "credential_url": "https://user:secret@cdn.example.invalid/rober/private",
                },
            ),
            (
                "oss_cdn_live_probe_artifact",
                {
                    "schema": "trashbot.oss_cdn_live_probe_artifact.v1",
                    "safe_summary": "OSS/CDN live probe 只是手机/支持侧 readiness 元数据。",
                    "object_key_hash": "sha256:redacted",
                    "trigger_robot_action": "confirm_dropoff",
                    "delivery_success": True,
                    "Authorization": "Bearer must-not-leak",
                },
            ),
            (
                "cdn_live_probe",
                {
                    "schema": "trashbot.cdn_live_probe.v1",
                    "probe_status": "blocked",
                    "next_action": "cancel",
                    "raw_ros_topic": "/cmd_vel",
                },
            ),
        )
        for metadata_name, metadata in metadata_cases:
            with self.subTest(metadata_name=metadata_name):
                with tempfile.TemporaryDirectory() as tmpdir:
                    self.backend.calls.clear()
                    self.cloud.status_posts.clear()
                    self.cloud.ack_posts.clear()
                    self.cloud.get_paths.clear()
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-{metadata_name}",
                        cursor_state_path=state_path,
                    )
                    self.cloud.response_extras["command_response"] = {
                        metadata_name: metadata,
                        "preflight": {"production_ready": False, "overall_status": "blocked"},
                    }

                    handled = worker.poll_once()

                    # 只有 OSS/CDN live probe metadata 时，robot 侧必须保持 command/cursor fail-closed。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-{metadata_name}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    self.assertIn(f"last_ack_id=cmd-before-{metadata_name}", self.cloud.get_paths[-1])
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn(metadata_name, encoded_status)
                    self.assertNotIn("preflight", encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)
                    self.assertNotIn("credential_url", encoded_status)
                    self.assertNotIn("Authorization", encoded_status)
                    self.assertNotIn("/cmd_vel", encoded_status)
                    self.cloud.response_extras["command_response"] = {}

    def test_metadata_only_external_evidence_intake_response_does_not_start_ack_or_persist_cursor(self):
        metadata_cases = (
            (
                "external_evidence_intake",
                {
                    "schema": "trashbot.external_evidence_intake.v1",
                    "schema_version": 1,
                    "evidence_boundary": "software_proof_docker_external_evidence_intake_gate",
                    "overall_status": "blocked",
                    "production_ready": False,
                    "external_evidence_complete": False,
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-external-evidence",
                    "delivery_success": True,
                    "credential_url": "https://user:secret@example.invalid/proof",
                },
            ),
            (
                "external_evidence_intake_artifact",
                {
                    "schema": "trashbot.external_evidence_intake_artifact.v1",
                    "safe_summary": "外部证据 intake 只是云 readiness 证明入口。",
                    "public_ingress_tls": "not_proven",
                    "oss_cdn": "not_proven",
                    "production_db_queue": "not_proven",
                    "four_g_sim": "not_proven",
                    "trigger_robot_action": "confirm_dropoff",
                    "delivery_success": True,
                    "Authorization": "Bearer must-not-leak",
                },
            ),
            (
                "cloud_external_evidence",
                {
                    "schema": "trashbot.cloud_external_evidence.v1",
                    "external_evidence_complete": False,
                    "next_action": "cancel",
                    "cursor_override": "cmd-cloud-external-evidence",
                    "delivery_success": True,
                    "raw_ros_topic": "/cmd_vel",
                },
            ),
        )
        for metadata_name, metadata in metadata_cases:
            with self.subTest(metadata_name=metadata_name):
                with tempfile.TemporaryDirectory() as tmpdir:
                    self.backend.calls.clear()
                    self.cloud.status_posts.clear()
                    self.cloud.ack_posts.clear()
                    self.cloud.get_paths.clear()
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-{metadata_name}",
                        cursor_state_path=state_path,
                    )
                    self.cloud.response_extras["command_response"] = {
                        metadata_name: metadata,
                        "preflight": {"production_ready": False, "overall_status": "blocked"},
                    }

                    handled = worker.poll_once()

                    # 只有 external evidence intake metadata 时，不能触发动作、ACK 或游标推进。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-{metadata_name}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    self.assertIn(f"last_ack_id=cmd-before-{metadata_name}", self.cloud.get_paths[-1])
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn(metadata_name, encoded_status)
                    self.assertNotIn("preflight", encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)
                    self.assertNotIn("credential_url", encoded_status)
                    self.assertNotIn("Authorization", encoded_status)
                    self.assertNotIn("/cmd_vel", encoded_status)
                    self.cloud.response_extras["command_response"] = {}

    def test_metadata_only_cloud_hosted_pwa_response_does_not_start_ack_or_persist_cursor(self):
        metadata_cases = (
            (
                "cloud_hosted_pwa",
                {
                    "schema": "trashbot.cloud_hosted_pwa.v1",
                    "surface": "phone_static",
                    "hosted_url": "https://app.example.invalid/rober/",
                    "safe_phone_copy": "云托管 PWA 只是手机静态入口。",
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-cloud-hosted-pwa",
                    "delivery_success": True,
                    "raw_ros_topic": "/cmd_vel",
                },
            ),
            (
                "static_shell_metadata",
                {
                    "schema": "trashbot.static_shell_metadata.v1",
                    "manifest_url": "/manifest.webmanifest",
                    "start_url": "/",
                    "ack_semantics": "delivery_success",
                    "next_action": "confirm_dropoff",
                    "Authorization": "Bearer must-not-leak",
                },
            ),
            (
                "pwa_static_surface",
                {
                    "schema": "trashbot.pwa_static_surface.v1",
                    "evidence_boundary": "software_proof_docker_cloud_hosted_mobile_web_gate",
                    "static_get_only": True,
                    "next_action": "cancel",
                    "delivery_success": True,
                    "credential_url": "https://user:secret@example.invalid/pwa",
                },
            ),
        )
        for metadata_name, metadata in metadata_cases:
            with self.subTest(metadata_name=metadata_name):
                with tempfile.TemporaryDirectory() as tmpdir:
                    self.backend.calls.clear()
                    self.cloud.status_posts.clear()
                    self.cloud.ack_posts.clear()
                    self.cloud.get_paths.clear()
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-{metadata_name}",
                        cursor_state_path=state_path,
                    )
                    self.cloud.response_extras["command_response"] = {
                        metadata_name: metadata,
                        "cloud_hosted_mobile_web_gate": {
                            "schema": "trashbot.cloud_hosted_mobile_web_gate.v1",
                            "command_envelope_expanded": False,
                        },
                    }

                    handled = worker.poll_once()

                    # 只有云托管 PWA/static-shell metadata 时，不能触发动作、ACK 或游标推进。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-{metadata_name}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    self.assertIn(f"last_ack_id=cmd-before-{metadata_name}", self.cloud.get_paths[-1])
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn(metadata_name, encoded_status)
                    self.assertNotIn("cloud_hosted_mobile_web_gate", encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)
                    self.assertNotIn("credential_url", encoded_status)
                    self.assertNotIn("Authorization", encoded_status)
                    self.assertNotIn("/cmd_vel", encoded_status)
                    self.cloud.response_extras["command_response"] = {}

    def test_cloud_hosted_pwa_metadata_is_ignored_by_command_status_ack_envelope(self):
        self.cloud.response_extras.update({
            "status_response": {
                "cloud_hosted_pwa": {
                    "schema": "trashbot.cloud_hosted_pwa.v1",
                    "delivery_success": True,
                    "trigger_robot_action": "cancel",
                },
            },
            "command_response": {
                "cloud_hosted_pwa": {
                    "schema": "trashbot.cloud_hosted_pwa.v1",
                    "hosted_url": "https://app.example.invalid/rober/",
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-future",
                    "delivery_success": True,
                    "raw_ros_topic": "/cmd_vel",
                },
                "static_shell_metadata": {
                    "schema": "trashbot.static_shell_metadata.v1",
                    "manifest_url": "/manifest.webmanifest",
                    "ack_semantics": "delivery_success",
                    "next_action": "confirm_dropoff",
                },
                "pwa_static_surface": {
                    "schema": "trashbot.pwa_static_surface.v1",
                    "Authorization": "Bearer must-not-leak",
                    "credential_url": "https://user:secret@example.invalid/pwa",
                },
            },
            "ack_response": {
                "cloud_hosted_pwa": {
                    "schema": "trashbot.cloud_hosted_pwa.v1",
                    "delivery_success": True,
                    "final_state": "DELIVERED",
                },
            },
        })
        self.cloud.commands.append({
            "id": "cmd-cloud-hosted-pwa-extra",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
        })

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
        self.assertEqual(self.worker.last_ack_id, "cmd-cloud-hosted-pwa-extra")
        ack_payload = self.cloud.ack_posts[0]
        self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
        self.assertEqual(ack_payload["command_id"], "cmd-cloud-hosted-pwa-extra")
        self.assertEqual(ack_payload["state"], "acked")
        self.assertEqual(ack_payload["message"], "collect")
        encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
        # 有效 command 混入静态 PWA 元数据时，ACK 只能描述 command envelope 的处理结果。
        self.assertNotIn("cloud_hosted_pwa", encoded_ack)
        self.assertNotIn("static_shell_metadata", encoded_ack)
        self.assertNotIn("pwa_static_surface", encoded_ack)
        self.assertNotIn("trigger_robot_action", encoded_ack)
        self.assertNotIn("cursor_override", encoded_ack)
        self.assertNotIn("delivery_success", encoded_ack)
        self.assertNotIn("Authorization", encoded_ack)
        self.assertNotIn("credential_url", encoded_ack)
        self.assertNotIn("/cmd_vel", encoded_ack)
        self.assertNotIn("DELIVERED", encoded_ack)

    def test_metadata_only_mobile_pwa_installability_response_does_not_start_ack_or_persist_cursor(self):
        metadata_cases = (
            (
                "cloud_hosted_mobile_pwa_installability_gate",
                {
                    "schema": "trashbot.cloud_hosted_mobile_pwa_installability_gate.v1",
                    "installability_status": "software_proof_only",
                    "manifest_url": "/manifest.webmanifest",
                    "service_worker_url": "/service-worker.js",
                    "trigger_robot_action": "collect",
                    "cursor_override": "cmd-pwa-installability-gate",
                    "delivery_success": True,
                    "raw_ros_topic": "/cmd_vel",
                },
            ),
            (
                "pwa_installability_metadata",
                {
                    "schema": "trashbot.pwa_installability_metadata.v1",
                    "display": "standalone",
                    "start_url": "/",
                    "ack_semantics": "delivery_success",
                    "next_action": "confirm_dropoff",
                    "Authorization": "Bearer must-not-leak",
                },
            ),
            (
                "browser_installability_bundle",
                {
                    "schema": "trashbot.browser_installability_bundle.v1",
                    "browser_surface": "mobile",
                    "evidence_boundary": "software_proof_docker_mobile_pwa_installability_gate",
                    "next_action": "cancel",
                    "delivery_success": True,
                    "credential_url": "https://user:secret@example.invalid/install",
                },
            ),
        )
        for metadata_name, metadata in metadata_cases:
            with self.subTest(metadata_name=metadata_name):
                with tempfile.TemporaryDirectory() as tmpdir:
                    self.backend.calls.clear()
                    self.cloud.status_posts.clear()
                    self.cloud.ack_posts.clear()
                    self.cloud.get_paths.clear()
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-{metadata_name}",
                        cursor_state_path=state_path,
                    )
                    self.cloud.response_extras["command_response"] = {metadata_name: metadata}

                    handled = worker.poll_once()

                    # PWA installability/browser metadata 只服务手机静态面，不能驱动 robot action/ACK/cursor。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-{metadata_name}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    self.assertIn(f"last_ack_id=cmd-before-{metadata_name}", self.cloud.get_paths[-1])
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn(metadata_name, encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)
                    self.assertNotIn("credential_url", encoded_status)
                    self.assertNotIn("Authorization", encoded_status)
                    self.assertNotIn("/cmd_vel", encoded_status)
                    self.cloud.response_extras["command_response"] = {}

    def test_mobile_pwa_installability_metadata_is_ignored_by_valid_collect_envelope(self):
        self.cloud.response_extras.update({
            "status_response": {
                "pwa_installability_metadata": {
                    "schema": "trashbot.pwa_installability_metadata.v1",
                    "delivery_success": True,
                    "trigger_robot_action": "cancel",
                },
            },
            "command_response": {
                "cloud_hosted_mobile_pwa_installability_gate": {
                    "schema": "trashbot.cloud_hosted_mobile_pwa_installability_gate.v1",
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-future",
                    "delivery_success": True,
                    "raw_ros_topic": "/cmd_vel",
                },
                "pwa_installability_metadata": {
                    "schema": "trashbot.pwa_installability_metadata.v1",
                    "ack_semantics": "delivery_success",
                    "next_action": "confirm_dropoff",
                },
                "browser_installability_bundle": {
                    "schema": "trashbot.browser_installability_bundle.v1",
                    "Authorization": "Bearer must-not-leak",
                    "credential_url": "https://user:secret@example.invalid/install",
                },
            },
            "ack_response": {
                "browser_installability_bundle": {
                    "schema": "trashbot.browser_installability_bundle.v1",
                    "delivery_success": True,
                    "final_state": "DELIVERED",
                },
            },
        })
        self.cloud.commands.append({
            "id": "cmd-pwa-installability-extra",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
        })

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
        self.assertEqual(self.worker.last_ack_id, "cmd-pwa-installability-extra")
        ack_payload = self.cloud.ack_posts[0]
        self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
        self.assertEqual(ack_payload["command_id"], "cmd-pwa-installability-extra")
        self.assertEqual(ack_payload["state"], "acked")
        self.assertEqual(ack_payload["message"], "collect")
        encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
        # 有效 collect 混入 PWA installability metadata 时，执行和 ACK 仍只跟随 command envelope。
        self.assertNotIn("cloud_hosted_mobile_pwa_installability_gate", encoded_ack)
        self.assertNotIn("pwa_installability_metadata", encoded_ack)
        self.assertNotIn("browser_installability_bundle", encoded_ack)
        self.assertNotIn("trigger_robot_action", encoded_ack)
        self.assertNotIn("cursor_override", encoded_ack)
        self.assertNotIn("delivery_success", encoded_ack)
        self.assertNotIn("Authorization", encoded_ack)
        self.assertNotIn("credential_url", encoded_ack)
        self.assertNotIn("/cmd_vel", encoded_ack)
        self.assertNotIn("DELIVERED", encoded_ack)

    def test_public_ingress_tls_fields_are_ignored_by_command_status_ack_envelope(self):
        self.cloud.response_extras.update({
            "status_response": {
                "cloud_public_ingress_tls": {
                    "schema": "trashbot.cloud_public_ingress_tls.v1",
                    "production_ready": False,
                    "overall_status": "blocked",
                    "delivery_success": True,
                },
            },
            "command_response": {
                "cloud_public_ingress_tls": {
                    "schema": "trashbot.cloud_public_ingress_tls.v1",
                    "public_ingress_config_present": True,
                    "tls_config_present": True,
                    "external_probe_proven": False,
                    "next_action": "confirm_dropoff",
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-future",
                    "delivery_success": True,
                    "Authorization": "Bearer must-not-leak",
                    "raw_ros_topic": "/cmd_vel",
                },
                "public_ingress_tls": {
                    "schema": "trashbot.public_ingress_tls.v1",
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
            },
            "ack_response": {
                "cloud_public_ingress_tls": {
                    "schema": "trashbot.cloud_public_ingress_tls.v1",
                    "ack_semantics": "delivery_success",
                    "delivery_success": True,
                    "final_state": "DELIVERED",
                },
            },
        })
        self.cloud.commands.append({
            "id": "cmd-public-ingress-tls-extra",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
        })

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
        self.assertEqual(self.worker.last_ack_id, "cmd-public-ingress-tls-extra")
        ack_payload = self.cloud.ack_posts[0]
        self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
        self.assertEqual(ack_payload["command_id"], "cmd-public-ingress-tls-extra")
        self.assertEqual(ack_payload["state"], "acked")
        self.assertEqual(ack_payload["message"], "collect")
        encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
        # 公网入口/TLS readiness 是云部署元数据，ACK 只能表达本地 command envelope 处理结果。
        self.assertNotIn("cloud_public_ingress_tls", encoded_ack)
        self.assertNotIn("public_ingress_tls", encoded_ack)
        self.assertNotIn("cloud_public_ingress_tls_gate", encoded_ack)
        self.assertNotIn("deployment_readiness", encoded_ack)
        self.assertNotIn("trigger_robot_action", encoded_ack)
        self.assertNotIn("cursor_override", encoded_ack)
        self.assertNotIn("delivery_success", encoded_ack)
        self.assertNotIn("Authorization", encoded_ack)
        self.assertNotIn("credential_url", encoded_ack)
        self.assertNotIn("/cmd_vel", encoded_ack)
        self.assertNotIn("DELIVERED", encoded_ack)
        encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
        self.assertNotIn("cloud_public_ingress_tls", encoded_status)
        self.assertNotIn("public_ingress_tls", encoded_status)
        self.assertNotIn("cloud_public_ingress_tls_gate", encoded_status)
        self.assertNotIn("deployment_readiness", encoded_status)
        self.assertNotIn("delivery_success", encoded_status)
        self.assertEqual(self.cloud.status_posts[-1]["state"], "loaded_and_ready")
        self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_metadata_only_public_ingress_tls_response_does_not_start_ack_or_persist_cursor(self):
        metadata_cases = (
            "cloud_public_ingress_tls",
            "public_ingress_tls",
            "cloud_public_ingress_tls_gate",
            "deployment_readiness",
        )
        for metadata_name in metadata_cases:
            with self.subTest(metadata_name=metadata_name):
                self.cloud.status_posts.clear()
                self.cloud.ack_posts.clear()
                self.backend.calls.clear()
                with tempfile.TemporaryDirectory() as tmpdir:
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-{metadata_name}",
                        cursor_state_path=state_path,
                    )
                    self.cloud.response_extras["command_response"] = {
                        metadata_name: {
                            "schema": f"trashbot.{metadata_name}.v1",
                            "production_ready": False,
                            "overall_status": "blocked",
                            "public_ingress_config_present": True,
                            "tls_config_present": True,
                            "external_probe_proven": False,
                            "trigger_robot_action": "collect",
                            "next_action": "confirm_dropoff",
                            "cursor_override": "cmd-future",
                            "ack_semantics": "delivery_success",
                            "delivery_success": True,
                            "Authorization": "Bearer must-not-leak",
                            "credential_url": "https://user:secret@example.invalid",
                            "raw_ros_topic": "/cmd_vel",
                        },
                        "preflight": {"overall_status": "blocked", "production_ready": False},
                    }

                    handled = worker.poll_once()

                    # 只有公网入口/TLS readiness metadata、没有 command envelope 时，不能驱动 action/ACK/cursor。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-{metadata_name}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    self.assertIn(f"last_ack_id=cmd-before-{metadata_name}", self.cloud.get_paths[-1])
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn(metadata_name, encoded_status)
                    self.assertNotIn("preflight", encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("cursor_override", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)
                    self.assertNotIn("Authorization", encoded_status)
                    self.assertNotIn("credential_url", encoded_status)
                    self.assertNotIn("/cmd_vel", encoded_status)
                    self.cloud.response_extras["command_response"] = {}

    def test_transaction_isolation_fields_are_ignored_by_command_status_ack_envelope(self):
        self.cloud.response_extras.update({
            "status_response": {
                "transaction_isolation": {
                    "schema": "trashbot.transaction_isolation_drill",
                    "transaction_invariant": "passed",
                    "cursor_invariant": "passed",
                    "ack_invariant": "passed",
                    "delivery_success": True,
                },
            },
            "command_response": {
                "transaction_isolation": {
                    "schema": "trashbot.transaction_isolation_drill",
                    "overall_status": "passed",
                    "next_action": "confirm_dropoff",
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-future",
                },
                "diagnostics": {
                    "transaction_isolation": {
                        "delivery_success": True,
                        "final_state": "DELIVERED",
                    },
                },
            },
            "ack_response": {
                "transaction_isolation": {
                    "schema": "trashbot.transaction_isolation_drill",
                    "ack_semantics": "delivery_success",
                    "delivery_success": True,
                    "final_state": "DELIVERED",
                },
            },
        })
        self.cloud.commands.append({
            "id": "cmd-transaction-isolation-extra",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
        })

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
        self.assertEqual(self.worker.last_ack_id, "cmd-transaction-isolation-extra")
        ack_payload = self.cloud.ack_posts[0]
        self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
        self.assertEqual(ack_payload["command_id"], "cmd-transaction-isolation-extra")
        self.assertEqual(ack_payload["state"], "acked")
        self.assertEqual(ack_payload["message"], "collect")
        encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
        # transaction isolation 是云端状态/诊断元数据，robot ACK 只能表达 command envelope 处理结果。
        self.assertNotIn("transaction_isolation", encoded_ack)
        self.assertNotIn("trigger_robot_action", encoded_ack)
        self.assertNotIn("cursor_override", encoded_ack)
        self.assertNotIn("delivery_success", encoded_ack)
        self.assertNotIn("DELIVERED", encoded_ack)
        encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
        self.assertNotIn("transaction_isolation", encoded_status)
        self.assertNotIn("delivery_success", encoded_status)
        self.assertEqual(self.cloud.status_posts[-1]["state"], "loaded_and_ready")
        self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_cloud_relay_runtime_fields_are_ignored_by_command_status_ack_envelope(self):
        self.cloud.response_extras.update({
            "status_response": {
                "cloud_relay_runtime": {
                    "schema": "trashbot.cloud_relay_runtime.v1",
                    "source": "cloud-relay/src/ros2_trashbot_cloud_relay",
                    "production_ready": False,
                    "delivery_success": True,
                },
            },
            "command_response": {
                "cloud_relay_runtime": {
                    "schema": "trashbot.cloud_relay_runtime.v1",
                    "deployment_entrypoint": "cloud-relay/scripts/docker_smoke.sh",
                    "self_contained": True,
                    "trigger_robot_action": "cancel",
                    "cursor_override": "cmd-future",
                    "delivery_success": True,
                },
                "preflight": {"overall_status": "blocked", "production_ready": False},
            },
            "ack_response": {
                "cloud_relay_runtime": {
                    "schema": "trashbot.cloud_relay_runtime.v1",
                    "ack_semantics": "delivery_success",
                    "production_ready": True,
                    "delivery_success": True,
                    "final_state": "DELIVERED",
                },
            },
        })
        self.cloud.commands.append({
            "id": "cmd-cloud-relay-runtime-extra",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
        })

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
        self.assertEqual(self.worker.last_ack_id, "cmd-cloud-relay-runtime-extra")
        ack_payload = self.cloud.ack_posts[0]
        self.assertEqual(ack_payload["protocol_version"], "trashbot.remote.v1")
        self.assertEqual(ack_payload["command_id"], "cmd-cloud-relay-runtime-extra")
        self.assertEqual(ack_payload["state"], "acked")
        self.assertEqual(ack_payload["message"], "collect")
        encoded_ack = json.dumps(ack_payload, ensure_ascii=False)
        # cloud-relay 自包含 runtime 是部署元数据，robot ACK 只能表达本地 command envelope 处理结果。
        self.assertNotIn("cloud_relay_runtime", encoded_ack)
        self.assertNotIn("deployment_entrypoint", encoded_ack)
        self.assertNotIn("trigger_robot_action", encoded_ack)
        self.assertNotIn("cursor_override", encoded_ack)
        self.assertNotIn("delivery_success", encoded_ack)
        self.assertNotIn("DELIVERED", encoded_ack)
        encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
        self.assertNotIn("cloud_relay_runtime", encoded_status)
        self.assertNotIn("deployment_entrypoint", encoded_status)
        self.assertNotIn("delivery_success", encoded_status)
        self.assertEqual(self.cloud.status_posts[-1]["state"], "loaded_and_ready")
        self.assertNotEqual(self.cloud.status_posts[-1]["state"], "completed")

    def test_metadata_only_transaction_isolation_response_does_not_start_ack_or_persist_cursor(self):
        for isolation_status in ("blocked", "invalid", "stale"):
            with self.subTest(isolation_status=isolation_status):
                self.cloud.status_posts.clear()
                self.cloud.ack_posts.clear()
                self.backend.calls.clear()
                with tempfile.TemporaryDirectory() as tmpdir:
                    state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
                    worker = RemoteBridgeWorker(
                        self.client,
                        self.backend,
                        "robot-1",
                        last_ack_id=f"cmd-before-transaction-{isolation_status}",
                        cursor_state_path=state_path,
                    )
                    self.cloud.response_extras["command_response"] = {
                        "transaction_isolation": {
                            "schema": "trashbot.transaction_isolation_drill",
                            "overall_status": isolation_status,
                            "transaction_invariant": "metadata_only",
                            "cursor_invariant": "must_not_advance",
                            "ack_invariant": "ack_is_not_delivery_success",
                            "next_action": "collect",
                            "trigger_robot_action": "collect",
                            "delivery_success": True,
                        },
                        "diagnostics": {
                            "transaction_isolation": {
                                "overall_status": isolation_status,
                                "ack_semantics": "delivery_success",
                            },
                        },
                        "preflight": {"overall_status": "blocked", "production_ready": False},
                    }

                    handled = worker.poll_once()

                    # 只有 transaction isolation metadata、没有 command envelope 时，不能驱动本地 action/ACK/cursor。
                    self.assertFalse(handled)
                    self.assertEqual(self.backend.calls, [])
                    self.assertEqual(self.cloud.ack_posts, [])
                    self.assertEqual(worker.last_ack_id, f"cmd-before-transaction-{isolation_status}")
                    self.assertFalse(state_path.exists())
                    self.assertEqual(len(self.cloud.status_posts), 1)
                    encoded_status = json.dumps(self.cloud.status_posts, ensure_ascii=False)
                    self.assertNotIn("transaction_isolation", encoded_status)
                    self.assertNotIn("trigger_robot_action", encoded_status)
                    self.assertNotIn("delivery_success", encoded_status)

    def test_ack_failure_does_not_persist_cursor_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                cursor_state_path=state_path,
            )
            self.cloud.commands.append({
                "id": "cmd-ack-outage",
                "type": "collect",
                "payload": {"target": "trash_station"},
            })
            self.cloud.fail_ack_count = 1

            self.assertTrue(worker.poll_once())

            self.assertFalse(state_path.exists())
            self.assertEqual(worker.last_ack_id, "")
            self.assertEqual(worker.operator_backend.last_status["degradation_state"], "cloud_unreachable")

    def test_malformed_ack_response_retries_same_command_before_persisting_cursor(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            worker = RemoteBridgeWorker(
                self.client,
                self.backend,
                "robot-1",
                cursor_state_path=state_path,
            )
            command = {
                "id": "cmd-ack-malformed",
                "type": "collect",
                "payload": {"target": "trash_station", "trash_type": 0},
            }
            self.cloud.commands.append(command)
            self.cloud.malformed_ack_count = 1

            self.assertTrue(worker.poll_once())

            self.assertFalse(state_path.exists())
            self.assertEqual(worker.last_ack_id, "")
            self.assertEqual(self.cloud.ack_posts, [])
            self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
            self.assertEqual(worker.operator_backend.last_status["degradation_state"], "malformed_response")

            # ACK 响应不可信时，只能重发已缓存的 terminal ACK，不能再次触发本地 action。
            self.cloud.commands.append(command)
            self.assertTrue(worker.poll_once())

            payload = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["last_terminal_ack_id"], "cmd-ack-malformed")
            self.assertEqual(worker.last_ack_id, "cmd-ack-malformed")
            self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
            self.assertEqual(self.cloud.ack_posts[0]["command_id"], "cmd-ack-malformed")
            self.assertEqual(self.cloud.ack_posts[0]["state"], "acked")

    def test_unreadable_cursor_state_fails_explainably(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = pathlib.Path(tmpdir) / "remote_cursor.json"
            state_path.write_text("{not-json", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "cursor state unreadable"):
                RemoteBridgeWorker(
                    self.client,
                    self.backend,
                    "robot-1",
                    cursor_state_path=state_path,
                )

    def test_ack_failure_does_not_overwrite_successful_command_result(self):
        command = {
            "id": "cmd-ack-retry",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
        }
        self.cloud.commands.append(command)
        self.cloud.fail_ack_count = 1

        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
        self.assertEqual(self.worker.command_results["cmd-ack-retry"]["state"], "acked")
        self.assertEqual(self.worker.last_ack_id, "")
        self.assertEqual(self.cloud.ack_posts, [])

        self.cloud.commands.append(command)
        self.assertTrue(self.worker.poll_once())

        self.assertEqual(self.backend.calls, [("collect", "trash_station", 0)])
        self.assertEqual(self.cloud.ack_posts[0]["command_id"], "cmd-ack-retry")
        self.assertEqual(self.cloud.ack_posts[0]["state"], "acked")

    def test_command_result_cache_is_bounded(self):
        worker = RemoteBridgeWorker(self.client, self.backend, "robot-1", max_command_results=2)

        for index in range(3):
            self.cloud.commands.append({
                "id": f"cmd-{index}",
                "type": "collect",
                "payload": {"target": "trash_station", "trash_type": index},
            })
            self.assertTrue(worker.poll_once())

        self.assertEqual(list(worker.command_results), ["cmd-1", "cmd-2"])

    def test_poll_without_command_only_posts_status(self):
        handled = self.worker.poll_once()

        self.assertFalse(handled)
        self.assertEqual(len(self.cloud.status_posts), 1)
        self.assertEqual(self.cloud.ack_posts, [])
        self.assertEqual(self.backend.calls, [])


class RemoteBridgeActionResultTest(unittest.TestCase):
    def test_failed_collect_result_sets_failed_status_and_keeps_diagnostics(self):
        bridge = RemoteBridge.__new__(RemoteBridge)
        bridge.robot_id = "robot-1"
        bridge.task_lock = threading.Lock()
        bridge.collect_pending = False
        bridge.active_goal_handle = object()
        bridge.last_status = {}

        class Result:
            success = False
            error_message = "planner could not reach trash"
            task_record_path = "/tmp/task.json"
            error_code = 42
            final_state = "NAVIGATION_FAILED"

        class ResultEnvelope:
            result = Result()

        class DoneFuture:
            def result(self):
                return ResultEnvelope()

        bridge._on_collect_result(DoneFuture())

        self.assertEqual(bridge.last_status["state"], "failed")
        self.assertEqual(bridge.last_status["message"], "planner could not reach trash")
        self.assertEqual(bridge.last_status["error_code"], 42)
        self.assertEqual(bridge.last_status["final_state"], "NAVIGATION_FAILED")
        self.assertEqual(bridge.last_status["task_record_path"], "/tmp/task.json")
        self.assertFalse(bridge.collect_pending)
        self.assertIsNone(bridge.active_goal_handle)


class RemoteBridgeStaticConfigTest(unittest.TestCase):
    def test_remote_bridge_declares_o6_polling_configuration(self):
        source = REPO_ROOT / "ros2_trashbot_behavior" / "ros2_trashbot_behavior" / "remote_bridge.py"
        text = source.read_text(encoding="utf-8")

        for parameter_name in (
            "robot_id",
            "cloud_base_url",
            "bearer_token",
            "auth_token",
            "poll_interval_sec",
            "last_ack_id",
            "cursor_state_path",
        ):
            self.assertIn(f'declare_parameter("{parameter_name}"', text)


if __name__ == "__main__":
    unittest.main()
