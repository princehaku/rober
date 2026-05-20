#!/usr/bin/env python3
"""field_evidence_rerun_callback_intake 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools 不是 Python package；测试显式加入 evidence 目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "pc-tools" / "evidence"
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_rerun_callback_intake as gate  # noqa: E402


# 测试约束 01：fixture 只表达 safe dispatch/callback，不创建真实材料目录。
# 测试约束 02：ready case 只证明 callback intake metadata 可复账。
# 测试约束 03：accepted 不能被解释成真实 field pass。
# 测试约束 04：missing/rejected/blocked 必须进入 next_required_evidence。
# 测试约束 05：same evidence_ref mismatch 必须 fail closed。
# 测试约束 06：unsupported dispatch schema/boundary 必须 fail closed。
# 测试约束 07：坏 JSON 和缺 callback 都不能产生 ready。
# 测试约束 08：raw path、ROS topic、checksum 必须被阻断和脱敏。
# 测试约束 09：delivery_success=true 必须被阻断。
# 测试约束 10：未知 material class 或非法分类必须 blocked。
# 测试约束 11：wrapper/nested JSON 必须可消费。
# 测试约束 12：所有输出保留 safe_to_control=false。
# 测试约束 13：所有输出保留 delivery_success=false。
# 测试约束 14：所有输出保留 primary_actions_enabled=false。
# 测试约束 15：单测不访问 ROS graph、硬件、外部云或手机 runtime。


class FieldEvidenceRerunCallbackIntakeTest(unittest.TestCase):
    def _dispatch(self, evidence_ref: str = "ev-field-callback-001", **extra: object) -> dict[str, object]:
        # dispatch fixture 沿用上一轮 material_dispatch 的 safe summary contract。
        payload: dict[str, object] = {
            "schema": "trashbot.field_evidence_rerun_material_dispatch_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_material_dispatch_gate",
            "status": "ready_for_field_evidence_rerun_material_dispatch_not_proven",
            "dispatch_status": "ready_for_field_evidence_rerun_material_dispatch_not_proven",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "required_material_groups": [
                {"material_group": material_class, "required": True}
                for material_class in gate.REQUIRED_MATERIAL_CLASSES
            ],
            "safe_copy": {
                "source": "software_proof",
                "status": "ready_for_field_evidence_rerun_material_dispatch_not_proven",
                "safe_evidence_ref": evidence_ref,
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

    def _callback(self, evidence_ref: str = "ev-field-callback-001", **extra: object) -> dict[str, object]:
        # callback fixture 是现场 owner 回执元数据，不包含文件内容或原始日志。
        payload: dict[str, object] = {
            "schema": "trashbot.field_evidence_rerun_callback_packet.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_callback_intake_gate",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "material_classifications": {
                material_class: {"classification": "accepted", "reason": "safe_owner_callback_received_not_proven"}
                for material_class in gate.REQUIRED_MATERIAL_CLASSES
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

    def test_ready_callback_intake_classifies_all_materials_but_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dispatch_path = self._write(root, "dispatch.json", self._dispatch())
            callback_path = self._write(root, "callback.json", self._callback())

            artifact, summary, exit_code = gate.build_field_evidence_rerun_callback_intake(dispatch_path, callback_path, "ev-field-callback-001")

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.field_evidence_rerun_callback_intake.v1")
        self.assertEqual(summary["schema"], "trashbot.field_evidence_rerun_callback_intake_summary.v1")
        self.assertEqual(summary["evidence_boundary"], "software_proof_docker_field_evidence_rerun_callback_intake_gate")
        self.assertEqual(summary["callback_intake_status"], "ready_for_field_evidence_rerun_callback_intake_not_proven")
        self.assertEqual(summary["material_counts"]["accepted"], len(gate.REQUIRED_MATERIAL_CLASSES))
        self.assertIn("real route completion signal", summary["accepted_materials"])
        self.assertIn("real field task record", summary["accepted_materials"])
        self.assertIn("real Nav2/fixed-route runtime log", summary["accepted_materials"])
        self.assertIn("real phone/browser evidence", summary["accepted_materials"])
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("real_phone_browser_evidence", summary["not_proven"])

    def test_missing_rejected_and_blocked_materials_are_reported(self) -> None:
        callback = self._callback()
        callback["material_classifications"] = {
            "real route completion signal": "accepted",
            "real field task record": {"classification": "rejected", "reason": "task_record_wrong_evidence_ref"},
            "real Nav2/fixed-route runtime log": {"classification": "blocked", "reason": "field_owner_pending_runtime_export"},
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dispatch_path = self._write(root, "dispatch.json", self._dispatch())
            callback_path = self._write(root, "callback.json", callback)

            artifact, summary, _exit_code = gate.build_field_evidence_rerun_callback_intake(dispatch_path, callback_path, "")

        self.assertEqual(artifact["callback_intake_status"], "blocked_field_evidence_rerun_callback_materials_not_ready")
        self.assertIn("real field task record", summary["rejected_materials"])
        self.assertIn("real Nav2/fixed-route runtime log", summary["blocked_materials"])
        self.assertIn("real phone/browser evidence", summary["missing_materials"])
        self.assertIn("real phone/browser evidence", summary["next_required_evidence"])

    def test_missing_bad_json_unsupported_and_ref_mismatch_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dispatch_path = self._write(root, "dispatch.json", self._dispatch())
            callback_path = self._write(root, "callback.json", self._callback())
            bad_json = root / "bad.json"
            bad_json.write_text("{", encoding="utf-8")
            wrong_schema = self._write(root, "wrong.json", self._dispatch(schema="trashbot.other.v1"))
            mismatch_callback = self._write(root, "mismatch.json", self._callback("other-ref"))

            missing_artifact, _missing_summary, _ = gate.build_field_evidence_rerun_callback_intake(dispatch_path, str(root / "missing.json"), "")
            bad_artifact, _bad_summary, _ = gate.build_field_evidence_rerun_callback_intake(dispatch_path, str(bad_json), "")
            unsupported_artifact, _unsupported_summary, _ = gate.build_field_evidence_rerun_callback_intake(wrong_schema, callback_path, "")
            mismatch_artifact, _mismatch_summary, _ = gate.build_field_evidence_rerun_callback_intake(dispatch_path, mismatch_callback, "")

        self.assertEqual(missing_artifact["callback_intake_status"], "blocked_unsupported_field_evidence_rerun_callback_intake_source")
        self.assertEqual(bad_artifact["callback_intake_status"], "blocked_unsupported_field_evidence_rerun_callback_intake_source")
        self.assertEqual(unsupported_artifact["callback_intake_status"], "blocked_unsupported_field_evidence_rerun_callback_intake_source")
        self.assertEqual(mismatch_artifact["callback_intake_status"], "evidence_ref_mismatch_field_evidence_rerun_callback_intake_blocked")

    def test_unsafe_copy_success_claim_and_unknown_material_fail_closed(self) -> None:
        unsafe = self._callback()
        unsafe["owner_note"] = "raw artifact /Users/m4/private.log /cmd_vel checksum=abcdef123456"
        success = self._callback(delivery_success=True)
        unknown = self._callback()
        unknown["material_classifications"] = {"unknown material": "accepted"}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dispatch_path = self._write(root, "dispatch.json", self._dispatch())
            unsafe_path = self._write(root, "unsafe.json", unsafe)
            success_path = self._write(root, "success.json", success)
            unknown_path = self._write(root, "unknown.json", unknown)

            unsafe_artifact, unsafe_summary, _ = gate.build_field_evidence_rerun_callback_intake(dispatch_path, unsafe_path, "")
            success_artifact, _success_summary, _ = gate.build_field_evidence_rerun_callback_intake(dispatch_path, success_path, "")
            unknown_artifact, unknown_summary, _ = gate.build_field_evidence_rerun_callback_intake(dispatch_path, unknown_path, "")

        self.assertEqual(unsafe_artifact["callback_intake_status"], "blocked_unsafe_field_evidence_rerun_callback_intake_copy")
        self.assertEqual(success_artifact["callback_intake_status"], "blocked_unsafe_field_evidence_rerun_callback_intake_copy")
        self.assertEqual(unknown_artifact["callback_intake_status"], "blocked_field_evidence_rerun_callback_materials_not_ready")
        self.assertIn("unsupported_material_class:unknown material", unknown_summary["status_reasons"])
        encoded_summary = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)
        self.assertNotIn("abcdef123456", encoded_summary)

    def test_wrapper_and_list_material_format_are_supported(self) -> None:
        callback = self._callback()
        callback["material_classifications"] = [
            {"material_class": material_class, "classification": "accepted", "reason": "list_format_safe_callback"}
            for material_class in gate.REQUIRED_MATERIAL_CLASSES
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dispatch_path = self._write(root, "dispatch_wrapper.json", {"payload": {"field_evidence_rerun_material_dispatch_summary": self._dispatch("ev-wrapper-callback-001")}})
            callback_path = self._write(root, "callback_wrapper.json", {"payload": {"field_evidence_rerun_callback_packet": callback | {"safe_evidence_ref": "ev-wrapper-callback-001", "evidence_ref": "ev-wrapper-callback-001"}}})

            artifact, summary, _exit_code = gate.build_field_evidence_rerun_callback_intake(dispatch_path, callback_path, "")

        self.assertEqual(artifact["callback_intake_status"], "ready_for_field_evidence_rerun_callback_intake_not_proven")
        self.assertEqual(summary["safe_evidence_ref"], "ev-wrapper-callback-001")
        self.assertEqual(summary["material_counts"]["accepted"], len(gate.REQUIRED_MATERIAL_CLASSES))


if __name__ == "__main__":
    unittest.main()
