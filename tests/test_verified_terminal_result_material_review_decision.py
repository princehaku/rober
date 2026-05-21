#!/usr/bin/env python3
"""verified_terminal_result_material_review_decision gate 的离线围栏测试。"""

from __future__ import annotations

# 测试约束 01：review decision 只处理上一轮 intake 的 safe summary。
# 测试约束 02：accepted_for_review 不是 delivery_success，也不打开主操作。
# 测试约束 03：delivery/dropoff/cancel 以外的 terminal_result_type 必须 blocked。
# 测试约束 04：same safe evidence_ref 不一致必须 blocked。
# 测试约束 05：missing materials 必须进入 needs_material_backfill。
# 测试约束 06：rejected materials 或 unsafe copy 必须进入 rejected。
# 测试约束 07：raw artifact、本机路径、凭证、ROS/control 和硬件细节不能泄漏输出。
# 测试约束 08：Robot safe alias 和常见 wrapper 形态必须被支持。

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "pc-tools" / "evidence" / "verified_terminal_result_material_review_decision.py"
SPEC = importlib.util.spec_from_file_location("verified_terminal_result_material_review_decision", SCRIPT)
gate = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(gate)


def _intake_summary(
    result_type: str = "delivery",
    evidence_ref: str = "terminal-review-2026-05-22T05-06Z",
    missing: list[str] | None = None,
    rejected: list[str] | None = None,
    **extra: object,
) -> dict[str, object]:
    # fixture 使用上一轮 summary contract，不创建真实 field material。
    payload: dict[str, object] = {
        "schema": "trashbot.verified_terminal_result_material_intake_summary.v1",
        "schema_version": 1,
        "capability": "verified_terminal_result_material_intake",
        "evidence_boundary": "software_proof_docker_verified_terminal_result_material_intake_gate",
        "source": "software_proof",
        "status": "not_proven",
        "verified_terminal_result_material_intake": "ready_for_terminal_result_manual_review_not_proven",
        "intake_status": "ready_for_terminal_result_manual_review_not_proven",
        "safe_evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "terminal_result_type": result_type,
        "accepted_materials": [
            "task_record",
            "nav2_fixed_route_runtime_log",
            "route_completion_signal",
            "delivery_result",
            "true_phone_browser_evidence",
        ],
        "missing_materials": [] if missing is None else missing,
        "rejected_materials": [] if rejected is None else rejected,
        "next_required_evidence": ["Product owner reviews safe terminal result materials."],
        "not_proven": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }
    payload.update(extra)
    return payload


