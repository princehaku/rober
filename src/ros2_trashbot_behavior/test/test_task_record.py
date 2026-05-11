import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
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
                nav_results=[
                    {
                        "success": True,
                        "result_code": "dry_run",
                        "evidence": {
                            "route_progress": {
                                "checkpoint": "cp-1",
                                "current_index": 1,
                                "target": {"name": "bin_a"},
                                "failure_code": "",
                                "evidence_ref": "/tmp/routes/fixed_route.yaml",
                                "source": "software_proof",
                            }
                        },
                    }
                ],
                dropoff_result={
                    "success": True,
                    "result_code": "manual_confirmed",
                    "message": "dropoff confirmed",
                    "source": "/trashbot/confirm_dropoff",
                    "elapsed_sec": 0.25,
                },
                elevator_assist={
                    "enabled": True,
                    "mode": "dry_run",
                    "state": "resume_delivery",
                    "phase": "resume_delivery",
                    "requires_human_help": False,
                    "reason": "elevator assist dry-run complete",
                    "target_floor": "1",
                    "speaker_prompt": "你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯,",
                    "evidence": {"waiting_elevator_open": "door_open"},
                    "events": [{"phase": "waiting_elevator_open"}],
                },
                detection_snapshot_refs=["vision://snapshot/1"],
                config={"dropoff_mode": "dry_run"},
                error_code="",
                final_state="idle",
                source="task_orchestrator",
                result_path="/tmp/routes/fixed_route.yaml",
                evidence_ref="/tmp/routes/fixed_route.yaml",
                failure_code="",
                human_intervention_required=False,
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
        self.assertEqual(payload["elevator_assist"]["enabled"], True)
        self.assertEqual(payload["elevator_assist"]["phase"], "resume_delivery")
        self.assertEqual(payload["elevator_assist"]["evidence"]["waiting_elevator_open"], "door_open")
        self.assertEqual(payload["detection_snapshot_refs"], ["vision://snapshot/1"])
        self.assertEqual(payload["config"]["dropoff_mode"], "dry_run")
        self.assertIn("started_at", payload)
        self.assertIn("ended_at", payload)
        self.assertEqual(payload["final_status"], "success")
        self.assertEqual(payload["error_code"], "")
        self.assertEqual(payload["final_state"], "idle")
        self.assertEqual(payload["source"], "software_proof")
        self.assertEqual(payload["result_path"], "/tmp/routes/fixed_route.yaml")
        self.assertEqual(payload["evidence_ref"], "/tmp/routes/fixed_route.yaml")
        self.assertEqual(payload["failure_code"], "")
        self.assertEqual(payload["human_intervention_required"], False)
        self.assertEqual(payload["route_progress"]["checkpoint"], "cp-1")
        self.assertEqual(payload["route_progress"]["current_index"], 1)
        self.assertEqual(payload["route_progress"]["evidence_ref"], "/tmp/routes/fixed_route.yaml")
        self.assertEqual(payload["state_transition_history"], payload["state_transitions"])
        self.assertGreaterEqual(len(payload["state_transitions"]), 4)

    def test_write_task_record_accepts_explicit_route_progress(self):
        with tempfile.TemporaryDirectory() as td:
            machine = DeliveryStateMachine()
            machine.confirm_loaded("trash_station")
            machine.start_delivery()
            machine.navigation_succeeded()
            machine.dropoff_confirmed()
            machine.return_succeeded()
            route_progress = {
                "checkpoint": "cp-2",
                "current_index": 2,
                "target": {"name": "trash_station"},
                "failure_code": "",
                "evidence_ref": "run-123",
                "source": "software_proof",
            }

            output = write_task_record(
                Path(td),
                "task-explicit-route-progress",
                machine,
                "success",
                "",
                nav_results=[],
                evidence_ref="run-123",
                route_progress=route_progress,
            )
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(payload["route_progress"], route_progress)

    def test_evidence_crosscheck_uses_task_record_dir(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = "run-123"
            replay_path = root / "route_replay.jsonl"
            status_path = root / "status.json"
            task_record_dir = root / "tasks"
            task_record_dir.mkdir()
            route_progress = {
                "checkpoint": "cp-3",
                "current_index": 3,
                "target": {"name": "trash_station"},
                "failure_code": "",
                "evidence_ref": evidence_ref,
            }
            replay_path.write_text(json.dumps(route_progress) + "\n", encoding="utf-8")
            status_path.write_text(
                json.dumps(
                    {
                        "status": "completed",
                        "route_progress": route_progress,
                        "evidence_ref": evidence_ref,
                        "software_proof": {"artifact_path": str(replay_path)},
                    }
                ),
                encoding="utf-8",
            )
            (task_record_dir / "task.json").write_text(
                json.dumps(
                    {
                        "task_id": "task-dir-lookup",
                        "evidence_ref": evidence_ref,
                        "route_progress": route_progress,
                        "nav_results": [{"evidence": {"route_progress": route_progress}}],
                    }
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "evidence_crosscheck.py"),
                    str(status_path),
                    "--task-record-dir",
                    str(task_record_dir),
                    "--evidence-ref",
                    evidence_ref,
                ],
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("task_record:", result.stdout)
        self.assertIn("CHECK summary: mismatches=0", result.stdout)

    def test_evidence_crosscheck_fails_when_task_record_dir_has_no_match(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = "run-no-task-match"
            replay_path = root / "route_replay.jsonl"
            status_path = root / "status.json"
            task_record_dir = root / "tasks"
            task_record_dir.mkdir()
            route_progress = {
                "checkpoint": "cp-3",
                "current_index": 3,
                "target": {"name": "trash_station"},
                "failure_code": "",
                "evidence_ref": evidence_ref,
            }
            replay_path.write_text(json.dumps(route_progress) + "\n", encoding="utf-8")
            status_path.write_text(
                json.dumps(
                    {
                        "status": "completed",
                        "route_progress": route_progress,
                        "evidence_ref": evidence_ref,
                        "software_proof": {"artifact_path": str(replay_path)},
                    }
                ),
                encoding="utf-8",
            )
            (task_record_dir / "other.json").write_text(
                json.dumps({"task_id": "other", "evidence_ref": "different-run"}),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "evidence_crosscheck.py"),
                    str(status_path),
                    "--task-record-dir",
                    str(task_record_dir),
                    "--evidence-ref",
                    evidence_ref,
                ],
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("no matching task_record", result.stdout)
        self.assertIn("CHECK summary: mismatches=1", result.stdout)

    def test_evidence_crosscheck_fails_when_task_record_lacks_route_progress(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = "run-missing-route-progress"
            replay_path = root / "route_replay.jsonl"
            status_path = root / "status.json"
            task_record_path = root / "task.json"
            route_progress = {
                "checkpoint": "cp-4",
                "current_index": 4,
                "target": {"name": "trash_station"},
                "failure_code": "",
                "evidence_ref": evidence_ref,
            }
            replay_path.write_text(json.dumps(route_progress) + "\n", encoding="utf-8")
            status_path.write_text(
                json.dumps(
                    {
                        "status": "completed",
                        "route_progress": route_progress,
                        "evidence_ref": evidence_ref,
                        "software_proof": {"artifact_path": str(replay_path)},
                    }
                ),
                encoding="utf-8",
            )
            task_record_path.write_text(
                json.dumps(
                    {
                        "task_id": "task-missing-route-progress",
                        "evidence_ref": evidence_ref,
                        "nav_results": [{"evidence": {}}],
                    }
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "evidence_crosscheck.py"),
                    str(status_path),
                    "--task-record",
                    str(task_record_path),
                    "--evidence-ref",
                    evidence_ref,
                ],
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("task_record.route_progress: missing", result.stdout)

    def test_write_task_record_persists_failure_terminal_diagnostics(self):
        with tempfile.TemporaryDirectory() as td:
            machine = DeliveryStateMachine()
            machine.confirm_loaded("trash_station")
            machine.start_delivery()
            machine.timed_out("fixed route status file did not report completion")

            output = write_task_record(
                Path(td),
                "task-timeout",
                machine,
                "failed",
                machine.error_message,
                delivery_mode="fixed_route",
                target="trash_station",
                nav_attempts=1,
                nav_results=[
                    {
                        "success": False,
                        "result_code": "timeout",
                        "message": machine.error_message,
                        "elapsed_sec": 120.0,
                    }
                ],
                dropoff_result={},
                config={
                    "delivery_mode": "fixed_route",
                    "fixed_route_status_file": "/tmp/trashbot_fixed_route_status.json",
                },
                source="task_orchestrator",
                result_path="/tmp/trashbot_fixed_route_status.json",
                evidence_ref="/tmp/trashbot_fixed_route_status.json",
                failure_code="NAV_TIMEOUT",
                human_intervention_required=True,
            )
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(payload["final_status"], "failed")
        self.assertEqual(payload["error_code"], "timed_out")
        self.assertEqual(payload["error_message"], "fixed route status file did not report completion")
        self.assertEqual(payload["final_state"], "error")
        self.assertEqual(payload["delivery_mode"], "fixed_route")
        self.assertEqual(payload["nav_results"][0]["result_code"], "timeout")
        self.assertEqual(payload["config"]["fixed_route_status_file"], "/tmp/trashbot_fixed_route_status.json")
        self.assertEqual(payload["source"], "software_proof")
        self.assertEqual(payload["result_path"], "/tmp/trashbot_fixed_route_status.json")
        self.assertEqual(payload["evidence_ref"], "/tmp/trashbot_fixed_route_status.json")
        self.assertEqual(payload["failure_code"], "NAV_TIMEOUT")
        self.assertEqual(payload["human_intervention_required"], True)


if __name__ == "__main__":
    unittest.main()
