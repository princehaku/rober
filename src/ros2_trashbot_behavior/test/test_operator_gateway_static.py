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


if __name__ == "__main__":
    unittest.main()
