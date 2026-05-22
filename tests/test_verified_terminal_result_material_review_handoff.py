#!/usr/bin/env python3
"""verified_terminal_result_material_review_handoff gate 的离线围栏测试。"""

from __future__ import annotations

# 测试约束 01：fixture 只表达上一轮 safe review-decision，不模拟 raw 现场材料。
# 测试约束 02：ready_for_owner_handoff 只表示 owner 可接手，不代表 delivery success。
# 测试约束 03：needs_material_backfill 必须保留 missing_required_materials。
# 测试约束 04：rejected/unsafe success/control/hardware/reviewer copy 必须 fail closed。
# 测试约束 05：missing source 必须 blocked。
# 测试约束 06：Robot diagnostics safe alias 与 wrapper 必须可消费。
# 测试约束 07：输出保持 source=software_proof 与 not_proven。
# 测试约束 08：输出保持 delivery_success=false、primary_actions_enabled=false、safe_to_control=false。

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "pc-tools" / "evidence" / "verified_terminal_result_material_review_handoff.py"
SPEC = importlib.util.spec_from_file_location("verified_terminal_result_material_review_handoff", SCRIPT)
gate = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(gate)


def _decision_summary(
    review_decision: str = "accepted_for_review",
    result_type: str = "delivery",
    evidence_ref: str = "terminal-handoff-2026-05-22T12-13Z",
    command_id: str = "cmd-terminal-safe-001",
    missing: list[str] | None = None,
    rejected: list[str] | None = None,
    **extra: object,
) -> dict[str, object]:
    # source 使用上一轮 review-decision summary 的安全消费面。
    payload: dict[str, object] = {
        "schema": "trashbot.verified_terminal_result_material_review_decision_summary.v1",
        "schema_version": 1,
        "capability": "verified_terminal_result_material_review_decision",
        "evidence_boundary": "software_proof_docker_verified_terminal_result_material_review_decision_gate",
        "source": "software_proof",
        "status": "not_proven",
        "review_decision": review_decision,
        "verified_terminal_result_material_review_decision": review_decision,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "safe_command_id": command_id,
        "same_evidence_ref_required": True,
        "terminal_result_type": result_type,
        "material_status_summary": {
            "accepted_materials": ["task_record", "delivery_result"] if review_decision == "accepted_for_review" else [],
            "missing_materials": [] if missing is None else missing,
            "rejected_materials": [] if rejected is None else rejected,
        },
        "next_required_evidence": [] if missing is None else missing,
        "not_proven": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "safe_copy": (
            f"verified_terminal_result_material_review_decision: review_decision={review_decision}; "
            f"evidence_ref={evidence_ref}; terminal_result_type={result_type}; not_proven; "
            "delivery_success=false; primary_actions_enabled=false; safe_to_control=false."
        ),
    }
    payload.update(extra)
    return payload


