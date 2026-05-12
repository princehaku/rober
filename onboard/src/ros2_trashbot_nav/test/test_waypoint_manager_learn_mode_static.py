import ast
import unittest
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[1] / "ros2_trashbot_nav" / "waypoint_manager.py"
PACKAGE_SOURCE = Path(__file__).resolve().parents[1] / "ros2_trashbot_nav"


def _source_tree():
    return ast.parse(SOURCE.read_text(encoding="utf-8"))


class WaypointManagerLearnModeStaticTest(unittest.TestCase):
    def test_waypoint_manager_consumes_learn_mode_parameters(self):
        tree = _source_tree()
        string_constants = {
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }

        self.assertIn("learn_mode", string_constants)
        self.assertIn("record_interval", string_constants)

    def test_waypoint_manager_creates_learn_mode_timer(self):
        tree = _source_tree()
        method_calls = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }

        self.assertIn("create_timer", method_calls)

    def test_waypoint_manager_uses_nav2_task_result_enum(self):
        tree = _source_tree()
        imported_names = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module == "nav2_simple_commander.robot_navigator"
            for alias in node.names
        }
        comparisons = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Compare)
        ]

        self.assertIn("TaskResult", imported_names)
        self.assertTrue(
            any(
                isinstance(compare.comparators[0], ast.Attribute)
                and compare.comparators[0].attr == "SUCCEEDED"
                for compare in comparisons
            )
        )

    def test_navigation_result_checks_do_not_compare_to_zero(self):
        for source in PACKAGE_SOURCE.glob("*.py"):
            tree = ast.parse(source.read_text(encoding="utf-8"))
            for compare in (
                node for node in ast.walk(tree) if isinstance(node, ast.Compare)
            ):
                operands = [compare.left, *compare.comparators]
                compares_to_zero = any(
                    isinstance(operand, ast.Constant) and operand.value == 0
                    for operand in operands
                )
                mentions_get_result = any(
                    isinstance(operand, ast.Call)
                    and isinstance(operand.func, ast.Attribute)
                    and operand.func.attr == "getResult"
                    for operand in operands
                )

                self.assertFalse(
                    compares_to_zero and mentions_get_result,
                    f"{source.name} compares BasicNavigator.getResult() to 0",
                )


if __name__ == "__main__":
    unittest.main()
