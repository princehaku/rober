import ast
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PATROL_ACTION = REPO_ROOT / "ros2_trashbot_interfaces" / "action" / "Patrol.action"
ORCHESTRATOR_SOURCE = (
    REPO_ROOT
    / "ros2_trashbot_behavior"
    / "ros2_trashbot_behavior"
    / "task_orchestrator.py"
)


def _action_sections():
    return [
        {
            line.split()[1]
            for line in section.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        for section in PATROL_ACTION.read_text(encoding="utf-8").split("---")
    ]


class PatrolActionContractStaticTest(unittest.TestCase):
    def test_patrol_result_contains_terminal_status_fields(self):
        _, result_fields, _ = _action_sections()

        self.assertIn("success", result_fields)
        self.assertIn("total_duration_sec", result_fields)
        self.assertIn("new_points_recorded", result_fields)
        self.assertIn("map_save_path", result_fields)

    def test_patrol_feedback_contains_progress_fields(self):
        _, _, feedback_fields = _action_sections()

        self.assertIn("current_waypoint", feedback_fields)
        self.assertIn("distance_traveled", feedback_fields)
        self.assertIn("waypoints_visited", feedback_fields)
        self.assertIn("waypoints_total", feedback_fields)

    def test_task_orchestrator_writes_patrol_fields_to_matching_sections(self):
        _, result_fields, feedback_fields = _action_sections()
        tree = ast.parse(ORCHESTRATOR_SOURCE.read_text(encoding="utf-8"))
        patrol_method = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "_execute_patrol"
        )
        assigned = {"result": set(), "feedback_msg": set()}
        for node in ast.walk(patrol_method):
            targets = []
            if isinstance(node, ast.Assign):
                targets = node.targets
            elif isinstance(node, ast.AugAssign):
                targets = [node.target]
            for target in targets:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id in assigned
                ):
                    assigned[target.value.id].add(target.attr)

        for field in assigned.get("result", set()):
            self.assertIn(field, result_fields)
        for field in assigned.get("feedback_msg", set()):
            self.assertIn(field, feedback_fields)

    def test_collection_no_long_sleep_placeholders(self):
        tree = ast.parse(ORCHESTRATOR_SOURCE.read_text(encoding="utf-8"))
        collection_method = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "_execute_collection"
        )
        source = ast.unparse(collection_method)

        self.assertNotIn("await self._sleep_async(3.0)", source)
        self.assertNotIn("await self._sleep_async(2.0)", source)

    def test_collection_uses_waypoint_navigation_in_non_dry_run_mode(self):
        source = ORCHESTRATOR_SOURCE.read_text(encoding="utf-8")

        self.assertIn("delivery_mode", source)
        self.assertIn("_navigate_to_waypoint_target", source)
        self.assertIn("load_waypoint_file", source)
        self.assertNotIn("delivery action wiring is not implemented", source)


if __name__ == "__main__":
    unittest.main()
