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
                    self._send_json(200, {"command": command})
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
                    self._send_json(200, {"ok": True})
                    return
                if len(parts) == 5 and parts[0] == "robots" and parts[2] == "commands" and parts[4] == "ack":
                    if unquote(parts[1]) != "robot-1" and unquote(parts[1]) != "robot/with space":
                        self._send_json(404, {"error": "unknown robot"})
                        return
                    cloud.acks.append(payload)
                    self._send_json(200, {"ok": True})
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
