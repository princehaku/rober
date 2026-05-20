#!/usr/bin/env python3
"""hardware_sensor_hil_entry_callback_review_handoff gate 的离线围栏测试。"""

from __future__ import annotations

# 测试约束 01：fixture 只表达 software-proof callback review decision。
# 测试约束 02：ready handoff 仍保持 not_proven 和 safe_to_control=false。
# 测试约束 03：ready handoff 仍保持 delivery_success=false。
# 测试约束 04：ready handoff 仍保持 primary_actions_enabled=false。
# 测试约束 05：缺 input、unsupported schema/boundary 必须 fail closed。
# 测试约束 06：missing/rejected source decision 必须转成 handoff 缺口。
# 测试约束 07：evidence_ref mismatch 和弱 bool/source 合同必须 fail closed。
# 测试约束 08：raw serial/UART、本机路径、凭证必须 fail closed。
# 测试约束 09：HIL pass / field pass / delivery success 文案必须 fail closed。
# 测试约束 10：summary/wrapper 输入也只能输出白名单摘要。
# 测试约束 11：测试不访问 ROS、串口、网络、采购系统或真实传感器。

import json
import sys
import tempfile
import unittest
from pathlib import Path


EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "pc-tools" / "evidence"
sys.path.insert(0, str(EVIDENCE_DIR))

import hardware_sensor_hil_entry_callback_review_handoff as gate  # noqa: E402


def ready_review_decision() -> dict:
    # source review fixture 是脱敏决策输出，不代表真实采购、安装、标定或 HIL。
    accepted = [
        "2d_lidar_sku_source_receipt",
        "tof_sku_source_receipt",
        "mounting",
        "wiring",
        "power",
        "calibration",
        "hil_entry_operator_result",
    ]
    return {
        "schema": "trashbot.hardware_sensor_hil_entry_callback_review_decision.v1",
        "schema_version": 1,
        "source": "software_proof",
        "evidence_boundary": "software_proof_docker_hardware_sensor_hil_entry_callback_review_decision_gate",
        "evidence_ref": "sensor-hil-callback-handoff-001",
        "review_decision": "ready_for_hardware_sensor_hil_entry_callback_owner_handoff_not_proven",
        "hardware_sensor_hil_entry_callback_review_decision": "ready_for_hardware_sensor_hil_entry_callback_owner_handoff_not_proven",
        "accepted_materials": [{"material": item, "ref": f"{item}-ref"} for item in accepted],
        "missing_materials": [],
        "rejected_materials": [],
        "owner_handoff": [
            {
                "owner": "Hardware Infra Engineer",
                "action": "Review sanitized callback materials before real HIL-entry scheduling.",
            }
        ],
        "next_required_evidence": [
            "Run hardware_sensor_hil_entry_callback_review_handoff over this sanitized review decision summary.",
        ],
        "evidence_status": "not_proven",
        "not_proven": ["real_sensor_hil_entry_pass", "delivery_success"],
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }


