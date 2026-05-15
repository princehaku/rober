#!/usr/bin/env python3
"""route/elevator field-session handoff gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import route_elevator_field_session_handoff as handoff  # noqa: E402


class RouteElevatorFieldSessionHandoffTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 临时 JSON 让测试 dependency-free，不依赖 ROS2、Nav2、硬件、电梯或云。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def pc_route_debug_console(self, evidence_ref: str) -> dict:
        # PC console 样本保留 route/elevator nested summary，但不声明真实路线成功。
        return {
            "schema": "trashbot.pc_route_debug_console.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_pc_route_debug_console_gate",
            "status": "available_software_proof",
            "evidence_ref": evidence_ref,
            "route_progress": {
                "evidence_ref": evidence_ref,
                "checkpoint_id": "trash_station_route:003",
                "checkpoint": 3,
            },
            "route_elevator_reconciliation": {
                "status": "reconciled_not_proven",
                "evidence_ref": evidence_ref,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "not_proven": ["real_nav2_fixed_route_run", "delivery_success"],
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def route_completion_signal(self, evidence_ref: str) -> dict:
        # completion signal 可以是 completed_not_proven；handoff 不能升级成送达成功。
        return {
            "schema": "trashbot.route_task_completion_signal.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_completion_signal_gate",
            "same_evidence_ref_required": True,
            "evidence_ref": evidence_ref,
            "completion_verdict": "completed_not_proven",
            "materials_status": {
                "missing_materials": [],
                "mismatch_reasons": [],
            },
            "phone_safe_summary": {
                "schema": "trashbot.route_task_completion_signal.v1",
                "evidence_boundary": "software_proof_docker_route_task_completion_signal_gate",
                "status": "completed_not_proven",
                "completion_verdict": "completed_not_proven",
                "evidence_ref": evidence_ref,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "not_proven": ["real_dropoff_completion", "delivery_success"],
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def elevator_route_reconciliation(self, evidence_ref: str) -> dict:
        # elevator-route 复账样本来自上一轮 gate，仍只是不证明现场电梯。
        return {
            "schema": "trashbot.elevator_route_evidence_reconciliation.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_elevator_route_evidence_reconciliation_gate",
            "same_evidence_ref_required": True,
            "same_evidence_ref_status": "matched_same_evidence_ref",
            "evidence_ref": evidence_ref,
            "reconciliation_verdict": "reconciled_not_proven",
            "materials_status": {
                "missing_materials": [],
                "mismatch_reasons": [],
            },
            "phone_safe_summary": {
                "schema": "trashbot.elevator_route_evidence_reconciliation_summary.v1",
                "source": "software_proof",
                "evidence_boundary": "software_proof_docker_elevator_route_evidence_reconciliation_gate",
                "status": "reconciled_not_proven",
                "reconciliation_verdict": "reconciled_not_proven",
                "evidence_ref": evidence_ref,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "not_proven": ["real_elevator_door_state", "delivery_success"],
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def build_with_payloads(
        self,
        root: Path,
        pc_payload: dict,
        completion_payload: dict,
        reconciliation_payload: dict,
        evidence_ref: str,
    ) -> tuple[dict, dict]:
        # 公共 helper 让 case 聚焦 schema/ref/safety，而不是文件读写样板。
        pc_path = self.write_json(root, "pc_route_debug.json", pc_payload)
        completion_path = self.write_json(root, "route_completion.json", completion_payload)
        reconciliation_path = self.write_json(root, "elevator_reconciliation.json", reconciliation_payload)
        artifact, summary, exit_code = handoff.build_handoff(
            str(pc_path),
            str(completion_path),
            str(reconciliation_path),
            evidence_ref,
            session_id="session-001",
            operator="field-operator",
            location="test-building",
            time_window="2026-05-16T04:30Z/2026-05-16T05:00Z",
        )
        self.assertEqual(exit_code, 0)
        return artifact, summary

    def test_ready_handoff_not_proven_with_same_evidence_ref(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = str(root / "run-001.json")
            artifact, summary = self.build_with_payloads(
                root,
                self.pc_route_debug_console(evidence_ref),
                self.route_completion_signal(evidence_ref),
                self.elevator_route_reconciliation(evidence_ref),
                evidence_ref,
            )

        self.assertEqual(artifact["schema"], "trashbot.route_elevator_field_session_handoff.v1")
        self.assertEqual(summary["schema"], "trashbot.route_elevator_field_session_handoff_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_elevator_field_session_handoff_gate",
        )
        self.assertEqual(artifact["schema_version"], 1)
        self.assertEqual(artifact["source"], "software_proof")
        self.assertEqual(artifact["handoff_verdict"], "ready_for_field_session_handoff_not_proven")
        self.assertEqual(artifact["same_evidence_ref_status"], "matched_same_evidence_ref")
        self.assertEqual(artifact["evidence_ref"], "file:run-001.json")
        self.assertEqual(len(artifact["required_materials"]), 9)
        self.assertIn("door_state.json", summary["required_materials_summary"]["required_names"])
        self.assertIn("real_nav2_fixed_route_run", artifact["not_proven"])
        self.assertIn("real_elevator_door_state", artifact["not_proven"])
        self.assertIn("delivery_success", artifact["not_proven"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(artifact["robot_diagnostics_summary"]["delivery_success"])
        self.assertFalse(artifact["mobile_readonly_summary"]["primary_actions_enabled"])

    def test_accepts_summary_inputs_without_full_artifacts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = "run-summary-001"
            pc_summary = self.pc_route_debug_console(evidence_ref)
            completion_summary = self.route_completion_signal(evidence_ref)["phone_safe_summary"]
            reconciliation_summary = self.elevator_route_reconciliation(evidence_ref)["phone_safe_summary"]
            artifact, _ = self.build_with_payloads(root, pc_summary, completion_summary, reconciliation_summary, evidence_ref)

        self.assertEqual(artifact["handoff_verdict"], "ready_for_field_session_handoff_not_proven")
        self.assertEqual(artifact["source_summaries"]["route_completion_signal"]["schema_status"], "supported")
        self.assertEqual(artifact["source_summaries"]["elevator_route_reconciliation"]["schema_status"], "supported")

    def test_missing_bad_json_and_unsupported_contract_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = "run-002"
            pc_path = self.write_json(root, "pc.json", self.pc_route_debug_console(evidence_ref))
            missing_completion = root / "missing-completion.json"
            reconciliation_path = self.write_json(root, "reconciliation.json", self.elevator_route_reconciliation(evidence_ref))
            missing_artifact, _, _ = handoff.build_handoff(
                str(pc_path),
                str(missing_completion),
                str(reconciliation_path),
                evidence_ref,
            )

            bad_json = root / "bad.json"
            bad_json.write_text("{bad json", encoding="utf-8")
            bad_artifact, _, _ = handoff.build_handoff(str(pc_path), str(bad_json), str(reconciliation_path), evidence_ref)

            completion = self.route_completion_signal(evidence_ref)
            completion["schema"] = "trashbot.unsupported_completion.v99"
            unsupported_artifact, _ = self.build_with_payloads(
                root,
                self.pc_route_debug_console(evidence_ref),
                completion,
                self.elevator_route_reconciliation(evidence_ref),
                evidence_ref,
            )

        self.assertEqual(missing_artifact["handoff_verdict"], "blocked_missing_inputs")
        self.assertEqual(bad_artifact["handoff_verdict"], "blocked_invalid_input")
        self.assertEqual(unsupported_artifact["handoff_verdict"], "blocked_invalid_input")
        self.assertIn("route_completion_signal:unsupported_schema", unsupported_artifact["materials_status"]["missing_inputs"])

    def test_unsupported_boundary_or_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = "run-003"
            pc = self.pc_route_debug_console(evidence_ref)
            pc["evidence_boundary"] = "wrong_boundary"
            wrong_boundary, _ = self.build_with_payloads(
                root,
                pc,
                self.route_completion_signal(evidence_ref),
                self.elevator_route_reconciliation(evidence_ref),
                evidence_ref,
            )
            reconciliation = self.elevator_route_reconciliation(evidence_ref)
            reconciliation["source"] = "production_cloud"
            wrong_source, _ = self.build_with_payloads(
                root,
                self.pc_route_debug_console(evidence_ref),
                self.route_completion_signal(evidence_ref),
                reconciliation,
                evidence_ref,
            )

        self.assertEqual(wrong_boundary["handoff_verdict"], "blocked_invalid_input")
        self.assertIn("pc_route_debug_console:unsupported_boundary", wrong_boundary["materials_status"]["missing_inputs"])
        self.assertEqual(wrong_source["handoff_verdict"], "blocked_invalid_input")
        self.assertIn("elevator_route_reconciliation:unsupported_source", wrong_source["materials_status"]["missing_inputs"])

    def test_evidence_ref_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact, _ = self.build_with_payloads(
                root,
                self.pc_route_debug_console("run-004"),
                self.route_completion_signal("run-other"),
                self.elevator_route_reconciliation("run-004"),
                "run-004",
            )

        self.assertEqual(artifact["handoff_verdict"], "blocked_evidence_ref_mismatch")
        self.assertTrue(artifact["materials_status"]["mismatch_reasons"])
        self.assertFalse(artifact["delivery_success"])

    def test_unsafe_copy_is_redacted_and_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pc = self.pc_route_debug_console("run-005")
            pc["operator_note"] = "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 baudrate=115200 raw robot response"
            artifact, _ = self.build_with_payloads(
                root,
                pc,
                self.route_completion_signal("run-005"),
                self.elevator_route_reconciliation("run-005"),
                "run-005",
            )

        encoded = json.dumps(artifact, ensure_ascii=False)
        self.assertEqual(artifact["handoff_verdict"], "blocked_unsafe_copy")
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("baudrate=115200", encoded)
        self.assertNotIn("raw robot response", encoded)

    def test_success_or_control_claim_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            completion = self.route_completion_signal("run-006")
            completion["delivery_success"] = True
            success_artifact, _ = self.build_with_payloads(
                root,
                self.pc_route_debug_console("run-006"),
                completion,
                self.elevator_route_reconciliation("run-006"),
                "run-006",
            )
            pc = self.pc_route_debug_console("run-007")
            pc["primary_actions_enabled"] = True
            control_artifact, _ = self.build_with_payloads(
                root,
                pc,
                self.route_completion_signal("run-007"),
                self.elevator_route_reconciliation("run-007"),
                "run-007",
            )
            reconciliation = self.elevator_route_reconciliation("run-008")
            reconciliation["operator_next_steps"] = ["delivery success completed"]
            claim_artifact, _ = self.build_with_payloads(
                root,
                self.pc_route_debug_console("run-008"),
                self.route_completion_signal("run-008"),
                reconciliation,
                "run-008",
            )

        self.assertEqual(success_artifact["handoff_verdict"], "blocked_success_claim")
        self.assertEqual(control_artifact["handoff_verdict"], "blocked_success_claim")
        self.assertEqual(claim_artifact["handoff_verdict"], "blocked_success_claim")
        self.assertFalse(success_artifact["delivery_success"])
        self.assertFalse(control_artifact["primary_actions_enabled"])

    def test_write_artifact_and_summary_outputs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact, summary = self.build_with_payloads(
                root,
                self.pc_route_debug_console("run-009"),
                self.route_completion_signal("run-009"),
                self.elevator_route_reconciliation("run-009"),
                "run-009",
            )
            artifact_path = root / "nested" / "handoff.json"
            summary_path = root / "nested" / "handoff_summary.json"
            handoff.write_json(artifact, str(artifact_path))
            handoff.write_json(summary, str(summary_path))
            loaded_artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            loaded_summary = json.loads(summary_path.read_text(encoding="utf-8"))

        self.assertEqual(loaded_artifact["schema"], "trashbot.route_elevator_field_session_handoff.v1")
        self.assertEqual(loaded_summary["schema"], "trashbot.route_elevator_field_session_handoff_summary.v1")
        self.assertFalse(loaded_artifact["delivery_success"])


if __name__ == "__main__":
    unittest.main()
