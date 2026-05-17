#!/usr/bin/env python3
"""wave_rover_hil_packet_intake 的 dependency-free 围栏测试。"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
FIXTURE_DIR = THIS_DIR / "fixtures" / "wave_rover_hil_packet_intake"
sys.path.insert(0, str(THIS_DIR))

import wave_rover_hil_packet_intake as gate  # noqa: E402


class WaveRoverHilPacketIntakeTest(unittest.TestCase):
    def write_text(self, root: Path, name: str, content: str) -> Path:
        # 测试只写临时 packet，不打开串口、不访问 /dev、不调用 ROS graph。
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def topic_payload(self, label: str, evidence_ref: str) -> dict[str, object]:
        # once snapshot 只放最小字段，真实性由 not_proven 边界阻止误读。
        payload: dict[str, object] = {"header": {"stamp": 1.0, "evidence_ref": evidence_ref}}
        if label == "odom":
            payload["pose"] = {"pose": {"position": {"x": 0.0}, "orientation": {"w": 1.0}}}
        elif label == "imu":
            payload["orientation"] = {"w": 1.0}
            payload["angular_velocity"] = {"z": 0.0}
        elif label == "battery":
            payload["voltage"] = 12.1
        return payload

    def write_packet(self, root: Path, evidence_ref: str = "hil-packet-001") -> Path:
        # happy path 覆盖直接 feedback 与 wrapper feedback，两者都绑定 evidence_ref。
        feedback_lines = [
            {"timestamp": 1.0, "evidence_ref": evidence_ref, "T": 1001, "L": 0.1, "R": 0.1, "r": 0.0, "p": 0.0, "y": 0.01, "v": 12.2},
            {
                "timestamp": 1.1,
                "evidence_ref": evidence_ref,
                "feedback": {"T": 1001, "L": 0.0, "R": 0.0, "r": 0.0, "p": 0.0, "y": 0.02, "v": 12.2},
            },
        ]
        self.write_text(root, "feedback_T1001.log", "\n".join(json.dumps(line) for line in feedback_lines) + "\n")
        for label, file_name in (("odom", "odom_once.jsonl"), ("imu", "imu_once.jsonl"), ("battery", "battery_once.jsonl")):
            self.write_text(root, file_name, json.dumps(self.topic_payload(label, evidence_ref)) + "\n")
        self.write_text(
            root,
            "operator_hil_report.json",
            json.dumps(
                {
                    "evidence_ref": evidence_ref,
                    "operator": "hardware-engineer",
                    "run_timestamp": "2026-05-17T21:22:00Z",
                    "robot_id": "trashbot-lab-unit",
                    "serial_visibility_statement": "synthetic packet only; no local device path captured",
                    "stop_path_statement": "stop command path not exercised in this software_proof gate",
                    "result_boundary": "not_proven; delivery_success=false; primary_actions_enabled=false",
                    "notes": "synthetic fixture for contract validation",
                },
                ensure_ascii=False,
            )
            + "\n",
        )
        return root

    def test_passes_with_complete_synthetic_packet(self):
        with tempfile.TemporaryDirectory() as td:
            packet = self.write_packet(Path(td))
            artifact, exit_code = gate.build_summary(str(packet), "hil-packet-001")

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.wave_rover_hil_packet_intake.v1")
        self.assertEqual(artifact["summary_schema"], "trashbot.wave_rover_hil_packet_intake_summary.v1")
        self.assertEqual(artifact["evidence_boundary"], "software_proof_docker_wave_rover_hil_packet_intake_gate")
        self.assertEqual(artifact["source"], "software_proof")
        self.assertEqual(artifact["overall_status"], "ready_for_hil_packet_review_not_proven")
        self.assertEqual(artifact["packet_status"], "pass")
        self.assertTrue(artifact["same_evidence_ref_required"])
        self.assertEqual(artifact["evidence_ref"], "hil-packet-001")
        self.assertIn("feedback_T1001.log", artifact["required_files"])
        self.assertIn("operator_hil_report", artifact["required_files"])
        self.assertIn("hil_pass", artifact["not_proven"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])

    def test_packet_dir_missing_fails_closed_with_stable_shape(self):
        artifact, exit_code = gate.build_summary("/path/that/does/not/exist", "")

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["packet_status"], "blocked")
        self.assertEqual(artifact["overall_status"], "blocked_not_proven")
        self.assertIn("packet_dir_missing", artifact["issues"])
        self.assertFalse(artifact["delivery_success"])

    def test_missing_required_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            packet = self.write_packet(Path(td), "hil-packet-missing")
            (packet / "imu_once.jsonl").unlink()
            artifact, exit_code = gate.build_summary(str(packet), "hil-packet-missing")

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["file_status"]["imu_once.jsonl"], "blocked")
        self.assertIn("imu_once.jsonl:missing", artifact["issues"])
        self.assertFalse(artifact["primary_actions_enabled"])

    def test_bad_feedback_and_missing_t1001_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            packet = self.write_packet(Path(td), "hil-packet-bad")
            (packet / "feedback_T1001.log").write_text("{bad json\n" + json.dumps({"T": 1002, "evidence_ref": "hil-packet-bad"}) + "\n", encoding="utf-8")
            artifact, exit_code = gate.build_summary(str(packet), "hil-packet-bad")

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["feedback_T1001"]["status"], "blocked")
        self.assertIn("line_1:bad_json", artifact["issues"])
        self.assertIn("line_2:missing_T1001", artifact["issues"])

    def test_jsonl_malformed_or_evidence_ref_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            packet = self.write_packet(Path(td), "hil-packet-a")
            (packet / "battery_once.jsonl").write_text(json.dumps(self.topic_payload("battery", "hil-packet-b")) + "\n", encoding="utf-8")
            (packet / "odom_once.jsonl").write_text("{bad json\n", encoding="utf-8")
            artifact, exit_code = gate.build_summary(str(packet), "hil-packet-a")

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["packet_status"], "blocked")
        self.assertIn("odom_line_1:bad_json", artifact["issues"])
        self.assertIn("packet_evidence_ref_mismatch", artifact["issues"])
        self.assertIn("requested_evidence_ref_mismatch", artifact["issues"])

    def test_feedback_evidence_ref_participates_in_packet_alignment(self):
        with tempfile.TemporaryDirectory() as td:
            packet = self.write_packet(Path(td), "hil-packet-topic")
            (packet / "feedback_T1001.log").write_text(
                json.dumps(
                    {
                        "timestamp": 1.0,
                        "evidence_ref": "hil-packet-feedback",
                        "T": 1001,
                        "L": 0.1,
                        "R": 0.1,
                        "r": 0.0,
                        "p": 0.0,
                        "y": 0.01,
                        "v": 12.2,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            artifact, exit_code = gate.build_summary(str(packet), "hil-packet-topic")

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["feedback_T1001"]["evidence_ref"], "hil-packet-feedback")
        self.assertIn("packet_evidence_ref_mismatch", artifact["issues"])
        self.assertIn("requested_evidence_ref_mismatch", artifact["issues"])

    def test_operator_report_json_and_md_contract(self):
        with tempfile.TemporaryDirectory() as td:
            packet = self.write_packet(Path(td), "hil-packet-md")
            (packet / "operator_hil_report.json").unlink()
            self.write_text(
                packet,
                "operator_hil_report.md",
                "\n".join(
                    [
                        "evidence_ref: hil-packet-md",
                        "operator: hardware-engineer",
                        "run_timestamp: 2026-05-17T21:22:00Z",
                        "robot_id: trashbot-lab-unit",
                        "serial_visibility_statement: synthetic packet only",
                        "stop_path_statement: stop path not exercised",
                        "result_boundary: not_proven delivery_success=false primary_actions_enabled=false",
                    ]
                )
                + "\n",
            )
            artifact, exit_code = gate.build_summary(str(packet), "hil-packet-md")

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["operator_hil_report"]["format"], "md")
        self.assertEqual(artifact["operator_hil_report"]["status"], "pass")

    def test_unsafe_leakage_and_success_claims_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            packet = self.write_packet(Path(td), "hil-packet-leak")
            report = json.loads((packet / "operator_hil_report.json").read_text(encoding="utf-8"))
            report["notes"] = "serial_port=/dev/ttyUSB0 delivery_success=true"
            (packet / "operator_hil_report.json").write_text(json.dumps(report) + "\n", encoding="utf-8")
            artifact, exit_code = gate.build_summary(str(packet), "hil-packet-leak")

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["operator_hil_report"]["status"], "blocked")
        self.assertTrue(any("unsafe_token" in issue for issue in artifact["issues"]))
        self.assertTrue(any("success_claim" in issue for issue in artifact["issues"]))

    def test_cli_writes_summary_and_uses_fixture_packet(self):
        output = None
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "summary.json"
            cmd = [
                sys.executable,
                str(THIS_DIR / "wave_rover_hil_packet_intake.py"),
                str(FIXTURE_DIR / "pass"),
                "--evidence-ref",
                "hil-packet-fixture-pass",
                "--summary-output",
                str(output),
                "--once-json",
            ]
            result = subprocess.run(cmd, check=False, text=True, capture_output=True)
            written = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(result.returncode, 0)
        self.assertIn("trashbot.wave_rover_hil_packet_intake.v1", result.stdout)
        self.assertEqual(written["packet_status"], "pass")
        self.assertFalse(written["delivery_success"])


if __name__ == "__main__":
    unittest.main()
