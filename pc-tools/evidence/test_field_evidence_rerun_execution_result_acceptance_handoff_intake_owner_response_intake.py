#!/usr/bin/env python3
"""acceptance handoff intake owner response intake gate 的围栏测试。"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools/evidence 不是 package；测试显式加入目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status as followup  # noqa: E402
import field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake as gate  # noqa: E402


# 测试约束 01：fixture 只表达上一轮 safe follow-up status 和 owner response packet。
# 测试约束 02：accepted 只表示 accepted_for_review_not_proven。
# 测试约束 03：missing/rejected/blocked 均保持 fail-closed。
# 测试约束 04：同一 safe evidence_ref 是 source 与 response 的硬约束。
# 测试约束 05：success/control/O5/HIL/PR #5 resolution claim 必须 blocked。
# 测试约束 06：PR #5 thread X 必须保持 unresolved / hardware_material_pending。
# 测试约束 07：输出保持 source=software_proof、software_proof 和 not_proven。
# 测试约束 08：输出保持 delivery_success=false。
# 测试约束 09：输出保持 primary_actions_enabled=false。
# 测试约束 10：输出保持 safe_to_control=false。
# 测试约束 11：测试不访问 ROS graph、硬件、外部云、手机 runtime 或 raw logs。


class FieldEvidenceRerunExecutionResultAcceptanceHandoffIntakeOwnerResponseIntakeTest(unittest.TestCase):
    def _write_json(self, root: Path, name: str, payload: object) -> Path:
        # 临时 JSON 只服务离线围栏，不模拟真实现场材料。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _followup_summary(self, evidence_ref: str, status: str = "escalated") -> dict[str, object]:
        # source 使用上一轮 follow-up escalation 的安全消费面。
        return {
            "schema": followup.SUMMARY_SCHEMA,
            "schema_version": 1,
            "source": "software_proof",
            "status": status,
            "due_state": status,
            "followup_status": status,
            "capability": followup.CAPABILITY,
            "evidence_boundary": followup.BOUNDARY,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "required_materials": list(followup.REQUIRED_FOLLOWUP_MATERIALS),
            "material_status": {
                "status": "accepted",
                "accepted_materials": list(followup.REQUIRED_FOLLOWUP_MATERIALS),
                "missing_materials": [],
                "rejected_materials": [],
                "is_complete": True,
            },
            "not_proven": list(followup.NOT_PROVEN),
            "software_proof": True,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_copy": {
                "source": "software_proof",
                "status": status,
                "followup_status": status,
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "not_proven": "not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
        }

    def _owner_response(self, evidence_ref: str) -> dict[str, object]:
        # owner response 样本只给安全类别索引，不携带真实 raw field log。
        return {
            "schema": gate.OWNER_RESPONSE_PACKET_SCHEMA,
            "source": "software_proof",
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
                    "safe_to_control": False,
                    "primary_actions_enabled": False,
                }
                for name in gate.REQUIRED_OWNER_RESPONSE_MATERIALS
            },
            "not_proven": "not_proven",
            "software_proof": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_to_control": False,
        }

    def _reviewer_ack_followup_summary(self, evidence_ref: str) -> dict[str, object]:
        # bridge source 复用 reviewer-ACK followup 的脱敏 summary，不新建 owner-response mainline。
        return {
            "schema": gate.BRIDGE_SOURCE_SUMMARY_SCHEMA,
            "schema_version": 1,
            "source": "software_proof",
            "status": "not_proven",
            "capability": gate.BRIDGE_SOURCE_CAPABILITY,
            "evidence_boundary": gate.BRIDGE_SOURCE_BOUNDARY,
            "followup_status": "escalated_missing_real_material_not_proven",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "missing_required_evidence": [
                "route_elevator_field_pass",
                "verified_terminal_result",
                "true_phone_browser_or_device_proof",
                "owner response material that preserves source=software_proof and not_proven",
            ],
            "not_proven": [
                "real_owner_response_intake_completion",
                "real_route_elevator_field_pass",
                "real_phone_browser_or_device",
                "delivery_success",
            ],
            "software_proof": True,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_copy": {
                "source": "software_proof",
                "status": "not_proven",
                "followup_status": "escalated_missing_real_material_not_proven",
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "not_proven": "not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
        }

    def _build(
        self,
        root: Path,
        source_payload: dict[str, object],
        response_payload: dict[str, object],
        evidence_ref: str = "field-rerun-owner-response-101",
    ) -> tuple[dict[str, object], dict[str, object], int]:
        # 公共 helper 让 case 聚焦分类和安全边界。
        source_path = self._write_json(root, "followup-status.json", source_payload)
        response_path = self._write_json(root, "owner-response.json", response_payload)
        return gate.build_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake(
            str(source_path),
            str(response_path),
            evidence_ref,
        )

    def test_safe_owner_response_is_accepted_for_review_not_proven_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._followup_summary("field-rerun-owner-response-101"),
                self._owner_response("field-rerun-owner-response-101"),
            )

        encoded = json.dumps(summary, ensure_ascii=False)
        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], gate.SCHEMA)
        self.assertEqual(summary["schema"], gate.SUMMARY_SCHEMA)
        self.assertEqual(artifact["capability"], gate.CAPABILITY)
        self.assertEqual(artifact["evidence_boundary"], gate.EVIDENCE_BOUNDARY)
        self.assertEqual(artifact["owner_response_status"], "accepted")
        self.assertEqual(len(artifact["accepted_materials"]), len(gate.REQUIRED_OWNER_RESPONSE_MATERIALS))
        self.assertEqual(artifact["missing_materials"], [])
        self.assertEqual(artifact["rejected_materials"], [])
        self.assertEqual(artifact["blocked_materials"], [])
        self.assertIn("accepted_for_review_not_proven", encoded)
        self.assertIn("source=software_proof", artifact["boundary_note"])
        self.assertIn("no OKR percentage lift", encoded)
        self.assertEqual(artifact["pr5_thread"]["thread_id"], "PRRT_kwDOSWB9286CJ3tX")
        self.assertEqual(artifact["pr5_thread"]["state"], "unresolved")
        self.assertEqual(artifact["pr5_thread"]["material_state"], "hardware_material_pending")
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["safe_to_control"])

    def test_reviewer_ack_followup_source_outputs_owner_response_intake_bridge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._reviewer_ack_followup_summary("field-rerun-owner-response-bridge-201"),
                self._owner_response("field-rerun-owner-response-bridge-201"),
                "field-rerun-owner-response-bridge-201",
            )

        encoded = json.dumps(artifact, ensure_ascii=False)
        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["owner_response_status"], "accepted")
        self.assertEqual(artifact["bridge_capability"], gate.BRIDGE_CAPABILITY)
        self.assertEqual(artifact["evidence_boundary"], gate.BRIDGE_EVIDENCE_BOUNDARY)
        self.assertEqual(
            artifact["source_bridge"],
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status",
        )
        self.assertIn(gate.BRIDGE_CAPABILITY, encoded)
        self.assertIn(gate.BRIDGE_EVIDENCE_BOUNDARY, encoded)
        self.assertIn("source_bridge=field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status", encoded)
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])

    def test_reviewer_ack_followup_bridge_ref_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._reviewer_ack_followup_summary("field-rerun-owner-response-bridge-202"),
                self._owner_response("other-field-rerun-owner-response-bridge-202"),
                "field-rerun-owner-response-bridge-202",
            )

        self.assertEqual(artifact["owner_response_status"], "blocked")
        self.assertNotEqual(exit_code, 0)
        self.assertIn("owner_response_evidence_ref_mismatch", artifact["owner_response_reasons"])
        self.assertEqual(summary["source_bridge"], gate.BRIDGE_SOURCE_CAPABILITY)
        self.assertFalse(artifact["safe_to_control"])

    def test_missing_owner_response_or_required_material_is_missing_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._write_json(root, "followup-status.json", self._followup_summary("field-rerun-owner-response-102"))
            missing_response, missing_summary, missing_exit = gate.build_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake(
                str(source),
                str(root / "missing-owner-response.json"),
                "field-rerun-owner-response-102",
            )

        response = self._owner_response("field-rerun-owner-response-103")
        materials = response["materials"]
        self.assertIsInstance(materials, dict)
        materials.pop("true phone/browser evidence")
        with tempfile.TemporaryDirectory() as tmp:
            partial, _summary, partial_exit = self._build(
                Path(tmp),
                self._followup_summary("field-rerun-owner-response-103"),
                response,
                "field-rerun-owner-response-103",
            )

        self.assertEqual(missing_response["owner_response_status"], "missing")
        self.assertEqual(partial["owner_response_status"], "missing")
        self.assertNotEqual(missing_exit, 0)
        self.assertNotEqual(partial_exit, 0)
        self.assertIn("owner_response_json_missing", missing_response["owner_response_reasons"])
        self.assertIn("true phone/browser evidence", partial["missing_materials"])
        self.assertFalse(missing_summary["primary_actions_enabled"])

    def test_rejected_material_remains_not_proven_and_nonzero(self) -> None:
        response = self._owner_response("field-rerun-owner-response-104")
        materials = response["materials"]
        self.assertIsInstance(materials, dict)
        materials["delivery result"] = {
            "name": "delivery result",
            "status": "rejected",
            "safe_evidence_ref": "field-rerun-owner-response-104",
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_to_control": False,
        }
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._followup_summary("field-rerun-owner-response-104"),
                response,
                "field-rerun-owner-response-104",
            )

        self.assertEqual(artifact["owner_response_status"], "rejected")
        self.assertNotEqual(exit_code, 0)
        self.assertIn("delivery result", artifact["rejected_materials"])
        self.assertIn("rejected_owner_response_material_not_proven", json.dumps(summary, ensure_ascii=False))
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["safe_to_control"])

    def test_bad_source_ref_mismatch_and_unsafe_claims_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mismatch, _, mismatch_exit = self._build(
                Path(tmp),
                self._followup_summary("field-rerun-owner-response-105"),
                self._owner_response("other-field-rerun-owner-response-105"),
                "field-rerun-owner-response-105",
            )

        unsafe_response = self._owner_response("field-rerun-owner-response-106")
        unsafe_response["operator_note"] = "verified terminal result with O5 external proof and PR #5 reviewer resolved"
        with tempfile.TemporaryDirectory() as tmp:
            unsafe, unsafe_summary, unsafe_exit = self._build(
                Path(tmp),
                self._followup_summary("field-rerun-owner-response-106"),
                unsafe_response,
                "field-rerun-owner-response-106",
            )

        bad_source = self._followup_summary("field-rerun-owner-response-107", "blocked")
        with tempfile.TemporaryDirectory() as tmp:
            blocked_source, _, blocked_source_exit = self._build(
                Path(tmp),
                bad_source,
                self._owner_response("field-rerun-owner-response-107"),
                "field-rerun-owner-response-107",
            )

        encoded = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertEqual(mismatch["owner_response_status"], "blocked")
        self.assertEqual(unsafe["owner_response_status"], "blocked")
        self.assertEqual(blocked_source["owner_response_status"], "blocked")
        self.assertNotEqual(mismatch_exit, 0)
        self.assertNotEqual(unsafe_exit, 0)
        self.assertNotEqual(blocked_source_exit, 0)
        self.assertIn("owner_response_evidence_ref_mismatch", mismatch["owner_response_reasons"])
        self.assertNotIn("reviewer resolved", encoded)
        self.assertFalse(unsafe["safe_to_control"])

    def test_raw_paths_ros_serial_wave_rover_and_control_flags_block(self) -> None:
        response = self._owner_response("field-rerun-owner-response-108")
        materials = response["materials"]
        self.assertIsInstance(materials, dict)
        materials["real task record"]["summary"] = "raw artifact at /Users/m4/log with /cmd_vel /dev/ttyUSB0 WAVE ROVER"
        materials["real task record"]["safe_to_control"] = True
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._followup_summary("field-rerun-owner-response-108"),
                response,
                "field-rerun-owner-response-108",
            )

        encoded = json.dumps(summary, ensure_ascii=False)
        self.assertEqual(artifact["owner_response_status"], "blocked")
        self.assertNotEqual(exit_code, 0)
        self.assertNotIn("/Users/m4/log", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["delivery_success"])

    def test_cli_help_and_once_json_include_required_literals(self) -> None:
        help_result = subprocess.run(
            [
                sys.executable,
                str(EVIDENCE_DIR / "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.py"),
                "--help",
            ],
            check=False,
            text=True,
            capture_output=True,
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._write_json(root, "followup-status.json", self._followup_summary("field-rerun-owner-response-109"))
            response = self._write_json(root, "owner-response.json", self._owner_response("field-rerun-owner-response-109"))
            run_result = subprocess.run(
                [
                    sys.executable,
                    str(EVIDENCE_DIR / "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.py"),
                    "--followup-status-json",
                    str(source),
                    "--owner-response-json",
                    str(response),
                    "--evidence-ref",
                    "field-rerun-owner-response-109",
                    "--once-json",
                ],
                check=False,
                text=True,
                capture_output=True,
            )

        self.assertEqual(help_result.returncode, 0)
        self.assertIn("--followup-status-json", help_result.stdout)
        self.assertIn("--owner-response-json", help_result.stdout)
        self.assertEqual(run_result.returncode, 0)
        self.assertIn(gate.CAPABILITY, run_result.stdout)
        self.assertIn(gate.EVIDENCE_BOUNDARY, run_result.stdout)
        self.assertIn("source=software_proof", run_result.stdout)
        self.assertIn("delivery_success", run_result.stdout)
        self.assertIn("primary_actions_enabled", run_result.stdout)
        self.assertIn("safe_to_control", run_result.stdout)
        self.assertIn("accepted", run_result.stdout)
        self.assertIn("missing", run_result.stdout)
        self.assertIn("rejected", run_result.stdout)
        self.assertIn("blocked", run_result.stdout)


if __name__ == "__main__":
    unittest.main()
