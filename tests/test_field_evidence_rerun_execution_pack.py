#!/usr/bin/env python3
"""field_evidence_rerun_execution_pack 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools 不是 Python package；测试显式加入 evidence 目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "pc-tools" / "evidence"
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_rerun_execution_pack as gate  # noqa: E402


# 测试约束 01：fixture 只表达 safe queue，不创建真实材料目录。
# 测试约束 02：ready case 只证明 metadata execution pack 可生成。
# 测试约束 03：ready 不证明真实 route/elevator field pass 或 Nav2 runtime。
# 测试约束 04：缺 queue source 必须 fail closed。
# 测试约束 05：unsupported schema/boundary 必须 fail closed。
# 测试约束 06：same evidence_ref mismatch 必须 fail closed。
# 测试约束 07：source queue 未 queued 必须进入 backfill。
# 测试约束 08：raw path、ROS topic、checksum 必须被阻断和脱敏。
# 测试约束 09：safe_to_control=true、delivery_success=true 必须被阻断。
# 测试约束 10：wrapper/nested artifact/summary JSON 必须可消费。
# 测试约束 11：所有输出保留 safe_to_control=false。
# 测试约束 12：所有输出保留 delivery_success=false。
# 测试约束 13：所有输出保留 primary_actions_enabled=false。
# 测试约束 14：单测不访问 ROS graph、硬件、外部云或手机 runtime。


class FieldEvidenceRerunExecutionPackTest(unittest.TestCase):
    def _queue(
        self,
        evidence_ref: str = "ev-field-pack-001",
        queue_status: str = "queued_for_controlled_field_rerun_not_proven",
        **extra: object,
    ) -> dict[str, object]:
        # source fixture 沿用上一轮 queue 的 safe summary contract。
        payload: dict[str, object] = {
            "schema": "trashbot.field_evidence_rerun_queue_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_queue_gate",
            "status": queue_status,
            "queue_status": queue_status,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "same_evidence_ref_status": "matched",
            "owner_safe_queue_request": {
                "owner_acknowledgement_state": "acknowledged",
                "safe_evidence_ref": evidence_ref,
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "next_required_evidence": [f"Hold queue candidate pending real materials for evidence_ref={evidence_ref}."],
            "owner_handoff": {
                "owner": "Autonomy Algorithm Engineer",
                "safe_evidence_ref": evidence_ref,
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "blocker_summary": {
                "blocked": queue_status != "queued_for_controlled_field_rerun_not_proven",
                "queue_status": queue_status,
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "safe_copy": {
                "source": "software_proof",
                "status": queue_status,
                "queue_status": queue_status,
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

    def _artifact(self, summary: dict[str, object]) -> dict[str, object]:
        # artifact fixture 携带 nested summary；execution pack 应优先消费 summary。
        return {
            "schema": "trashbot.field_evidence_rerun_queue.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_queue_gate",
            "queue_status": summary["queue_status"],
            "safe_evidence_ref": summary["safe_evidence_ref"],
            "evidence_ref": summary["evidence_ref"],
            "same_evidence_ref_required": True,
            "same_evidence_ref_status": "matched",
            "field_evidence_rerun_queue_summary": summary,
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

    def test_ready_queue_maps_to_execution_pack_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            queue_path = self._write(root, "queue.json", self._queue())

            artifact, summary, exit_code = gate.build_field_evidence_rerun_execution_pack(queue_path, "ev-field-pack-001")

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.field_evidence_rerun_execution_pack.v1")
        self.assertEqual(summary["schema"], "trashbot.field_evidence_rerun_execution_pack_summary.v1")
        self.assertEqual(summary["evidence_boundary"], "software_proof_docker_field_evidence_rerun_execution_pack_gate")
        self.assertEqual(summary["execution_pack_status"], "ready_for_field_evidence_rerun_execution_pack_not_proven")
        self.assertEqual(summary["source_queue_status"], "queued_for_controlled_field_rerun_not_proven")
        self.assertEqual(summary["same_evidence_ref_status"], "matched")
        self.assertEqual(len(summary["execution_steps"]), 9)
        self.assertEqual(len(summary["material_templates"]), 7)
        self.assertIn("owner_handoff", summary)
        self.assertIn("fail_thresholds", summary)
        self.assertIn("pass_thresholds", summary)
        self.assertIn("backfill_instructions", summary)
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("real_phone_browser_evidence", summary["not_proven"])

    def test_missing_inputs_and_unsupported_source_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrong_source = self._write(root, "wrong.json", self._queue(schema="trashbot.other.v1"))

            missing_source, _missing_summary, _ = gate.build_field_evidence_rerun_execution_pack(str(root / "missing.json"), "")
            unsupported, _unsupported_summary, _ = gate.build_field_evidence_rerun_execution_pack(wrong_source, "")

        self.assertEqual(missing_source["execution_pack_status"], "blocked_unsupported_field_evidence_rerun_queue")
        self.assertEqual(unsupported["execution_pack_status"], "blocked_unsupported_field_evidence_rerun_queue")

    def test_non_ready_source_mismatch_and_weak_same_ref_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_path = self._write(root, "queue.json", self._queue())
            blocked_source = self._write(root, "blocked.json", self._queue(queue_status="needs_field_evidence_rerun_queue_backfill"))
            weak_source = self._write(root, "weak.json", self._queue(same_evidence_ref_required="true"))

            not_ready, _not_ready_summary, _ = gate.build_field_evidence_rerun_execution_pack(blocked_source, "")
            mismatch, _mismatch_summary, _ = gate.build_field_evidence_rerun_execution_pack(source_path, "other-ref")
            weak, _weak_summary, _ = gate.build_field_evidence_rerun_execution_pack(weak_source, "")

        self.assertEqual(not_ready["execution_pack_status"], "needs_field_evidence_rerun_execution_pack_backfill")
        self.assertEqual(mismatch["execution_pack_status"], "evidence_ref_mismatch_field_evidence_rerun_execution_pack")
        self.assertEqual(weak["execution_pack_status"], "evidence_ref_mismatch_field_evidence_rerun_execution_pack")

    def test_unsafe_copy_and_success_claim_fail_closed_without_leaking_raw_text(self) -> None:
        unsafe_queue = self._queue()
        unsafe_queue["next_required_evidence"] = ["raw artifact /Users/m4/private.log /cmd_vel checksum=abcdef123456"]
        success_queue = self._queue(delivery_success=True)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe_path = self._write(root, "unsafe.json", unsafe_queue)
            success_path = self._write(root, "success.json", success_queue)

            unsafe_artifact, unsafe_summary, _ = gate.build_field_evidence_rerun_execution_pack(unsafe_path, "")
            success_artifact, _success_summary, _ = gate.build_field_evidence_rerun_execution_pack(success_path, "")

        self.assertEqual(unsafe_artifact["execution_pack_status"], "blocked_unsafe_field_evidence_rerun_execution_pack")
        self.assertEqual(success_artifact["execution_pack_status"], "blocked_unsafe_field_evidence_rerun_execution_pack")
        encoded_summary = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)
        self.assertNotIn("abcdef123456", encoded_summary)
        self.assertFalse(unsafe_summary["safe_to_control"])

    def test_wrapper_nested_artifact_is_supported(self) -> None:
        summary = self._queue("ev-wrapper-pack-001")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrapper_path = self._write(root, "wrapper.json", {"payload": {"artifact": self._artifact(summary)}})

            artifact, out_summary, _exit_code = gate.build_field_evidence_rerun_execution_pack(wrapper_path, "")

        self.assertEqual(artifact["execution_pack_status"], "ready_for_field_evidence_rerun_execution_pack_not_proven")
        self.assertEqual(out_summary["safe_evidence_ref"], "ev-wrapper-pack-001")
        self.assertFalse(out_summary["safe_to_control"])
        self.assertFalse(out_summary["delivery_success"])
        self.assertFalse(out_summary["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
