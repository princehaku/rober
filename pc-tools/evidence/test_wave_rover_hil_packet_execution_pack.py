#!/usr/bin/env python3
"""wave_rover_hil_packet_execution_pack 的 dependency-free 围栏测试。"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
FIXTURE_DIR = THIS_DIR / "fixtures" / "wave_rover_hil_packet_execution_pack"
sys.path.insert(0, str(THIS_DIR))

import wave_rover_hil_packet_execution_pack as gate  # noqa: E402


class WaveRoverHilPacketExecutionPackTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict[str, object]) -> Path:
        # 测试只写临时 JSON，确保 gate 不探测串口、不访问 /dev、不调用 ROS graph。
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def review_summary(self, evidence_ref: str = "hil-packet-execution-001") -> dict[str, object]:
        # 这是上一轮 review decision 的最小 ready shape；真实性仍由 not_proven 边界约束。
        return {
            "schema": "trashbot.wave_rover_hil_packet_review_decision.v1",
            "summary_schema": "trashbot.wave_rover_hil_packet_review_decision_summary.v1",
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_wave_rover_hil_packet_review_decision_gate",
            "overall_status": "not_proven",
            "review_decision": "blocked_pending_real_hil_packet",
            "same_evidence_ref_required": True,
            "evidence_ref": evidence_ref,
            "accepted_required_materials": [
                "software-proof feedback_T1001.log",
                "software-proof odom_once.jsonl",
                "software-proof imu_once.jsonl",
                "software-proof battery_once.jsonl",
                "software-proof operator_hil_report",
            ],
            "missing_required_materials": [
                "real feedback_T1001.log",
                "real odom_once.jsonl",
                "real imu_once.jsonl",
                "real battery_once.jsonl",
                "operator_hil_report",
            ],
            "next_required_evidence": [
                "real WAVE ROVER HIL run",
                "same evidence_ref HIL packet",
                "real feedback_T1001.log",
                "real odom_once.jsonl",
                "real imu_once.jsonl",
                "real battery_once.jsonl",
                "operator_hil_report",
            ],
            "owner_handoff": {
                "hardware-engineer": "collect real HIL packet on a host with WAVE ROVER UART access",
                "robot-software-engineer": "keep diagnostics read-only until review_decision changes with real evidence",
                "full-stack-software-engineer": "keep mobile panel read-only and actions disabled",
            },
            "rerun_commands": [
                "python3 pc-tools/evidence/wave_rover_hil_packet_intake.py --packet-dir <real_packet_dir>",
                "python3 pc-tools/evidence/wave_rover_hil_packet_review_decision.py --intake-summary <summary.json>",
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

    def test_supported_review_decision_outputs_execution_pack_not_proven(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.write_json(Path(td), "review.json", self.review_summary())
            artifact, summary, exit_code = gate.build_execution_pack(path, "hil-packet-execution-001")

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.wave_rover_hil_packet_execution_pack.v1")
        self.assertEqual(summary["schema"], "trashbot.wave_rover_hil_packet_execution_pack_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_wave_rover_hil_packet_execution_pack_gate",
        )
        self.assertEqual(artifact["overall_status"], "not_proven")
        self.assertEqual(artifact["execution_pack_status"], "ready_for_real_hil_collection_not_proven")
        self.assertEqual(summary["execution_pack_status"], "ready_for_real_hil_collection_not_proven")
        self.assertIn("feedback_T1001.log", summary["required_material_templates"])
        self.assertTrue(any("collect same evidence_ref feedback_T1001.log" in item for item in artifact["collection_sequence"]))
        self.assertIn("owner_handoff", artifact)
        self.assertIn("backfill_guidance", artifact)
        self.assertIn("rerun_commands", artifact)
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertIn("hil_pass", artifact["not_proven"])

    def test_summary_and_wrapper_input_are_supported(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = {"payload": {"summary": self.review_summary("hil-packet-wrapper")}}
            path = self.write_json(root, "wrapper.json", payload)
            artifact, _, exit_code = gate.build_execution_pack(path, "hil-packet-wrapper")

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema_status"], "supported")
        self.assertEqual(artifact["evidence_ref"], "hil-packet-wrapper")

    def test_missing_review_summary_fails_closed_with_stable_shape(self):
        artifact, summary, exit_code = gate.build_execution_pack("/path/that/does/not/exist")

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["execution_pack_status"], "blocked_missing_wave_rover_hil_packet_review_decision")
        self.assertEqual(summary["status"], "blocked_missing_wave_rover_hil_packet_review_decision")
        self.assertIn("review_summary:missing", artifact["issues"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])

    def test_unsupported_schema_and_boundary_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            payload = self.review_summary()
            payload["schema"] = "trashbot.other.v1"
            path = self.write_json(Path(td), "bad.json", payload)
            artifact, _, exit_code = gate.build_execution_pack(path)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["schema_status"], "unsupported_schema")
        self.assertEqual(artifact["execution_pack_status"], "blocked_unsupported_wave_rover_hil_packet_review_decision")
        self.assertIn("unsupported_schema", artifact["issues"])

    def test_success_claims_and_primary_action_enable_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            payload = self.review_summary("hil-packet-unsafe")
            payload["delivery_success"] = True
            payload["primary_actions_enabled"] = True
            payload["operator_note"] = "hil_pass=true"
            path = self.write_json(Path(td), "unsafe.json", payload)
            artifact, _, exit_code = gate.build_execution_pack(path, "hil-packet-unsafe")

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["execution_pack_status"], "blocked_unsafe_wave_rover_hil_packet_claim")
        self.assertTrue(any(issue.startswith("unsafe_input") for issue in artifact["issues"]))
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])

    def test_evidence_ref_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.write_json(Path(td), "review.json", self.review_summary("hil-packet-a"))
            artifact, _, exit_code = gate.build_execution_pack(path, "hil-packet-b")

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["execution_pack_status"], "blocked_wave_rover_hil_packet_evidence_ref_mismatch")
        self.assertIn("requested_evidence_ref_mismatch", artifact["issues"])

    def test_missing_next_required_evidence_becomes_contract_blocker(self):
        with tempfile.TemporaryDirectory() as td:
            payload = self.review_summary("hil-packet-missing")
            payload["next_required_evidence"] = ["real WAVE ROVER HIL run"]
            path = self.write_json(Path(td), "missing.json", payload)
            artifact, _, exit_code = gate.build_execution_pack(path, "hil-packet-missing")

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["execution_pack_status"], "blocked_wave_rover_hil_packet_execution_pack_contract")
        self.assertTrue(any(issue.startswith("next_required_evidence_missing") for issue in artifact["issues"]))

    def test_review_decision_not_ready_stays_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            payload = self.review_summary("hil-packet-not-ready")
            payload["review_decision"] = "blocked_unsafe_wave_rover_hil_packet_claim"
            path = self.write_json(Path(td), "blocked.json", payload)
            artifact, _, exit_code = gate.build_execution_pack(path, "hil-packet-not-ready")

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["execution_pack_status"], "blocked_review_decision_not_ready")
        self.assertFalse(artifact["delivery_success"])

    def test_cli_writes_artifact_and_summary_from_fixture(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "artifact.json"
            summary = Path(td) / "summary.json"
            cmd = [
                sys.executable,
                str(THIS_DIR / "wave_rover_hil_packet_execution_pack.py"),
                "--review-summary",
                str(FIXTURE_DIR / "review_ready.json"),
                "--evidence-ref",
                "hil-packet-execution-fixture",
                "--output",
                str(output),
                "--summary-output",
                str(summary),
            ]
            result = subprocess.run(cmd, check=False, text=True, capture_output=True)
            artifact = json.loads(output.read_text(encoding="utf-8"))
            summary_payload = json.loads(summary.read_text(encoding="utf-8"))

        self.assertEqual(result.returncode, 0)
        self.assertIn("execution_pack_status: ready_for_real_hil_collection_not_proven", result.stdout)
        self.assertEqual(artifact["execution_pack_status"], "ready_for_real_hil_collection_not_proven")
        self.assertEqual(summary_payload["schema"], "trashbot.wave_rover_hil_packet_execution_pack_summary.v1")


if __name__ == "__main__":
    unittest.main()
