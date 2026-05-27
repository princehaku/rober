import json
from pathlib import Path
import sys
import tempfile
import unittest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from ros2_trashbot_nav.algorithm_evidence_feed import (  # noqa: E402
    ARCHIVE_SCHEMA,
    EVIDENCE_BOUNDARY,
    PROOF_STATUS,
    SOURCE,
    build_offline_algorithm_archive,
    write_offline_algorithm_archive,
)


class AlgorithmEvidenceFeedTest(unittest.TestCase):
    def test_archive_matches_o6_schema_and_o7_consumable_shapes(self):
        archive = build_offline_algorithm_archive(robot_id="robot-o6-01", task_id="task-o6-d")

        self.assertEqual(archive["schema"], ARCHIVE_SCHEMA)
        self.assertEqual(archive["source"], SOURCE)
        self.assertEqual(archive["proof_status"], PROOF_STATUS)
        self.assertEqual(archive["evidence_boundary"], EVIDENCE_BOUNDARY)
        self.assertTrue(archive["mock_feed"])
        self.assertTrue(archive["offline_only"])
        self.assertFalse(archive["real_cloud_archive_connected"])
        self.assertFalse(archive["real_realtime_api_connected"])

        task = archive["tasks"][0]
        self.assertEqual(task["robot_id"], "robot-o6-01")
        self.assertEqual(task["task_id"], "task-o6-d")
        self.assertEqual(task["status"], "offline_mock_bundle")
        self.assertEqual(task["evidence_ref"]["proof_status"], PROOF_STATUS)

        route_frames = [event for event in archive["events"] if event["event_type"] == "route_frame"]
        self.assertEqual(len(route_frames), 3)
        first_payload = route_frames[0]["payload"]
        self.assertEqual(first_payload["frame_index"], 0)
        self.assertEqual(first_payload["pose"]["x_m"], 0.0)
        self.assertEqual(first_payload["velocity"]["linear_mps"], 0.0)
        self.assertIn("mock://", first_payload["evidence_ref"])

        asr_events = [event for event in archive["events"] if event["event_type"] == "asr_transcript"]
        tts_events = [event for event in archive["events"] if event["event_type"] == "tts_draft"]
        command_events = [event for event in archive["events"] if event["event_type"] == "safe_command_stub"]
        self.assertEqual([event["payload"]["event_type"] for event in asr_events], ["partial", "final"])
        self.assertEqual(tts_events[0]["payload"]["voice_profile"], "mock-operator-default")
        self.assertEqual({event["payload"]["command_type"] for event in command_events}, {"manual_turn", "navigate_goal"})
        for event in asr_events + tts_events + command_events:
            self.assertEqual(event["source"], SOURCE)
            self.assertEqual(event["proof_status"], PROOF_STATUS)
            self.assertIn("mock://", event["payload"]["evidence_ref"])

    def test_annotations_and_inferences_cover_algorithm_review_labels(self):
        archive = build_offline_algorithm_archive()
        labels = {item["label_type"] for item in archive["annotations"]}
        inference_types = {item["inference_type"] for item in archive["inferences"]}

        self.assertEqual(labels, {"elevator_door_state", "floor_label", "obstacle_type"})
        self.assertEqual(inference_types, {"elevator_door_state", "floor_label"})
        self.assertIn("real_asr_tts_runtime", archive["not_proven"])
        self.assertIn("real_safe_command_api", archive["not_proven"])
        self.assertIn("real_robot_ack", archive["not_proven"])
        for item in archive["annotations"] + archive["inferences"]:
            self.assertEqual(item["robot_id"], "trashbot-dev")
            self.assertEqual(item["task_id"], "offline-algorithm-evidence-001")
            self.assertEqual(item["evidence_ref"]["source"], SOURCE)
            self.assertEqual(item["evidence_ref"]["proof_status"], PROOF_STATUS)

    def test_write_offline_algorithm_archive_writes_json_file(self):
        with tempfile.TemporaryDirectory() as td:
            output_path = Path(td) / "algorithm_archive.json"
            archive = write_offline_algorithm_archive(output_path, robot_id="robot-a", task_id="task-a")
            loaded = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(loaded["schema"], ARCHIVE_SCHEMA)
        self.assertEqual(loaded["tasks"][0]["task_id"], "task-a")
        self.assertEqual(loaded["events"][0]["task_id"], archive["tasks"][0]["task_id"])


if __name__ == "__main__":
    unittest.main()
