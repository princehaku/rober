import ast
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPO_ROOT / "ros2_trashbot_nav" / "ros2_trashbot_nav" / "fixed_route_autonomy.py"


class FixedRouteStatusStaticTest(unittest.TestCase):
    def test_debug_status_contains_diagnostic_fields(self):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        method = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "_write_debug_status"
        )
        source = ast.unparse(method)

        self.assertIn("'last_error'", source)
        self.assertIn("'failure_reason'", source)
        self.assertIn("'mode'", source)
        self.assertIn("'last_transition'", source)
        self.assertIn("'route_contract_version'", source)
        self.assertIn("'last_nav_result'", source)
        self.assertIn("'updated_at'", source)
        self.assertIn("'current_target'", source)
        self.assertIn("'visual_gate_status'", source)
        self.assertIn("'visual_gate_detail'", source)
        self.assertIn("'visual_gate_checkpoint'", source)
        self.assertIn("'route_proof_summary'", source)
        self.assertIn("'keyframe_preflight'", source)
        self.assertIn("self.keyframe_preflight", source)

    def test_keyframe_preflight_reports_route_wide_coverage(self):
        source = SOURCE.read_text(encoding="utf-8")

        for field in (
            "'total_checkpoints'",
            "'loaded_keyframes'",
            "'missing_keyframes'",
            "'invalid_keyframes'",
            "'route_visual_ready'",
            "'keyframe_preflight_failed'",
        ):
            self.assertIn(field, source)


if __name__ == "__main__":
    unittest.main()
