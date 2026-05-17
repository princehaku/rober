#!/usr/bin/env python3
"""wave_rover_hil_packet_review_decision 的 dependency-free 围栏测试。"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
FIXTURE_DIR = THIS_DIR / "fixtures" / "wave_rover_hil_packet_review_decision"
sys.path.insert(0, str(THIS_DIR))

import wave_rover_hil_packet_review_decision as gate  # noqa: E402


class WaveRoverHilPacketReviewDecisionTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict[str, object]) -> Path:
        # 测试只写临时 summary，不打开串口、不访问 /dev、不调用 ROS graph。
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def intake_summary(self, evidence_ref: str = "hil-packet-review-001") -> dict[str, object]:
        # 这是上一轮 intake 的最小 pass shape；真实性仍由 not_proven 边界约束。
        return {
            "schema": "trashbot.wave_rover_hil_packet_intake.v1",
            "summary_schema": "trashbot.wave_rover_hil_packet_intake_summary.v1",
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_wave_rover_hil_packet_intake_gate",
            "overall_status": "ready_for_hil_packet_review_not_proven",
            "packet_status": "pass",
            "same_evidence_ref_required": True,
            "evidence_ref": evidence_ref,
            "required_files": [
                "feedback_T1001.log",
                "odom_once.jsonl",
                "imu_once.jsonl",
                "battery_once.jsonl",
                "operator_hil_report",
            ],
            "file_status": {
                "feedback_T1001.log": "pass",
                "odom_once.jsonl": "pass",
                "imu_once.jsonl": "pass",
                "battery_once.jsonl": "pass",
                "operator_hil_report": "pass",
            },
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

    def test_supported_intake_outputs_blocked_pending_real_hil_packet(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.write_json(Path(td), "intake.json", self.intake_summary())
            artifact, summary, exit_code = gate.build_review_decision(path, "hil-packet-review-001")

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.wave_rover_hil_packet_review_decision.v1")
        self.assertEqual(artifact["summary_schema"], "trashbot.wave_rover_hil_packet_review_decision_summary.v1")
        self.assertEqual(artifact["evidence_boundary"], "software_proof_docker_wave_rover_hil_packet_review_decision_gate")
        self.assertEqual(artifact["overall_status"], "not_proven")
        self.assertEqual(artifact["review_decision"], "blocked_pending_real_hil_packet")
        self.assertEqual(summary["review_decision"], "blocked_pending_real_hil_packet")
        self.assertIn("software-proof feedback_T1001.log", artifact["accepted_required_materials"])
        self.assertIn("real feedback_T1001.log", artifact["missing_required_materials"])
        self.assertEqual(artifact["rejected_required_materials"], [])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertIn("hil_pass", artifact["not_proven"])

    def test_missing_intake_summary_fails_closed_with_stable_shape(self):
        artifact, summary, exit_code = gate.build_review_decision("/path/that/does/not/exist")

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["review_decision"], "blocked_missing_wave_rover_hil_packet_intake")
        self.assertEqual(summary["status"], "blocked_missing_wave_rover_hil_packet_intake")
        self.assertIn("intake_summary:missing", artifact["issues"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])

    def test_unsupported_schema_and_boundary_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            payload = self.intake_summary()
            payload["schema"] = "trashbot.other.v1"
            path = self.write_json(Path(td), "bad.json", payload)
            artifact, _, exit_code = gate.build_review_decision(path)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["schema_status"], "unsupported_schema")
        self.assertEqual(artifact["review_decision"], "blocked_unsupported_wave_rover_hil_packet_intake")
        self.assertIn("unsupported_schema", artifact["issues"])

    def test_success_claims_and_primary_action_enable_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            payload = self.intake_summary("hil-packet-unsafe")
            payload["delivery_success"] = True
            payload["primary_actions_enabled"] = True
            payload["operator_note"] = "hil_pass=true"
            path = self.write_json(Path(td), "unsafe.json", payload)
            artifact, _, exit_code = gate.build_review_decision(path, "hil-packet-unsafe")

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["review_decision"], "blocked_unsafe_wave_rover_hil_packet_claim")
        self.assertTrue(any(issue.startswith("unsafe_input") for issue in artifact["issues"]))
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])

    def test_evidence_ref_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.write_json(Path(td), "intake.json", self.intake_summary("hil-packet-a"))
            artifact, _, exit_code = gate.build_review_decision(path, "hil-packet-b")

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["review_decision"], "blocked_wave_rover_hil_packet_evidence_ref_mismatch")
        self.assertIn("requested_evidence_ref_mismatch", artifact["issues"])

    def test_missing_file_status_becomes_contract_blocker(self):
        with tempfile.TemporaryDirectory() as td:
            payload = self.intake_summary("hil-packet-missing")
            payload["file_status"] = {"feedback_T1001.log": "pass"}
            path = self.write_json(Path(td), "missing.json", payload)
            artifact, _, exit_code = gate.build_review_decision(path, "hil-packet-missing")

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["review_decision"], "blocked_wave_rover_hil_packet_review_contract")
        self.assertIn("odom_once.jsonl", artifact["software_proof_missing_materials"])
        self.assertTrue(any(issue.startswith("missing_required_material") for issue in artifact["issues"]))

    def test_cli_writes_artifact_and_summary_from_fixture(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "artifact.json"
            summary = Path(td) / "summary.json"
            cmd = [
                sys.executable,
                str(THIS_DIR / "wave_rover_hil_packet_review_decision.py"),
                "--intake-summary",
                str(FIXTURE_DIR / "intake_ready.json"),
                "--evidence-ref",
                "hil-packet-review-fixture",
                "--output",
                str(output),
                "--summary-output",
                str(summary),
            ]
            result = subprocess.run(cmd, check=False, text=True, capture_output=True)
            artifact = json.loads(output.read_text(encoding="utf-8"))
            summary_payload = json.loads(summary.read_text(encoding="utf-8"))

        self.assertEqual(result.returncode, 0)
        self.assertIn("review_decision: blocked_pending_real_hil_packet", result.stdout)
        self.assertEqual(artifact["review_decision"], "blocked_pending_real_hil_packet")
        self.assertEqual(summary_payload["schema"], "trashbot.wave_rover_hil_packet_review_decision_summary.v1")


if __name__ == "__main__":
    unittest.main()
