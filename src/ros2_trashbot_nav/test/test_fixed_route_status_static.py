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
        self.assertIn("'failure_code'", source)
        self.assertIn("'mode'", source)
        self.assertIn("'last_transition'", source)
        self.assertIn("'route_contract_version'", source)
        self.assertIn("'last_nav_result'", source)
        self.assertIn("'updated_at'", source)
        self.assertIn("'checkpoint'", source)
        self.assertIn("'current_target'", source)
        self.assertIn("'target'", source)
        self.assertIn("'visual_gate_status'", source)
        self.assertIn("'visual_gate_detail'", source)
        self.assertIn("'visual_gate_checkpoint'", source)
        self.assertIn("'route_proof_summary'", source)
        self.assertIn("'software_proof'", source)
        self.assertIn("'keyframe_preflight'", source)
        self.assertIn("'elevator_assist'", source)
        self.assertIn("build_route_replay_entry", source)
        self.assertIn("build_elevator_assist_evidence", source)
        self.assertIn("build_elevator_assist_status", source)
        self.assertIn("self.keyframe_preflight", source)
        self.assertIn("failure_code", source)
        self.assertIn("build_route_replay_artifact_path", SOURCE.read_text(encoding="utf-8"))

    def test_elevator_evidence_schema_is_offline_and_explicit(self):
        route_utils = REPO_ROOT / "ros2_trashbot_nav" / "ros2_trashbot_nav" / "route_utils.py"
        source = route_utils.read_text(encoding="utf-8")

        for status in (
            "'door_open'",
            "'door_closed_or_unknown'",
            "'inside_elevator'",
            "'target_floor_confirmed'",
            "'target_floor_unconfirmed'",
            "'safe_to_exit'",
            "'unsafe_to_exit'",
        ):
            self.assertIn(status, source)
        self.assertIn("'elevator_assist.evidence.v1'", source)
        self.assertIn("'robot_readable'", source)
        self.assertIn("'operator_readable'", source)

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

    def test_route_progress_payload_includes_failure_code(self):
        source = SOURCE.read_text(encoding="utf-8")

        self.assertIn("build_route_checkpoint_payload(", source)
        self.assertIn("failure_code=self.failure_code", source)


if __name__ == "__main__":
    unittest.main()
