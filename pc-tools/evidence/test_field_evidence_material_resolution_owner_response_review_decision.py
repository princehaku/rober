#!/usr/bin/env python3
"""field evidence material resolution owner response review decision gate 围栏测试。"""

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

import field_evidence_material_resolution_owner_response_intake as intake  # noqa: E402
import field_evidence_material_resolution_owner_response_review_decision as gate  # noqa: E402


# 测试约束 01：fixture 只表达上一轮 owner-response-intake safe summary。
# 测试约束 02：accepted 只表示 accepted_for_material_review_not_proven。
# 测试约束 03：missing material 映射 needs_more_evidence_not_proven。
# 测试约束 04：rejected/unsafe/success/control claim 映射 rejected unsafe。
# 测试约束 05：缺 intake source 映射 blocked_missing_owner_response_intake。
# 测试约束 06：同一 safe evidence_ref 是硬约束。
# 测试约束 07：PR #5 thread X 必须 unresolved / hardware_material_pending。
# 测试约束 08：输出保持 source=software_proof 与 not_proven。
# 测试约束 09：输出保持 primary_actions_enabled=false。
# 测试约束 10：输出保持 delivery_success=false。
# 测试约束 11：输出保持 safe_to_control=false。
# 测试约束 12：单测不访问 ROS graph、硬件、外部云或手机 runtime。


