import unittest
import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ORCHESTRATOR = REPO_ROOT / "ros2_trashbot_behavior" / "ros2_trashbot_behavior" / "task_orchestrator.py"
CONFIRMATION_GATE = REPO_ROOT / "ros2_trashbot_behavior" / "ros2_trashbot_behavior" / "dropoff_confirmation.py"


class TaskOrchestratorStaticTest(unittest.TestCase):
    def test_delivery_parameters_are_declared(self):
        source = ORCHESTRATOR.read_text(encoding="utf-8")

        for parameter in (
            "navigation_timeout_sec",
            "navigation_retry_limit",
            "dropoff_mode",
            "dropoff_timeout_sec",
            "fixed_route_status_file",
        ):
            self.assertIn(f'declare_parameter("{parameter}"', source)

    def test_navigation_result_contract_is_structured(self):
        source = ORCHESTRATOR.read_text(encoding="utf-8")

        for field in ("success", "result_code", "message", "elapsed_sec"):
            self.assertIn(field, source)

    def test_fixed_route_mode_has_no_uart_control(self):
        source = ORCHESTRATOR.read_text(encoding="utf-8").lower()

        self.assertIn('"fixed_route"', source)
        self.assertIn("navigate_fixed_route_status", source)
        self.assertIn("fixed_route_status_file", source)
        self.assertIn('payload.get("state"', source)
        self.assertIn('state in ("success", "succeeded", "completed")', source)
        self.assertIn('state in ("failed", "error")', source)
        self.assertIn("did not report completion", source)
        self.assertNotIn("fixed_route_dry_run", source)
        self.assertNotIn("serial", source)
        self.assertNotIn("uart", source)

    def test_fixed_route_status_reader_accepts_runner_state_field(self):
        source = ORCHESTRATOR.read_text(encoding="utf-8")

        self.assertIn('payload.get("state"', source)
        self.assertIn('"completed"', source)

    def test_fixed_route_status_reader_uses_state_for_terminal_result(self):
        source = ORCHESTRATOR.read_text(encoding="utf-8")
        tree = ast.parse(source)
        function_node = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
            and node.name == "_navigate_fixed_route_status"
        )
        function_source = ast.get_source_segment(source, function_node)

        self.assertIn('state = str(payload.get("state", "")).lower()', function_source)
        self.assertIn('state in ("success", "succeeded", "completed")', function_source)
        self.assertIn('state in ("failed", "error")', function_source)

    def test_manual_dropoff_requires_external_setbool_confirmation(self):
        source = ORCHESTRATOR.read_text(encoding="utf-8")
        gate_source = CONFIRMATION_GATE.read_text(encoding="utf-8")

        self.assertIn("from std_srvs.srv import SetBool", source)
        self.assertIn("'/trashbot/confirm_dropoff'", source)
        self.assertIn("DropoffConfirmationGate", source)
        self.assertIn("self.dropoff_gate.begin(task_id)", source)
        self.assertIn("manual_confirm_timeout", gate_source)
        self.assertNotIn("manual_confirm_timeout_elapsed", source)


if __name__ == "__main__":
    unittest.main()
