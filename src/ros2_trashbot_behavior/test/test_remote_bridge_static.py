import ast
from pathlib import Path
import threading
import unittest

from ros2_trashbot_behavior.remote_bridge import RemoteBridge
from ros2_trashbot_behavior.remote_bridge_protocol import PROTOCOL_VERSION


REPO_ROOT = Path(__file__).resolve().parents[2]
REMOTE_BRIDGE = REPO_ROOT / "ros2_trashbot_behavior" / "ros2_trashbot_behavior" / "remote_bridge.py"
PROTOCOL = REPO_ROOT / "ros2_trashbot_behavior" / "ros2_trashbot_behavior" / "remote_bridge_protocol.py"
SETUP = REPO_ROOT / "ros2_trashbot_behavior" / "setup.py"


class RemoteBridgeStaticTest(unittest.TestCase):
    def test_remote_bridge_uses_outbound_polling_contract(self):
        source = REMOTE_BRIDGE.read_text(encoding="utf-8")
        protocol = PROTOCOL.read_text(encoding="utf-8")
        ast.parse(source)
        ast.parse(protocol)

        self.assertIn("RemoteCloudClient", source)
        self.assertIn("post_status", source)
        self.assertIn("get_next_command", source)
        self.assertIn("post_ack", source)
        self.assertIn("command_expired", source)
        self.assertIn("command_results", source)
        self.assertIn('COMMAND_TYPES = {"collect", "confirm_dropoff", "cancel"}', protocol)

    def test_remote_bridge_has_console_entry_point(self):
        source = SETUP.read_text(encoding="utf-8")

        self.assertIn("remote_bridge = ros2_trashbot_behavior.remote_bridge:main", source)

    def test_remote_bridge_parses_enabled_parameter_without_string_truthiness(self):
        source = REMOTE_BRIDGE.read_text(encoding="utf-8")
        ast.parse(source)

        self.assertIn("self.enabled = parse_bool(self.get_parameter(\"enabled\").value, default=False)", source)
        self.assertNotIn("self.enabled = bool(self.get_parameter(\"enabled\").value)", source)

    def test_remote_bridge_blocks_duplicate_collect_while_goal_response_is_pending(self):
        source = REMOTE_BRIDGE.read_text(encoding="utf-8")
        ast.parse(source)

        self.assertIn("self.collect_pending = False", source)
        self.assertIn("self.collect_pending = True", source)
        self.assertIn("if self.collect_pending or self.active_goal_handle is not None", source)
        goal_response_block = source[source.index("def _on_goal_response"):]
        self.assertIn("self.collect_pending = False", goal_response_block)

    def test_remote_bridge_waits_for_dropoff_service_result_before_ack(self):
        source = REMOTE_BRIDGE.read_text(encoding="utf-8")
        ast.parse(source)

        confirm_block = source[
            source.index("def confirm_dropoff"):
            source.index("def cancel_collection")
        ]
        self.assertIn("done = threading.Event()", confirm_block)
        self.assertIn("done.wait(2.0)", confirm_block)
        self.assertIn("return (200 if response.success else 409), payload", confirm_block)

    def test_cancel_does_not_report_canceled_before_goal_handle_exists(self):
        bridge = RemoteBridge.__new__(RemoteBridge)
        bridge.robot_id = "robot-1"
        bridge.task_lock = threading.Lock()
        bridge.collect_pending = True
        bridge.active_goal_handle = None
        bridge.last_status = {
            "protocol_version": PROTOCOL_VERSION,
            "robot_id": "robot-1",
            "state": "delivering",
            "message": "goal pending",
        }

        status, payload = bridge.cancel_collection()

        self.assertEqual(status, 409)
        self.assertEqual(payload["state"], "busy")
        self.assertIn("pending", payload["message"])
        self.assertTrue(bridge.collect_pending)

    def test_result_future_failure_clears_active_task_state(self):
        bridge = RemoteBridge.__new__(RemoteBridge)
        bridge.robot_id = "robot-1"
        bridge.task_lock = threading.Lock()
        bridge.collect_pending = False
        bridge.active_goal_handle = object()
        bridge.last_status = {
            "protocol_version": PROTOCOL_VERSION,
            "robot_id": "robot-1",
            "state": "delivering",
            "message": "goal active",
        }

        class FailedFuture:
            def result(self):
                raise RuntimeError("result transport failed")

        bridge._on_collect_result(FailedFuture())

        self.assertFalse(bridge.collect_pending)
        self.assertIsNone(bridge.active_goal_handle)
        self.assertEqual(bridge.last_status["state"], "needs_human_help")
        self.assertIn("result failed", bridge.last_status["message"])


if __name__ == "__main__":
    unittest.main()
