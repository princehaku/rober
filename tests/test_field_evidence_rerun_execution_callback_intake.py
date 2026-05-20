#!/usr/bin/env python3
"""field_evidence_rerun_execution_callback_intake 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools 不是 Python package；测试显式加入 evidence 目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "pc-tools" / "evidence"
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_rerun_execution_callback_intake as gate  # noqa: E402


# 测试约束 01：fixture 只表达 safe execution pack，不创建真实材料目录。
# 测试约束 02：ready case 只证明 metadata callback intake 可分类复账。
# 测试约束 03：accepted 全齐也不能解释成真实 field rerun 或 Nav2 proof。
# 测试约束 04：缺 execution pack 必须 fail closed。
# 测试约束 05：缺 callback packet 必须 fail closed。
# 测试约束 06：unsupported schema/boundary 必须 fail closed。
# 测试约束 07：non-ready execution pack 不能被 callback packet 提升。
# 测试约束 08：same evidence_ref mismatch 必须 fail closed。
# 测试约束 09：unknown category 和非法 classification 必须 fail closed。
# 测试约束 10：missing/rejected/blocked materials 不能 ready。
# 测试约束 11：raw path、ROS topic、checksum 必须被阻断和脱敏。
# 测试约束 12：safe_to_control=true、delivery_success=true 必须被阻断。
# 测试约束 13：wrapper/nested artifact/summary JSON 必须可消费。
# 测试约束 14：所有输出保留 safe_to_control=false。
# 测试约束 15：单测不访问 ROS graph、硬件、外部云或手机 runtime。


class FieldEvidenceRerunExecutionCallbackIntakeTest(unittest.TestCase):
    def _execution_pack(
        self,
        evidence_ref: str = "ev-field-exec-callback-001",
        execution_pack_status: str = "ready_for_field_evidence_rerun_execution_pack_not_proven",
        **extra: object,
    ) -> dict[str, object]:
        # source fixture 沿用 execution_pack 的 safe summary contract。
        payload: dict[str, object] = {
            "schema": "trashbot.field_evidence_rerun_execution_pack_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_execution_pack_gate",
            "status": execution_pack_status,
            "execution_pack_status": execution_pack_status,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "same_evidence_ref_status": "matched",
            "material_templates": [
                {"material_type": "field_task_record", "safe_evidence_ref": evidence_ref},
                {"material_type": "nav2_fixed_route_runtime_log", "safe_evidence_ref": evidence_ref},
                {"material_type": "route_completion_signal", "safe_evidence_ref": evidence_ref},
                {"material_type": "elevator_door_floor_human_assist", "safe_evidence_ref": evidence_ref},
                {"material_type": "dropoff_cancel_completion", "safe_evidence_ref": evidence_ref},
                {"material_type": "delivery_result", "safe_evidence_ref": evidence_ref},
                {"material_type": "real_phone_browser_evidence", "safe_evidence_ref": evidence_ref},
            ],
            "owner_handoff": {
                "owner": "Autonomy Algorithm Engineer",
                "safe_evidence_ref": evidence_ref,
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "next_required_evidence": [f"Collect same-evidence-ref field materials for evidence_ref={evidence_ref}."],
            "safe_copy": {
                "source": "software_proof",
                "status": execution_pack_status,
                "execution_pack_status": execution_pack_status,
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "same_evidence_ref_status": "matched",
                "not_proven": "not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "not_proven": list(gate.NOT_PROVEN),
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        return payload

    def _packet(
        self,
        evidence_ref: str = "ev-field-exec-callback-001",
        classification: str = "accepted",
        **extra: object,
    ) -> dict[str, object]:
        # packet fixture 只放 owner-safe 分类，不包含 raw artifact 或材料正文。
        payload: dict[str, object] = {
            "schema": "trashbot.field_evidence_rerun_execution_callback_packet.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_execution_callback_intake_gate",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "materials": {
                category: {"classification": classification, "reason": f"{category} owner-safe callback classification"}
                for category in gate.REQUIRED_MATERIAL_CATEGORIES
            },
            "not_proven": list(gate.NOT_PROVEN),
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        return payload

    def _artifact(self, summary: dict[str, object]) -> dict[str, object]:
        # artifact fixture 携带 nested summary；callback intake 应优先消费 summary。
        return {
            "schema": "trashbot.field_evidence_rerun_execution_pack.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_execution_pack_gate",
            "execution_pack_status": summary["execution_pack_status"],
            "safe_evidence_ref": summary["safe_evidence_ref"],
            "evidence_ref": summary["evidence_ref"],
            "same_evidence_ref_required": True,
            "same_evidence_ref_status": "matched",
            "field_evidence_rerun_execution_pack_summary": summary,
            "robot_diagnostics_field_evidence_rerun_execution_pack_summary": summary,
            "robot_diagnostics_summary": summary,
            "mobile_readonly_summary": summary,
            "not_proven": list(gate.NOT_PROVEN),
            "non_access_scope": ["serial_uart", "wave_rover", "ros_graph"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def _write(self, root: Path, name: str, payload: object) -> str:
        # 临时文件只服务 JSON 输入输出围栏，不模拟真实现场材料路径。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return str(path)

    def test_ready_execution_pack_and_callback_packet_map_to_intake_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack_path = self._write(root, "execution_pack.json", self._execution_pack())
            packet_path = self._write(root, "packet.json", self._packet())

            artifact, summary, exit_code = gate.build_field_evidence_rerun_execution_callback_intake(
                pack_path,
                packet_path,
                "ev-field-exec-callback-001",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.field_evidence_rerun_execution_callback_intake.v1")
        self.assertEqual(summary["schema"], "trashbot.field_evidence_rerun_execution_callback_intake_summary.v1")
        self.assertEqual(summary["evidence_boundary"], "software_proof_docker_field_evidence_rerun_execution_callback_intake_gate")
        self.assertEqual(summary["callback_intake_status"], "ready_for_field_evidence_rerun_execution_callback_intake_not_proven")
        self.assertEqual(summary["source_execution_pack_status"], "ready_for_field_evidence_rerun_execution_pack_not_proven")
        self.assertEqual(summary["same_evidence_ref_status"], "matched")
        self.assertEqual(summary["accepted_materials"], list(gate.REQUIRED_MATERIAL_CATEGORIES))
        self.assertEqual(summary["missing_materials"], [])
        self.assertIn("owner_handoff", summary)
        self.assertIn("next_required_evidence", summary)
        self.assertIn("safe_copy", summary)
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("real_phone_browser_evidence", summary["not_proven"])

    def test_missing_inputs_unsupported_source_and_non_ready_pack_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet_path = self._write(root, "packet.json", self._packet())
            good_pack = self._write(root, "pack.json", self._execution_pack())
            wrong_pack = self._write(root, "wrong.json", self._execution_pack(schema="trashbot.other.v1"))
            blocked_pack = self._write(root, "blocked.json", self._execution_pack(execution_pack_status="needs_field_evidence_rerun_execution_pack_backfill"))

            missing_source, _missing_summary, _ = gate.build_field_evidence_rerun_execution_callback_intake(str(root / "missing.json"), packet_path, "")
            missing_packet, _packet_summary, _ = gate.build_field_evidence_rerun_execution_callback_intake(good_pack, str(root / "missing_packet.json"), "")
            unsupported, _unsupported_summary, _ = gate.build_field_evidence_rerun_execution_callback_intake(wrong_pack, packet_path, "")
            not_ready, _not_ready_summary, _ = gate.build_field_evidence_rerun_execution_callback_intake(blocked_pack, packet_path, "")

        self.assertEqual(missing_source["callback_intake_status"], "blocked_unsupported_field_evidence_rerun_execution_callback_intake_source")
        self.assertEqual(missing_packet["callback_intake_status"], "blocked_unsupported_field_evidence_rerun_execution_callback_intake_source")
        self.assertEqual(unsupported["callback_intake_status"], "blocked_unsupported_field_evidence_rerun_execution_callback_intake_source")
        self.assertEqual(not_ready["callback_intake_status"], "blocked_field_evidence_rerun_execution_pack_not_ready")

    def test_mismatch_weak_same_ref_unknown_category_and_invalid_classification_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack_path = self._write(root, "pack.json", self._execution_pack())
            packet_other = self._write(root, "packet_other.json", self._packet("other-ref"))
            weak_packet = self._write(root, "weak_packet.json", self._packet(same_evidence_ref_required="true"))
            unknown_packet = self._packet()
            unknown_packet["materials"] = {"unknown_material": {"classification": "accepted"}}
            unknown_path = self._write(root, "unknown.json", unknown_packet)
            invalid_packet = self._packet()
            invalid_packet["materials"] = {"task_record": {"classification": "maybe"}}
            invalid_path = self._write(root, "invalid.json", invalid_packet)

            mismatch, _mismatch_summary, _ = gate.build_field_evidence_rerun_execution_callback_intake(pack_path, packet_other, "ev-field-exec-callback-001")
            weak, _weak_summary, _ = gate.build_field_evidence_rerun_execution_callback_intake(pack_path, weak_packet, "")
            unknown, _unknown_summary, _ = gate.build_field_evidence_rerun_execution_callback_intake(pack_path, unknown_path, "")
            invalid, _invalid_summary, _ = gate.build_field_evidence_rerun_execution_callback_intake(pack_path, invalid_path, "")

        self.assertEqual(mismatch["callback_intake_status"], "evidence_ref_mismatch_field_evidence_rerun_execution_callback_intake_blocked")
        self.assertEqual(weak["callback_intake_status"], "evidence_ref_mismatch_field_evidence_rerun_execution_callback_intake_blocked")
        self.assertEqual(unknown["callback_intake_status"], "blocked_field_evidence_rerun_execution_callback_materials_not_ready")
        self.assertIn("unsupported_material_category:unknown_material", unknown["status_reasons"])
        self.assertEqual(invalid["callback_intake_status"], "blocked_field_evidence_rerun_execution_callback_materials_not_ready")
        self.assertIn("unsupported_classification:task_record:maybe", invalid["status_reasons"])

    def test_missing_rejected_and_blocked_categories_stay_not_ready(self) -> None:
        packet = self._packet()
        packet["materials"] = {
            "task_record": {"classification": "accepted"},
            "nav2_fixed_route_runtime_log": {"classification": "rejected", "reason": "runtime log redaction incomplete"},
            "route_completion_signal": {"classification": "blocked", "reason": "field owner has no signal export"},
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack_path = self._write(root, "pack.json", self._execution_pack())
            packet_path = self._write(root, "packet.json", packet)

            artifact, summary, _exit_code = gate.build_field_evidence_rerun_execution_callback_intake(pack_path, packet_path, "")

        self.assertEqual(artifact["callback_intake_status"], "blocked_field_evidence_rerun_execution_callback_materials_not_ready")
        self.assertIn("task_record", summary["accepted_materials"])
        self.assertIn("nav2_fixed_route_runtime_log", summary["rejected_materials"])
        self.assertIn("route_completion_signal", summary["blocked_materials"])
        self.assertIn("elevator_door_state", summary["missing_materials"])
        self.assertFalse(summary["delivery_success"])

    def test_unsafe_copy_and_success_claim_fail_closed_without_leaking_raw_text(self) -> None:
        unsafe_packet = self._packet()
        unsafe_packet["materials"]["task_record"]["reason"] = "raw artifact /Users/m4/private.log /cmd_vel checksum=abcdef123456"
        success_packet = self._packet(delivery_success=True)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack_path = self._write(root, "pack.json", self._execution_pack())
            unsafe_path = self._write(root, "unsafe.json", unsafe_packet)
            success_path = self._write(root, "success.json", success_packet)

            unsafe_artifact, unsafe_summary, _ = gate.build_field_evidence_rerun_execution_callback_intake(pack_path, unsafe_path, "")
            success_artifact, _success_summary, _ = gate.build_field_evidence_rerun_execution_callback_intake(pack_path, success_path, "")

        self.assertEqual(unsafe_artifact["callback_intake_status"], "blocked_unsafe_field_evidence_rerun_execution_callback_intake_copy")
        self.assertEqual(success_artifact["callback_intake_status"], "blocked_unsafe_field_evidence_rerun_execution_callback_intake_copy")
        encoded_summary = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)
        self.assertNotIn("abcdef123456", encoded_summary)

    def test_wrapper_nested_artifact_and_grouped_packet_are_supported(self) -> None:
        summary = self._execution_pack("ev-wrapper-exec-callback-001")
        grouped_packet = {
            "payload": {
                "schema": "trashbot.field_evidence_rerun_execution_callback_packet_summary.v1",
                "source": "software_proof",
                "safe_evidence_ref": "ev-wrapper-exec-callback-001",
                "evidence_ref": "ev-wrapper-exec-callback-001",
                "same_evidence_ref_required": True,
                "accepted_materials": list(gate.REQUIRED_MATERIAL_CATEGORIES),
                "not_proven": list(gate.NOT_PROVEN),
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrapper_path = self._write(root, "wrapper.json", {"payload": {"artifact": self._artifact(summary)}})
            packet_path = self._write(root, "packet.json", grouped_packet)

            artifact, out_summary, _exit_code = gate.build_field_evidence_rerun_execution_callback_intake(wrapper_path, packet_path, "")

        self.assertEqual(artifact["callback_intake_status"], "ready_for_field_evidence_rerun_execution_callback_intake_not_proven")
        self.assertEqual(out_summary["safe_evidence_ref"], "ev-wrapper-exec-callback-001")
        self.assertFalse(out_summary["safe_to_control"])
        self.assertFalse(out_summary["delivery_success"])
        self.assertFalse(out_summary["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
