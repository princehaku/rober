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
