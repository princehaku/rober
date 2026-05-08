import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ACTION = REPO_ROOT / "ros2_trashbot_interfaces" / "action" / "TrashCollection.action"


def _action_sections():
    return [
        {
            line.split()[1]
            for line in section.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        for section in ACTION.read_text(encoding="utf-8").split("---")
    ]


class TrashCollectionActionContractStaticTest(unittest.TestCase):
    def test_terminal_fields_are_result_fields(self):
        _, result_fields, _ = _action_sections()

        for field in (
            "success",
            "items_collected",
            "items_disposed",
            "total_duration_sec",
            "error_message",
            "task_record_path",
        ):
            self.assertIn(field, result_fields)

    def test_progress_fields_are_feedback_fields(self):
        _, _, feedback_fields = _action_sections()

        for field in (
            "arrived",
            "collected",
            "delivered",
            "status",
            "percent_complete",
            "current_step",
            "state",
            "event",
            "message",
            "elapsed_sec",
        ):
            self.assertIn(field, feedback_fields)


if __name__ == "__main__":
    unittest.main()
