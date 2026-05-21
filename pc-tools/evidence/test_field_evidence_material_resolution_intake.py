#!/usr/bin/env python3
"""field_evidence_material_resolution_intake gate 的围栏测试。"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools/evidence 不是常规包；测试显式加入目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_material_blocker_escalation_pack as blocker_pack  # noqa: E402
import field_evidence_material_resolution_intake as gate  # noqa: E402


# 测试约束 01：fixture 只表达 safe summary，不模拟 raw 现场材料。
# 测试约束 02：accepted 只表示 owner resolution packet 可进入复核。
# 测试约束 03：missing owner packet 必须记录 missing。
# 测试约束 04：unsafe owner material 必须记录 rejected。
# 测试约束 05：missing source 与 evidence_ref mismatch 必须 blocked。
# 测试约束 06：输出保持 source=software_proof 与 not_proven。
# 测试约束 07：输出保持 delivery_success=false。
# 测试约束 08：输出保持 primary_actions_enabled=false。
# 测试约束 09：输出保持 safe_to_control=false。
# 测试约束 10：测试不访问 ROS graph、Nav2、硬件、云或手机 runtime。


class FieldEvidenceMaterialResolutionIntakeTest(unittest.TestCase):
    def _write_json(self, root: Path, name: str, payload: object) -> Path:
        # 临时 JSON 只服务离线围栏，不代表真实现场材料。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _source_summary(self, evidence_ref: str) -> dict[str, object]:
        # source 使用 blocker escalation summary 的安全消费面。
        return {
            "schema": blocker_pack.SUMMARY_SCHEMA,
            "schema_version": 1,
            "source": "software_proof",
            "status": "not_proven",
            "capability": "field_evidence_material_blocker_escalation_pack",
            "field_evidence_material_blocker_escalation_pack_status": blocker_pack.READY_STATUS,
            "evidence_boundary": blocker_pack.EVIDENCE_BOUNDARY,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "next_required_evidence": ["real field task record", "real route completion signal"],
            "not_proven": ["not_proven"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "field_safe_copy": {
                "schema": f"{blocker_pack.SUMMARY_SCHEMA}.field_safe_copy",
                "source": "software_proof",
                "status": "not_proven",
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "same_evidence_ref_required": True,
                "not_proven": "not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
        }

    def _owner_packet(self, evidence_ref: str, decision: str = "accepted") -> dict[str, object]:
        # owner packet 是脱敏分类结果，不包含 raw 材料正文。
        return {
            "schema": "trashbot.field_evidence_material_resolution_packet.v1",
            "source": "software_proof",
            "status": "not_proven",
            "resolution_decision": decision,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "accepted_materials": ["owner safe resolution packet summary"] if decision == "accepted" else [],
            "missing_materials": ["real terminal result material"] if decision == "missing" else [],
            "rejected_materials": ["unsafe owner material"] if decision == "rejected" else [],
            "blocked_materials": ["source escalation still blocked"] if decision == "blocked" else [],
            "safe_note": "owner provided sanitized material resolution summary only",
            "not_proven": ["not_proven"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def _build(
        self,
        root: Path,
        source_payload: dict[str, object],
        packet_payload: dict[str, object],
        evidence_ref: str,
    ) -> tuple[dict[str, object], dict[str, object]]:
        # 公共 helper 让 case 聚焦状态映射和安全边界。
        source_path = self._write_json(root, "source.json", source_payload)
        packet_path = self._write_json(root, "packet.json", packet_payload)
        artifact, summary, exit_code = gate.build_field_evidence_material_resolution_intake(
            str(source_path),
            str(packet_path),
            evidence_ref,
        )
        self.assertEqual(exit_code, 0)
        return artifact, summary

    def test_accepted_packet_with_same_evidence_ref_ready_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(
                root,
                {"payload": self._source_summary("field-resolution-701")},
                self._owner_packet("field-resolution-701", "accepted"),
                "field-resolution-701",
            )

        self.assertEqual(artifact["schema"], gate.SCHEMA)
        self.assertEqual(summary["schema"], gate.SUMMARY_SCHEMA)
        self.assertEqual(artifact["decision"], "accepted")
        self.assertEqual(artifact["field_evidence_material_resolution_intake_status"], gate.READY_STATUS)
        self.assertEqual(artifact["evidence_boundary"], gate.EVIDENCE_BOUNDARY)
        self.assertTrue(artifact["same_evidence_ref_required"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(artifact["safe_to_control"])
        self.assertEqual(summary["safe_copy"]["decision"], "accepted")

    def test_missing_owner_packet_records_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_path = self._write_json(root, "source.json", self._source_summary("field-resolution-702"))
            artifact, summary, exit_code = gate.build_field_evidence_material_resolution_intake(
                str(source_path),
                str(root / "missing-owner.json"),
                "field-resolution-702",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["decision"], "missing")
        self.assertEqual(artifact["field_evidence_material_resolution_intake_status"], gate.MISSING_STATUS)
        self.assertIn("owner_resolution_json_missing", artifact["decision_reasons"])
        self.assertEqual(summary["material_categories"]["missing"], ["owner_resolution_packet_missing_required_materials"])

    def test_rejected_unsafe_material_records_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = self._owner_packet("field-resolution-703", "accepted")
            packet["safe_note"] = "delivery_success=true"
            artifact, summary = self._build(root, self._source_summary("field-resolution-703"), packet, "field-resolution-703")

        self.assertEqual(artifact["decision"], "rejected")
        self.assertEqual(artifact["field_evidence_material_resolution_intake_status"], gate.REJECTED_STATUS)
        self.assertIn("unsafe_or_success_control_claim_in_owner_resolution_packet", artifact["decision_reasons"])
        self.assertFalse(summary["safe_copy"]["delivery_success"])

    def test_missing_source_and_evidence_ref_mismatch_record_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet_path = self._write_json(root, "packet.json", self._owner_packet("field-resolution-704", "accepted"))
            missing_source, _, missing_code = gate.build_field_evidence_material_resolution_intake(
                str(root / "missing-source.json"),
                str(packet_path),
                "field-resolution-704",
            )
            mismatch, _ = self._build(
                root,
                self._source_summary("field-resolution-705"),
                self._owner_packet("field-resolution-705", "accepted"),
                "different-resolution-ref",
            )

        self.assertEqual(missing_code, 0)
        self.assertEqual(missing_source["decision"], "blocked")
        self.assertEqual(missing_source["field_evidence_material_resolution_intake_status"], gate.BLOCKED_STATUS)
        self.assertEqual(mismatch["decision"], "blocked")
        self.assertIn("source_ref:field-resolution-705!=different-resolution-ref", mismatch["decision_reasons"])

    def test_cli_prints_ready_status_for_accepted_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_path = self._write_json(root, "source.json", self._source_summary("field-resolution-706"))
            packet_path = self._write_json(root, "packet.json", self._owner_packet("field-resolution-706", "accepted"))
            result = subprocess.run(
                [
                    sys.executable,
                    str(EVIDENCE_DIR / "field_evidence_material_resolution_intake.py"),
                    "--blocker-escalation-json",
                    str(source_path),
                    "--owner-resolution-json",
                    str(packet_path),
                    "--evidence-ref",
                    "field-resolution-706",
                ],
                check=False,
                text=True,
                capture_output=True,
            )

        self.assertEqual(result.returncode, 0)
        self.assertIn(gate.READY_STATUS, result.stdout)

    def test_output_preserves_required_boundary_literals_and_no_raw_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(
                root,
                self._source_summary("field-resolution-707"),
                self._owner_packet("field-resolution-707", "accepted"),
                "field-resolution-707",
            )

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertIn("field_evidence_material_resolution_intake", encoded)
        self.assertIn("software_proof_docker_field_evidence_material_resolution_intake_gate", encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("delivery_success=false", encoded)
        self.assertIn("primary_actions_enabled=false", encoded)
        self.assertIn("safe_to_control=false", encoded)
        self.assertIn("same_evidence_ref_required", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("Traceback", encoded)
        self.assertNotIn("raw artifact", encoded)


if __name__ == "__main__":
    unittest.main()
