import ast
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
GATEWAY = REPO_ROOT / "ros2_trashbot_behavior" / "ros2_trashbot_behavior" / "operator_gateway.py"
HTTP = REPO_ROOT / "ros2_trashbot_behavior" / "ros2_trashbot_behavior" / "operator_gateway_http.py"
SETUP = REPO_ROOT / "ros2_trashbot_behavior" / "setup.py"


class OperatorGatewayStaticTest(unittest.TestCase):
    def test_gateway_exposes_minimum_http_contract(self):
        source = GATEWAY.read_text(encoding="utf-8")
        http_source = HTTP.read_text(encoding="utf-8")
        ast.parse(source)
        ast.parse(http_source)

        for route in (
            '"/api/status"',
            '"/api/collect"',
            '"/api/dropoff/confirm"',
            '"/api/cancel"',
        ):
            self.assertIn(route, http_source)

        self.assertIn("default_target", source)
        self.assertIn("collect_action_name", source)
        self.assertIn("dropoff_service_name", source)
        self.assertIn("pose_topic", source)
        self.assertIn("PoseWithCovarianceStamped", source)
        self.assertIn("robot_pose", source)
        self.assertIn("robot_path", source)
        self.assertIn("ActionClient(self, TrashCollection, self.collect_action_name)", source)
        self.assertIn("create_client(SetBool, self.dropoff_service_name)", source)
        self.assertIn("make_handler(self)", source)
        self.assertIn("status_payload", source)
        self.assertNotIn("flask", source.lower())
        self.assertNotIn("aiohttp", source.lower())

    def test_gateway_has_console_entry_point(self):
        source = SETUP.read_text(encoding="utf-8")

        self.assertIn(
            "operator_gateway = ros2_trashbot_behavior.operator_gateway:main",
            source,
        )

    def test_gateway_blocks_duplicate_collect_while_goal_response_is_pending(self):
        source = GATEWAY.read_text(encoding="utf-8")
        ast.parse(source)

        self.assertIn("self._collect_pending = False", source)
        self.assertIn("self._collect_pending = True", source)
        self.assertIn("task_active = self._collect_pending", source)
        goal_response_block = source[source.index("def _on_goal_response"):]
        self.assertIn("self._collect_pending = False", goal_response_block)

    def test_gateway_cancel_does_not_claim_canceled_before_goal_handle_exists(self):
        source = GATEWAY.read_text(encoding="utf-8")
        ast.parse(source)

        cancel_block = source[
            source.index("def cancel_collection"):
            source.index("def _on_goal_response")
        ]
        self.assertIn("collect goal is still pending", cancel_block)
        self.assertIn('status_payload("busy"', cancel_block)

    def test_gateway_handles_async_action_result_and_dropoff_service_errors(self):
        source = GATEWAY.read_text(encoding="utf-8")
        ast.parse(source)

        result_block = source[
            source.index("def _on_collect_result"):
            source.index("def _set_status")
        ]
        confirm_block = source[
            source.index("def confirm_dropoff"):
            source.index("def cancel_collection")
        ]
        self.assertIn("except Exception as exc", result_block)
        self.assertIn("finally:", result_block)
        self.assertIn("self._goal_handle = None", result_block)
        self.assertIn("self._collect_pending = False", result_block)
        self.assertIn('holder["error"]', confirm_block)
        self.assertIn("finally:", confirm_block)
        self.assertIn("confirm_dropoff service failed", confirm_block)


if __name__ == "__main__":
    unittest.main()
