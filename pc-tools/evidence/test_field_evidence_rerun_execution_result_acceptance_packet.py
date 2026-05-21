#!/usr/bin/env python3
"""field_evidence_rerun_execution_result_acceptance_packet 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools/evidence 不是 package；测试显式加入目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_rerun_execution_result_acceptance_packet as gate  # noqa: E402


# 测试约束 01：fixture 只表达 safe review handoff 和 safe material index。
# 测试约束 02：ready verdict 只证明验收包可人工复核，不证明现场通过。
# 测试约束 03：八类 required_materials 必须全部同一 evidence_ref。
# 测试约束 04：task record、Nav2、fixed-route、电梯、dropoff/cancel 和 delivery result 都只是材料类别。
# 测试约束 05：true phone/browser evidence 只是材料类别，不证明真实手机通过。
# 测试约束 06：缺 packet、缺材料、rejected material 必须 fail closed。
# 测试约束 07：same evidence_ref mismatch 必须 fail closed。
# 测试约束 08：raw path、ROS topic、checksum、serial/UART/WAVE ROVER 必须阻断。
# 测试约束 09：delivery_success=true、safe_to_control=true 必须拒绝。
# 测试约束 10：wrapper/nested JSON 必须可消费。
# 测试约束 11：所有输出保持 safe_to_control=false。
# 测试约束 12：所有输出保持 delivery_success=false。
# 测试约束 13：所有输出保持 primary_actions_enabled=false。
# 测试约束 14：单测不访问 ROS graph、硬件、外部云或手机 runtime。


class FieldEvidenceRerunExecutionResultAcceptancePacketTest(unittest.TestCase):
    def _handoff(self, evidence_ref: str = "ev-acceptance-001", status: str = gate.READY_HANDOFF_STATUS) -> dict[str, object]:
        # handoff fixture 沿用上一轮 review_handoff safe summary contract。
        return {
            "schema": "trashbot.field_evidence_rerun_execution_result_review_handoff_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_execution_result_review_handoff_gate",
            "status": status,
            "handoff_status": status,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "same_evidence_ref_status": "matched",
            "owner_handoff": {"owner": "Autonomy Algorithm Engineer", "action": "fixture_safe_handoff"},
            "next_required_real_materials": list(gate.REQUIRED_MATERIALS),
            "not_proven": list(gate.NOT_PROVEN),
            "safe_copy": {
                "source": "software_proof",
                "status": status,
                "handoff_status": status,
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "not_proven": "not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def _packet(
        self,
        evidence_ref: str = "ev-acceptance-001",
        accepted: list[str] | None = None,
        **extra: object,
    ) -> dict[str, object]:
        # acceptance packet 是脱敏索引，不包含真实 task record 或 runtime log 正文。
        accepted_materials = accepted if accepted is not None else list(gate.REQUIRED_MATERIALS)
        payload: dict[str, object] = {
            "schema": "trashbot.field_evidence_rerun_execution_result_acceptance_packet_input.v1",
            "source": "software_proof",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "accepted_materials": accepted_materials,
            "missing_materials": [],
            "rejected_materials": [],
            "blocked_materials": [],
            "material_evidence_refs": {name: evidence_ref for name in accepted_materials},
            "owner_next_steps": ["fixture safe field owner acceptance review"],
            "safe_copy": {
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "accepted_materials": accepted_materials,
                "not_proven": "not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        return payload

    def _write(self, root: Path, name: str, payload: object) -> str:
        # 临时文件只服务 JSON 输入输出围栏，不模拟真实材料路径。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return str(path)

    def test_complete_packet_builds_acceptance_review_readiness_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff_path = self._write(root, "handoff.json", self._handoff())
            packet_path = self._write(root, "packet.json", self._packet())

            artifact, summary, exit_code = gate.build_field_evidence_rerun_execution_result_acceptance_packet(
                handoff_path,
                packet_path,
                "ev-acceptance-001",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.field_evidence_rerun_execution_result_acceptance_packet.v1")
        self.assertEqual(summary["schema"], "trashbot.field_evidence_rerun_execution_result_acceptance_packet_summary.v1")
        self.assertEqual(summary["evidence_boundary"], "software_proof_docker_field_evidence_rerun_execution_result_acceptance_packet_gate")
        self.assertEqual(summary["acceptance_verdict"], "ready_for_field_owner_acceptance_review_not_proven")
        self.assertEqual(summary["missing_materials"], [])
        self.assertIn("task_record", summary["required_materials"])
        self.assertIn("nav2_fixed_route_runtime_log", summary["required_materials"])
        self.assertIn("route_completion_signal", summary["required_materials"])
        self.assertIn("elevator_evidence", summary["required_materials"])
        self.assertIn("dropoff_cancel_completion", summary["required_materials"])
        self.assertIn("delivery_result", summary["required_materials"])
        self.assertIn("true_phone_browser_evidence", summary["required_materials"])
        self.assertIn("real_delivery_success", summary["not_proven"])
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_missing_packet_missing_material_and_non_ready_handoff_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff_path = self._write(root, "handoff.json", self._handoff())
            missing_packet_artifact, missing_packet_summary, _ = gate.build_field_evidence_rerun_execution_result_acceptance_packet(
                handoff_path,
                str(root / "missing_packet.json"),
                "ev-acceptance-001",
            )
            partial_path = self._write(root, "partial.json", self._packet(accepted=list(gate.REQUIRED_MATERIALS[:-1])))
            partial_artifact, partial_summary, _ = gate.build_field_evidence_rerun_execution_result_acceptance_packet(
                handoff_path,
                partial_path,
                "ev-acceptance-001",
            )
            blocked_handoff_path = self._write(root, "blocked_handoff.json", self._handoff(status="needs_field_owner_material_backfill_for_execution_result_review_handoff_not_proven"))
            packet_path = self._write(root, "packet.json", self._packet())
            blocked_artifact, blocked_summary, _ = gate.build_field_evidence_rerun_execution_result_acceptance_packet(
                blocked_handoff_path,
                packet_path,
                "ev-acceptance-001",
            )

        self.assertEqual(missing_packet_artifact["acceptance_verdict"], "blocked_missing_acceptance_packet")
        self.assertEqual(missing_packet_summary["safe_to_control"], False)
        self.assertEqual(partial_artifact["acceptance_verdict"], "needs_material_backfill")
        self.assertIn("diagnostics_mobile_safe_summary", partial_summary["missing_materials"])
        self.assertEqual(blocked_artifact["acceptance_verdict"], "needs_material_backfill")
        self.assertIn("source_handoff_not_ready", blocked_summary["status_reasons"][0])

    def test_evidence_ref_mismatch_unsafe_material_and_success_claim_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff_path = self._write(root, "handoff.json", self._handoff("ev-acceptance-002"))
            packet_mismatch_path = self._write(root, "packet_mismatch.json", self._packet("other-ref"))
            mismatch_artifact, _mismatch_summary, _ = gate.build_field_evidence_rerun_execution_result_acceptance_packet(
                handoff_path,
                packet_mismatch_path,
                "ev-acceptance-002",
            )
            unsafe = self._packet("ev-acceptance-002")
            unsafe["owner_next_steps"] = ["raw artifact /Users/m4/raw.json /cmd_vel /dev/ttyUSB0 baudrate=115200 checksum=abcdef123456"]
            unsafe_path = self._write(root, "unsafe.json", unsafe)
            unsafe_artifact, unsafe_summary, _ = gate.build_field_evidence_rerun_execution_result_acceptance_packet(
                handoff_path,
                unsafe_path,
                "ev-acceptance-002",
            )
            success = self._packet("ev-acceptance-002", delivery_success=True, primary_actions_enabled=True, safe_to_control=True)
            success_path = self._write(root, "success.json", success)
            success_artifact, success_summary, _ = gate.build_field_evidence_rerun_execution_result_acceptance_packet(
                handoff_path,
                success_path,
                "ev-acceptance-002",
            )

        encoded = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertEqual(mismatch_artifact["acceptance_verdict"], "blocked_evidence_ref_mismatch")
        self.assertEqual(unsafe_artifact["acceptance_verdict"], "blocked_unsafe_material")
        self.assertNotIn("/Users/m4", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("abcdef123456", encoded)
        self.assertEqual(success_artifact["acceptance_verdict"], "rejected_success_claim")
        self.assertFalse(success_summary["delivery_success"])
        self.assertFalse(success_summary["primary_actions_enabled"])
        self.assertFalse(success_summary["safe_to_control"])

    def test_nested_handoff_and_materials_object_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff_path = self._write(root, "wrapper.json", {"payload": {"summary": self._handoff("ev-wrapper-001")}})
            packet = self._packet("ev-wrapper-001", accepted=[])
            packet["materials"] = {
                name: {"status": "provided", "evidence_ref": "ev-wrapper-001"}
                for name in gate.REQUIRED_MATERIALS
            }
            packet_path = self._write(root, "materials.json", {"data": {"acceptance_packet": packet}})

            artifact, summary, exit_code = gate.build_field_evidence_rerun_execution_result_acceptance_packet(
                handoff_path,
                packet_path,
                "",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["acceptance_verdict"], "ready_for_field_owner_acceptance_review_not_proven")
        self.assertEqual(summary["safe_evidence_ref"], "ev-wrapper-001")
        self.assertEqual(set(summary["accepted_materials"]), set(gate.REQUIRED_MATERIALS))


if __name__ == "__main__":
    unittest.main()
