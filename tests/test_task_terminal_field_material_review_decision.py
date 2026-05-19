#!/usr/bin/env python3
"""task terminal field material review decision gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools 不是 Python package；测试显式加入 evidence 目录，保证 CLI 与单测同源。
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "pc-tools" / "evidence"
sys.path.insert(0, str(EVIDENCE_DIR))

import task_terminal_field_material_review_decision as gate  # noqa: E402


# 测试约束 01：fixture 只表达 sanitized intake summary，不创建真实材料目录。
# 测试约束 02：ready case 只能证明 owner handoff readiness，不证明 field pass。
# 测试约束 03：missing case 必须保持 delivery_success=false。
# 测试约束 04：missing case 必须保持 primary_actions_enabled=false。
# 测试约束 05：missing case 必须保持 safe_to_control=false。
# 测试约束 06：unsupported schema 不能包装成可复核材料。
# 测试约束 07：evidence_ref mismatch 不能静默覆盖 source。
# 测试约束 08：rejected materials 必须进入 unsafe blocked。
# 测试约束 09：raw path、checksum、runtime topic 必须被阻断。
# 测试约束 10：成功/控制 true 旗标必须被阻断。
# 测试约束 11：Robot safe alias schema 作为兼容输入被支持。
# 测试约束 12：测试不访问 ROS graph、Nav2、硬件、外部云或手机 runtime。


class TaskTerminalFieldMaterialReviewDecisionTest(unittest.TestCase):
    def _write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 只写临时 JSON，验证文件型 gate 可离线复跑。
        path = root / name
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def _intake_summary(
        self,
        evidence_ref: str = "terminal-field-material-review-001",
        missing: list[str] | None = None,
        accepted: list[str] | None = None,
        **extra: object,
    ) -> dict[str, object]:
        # fixture 保持上一轮 Robot safe alias 字段形状，避免测试依赖 raw artifact。
        payload: dict[str, object] = {
            "schema": "trashbot.task_terminal_field_material_intake_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_task_terminal_field_material_intake_gate",
            "status": "blocked_missing_field_materials" if missing is not None else "ready_for_review_not_proven",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "accepted_safe_refs": accepted if accepted is not None else ["safe-task-record-ref"],
            "returned_materials": accepted if accepted is not None else ["safe-task-record-ref"],
            "missing_materials": missing if missing is not None else [],
            "rejected_materials": [],
            "next_required_evidence": [
                "同一 safe evidence_ref 的真实 task record",
                "真实 route/elevator field materials",
            ],
            "phone_safe_copy": (
                "现场材料复核入口；software_proof；not_proven；"
                "delivery_success=false；primary_actions_enabled=false；safe_to_control=false。"
            ),
            "evidence_boundary_flags": [
                "software_proof",
                "not_proven",
                "delivery_success=false",
                "primary_actions_enabled=false",
                "safe_to_control=false",
            ],
            "not_proven": ["real_route_elevator_field_pass", "real_phone_device_or_browser"],
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_to_control": False,
        }
        payload.update(extra)
        return payload

    def _build(self, root: Path, payload: dict, evidence_ref: str = "") -> tuple[dict, dict, int]:
        # 公共 helper 让测试关注状态映射，而不是文件读写样板。
        path = self._write_json(root, "intake.json", payload)
        return gate.build_review_decision(str(path), evidence_ref)

    def test_ready_returned_materials_become_owner_handoff_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact, summary, exit_code = self._build(root, self._intake_summary())

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.task_terminal_field_material_review_decision.v1")
        self.assertEqual(summary["schema"], "trashbot.task_terminal_field_material_review_decision_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_task_terminal_field_material_review_decision_gate",
        )
        self.assertEqual(artifact["review_decision"], "ready_for_owner_handoff_not_proven")
        self.assertEqual(summary["summary_alias"], "robot_diagnostics_task_terminal_field_material_review_decision_summary")
        self.assertIn("safe-task-record-ref", artifact["accepted_materials"])
        self.assertEqual(artifact["missing_materials"], [])
        self.assertEqual(artifact["rejected_materials"], [])
        self.assertIn("Product Manager / OKR Owner", artifact["owner_handoff"])
        self.assertIn("rerun_guidance", artifact)
        self.assertIn("not_proven", artifact)
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(artifact["safe_to_control"])

    def test_missing_materials_need_required_material_backfill(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact, summary, exit_code = self._build(
                root,
                self._intake_summary(
                    missing=[
                        "real_task_record",
                        "real_dropoff_or_cancel_terminal_material",
                        "real_route_elevator_field_material",
                        "real_phone_browser_evidence",
                    ]
                ),
            )

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["review_decision"], "needs_required_material_backfill_not_proven")
        self.assertIn("real_task_record", artifact["missing_materials"])
        self.assertIn("real_route_elevator_field_material", artifact["blocked_materials"])
        self.assertIn("Robot Platform Engineer", summary["owner_handoff"])
        self.assertIn("Autonomy Algorithm Engineer", summary["owner_handoff"])
        self.assertIn("User Touchpoint Full-Stack Engineer", summary["owner_handoff"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])

    def test_rejected_unsafe_and_success_claims_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rejected_artifact, _, rejected_exit = self._build(
                root,
                self._intake_summary(rejected_materials=["operator_note_rejected"]),
            )
            unsafe = self._intake_summary()
            unsafe["operator_note"] = "raw artifact /Users/m4/private.log /cmd_vel checksum=abcdef123456"
            unsafe_artifact, unsafe_summary, unsafe_exit = self._build(root, unsafe)
            success_artifact, _, success_exit = self._build(
                root,
                self._intake_summary(delivery_success=True),
            )

        self.assertEqual(rejected_exit, 2)
        self.assertEqual(unsafe_exit, 2)
        self.assertEqual(success_exit, 2)
        self.assertEqual(rejected_artifact["review_decision"], "blocked_rejected_or_unsafe_materials_not_proven")
        self.assertEqual(unsafe_artifact["review_decision"], "blocked_rejected_or_unsafe_materials_not_proven")
        self.assertEqual(success_artifact["review_decision"], "blocked_rejected_or_unsafe_materials_not_proven")
        encoded_summary = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)
        self.assertNotIn("abcdef123456", encoded_summary)

    def test_evidence_ref_mismatch_and_unsupported_input_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            mismatch_artifact, _, mismatch_exit = self._build(
                root,
                self._intake_summary("source-ref"),
                "expected-ref",
            )
            unsupported = self._intake_summary()
            unsupported["schema"] = "trashbot.unsupported.v1"
            unsupported_artifact, _, unsupported_exit = self._build(root, unsupported)
            missing_artifact, _, missing_exit = gate.build_review_decision(str(root / "missing.json"))

        self.assertEqual(mismatch_exit, 2)
        self.assertEqual(unsupported_exit, 2)
        self.assertEqual(missing_exit, 2)
        self.assertEqual(mismatch_artifact["review_decision"], "blocked_evidence_ref_mismatch_not_proven")
        self.assertEqual(unsupported_artifact["review_decision"], "blocked_missing_or_unsupported_intake_not_proven")
        self.assertEqual(missing_artifact["review_decision"], "blocked_missing_or_unsupported_intake_not_proven")

    def test_robot_safe_alias_and_nested_wrapper_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            nested = {
                "schema": "trashbot.task_terminal_field_material_intake.v1",
                "evidence_boundary": "software_proof_docker_task_terminal_field_material_intake_gate",
                "task_terminal_field_material_intake_summary": self._intake_summary(
                    "nested-ref",
                    accepted=["safe-nested-ref"],
                ),
            }
            alias = self._intake_summary("alias-ref", accepted=["safe-alias-ref"])
            alias["schema"] = "trashbot.robot_diagnostics_task_terminal_field_material_intake_summary.v1"
            nested_artifact, _, nested_exit = self._build(root, nested)
            alias_artifact, _, alias_exit = self._build(root, alias)

        self.assertEqual(nested_exit, 0)
        self.assertEqual(alias_exit, 0)
        self.assertEqual(nested_artifact["safe_evidence_ref"], "nested-ref")
        self.assertIn("safe-nested-ref", nested_artifact["accepted_materials"])
        self.assertEqual(alias_artifact["safe_evidence_ref"], "alias-ref")
        self.assertIn("safe-alias-ref", alias_artifact["accepted_materials"])


if __name__ == "__main__":
    unittest.main()
