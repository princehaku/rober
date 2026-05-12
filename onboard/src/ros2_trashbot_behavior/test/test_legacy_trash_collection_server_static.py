import ast
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BEHAVIOR_ROOT = REPO_ROOT / "ros2_trashbot_behavior"
LEGACY_SERVER = BEHAVIOR_ROOT / "ros2_trashbot_behavior" / "trash_collection_server.py"
SETUP_PY = BEHAVIOR_ROOT / "setup.py"
ROS_CONTRACTS = REPO_ROOT.parent / "docs" / "interfaces" / "ros_contracts.md"


def _legacy_source():
    return LEGACY_SERVER.read_text(encoding="utf-8")


class LegacyTrashCollectionServerStaticTest(unittest.TestCase):
    def test_legacy_server_is_quarantined_with_machine_readable_result(self):
        source = _legacy_source()

        self.assertIn("LEGACY_ERROR_CODE = 'legacy_server_quarantined'", source)
        self.assertIn("Use task_orchestrator", source)
        self.assertIn("result.success = False", source)
        self.assertIn("result.error_code = LEGACY_ERROR_CODE", source)
        self.assertIn("result.final_state = 'error'", source)
        self.assertIn("goal_handle.abort()", source)

    def test_sleep_demo_pipeline_was_removed(self):
        source = _legacy_source()
        tree = ast.parse(source)
        function_names = {
            node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
        } | {
            node.name for node in ast.walk(tree) if isinstance(node, ast.AsyncFunctionDef)
        }

        self.assertNotIn("_navigate_to_trash", function_names)
        self.assertNotIn("_collect_trash", function_names)
        self.assertNotIn("_deliver_to_bin", function_names)
        self.assertNotIn("_sleep", function_names)
        self.assertNotIn("asyncio.sleep", source)
        self.assertNotIn("goal_handle.succeed()", source)
        self.assertNotIn("result.success = True", source)

    def test_default_entrypoint_stays_task_orchestrator_and_legacy_is_legacy_only(self):
        setup_source = SETUP_PY.read_text(encoding="utf-8")
        docs_source = ROS_CONTRACTS.read_text(encoding="utf-8")

        self.assertIn(
            "task_orchestrator = ros2_trashbot_behavior.task_orchestrator:main",
            setup_source,
        )
        self.assertIn(
            "legacy_trash_collection_server = ros2_trashbot_behavior.trash_collection_server:main",
            setup_source,
        )
        self.assertIn(
            "Default product entry point is `task_orchestrator`",
            docs_source,
        )
        self.assertIn(
            "legacy standalone server is installed as `legacy_trash_collection_server` only",
            docs_source,
        )


if __name__ == "__main__":
    unittest.main()
