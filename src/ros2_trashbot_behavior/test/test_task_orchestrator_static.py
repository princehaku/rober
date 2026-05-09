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
            "max_detection_snapshot_refs",
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

    def test_collection_action_rejects_concurrent_goals(self):
        source = ORCHESTRATOR.read_text(encoding="utf-8")
        ast.parse(source)

        self.assertIn("GoalResponse", source)
        self.assertIn("goal_callback=self._collection_goal_callback", source)
        self.assertIn("self.collection_lock = threading.Lock()", source)
        self.assertIn("self.collection_active = False", source)
        self.assertIn("def _collection_goal_callback", source)
        self.assertIn("return GoalResponse.REJECT", source)
        self.assertIn("return GoalResponse.ACCEPT", source)
        self.assertIn("def _clear_collection_active", source)
        self.assertIn("self._clear_collection_active()", source)

    def test_collection_active_flag_is_cleared_in_finally(self):
        source = ORCHESTRATOR.read_text(encoding="utf-8")
        tree = ast.parse(source)
        function_node = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.AsyncFunctionDef)
            and node.name == "_execute_collection"
        )
        try_nodes = [node for node in ast.walk(function_node) if isinstance(node, ast.Try)]

        self.assertTrue(
            any(
                any(
                    isinstance(stmt, ast.Expr)
                    and isinstance(stmt.value, ast.Call)
                    and isinstance(stmt.value.func, ast.Attribute)
                    and stmt.value.func.attr == "_clear_collection_active"
                    for stmt in try_node.finalbody
                )
                for try_node in try_nodes
            )
        )

    def test_collection_maps_navigation_timeout_to_timeout_event(self):
        source = ORCHESTRATOR.read_text(encoding="utf-8")
        ast.parse(source)

        self.assertIn('nav_result.result_code == "timeout"', source)
        self.assertIn("machine.timed_out(nav_result.message)", source)

    def test_collection_result_sets_error_code_and_final_state(self):
        source = ORCHESTRATOR.read_text(encoding="utf-8")
        ast.parse(source)

        self.assertIn("result.error_code", source)
        self.assertIn("result.final_state", source)
        self.assertIn('result.error_code = ""', source)
        self.assertIn("result.error_code = machine.events[-1].event.value", source)
        self.assertIn('result.error_code = "canceled"', source)
        self.assertIn("result.final_state = machine.state.value", source)

    def test_collection_record_uses_detection_snapshot_refs_without_algorithm_coupling(self):
        source = ORCHESTRATOR.read_text(encoding="utf-8")
        tree = ast.parse(source)
        function_node = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
            and node.name == "_write_collection_record"
        )
        function_source = ast.get_source_segment(source, function_node)

        self.assertIn("detection_snapshot_refs=list(self.detection_snapshot_refs)", function_source)
        self.assertIn("trash_status://detection/", source)
        self.assertIn("urlencode", source)
        self.assertNotIn("cv2", function_source.lower())
        self.assertNotIn("opencv", function_source.lower())

    def test_collection_record_persists_terminal_diagnostics(self):
        source = ORCHESTRATOR.read_text(encoding="utf-8")
        tree = ast.parse(source)
        function_node = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
            and node.name == "_write_collection_record"
        )
        function_source = ast.get_source_segment(source, function_node)

        self.assertIn('error_code="" if final_status == "success"', function_source)
        self.assertIn("machine.events[-1].event.value if machine.events else", function_source)
        self.assertIn("final_state=machine.state.value", function_source)


if __name__ == "__main__":
    unittest.main()
