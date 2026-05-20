#!/usr/bin/env python3
"""field_evidence_rerun_queue 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools 不是 Python package；测试显式加入 evidence 目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "pc-tools" / "evidence"
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_rerun_queue as gate  # noqa: E402


# 测试约束 01：fixture 只表达 safe handoff intake，不创建真实材料目录。
# 测试约束 02：queued case 只证明 metadata queue candidate 可生成。
# 测试约束 03：queued 不证明真实 route/elevator field pass 或 Nav2 runtime。
# 测试约束 04：缺 handoff intake source 必须 fail closed。
# 测试约束 05：缺 queue request 必须 fail closed 且不能 ready。
# 测试约束 06：same evidence_ref mismatch 必须 fail closed。
# 测试约束 07：unsupported schema/boundary 必须 fail closed。
# 测试约束 08：source intake 未 ready 必须进入 backfill。
# 测试约束 09：raw path、ROS topic、checksum 必须被阻断和脱敏。
# 测试约束 10：safe_to_control=true、delivery_success=true 必须被阻断。
# 测试约束 11：wrapper/nested artifact/summary JSON 必须可消费。
# 测试约束 12：所有输出保留 safe_to_control=false。
# 测试约束 13：所有输出保留 delivery_success=false。
# 测试约束 14：所有输出保留 primary_actions_enabled=false。
# 测试约束 15：单测不访问 ROS graph、硬件、外部云或手机 runtime。


class FieldEvidenceRerunQueueTest(unittest.TestCase):
    def _handoff_intake(
        self,
        evidence_ref: str = "ev-field-queue-001",
        intake_status: str = "ready_for_field_evidence_rerun_handoff_intake_not_proven",
        **extra: object,
    ) -> dict[str, object]:
        # source fixture 沿用上一轮 handoff intake 的 safe summary contract。
        payload: dict[str, object] = {
            "schema": "trashbot.field_evidence_rerun_handoff_intake_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_handoff_intake_gate",
            "status": intake_status,
            "intake_status": intake_status,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "same_evidence_ref_status": "matched",
            "owner_intake": {
                "owner": "Autonomy Algorithm Engineer",
                "intake_status": intake_status,
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "next_required_evidence": [f"Prepare metadata-only queue request for evidence_ref={evidence_ref}."],
            "rerun_guidance": {
                "required": False,
                "safe_evidence_ref": evidence_ref,
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "blocker_summary": {
                "blocked": intake_status != "ready_for_field_evidence_rerun_handoff_intake_not_proven",
                "intake_status": intake_status,
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "safe_copy": {
                "source": "software_proof",
                "status": intake_status,
                "intake_status": intake_status,
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

    def _queue_request(self, evidence_ref: str = "ev-field-queue-001", **extra: object) -> dict[str, object]:
        # request fixture 只放 owner-safe 元数据，不包含 raw artifact 或现场材料正文。
        payload: dict[str, object] = {
            "schema": "trashbot.field_evidence_rerun_queue_request.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_queue_gate",
            "owner": "Autonomy Algorithm Engineer",
            "owner_ack": True,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "requested_rerun_reason": "Queue sanitized field rerun candidate for owner-controlled scheduling.",
            "next_required_evidence": [f"Keep evidence_ref={evidence_ref} pending real field rerun materials."],
            "not_proven": list(gate.NOT_PROVEN),
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        return payload

    def _artifact(self, summary: dict[str, object]) -> dict[str, object]:
        # artifact fixture 携带 nested summary；queue 应优先消费 summary。
        return {
            "schema": "trashbot.field_evidence_rerun_handoff_intake.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_handoff_intake_gate",
            "intake_status": summary["intake_status"],
            "safe_evidence_ref": summary["safe_evidence_ref"],
            "evidence_ref": summary["evidence_ref"],
            "same_evidence_ref_required": True,
            "same_evidence_ref_status": "matched",
            "field_evidence_rerun_handoff_intake_summary": summary,
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

    def test_ready_intake_and_owner_queue_request_map_to_queue_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_path = self._write(root, "handoff_intake.json", self._handoff_intake())
            request_path = self._write(root, "queue_request.json", self._queue_request())

            artifact, summary, exit_code = gate.build_field_evidence_rerun_queue(source_path, request_path, "ev-field-queue-001")

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.field_evidence_rerun_queue.v1")
        self.assertEqual(summary["schema"], "trashbot.field_evidence_rerun_queue_summary.v1")
        self.assertEqual(summary["evidence_boundary"], "software_proof_docker_field_evidence_rerun_queue_gate")
        self.assertEqual(summary["queue_status"], "queued_for_controlled_field_rerun_not_proven")
        self.assertEqual(summary["source_handoff_intake_status"], "ready_for_field_evidence_rerun_handoff_intake_not_proven")
        self.assertEqual(summary["same_evidence_ref_status"], "matched")
        self.assertIn("owner_safe_queue_request", summary)
        self.assertIn("safe_rerun_hint", summary)
        self.assertIn("rerun_guidance", summary)
        self.assertIn("blocker_summary", summary)
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("real_phone_browser_evidence", summary["not_proven"])

    def test_missing_inputs_and_unsupported_source_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request_path = self._write(root, "queue_request.json", self._queue_request())
            good_source = self._write(root, "handoff_intake.json", self._handoff_intake())
            wrong_source = self._write(root, "wrong.json", self._handoff_intake(schema="trashbot.other.v1"))

            missing_source, _missing_summary, _ = gate.build_field_evidence_rerun_queue(str(root / "missing.json"), request_path, "")
            missing_request, _request_summary, _ = gate.build_field_evidence_rerun_queue(good_source, "", "")
            unsupported, _unsupported_summary, _ = gate.build_field_evidence_rerun_queue(wrong_source, request_path, "")

        self.assertEqual(missing_source["queue_status"], "blocked_unsupported_field_evidence_rerun_handoff_intake")
        self.assertEqual(missing_request["queue_status"], "needs_owner_safe_queue_request_before_rerun_queue")
        self.assertEqual(unsupported["queue_status"], "blocked_unsupported_field_evidence_rerun_handoff_intake")

    def test_non_ready_source_ack_missing_mismatch_and_weak_same_ref_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_path = self._write(root, "handoff_intake.json", self._handoff_intake())
            blocked_source = self._write(root, "blocked.json", self._handoff_intake(intake_status="blocked_field_evidence_rerun_review_handoff_not_ready"))
            no_ack_request = self._write(root, "no_ack.json", self._queue_request(owner_ack=False))
            other_ref_request = self._write(root, "other.json", self._queue_request("other-ref"))
            weak_request = self._write(root, "weak.json", self._queue_request(same_evidence_ref_required="true"))

            not_ready, _not_ready_summary, _ = gate.build_field_evidence_rerun_queue(blocked_source, self._write(root, "request.json", self._queue_request()), "")
            no_ack, _no_ack_summary, _ = gate.build_field_evidence_rerun_queue(source_path, no_ack_request, "")
            mismatch, _mismatch_summary, _ = gate.build_field_evidence_rerun_queue(source_path, other_ref_request, "")
            weak, _weak_summary, _ = gate.build_field_evidence_rerun_queue(source_path, weak_request, "")

        self.assertEqual(not_ready["queue_status"], "needs_field_evidence_rerun_queue_backfill")
        self.assertEqual(no_ack["queue_status"], "needs_owner_safe_queue_request_before_rerun_queue")
        self.assertEqual(mismatch["queue_status"], "evidence_ref_mismatch_field_evidence_rerun_queue")
        self.assertEqual(weak["queue_status"], "evidence_ref_mismatch_field_evidence_rerun_queue")

    def test_unsafe_copy_and_success_claim_fail_closed_without_leaking_raw_text(self) -> None:
        unsafe_request = self._queue_request()
        unsafe_request["requested_rerun_reason"] = "raw artifact /Users/m4/private.log /cmd_vel checksum=abcdef123456"
        success_request = self._queue_request(delivery_success=True)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_path = self._write(root, "handoff_intake.json", self._handoff_intake())
            unsafe_path = self._write(root, "unsafe.json", unsafe_request)
            success_path = self._write(root, "success.json", success_request)

            unsafe_artifact, unsafe_summary, _ = gate.build_field_evidence_rerun_queue(source_path, unsafe_path, "")
            success_artifact, _success_summary, _ = gate.build_field_evidence_rerun_queue(source_path, success_path, "")

        self.assertEqual(unsafe_artifact["queue_status"], "blocked_unsafe_field_evidence_rerun_queue")
        self.assertEqual(success_artifact["queue_status"], "blocked_unsafe_field_evidence_rerun_queue")
        encoded_summary = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)
        self.assertNotIn("abcdef123456", encoded_summary)
        self.assertFalse(unsafe_summary["safe_to_control"])

    def test_wrapper_nested_artifact_is_supported(self) -> None:
        summary = self._handoff_intake("ev-wrapper-queue-001")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrapper_path = self._write(root, "wrapper.json", {"payload": {"artifact": self._artifact(summary)}})
            request_path = self._write(root, "request.json", {"payload": self._queue_request("ev-wrapper-queue-001")})

            artifact, out_summary, _exit_code = gate.build_field_evidence_rerun_queue(wrapper_path, request_path, "")

        self.assertEqual(artifact["queue_status"], "queued_for_controlled_field_rerun_not_proven")
        self.assertEqual(out_summary["safe_evidence_ref"], "ev-wrapper-queue-001")
        self.assertFalse(out_summary["safe_to_control"])
        self.assertFalse(out_summary["delivery_success"])
        self.assertFalse(out_summary["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
