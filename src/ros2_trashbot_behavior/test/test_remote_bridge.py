import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from ros2_trashbot_behavior.remote_bridge import RemoteBridgeWorker
from ros2_trashbot_behavior.remote_bridge_protocol import RemoteCloudClient


class MockCloud:
    def __init__(self):
        self.commands = []
        self.status_posts = []
        self.ack_posts = []
        self.fail_ack_count = 0
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
                    command = cloud.commands.pop(0) if cloud.commands else None
                    self._json(200, {"command": command})
                    return
                self._json(404, {"error": self.path})

            def do_POST(self):
                if self.path == "/robots/robot-1/status":
                    cloud.status_posts.append(self._body())
                    self._json(200, {"ok": True})
                    return
                if self.path.startswith("/robots/robot-1/commands/") and self.path.endswith("/ack"):
                    if cloud.fail_ack_count > 0:
                        cloud.fail_ack_count -= 1
                        self._json(503, {"error": "temporary ack outage"})
                        return
                    cloud.ack_posts.append(self._body())
                    self._json(200, {"ok": True})
                    return
                self._json(404, {"error": self.path})

            def log_message(self, _format, *_args):
                return

        return Handler


class FakeOperatorBackend:
    def __init__(self):
        self.calls = []

    def snapshot(self):
        return {"state": "waiting_for_trash", "message": "ready"}

    def start_collection(self, target, trash_type=0):
        self.calls.append(("collect", target, trash_type))
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
        self.assertIn("unsupported command.type", self.cloud.ack_posts[0]["message"])

    def test_ack_failure_does_not_overwrite_successful_command_result(self):
        command = {
            "id": "cmd-ack-retry",
            "type": "collect",
            "payload": {"target": "trash_station", "trash_type": 0},
        }
        self.cloud.commands.append(command)
        self.cloud.fail_ack_count = 1

        with self.assertRaises(RuntimeError):
            self.worker.poll_once()

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


if __name__ == "__main__":
    unittest.main()
