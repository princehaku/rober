#!/usr/bin/env python3
"""field_evidence_material_resolution_followup_escalation_status gate 的围栏测试。"""

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

import field_evidence_material_resolution_followup_escalation_status as gate  # noqa: E402
import field_evidence_material_resolution_review_handoff as handoff_gate  # noqa: E402


# 测试约束 01：fixture 只表达上一轮 safe handoff，不模拟真实 owner material。
# 测试约束 02：sent handoff 只可生成 pending/overdue/escalated，不代表完成。
# 测试约束 03：lineage 必须保留 43a3f01 与 a384c84。
# 测试约束 04：PR #5 thread X 必须保持 unresolved / hardware_material_pending。
# 测试约束 05：comment 3269642220 只能是 software-proof reply。
# 测试约束 06：missing source 必须 blocked。
# 测试约束 07：unsupported schema/boundary 必须 blocked。
# 测试约束 08：success/control/resolution/raw/hardware claim 必须 fail closed。
# 测试约束 09：输出保持 source=software_proof 与 not_proven。
# 测试约束 10：输出保持 delivery_success=false。
# 测试约束 11：输出保持 primary_actions_enabled=false。
# 测试约束 12：输出保持 safe_to_control=false。


class FieldEvidenceMaterialResolutionFollowupEscalationStatusTest(unittest.TestCase):
    def _write_json(self, root: Path, name: str, payload: object) -> Path:
        # 临时 JSON 只服务离线围栏，不代表真实外部、现场或硬件材料。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _handoff_summary(
        self,
        evidence_ref: str,
        handoff_status: str = handoff_gate.HANDOFF_READY,
    ) -> dict[str, object]:
        # source 使用上一轮 review-handoff summary 的安全消费面。
        return {
            "schema": handoff_gate.SUMMARY_SCHEMA,
            "schema_version": 1,
            "source": "software_proof",
            "status": "not_proven",
            "capability": handoff_gate.CAPABILITY,
            "handoff_status": handoff_status,
            "field_evidence_material_resolution_review_handoff": handoff_status,
            "evidence_boundary": handoff_gate.EVIDENCE_BOUNDARY,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "missing_required_materials": ["real terminal result material"],
            "next_required_evidence": [
                "Collect real external, terminal-result, phone/browser, field route/elevator, hardware/HIL, or PR #5 evidence before any completion claim."
            ],
            "owner_handoff": {
                "role": "Product Manager / OKR Owner",
                "owner_next_action": "review_sanitized_resolution_handoff_without_marking_delivery_or_pr5_resolved",
                "safe_evidence_ref": evidence_ref,
                "not_delivery_success": True,
                "not_pr5_resolution": True,
                "safe_to_control": False,
                "primary_actions_enabled": False,
            },
            "not_proven": ["not_proven"],
            "not_proven_items": ["delivery_success"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_copy": (
                f"{handoff_gate.CAPABILITY}: handoff_status={handoff_status}; evidence_ref={evidence_ref}; "
                "source=software_proof; not_proven; delivery_success=false; "
                "primary_actions_enabled=false; safe_to_control=false."
            ),
        }

    def _build(
        self,
        root: Path,
        payload: dict[str, object],
        due_status: str = "escalated",
    ) -> tuple[dict[str, object], dict[str, object], int]:
        # 公共 helper 让 case 聚焦 followup 映射和安全边界。
        source_path = self._write_json(root, "review_handoff.json", payload)
        return gate.build_field_evidence_material_resolution_followup_escalation_status(str(source_path), due_status)

    def test_ready_handoff_maps_to_escalated_owner_response_material_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(Path(tmp), self._handoff_summary("field-resolution-followup-901"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], gate.SCHEMA)
        self.assertEqual(summary["schema"], gate.SUMMARY_SCHEMA)
        self.assertEqual(artifact["capability"], gate.CAPABILITY)
        self.assertEqual(artifact["followup_status"], gate.ESCALATED_STATUS)
        self.assertEqual(artifact["owner_response_material_status"], "missing")
        self.assertEqual(artifact["due_status"], "escalated")
        self.assertEqual(artifact["lineage"]["previous_handoff"], "43a3f01")
        self.assertEqual(artifact["lineage"]["previous_review_decision"], "a384c84")
        self.assertEqual(artifact["pr5_thread"]["thread_id"], "PRRT_kwDOSWB9286CJ3tX")
        self.assertEqual(artifact["pr5_thread"]["comment_id"], "3269642220")
        self.assertEqual(artifact["pr5_thread"]["state"], "unresolved")
        self.assertEqual(artifact["pr5_thread"]["material_state"], "hardware_material_pending")
        self.assertIn("owner response material", summary["next_required_evidence"])
        self.assertTrue(summary["owner_escalation"]["escalate"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(artifact["safe_to_control"])

    def test_due_status_can_remain_pending_or_overdue_without_success_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pending, _, pending_exit = self._build(
                Path(tmp),
                self._handoff_summary("field-resolution-followup-902"),
                "pending",
            )
        with tempfile.TemporaryDirectory() as tmp:
            overdue, _, overdue_exit = self._build(
                Path(tmp),
                self._handoff_summary("field-resolution-followup-903"),
                "overdue",
            )

        self.assertEqual(pending_exit, 0)
        self.assertEqual(overdue_exit, 0)
        self.assertEqual(pending["followup_status"], gate.PENDING_STATUS)
        self.assertEqual(overdue["followup_status"], gate.OVERDUE_STATUS)
        self.assertEqual(pending["owner_response_material_status"], "missing")
        self.assertEqual(overdue["owner_response_material_status"], "missing")
        self.assertFalse(pending["delivery_success"])
        self.assertFalse(overdue["primary_actions_enabled"])

    def test_robot_alias_wrapper_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = {handoff_gate.ROBOT_ALIAS: self._handoff_summary("field-resolution-followup-904")}
            artifact, summary, exit_code = self._build(Path(tmp), payload)

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["safe_evidence_ref"], "field-resolution-followup-904")
        self.assertEqual(summary["source_schema"], handoff_gate.SUMMARY_SCHEMA)
        self.assertEqual(summary["summary_alias"], gate.ROBOT_ALIAS)

    def test_missing_unsupported_nonready_or_unsafe_handoff_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing, _, missing_exit = gate.build_field_evidence_material_resolution_followup_escalation_status(
                str(Path(tmp) / "missing-review-handoff.json")
            )
        with tempfile.TemporaryDirectory() as tmp:
            unsupported, _, unsupported_exit = self._build(
                Path(tmp),
                {"schema": "trashbot.unsupported.v1", "evidence_ref": "field-resolution-followup-905"},
            )
        with tempfile.TemporaryDirectory() as tmp:
            nonready, _, nonready_exit = self._build(
                Path(tmp),
                self._handoff_summary("field-resolution-followup-906", handoff_gate.HANDOFF_BACKFILL),
            )
        with tempfile.TemporaryDirectory() as tmp:
            payload = self._handoff_summary("field-resolution-followup-907")
            payload["safe_note"] = "reviewer resolved and delivery_success=true"
            unsafe, unsafe_summary, unsafe_exit = self._build(Path(tmp), payload)

        encoded = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertEqual(missing_exit, 2)
        self.assertEqual(unsupported_exit, 2)
        self.assertEqual(nonready_exit, 2)
        self.assertEqual(unsafe_exit, 2)
        self.assertEqual(missing["followup_status"], gate.BLOCKED_STATUS)
        self.assertEqual(unsupported["followup_status"], gate.BLOCKED_STATUS)
        self.assertEqual(nonready["followup_status"], gate.BLOCKED_STATUS)
        self.assertEqual(unsafe["followup_status"], gate.BLOCKED_STATUS)
        self.assertFalse(unsafe_summary["fail_closed_flags"]["safe_to_control"])
        self.assertNotIn("delivery_success=true", encoded)
        self.assertNotIn("reviewer resolved", encoded)

    def test_cli_prints_escalated_summary_for_safe_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_path = self._write_json(root, "review_handoff.json", self._handoff_summary("field-resolution-followup-908"))
            result = subprocess.run(
                [
                    sys.executable,
                    str(EVIDENCE_DIR / "field_evidence_material_resolution_followup_escalation_status.py"),
                    "--input",
                    str(source_path),
                ],
                check=False,
                text=True,
                capture_output=True,
            )

        self.assertEqual(result.returncode, 0)
        self.assertIn(gate.ESCALATED_STATUS, result.stdout)
        self.assertIn("owner response material", result.stdout)
        self.assertIn("software_proof_docker_field_evidence_material_resolution_followup_escalation_status_gate", result.stdout)

    def test_output_preserves_required_literals_and_no_raw_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, _ = self._build(Path(tmp), self._handoff_summary("field-resolution-followup-909"))

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertIn("field_evidence_material_resolution_followup_escalation_status", encoded)
        self.assertIn("software_proof_docker_field_evidence_material_resolution_followup_escalation_status_gate", encoded)
        self.assertIn("owner response material", encoded)
        self.assertIn("escalate", encoded)
        self.assertIn("43a3f01", encoded)
        self.assertIn("a384c84", encoded)
        self.assertIn("PRRT_kwDOSWB9286CJ3tX", encoded)
        self.assertIn("3269642220", encoded)
        self.assertIn("delivery_success=false", encoded)
        self.assertIn("primary_actions_enabled=false", encoded)
        self.assertIn("safe_to_control=false", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("Traceback", encoded)
        self.assertNotIn("raw artifact", encoded)


if __name__ == "__main__":
    unittest.main()
