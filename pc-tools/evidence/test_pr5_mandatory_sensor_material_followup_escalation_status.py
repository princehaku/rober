#!/usr/bin/env python3
"""PR #5 mandatory sensor material follow-up escalation status gate 围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools/evidence 不是 Python package；测试显式加入目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE_DIR))

import pr5_mandatory_sensor_material_followup_escalation_status as gate  # noqa: E402


# 测试约束 01：fixture 只表达 source-alignment safe summary 与 safe follow-up packet。
# 测试约束 02：pending/overdue/escalated/ready 只表示跟进状态，不证明真实材料。
# 测试约束 03：缺 source、缺材料、mismatch、unsafe 都必须 blocked。
# 测试约束 04：所有输出保持 source=software_proof 和 hardware_material_pending。
# 测试约束 05：所有输出保持 safe_to_control=false。
# 测试约束 06：所有输出保持 delivery_success=false。
# 测试约束 07：所有输出保持 primary_actions_enabled=false。
# 测试约束 08：单测不访问 ROS graph、GitHub 写接口、串口、硬件或网络。


class PR5MandatorySensorMaterialFollowupEscalationStatusTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict | str) -> Path:
        # 测试只写临时 JSON，保证 gate 不依赖真实 vendor、硬件或网络。
        path = root / name
        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def source_alignment_summary(self, evidence_ref: str, ready: bool = True) -> dict:
        # 上游 fixture 模拟 source-alignment safe output，不夹带 raw vendor artifact。
        status = "ready_for_pr5_mandatory_sensor_source_alignment_not_proven" if ready else "blocked_missing_source"
        return {
            "schema": "trashbot.pr5_mandatory_sensor_source_alignment_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "capability": "pr5_mandatory_sensor_source_alignment",
            "evidence_boundary": "software_proof_docker_pr5_mandatory_sensor_source_alignment_gate",
            "proof_boundary": "software_proof_docker_pr5_mandatory_sensor_source_alignment_gate",
            "alignment_status": status,
            "status": status,
            "thread_id": "PRRT_kwDOSWB9286CJ3tX",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "hardware_material_status": "hardware_material_pending",
            "missing_materials": list(gate.REQUIRED_MATERIALS),
            "safe_copy": {
                "source": "software_proof",
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "alignment_status": status,
                "status": status,
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

    def followup_packet(self, evidence_ref: str, status: str = "pending", materials: list[str] | None = None) -> dict:
        # packet 只确认安全类别纳入跟进，不提交真实传感器材料正文。
        return {
            "schema": gate.POLICY_SCHEMA,
            "schema_version": 1,
            "source": "software_proof",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "followup_status": status,
            "accepted_materials": list(materials if materials is not None else gate.REQUIRED_MATERIALS),
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
        packet_payload: dict | str,
        evidence_ref: str = "pr5-followup-001",
    ) -> tuple[dict, dict, int]:
        # 公共 helper 让 case 聚焦 status、evidence_ref 和 fail-closed 规则。
        source_path = self.write_json(root, "source_alignment.json", source_payload)
        packet_path = self.write_json(root, "followup_packet.json", packet_payload)
        return gate.build_pr5_mandatory_sensor_material_followup_escalation_status(
            str(source_path),
            str(packet_path),
            evidence_ref,
        )

    def test_pending_followup_status_keeps_safe_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary, exit_code = self.build(
                root,
                {"payload": {"summary": self.source_alignment_summary("pr5-followup-001")}},
                {"payload": {"safe_material_followup_packet": self.followup_packet("pr5-followup-001", "pending")}},
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], gate.SCHEMA)
        self.assertEqual(summary["schema"], gate.SUMMARY_SCHEMA)
        self.assertEqual(artifact["capability"], gate.CAPABILITY)
        self.assertEqual(artifact["followup_status"], "pending")
        self.assertIn("overdue", artifact["allowed_followup_statuses"])
        self.assertIn("ready_for_reviewer_followup_not_proven", artifact["allowed_followup_statuses"])
        self.assertIn("source=software_proof", artifact["boundary_note"])
        self.assertEqual(summary["hardware_material_status"], "hardware_material_pending")
        self.assertIn("not_proven", json.dumps(summary["safe_copy"], ensure_ascii=False))
        self.assertFalse(artifact["safe_to_control"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_overdue_escalated_and_ready_statuses_remain_not_proven(self) -> None:
        for idx, status in enumerate(("overdue", "escalated", "ready_for_reviewer_followup_not_proven"), start=2):
            evidence_ref = f"pr5-followup-00{idx}"
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                artifact, summary, exit_code = self.build(
                    root,
                    self.source_alignment_summary(evidence_ref),
                    self.followup_packet(evidence_ref, status),
                    evidence_ref,
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(artifact["followup_status"], status)
            self.assertEqual(summary["followup_status"], status)
            self.assertIn("software_proof", json.dumps(artifact, ensure_ascii=False))
            self.assertIn("hardware_material_pending", json.dumps(summary, ensure_ascii=False))
            self.assertFalse(artifact["delivery_success"])
            self.assertFalse(summary["primary_actions_enabled"])

    def test_missing_source_alignment_and_missing_material_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet_path = self.write_json(root, "followup_packet.json", self.followup_packet("pr5-followup-005"))
            missing, missing_summary, missing_exit = gate.build_pr5_mandatory_sensor_material_followup_escalation_status(
                str(root / "missing_source_alignment.json"),
                str(packet_path),
                "pr5-followup-005",
            )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            blocked, blocked_summary, blocked_exit = self.build(
                root,
                self.source_alignment_summary("pr5-followup-006"),
                self.followup_packet("pr5-followup-006", "pending", list(gate.REQUIRED_MATERIALS[:-1])),
                "pr5-followup-006",
            )

        self.assertEqual(missing["followup_status"], "blocked")
        self.assertEqual(blocked["followup_status"], "blocked")
        self.assertNotEqual(missing_exit, 0)
        self.assertNotEqual(blocked_exit, 0)
        self.assertIn("source_alignment_json_missing", missing["followup_reasons"])
        self.assertIn("material_followup_packet_missing_required_materials", blocked["followup_reasons"])
        self.assertIn("PR #5 reviewer follow-up", "\n".join(blocked_summary["material_status"]["missing_materials"]))
        self.assertFalse(missing_summary["safe_to_control"])
        self.assertFalse(blocked["primary_actions_enabled"])

    def test_missing_material_followup_packet_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_path = self.write_json(root, "source_alignment.json", self.source_alignment_summary("pr5-followup-016"))
            artifact, summary, exit_code = gate.build_pr5_mandatory_sensor_material_followup_escalation_status(
                str(source_path),
                str(root / "missing_followup_packet.json"),
                "pr5-followup-016",
            )

        self.assertEqual(artifact["followup_status"], "blocked")
        self.assertNotEqual(exit_code, 0)
        self.assertIn("material_followup_json_missing", artifact["followup_reasons"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_evidence_ref_mismatch_is_blocked_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary, exit_code = self.build(
                root,
                self.source_alignment_summary("pr5-followup-007"),
                self.followup_packet("different-pr5-followup-007"),
                "pr5-followup-007",
            )

        self.assertEqual(artifact["followup_status"], "blocked")
        self.assertNotEqual(exit_code, 0)
        self.assertIn("source_packet_evidence_ref_mismatch", artifact["followup_reasons"])
        self.assertEqual(summary["safe_copy"]["followup_status"], "blocked")

    def test_unsafe_success_hil_installed_sensor_and_pr_resolution_reject(self) -> None:
        unsafe_notes = (
            "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 raw artifact",
            "delivery_success=true and primary_actions_enabled=true",
            "real HIL passed for the sensor rig",
            "2D LiDAR installed and ToF wired",
            "Objective 5 external proof accepted",
            "PRRT_kwDOSWB9286CJ3tX resolved by reviewer",
        )
        for idx, note in enumerate(unsafe_notes, start=8):
            evidence_ref = f"pr5-followup-0{idx}"
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                packet = self.followup_packet(evidence_ref)
                packet["operator_note"] = note
                artifact, summary, exit_code = self.build(
                    root,
                    self.source_alignment_summary(evidence_ref),
                    packet,
                    evidence_ref,
                )

            encoded = json.dumps(artifact, ensure_ascii=False)
            self.assertEqual(artifact["followup_status"], "blocked")
            self.assertNotEqual(exit_code, 0)
            self.assertFalse(artifact["delivery_success"])
            self.assertFalse(summary["primary_actions_enabled"])
            self.assertNotIn("Bearer abc", encoded)
            self.assertNotIn("/cmd_vel", encoded)
            self.assertNotIn("/dev/ttyUSB0", encoded)

    def test_unsupported_or_nonready_source_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsupported, _, unsupported_exit = self.build(
                root,
                self.source_alignment_summary("pr5-followup-014"),
                self.followup_packet("pr5-followup-014", "done"),
                "pr5-followup-014",
            )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nonready, _, nonready_exit = self.build(
                root,
                self.source_alignment_summary("pr5-followup-015", ready=False),
                self.followup_packet("pr5-followup-015", "pending"),
                "pr5-followup-015",
            )

        self.assertEqual(unsupported["followup_status"], "blocked")
        self.assertEqual(nonready["followup_status"], "blocked")
        self.assertNotEqual(unsupported_exit, 0)
        self.assertNotEqual(nonready_exit, 0)
        self.assertIn("unsupported_or_blocked_followup_status", unsupported["followup_reasons"])
        self.assertIn("source_alignment_not_ready_not_proven", nonready["followup_reasons"])


if __name__ == "__main__":
    unittest.main()
