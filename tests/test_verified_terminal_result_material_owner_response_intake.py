#!/usr/bin/env python3
"""verified_terminal_result_material_owner_response_intake gate 的离线围栏测试。"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "pc-tools" / "evidence" / "verified_terminal_result_material_owner_response_intake.py"
SPEC = importlib.util.spec_from_file_location("verified_terminal_result_material_owner_response_intake", SCRIPT)
gate = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(gate)


# 测试约束 01：fixture 只表达上一轮 safe follow-up status 和脱敏 owner response。
# 测试约束 02：accepted 只表示 accepted_terminal_result_material_owner_response_not_proven。
# 测试约束 03：missing/rejected/unsafe/blocked 全部非 0 且 fail-closed。
# 测试约束 04：source、response 与 CLI 指定值必须使用同一个 safe evidence_ref。
# 测试约束 05：raw/URL/DB/OSS/path/ROS/control/hardware/ACK/replay/reviewer claim 必须拒绝。
# 测试约束 06：PR #5 thread PRRT_kwDOSWB9286CJ3tX 必须保持 unresolved / hardware_material_pending。
# 测试约束 07：输出保持 source=software_proof、software_proof 和 not_proven。
# 测试约束 08：输出保持 delivery_success=false、primary_actions_enabled=false、safe_to_control=false。
# 测试约束 09：测试不访问 ROS graph、硬件、外部云、手机 runtime 或 raw logs。


class VerifiedTerminalResultMaterialOwnerResponseIntakeTest(unittest.TestCase):
    def _write_json(self, root: Path, name: str, payload: object) -> Path:
        # 临时 JSON 只服务离线 gate 测试，不代表真实现场材料。
        path = root / name
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def _source(self, evidence_ref: str = "terminal-owner-response-101", followup_status: str = "escalated_for_terminal_result_material_followup_not_proven") -> dict[str, object]:
        # source 使用上一轮 follow-up escalation status 的安全消费面。
        return {
            "schema": "trashbot.verified_terminal_result_material_followup_escalation_status_summary.v1",
            "schema_version": 1,
            "capability": "verified_terminal_result_material_followup_escalation_status",
            "source": "software_proof",
            "status": "not_proven",
            "software_proof": True,
            "not_proven": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_to_control": False,
            "evidence_boundary": "software_proof_docker_verified_terminal_result_material_followup_escalation_status_gate",
            "followup_status": followup_status,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "safe_command_id": "cmd-terminal-owner-response-001",
            "command_id": "cmd-terminal-owner-response-001",
            "terminal_result_type": "delivery",
            "field_owner": "field_terminal_result_material_owner",
            "support_owner": "support_terminal_result_material_owner",
            "reviewer_route": "terminal_result_material_reviewer",
            "safe_copy": "source=software_proof; software_proof; not_proven; delivery_success=false; primary_actions_enabled=false; safe_to_control=false.",
        }

    def _owner_response(self, evidence_ref: str = "terminal-owner-response-101") -> dict[str, object]:
        # owner response 样本只给安全类别索引，不携带 raw terminal material。
        return {
            "schema": gate.OWNER_RESPONSE_SCHEMA,
            "source": "software_proof",
            "status": "not_proven",
            "software_proof": True,
            "not_proven": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_to_control": False,
            "owner_response_status": "accepted",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "materials": {
                name: {
                    "name": name,
                    "status": "accepted",
                    "safe_evidence_ref": evidence_ref,
                    "summary": f"sanitized owner response category index for {name}",
                    "delivery_success": False,
                    "primary_actions_enabled": False,
                    "safe_to_control": False,
                }
                for name in gate.REQUIRED_OWNER_RESPONSE_MATERIALS
            },
        }

    def _build(self, root: Path, source_payload: dict[str, object], response_payload: dict[str, object] | None, evidence_ref: str = "terminal-owner-response-101") -> tuple[dict[str, object], dict[str, object], int]:
        # 公共 helper 让 case 聚焦分类和安全边界。
        source_path = self._write_json(root, "source.json", source_payload)
        response_path = ""
        if response_payload is not None:
            response_path = str(self._write_json(root, "owner-response.json", response_payload))
        return gate.build_verified_terminal_result_material_owner_response_intake(str(source_path), response_path, evidence_ref)

    def test_safe_owner_response_is_accepted_not_proven_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(Path(tmp), self._source(), self._owner_response())

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], gate.ARTIFACT_SCHEMA)
        self.assertEqual(summary["schema"], gate.SUMMARY_SCHEMA)
        self.assertEqual(artifact["owner_response_status"], gate.ACCEPTED_STATUS)
        self.assertEqual(summary["source_followup_status"], "escalated_for_terminal_result_material_followup_not_proven")
        self.assertEqual(summary["safe_evidence_ref"], "terminal-owner-response-101")
        self.assertEqual(summary["safe_command_id"], "cmd-terminal-owner-response-001")
        self.assertEqual(summary["terminal_result_type"], "delivery")
        self.assertEqual(len(summary["accepted_materials"]), len(gate.REQUIRED_OWNER_RESPONSE_MATERIALS))
        self.assertIn("software_proof_docker_verified_terminal_result_material_owner_response_intake_gate", encoded)
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

    def test_missing_owner_response_is_missing_and_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(Path(tmp), self._source("terminal-owner-response-102"), None, "terminal-owner-response-102")

        self.assertEqual(artifact["owner_response_status"], gate.MISSING_STATUS)
        self.assertNotEqual(exit_code, 0)
        self.assertIn("owner_response_json_not_provided", artifact["owner_response_reasons"])
        self.assertIn("sanitized_owner_response_metadata", artifact["next_required_evidence"][0])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["safe_to_control"])

    def test_partial_and_rejected_owner_response_classify_without_control_claims(self) -> None:
        partial = self._owner_response("terminal-owner-response-103")
        materials = partial["materials"]
        self.assertIsInstance(materials, dict)
        materials.pop("reviewer_route_confirmation")
        rejected = self._owner_response("terminal-owner-response-104")
        rejected_materials = rejected["materials"]
        self.assertIsInstance(rejected_materials, dict)
        rejected_materials["terminal_result_material_status"]["status"] = "rejected"
        with tempfile.TemporaryDirectory() as tmp:
            partial_artifact, _partial_summary, partial_exit = self._build(
                Path(tmp),
                self._source("terminal-owner-response-103"),
                partial,
                "terminal-owner-response-103",
            )
        with tempfile.TemporaryDirectory() as tmp:
            rejected_artifact, rejected_summary, rejected_exit = self._build(
                Path(tmp),
                self._source("terminal-owner-response-104"),
                rejected,
                "terminal-owner-response-104",
            )

        self.assertEqual(partial_artifact["owner_response_status"], gate.MISSING_STATUS)
        self.assertEqual(rejected_artifact["owner_response_status"], gate.REJECTED_STATUS)
        self.assertNotEqual(partial_exit, 0)
        self.assertNotEqual(rejected_exit, 0)
        self.assertIn("reviewer_route_confirmation", partial_artifact["missing_materials"])
        self.assertIn("terminal_result_material_status", rejected_artifact["rejected_materials"])
        self.assertFalse(rejected_summary["primary_actions_enabled"])

    def test_bad_source_and_evidence_ref_mismatch_block(self) -> None:
        bad_source = self._source("terminal-owner-response-105", "blocked_missing_terminal_result_review_handoff_not_proven")
        with tempfile.TemporaryDirectory() as tmp:
            blocked_artifact, _blocked_summary, blocked_exit = self._build(
                Path(tmp),
                bad_source,
                self._owner_response("terminal-owner-response-105"),
                "terminal-owner-response-105",
            )
        with tempfile.TemporaryDirectory() as tmp:
            mismatch_artifact, mismatch_summary, mismatch_exit = self._build(
                Path(tmp),
                self._source("terminal-owner-response-106"),
                self._owner_response("other-terminal-owner-response-106"),
                "terminal-owner-response-106",
            )

        self.assertEqual(blocked_artifact["owner_response_status"], gate.BLOCKED_SOURCE_STATUS)
        self.assertEqual(mismatch_artifact["owner_response_status"], gate.BLOCKED_REF_STATUS)
        self.assertNotEqual(blocked_exit, 0)
        self.assertNotEqual(mismatch_exit, 0)
        self.assertIn("previous_followup_status_not_safe_for_owner_response_intake", blocked_artifact["blocked_reason"])
        self.assertIn("owner_response_evidence_ref_mismatch", mismatch_summary["blocked_reason"])
        self.assertFalse(mismatch_summary["delivery_success"])

    def test_unsafe_raw_paths_ros_hardware_ack_and_resolution_claims_are_sanitized(self) -> None:
        unsafe = self._owner_response("terminal-owner-response-107")
        unsafe["operator_note"] = (
            "raw owner body /Users/m4/raw.json traceback /cmd_vel WAVE ROVER UART "
            "ack cursor replay command PRRT_kwDOSWB9286CJ3tX resolved delivery_success=true"
        )
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._source("terminal-owner-response-107"),
                unsafe,
                "terminal-owner-response-107",
            )

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertEqual(artifact["owner_response_status"], gate.UNSAFE_STATUS)
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
        alias = self._source("terminal-owner-response-108")
        alias["schema"] = "robot_diagnostics_verified_terminal_result_material_followup_escalation_status_summary"
        nested = {"summary": alias}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._write_json(root, "nested-source.json", nested)
            response = self._write_json(root, "owner-response.json", self._owner_response("terminal-owner-response-108"))
            output_dir = root / "out"
            exit_code = gate.main(["--source", str(source), "--owner-response", str(response), "--evidence-ref", "terminal-owner-response-108", "--output-dir", str(output_dir)])
            artifact = json.loads((output_dir / "verified_terminal_result_material_owner_response_intake.json").read_text())
            summary = json.loads((output_dir / "verified_terminal_result_material_owner_response_intake_summary.json").read_text())

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["owner_response_status"], gate.ACCEPTED_STATUS)
        self.assertEqual(summary["summary_alias"], "robot_diagnostics_verified_terminal_result_material_owner_response_intake_summary")
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
        self.assertIn("--owner-response", result.stdout)
        self.assertIn("source=software_proof", result.stdout)
        self.assertIn("delivery_success=false", result.stdout)
        self.assertIn("primary_actions_enabled=false", result.stdout)
        self.assertIn("safe_to_control=false", result.stdout)


if __name__ == "__main__":
    unittest.main()
