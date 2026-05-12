import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_XML = REPO_ROOT / "ros2_trashbot_behavior" / "package.xml"
SETUP_PY = REPO_ROOT / "ros2_trashbot_behavior" / "setup.py"


class BehaviorPackageContractStaticTest(unittest.TestCase):
    def test_nav2_simple_commander_dependency_is_declared(self):
        source = PACKAGE_XML.read_text(encoding="utf-8")

        self.assertIn("<depend>nav2_simple_commander</depend>", source)

    def test_legacy_trash_collection_server_is_not_default_entry_point(self):
        source = SETUP_PY.read_text(encoding="utf-8")
        entry_lines = {line.strip().strip("',") for line in source.splitlines()}

        self.assertIn("task_orchestrator = ros2_trashbot_behavior.task_orchestrator:main", source)
        self.assertNotIn(
            "trash_collection_server = ros2_trashbot_behavior.trash_collection_server:main",
            entry_lines,
        )
        self.assertIn(
            "legacy_trash_collection_server = ros2_trashbot_behavior.trash_collection_server:main",
            entry_lines,
        )


if __name__ == "__main__":
    unittest.main()
