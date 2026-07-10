import json
import tempfile
import unittest
from pathlib import Path

import sys


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import o5_same_task_mission_archive_smoke as smoke  # noqa: E402


class O5SameTaskMissionArchiveSmokeTest(unittest.TestCase):
    def test_run_smoke_proves_reconciliation_archive_consumer_chain(self):
        # 该 smoke 必须严格走 reconciliation v2 -> manifest -> O6 archive -> consumer 主链路。
        summary = smoke.run_smoke(task_id="o5-same-task-unit-001")

        self.assertEqual(summary["schema"], smoke.SMOKE_SCHEMA)
        self.assertEqual(summary["proof_boundary"], smoke.SMOKE_PROOF_BOUNDARY)
        self.assertEqual(summary["status"], "ready")
        self.assertEqual(summary["task_id"], "o5-same-task-unit-001")
        self.assertEqual(summary["relay_state_backend"], "file")
        self.assertFalse(summary["relay_restart_readback"])
        self.assertFalse(summary["sqlite_state_store_reopened"])
        self.assertEqual(summary["reconciliation"]["schema"], "trashbot.cloud_command_result_reconciliation.v2")
        self.assertEqual(summary["reconciliation"]["result_state"], "terminal_result_recorded")
        self.assertEqual(summary["reconciliation"]["terminal_result_schema"], "trashbot.cloud_command_terminal_result.v1")
        self.assertEqual(summary["manifest"]["delivery_result_source_schema"], "trashbot.cloud_command_terminal_result.v1")
        self.assertEqual(
            summary["manifest"]["same_task_mission_gate_status"],
            "same_task_mission_gate_ready_not_success_proof",
        )
        self.assertEqual(
            summary["archive"]["same_task_mission_gate_status"],
            "same_task_mission_gate_ready_not_success_proof",
        )
        self.assertEqual(
            summary["consumer"]["same_task_mission_gate_status"],
            "same_task_mission_gate_ready_not_success_proof",
        )
        self.assertEqual(
            summary["archive"]["cloud_external_probe_status"],
            "cloud_external_probe_ready_not_production_proof",
        )
        self.assertEqual(
            summary["archive"]["cloud_db_queue_external_probe_status"],
            "cloud_db_queue_external_probe_ready_not_production_proof",
        )
        self.assertEqual(
            summary["consumer"]["cloud_external_probe_status"],
            "cloud_external_probe_ready_not_production_proof",
        )
        self.assertEqual(summary["consumer"]["cloud_external_probe_endpoint_count"], 3)
        self.assertEqual(
            summary["consumer"]["cloud_db_queue_external_probe_status"],
            "cloud_db_queue_external_probe_ready_not_production_proof",
        )
        self.assertEqual(summary["consumer"]["cloud_db_queue_external_probe_probe_count"], 8)
        self.assertIn("o5-same-task-command-001", summary["consumer"]["terminal_refs"])
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["robot_control_executed"])
        self.assertFalse(summary["connects_cloud_production"])

    def test_run_smoke_sqlite_restarts_relay_before_reconciliation_readback(self):
        # SQLite shadow 必须证明 terminal result 跨 relay restart 仍能被 reconciliation 和 O6 gate 消费。
        summary = smoke.run_smoke(task_id="o5-same-task-sqlite-unit-001", state_backend="sqlite")

        self.assertEqual(summary["schema"], smoke.SMOKE_SCHEMA)
        self.assertEqual(summary["proof_boundary"], smoke.SMOKE_PROOF_BOUNDARY)
        self.assertEqual(summary["status"], "ready")
        self.assertEqual(summary["task_id"], "o5-same-task-sqlite-unit-001")
        self.assertEqual(summary["relay_state_backend"], "sqlite")
        self.assertTrue(summary["relay_restart_readback"])
        self.assertTrue(summary["sqlite_state_store_reopened"])
        self.assertEqual(summary["reconciliation"]["result_state"], "terminal_result_recorded")
        self.assertEqual(summary["reconciliation"]["terminal_result_schema"], "trashbot.cloud_command_terminal_result.v1")
        self.assertEqual(
            summary["consumer"]["same_task_mission_gate_status"],
            "same_task_mission_gate_ready_not_success_proof",
        )
        self.assertEqual(
            summary["consumer"]["cloud_external_probe_status"],
            "cloud_external_probe_ready_not_production_proof",
        )
        self.assertEqual(
            summary["consumer"]["cloud_db_queue_external_probe_status"],
            "cloud_db_queue_external_probe_ready_not_production_proof",
        )
        self.assertFalse(summary["connects_cloud_production"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["robot_control_executed"])

    def test_main_writes_summary_json(self):
        # CLI 入口必须可单独输出 JSON，方便 sprint artifact 和本地重放复核。
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "smoke.json"
            rc = smoke.main(["--task-id", "o5-same-task-unit-002", "--output", str(output)])
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(rc, 0)
        self.assertEqual(payload["task_id"], "o5-same-task-unit-002")
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["relay_state_backend"], "file")
        self.assertEqual(payload["generated_files"]["manifest_output"], "field_evidence_manifest.json")
        self.assertEqual(
            payload["generated_files"]["cloud_external_probe_artifact"],
            "cloud_external_probe.json",
        )


if __name__ == "__main__":
    unittest.main()
