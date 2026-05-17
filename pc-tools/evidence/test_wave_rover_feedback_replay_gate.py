#!/usr/bin/env python3
"""wave_rover_feedback_replay_gate 的 dependency-free 围栏测试。"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import wave_rover_feedback_replay_gate as gate  # noqa: E402


class WaveRoverFeedbackReplayGateTest(unittest.TestCase):
    def write_text(self, root: Path, name: str, content: str) -> Path:
        # 测试只写临时文件，避免依赖真实串口、ROS2 graph 或 WAVE ROVER。
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def topic_line(self, topic: str, evidence_ref: str) -> str:
        # once snapshot 使用最小字段；真实性仍由 not_proven 阻止误读。
        common = {"header": {"stamp": 1.0, "evidence_ref": evidence_ref}}
        if topic == "odom":
            common["pose"] = {"pose": {"position": {"x": 0.0}, "orientation": {"w": 1.0}}}
        elif topic == "imu":
            common["orientation"] = {"w": 1.0}
            common["angular_velocity"] = {"z": 0.0}
        elif topic == "battery":
            common["voltage"] = 12.1
        return json.dumps(common)

    def write_topics(self, root: Path, evidence_ref: str) -> tuple[Path, Path, Path]:
        # 失败 case 复用 topic fixture 时不能重写 feedback_T1001.log。
        odom = self.write_text(root, "odom_once.jsonl", self.topic_line("odom", evidence_ref) + "\n")
        imu = self.write_text(root, "imu_once.jsonl", self.topic_line("imu", evidence_ref) + "\n")
        battery = self.write_text(root, "battery_once.jsonl", self.topic_line("battery", evidence_ref) + "\n")
        return odom, imu, battery

    def build_paths(self, root: Path, evidence_ref: str = "run-001") -> tuple[Path, Path, Path, Path]:
        # happy path 同时覆盖直接 JSON 和 wrapper JSON 两种 feedback 行格式。
        feedback = "\n".join(
            [
                json.dumps({"timestamp": 1.0, "T": 1001, "L": 0.1, "R": 0.1, "r": 0.0, "p": 0.0, "y": 0.01, "v": 12.2}),
                json.dumps({"timestamp": 1.1, "feedback": {"T": 1001, "L": 0.1, "R": 0.1, "r": 0.0, "p": 0.0, "y": 0.02, "v": 12.2}}),
                json.dumps({"time": 1.2, "message": json.dumps({"T": 1001, "L": 0.0, "R": 0.0, "r": 0.0, "p": 0.0, "y": 0.02, "v": 12.2})}),
            ]
        )
        feedback_path = self.write_text(root, "feedback_T1001.log", feedback + "\n")
        odom, imu, battery = self.write_topics(root, evidence_ref)
        return feedback_path, odom, imu, battery

    def test_passes_with_t1001_feedback_interval_and_topic_alignment(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            feedback, odom, imu, battery = self.build_paths(root)
            artifact, exit_code = gate.build_summary(str(feedback), str(odom), str(imu), str(battery), "run-001")

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.wave_rover_feedback_replay.v1")
        self.assertEqual(artifact["evidence_boundary"], "software_proof_docker_wave_rover_feedback_replay_gate")
        self.assertEqual(artifact["source"], "software_proof")
        self.assertEqual(artifact["overall_status"], "ready_for_hil_review_not_proven")
        self.assertEqual(artifact["feedback_replay_status"], "pass")
        self.assertEqual(artifact["interval_status"], "pass")
        self.assertEqual(artifact["topic_alignment_status"], "pass")
        self.assertTrue(artifact["same_evidence_ref_required"])
        self.assertIn("real_hil_pass", artifact["not_proven"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])

    def test_timestamp_less_feedback_is_parseable_but_interval_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            feedback = self.write_text(
                root,
                "feedback_T1001.log",
                json.dumps({"T": 1001, "L": 0.1, "R": 0.1, "r": 0, "p": 0, "y": 0, "v": 12.0}) + "\n",
            )
            odom, imu, battery = self.write_topics(root, "run-no-ts")
            artifact, exit_code = gate.build_summary(str(feedback), str(odom), str(imu), str(battery), "run-no-ts")

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["feedback_replay_status"], "pass")
        self.assertEqual(artifact["interval_status"], "blocked_missing_timestamps")
        self.assertEqual(artifact["overall_status"], "blocked_not_proven")
        self.assertFalse(artifact["delivery_success"])

    def test_bad_feedback_json_or_missing_fields_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            feedback = self.write_text(root, "feedback_T1001.log", "{bad json\n" + json.dumps({"T": 1001, "L": 1}) + "\n")
            odom, imu, battery = self.write_topics(root, "run-bad")
            artifact, exit_code = gate.build_summary(str(feedback), str(odom), str(imu), str(battery), "run-bad")

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["feedback_replay_status"], "blocked")
        self.assertIn("line_1:bad_json", artifact["feedback_replay"]["errors"])
        self.assertFalse(artifact["primary_actions_enabled"])

    def test_evidence_ref_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            feedback, odom, imu, battery = self.build_paths(root, "run-a")
            battery.write_text(self.topic_line("battery", "run-b") + "\n", encoding="utf-8")
            artifact, exit_code = gate.build_summary(str(feedback), str(odom), str(imu), str(battery), "run-a")

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["topic_alignment_status"], "blocked")
        self.assertIn("evidence_ref_mismatch", artifact["topic_alignment"]["issues"])
        self.assertIn("topic_evidence_ref_mismatch", artifact["topic_alignment"]["issues"])

    def test_missing_topic_or_minimum_fields_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            feedback, odom, imu, battery = self.build_paths(root, "run-missing")
            imu.write_text(json.dumps({"header": {"evidence_ref": "run-missing"}}) + "\n", encoding="utf-8")
            battery.unlink()
            artifact, exit_code = gate.build_summary(str(feedback), str(odom), str(imu), str(battery), "run-missing")

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["topic_alignment_status"], "blocked")
        self.assertIn("imu_missing_minimum_fields", artifact["topic_alignment"]["issues"])
        self.assertIn("battery_missing", artifact["topic_alignment"]["issues"])

    def test_large_gap_and_unordered_timestamps_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            feedback, odom, imu, battery = self.build_paths(root, "run-gap")
            feedback.write_text(
                "\n".join(
                    json.dumps({"timestamp": stamp, "T": 1001, "L": 0, "R": 0, "r": 0, "p": 0, "y": 0, "v": 12})
                    for stamp in (1.0, 1.1, 4.5)
                )
                + "\n",
                encoding="utf-8",
            )
            artifact, _ = gate.build_summary(str(feedback), str(odom), str(imu), str(battery), "run-gap")
        self.assertEqual(artifact["interval_status"], "blocked_large_gap")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            feedback, odom, imu, battery = self.build_paths(root, "run-order")
            feedback.write_text(
                "\n".join(
                    json.dumps({"timestamp": stamp, "T": 1001, "L": 0, "R": 0, "r": 0, "p": 0, "y": 0, "v": 12})
                    for stamp in (2.0, 1.0)
                )
                + "\n",
                encoding="utf-8",
            )
            artifact, _ = gate.build_summary(str(feedback), str(odom), str(imu), str(battery), "run-order")
        self.assertEqual(artifact["interval_status"], "blocked_unordered_timestamps")

    def test_cli_writes_summary_and_once_json(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            feedback, odom, imu, battery = self.build_paths(root, "run-cli")
            output = root / "summary.json"
            cmd = [
                sys.executable,
                str(THIS_DIR / "wave_rover_feedback_replay_gate.py"),
                str(feedback),
                str(odom),
                str(imu),
                str(battery),
                "--evidence-ref",
                "run-cli",
                "--summary-output",
                str(output),
                "--once-json",
            ]
            result = subprocess.run(cmd, check=False, text=True, capture_output=True)
            written = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(result.returncode, 0)
        self.assertIn("trashbot.wave_rover_feedback_replay.v1", result.stdout)
        self.assertEqual(written["overall_status"], "ready_for_hil_review_not_proven")


if __name__ == "__main__":
    unittest.main()