class VerifiedTerminalResultMaterialReviewDecisionTest(unittest.TestCase):
    def _write_json(self, root: Path, payload: dict) -> Path:
        # 临时输入只服务离线 gate 测试，不会进入 artifact 的 raw source。
        path = root / "input.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def test_valid_intake_summary_becomes_accepted_for_review_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_path = self._write_json(root, _intake_summary())
            artifact, summary, exit_code = gate.build_verified_terminal_result_material_review_decision(input_path)

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], gate.ARTIFACT_SCHEMA)
        self.assertEqual(summary["schema"], gate.SUMMARY_SCHEMA)
        self.assertEqual(artifact["review_decision"], "accepted_for_review")
        self.assertEqual(summary["safe_evidence_ref"], "terminal-review-2026-05-22T05-06Z")
        self.assertEqual(summary["terminal_result_type"], "delivery")
        self.assertIn("owner_handoff", summary)
        self.assertIn("next_required_evidence", summary)
        self.assertIn("safe_copy", summary)
        self.assertIn("material_status_summary", summary)
        self.assertEqual(artifact["evidence_boundary"], gate.EVIDENCE_BOUNDARY)
        self.assertIn("software_proof_docker_verified_terminal_result_material_review_decision_gate", encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("delivery_success=false", encoded)
        self.assertIn("primary_actions_enabled=false", encoded)
        self.assertIn("safe_to_control=false", encoded)
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])

    def test_missing_materials_need_backfill_without_success_claim(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            input_path = self._write_json(
                Path(td),
                _intake_summary(missing=["delivery_result", "true_phone_browser_evidence"]),
            )
            artifact, summary, exit_code = gate.build_verified_terminal_result_material_review_decision(input_path)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["review_decision"], "needs_material_backfill")
        self.assertIn("delivery_result", summary["material_status_summary"]["missing_materials"])
        self.assertIn("Backfill same safe evidence_ref material: delivery_result", summary["next_required_evidence"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])

    def test_robot_safe_alias_and_nested_wrapper_are_supported(self) -> None:
        alias = _intake_summary("dropoff", "alias-terminal-result-ref")
        alias["schema"] = "robot_diagnostics_verified_terminal_result_material_intake_summary"
        nested = {
            "schema": "trashbot.verified_terminal_result_material_intake.v1",
            "verified_terminal_result_material_intake_summary": _intake_summary("cancel", "nested-terminal-result-ref"),
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            alias_artifact, _, alias_exit = gate.build_verified_terminal_result_material_review_decision(
                self._write_json(root, alias)
            )
            nested_artifact, nested_summary, nested_exit = gate.build_verified_terminal_result_material_review_decision(
                self._write_json(root, nested)
            )

        self.assertEqual(alias_exit, 0)
        self.assertEqual(nested_exit, 0)
        self.assertEqual(alias_artifact["terminal_result_type"], "dropoff")
        self.assertEqual(alias_artifact["safe_evidence_ref"], "alias-terminal-result-ref")
        self.assertEqual(nested_artifact["terminal_result_type"], "cancel")
        self.assertEqual(nested_summary["safe_evidence_ref"], "nested-terminal-result-ref")

    def test_unsupported_type_and_evidence_ref_mismatch_are_blocked(self) -> None:
        unsupported = _intake_summary("success")
        mismatch = _intake_summary("delivery", "top-terminal-ref")
        mismatch["evidence_ref"] = "other-terminal-ref"
        mismatch["accepted_materials"] = [
            {"name": "task_record", "safe_evidence_ref": "nested-terminal-ref", "summary": "safe note"}
        ]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            unsupported_artifact, _, unsupported_exit = gate.build_verified_terminal_result_material_review_decision(
                self._write_json(root, unsupported)
            )
            mismatch_artifact, mismatch_summary, mismatch_exit = gate.build_verified_terminal_result_material_review_decision(
                self._write_json(root, mismatch)
            )

        self.assertEqual(unsupported_exit, 2)
        self.assertEqual(unsupported_artifact["review_decision"], "blocked")
        self.assertIn("unsupported_terminal_result_type", unsupported_artifact["decision_reasons"])
        self.assertEqual(mismatch_exit, 2)
        self.assertEqual(mismatch_artifact["review_decision"], "blocked")
        self.assertIn("evidence_ref_mismatch", json.dumps(mismatch_summary, ensure_ascii=False))
        self.assertFalse(mismatch_summary["delivery_success"])
        self.assertFalse(mismatch_summary["safe_to_control"])

    def test_rejected_materials_and_unsafe_raw_details_fail_closed_sanitized(self) -> None:
        rejected = _intake_summary(rejected=["operator_note_rejected"])
        unsafe = _intake_summary()
        unsafe["raw_artifacts"] = {"route_log": "/tmp/raw-route.jsonl"}
        unsafe["operator_note"] = "Authorization: Bearer secret-token /cmd_vel WAVE ROVER UART delivery_success=true"
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rejected_artifact, _, rejected_exit = gate.build_verified_terminal_result_material_review_decision(
                self._write_json(root, rejected)
            )
            unsafe_artifact, unsafe_summary, unsafe_exit = gate.build_verified_terminal_result_material_review_decision(
                self._write_json(root, unsafe)
            )

        encoded = json.dumps({"artifact": unsafe_artifact, "summary": unsafe_summary}, ensure_ascii=False)
        self.assertEqual(rejected_exit, 2)
        self.assertEqual(unsafe_exit, 2)
        self.assertEqual(rejected_artifact["review_decision"], "rejected")
        self.assertEqual(unsafe_artifact["review_decision"], "rejected")
        self.assertNotIn("/tmp/raw-route.jsonl", encoded)
        self.assertNotIn("secret-token", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("WAVE ROVER UART", encoded)
        self.assertFalse(unsafe_summary["delivery_success"])
        self.assertFalse(unsafe_summary["primary_actions_enabled"])
        self.assertFalse(unsafe_summary["safe_to_control"])

    def test_cli_writes_review_decision_artifact_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_path = self._write_json(root, _intake_summary("cancel"))
            output_dir = root / "out"
            exit_code = gate.main(["--input", str(input_path), "--output-dir", str(output_dir)])
            artifact = json.loads((output_dir / "verified_terminal_result_material_review_decision.json").read_text())
            summary = json.loads((output_dir / "verified_terminal_result_material_review_decision_summary.json").read_text())

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["verified_terminal_result_material_review_decision"], "accepted_for_review")
        self.assertEqual(summary["terminal_result_type"], "cancel")
        self.assertEqual(summary["summary_alias"], "robot_diagnostics_verified_terminal_result_material_review_decision_summary")
        self.assertTrue(summary["summary_only"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])


if __name__ == "__main__":
    unittest.main()