class VerifiedTerminalResultMaterialReviewHandoffTest(unittest.TestCase):
    def _write_json(self, root: Path, payload: dict) -> Path:
        # 临时输入只服务离线 gate 测试，不会进入 artifact 的 raw source。
        path = root / "input.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def test_accepted_review_decision_maps_to_ready_owner_handoff_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            input_path = self._write_json(Path(td), _decision_summary())
            artifact, summary, exit_code = gate.build_verified_terminal_result_material_review_handoff(input_path)

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], gate.ARTIFACT_SCHEMA)
        self.assertEqual(summary["schema"], gate.SUMMARY_SCHEMA)
        self.assertEqual(artifact["handoff_status"], "ready_for_owner_handoff")
        self.assertEqual(summary["source_review_decision"], "accepted_for_review")
        self.assertEqual(summary["safe_evidence_ref"], "terminal-handoff-2026-05-22T12-13Z")
        self.assertEqual(summary["safe_command_id"], "cmd-terminal-safe-001")
        self.assertEqual(summary["terminal_result_type"], "delivery")
        self.assertIn("real_terminal_delivery_result", summary["missing_required_materials"])
        self.assertIn("owner_handoff", summary)
        self.assertIn("next_required_evidence", summary)
        self.assertIn("safe_copy", summary)
        self.assertIn("material_status_summary", summary)
        self.assertIn("software_proof_docker_verified_terminal_result_material_review_handoff_gate", encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("delivery_success=false", encoded)
        self.assertIn("primary_actions_enabled=false", encoded)
        self.assertIn("safe_to_control=false", encoded)
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])

    def test_needs_material_backfill_preserves_missing_terminal_materials(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            input_path = self._write_json(
                Path(td),
                _decision_summary(
                    "needs_material_backfill",
                    missing=["real_terminal_dropoff_result", "true_phone_browser_or_device_evidence"],
                ),
            )
            artifact, summary, exit_code = gate.build_verified_terminal_result_material_review_handoff(input_path)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["handoff_status"], "needs_material_backfill")
        self.assertIn("review_decision_requires_missing_terminal_result_material_backfill", artifact["handoff_reasons"])
        self.assertIn("real_terminal_dropoff_result", summary["missing_required_materials"])
        self.assertIn("Backfill same safe evidence_ref material: real_terminal_dropoff_result", summary["next_required_evidence"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["safe_to_control"])

    def test_robot_alias_and_nested_wrapper_are_supported(self) -> None:
        alias = _decision_summary("accepted_for_review", "dropoff", "alias-terminal-handoff-ref")
        alias["schema"] = "robot_diagnostics_verified_terminal_result_material_review_decision_summary"
        nested = {
            "schema": "trashbot.verified_terminal_result_material_review_decision.v1",
            "verified_terminal_result_material_review_decision_summary": _decision_summary(
                "accepted_for_review",
                "cancel",
                "nested-terminal-handoff-ref",
            ),
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            alias_artifact, _, alias_exit = gate.build_verified_terminal_result_material_review_handoff(
                self._write_json(root, alias)
            )
            nested_artifact, nested_summary, nested_exit = gate.build_verified_terminal_result_material_review_handoff(
                self._write_json(root, nested)
            )

        self.assertEqual(alias_exit, 0)
        self.assertEqual(nested_exit, 0)
        self.assertEqual(alias_artifact["terminal_result_type"], "dropoff")
        self.assertEqual(alias_artifact["handoff_status"], "ready_for_owner_handoff")
        self.assertEqual(nested_artifact["terminal_result_type"], "cancel")
        self.assertEqual(nested_summary["safe_evidence_ref"], "nested-terminal-handoff-ref")

    def test_rejected_and_blocked_review_decisions_map_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rejected_artifact, rejected_summary, rejected_exit = gate.build_verified_terminal_result_material_review_handoff(
                self._write_json(root, _decision_summary("rejected", rejected=["unsafe_terminal_material"]))
            )
            blocked_artifact, blocked_summary, blocked_exit = gate.build_verified_terminal_result_material_review_handoff(
                self._write_json(root, _decision_summary("blocked", result_type="delivery"))
            )

        self.assertEqual(rejected_exit, 2)
        self.assertEqual(blocked_exit, 2)
        self.assertEqual(rejected_artifact["handoff_status"], "rejected")
        self.assertEqual(blocked_artifact["handoff_status"], "blocked")
        self.assertIn("unsafe_terminal_material", rejected_summary["rejected_material_refs"])
        self.assertEqual(blocked_summary["blocked_reason"], "review_decision_blocked_before_owner_handoff")
        self.assertFalse(rejected_summary["primary_actions_enabled"])
        self.assertFalse(blocked_summary["safe_to_control"])

    def test_unsupported_type_ref_mismatch_and_unsafe_details_fail_closed_sanitized(self) -> None:
        unsupported = _decision_summary(result_type="success")
        mismatch = _decision_summary(evidence_ref="top-terminal-ref")
        mismatch["accepted_material_refs"] = [{"name": "task_record", "safe_evidence_ref": "other-terminal-ref"}]
        unsafe = _decision_summary()
        unsafe["raw_artifacts"] = {"route_log": "/tmp/raw-route.jsonl"}
        unsafe["operator_note"] = "Authorization: Bearer secret-token /cmd_vel WAVE ROVER UART delivery_success=true"
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            unsupported_artifact, _, unsupported_exit = gate.build_verified_terminal_result_material_review_handoff(
                self._write_json(root, unsupported)
            )
            mismatch_artifact, mismatch_summary, mismatch_exit = gate.build_verified_terminal_result_material_review_handoff(
                self._write_json(root, mismatch)
            )
            unsafe_artifact, unsafe_summary, unsafe_exit = gate.build_verified_terminal_result_material_review_handoff(
                self._write_json(root, unsafe)
            )

        encoded = json.dumps({"artifact": unsafe_artifact, "summary": unsafe_summary}, ensure_ascii=False)
        self.assertEqual(unsupported_exit, 2)
        self.assertEqual(mismatch_exit, 2)
        self.assertEqual(unsafe_exit, 2)
        self.assertEqual(unsupported_artifact["handoff_status"], "blocked")
        self.assertEqual(mismatch_artifact["handoff_status"], "blocked")
        self.assertEqual(unsafe_artifact["handoff_status"], "rejected")
        self.assertIn("unsupported_terminal_result_type", unsupported_artifact["handoff_reasons"])
        self.assertIn("evidence_ref_mismatch", json.dumps(mismatch_summary, ensure_ascii=False))
        self.assertNotIn("/tmp/raw-route.jsonl", encoded)
        self.assertNotIn("secret-token", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("WAVE ROVER UART", encoded)
        self.assertFalse(unsafe_summary["delivery_success"])
        self.assertFalse(unsafe_summary["primary_actions_enabled"])
        self.assertFalse(unsafe_summary["safe_to_control"])

    def test_cli_writes_handoff_artifact_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_path = self._write_json(root, _decision_summary("accepted_for_review", "cancel"))
            output_dir = root / "out"
            exit_code = gate.main(["--input", str(input_path), "--output-dir", str(output_dir)])
            artifact = json.loads((output_dir / "verified_terminal_result_material_review_handoff.json").read_text())
            summary = json.loads((output_dir / "verified_terminal_result_material_review_handoff_summary.json").read_text())

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["verified_terminal_result_material_review_handoff"], "ready_for_owner_handoff")
        self.assertEqual(summary["terminal_result_type"], "cancel")
        self.assertEqual(summary["summary_alias"], "robot_diagnostics_verified_terminal_result_material_review_handoff_summary")
        self.assertTrue(summary["summary_only"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])


if __name__ == "__main__":
    unittest.main()
