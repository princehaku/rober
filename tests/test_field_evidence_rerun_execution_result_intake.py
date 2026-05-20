#!/usr/bin/env python3
"""field_evidence_rerun_execution_result_intake 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools 不是 Python package；测试显式加入 evidence 目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "pc-tools" / "evidence"
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_rerun_execution_result_intake as gate  # noqa: E402


# 测试约束 01：fixture 只表达 safe handoff/result packet，不创建真实材料目录。
# 测试约束 02：accepted 只证明 result packet 可进入 review intake。
# 测试约束 03：accepted 不能被解释成真实 field pass 或 delivery success。
# 测试约束 04：缺 result packet 必须得到 missing，而不是 blocked。
# 测试约束 05：packet rejected/blocked 必须保留短状态。
# 测试约束 06：unsupported source、non-ready source 必须 blocked。
# 测试约束 07：same evidence_ref mismatch 必须 blocked。
# 测试约束 08：weak same-ref typing 必须 blocked。
# 测试约束 09：raw path、ROS topic、checksum 必须被阻断和脱敏。
# 测试约束 10：safe_to_control=true、delivery_success=true 必须 blocked。
# 测试约束 11：wrapper/nested artifact/summary JSON 必须可消费。
# 测试约束 12：所有输出保留 safe_to_control=false。
# 测试约束 13：所有输出保留 delivery_success=false。
# 测试约束 14：所有输出保留 primary_actions_enabled=false。
# 测试约束 15：单测不访问 ROS graph、硬件、外部云或手机 runtime。


class FieldEvidenceRerunExecutionResultIntakeTest(unittest.TestCase):
    def _handoff(
        self,
        evidence_ref: str = "ev-field-result-001",
        handoff_status: str = "ready_for_field_evidence_rerun_execution_callback_review_handoff",
        **extra: object,
    ) -> dict[str, object]:
        # source fixture 沿用 execution_callback_review_handoff 的 safe summary contract。
        payload: dict[str, object] = {
            "schema": "trashbot.field_evidence_rerun_execution_callback_review_handoff_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_execution_callback_review_handoff_gate",
            "status": handoff_status,
            "handoff_status": handoff_status,
            "source_review_decision": "ready",
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
                "ready": handoff_status == "ready_for_field_evidence_rerun_execution_callback_review_handoff",
                "safe_evidence_ref": evidence_ref,
                "not_proven": "not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "next_required_evidence": [f"Submit execution result packet for evidence_ref={evidence_ref}."],
            "rerun_guidance": {"required": handoff_status != "ready_for_field_evidence_rerun_execution_callback_review_handoff"},
            "blocker_summary": {
                "blocked": handoff_status != "ready_for_field_evidence_rerun_execution_callback_review_handoff",
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

    def _handoff_artifact(self, summary: dict[str, object]) -> dict[str, object]:
        # artifact fixture 携带 nested summary；result intake 应优先消费 summary。
        return {
            "schema": "trashbot.field_evidence_rerun_execution_callback_review_handoff.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_execution_callback_review_handoff_gate",
            "handoff_status": summary["handoff_status"],
            "safe_evidence_ref": summary["safe_evidence_ref"],
            "evidence_ref": summary["evidence_ref"],
            "same_evidence_ref_required": True,
            "same_evidence_ref_status": "matched",
            "field_evidence_rerun_execution_callback_review_handoff_summary": summary,
            "robot_diagnostics_field_evidence_rerun_execution_callback_review_handoff_summary": summary,
            "robot_diagnostics_summary": summary,
            "mobile_readonly_summary": summary,
            "not_proven": list(gate.NOT_PROVEN),
            "non_access_scope": ["serial_uart", "wave_rover", "ros_graph"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def _packet(
        self,
        evidence_ref: str = "ev-field-result-001",
        packet_status: str = "accepted",
        **extra: object,
    ) -> dict[str, object]:
        # packet fixture 只放 owner-safe 摘要字段，不放 raw material body。
        payload: dict[str, object] = {
            "schema": "trashbot.field_evidence_rerun_execution_result_packet.v1",
            "schema_version": 1,
            "source": "software_proof",
            "packet_status": packet_status,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "same_evidence_ref_status": "matched",
            "material_summary": {
                "packet_state": packet_status,
                "accepted_for_review_intake_only": packet_status == "accepted",
                "safe_evidence_ref": evidence_ref,
            },
            "result_reasons": [f"packet_status={packet_status} for review intake"],
            "owner_handoff": {
                "owner": "field_rerun_owner",
                "safe_evidence_ref": evidence_ref,
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "safe_copy": {
                "source": "software_proof",
                "packet_status": packet_status,
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

    def _write(self, root: Path, name: str, payload: object) -> str:
        # 临时文件只服务 JSON 输入输出围栏，不模拟真实材料路径。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return str(path)

    def test_accepted_packet_maps_to_review_intake_only_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff_path = self._write(root, "handoff.json", self._handoff())
            packet_path = self._write(root, "packet.json", self._packet())

            artifact, summary, exit_code = gate.build_field_evidence_rerun_execution_result_intake(
                handoff_path,
                packet_path,
                "ev-field-result-001",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.field_evidence_rerun_execution_result_intake.v1")
        self.assertEqual(summary["schema"], "trashbot.field_evidence_rerun_execution_result_intake_summary.v1")
        self.assertEqual(summary["evidence_boundary"], "software_proof_docker_field_evidence_rerun_execution_result_intake_gate")
        self.assertEqual(summary["result_intake_status"], "accepted")
        self.assertEqual(summary["accepted_meaning"], "accepted_for_review_intake_only_not_field_pass")
        self.assertEqual(summary["source_handoff_status"], "ready_for_field_evidence_rerun_execution_callback_review_handoff")
        self.assertEqual(summary["result_packet_status"], "accepted")
        self.assertIn("owner_handoff", summary)
        self.assertIn("material_summary", summary)
        self.assertIn("next_required_evidence", summary)
        self.assertIn("reconciliation_hint", summary)
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("real_delivery_success", summary["not_proven"])

    def test_missing_rejected_and_blocked_packet_states_are_short_statuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff_path = self._write(root, "handoff.json", self._handoff())
            missing_packet = self._write(root, "missing-packet.json", self._packet(packet_status="missing"))
            rejected_packet = self._write(root, "rejected-packet.json", self._packet(packet_status="rejected"))
            blocked_packet = self._write(root, "blocked-packet.json", self._packet(packet_status="blocked"))

            missing_artifact, missing_summary, _ = gate.build_field_evidence_rerun_execution_result_intake(handoff_path, "")
            marked_missing, _marked_missing_summary, _ = gate.build_field_evidence_rerun_execution_result_intake(handoff_path, missing_packet)
            rejected, rejected_summary, _ = gate.build_field_evidence_rerun_execution_result_intake(handoff_path, rejected_packet)
            blocked, blocked_summary, _ = gate.build_field_evidence_rerun_execution_result_intake(handoff_path, blocked_packet)

        self.assertEqual(missing_artifact["result_intake_status"], "missing")
        self.assertEqual(marked_missing["result_intake_status"], "missing")
        self.assertEqual(rejected["result_intake_status"], "rejected")
        self.assertEqual(blocked["result_intake_status"], "blocked")
        self.assertEqual(missing_summary["owner_handoff"]["action"], "request_owner_safe_execution_result_packet")
        self.assertEqual(rejected_summary["owner_handoff"]["action"], "return_execution_result_packet_for_owner_correction")
        self.assertEqual(blocked_summary["owner_handoff"]["action"], "repair_result_intake_source_or_remove_unsafe_copy")

    def test_bad_source_non_ready_mismatch_and_weak_same_ref_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet_path = self._write(root, "packet.json", self._packet())
            wrong_source = self._write(root, "wrong.json", self._handoff(schema="trashbot.other.v1"))
            non_ready = self._write(root, "non-ready.json", self._handoff(handoff_status="needs_owner_follow_up"))
            mismatch = self._write(root, "mismatch.json", self._handoff("other-ref"))
            weak_same_ref = self._write(root, "weak.json", self._handoff(same_evidence_ref_required="true"))
            bad_json = root / "bad.json"
            bad_json.write_text("{", encoding="utf-8")

            missing_source, _missing_summary, _ = gate.build_field_evidence_rerun_execution_result_intake(str(root / "missing.json"), packet_path)
            bad_source, _bad_summary, _ = gate.build_field_evidence_rerun_execution_result_intake(str(bad_json), packet_path)
            unsupported, _unsupported_summary, _ = gate.build_field_evidence_rerun_execution_result_intake(wrong_source, packet_path)
            blocked_source, _blocked_summary, _ = gate.build_field_evidence_rerun_execution_result_intake(non_ready, packet_path)
            mismatch_artifact, _mismatch_summary, _ = gate.build_field_evidence_rerun_execution_result_intake(mismatch, packet_path, "ev-field-result-001")
            weak_artifact, _weak_summary, _ = gate.build_field_evidence_rerun_execution_result_intake(weak_same_ref, packet_path)

        self.assertEqual(missing_source["result_intake_status"], "blocked")
        self.assertEqual(bad_source["result_intake_status"], "blocked")
        self.assertEqual(unsupported["result_intake_status"], "blocked")
        self.assertEqual(blocked_source["result_intake_status"], "blocked")
        self.assertEqual(mismatch_artifact["result_intake_status"], "blocked")
        self.assertEqual(weak_artifact["result_intake_status"], "blocked")

    def test_unsafe_copy_success_claim_and_bad_packet_fail_closed_without_leak(self) -> None:
        unsafe_packet = self._packet()
        unsafe_packet["material_summary"] = "raw artifact /Users/m4/private.log /cmd_vel checksum=abcdef123456"
        success_packet = self._packet(delivery_success=True)
        unsupported_packet = self._packet(schema="trashbot.other_packet.v1")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff_path = self._write(root, "handoff.json", self._handoff())
            unsafe_path = self._write(root, "unsafe.json", unsafe_packet)
            success_path = self._write(root, "success.json", success_packet)
            unsupported_path = self._write(root, "unsupported-packet.json", unsupported_packet)

            unsafe_artifact, unsafe_summary, _ = gate.build_field_evidence_rerun_execution_result_intake(handoff_path, unsafe_path)
            success_artifact, _success_summary, _ = gate.build_field_evidence_rerun_execution_result_intake(handoff_path, success_path)
            unsupported_artifact, _unsupported_summary, _ = gate.build_field_evidence_rerun_execution_result_intake(handoff_path, unsupported_path)

        self.assertEqual(unsafe_artifact["result_intake_status"], "blocked")
        self.assertEqual(success_artifact["result_intake_status"], "blocked")
        self.assertEqual(unsupported_artifact["result_intake_status"], "blocked")
        encoded_summary = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)
        self.assertNotIn("abcdef123456", encoded_summary)

    def test_wrapper_nested_handoff_and_packet_are_supported(self) -> None:
        handoff_summary = self._handoff("ev-wrapper-result-001")
        packet_summary = self._packet("ev-wrapper-result-001")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff_path = self._write(root, "wrapper-handoff.json", {"payload": {"artifact": self._handoff_artifact(handoff_summary)}})
            packet_path = self._write(root, "wrapper-packet.json", {"payload": {"summary": packet_summary}})

            artifact, summary, _exit_code = gate.build_field_evidence_rerun_execution_result_intake(handoff_path, packet_path)

        self.assertEqual(artifact["result_intake_status"], "accepted")
        self.assertEqual(summary["safe_evidence_ref"], "ev-wrapper-result-001")
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
