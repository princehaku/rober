#!/usr/bin/env python3
"""field evidence material resolution owner response intake gate 的围栏测试。"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools/evidence 不是常规 package；测试显式加入目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_material_resolution_followup_escalation_status as followup  # noqa: E402
import field_evidence_material_resolution_owner_response_intake as gate  # noqa: E402
import field_evidence_material_resolution_reviewer_ack_followup_escalation_status as reviewer_ack_followup  # noqa: E402


# 测试约束 01：fixture 只表达上一轮 safe followup escalation summary。
# 测试约束 02：owner response 缺失时必须 missing/not_proven，不能 accepted。
# 测试约束 03：accepted 只表示 accepted_for_review_not_proven。
# 测试约束 04：同一 safe evidence_ref 是硬约束。
# 测试约束 05：success/control/reviewer-resolution/field proof claim 必须拒绝。
# 测试约束 06：PR #5 thread X 必须保持 unresolved / hardware_material_pending。
# 测试约束 07：输出保持 source=software_proof 和 not_proven。
# 测试约束 08：输出保持 primary_actions_enabled=false。
# 测试约束 09：输出保持 delivery_success=false。
# 测试约束 10：输出保持 safe_to_control=false。
# 测试约束 11：测试不访问 ROS graph、硬件、外部云或手机 runtime。


class FieldEvidenceMaterialResolutionOwnerResponseIntakeTest(unittest.TestCase):
    def _write_json(self, root: Path, name: str, payload: object) -> Path:
        # 临时 JSON 只服务离线围栏，不模拟真实现场材料。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _followup_summary(self, evidence_ref: str, status: str = followup.ESCALATED_STATUS) -> dict[str, object]:
        # source 使用上一轮 followup escalation 的安全消费面。
        return {
            "schema": followup.SUMMARY_SCHEMA,
            "schema_version": 1,
            "source": "software_proof",
            "status": "not_proven",
            "capability": followup.CAPABILITY,
            "followup_status": status,
            "field_evidence_material_resolution_followup_escalation_status": status,
            "evidence_boundary": followup.EVIDENCE_BOUNDARY,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "owner_response_material_status": "missing",
            "next_required_evidence": list(gate.DEFAULT_REQUIRED_MATERIALS),
            "lineage": {
                "previous_handoff": followup.PREVIOUS_HANDOFF_COMMIT,
                "previous_handoff_capability": "field_evidence_material_resolution_review_handoff",
            },
            "pr5_thread": {
                "thread_id": followup.PR5_THREAD_ID,
                "state": "unresolved",
                "material_state": "hardware_material_pending",
            },
            "not_proven": ["not_proven"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_copy": (
                f"{followup.CAPABILITY}: evidence_ref={evidence_ref}; owner response material missing; "
                "source=software_proof; not_proven; primary_actions_enabled=false; "
                "delivery_success=false; safe_to_control=false."
            ),
        }

    def _reviewer_ack_summary(
        self,
        evidence_ref: str,
        status: str = reviewer_ack_followup.ACCEPTED_FOR_OWNER_RESPONSE_INTAKE,
        schema: str = reviewer_ack_followup.SUMMARY_SCHEMA,
    ) -> dict[str, object]:
        # reviewer ACK followup 是本轮新增桥接 source，仍然只能是 software_proof/not_proven。
        return {
            "schema": schema,
            "schema_version": 1,
            "source": "software_proof",
            "status": "not_proven",
            "capability": reviewer_ack_followup.CAPABILITY,
            "followup_status": status,
            "field_evidence_material_resolution_reviewer_ack_followup_escalation_status": status,
            "evidence_boundary": reviewer_ack_followup.EVIDENCE_BOUNDARY,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "owner_response_material_status": "pending",
            "next_required_evidence": list(gate.DEFAULT_REQUIRED_MATERIALS),
            "lineage": {
                "previous_handoff": "field_evidence_material_resolution_reviewer_ack_review_handoff",
                "previous_handoff_capability": "field_evidence_material_resolution_reviewer_ack_review_handoff",
            },
            "pr5_thread": {
                "thread_id": followup.PR5_THREAD_ID,
                "state": "unresolved",
                "material_state": "hardware_material_pending",
            },
            "not_proven": ["not_proven"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_copy": (
                f"{reviewer_ack_followup.CAPABILITY}: followup_status={status}; "
                f"evidence_ref={evidence_ref}; source=software_proof; not_proven; "
                "primary_actions_enabled=false; delivery_success=false; safe_to_control=false."
            ),
        }

    def _accepted_response(self, evidence_ref: str) -> dict[str, object]:
        # accepted 样本只给安全索引，不携带真实 raw artifact。
        return {
            "schema": "trashbot.field_evidence_material_resolution_owner_response_packet.v1",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "materials": {
                name: {
                    "name": name,
                    "status": "accepted",
                    "safe_evidence_ref": evidence_ref,
                    "summary": f"sanitized owner response material index for {name}",
                    "delivery_success": False,
                    "safe_to_control": False,
                    "primary_actions_enabled": False,
                }
                for name in gate.DEFAULT_REQUIRED_MATERIALS
            },
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def _build(
        self,
        root: Path,
        source_payload: dict[str, object],
        response_payload: dict[str, object] | None = None,
        evidence_ref: str = "field-resolution-owner-101",
    ) -> tuple[dict[str, object], dict[str, object], int]:
        # 公共 helper 让 case 聚焦 intake 分类和安全边界。
        source_path = self._write_json(root, "followup.json", source_payload)
        response_path = ""
        if response_payload is not None:
            response_path = str(self._write_json(root, "owner-response.json", response_payload))
        return gate.build_field_evidence_material_resolution_owner_response_intake(
            str(source_path),
            response_path,
            evidence_ref,
        )

    def test_safe_owner_response_is_received_not_reviewed_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._followup_summary("field-resolution-owner-101"),
                self._accepted_response("field-resolution-owner-101"),
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], gate.SCHEMA)
        self.assertEqual(summary["schema"], gate.SUMMARY_SCHEMA)
        self.assertEqual(artifact["capability"], gate.CAPABILITY)
        self.assertEqual(artifact["evidence_boundary"], gate.EVIDENCE_BOUNDARY)
        self.assertEqual(artifact["owner_response_material_status"], "received_not_reviewed")
        self.assertEqual(artifact["review_readiness"], gate.ACCEPTED_REVIEW_READINESS)
        self.assertEqual(len(artifact["accepted_materials"]), len(gate.DEFAULT_REQUIRED_MATERIALS))
        self.assertEqual(artifact["missing_materials"], [])
        self.assertEqual(artifact["rejected_materials"], [])
        self.assertEqual(artifact["unsafe_materials"], [])
        self.assertEqual(artifact["previous_escalation_reference"]["capability"], followup.CAPABILITY)
        self.assertEqual(artifact["previous_handoff_reference"]["trace"], "field_evidence_material_resolution_review_handoff")
        self.assertEqual(artifact["pr5_thread"]["thread_id"], "PRRT_kwDOSWB9286CJ3tX")
        self.assertEqual(artifact["pr5_thread"]["state"], "unresolved")
        self.assertEqual(artifact["pr5_thread"]["material_state"], "hardware_material_pending")
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["safe_to_control"])

    def test_reviewer_ack_bridge_accepts_owner_response_intake_ready_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._reviewer_ack_summary("field-resolution-reviewer-ack-101"),
                self._accepted_response("field-resolution-reviewer-ack-101"),
                "field-resolution-reviewer-ack-101",
            )

        encoded = json.dumps(summary, ensure_ascii=False)
        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["owner_response_material_status"], "received_not_reviewed")
        self.assertEqual(artifact["source_capability"], reviewer_ack_followup.CAPABILITY)
        self.assertEqual(artifact["source_bridge"], gate.SOURCE_BRIDGE)
        self.assertEqual(artifact["previous_escalation_reference"]["bridge_status"], reviewer_ack_followup.ACCEPTED_FOR_OWNER_RESPONSE_INTAKE)
        self.assertIn("accepted_for_owner_response_intake_not_proven", encoded)
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(artifact["safe_to_control"])

    def test_reviewer_ack_robot_alias_and_wrapper_inputs_are_supported(self) -> None:
        robot_alias = self._reviewer_ack_summary(
            "field-resolution-reviewer-ack-102",
            schema=f"trashbot.{reviewer_ack_followup.ROBOT_ALIAS}.v1",
        )
        wrapper = {
            "field_evidence_material_resolution_reviewer_ack_followup_escalation_status": {
                "summary": self._reviewer_ack_summary("field-resolution-reviewer-ack-103")
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            alias_artifact, _alias_summary, _alias_exit = self._build(
                Path(tmp),
                robot_alias,
                self._accepted_response("field-resolution-reviewer-ack-102"),
                "field-resolution-reviewer-ack-102",
            )
        with tempfile.TemporaryDirectory() as tmp:
            wrapper_artifact, _wrapper_summary, _wrapper_exit = self._build(
                Path(tmp),
                wrapper,
                self._accepted_response("field-resolution-reviewer-ack-103"),
                "field-resolution-reviewer-ack-103",
            )

        self.assertEqual(alias_artifact["review_readiness"], gate.ACCEPTED_REVIEW_READINESS)
        self.assertEqual(wrapper_artifact["review_readiness"], gate.ACCEPTED_REVIEW_READINESS)
        self.assertEqual(alias_artifact["source_bridge"], gate.SOURCE_BRIDGE)
        self.assertEqual(wrapper_artifact["source_bridge"], gate.SOURCE_BRIDGE)

    def test_missing_owner_response_blocks_all_required_materials(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._followup_summary("field-resolution-owner-102"),
                None,
                "field-resolution-owner-102",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["owner_response_material_status"], "missing")
        self.assertEqual(artifact["review_readiness"], gate.MISSING_REVIEW_READINESS)
        self.assertEqual(len(artifact["missing_materials"]), len(gate.DEFAULT_REQUIRED_MATERIALS))
        self.assertEqual(artifact["accepted_materials"], [])
        self.assertIn("owner_response_json_not_provided", json.dumps(summary, ensure_ascii=False))
        self.assertFalse(summary["primary_actions_enabled"])

    def test_old_followup_source_path_remains_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, _summary, exit_code = self._build(
                Path(tmp),
                self._followup_summary("field-resolution-owner-legacy-101"),
                self._accepted_response("field-resolution-owner-legacy-101"),
                "field-resolution-owner-legacy-101",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["source_capability"], followup.CAPABILITY)
        self.assertEqual(artifact["source_bridge"], "field_evidence_material_resolution_followup_owner_response_intake_legacy_path")
        self.assertEqual(artifact["review_readiness"], gate.ACCEPTED_REVIEW_READINESS)

    def test_partial_response_reports_accepted_missing_rejected_and_unsafe_categories(self) -> None:
        response = self._accepted_response("field-resolution-owner-103")
        materials = response["materials"]
        self.assertIsInstance(materials, dict)
        materials["real terminal delivery/dropoff/cancel result material"] = {
            "status": "missing",
            "safe_evidence_ref": "field-resolution-owner-103",
        }
        materials["true phone/browser evidence"] = {
            "status": "rejected",
            "safe_evidence_ref": "field-resolution-owner-103",
        }
        materials["real hardware/HIL evidence"] = {
            "status": "unsafe",
            "safe_evidence_ref": "field-resolution-owner-103",
        }

        with tempfile.TemporaryDirectory() as tmp:
            artifact, _summary, _exit_code = self._build(
                Path(tmp),
                self._followup_summary("field-resolution-owner-103"),
                response,
                "field-resolution-owner-103",
            )

        self.assertEqual(artifact["owner_response_material_status"], "rejected_not_proven")
        self.assertEqual(artifact["review_readiness"], gate.REJECTED_REVIEW_READINESS)
        self.assertEqual(len(artifact["accepted_materials"]), len(gate.DEFAULT_REQUIRED_MATERIALS) - 3)
        self.assertIn("real terminal delivery/dropoff/cancel result material", artifact["missing_materials"])
        self.assertIn("true phone/browser evidence", artifact["rejected_materials"])
        self.assertIn("real hardware/HIL evidence", artifact["unsafe_materials"])

    def test_ref_mismatch_unsafe_claims_and_bad_source_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mismatch, _, _ = self._build(
                Path(tmp),
                self._followup_summary("field-resolution-owner-104"),
                self._accepted_response("field-resolution-owner-104"),
                "other-ref",
            )

        with tempfile.TemporaryDirectory() as tmp:
            unsafe_response = self._accepted_response("field-resolution-owner-105")
            unsafe_response["materials"]["owner response material"]["summary"] = (
                "reviewer resolved and delivery_success=true /cmd_vel /dev/ttyUSB0"
            )
            unsafe, unsafe_summary, _ = self._build(
                Path(tmp),
                self._followup_summary("field-resolution-owner-105"),
                unsafe_response,
                "field-resolution-owner-105",
            )

        with tempfile.TemporaryDirectory() as tmp:
            bad_source, _, _ = self._build(
                Path(tmp),
                {"schema": followup.SUMMARY_SCHEMA, "safe_evidence_ref": "field-resolution-owner-106"},
                self._accepted_response("field-resolution-owner-106"),
                "field-resolution-owner-106",
            )

        encoded = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertEqual(mismatch["review_readiness"], gate.MISSING_REVIEW_READINESS)
        self.assertEqual(bad_source["review_readiness"], gate.MISSING_REVIEW_READINESS)
        self.assertEqual(unsafe["review_readiness"], gate.REJECTED_REVIEW_READINESS)
        self.assertEqual(unsafe["owner_response_material_status"], "rejected_not_proven")
        self.assertNotIn("delivery_success=true", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertFalse(unsafe["delivery_success"])

    def test_reviewer_ack_source_rejects_unsafe_status_and_missing_material(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            unsafe_status, unsafe_status_summary, _ = self._build(
                Path(tmp),
                self._reviewer_ack_summary(
                    "field-resolution-reviewer-ack-104",
                    reviewer_ack_followup.BLOCKED_UNSAFE_MATERIAL_CLAIMS,
                ),
                self._accepted_response("field-resolution-reviewer-ack-104"),
                "field-resolution-reviewer-ack-104",
            )
        with tempfile.TemporaryDirectory() as tmp:
            missing_material, _missing_summary, _ = self._build(
                Path(tmp),
                self._reviewer_ack_summary("field-resolution-reviewer-ack-105"),
                None,
                "field-resolution-reviewer-ack-105",
            )

        self.assertEqual(unsafe_status["review_readiness"], gate.MISSING_REVIEW_READINESS)
        self.assertIn("previous_escalation_status_not_safe_for_owner_response_intake", json.dumps(unsafe_status_summary, ensure_ascii=False))
        self.assertEqual(missing_material["owner_response_material_status"], "missing")
        self.assertEqual(missing_material["review_readiness"], gate.MISSING_REVIEW_READINESS)

    def test_cli_help_and_output_literals_are_stable(self) -> None:
        help_result = subprocess.run(
            [
                sys.executable,
                str(EVIDENCE_DIR / "field_evidence_material_resolution_owner_response_intake.py"),
                "--help",
            ],
            check=False,
            text=True,
            capture_output=True,
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._write_json(root, "followup.json", self._followup_summary("field-resolution-owner-107"))
            response = self._write_json(root, "response.json", self._accepted_response("field-resolution-owner-107"))
            run_result = subprocess.run(
                [
                    sys.executable,
                    str(EVIDENCE_DIR / "field_evidence_material_resolution_owner_response_intake.py"),
                    "--followup-summary-json",
                    str(source),
                    "--owner-response-json",
                    str(response),
                    "--evidence-ref",
                    "field-resolution-owner-107",
                    "--once-json",
                ],
                check=False,
                text=True,
                capture_output=True,
            )

        self.assertEqual(help_result.returncode, 0)
        self.assertIn("--followup-summary-json", help_result.stdout)
        self.assertEqual(run_result.returncode, 0)
        self.assertIn(gate.CAPABILITY, run_result.stdout)
        self.assertIn(gate.EVIDENCE_BOUNDARY, run_result.stdout)
        self.assertIn("accepted_materials", run_result.stdout)
        self.assertIn("missing_materials", run_result.stdout)
        self.assertIn("rejected_materials", run_result.stdout)
        self.assertIn("primary_actions_enabled", run_result.stdout)


if __name__ == "__main__":
    unittest.main()
