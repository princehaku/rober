#!/usr/bin/env python3
"""verified_terminal_result_material_followup_escalation_status gate 的离线围栏测试。"""

from __future__ import annotations

# 测试约束 01：fixture 只表达上一轮 safe review-handoff，不模拟 raw 现场材料。
# 测试约束 02：escalated 只表示人工补证路由已形成，不代表 delivery success。
# 测试约束 03：waiting 必须保留 required_material_backfill。
# 测试约束 04：unsafe success/control/hardware/ACK/replay/reviewer copy 必须 fail closed。
# 测试约束 05：missing source 必须 blocked。
# 测试约束 06：Robot diagnostics safe alias 与 wrapper 必须可消费。
# 测试约束 07：输出保持 source=software_proof、software_proof 与 not_proven。
# 测试约束 08：输出保持 delivery_success=false、primary_actions_enabled=false、safe_to_control=false。

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "pc-tools" / "evidence" / "verified_terminal_result_material_followup_escalation_status.py"
SPEC = importlib.util.spec_from_file_location("verified_terminal_result_material_followup_escalation_status", SCRIPT)
gate = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(gate)


def _handoff_summary(
    handoff_status: str = "ready_for_owner_handoff",
    result_type: str = "delivery",
    evidence_ref: str = "terminal-followup-2026-05-23T12-13Z",
    command_id: str = "cmd-terminal-safe-002",
    missing: list[str] | None = None,
    **extra: object,
) -> dict[str, object]:
    # source 使用上一轮 review-handoff summary 的安全消费面。
    payload: dict[str, object] = {
        "schema": "trashbot.verified_terminal_result_material_review_handoff_summary.v1",
        "schema_version": 1,
        "capability": "verified_terminal_result_material_review_handoff",
        "evidence_boundary": "software_proof_docker_verified_terminal_result_material_review_handoff_gate",
        "source": "software_proof",
        "status": "not_proven",
        "handoff_status": handoff_status,
        "verified_terminal_result_material_review_handoff": handoff_status,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "safe_command_id": command_id,
        "command_id": command_id,
        "same_evidence_ref_required": True,
        "terminal_result_type": result_type,
        "assigned_owner": "field_terminal_result_material_owner",
        "support_owner": "support_terminal_result_material_owner",
        "reviewer_route": "terminal_result_material_reviewer",
        "missing_required_materials": [] if missing is None else missing,
        "next_required_evidence": [] if missing is None else missing,
        "not_proven": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "safe_copy": (
            f"verified_terminal_result_material_review_handoff: handoff_status={handoff_status}; "
            f"evidence_ref={evidence_ref}; terminal_result_type={result_type}; source=software_proof; "
            "software_proof; not_proven; delivery_success=false; primary_actions_enabled=false; safe_to_control=false."
        ),
    }
    payload.update(extra)
    return payload


