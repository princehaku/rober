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
        source = pathlib.Path(RemoteBridge.__module__.replace(".", "/") + ".py")
        if not source.exists():
            source = pathlib.Path("src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py")
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
