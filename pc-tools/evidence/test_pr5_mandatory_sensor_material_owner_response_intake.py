#!/usr/bin/env python3
"""PR #5 mandatory sensor material owner-response intake gate 围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools/evidence 不是 Python package；测试显式加入目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE_DIR))

import pr5_mandatory_sensor_material_owner_response_intake as gate  # noqa: E402


# 测试约束 01：fixture 只表达 follow-up safe summary 与 sanitized owner response。
# 测试约束 02：accepted 只是 response refs 齐全，不证明真实材料。
# 测试约束 03：missing/rejected/unsafe/blocked 都必须保持 fail-closed 旗标。
# 测试约束 04：所有输出保持 source=software_proof 和 hardware_material_pending。
# 测试约束 05：所有输出保持 safe_to_control=false。
# 测试约束 06：所有输出保持 delivery_success=false。
# 测试约束 07：所有输出保持 primary_actions_enabled=false。
# 测试约束 08：单测不访问 ROS graph、GitHub 写接口、串口、硬件或网络。


class PR5MandatorySensorMaterialOwnerResponseIntakeTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict | str) -> Path:
        # 测试只写临时 JSON，保证 gate 不依赖真实 vendor、硬件或网络。
        path = root / name
        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def followup_summary(self, evidence_ref: str, status: str = "ready_for_reviewer_followup_not_proven") -> dict:
        # 上游 fixture 模拟上一 rung safe output，不夹带 raw vendor artifact。
        return {
            "schema": "trashbot.pr5_mandatory_sensor_material_followup_escalation_status_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "capability": "pr5_mandatory_sensor_material_followup_escalation_status",
            "evidence_boundary": "software_proof_docker_pr5_mandatory_sensor_material_followup_escalation_status_gate",
            "proof_boundary": "software_proof_docker_pr5_mandatory_sensor_material_followup_escalation_status_gate",
            "status": status,
            "followup_status": status,
            "thread_id": "PRRT_kwDOSWB9286CJ3tX",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "hardware_material_status": "hardware_material_pending",
            "material_status": {
                "accepted_materials": list(gate.followup_gate.REQUIRED_MATERIALS),
                "missing_materials": [],
                "rejected_materials": [],
            },
            "safe_copy": {
                "source": "software_proof",
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "status": status,
                "followup_status": status,
                "hardware_material_pending": "hardware_material_pending",
                "not_proven": "not_proven",
                "software_proof": True,
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "not_proven": list(gate.NOT_PROVEN),
            "software_proof": True,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def owner_response(self, evidence_ref: str, status: str = "accepted", refs: list[str] | None = None) -> dict:
        # response packet 只提交安全引用类别，不提交真实传感器材料正文。
        return {
            "schema": gate.RESPONSE_SCHEMA,
            "schema_version": 1,
            "source": "software_proof",
            "owner_id": "hardware-owner-a",
            "owner_role": "Hardware Infra Engineer",
            "response_status": status,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "material_refs": list(refs if refs is not None else gate.REQUIRED_RESPONSE_REFS),
            "missing_refs": [],
            "rejected_refs": [],
            "reviewer_next_step": "review_safe_owner_response_refs_not_proven",
            "safe_notes": ["owner response refs are metadata only"],
            "hardware_material_status": "hardware_material_pending",
            "not_proven": "not_proven",
            "software_proof": True,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def build(
        self,
        root: Path,
        source_payload: dict | str,
        response_payload: dict | str,
        evidence_ref: str = "pr5-owner-response-001",
    ) -> tuple[dict, dict, int]:
        # 公共 helper 让 case 聚焦 decision、evidence_ref 和 fail-closed 规则。
        source_path = self.write_json(root, "followup_summary.json", source_payload)
        response_path = self.write_json(root, "owner_response.json", response_payload)
        return gate.build_pr5_mandatory_sensor_material_owner_response_intake(
            str(source_path),
            str(response_path),
            evidence_ref,
        )

    def test_accepted_owner_response_keeps_safe_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary, exit_code = self.build(
                root,
                {"payload": {"summary": self.followup_summary("pr5-owner-response-001")}},
                {"payload": {"safe_owner_response_packet": self.owner_response("pr5-owner-response-001")}},
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], gate.SCHEMA)
        self.assertEqual(summary["schema"], gate.SUMMARY_SCHEMA)
        self.assertEqual(artifact["capability"], gate.CAPABILITY)
        self.assertEqual(artifact["decision"], "accepted")
        self.assertIn("software_proof_docker_pr5_mandatory_sensor_material_owner_response_intake_gate", artifact["boundary_note"])
        self.assertIn("docs/vendor/VENDOR_INDEX.md", artifact["boundary_note"])
        self.assertEqual(summary["hardware_material_status"], "hardware_material_pending")
        self.assertIn("not_proven", json.dumps(summary["safe_copy"], ensure_ascii=False))
        self.assertEqual(summary["safe_owner_response_packet"]["owner_id"], "hardware-owner-a")
        self.assertFalse(artifact["safe_to_control"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_missing_owner_response_refs_returns_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary, exit_code = self.build(
                root,
                self.followup_summary("pr5-owner-response-002"),
                self.owner_response("pr5-owner-response-002", "missing", list(gate.REQUIRED_RESPONSE_REFS[:-1])),
                "pr5-owner-response-002",
            )

        self.assertEqual(artifact["decision"], "missing")
        self.assertNotEqual(exit_code, 0)
        self.assertIn("owner_response_missing_required_material_refs", artifact["decision_reasons"])
        self.assertIn("PR #5 reviewer follow-up", "\n".join(summary["material_status"]["missing_refs"]))
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(artifact["primary_actions_enabled"])

    def test_rejected_owner_response_refs_returns_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            response = self.owner_response("pr5-owner-response-003", "rejected")
            response["rejected_refs"] = ["ToF SKU/source/receipt/procurement material owner response"]
            artifact, summary, exit_code = self.build(
                root,
                self.followup_summary("pr5-owner-response-003"),
                response,
                "pr5-owner-response-003",
            )

        self.assertEqual(artifact["decision"], "rejected")
        self.assertNotEqual(exit_code, 0)
        self.assertIn("owner_response_contains_rejected_material_refs", artifact["decision_reasons"])
        self.assertIn("ToF", "\n".join(summary["material_status"]["rejected_refs"]))
        self.assertFalse(summary["delivery_success"])

    def test_missing_source_or_owner_response_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            response_path = self.write_json(root, "owner_response.json", self.owner_response("pr5-owner-response-004"))
            missing_source, missing_source_summary, missing_source_exit = gate.build_pr5_mandatory_sensor_material_owner_response_intake(
                str(root / "missing_followup_summary.json"),
                str(response_path),
                "pr5-owner-response-004",
            )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_path = self.write_json(root, "followup_summary.json", self.followup_summary("pr5-owner-response-005"))
            missing_response, missing_response_summary, missing_response_exit = gate.build_pr5_mandatory_sensor_material_owner_response_intake(
                str(source_path),
                str(root / "missing_owner_response.json"),
                "pr5-owner-response-005",
            )

        self.assertEqual(missing_source["decision"], "blocked")
        self.assertEqual(missing_response["decision"], "blocked")
        self.assertNotEqual(missing_source_exit, 0)
        self.assertNotEqual(missing_response_exit, 0)
        self.assertIn("followup_summary_json_missing", missing_source["decision_reasons"])
        self.assertIn("owner_response_json_missing", missing_response["decision_reasons"])
        self.assertFalse(missing_source_summary["safe_to_control"])
        self.assertFalse(missing_response_summary["primary_actions_enabled"])

    def test_evidence_ref_mismatch_is_blocked_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary, exit_code = self.build(
                root,
                self.followup_summary("pr5-owner-response-006"),
                self.owner_response("different-pr5-owner-response-006"),
                "pr5-owner-response-006",
            )

        self.assertEqual(artifact["decision"], "blocked")
        self.assertNotEqual(exit_code, 0)
        self.assertIn("source_response_evidence_ref_mismatch", artifact["decision_reasons"])
        self.assertEqual(summary["safe_copy"]["decision"], "blocked")

    def test_unsafe_raw_control_hardware_and_pr_resolution_claims_return_unsafe(self) -> None:
        unsafe_notes = (
            {"raw_artifact": {"body": "complete artifact body"}},
            {"safe_notes": ["Authorization: Bearer abc /cmd_vel /dev/ttyUSB0"]},
            {"safe_notes": ["serial_port=/dev/ttyAMA0 baudrate=115200"]},
            {"safe_notes": ["WAVE ROVER wheel_diameter parameter checksum copied"]},
            {"safe_notes": ["delivery_success=true and primary_actions_enabled=true"]},
            {"safe_notes": ["real HIL passed and hil_pass copy attached"]},
            {"safe_notes": ["2D LiDAR installed and ToF wired"]},
            {"reviewer_next_step": "PRRT_kwDOSWB9286CJ3tX resolved by reviewer"},
        )
        for idx, patch in enumerate(unsafe_notes, start=7):
            evidence_ref = f"pr5-owner-response-0{idx}"
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                response = self.owner_response(evidence_ref)
                response.update(patch)
                artifact, summary, exit_code = self.build(
                    root,
                    self.followup_summary(evidence_ref),
                    response,
                    evidence_ref,
                )

            encoded = json.dumps(artifact, ensure_ascii=False)
            self.assertEqual(artifact["decision"], "unsafe")
            self.assertNotEqual(exit_code, 0)
            self.assertFalse(artifact["delivery_success"])
            self.assertFalse(summary["primary_actions_enabled"])
            self.assertNotIn("Bearer abc", encoded)
            self.assertNotIn("/cmd_vel", encoded)
            self.assertNotIn("/dev/ttyUSB0", encoded)
            self.assertNotIn("/dev/ttyAMA0", encoded)
            self.assertNotIn("115200", encoded)

    def test_unsupported_or_blocked_source_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsupported, _, unsupported_exit = self.build(
                root,
                self.followup_summary("pr5-owner-response-015", "blocked"),
                self.owner_response("pr5-owner-response-015"),
                "pr5-owner-response-015",
            )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad_source = self.followup_summary("pr5-owner-response-016")
            bad_source["schema"] = "trashbot.some_other_schema.v1"
            nonready, _, nonready_exit = self.build(
                root,
                bad_source,
                self.owner_response("pr5-owner-response-016"),
                "pr5-owner-response-016",
            )

        self.assertEqual(unsupported["decision"], "blocked")
        self.assertEqual(nonready["decision"], "blocked")
        self.assertNotEqual(unsupported_exit, 0)
        self.assertNotEqual(nonready_exit, 0)
        self.assertIn("source_followup_escalation_status_not_ready", unsupported["decision_reasons"])
        self.assertIn("missing_or_unsupported_pr5_mandatory_sensor_material_followup_escalation_status", nonready["decision_reasons"])


if __name__ == "__main__":
    unittest.main()