class HardwareSensorHilEntryCallbackReviewHandoffGateTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict | str) -> Path:
        # 测试只写临时 JSON，不污染 sprint evidence。
        path = root / name
        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def build(self, payload: dict | str, evidence_ref: str = ""):
        # 统一走文件入口，覆盖 CLI 同款读取、wrapper 和安全扫描。
        with tempfile.TemporaryDirectory() as td:
            path = self.write_json(Path(td), "callback_review_decision.json", payload)
            return gate.build_hardware_sensor_hil_entry_callback_review_handoff(path, evidence_ref=evidence_ref)

    def test_ready_review_decision_becomes_accepted_handoff_not_proven(self):
        artifact, summary, exit_code = self.build(ready_review_decision())

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.hardware_sensor_hil_entry_callback_review_handoff.v1")
        self.assertEqual(summary["schema"], "trashbot.hardware_sensor_hil_entry_callback_review_handoff_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_hardware_sensor_hil_entry_callback_review_handoff_gate",
        )
        self.assertEqual(
            artifact["handoff_status"],
            "accepted_ready_hardware_sensor_hil_entry_callback_review_handoff_not_proven",
        )
        self.assertEqual(summary["source_review_decision_status"], "ready_for_hardware_sensor_hil_entry_callback_owner_handoff_not_proven")
        self.assertEqual(summary["missing_required_materials"], [])
        self.assertIn("docs/vendor/VENDOR_INDEX.md", json.dumps(artifact, ensure_ascii=False))
        self.assertIn("PRRT_kwDOSWB9286CJ3tX", json.dumps(artifact, ensure_ascii=False))
        self.assertEqual(summary["source"], "software_proof")
        self.assertEqual(summary["evidence_status"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])

    def test_missing_and_malformed_inputs_fail_closed(self):
        missing_artifact, missing_summary, missing_exit = gate.build_hardware_sensor_hil_entry_callback_review_handoff(None)
        malformed_artifact, _malformed_summary, malformed_exit = self.build("{bad-json")

        self.assertEqual(missing_exit, 2)
        self.assertEqual(malformed_exit, 2)
        self.assertEqual(
            missing_artifact["handoff_status"],
            "blocked_unsupported_hardware_sensor_hil_entry_callback_review_decision_not_proven",
        )
        self.assertEqual(
            malformed_artifact["handoff_status"],
            "blocked_malformed_hardware_sensor_hil_entry_callback_review_decision_not_proven",
        )
        self.assertFalse(missing_summary["delivery_success"])
        self.assertFalse(missing_summary["primary_actions_enabled"])
        self.assertFalse(missing_summary["safe_to_control"])

    def test_summary_and_wrapper_inputs_are_supported(self):
        summary = ready_review_decision()
        summary["schema"] = "trashbot.hardware_sensor_hil_entry_callback_review_decision_summary.v1"
        wrapper = {"hardware_sensor_hil_entry_callback_review_decision_summary": summary}
        summary_artifact, _summary, summary_exit = self.build(summary)
        wrapper_artifact, _wrapper_summary, wrapper_exit = self.build(wrapper)

        self.assertEqual(summary_exit, 0)
        self.assertEqual(wrapper_exit, 0)
        self.assertEqual(summary_artifact["source_callback_review_decision_schema"], "trashbot.hardware_sensor_hil_entry_callback_review_decision_summary.v1")
        self.assertEqual(wrapper_artifact["schema_status"], "supported")

    def test_missing_materials_map_to_blocked_missing_handoff(self):
        payload = ready_review_decision()
        payload["review_decision"] = "needs_hardware_sensor_hil_entry_callback_material_backfill_not_proven"
        payload["accepted_materials"] = payload["accepted_materials"][:-2]
        payload["missing_materials"] = ["calibration", "hil_entry_operator_result"]
        artifact, summary, exit_code = self.build(payload)

        self.assertEqual(exit_code, 2)
        self.assertEqual(
            artifact["handoff_status"],
            "blocked_missing_hardware_sensor_hil_entry_callback_handoff_materials_not_proven",
        )
        self.assertIn("calibration", " ".join(summary["next_required_evidence"]))

    def test_rejected_source_decision_maps_to_rejected_handoff(self):
        payload = ready_review_decision()
        payload["review_decision"] = "blocked_rejected_hardware_sensor_hil_entry_callback_materials_not_proven"
        payload["rejected_materials"] = [{"material": "wiring", "reason": "unsafe_raw_or_success_claim"}]
        artifact, _summary, exit_code = self.build(payload)

        self.assertEqual(exit_code, 2)
        self.assertEqual(
            artifact["handoff_status"],
            "blocked_rejected_hardware_sensor_hil_entry_callback_source_decision_not_proven",
        )
        self.assertEqual(artifact["rejected_materials"][0], "wiring")

    def test_unsupported_boundary_evidence_ref_mismatch_and_weak_contract_fail_closed(self):
        unsupported = ready_review_decision()
        unsupported["evidence_boundary"] = "software_proof_other_gate"
        unsupported_artifact, _unsupported_summary, unsupported_exit = self.build(unsupported)

        mismatch_artifact, _mismatch_summary, mismatch_exit = self.build(
            ready_review_decision(),
            evidence_ref="different-evidence-ref-001",
        )

        weak = ready_review_decision()
        weak["safe_to_control"] = "false"
        weak_artifact, _weak_summary, weak_exit = self.build(weak)

        self.assertEqual(unsupported_exit, 2)
        self.assertEqual(mismatch_exit, 2)
        self.assertEqual(weak_exit, 2)
        self.assertEqual(
            unsupported_artifact["handoff_status"],
            "blocked_unsupported_hardware_sensor_hil_entry_callback_review_decision_not_proven",
        )
        self.assertEqual(mismatch_artifact["handoff_status"], "blocked_evidence_ref_mismatch_not_proven")
        self.assertEqual(
            weak_artifact["handoff_status"],
            "blocked_unsafe_hardware_sensor_hil_entry_callback_review_handoff_input_not_proven",
        )

    def test_unsafe_copy_and_success_claim_fail_closed_and_redacted(self):
        unsafe = ready_review_decision()
        unsafe["owner_handoff"][0]["action"] = "Authorization: Bearer abc /dev/ttyUSB0 raw UART"
        unsafe_artifact, _unsafe_summary, unsafe_exit = self.build(unsafe)

        success = ready_review_decision()
        success["next_required_evidence"][0] = "HIL passed and delivery success"
        success["delivery_success"] = True
        success_artifact, success_summary, success_exit = self.build(success)

        encoded = json.dumps(unsafe_artifact, ensure_ascii=False)
        self.assertEqual(unsafe_exit, 2)
        self.assertEqual(success_exit, 2)
        self.assertEqual(
            unsafe_artifact["handoff_status"],
            "blocked_unsafe_hardware_sensor_hil_entry_callback_review_handoff_input_not_proven",
        )
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertFalse(success_artifact["delivery_success"])
        self.assertFalse(success_summary["primary_actions_enabled"])
        self.assertFalse(success_summary["safe_to_control"])


if __name__ == "__main__":
    unittest.main()
