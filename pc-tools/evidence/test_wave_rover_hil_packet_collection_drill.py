#!/usr/bin/env python3
"""wave_rover_hil_packet_collection_drill 的 dependency-free 围栏测试。"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
FIXTURE_DIR = THIS_DIR / "fixtures" / "wave_rover_hil_packet_collection_drill"
sys.path.insert(0, str(THIS_DIR))

import wave_rover_hil_packet_collection_drill as gate  # noqa: E402


class WaveRoverHilPacketCollectionDrillTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict[str, object]) -> Path:
        # 测试只写临时 JSON，确保 gate 不探测硬件、不访问 /dev、不调用 ROS graph。
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def execution_pack(self, evidence_ref: str = "hil-packet-drill-001") -> dict[str, object]:
        # 这是上一轮 execution pack 的最小 ready shape；真实性仍由 not_proven 边界约束。
        return {
            "schema": "trashbot.wave_rover_hil_packet_execution_pack.v1",
            "summary_schema": "trashbot.wave_rover_hil_packet_execution_pack_summary.v1",
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_wave_rover_hil_packet_execution_pack_gate",
            "overall_status": "not_proven",
            "execution_pack_status": "ready_for_real_hil_collection_not_proven",
            "same_evidence_ref_required": True,
            "evidence_ref": evidence_ref,
            "required_material_templates": [
                {"file": "feedback_T1001.log"},
                {"file": "odom_once.jsonl"},
                {"file": "imu_once.jsonl"},
                {"file": "battery_once.jsonl"},
                {"file": "operator_hil_report"},
            ],
            "collection_sequence": [
                "collect same evidence_ref feedback_T1001.log",
                "capture odom_once.jsonl",
                "capture imu_once.jsonl",
                "capture battery_once.jsonl",
                "write operator_hil_report",
            ],
            "owner_handoff": {
                "hardware-engineer": "collect real packet materials",
                "robot-software-engineer": "consume safe summaries",
                "full-stack-software-engineer": "keep actions disabled",
            },
            "backfill_guidance": [
                "Backfill missing packet files into a single material directory before rerunning intake."
            ],
            "rerun_commands": [
                "python3 pc-tools/evidence/wave_rover_hil_packet_intake.py --packet-dir <real_packet_dir>"
            ],
            "not_proven": [
                "real_wave_rover",
                "real_uart",
                "hil_pass",
                "real_odom",
                "real_imu",
                "real_battery",
                "delivery_success",
            ],
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def test_supported_execution_pack_outputs_collection_drill_not_proven(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.write_json(Path(td), "execution_pack.json", self.execution_pack())
            artifact, summary, exit_code = gate.build_collection_drill(path, "hil-packet-drill-001")

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.wave_rover_hil_packet_collection_drill.v1")
        self.assertEqual(summary["schema"], "trashbot.wave_rover_hil_packet_collection_drill_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_wave_rover_hil_packet_collection_drill_gate",
        )
        self.assertEqual(artifact["overall_status"], "not_proven")
        self.assertEqual(artifact["collection_drill_status"], "ready_for_real_hil_collection_drill_not_proven")
        self.assertIn("feedback_T1001.log", summary["required_material_templates"])
        self.assertIn("operator_hil_report", summary["required_material_templates"])
        self.assertTrue(any("safe_to_control=false" in item for item in [artifact["boundary_note"]]))
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(artifact["safe_to_control"])
        self.assertIn("hil_pass", artifact["not_proven"])

    def test_summary_and_wrapper_input_are_supported(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = {"payload": {"summary": self.execution_pack("hil-packet-wrapper")}}
            payload["payload"]["summary"]["schema"] = "trashbot.wave_rover_hil_packet_execution_pack_summary.v1"
            path = self.write_json(root, "wrapper.json", payload)
            artifact, _, exit_code = gate.build_collection_drill(path, "hil-packet-wrapper")

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema_status"], "supported")
        self.assertEqual(artifact["evidence_ref"], "hil-packet-wrapper")

    def test_missing_execution_pack_fails_closed_with_stable_shape(self):
        artifact, summary, exit_code = gate.build_collection_drill("/path/that/does/not/exist")

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["collection_drill_status"], "blocked_missing_wave_rover_hil_packet_execution_pack")
        self.assertEqual(summary["status"], "blocked_missing_wave_rover_hil_packet_execution_pack")
        self.assertIn("execution_pack:missing", artifact["blocked_reasons"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(artifact["safe_to_control"])

    def test_unsupported_schema_and_boundary_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            payload = self.execution_pack()
            payload["schema"] = "trashbot.other.v1"
            path = self.write_json(Path(td), "bad.json", payload)
            artifact, _, exit_code = gate.build_collection_drill(path)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["schema_status"], "unsupported_schema")
        self.assertEqual(artifact["collection_drill_status"], "blocked_unsupported_wave_rover_hil_packet_execution_pack")
        self.assertIn("unsupported_schema", artifact["blocked_reasons"])

    def test_success_claims_control_and_runtime_details_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            payload = self.execution_pack("hil-packet-unsafe")
            payload["delivery_success"] = True
            payload["primary_actions_enabled"] = True
            payload["safe_to_control"] = True
            payload["operator_note"] = "hil_pass=true /cmd_vel"
            payload["runtime_detail"] = "/dev/ttyUSB0"
            path = self.write_json(Path(td), "unsafe.json", payload)
            artifact, _, exit_code = gate.build_collection_drill(path, "hil-packet-unsafe")

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["collection_drill_status"], "blocked_unsafe_wave_rover_hil_packet_collection_drill_claim")
        self.assertTrue(any(issue.startswith("unsafe_input") for issue in artifact["blocked_reasons"]))
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(artifact["safe_to_control"])

    def test_evidence_ref_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.write_json(Path(td), "execution_pack.json", self.execution_pack("hil-packet-a"))
            artifact, _, exit_code = gate.build_collection_drill(path, "hil-packet-b")

        self.assertEqual(exit_code, 2)
        self.assertEqual(
            artifact["collection_drill_status"],
            "blocked_wave_rover_hil_packet_collection_drill_evidence_ref_mismatch",
        )
        self.assertIn("requested_evidence_ref_mismatch", artifact["blocked_reasons"])

    def test_missing_required_material_becomes_contract_blocker(self):
        with tempfile.TemporaryDirectory() as td:
            payload = self.execution_pack("hil-packet-missing")
            payload["required_material_templates"] = [{"file": "feedback_T1001.log"}]
            path = self.write_json(Path(td), "missing.json", payload)
            artifact, _, exit_code = gate.build_collection_drill(path, "hil-packet-missing")

        self.assertEqual(exit_code, 2)
        self.assertEqual(
            artifact["collection_drill_status"],
            "blocked_wave_rover_hil_packet_collection_drill_contract",
        )
        self.assertTrue(any(issue.startswith("required_material_template_missing") for issue in artifact["blocked_reasons"]))

    def test_execution_pack_not_ready_stays_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            payload = self.execution_pack("hil-packet-not-ready")
            payload["execution_pack_status"] = "blocked_review_decision_not_ready"
            path = self.write_json(Path(td), "blocked.json", payload)
            artifact, _, exit_code = gate.build_collection_drill(path, "hil-packet-not-ready")

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["collection_drill_status"], "blocked_execution_pack_not_ready")
        self.assertFalse(artifact["delivery_success"])

    def test_cli_writes_artifact_and_summary_from_fixture(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "artifact.json"
            summary = Path(td) / "summary.json"
            cmd = [
                sys.executable,
                str(THIS_DIR / "wave_rover_hil_packet_collection_drill.py"),
                "--execution-pack",
                str(FIXTURE_DIR / "execution_pack_ready.json"),
                "--evidence-ref",
                "hil-packet-collection-drill-fixture",
                "--output",
                str(output),
                "--summary-output",
                str(summary),
            ]
            result = subprocess.run(cmd, check=False, text=True, capture_output=True)
            artifact = json.loads(output.read_text(encoding="utf-8"))
            summary_payload = json.loads(summary.read_text(encoding="utf-8"))

        self.assertEqual(result.returncode, 0)
        self.assertIn("collection_drill_status: ready_for_real_hil_collection_drill_not_proven", result.stdout)
        self.assertEqual(artifact["collection_drill_status"], "ready_for_real_hil_collection_drill_not_proven")
        self.assertEqual(summary_payload["schema"], "trashbot.wave_rover_hil_packet_collection_drill_summary.v1")


if __name__ == "__main__":
    unittest.main()
