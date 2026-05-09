import json
from pathlib import Path
import sys
import tempfile
import unittest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from ros2_trashbot_behavior.delivery_state_machine import DeliveryStateMachine
from ros2_trashbot_behavior.task_record import write_task_record


class TaskRecordTest(unittest.TestCase):
    def test_write_task_record_persists_state_transitions(self):
        with tempfile.TemporaryDirectory() as td:
            machine = DeliveryStateMachine()
            machine.confirm_loaded("bin_a")
            machine.start_delivery()
            machine.navigation_succeeded()
            machine.dropoff_confirmed()
            machine.return_succeeded()

            output = write_task_record(
                Path(td),
                "task-1",
                machine,
                "success",
                "",
                delivery_mode="dry_run",
                target="bin_a",
                return_target="home",
                nav_attempts=1,
                nav_results=[{"success": True, "result_code": "dry_run"}],
                dropoff_result={
                    "success": True,
                    "result_code": "manual_confirmed",
                    "message": "dropoff confirmed",
                    "source": "/trashbot/confirm_dropoff",
                    "elapsed_sec": 0.25,
                },
                detection_snapshot_refs=["vision://snapshot/1"],
                config={"dropoff_mode": "dry_run"},
            )
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(payload["task_id"], "task-1")
        self.assertEqual(payload["target"], "bin_a")
        self.assertEqual(payload["return_target"], "home")
        self.assertEqual(payload["delivery_mode"], "dry_run")
        self.assertEqual(payload["nav_attempts"], 1)
        self.assertEqual(payload["nav_results"][0]["result_code"], "dry_run")
        self.assertEqual(payload["dropoff_result"]["result_code"], "manual_confirmed")
        self.assertEqual(payload["dropoff_result"]["source"], "/trashbot/confirm_dropoff")
        self.assertEqual(payload["dropoff_result"]["message"], "dropoff confirmed")
        self.assertEqual(payload["dropoff_result"]["elapsed_sec"], 0.25)
        self.assertEqual(payload["detection_snapshot_refs"], ["vision://snapshot/1"])
        self.assertEqual(payload["config"]["dropoff_mode"], "dry_run")
        self.assertIn("started_at", payload)
        self.assertIn("ended_at", payload)
        self.assertEqual(payload["final_status"], "success")
        self.assertGreaterEqual(len(payload["state_transitions"]), 4)


if __name__ == "__main__":
    unittest.main()
