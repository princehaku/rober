#!/usr/bin/env python3
"""field_evidence_rerun_handoff_intake 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools 不是 Python package；测试显式加入 evidence 目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "pc-tools" / "evidence"
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_rerun_handoff_intake as gate  # noqa: E402


# 测试约束 01：fixture 只表达 safe handoff summary，不创建真实材料目录。
# 测试约束 02：ready case 只证明 metadata handoff intake 可复账。
# 测试约束 03：ready intake 不能被解释成真实 field pass。
# 测试约束 04：缺 handoff source 必须 fail closed。
# 测试约束 05：缺 owner packet 必须 fail closed。
# 测试约束 06：same evidence_ref mismatch 必须 fail closed。
# 测试约束 07：unsupported schema/boundary 必须 fail closed。
# 测试约束 08：坏 JSON、弱类型 same-ref 都不能 ready。
# 测试约束 09：raw path、ROS topic、checksum 必须被阻断和脱敏。
# 测试约束 10：safe_to_control=true、delivery_success=true 必须被阻断。
# 测试约束 11：wrapper/nested artifact/summary JSON 必须可消费。
# 测试约束 12：所有输出保留 safe_to_control=false。
# 测试约束 13：所有输出保留 delivery_success=false。
# 测试约束 14：所有输出保留 primary_actions_enabled=false。
# 测试约束 15：单测不访问 ROS graph、硬件、外部云或手机 runtime。


class FieldEvidenceRerunHandoffIntakeTest(unittest.TestCase):
    def _handoff(
        self,
        evidence_ref: str = "ev-field-intake-001",
        handoff_status: str = "ready_for_field_evidence_rerun_callback_review_handoff",
        **extra: object,
    ) -> dict[str, object]:
        # source fixture 沿用 callback_review_handoff 的 safe summary contract。
        payload: dict[str, object] = {
            "schema": "trashbot.field_evidence_rerun_callback_review_handoff_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_callback_review_handoff_gate",
            "status": handoff_status,
            "handoff_status": handoff_status,
            "source_review_decision": "accepted",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "same_evidence_ref_status": "matched",
            "owner_handoff": {
                "owner": "Autonomy Algorithm Engineer",
                "handoff_status": handoff_status,
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "handoff_package": {
                "ready": handoff_status == "ready_for_field_evidence_rerun_callback_review_handoff",
                "safe_evidence_ref": evidence_ref,
                "not_proven": "not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "next_required_evidence": [f"Hand off sanitized callback review decision for evidence_ref={evidence_ref}."],
            "rerun_guidance": {
                "required": False,
                "safe_evidence_ref": evidence_ref,
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "blocker_summary": {
                "blocked": handoff_status != "ready_for_field_evidence_rerun_callback_review_handoff",
                "handoff_status": handoff_status,
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "safe_copy": {
                "source": "software_proof",
                "handoff_status": handoff_status,
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
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

    def _packet(self, evidence_ref: str = "ev-field-intake-001", **extra: object) -> dict[str, object]:
        # packet fixture 只放 owner-safe 字段，不包含 raw artifact 或材料正文。
        payload: dict[str, object] = {
            "schema": "trashbot.field_evidence_rerun_handoff_intake_packet.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_handoff_intake_gate",
            "owner": "Autonomy Algorithm Engineer",
            "handoff_received": True,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "intake_notes": ["Owner-safe handoff packet received for product closeout."],
            "next_required_evidence": [f"Keep evidence_ref={evidence_ref} in the same software_proof chain."],
            "not_proven": list(gate.NOT_PROVEN),
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        return payload

    def _artifact(self, summary: dict[str, object]) -> dict[str, object]:
        # artifact fixture 携带 nested summary；intake 应优先消费 summary。
        return {
            "schema": "trashbot.field_evidence_rerun_callback_review_handoff.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_callback_review_handoff_gate",
            "handoff_status": summary["handoff_status"],
            "safe_evidence_ref": summary["safe_evidence_ref"],
            "evidence_ref": summary["evidence_ref"],
            "same_evidence_ref_required": True,
            "same_evidence_ref_status": "matched",
            "field_evidence_rerun_callback_review_handoff_summary": summary,
            "robot_diagnostics_summary": summary,
            "mobile_readonly_summary": summary,
            "not_proven": list(gate.NOT_PROVEN),
            "non_access_scope": ["serial_uart", "wave_rover", "ros_graph"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def _write(self, root: Path, name: str, payload: object) -> str:
        # 临时文件只服务 JSON 输入输出围栏，不模拟真实材料路径。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return str(path)

    def test_ready_handoff_and_owner_packet_map_to_intake_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff_path = self._write(root, "handoff.json", self._handoff())
            packet_path = self._write(root, "packet.json", self._packet())

            artifact, summary, exit_code = gate.build_field_evidence_rerun_handoff_intake(
                handoff_path,
                packet_path,
                "ev-field-intake-001",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.field_evidence_rerun_handoff_intake.v1")
        self.assertEqual(summary["schema"], "trashbot.field_evidence_rerun_handoff_intake_summary.v1")
        self.assertEqual(summary["evidence_boundary"], "software_proof_docker_field_evidence_rerun_handoff_intake_gate")
        self.assertEqual(summary["intake_status"], "ready_for_field_evidence_rerun_handoff_intake_not_proven")
        self.assertEqual(summary["source_handoff_status"], "ready_for_field_evidence_rerun_callback_review_handoff")
        self.assertIn("owner_intake", summary)
        self.assertIn("next_required_evidence", summary)
        self.assertIn("rerun_guidance", summary)
        self.assertIn("blocker_summary", summary)
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("real_phone_browser_evidence", summary["not_proven"])

    def test_missing_inputs_unsupported_source_and_non_ready_handoff_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet_path = self._write(root, "packet.json", self._packet())
            wrong_handoff = self._write(root, "wrong.json", self._handoff(schema="trashbot.other.v1"))
            blocked_handoff = self._write(root, "blocked.json", self._handoff(handoff_status="needs_owner_follow_up"))
            good_handoff = self._write(root, "handoff.json", self._handoff())

            missing_source, _missing_summary, _ = gate.build_field_evidence_rerun_handoff_intake(str(root / "missing.json"), packet_path, "")
            missing_packet, _packet_summary, _ = gate.build_field_evidence_rerun_handoff_intake(good_handoff, str(root / "missing_packet.json"), "")
            unsupported, _unsupported_summary, _ = gate.build_field_evidence_rerun_handoff_intake(wrong_handoff, packet_path, "")
            not_ready, _not_ready_summary, _ = gate.build_field_evidence_rerun_handoff_intake(blocked_handoff, packet_path, "")

        self.assertEqual(missing_source["intake_status"], "blocked_unsupported_field_evidence_rerun_handoff_intake_source")
        self.assertEqual(missing_packet["intake_status"], "blocked_missing_field_evidence_rerun_handoff_intake_packet")
        self.assertEqual(unsupported["intake_status"], "blocked_unsupported_field_evidence_rerun_handoff_intake_source")
        self.assertEqual(not_ready["intake_status"], "blocked_field_evidence_rerun_review_handoff_not_ready")

    def test_mismatch_weak_same_ref_and_missing_packet_fields_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff_path = self._write(root, "handoff.json", self._handoff())
            packet_other = self._write(root, "packet_other.json", self._packet("other-ref"))
            weak_packet = self._write(root, "weak_packet.json", self._packet(same_evidence_ref_required="true"))
            incomplete_packet = self._write(root, "incomplete_packet.json", self._packet(intake_notes=[]))

            mismatch, _mismatch_summary, _ = gate.build_field_evidence_rerun_handoff_intake(handoff_path, packet_other, "ev-field-intake-001")
            weak, _weak_summary, _ = gate.build_field_evidence_rerun_handoff_intake(handoff_path, weak_packet, "")
            incomplete, _incomplete_summary, _ = gate.build_field_evidence_rerun_handoff_intake(handoff_path, incomplete_packet, "")

        self.assertEqual(mismatch["intake_status"], "evidence_ref_mismatch_field_evidence_rerun_handoff_intake_blocked")
        self.assertEqual(weak["intake_status"], "evidence_ref_mismatch_field_evidence_rerun_handoff_intake_blocked")
        self.assertEqual(incomplete["intake_status"], "blocked_missing_field_evidence_rerun_handoff_intake_packet")
        self.assertIn("intake_notes_empty", incomplete["status_reasons"])

    def test_unsafe_copy_and_success_claim_fail_closed_without_leaking_raw_text(self) -> None:
        unsafe_packet = self._packet()
        unsafe_packet["intake_notes"] = ["raw artifact /Users/m4/private.log /cmd_vel checksum=abcdef123456"]
        success_packet = self._packet(delivery_success=True)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff_path = self._write(root, "handoff.json", self._handoff())
            unsafe_path = self._write(root, "unsafe.json", unsafe_packet)
            success_path = self._write(root, "success.json", success_packet)

            unsafe_artifact, unsafe_summary, _ = gate.build_field_evidence_rerun_handoff_intake(handoff_path, unsafe_path, "")
            success_artifact, _success_summary, _ = gate.build_field_evidence_rerun_handoff_intake(handoff_path, success_path, "")

        self.assertEqual(unsafe_artifact["intake_status"], "blocked_unsafe_field_evidence_rerun_handoff_intake_copy")
        self.assertEqual(success_artifact["intake_status"], "blocked_unsafe_field_evidence_rerun_handoff_intake_copy")
        encoded_summary = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)
        self.assertNotIn("abcdef123456", encoded_summary)

    def test_wrapper_nested_artifact_is_supported(self) -> None:
        summary = self._handoff("ev-wrapper-intake-001")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrapper_path = self._write(root, "wrapper.json", {"payload": {"artifact": self._artifact(summary)}})
            packet_path = self._write(root, "packet.json", {"payload": self._packet("ev-wrapper-intake-001")})

            artifact, out_summary, _exit_code = gate.build_field_evidence_rerun_handoff_intake(wrapper_path, packet_path, "")

        self.assertEqual(artifact["intake_status"], "ready_for_field_evidence_rerun_handoff_intake_not_proven")
        self.assertEqual(out_summary["safe_evidence_ref"], "ev-wrapper-intake-001")
        self.assertFalse(out_summary["safe_to_control"])
        self.assertFalse(out_summary["delivery_success"])
        self.assertFalse(out_summary["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
