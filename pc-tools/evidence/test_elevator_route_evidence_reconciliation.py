#!/usr/bin/env python3
"""elevator route evidence reconciliation gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import elevator_route_evidence_reconciliation as gate  # noqa: E402


class ElevatorRouteEvidenceReconciliationTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 临时 JSON 让测试保持 dependency-free，不依赖 ROS2、Nav2、硬件、电梯或网络。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def elevator_artifact(self, evidence_ref: str) -> dict:
        # 样本覆盖电梯阶段 evidence，但每个阶段都只是不证明现场状态的 rehearsal 材料。
        return {
            "schema": "trashbot.elevator_assist_rehearsal_evidence.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_elevator_evidence_driven_mainline_gate",
            "evidence_ref": evidence_ref,
            "target_floor": "1F",
            "same_evidence_ref_required": True,
            "rehearsal_evidence_verdict": "ready_for_robot_dry_run_readonly_rehearsal_evidence_not_proven",
            "phase_evidence": {
                "waiting_elevator_open": {"evidence_ref": evidence_ref},
                "entering_elevator": {"evidence_ref": evidence_ref},
                "requesting_floor_help": {"evidence_ref": evidence_ref, "target_floor": "1F"},
                "waiting_target_floor": {"evidence_ref": evidence_ref, "target_floor": "1F"},
                "exiting_elevator": {"evidence_ref": evidence_ref},
            },
            "phone_safe_summary": {
                "schema": "trashbot.elevator_assist_rehearsal_evidence_summary.v1",
                "source": "software_proof",
                "evidence_boundary": "software_proof_docker_elevator_evidence_driven_mainline_gate",
                "status": "ready_for_robot_dry_run_readonly_rehearsal_evidence_not_proven",
                "evidence_ref": evidence_ref,
                "target_floor": "1F",
                "phase_names": ["waiting_elevator_open", "entering_elevator", "requesting_floor_help"],
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "not_proven": ["real_elevator_door_state", "delivery_success"],
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def route_completion(self, evidence_ref: str) -> dict:
        # completion signal 可以是 completed_not_proven，但本 gate 不把它升级为真实送达。
        return {
            "schema": "trashbot.route_task_completion_signal.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_completion_signal_gate",
            "same_evidence_ref_required": True,
            "evidence_ref": evidence_ref,
            "completion_verdict": "completed_not_proven",
            "fixed_route_summary": {"route_status": "replay_pass", "target": "trash_station"},
            "task_record_summary": {"task_status": "returned_idle", "last_state": "IDLE"},
            "dropoff_completion": {"material_status": "material_present_not_proven", "completion_claimed": True},
            "cancel_completion": {"material_status": "not_provided", "completion_claimed": False},
            "failure_reason": "",
            "recovery_reason": "",
            "phone_safe_summary": {
                "schema": "trashbot.route_task_completion_signal.v1",
                "evidence_boundary": "software_proof_docker_route_task_completion_signal_gate",
                "status": "completed_not_proven",
                "completion_verdict": "completed_not_proven",
                "evidence_ref": evidence_ref,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "not_proven": ["real_delivery", "real_dropoff_completion", "delivery_success"],
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def build(self, root: Path, elevator_payload: dict, route_payload: dict, evidence_ref: str = "") -> dict:
        # 公共 helper 让 case 聚焦 ref/schema/safety 规则，而不是文件读写样板。
        elevator_path = self.write_json(root, "elevator.json", elevator_payload)
        route_path = self.write_json(root, "route_completion.json", route_payload)
        artifact, exit_code = gate.build_reconciliation(str(elevator_path), str(route_path), evidence_ref)
        self.assertEqual(exit_code, 0)
        return artifact

    def test_reconciled_not_proven_with_same_evidence_ref(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = str(root / "run-001.json")
            artifact = self.build(
                root,
                self.elevator_artifact(evidence_ref),
                self.route_completion(evidence_ref),
                evidence_ref,
            )

        self.assertEqual(artifact["schema"], "trashbot.elevator_route_evidence_reconciliation.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_elevator_route_evidence_reconciliation_gate",
        )
        self.assertEqual(artifact["schema_version"], 1)
        self.assertEqual(artifact["source"], "software_proof")
        self.assertTrue(artifact["same_evidence_ref_required"])
        self.assertEqual(artifact["same_evidence_ref_status"], "matched_same_evidence_ref")
        self.assertEqual(artifact["reconciliation_verdict"], "reconciled_not_proven")
        self.assertEqual(artifact["evidence_ref"], "file:run-001.json")
        self.assertEqual(artifact["elevator_rehearsal_summary"]["target_floor"], "1F")
        self.assertEqual(artifact["route_completion_summary"]["completion_verdict"], "completed_not_proven")
        self.assertIn("real_elevator_door_state", artifact["not_proven"])
        self.assertIn("real_nav2_fixed_route_run", artifact["not_proven"])
        self.assertIn("delivery_success", artifact["not_proven"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertEqual(
            artifact["phone_safe_summary"]["schema"],
            "trashbot.elevator_route_evidence_reconciliation_summary.v1",
        )
        self.assertFalse(artifact["phone_safe_summary"]["delivery_success"])
        self.assertFalse(artifact["phone_safe_summary"]["primary_actions_enabled"])

    def test_accepts_source_summaries_without_full_artifacts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = "run-summary-001"
            elevator_summary = self.elevator_artifact(evidence_ref)["phone_safe_summary"]
            route_summary = self.route_completion(evidence_ref)["phone_safe_summary"]
            artifact = self.build(root, elevator_summary, route_summary, evidence_ref)

        self.assertEqual(artifact["reconciliation_verdict"], "reconciled_not_proven")
        self.assertEqual(artifact["source_states"]["elevator_rehearsal"]["schema_status"], "supported")
        self.assertEqual(artifact["source_states"]["route_completion"]["schema_status"], "supported")
        self.assertEqual(artifact["evidence_ref"], "run-summary-001")

    def test_missing_or_bad_json_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            elevator_path = self.write_json(root, "elevator.json", self.elevator_artifact("run-002"))
            bad_path = root / "bad.json"
            bad_path.write_text("{bad json", encoding="utf-8")
            artifact, _ = gate.build_reconciliation(str(elevator_path), str(bad_path), "run-002")

        self.assertEqual(artifact["reconciliation_verdict"], "blocked_bad_json")
        self.assertFalse(artifact["delivery_success"])

    def test_unsupported_schema_and_boundary_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            elevator = self.elevator_artifact("run-003")
            route = self.route_completion("run-003")
            route["schema"] = "trashbot.unsupported_completion.v99"
            route["evidence_boundary"] = "wrong_boundary"
            artifact = self.build(root, elevator, route, "run-003")

        self.assertEqual(artifact["reconciliation_verdict"], "blocked_unsupported_schema")
        self.assertIn("route_completion:unsupported_schema", artifact["materials_status"]["missing_materials"])

    def test_evidence_ref_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact = self.build(
                root,
                self.elevator_artifact("run-004"),
                self.route_completion("run-other"),
                "run-004",
            )

        self.assertEqual(artifact["same_evidence_ref_status"], "blocked_evidence_ref_mismatch")
        self.assertEqual(artifact["reconciliation_verdict"], "blocked_evidence_ref_mismatch")
        self.assertTrue(artifact["materials_status"]["mismatch_reasons"])
        self.assertFalse(artifact["delivery_success"])

    def test_unsafe_copy_is_redacted_and_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            route = self.route_completion("run-005")
            route["phone_safe_summary"]["operator_note"] = (
                "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 baudrate=115200 raw robot response"
            )
            artifact = self.build(root, self.elevator_artifact("run-005"), route, "run-005")
            encoded = json.dumps(artifact, ensure_ascii=False)

        self.assertEqual(artifact["reconciliation_verdict"], "blocked_unsafe_copy")
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertFalse(artifact["delivery_success"])

    def test_success_or_control_claim_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            route = self.route_completion("run-006")
            route["delivery_success"] = True
            artifact = self.build(root, self.elevator_artifact("run-006"), route, "run-006")

        self.assertEqual(artifact["reconciliation_verdict"], "blocked_success_claim")
        self.assertFalse(artifact["delivery_success"])

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            route = self.route_completion("run-007")
            route["phone_safe_summary"]["primary_actions_enabled"] = True
            artifact = self.build(root, self.elevator_artifact("run-007"), route, "run-007")

        self.assertEqual(artifact["reconciliation_verdict"], "blocked_control_claim")
        self.assertFalse(artifact["primary_actions_enabled"])

    def test_write_output_creates_json_file(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact = self.build(root, self.elevator_artifact("run-008"), self.route_completion("run-008"), "run-008")
            output = root / "nested" / "elevator_route_evidence_reconciliation.json"
            gate.write_reconciliation(artifact, str(output))
            loaded = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(loaded["schema"], "trashbot.elevator_route_evidence_reconciliation.v1")
        self.assertEqual(loaded["phone_safe_summary"]["schema"], "trashbot.elevator_route_evidence_reconciliation_summary.v1")
        self.assertEqual(loaded["reconciliation_verdict"], "reconciled_not_proven")
        self.assertFalse(loaded["delivery_success"])


if __name__ == "__main__":
    unittest.main()