class FieldEvidenceMaterialResolutionOwnerResponseReviewDecisionTest(unittest.TestCase):
    def _write_json(self, root: Path, name: str, payload: object) -> Path:
        # 临时 JSON 只服务离线围栏，不模拟真实现场材料。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _intake_summary(
        self,
        evidence_ref: str,
        readiness: str = intake.ACCEPTED_REVIEW_READINESS,
        accepted: list[str] | None = None,
        missing: list[str] | None = None,
        rejected: list[str] | None = None,
        unsafe: list[str] | None = None,
        owner_status: str = "received_not_reviewed",
    ) -> dict[str, object]:
        # 样本沿用上一轮 intake summary 的安全消费面。
        accepted = accepted if accepted is not None else list(intake.DEFAULT_REQUIRED_MATERIALS)
        missing = missing or []
        rejected = rejected or []
        unsafe = unsafe or []
        return {
            "schema": intake.SUMMARY_SCHEMA,
            "schema_version": 1,
            "source": "software_proof",
            "status": "not_proven",
            "capability": intake.CAPABILITY,
            "evidence_boundary": intake.EVIDENCE_BOUNDARY,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "owner_response_material_status": owner_status,
            "review_readiness": readiness,
            "accepted_materials": accepted,
            "missing_materials": missing,
            "rejected_materials": rejected,
            "unsafe_materials": unsafe,
            "review_reasons": ["accepted_for_review_not_proven"],
            "previous_escalation_reference": {"capability": "field_evidence_material_resolution_followup_escalation_status"},
            "previous_handoff_reference": {"trace": "field_evidence_material_resolution_review_handoff"},
            "pr5_thread": {
                "thread_id": "PRRT_kwDOSWB9286CJ3tX",
                "state": "unresolved",
                "material_state": "hardware_material_pending",
            },
            "not_proven": ["not_proven"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_copy": {
                "schema": f"{intake.SUMMARY_SCHEMA}.safe_copy",
                "source": "software_proof",
                "status": "not_proven",
                "evidence_boundary": intake.EVIDENCE_BOUNDARY,
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "same_evidence_ref_required": True,
                "owner_response_material_status": owner_status,
                "review_readiness": readiness,
                "accepted_materials": accepted,
                "missing_materials": missing,
                "rejected_materials": rejected,
                "unsafe_materials": unsafe,
                "not_proven": "not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
        }

    def _build(
        self,
        root: Path,
        payload: dict[str, object],
        evidence_ref: str = "field-resolution-owner-review-101",
    ) -> tuple[dict[str, object], dict[str, object], int]:
        # 公共 helper 让 case 聚焦 decision 映射和 fail-closed 规则。
        source_path = self._write_json(root, "owner-response-intake.json", payload)
        return gate.build_field_evidence_material_resolution_owner_response_review_decision(str(source_path), evidence_ref)

    def test_received_owner_response_maps_to_accepted_for_material_review_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                {"payload": {"field_evidence_material_resolution_owner_response_intake_summary": self._intake_summary("field-resolution-owner-review-101")}},
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], gate.SCHEMA)
        self.assertEqual(summary["schema"], gate.SUMMARY_SCHEMA)
        self.assertEqual(artifact["capability"], gate.CAPABILITY)
        self.assertEqual(artifact["evidence_boundary"], gate.EVIDENCE_BOUNDARY)
        self.assertEqual(artifact["review_decision"], gate.ACCEPTED)
        self.assertEqual(len(artifact["accepted_materials"]), len(intake.DEFAULT_REQUIRED_MATERIALS))
        self.assertEqual(artifact["pr5_thread"]["state"], "unresolved")
        self.assertEqual(artifact["pr5_thread"]["material_state"], "hardware_material_pending")
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["safe_to_control"])
        self.assertIn("no OKR lift", artifact["owner_action"])

    def test_missing_owner_response_material_needs_more_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, _exit_code = self._build(
                Path(tmp),
                self._intake_summary(
                    "field-resolution-owner-review-102",
                    intake.MISSING_REVIEW_READINESS,
                    accepted=["owner response material"],
                    missing=["true phone/browser evidence"],
                    owner_status="missing",
                ),
                "field-resolution-owner-review-102",
            )

        self.assertEqual(artifact["review_decision"], gate.NEEDS_MORE)
        self.assertIn("true phone/browser evidence", artifact["missing_materials"])
        self.assertIn("backfill_missing_owner_response_material", json.dumps(summary, ensure_ascii=False))
        self.assertFalse(summary["primary_actions_enabled"])

    def test_rejected_unsafe_mismatch_and_success_claims_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rejected, _summary, _ = self._build(
                Path(tmp),
                self._intake_summary(
                    "field-resolution-owner-review-103",
                    intake.REJECTED_REVIEW_READINESS,
                    accepted=[],
                    rejected=["real hardware/HIL evidence"],
                    owner_status="rejected_not_proven",
                ),
                "field-resolution-owner-review-103",
            )
        with tempfile.TemporaryDirectory() as tmp:
            unsafe_source = self._intake_summary("field-resolution-owner-review-104")
            unsafe_source["safe_copy"]["operator_note"] = "delivery_success=true reviewer resolved /cmd_vel"
            unsafe, unsafe_summary, _ = self._build(Path(tmp), unsafe_source, "field-resolution-owner-review-104")
        with tempfile.TemporaryDirectory() as tmp:
            mismatch, _summary, _ = self._build(
                Path(tmp),
                self._intake_summary("field-resolution-owner-review-105"),
                "other-ref",
            )

        encoded = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertEqual(rejected["review_decision"], gate.REJECTED_UNSAFE)
        self.assertEqual(unsafe["review_decision"], gate.REJECTED_UNSAFE)
        self.assertEqual(mismatch["review_decision"], gate.REJECTED_UNSAFE)
        self.assertNotIn("delivery_success=true", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertFalse(unsafe["delivery_success"])

    def test_missing_bad_and_unsupported_intake_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing, missing_summary, _ = gate.build_field_evidence_material_resolution_owner_response_review_decision(
                str(root / "missing.json"),
                "field-resolution-owner-review-106",
            )
            unsupported, _summary, _ = self._build(
                root,
                {"schema": "trashbot.unsupported.v1", "evidence_ref": "field-resolution-owner-review-106"},
                "field-resolution-owner-review-106",
            )

        self.assertEqual(missing["review_decision"], gate.BLOCKED_MISSING_INTAKE)
        self.assertEqual(unsupported["review_decision"], gate.BLOCKED_MISSING_INTAKE)
        self.assertIn("owner_response_intake_json_missing", missing["decision_reasons"])
        self.assertFalse(missing_summary["safe_to_control"])

    def test_robot_diagnostics_alias_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            alias = {
                "latest_status": {
                    "diagnostics": {
                        intake.ROBOT_ALIAS: self._intake_summary("field-resolution-owner-review-107")
                    }
                }
            }
            artifact, summary, _exit_code = self._build(Path(tmp), alias, "field-resolution-owner-review-107")

        self.assertEqual(artifact["review_decision"], gate.ACCEPTED)
        self.assertEqual(summary["previous_intake_reference"]["capability"], intake.CAPABILITY)

    def test_cli_help_and_output_literals_are_stable(self) -> None:
        help_result = subprocess.run(
            [
                sys.executable,
                str(EVIDENCE_DIR / "field_evidence_material_resolution_owner_response_review_decision.py"),
                "--help",
            ],
            check=False,
            text=True,
            capture_output=True,
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._write_json(root, "intake.json", self._intake_summary("field-resolution-owner-review-108"))
            run_result = subprocess.run(
                [
                    sys.executable,
                    str(EVIDENCE_DIR / "field_evidence_material_resolution_owner_response_review_decision.py"),
                    "--owner-response-intake-json",
                    str(source),
                    "--evidence-ref",
                    "field-resolution-owner-review-108",
                    "--once-json",
                ],
                check=False,
                text=True,
                capture_output=True,
            )

        self.assertEqual(help_result.returncode, 0)
        self.assertIn("--owner-response-intake-json", help_result.stdout)
        self.assertEqual(run_result.returncode, 0)
        self.assertIn(gate.CAPABILITY, run_result.stdout)
        self.assertIn(gate.EVIDENCE_BOUNDARY, run_result.stdout)
        self.assertIn(gate.ACCEPTED, run_result.stdout)
        self.assertIn(gate.NEEDS_MORE, run_result.stdout)
        self.assertIn(gate.REJECTED_UNSAFE, run_result.stdout)
        self.assertIn(gate.BLOCKED_MISSING_INTAKE, run_result.stdout)
        self.assertIn("primary_actions_enabled", run_result.stdout)
        self.assertIn("delivery_success", run_result.stdout)
        self.assertIn("safe_to_control", run_result.stdout)

    def test_output_preserves_required_boundary_literals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, _exit_code = self._build(
                Path(tmp),
                self._intake_summary("field-resolution-owner-review-109"),
                "field-resolution-owner-review-109",
            )

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertIn("field_evidence_material_resolution_owner_response_review_decision", encoded)
        self.assertIn("software_proof_docker_field_evidence_material_resolution_owner_response_review_decision_gate", encoded)
        self.assertIn("owner response material", encoded)
        self.assertIn(gate.ACCEPTED, encoded)
        self.assertIn(gate.NEEDS_MORE, encoded)
        self.assertIn(gate.REJECTED_UNSAFE, encoded)
        self.assertIn(gate.BLOCKED_MISSING_INTAKE, encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("primary_actions_enabled=false", encoded)
        self.assertIn("delivery_success=false", encoded)
        self.assertIn("safe_to_control=false", encoded)
        self.assertNotIn("/dev/ttyUSB", encoded)
        self.assertNotIn("Traceback", encoded)


if __name__ == "__main__":
    unittest.main()
