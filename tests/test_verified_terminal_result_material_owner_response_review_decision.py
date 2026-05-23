#!/usr/bin/env python3
"""verified_terminal_result_material_owner_response_review_decision gate 的离线围栏测试。"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "pc-tools" / "evidence" / "verified_terminal_result_material_owner_response_review_decision.py"
SPEC = importlib.util.spec_from_file_location("verified_terminal_result_material_owner_response_review_decision", SCRIPT)
gate = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(gate)


# 测试约束 01：fixture 只表达上一轮 owner response intake safe metadata。
# 测试约束 02：accepted 只表示 review decision accepted_not_proven，不证明真实结果。
# 测试约束 03：missing/rejected/unsafe/blocked 全部非 0 且 fail-closed。
# 测试约束 04：source 与 CLI 指定值必须使用同一个 safe evidence_ref。
# 测试约束 05：raw/URL/DB/OSS/path/ROS/control/hardware/ACK/replay/reviewer claim 必须拒绝。
# 测试约束 06：PR #5 thread PRRT_kwDOSWB9286CJ3tX 必须保持 unresolved / hardware_material_pending。
# 测试约束 07：输出保持 source=software_proof、software_proof 和 not_proven。
# 测试约束 08：输出保持 delivery_success=false、primary_actions_enabled=false、safe_to_control=false。
# 测试约束 09：测试不访问 ROS graph、硬件、外部云、手机 runtime 或 raw logs。


class VerifiedTerminalResultMaterialOwnerResponseReviewDecisionTest(unittest.TestCase):
    def _write_json(self, root: Path, name: str, payload: object) -> Path:
        # 临时 JSON 只服务离线 gate 测试，不代表真实现场材料。
        path = root / name
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def _source(
        self,
        evidence_ref: str = "terminal-owner-review-101",
        owner_status: str = gate.SOURCE_ACCEPTED_STATUS,
    ) -> dict[str, object]:
        # source 使用上一轮 owner response intake 的安全消费面。
        return {
            "schema": "trashbot.verified_terminal_result_material_owner_response_intake_summary.v1",
            "schema_version": 1,
            "capability": "verified_terminal_result_material_owner_response_intake",
            "source": "software_proof",
            "status": "not_proven",
            "software_proof": True,
            "not_proven": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_to_control": False,
            "evidence_boundary": "software_proof_docker_verified_terminal_result_material_owner_response_intake_gate",
            "owner_response_status": owner_status,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "safe_command_id": "cmd-terminal-owner-review-001",
            "command_id": "cmd-terminal-owner-review-001",
            "terminal_result_type": "delivery",
            "field_owner": "field_terminal_result_material_owner",
            "support_owner": "support_terminal_result_material_owner",
            "reviewer_route": "terminal_result_material_reviewer",
            "accepted_materials": list(gate.REQUIRED_REVIEW_MATERIALS),
            "missing_materials": [],
            "rejected_materials": [],
            "unsafe_materials": [],
            "safe_copy": {
                "source": "software_proof",
                "status": "not_proven",
                "software_proof": True,
                "not_proven": True,
                "delivery_success": False,
                "primary_actions_enabled": False,
                "safe_to_control": False,
                "evidence_ref": evidence_ref,
            },
        }

    def _build(
        self,
        root: Path,
        source_payload: dict[str, object],
        evidence_ref: str = "terminal-owner-review-101",
    ) -> tuple[dict[str, object], dict[str, object], int]:
        # 公共 helper 让 case 聚焦分类和安全边界。
        source_path = self._write_json(root, "owner-response-intake.json", source_payload)
        return gate.build_verified_terminal_result_material_owner_response_review_decision(str(source_path), evidence_ref)

    def test_safe_owner_response_intake_is_accepted_not_proven_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(Path(tmp), self._source())

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], gate.ARTIFACT_SCHEMA)
        self.assertEqual(summary["schema"], gate.SUMMARY_SCHEMA)
        self.assertEqual(artifact["review_decision"], gate.ACCEPTED_STATUS)
        self.assertEqual(summary["source_owner_response_status"], gate.SOURCE_ACCEPTED_STATUS)
        self.assertEqual(summary["safe_evidence_ref"], "terminal-owner-review-101")
        self.assertEqual(summary["safe_command_id"], "cmd-terminal-owner-review-001")
        self.assertEqual(summary["terminal_result_type"], "delivery")
        self.assertEqual(len(summary["accepted_materials"]), len(gate.REQUIRED_REVIEW_MATERIALS))
        self.assertIn("software_proof_docker_verified_terminal_result_material_owner_response_review_decision_gate", encoded)
        self.assertIn("source=software_proof", encoded)
        self.assertIn("software_proof", encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("delivery_success=false", encoded)
        self.assertIn("primary_actions_enabled=false", encoded)
        self.assertIn("safe_to_control=false", encoded)
        self.assertIn("no OKR percentage lift", encoded)
        self.assertEqual(artifact["pr5_thread"]["thread_id"], "PRRT_kwDOSWB9286CJ3tX")
        self.assertEqual(artifact["pr5_thread"]["state"], "unresolved")
        self.assertEqual(artifact["pr5_thread"]["material_state"], "hardware_material_pending")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])

    def test_missing_owner_response_intake_material_is_missing_and_nonzero(self) -> None:
        source = self._source("terminal-owner-review-102", gate.SOURCE_MISSING_STATUS)
        source["accepted_materials"] = []
        source["missing_materials"] = ["reviewer_route_confirmation"]
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(Path(tmp), source, "terminal-owner-review-102")

        self.assertEqual(artifact["review_decision"], gate.MISSING_STATUS)
        self.assertNotEqual(exit_code, 0)
        self.assertIn("reviewer_route_confirmation", artifact["missing_materials"])
        self.assertIn("reviewer_route_confirmation", artifact["next_required_evidence"][0])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["safe_to_control"])

    def test_rejected_and_unsafe_owner_response_intake_classify_without_control_claims(self) -> None:
        rejected = self._source("terminal-owner-review-103", gate.SOURCE_REJECTED_STATUS)
        rejected["accepted_materials"] = []
        rejected["rejected_materials"] = ["terminal_result_material_status"]
        unsafe = self._source("terminal-owner-review-104", gate.SOURCE_UNSAFE_STATUS)
        unsafe["accepted_materials"] = []
        unsafe["unsafe_materials"] = ["sanitized_owner_response_metadata"]
        with tempfile.TemporaryDirectory() as tmp:
            rejected_artifact, rejected_summary, rejected_exit = self._build(
                Path(tmp),
                rejected,
                "terminal-owner-review-103",
            )
        with tempfile.TemporaryDirectory() as tmp:
            unsafe_artifact, unsafe_summary, unsafe_exit = self._build(
                Path(tmp),
                unsafe,
                "terminal-owner-review-104",
            )

        self.assertEqual(rejected_artifact["review_decision"], gate.REJECTED_STATUS)
        self.assertEqual(unsafe_artifact["review_decision"], gate.UNSAFE_STATUS)
        self.assertNotEqual(rejected_exit, 0)
        self.assertNotEqual(unsafe_exit, 0)
        self.assertIn("terminal_result_material_status", rejected_artifact["rejected_materials"])
        self.assertIn("sanitized_owner_response_metadata", unsafe_artifact["unsafe_materials"])
        self.assertFalse(rejected_summary["primary_actions_enabled"])
        self.assertFalse(unsafe_summary["safe_to_control"])

    def test_bad_source_and_evidence_ref_mismatch_block(self) -> None:
        bad_source = self._source("terminal-owner-review-105")
        bad_source["schema"] = "trashbot.unsupported_owner_response_intake.v1"
        bad_source["capability"] = "unsupported_owner_response_intake"
        mismatch = self._source("terminal-owner-review-106")
        with tempfile.TemporaryDirectory() as tmp:
            blocked_artifact, _blocked_summary, blocked_exit = self._build(
                Path(tmp),
                bad_source,
                "terminal-owner-review-105",
            )
        with tempfile.TemporaryDirectory() as tmp:
            mismatch_artifact, mismatch_summary, mismatch_exit = self._build(
                Path(tmp),
                mismatch,
                "other-terminal-owner-review-106",
            )

        self.assertEqual(blocked_artifact["review_decision"], gate.BLOCKED_SOURCE_STATUS)
        self.assertEqual(mismatch_artifact["review_decision"], gate.BLOCKED_REF_STATUS)
        self.assertNotEqual(blocked_exit, 0)
        self.assertNotEqual(mismatch_exit, 0)
        self.assertIn("unsupported_terminal_result_owner_response_intake_schema", blocked_artifact["blocked_reason"])
        self.assertIn("evidence_ref_mismatch", mismatch_summary["blocked_reason"])
        self.assertFalse(mismatch_summary["delivery_success"])

    def test_unsafe_raw_paths_ros_hardware_ack_and_resolution_claims_are_sanitized(self) -> None:
        unsafe = self._source("terminal-owner-review-107")
        unsafe["operator_note"] = (
            "raw owner body /Users/m4/raw.json traceback /cmd_vel WAVE ROVER UART "
            "ack cursor replay command PRRT_kwDOSWB9286CJ3tX resolved delivery_success=true"
        )
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                unsafe,
                "terminal-owner-review-107",
            )

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertEqual(artifact["review_decision"], gate.UNSAFE_STATUS)
        self.assertNotEqual(exit_code, 0)
        self.assertIn("unsafe_raw_terminal_material_credential_ros_control_hardware_ack_replay_resolution_or_success_claim", artifact["blocked_reason"])
        self.assertNotIn("/Users/m4/raw.json", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("WAVE ROVER UART", encoded)
        self.assertNotIn("resolved delivery_success=true", encoded)
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])

    def test_robot_alias_nested_wrapper_source_alias_and_cli_outputs(self) -> None:
        alias = self._source("terminal-owner-review-108")
        alias["schema"] = "robot_diagnostics_verified_terminal_result_material_owner_response_intake_summary"
        nested = {"summary": alias}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._write_json(root, "nested-source.json", nested)
            output_dir = root / "out"
            exit_code = gate.main(["--source", str(source), "--evidence-ref", "terminal-owner-review-108", "--output-dir", str(output_dir)])
            artifact = json.loads((output_dir / "verified_terminal_result_material_owner_response_review_decision.json").read_text())
            summary = json.loads((output_dir / "verified_terminal_result_material_owner_response_review_decision_summary.json").read_text())

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["review_decision"], gate.ACCEPTED_STATUS)
        self.assertEqual(summary["summary_alias"], "robot_diagnostics_verified_terminal_result_material_owner_response_review_decision_summary")
        self.assertTrue(summary["summary_only"])
        self.assertFalse(artifact["safe_to_control"])

    def test_cli_help_mentions_required_inputs_and_literals(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            check=False,
            text=True,
            capture_output=True,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("--input", result.stdout)
        self.assertIn("--source", result.stdout)
        self.assertIn("source=software_proof", result.stdout)
        self.assertIn("evidence_ref", result.stdout)
        self.assertIn("delivery_success=false", result.stdout)
        self.assertIn("primary_actions_enabled=false", result.stdout)
        self.assertIn("safe_to_control=false", result.stdout)


if __name__ == "__main__":
    unittest.main()