class VerifiedTerminalResultMaterialFollowupEscalationStatusTest(unittest.TestCase):
    def _write_json(self, root: Path, payload: dict) -> Path:
        # 临时输入只服务离线 gate 测试，不会进入 artifact 的 raw source。
        path = root / "input.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def test_ready_handoff_maps_to_escalated_followup_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            input_path = self._write_json(Path(td), _handoff_summary())
            artifact, summary, exit_code = gate.build_verified_terminal_result_material_followup_escalation_status(input_path)

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], gate.ARTIFACT_SCHEMA)
        self.assertEqual(summary["schema"], gate.SUMMARY_SCHEMA)
        self.assertEqual(artifact["followup_status"], "escalated_for_terminal_result_material_followup_not_proven")
        self.assertEqual(summary["source_handoff_status"], "ready_for_owner_handoff")
        self.assertEqual(summary["safe_evidence_ref"], "terminal-followup-2026-05-23T12-13Z")
        self.assertEqual(summary["safe_command_id"], "cmd-terminal-safe-002")
        self.assertEqual(summary["terminal_result_type"], "delivery")
        self.assertEqual(summary["assigned_owner"], "field_terminal_result_material_owner")
        self.assertIn("real_terminal_delivery_result", summary["required_material_backfill"])
        self.assertIn("software_proof_docker_verified_terminal_result_material_followup_escalation_status_gate", encoded)
        self.assertIn("source=software_proof", encoded)
        self.assertIn("software_proof", encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("delivery_success=false", encoded)
        self.assertIn("primary_actions_enabled=false", encoded)
        self.assertIn("safe_to_control=false", encoded)
        self.assertIn("no OKR percentage lift", encoded)
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])

    def test_material_backfill_maps_to_waiting_status(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            input_path = self._write_json(
                Path(td),
                _handoff_summary(
                    "needs_material_backfill",
                    missing=["real_terminal_dropoff_result", "true_phone_browser_or_device_evidence"],
                ),
            )
            artifact, summary, exit_code = gate.build_verified_terminal_result_material_followup_escalation_status(input_path)

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["followup_status"], "waiting_for_terminal_result_material_backfill_not_proven")
        self.assertIn("real_terminal_dropoff_result", summary["required_material_backfill"])
        self.assertIn("Waiting for same safe evidence_ref material backfill: real_terminal_dropoff_result", summary["next_required_evidence"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["safe_to_control"])

    def test_missing_support_owner_maps_to_reassignment(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            input_path = self._write_json(Path(td), _handoff_summary(support_owner=""))
            artifact, summary, exit_code = gate.build_verified_terminal_result_material_followup_escalation_status(input_path)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["followup_status"], "needs_support_owner_reassignment_not_proven")
        self.assertIn("missing_assigned_owner_support_owner_or_reviewer_route", summary["escalation_reason"])
        self.assertIn("Assign field owner, support owner, and reviewer route", summary["next_required_evidence"][0])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_robot_alias_and_nested_wrapper_are_supported(self) -> None:
        alias = _handoff_summary("ready_for_owner_handoff", "dropoff", "alias-terminal-followup-ref")
        alias["schema"] = "robot_diagnostics_verified_terminal_result_material_review_handoff_summary"
        nested = {
            "schema": "trashbot.verified_terminal_result_material_review_handoff.v1",
            "verified_terminal_result_material_review_handoff_summary": _handoff_summary(
                "ready_for_owner_handoff",
                "cancel",
                "nested-terminal-followup-ref",
            ),
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            alias_artifact, _, alias_exit = gate.build_verified_terminal_result_material_followup_escalation_status(
                self._write_json(root, alias)
            )
            nested_artifact, nested_summary, nested_exit = gate.build_verified_terminal_result_material_followup_escalation_status(
                self._write_json(root, nested)
            )

        self.assertEqual(alias_exit, 0)
        self.assertEqual(nested_exit, 0)
        self.assertEqual(alias_artifact["terminal_result_type"], "dropoff")
        self.assertEqual(alias_artifact["followup_status"], "escalated_for_terminal_result_material_followup_not_proven")
        self.assertEqual(nested_artifact["terminal_result_type"], "cancel")
        self.assertEqual(nested_summary["safe_evidence_ref"], "nested-terminal-followup-ref")

    def test_rejected_blocked_and_missing_inputs_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rejected_artifact, rejected_summary, rejected_exit = gate.build_verified_terminal_result_material_followup_escalation_status(
                self._write_json(root, _handoff_summary("rejected", rejected_material_refs=["unsafe_terminal_material"]))
            )
            blocked_artifact, blocked_summary, blocked_exit = gate.build_verified_terminal_result_material_followup_escalation_status(
                self._write_json(root, _handoff_summary("blocked", result_type="delivery"))
            )
            missing_artifact, missing_summary, missing_exit = gate.build_verified_terminal_result_material_followup_escalation_status(
                root / "missing.json"
            )

        self.assertEqual(rejected_exit, 2)
        self.assertEqual(blocked_exit, 2)
        self.assertEqual(missing_exit, 2)
        self.assertEqual(rejected_artifact["followup_status"], "rejected_unsafe_terminal_result_followup_not_proven")
        self.assertEqual(blocked_artifact["followup_status"], "blocked_missing_terminal_result_review_handoff_not_proven")
        self.assertEqual(missing_artifact["followup_status"], "blocked_missing_terminal_result_review_handoff_not_proven")
        self.assertIn("unsafe_terminal_material", rejected_summary["next_required_evidence"][0])
        self.assertIn("source_review_handoff_blocked_before_followup", blocked_summary["blocked_reason"])
        self.assertIn("input_missing", missing_summary["blocked_reason"])
        self.assertFalse(rejected_summary["primary_actions_enabled"])
        self.assertFalse(blocked_summary["safe_to_control"])

    def test_unsupported_type_ref_mismatch_and_unsafe_details_fail_closed_sanitized(self) -> None:
        unsupported = _handoff_summary(result_type="success")
        mismatch = _handoff_summary(evidence_ref="top-terminal-followup-ref")
        mismatch["required_material_backfill"] = [{"name": "task_record", "safe_evidence_ref": "other-terminal-followup-ref"}]
        unsafe = _handoff_summary()
        unsafe["raw_artifacts"] = {"route_log": "/tmp/raw-route.jsonl"}
        unsafe["operator_note"] = "Authorization: Bearer secret-token /cmd_vel WAVE ROVER UART delivery_success=true ack cursor replay hint reviewer resolved"
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            unsupported_artifact, _, unsupported_exit = gate.build_verified_terminal_result_material_followup_escalation_status(
                self._write_json(root, unsupported)
            )
            mismatch_artifact, mismatch_summary, mismatch_exit = gate.build_verified_terminal_result_material_followup_escalation_status(
                self._write_json(root, mismatch)
            )
            unsafe_artifact, unsafe_summary, unsafe_exit = gate.build_verified_terminal_result_material_followup_escalation_status(
                self._write_json(root, unsafe)
            )

        encoded = json.dumps({"artifact": unsafe_artifact, "summary": unsafe_summary}, ensure_ascii=False)
        self.assertEqual(unsupported_exit, 2)
        self.assertEqual(mismatch_exit, 2)
        self.assertEqual(unsafe_exit, 2)
        self.assertEqual(unsupported_artifact["followup_status"], "blocked_missing_terminal_result_review_handoff_not_proven")
        self.assertEqual(mismatch_artifact["followup_status"], "blocked_missing_terminal_result_review_handoff_not_proven")
        self.assertEqual(unsafe_artifact["followup_status"], "rejected_unsafe_terminal_result_followup_not_proven")
        self.assertIn("unsupported_terminal_result_type", unsupported_artifact["escalation_reason"])
        self.assertIn("evidence_ref_mismatch", json.dumps(mismatch_summary, ensure_ascii=False))
        self.assertNotIn("/tmp/raw-route.jsonl", encoded)
        self.assertNotIn("secret-token", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("WAVE ROVER UART", encoded)
        self.assertFalse(unsafe_summary["delivery_success"])
        self.assertFalse(unsafe_summary["primary_actions_enabled"])
        self.assertFalse(unsafe_summary["safe_to_control"])

    def test_cli_writes_followup_escalation_artifact_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_path = self._write_json(root, _handoff_summary("ready_for_owner_handoff", "cancel"))
            output_dir = root / "out"
            exit_code = gate.main(["--input", str(input_path), "--output-dir", str(output_dir)])
            artifact = json.loads((output_dir / "verified_terminal_result_material_followup_escalation_status.json").read_text())
            summary = json.loads((output_dir / "verified_terminal_result_material_followup_escalation_status_summary.json").read_text())

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            artifact["verified_terminal_result_material_followup_escalation_status"],
            "escalated_for_terminal_result_material_followup_not_proven",
        )
        self.assertEqual(summary["terminal_result_type"], "cancel")
        self.assertEqual(summary["summary_alias"], "robot_diagnostics_verified_terminal_result_material_followup_escalation_status_summary")
        self.assertTrue(summary["summary_only"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])


if __name__ == "__main__":
    unittest.main()
