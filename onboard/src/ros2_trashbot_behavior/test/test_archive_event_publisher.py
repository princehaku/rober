import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from ros2_trashbot_behavior.archive_event_publisher import (  # noqa: E402
    ARCHIVE_EVENT_BOUNDARY,
    ArchiveEventQueueClient,
    publish_task_record_archive_events,
    task_record_to_archive_events,
)


class ArchiveEventPublisherTest(unittest.TestCase):
    def make_task_record(self, final_status="failed"):
        return {
            "task_id": "delivery-1",
            "delivery_mode": "fixed_route",
            "target": "trash_station",
            "return_target": "home",
            "started_at": 1.0,
            "ended_at": 3.0,
            "duration": 2.0,
            "final_status": final_status,
            "final_state": "error" if final_status != "success" else "idle",
            "error_code": "navigation_failed" if final_status != "success" else "",
            "error_message": "fixed route failed" if final_status != "success" else "",
            "failure_code": "NAV_FAIL" if final_status != "success" else "",
            "human_intervention_required": final_status != "success",
            "evidence_ref": "run-001",
            "state_transitions": [{"event": "loaded"}, {"event": "navigation_failed"}],
            "route_progress": {
                "checkpoint": "cp-1",
                "current_index": 1,
                "total": 3,
                "evidence_ref": "run-001",
                "keyframe_dir": "/tmp/keyframes/run-001",
                "source": "software_proof",
            },
            "elevator_assist": {
                "enabled": True,
                "mode": "dry_run",
                "state": "resume_delivery",
                "phase": "resume_delivery",
                "target_floor": "1",
                "requires_human_help": False,
                "reason": "dry-run complete",
                "events": [{"phase": "waiting_elevator_open"}],
            },
            "detection_snapshot_refs": ["vision://snapshot/1"],
        }

    def test_task_record_to_archive_events_matches_task_a_envelope(self):
        events = task_record_to_archive_events(self.make_task_record(), robot_id="robot-a")
        event_types = [event["event_type"] for event in events]

        self.assertEqual(event_types[0], "task_status")
        self.assertIn("elevator_state", event_types)
        self.assertIn("route_frame", event_types)
        self.assertIn("keyframe", event_types)
        self.assertIn("detection_result", event_types)
        self.assertIn("failure_reason", event_types)
        for event in events:
            self.assertEqual(event["robot_id"], "robot-a")
            self.assertEqual(event["task_id"], "delivery-1")
            self.assertEqual(event["source"], "software_proof")
            self.assertEqual(event["proof_status"], "not_proven")
            self.assertEqual(event["evidence_boundary"], ARCHIVE_EVENT_BOUNDARY)
            self.assertIn("timestamp", event)
            self.assertEqual(event["created_at"], event["timestamp"])
            self.assertEqual(event["evidence_ref"]["source"], "software_proof")
            self.assertEqual(event["evidence_ref"]["proof_status"], "not_proven")
            self.assertIsInstance(event["payload"], dict)

    def test_success_task_omits_failure_reason_but_keeps_route_and_detection(self):
        events = task_record_to_archive_events(self.make_task_record("success"), robot_id="robot-a")
        event_types = [event["event_type"] for event in events]

        self.assertNotIn("failure_reason", event_types)
        self.assertIn("task_status", event_types)
        self.assertIn("route_frame", event_types)
        self.assertIn("detection_result", event_types)

    def test_queue_client_keeps_local_retry_stub_when_no_archive_url(self):
        with tempfile.TemporaryDirectory() as td:
            queue_path = Path(td) / "events.jsonl"
            client = ArchiveEventQueueClient(queue_path)
            event = task_record_to_archive_events(self.make_task_record(), robot_id="robot-a")[0]
            result = client.submit_event(event)
            queued = [json.loads(line) for line in queue_path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(result["delivery_status"], "queued")
        self.assertEqual(result["retry_stub"]["reason"], "queued_without_archive_base_url")
        self.assertEqual(queued[0]["event"]["event_type"], "task_status")

    def test_http_failure_falls_back_to_local_queue(self):
        with tempfile.TemporaryDirectory() as td:
            queue_path = Path(td) / "events.jsonl"
            client = ArchiveEventQueueClient(queue_path, archive_base_url="http://127.0.0.1:1")
            event = task_record_to_archive_events(self.make_task_record(), robot_id="robot-a")[0]
            with mock.patch("urllib.request.urlopen", side_effect=OSError("offline")):
                result = client.submit_event(event)
            queued = [json.loads(line) for line in queue_path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(result["delivery_status"], "queued")
        self.assertEqual(result["retry_stub"]["reason"], "archive_post_failed_retry_stub")
        self.assertIn("offline", result["retry_stub"]["last_error"])
        self.assertEqual(queued[0]["event"]["source"], "software_proof")

    def test_publish_task_record_archive_events_reads_record_and_writes_queue(self):
        with tempfile.TemporaryDirectory() as td:
            task_record_path = Path(td) / "task.json"
            queue_path = Path(td) / "queue" / "events.jsonl"
            task_record_path.write_text(json.dumps(self.make_task_record()), encoding="utf-8")
            result = publish_task_record_archive_events(
                task_record_path,
                robot_id="robot-a",
                queue_path=queue_path,
            )
            queued = [json.loads(line) for line in queue_path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(result["event_count"], len(queued))
        self.assertEqual(result["queued_count"], len(queued))
        self.assertEqual(result["sent_count"], 0)
        self.assertEqual(queued[0]["event"]["robot_id"], "robot-a")


if __name__ == "__main__":
    unittest.main()
