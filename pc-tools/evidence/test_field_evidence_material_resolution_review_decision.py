#!/usr/bin/env python3
"""field_evidence_material_resolution_review_decision gate 的围栏测试。"""

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

import field_evidence_material_resolution_intake as intake_gate  # noqa: E402
import field_evidence_material_resolution_review_decision as gate  # noqa: E402


# 测试约束 01：fixture 只表达上一轮 safe intake，不模拟 raw 现场材料。
# 测试约束 02：accepted 只表示 owner review 入口，不代表真实 delivery success。
# 测试约束 03：missing intake 必须 blocked_missing_resolution_intake_not_proven。
# 测试约束 04：缺补证材料必须 needs_more_evidence_not_proven。
# 测试约束 05：unsafe success/control/hardware copy 必须 rejected。
# 测试约束 06：输出保持 source=software_proof 与 not_proven。
# 测试约束 07：输出保持 delivery_success=false。
# 测试约束 08：输出保持 primary_actions_enabled=false。
# 测试约束 09：输出保持 safe_to_control=false。
# 测试约束 10：测试不访问 ROS graph、Nav2、硬件、云或手机 runtime。


class FieldEvidenceMaterialResolutionReviewDecisionTest(unittest.TestCase):
    def _write_json(self, root: Path, name: str, payload: object) -> Path:
        # 临时 JSON 只服务离线围栏，不代表真实外部材料。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _intake_summary(self, evidence_ref: str, decision: str = "accepted") -> dict[str, object]:
        # source 使用上一轮 resolution intake summary 的安全消费面。
        materials = {
            "accepted": ["owner safe resolution packet summary"] if decision == "accepted" else [],
            "missing": ["real terminal result material"] if decision == "missing" else [],
            "rejected": ["unsafe owner material"] if decision == "rejected" else [],
            "blocked": ["resolution source still blocked"] if decision == "blocked" else [],
        }
        return {
            "schema": intake_gate.SUMMARY_SCHEMA,
            "schema_version": 1,
            "source": "software_proof",
            "status": "not_proven",
            "capability": intake_gate.CAPABILITY,
            "field_evidence_material_resolution_intake_status": intake_gate.READY_STATUS,
            "decision": decision,
            "evidence_boundary": intake_gate.EVIDENCE_BOUNDARY,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "material_categories": materials,
            "next_required_evidence": materials["missing"],
            "not_proven": ["not_proven"],
            "not_proven_items": ["real_terminal_delivery_or_dropoff_or_cancel_result"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_copy": {
                "schema": f"{intake_gate.SUMMARY_SCHEMA}.safe_copy",
                "source": "software_proof",
                "status": "not_proven",
                "decision": decision,
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "same_evidence_ref_required": True,
                "evidence_boundary": intake_gate.EVIDENCE_BOUNDARY,
                "not_proven": "not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
        }

    def _build(self, root: Path, payload: dict[str, object]) -> tuple[dict[str, object], dict[str, object], int]:
        # 公共 helper 让 case 聚焦决策映射和安全边界。
        source_path = self._write_json(root, "intake.json", payload)
        return gate.build_field_evidence_material_resolution_review_decision(str(source_path))

    def test_accepted_intake_maps_to_owner_review_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(Path(tmp), self._intake_summary("field-resolution-review-701"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], gate.SCHEMA)
        self.assertEqual(summary["schema"], gate.SUMMARY_SCHEMA)
        self.assertEqual(artifact["decision"], gate.DECISION_ACCEPTED)
        self.assertEqual(summary["summary_alias"], gate.ROBOT_ALIAS)
        self.assertEqual(artifact["evidence_boundary"], gate.EVIDENCE_BOUNDARY)
        self.assertTrue(artifact["same_evidence_ref_required"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(artifact["safe_to_control"])

    def test_missing_required_material_maps_to_needs_more_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._intake_summary("field-resolution-review-702", "missing"),
            )

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["decision"], gate.DECISION_NEEDS_MORE)
        self.assertIn("source_intake_needs_more_resolution_evidence", artifact["decision_reasons"])
        self.assertEqual(summary["next_required_evidence"], ["real terminal result material"])

    def test_unsafe_intake_maps_to_rejected_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = self._intake_summary("field-resolution-review-703")
            payload["safe_note"] = "delivery_success=true"
            artifact, summary, exit_code = self._build(Path(tmp), payload)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["decision"], gate.DECISION_REJECTED)
        self.assertIn("delivery_success_true_overclaim", artifact["decision_reasons"])
        self.assertFalse(summary["fail_closed_flags"]["delivery_success"])

    def test_missing_intake_maps_to_blocked_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = gate.build_field_evidence_material_resolution_review_decision(
                str(Path(tmp) / "missing-intake.json")
            )

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["decision"], gate.DECISION_BLOCKED)
        self.assertIn("input_missing", artifact["decision_reasons"])
        self.assertEqual(summary["safe_evidence_ref"], "")

    def test_robot_alias_wrapper_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = {intake_gate.ROBOT_ALIAS: self._intake_summary("field-resolution-review-704")}
            artifact, _, _ = self._build(Path(tmp), payload)

        self.assertEqual(artifact["decision"], gate.DECISION_ACCEPTED)
        self.assertEqual(artifact["safe_evidence_ref"], "field-resolution-review-704")

    def test_cli_prints_accepted_decision_for_safe_intake(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_path = self._write_json(root, "intake.json", self._intake_summary("field-resolution-review-705"))
            result = subprocess.run(
                [
                    sys.executable,
                    str(EVIDENCE_DIR / "field_evidence_material_resolution_review_decision.py"),
                    "--input",
                    str(source_path),
                ],
                check=False,
                text=True,
                capture_output=True,
            )

        self.assertEqual(result.returncode, 0)
        self.assertIn(gate.DECISION_ACCEPTED, result.stdout)
        self.assertIn("software_proof_docker_field_evidence_material_resolution_review_decision_gate", result.stdout)

    def test_output_preserves_required_boundary_literals_and_no_raw_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, _ = self._build(Path(tmp), self._intake_summary("field-resolution-review-706"))

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertIn("field_evidence_material_resolution_review_decision", encoded)
        self.assertIn("software_proof_docker_field_evidence_material_resolution_review_decision_gate", encoded)
        self.assertIn("accepted_for_owner_review_not_proven", encoded)
        self.assertIn("needs_more_evidence_not_proven", encoded)
        self.assertIn("rejected_unsafe_resolution_not_proven", encoded)
        self.assertIn("blocked_missing_resolution_intake_not_proven", encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("delivery_success=false", encoded)
        self.assertIn("primary_actions_enabled=false", encoded)
        self.assertIn("safe_to_control=false", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("Traceback", encoded)
        self.assertNotIn("raw artifact", encoded)


if __name__ == "__main__":
    unittest.main()
