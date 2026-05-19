#!/usr/bin/env python3
"""real_material_followup_escalation_status gate 的离线围栏测试。"""

from __future__ import annotations

# 测试约束 01：默认输出必须是 software_proof follow-up status，不证明真实材料。
# 测试约束 02：四类 material group 必须全部输出，并都带 due_status / escalation_level。
# 测试约束 03：O1 / PR #5 必须保留 PRRT_kwDOSWB9286CJ3tX 与 blocked_pending_real_materials。
# 测试约束 04：mandatory sensor baseline 必须要求 docs/vendor/VENDOR_INDEX.md citation。
# 测试约束 05：summary 只能携带安全追责字段，不能携带 success/control claim。
# 测试约束 06：缺 vendor index 必须 fail closed。
# 测试约束 07：不安全 evidence_ref 必须 fail closed。
# 测试约束 08：CLI 必须写出 artifact 和 summary。
# 测试约束 09：所有输出必须保持 delivery_success=false。
# 测试约束 10：所有输出必须保持 primary_actions_enabled=false 和 safe_to_control=false。

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "pc-tools" / "evidence" / "real_material_followup_escalation_status.py"
SPEC = importlib.util.spec_from_file_location("real_material_followup_escalation_status", SCRIPT)
gate = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(gate)


class RealMaterialFollowupEscalationStatusTest(unittest.TestCase):
    def test_default_output_tracks_all_groups_and_stays_not_proven(self):
        artifact, summary, exit_code = gate.build_real_material_followup_escalation_status()
        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        group_ids = {group["material_group"] for group in artifact["material_groups"]}

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.real_material_followup_escalation_status.v1")
        self.assertEqual(summary["schema"], "trashbot.real_material_followup_escalation_status_summary.v1")
        self.assertEqual(artifact["real_material_followup_escalation_status"], "blocked_pending_real_materials")
        self.assertEqual(summary["real_material_followup_escalation_status"], "blocked_pending_real_materials")
        self.assertEqual(group_ids, {"o5_external", "o1_pr5_hardware", "pr4_route_elevator", "o4_real_phone"})
        self.assertIn("Objective 5", encoded)
        self.assertIn("Objective 1", encoded)
        self.assertIn("Objective 4", encoded)
        self.assertIn("software_proof_docker_real_material_followup_escalation_status_gate", encoded)
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(artifact["safe_to_control"])
        self.assertFalse(summary["safe_to_control"])

    def test_group_contract_exposes_due_blocker_evidence_and_rerun_fields(self):
        artifact, summary, _ = gate.build_real_material_followup_escalation_status()
        for group in artifact["material_groups"]:
            self.assertEqual(group["due_status"], "overdue_pending_real_materials")
            self.assertTrue(group["blocked_reason"])
            self.assertTrue(group["next_required_evidence"])
            self.assertTrue(group["escalation_level"])
            self.assertIn("real_material_evidence_intake.py", group["rerun_command"])
            self.assertEqual(group["source_template_status"], "ready_for_field_owner_submission_pack_not_proven")
            self.assertEqual(group["source_intake_status"], "blocked_missing_real_material_items")
            self.assertFalse(group["delivery_success"])
            self.assertFalse(group["primary_actions_enabled"])
            self.assertFalse(group["safe_to_control"])
        for group in summary["material_groups"]:
            self.assertIn("due_status", group)
            self.assertIn("blocked_reason", group)
            self.assertIn("next_required_evidence", group)
            self.assertIn("escalation_level", group)

    def test_pr5_hardware_group_preserves_review_thread_and_vendor_citation(self):
        artifact, summary, _ = gate.build_real_material_followup_escalation_status()
        hardware = next(group for group in artifact["material_groups"] if group["material_group"] == "o1_pr5_hardware")
        encoded = json.dumps({"hardware": hardware, "summary": summary}, ensure_ascii=False)

        self.assertEqual(hardware["review_thread_id"], "PRRT_kwDOSWB9286CJ3tX")
        self.assertEqual(hardware["review_thread_state"], "blocked_pending_real_materials")
        self.assertIn("mandatory sensor baseline", encoded)
        self.assertIn("docs/vendor/VENDOR_INDEX.md", encoded)
        self.assertIn("2D LiDAR", encoded)
        self.assertIn("ToF", encoded)
        self.assertIn("WAVE ROVER", encoded)
        self.assertIn("feedback_T1001", encoded)
        self.assertFalse(hardware["delivery_success"])
        self.assertFalse(hardware["safe_to_control"])

    def test_missing_vendor_index_fails_closed_without_success_flags(self):
        with tempfile.TemporaryDirectory() as td:
            artifact, summary, exit_code = gate.build_real_material_followup_escalation_status(
                vendor_index=Path(td) / "missing_VENDOR_INDEX.md"
            )

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["real_material_followup_escalation_status"], "blocked_missing_vendor_index")
        self.assertFalse(artifact["vendor_source_boundary"]["vendor_index_exists"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])

    def test_unsafe_evidence_ref_fails_closed(self):
        artifact, summary, exit_code = gate.build_real_material_followup_escalation_status(evidence_ref="/tmp/token")

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["real_material_followup_escalation_status"], "blocked_unsafe_real_material_followup_evidence_ref")
        self.assertEqual(summary["safe_evidence_ref"], "")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["safe_to_control"])

    def test_cli_writes_artifact_and_summary(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact_path = root / "real_material_followup_escalation_status.json"
            summary_path = root / "real_material_followup_escalation_status_summary.json"
            exit_code = gate.main(["--output", str(artifact_path), "--summary-output", str(summary_path)])
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            summary = json.loads(summary_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["real_material_followup_escalation_status"], summary["real_material_followup_escalation_status"])
        self.assertEqual(summary["group_count"], 4)
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])


if __name__ == "__main__":
    unittest.main()
