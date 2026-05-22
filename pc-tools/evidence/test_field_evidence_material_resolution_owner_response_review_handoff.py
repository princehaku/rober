#!/usr/bin/env python3
"""owner response review handoff gate 的离线围栏测试。"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools/evidence 不是常规包；测试显式加入目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_material_resolution_owner_response_review_decision as decision_gate  # noqa: E402
import field_evidence_material_resolution_owner_response_review_handoff as gate  # noqa: E402


# 测试约束 01：fixture 只表达上一轮 safe review-decision，不模拟 raw 现场材料。
# 测试约束 02：ready handoff 只表示 support/field owner/reviewer 可接手。
# 测试约束 03：needs-more handoff 必须保留 missing_required_materials。
# 测试约束 04：rejected/unsafe success/control/hardware copy 必须 fail closed。
# 测试约束 05：missing source 必须 blocked_missing_owner_response_intake_handoff_not_proven。
# 测试约束 06：Robot diagnostics safe alias 必须可消费。
# 测试约束 07：输出保持 source=software_proof 与 not_proven。
# 测试约束 08：输出保持 delivery_success=false。
# 测试约束 09：输出保持 primary_actions_enabled=false。
# 测试约束 10：输出保持 safe_to_control=false。
# 测试约束 11：测试不访问 ROS graph、Nav2、硬件、云或手机 runtime。


class FieldEvidenceMaterialResolutionOwnerResponseReviewHandoffTest(unittest.TestCase):
    def _write_json(self, root: Path, name: str, payload: object) -> Path:
        # 临时 JSON 只服务离线围栏，不代表真实外部或现场材料。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _decision_summary(
        self,
        evidence_ref: str,
        review_decision: str = decision_gate.ACCEPTED,
    ) -> dict[str, object]:
        # source 使用上一轮 owner-response review-decision summary 的安全消费面。
        missing = ["owner route evidence memo"] if review_decision == decision_gate.NEEDS_MORE else []
        rejected = ["unsafe owner success claim"] if review_decision == decision_gate.REJECTED_UNSAFE else []
        accepted = ["owner response material summary"] if review_decision == decision_gate.ACCEPTED else []
        return {
            "schema": decision_gate.SUMMARY_SCHEMA,
            "schema_version": 1,
            "source": "software_proof",
            "status": "not_proven",
            "capability": decision_gate.CAPABILITY,
            "review_decision": review_decision,
            "field_evidence_material_resolution_owner_response_review_decision": review_decision,
            "evidence_boundary": decision_gate.EVIDENCE_BOUNDARY,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "accepted_materials": accepted,
            "missing_materials": missing,
            "rejected_materials": rejected,
            "unsafe_materials": [],
            "decision_reasons": ["owner response review decision fixture"],
            "next_required_evidence": missing or [
                "field owner and reviewer inspect sanitized owner-response material later"
            ],
            "not_proven": ["not_proven"],
            "not_proven_items": ["real_material_review_completion"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_copy": (
                f"{decision_gate.CAPABILITY}: review_decision={review_decision}; evidence_ref={evidence_ref}; "
                "source=software_proof; not_proven; delivery_success=false; "
                "primary_actions_enabled=false; safe_to_control=false."
            ),
        }

    def _build(self, root: Path, payload: dict[str, object]) -> tuple[dict[str, object], dict[str, object], int]:
        # 公共 helper 让 case 聚焦四态映射和安全边界。
        source_path = self._write_json(root, "owner_response_review_decision.json", payload)
        return gate.build_field_evidence_material_resolution_owner_response_review_handoff(str(source_path))

    def test_accepted_review_decision_maps_to_ready_material_review_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(Path(tmp), self._decision_summary("owner-response-handoff-901"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], gate.SCHEMA)
        self.assertEqual(summary["schema"], gate.SUMMARY_SCHEMA)
        self.assertEqual(artifact["handoff_status"], gate.HANDOFF_READY)
        self.assertEqual(summary["summary_alias"], gate.ROBOT_ALIAS)
        self.assertEqual(artifact["source_review_decision"], decision_gate.ACCEPTED)
        self.assertEqual(artifact["evidence_boundary"], gate.EVIDENCE_BOUNDARY)
        self.assertEqual(artifact["field_owner_handoff"]["role"], "field owner")
        self.assertEqual(summary["support_handoff"]["role"], "support")
        self.assertEqual(summary["reviewer_handoff"]["role"], "reviewer")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(artifact["safe_to_control"])

    def test_needs_more_review_decision_preserves_missing_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._decision_summary("owner-response-handoff-902", decision_gate.NEEDS_MORE),
            )

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["handoff_status"], gate.HANDOFF_NEEDS_MORE)
        self.assertIn("owner_response_review_decision_requires_more_evidence", artifact["handoff_reasons"])
        self.assertEqual(summary["missing_required_materials"], ["owner route evidence memo"])
        self.assertIn("owner route evidence memo", summary["field_owner_handoff"]["next_required_evidence"])

    def test_rejected_and_unsafe_review_decision_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rejected, _, rejected_exit = self._build(
                Path(tmp),
                self._decision_summary("owner-response-handoff-903", decision_gate.REJECTED_UNSAFE),
            )
        with tempfile.TemporaryDirectory() as tmp:
            payload = self._decision_summary("owner-response-handoff-904")
            payload["safe_note"] = "delivery_success=true"
            unsafe, unsafe_summary, unsafe_exit = self._build(Path(tmp), payload)

        encoded = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertEqual(rejected_exit, 2)
        self.assertEqual(unsafe_exit, 2)
        self.assertEqual(rejected["handoff_status"], gate.HANDOFF_REJECTED)
        self.assertEqual(unsafe["handoff_status"], gate.HANDOFF_REJECTED)
        self.assertIn("delivery_success_true_overclaim", unsafe["handoff_reasons"])
        self.assertFalse(unsafe_summary["proof_flags"]["delivery_success"])
        self.assertNotIn("delivery_success=true", encoded)

    def test_missing_review_decision_maps_to_blocked_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = gate.build_field_evidence_material_resolution_owner_response_review_handoff(
                str(Path(tmp) / "missing-owner-response-review-decision.json")
            )

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["handoff_status"], gate.HANDOFF_BLOCKED)
        self.assertIn("owner_response_review_decision_input_missing", artifact["handoff_reasons"])
        self.assertEqual(summary["safe_evidence_ref"], "")
        self.assertFalse(summary["primary_actions_enabled"])

    def test_robot_alias_wrapper_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = {decision_gate.ROBOT_ALIAS: self._decision_summary("owner-response-handoff-905")}
            artifact, summary, exit_code = self._build(Path(tmp), payload)

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["handoff_status"], gate.HANDOFF_READY)
        self.assertEqual(artifact["safe_evidence_ref"], "owner-response-handoff-905")
        self.assertEqual(summary["source_schema"], decision_gate.SUMMARY_SCHEMA)

    def test_cli_prints_ready_handoff_for_safe_review_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_path = self._write_json(root, "review_decision.json", self._decision_summary("owner-response-handoff-906"))
            result = subprocess.run(
                [
                    sys.executable,
                    str(EVIDENCE_DIR / "field_evidence_material_resolution_owner_response_review_handoff.py"),
                    "--input",
                    str(source_path),
                ],
                check=False,
                text=True,
                capture_output=True,
            )

        self.assertEqual(result.returncode, 0)
        self.assertIn(gate.HANDOFF_READY, result.stdout)
        self.assertIn("software_proof_docker_field_evidence_material_resolution_owner_response_review_handoff_gate", result.stdout)

    def test_output_preserves_required_boundary_literals_and_no_raw_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, _ = self._build(Path(tmp), self._decision_summary("owner-response-handoff-907"))

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertIn("field_evidence_material_resolution_owner_response_review_handoff", encoded)
        self.assertIn("software_proof_docker_field_evidence_material_resolution_owner_response_review_handoff_gate", encoded)
        self.assertIn("safe_to_control=false", encoded)
        self.assertIn("delivery_success=false", encoded)
        self.assertIn("primary_actions_enabled=false", encoded)
        self.assertIn(gate.HANDOFF_NEEDS_MORE, encoded)
        self.assertIn(gate.HANDOFF_REJECTED, encoded)
        self.assertIn(gate.HANDOFF_BLOCKED, encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("Traceback", encoded)
        self.assertNotIn("raw artifact", encoded)


if __name__ == "__main__":
    unittest.main()
