#!/usr/bin/env python3
"""elevator assist rehearsal evidence gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import elevator_assist_rehearsal_evidence as gate  # noqa: E402


class ElevatorAssistRehearsalEvidenceTest(unittest.TestCase):
    def build(self, **kwargs: str) -> dict:
        # 测试直接调用纯函数，保证 gate 不依赖 ROS2、Nav2、硬件、电梯或网络。
        artifact, exit_code = gate.build_rehearsal_evidence(
            kwargs.get("evidence_ref", "elevator-rehearsal-001"),
            kwargs.get("target_floor", "1F"),
            kwargs.get("failure_phase", ""),
            kwargs.get("failure_reason", ""),
            kwargs.get("manual_takeover_reason", ""),
        )
        self.assertEqual(exit_code, 0)
        return artifact

    def test_ready_artifact_contains_required_contract_without_delivery_claim(self):
        artifact = self.build()

        self.assertEqual(artifact["schema"], "trashbot.elevator_assist_rehearsal_evidence.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_elevator_evidence_driven_mainline_gate",
        )
        self.assertEqual(artifact["source"], "software_proof")
        self.assertEqual(
            artifact["rehearsal_evidence_verdict"],
            "ready_for_robot_dry_run_readonly_rehearsal_evidence_not_proven",
        )
        self.assertEqual(artifact["evidence_ref"], "elevator-rehearsal-001")
        self.assertEqual(artifact["target_floor"], "1F")
        self.assertTrue(artifact["same_evidence_ref_required"])
        self.assertEqual(
            sorted(artifact["phase_evidence"].keys()),
            sorted(gate.REQUIRED_PHASES),
        )
        self.assertIn("target_floor", artifact["phase_evidence"]["requesting_floor_help"])
        self.assertIn("real_elevator_door_state", artifact["not_proven"])
        self.assertIn("delivery_success", artifact["not_proven"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertEqual(artifact["phone_safe_summary"]["source"], "software_proof")
        self.assertFalse(artifact["phone_safe_summary"]["delivery_success"])
        self.assertFalse(artifact["phone_safe_summary"]["primary_actions_enabled"])

    def test_failure_phase_blocks_robot_consumption_but_keeps_contract(self):
        artifact = self.build(
            failure_phase="waiting_target_floor",
            failure_reason="target_floor_not_confirmed",
            manual_takeover_reason="observer_keeps_robot_stationary",
        )

        self.assertEqual(
            artifact["rehearsal_evidence_verdict"],
            "blocked_rehearsal_failure_injected_not_proven",
        )
        self.assertEqual(artifact["failure"]["phase"], "waiting_target_floor")
        self.assertEqual(artifact["failure"]["reason"], "target_floor_not_confirmed")
        self.assertEqual(artifact["failure"]["manual_takeover_reason"], "observer_keeps_robot_stationary")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])

    def test_invalid_evidence_ref_or_target_floor_fail_closed(self):
        bad_ref = self.build(evidence_ref="/tmp/local/path.json")
        bad_floor = self.build(target_floor="/dev/ttyUSB0")

        self.assertEqual(bad_ref["rehearsal_evidence_verdict"], "blocked_invalid_evidence_ref")
        self.assertEqual(bad_ref["evidence_ref"], "")
        self.assertEqual(bad_floor["rehearsal_evidence_verdict"], "blocked_invalid_target_floor")
        self.assertEqual(bad_floor["target_floor"], "")
        self.assertFalse(bad_ref["delivery_success"])
        self.assertFalse(bad_floor["primary_actions_enabled"])

    def test_artifact_and_summary_stay_phone_safe(self):
        artifact = self.build()
        encoded = json.dumps(artifact, ensure_ascii=False)

        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB", encoded)
        self.assertNotIn("baudrate", encoded)
        self.assertNotIn("WAVE ROVER", encoded)
        self.assertNotIn("Authorization", encoded)
        self.assertNotIn("raw robot response", encoded)
        self.assertNotIn("delivery completed", encoded.lower())
        self.assertNotIn("dropoff success", encoded.lower())

    def test_write_output_creates_json_file(self):
        with tempfile.TemporaryDirectory() as td:
            artifact = self.build()
            output = Path(td) / "nested" / "elevator_assist_rehearsal_evidence.json"
            gate.write_rehearsal_evidence(artifact, str(output))
            loaded = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(loaded["schema"], "trashbot.elevator_assist_rehearsal_evidence.v1")
        self.assertEqual(loaded["source"], "software_proof")
        self.assertEqual(loaded["evidence_ref"], "elevator-rehearsal-001")
        self.assertFalse(loaded["delivery_success"])


if __name__ == "__main__":
    unittest.main()
