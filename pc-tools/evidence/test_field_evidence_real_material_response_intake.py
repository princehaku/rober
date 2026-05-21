#!/usr/bin/env python3
"""field evidence real material response intake gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools/evidence 不是 package；测试显式加入目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_real_material_response_intake as intake  # noqa: E402


# 测试约束 01：fixture 只表达 safe request dispatch summary。
# 测试约束 02：accepted 仅表示 ready for later review，不表示现场通过。
# 测试约束 03：缺 field-owner response 时不能产生 accepted。
# 测试约束 04：九类材料必须全部同一 evidence_ref。
# 测试约束 05：mixed evidence_ref 必须 rejected。
# 测试约束 06：raw ROS topic、/cmd_vel、serial/UART/WAVE ROVER、路径、凭证必须阻断。
# 测试约束 07：delivery_success=true、safe_to_control=true 必须拒绝。
# 测试约束 08：blocked/missing/rejected/accepted 四类状态都要覆盖。
# 测试约束 09：输出必须保持 source=software_proof 和 not_proven。
# 测试约束 10：所有输出保持 safe_to_control=false。
# 测试约束 11：所有输出保持 delivery_success=false。
# 测试约束 12：所有输出保持 primary_actions_enabled=false。
# 测试约束 13：单测不访问 ROS graph、硬件、外部云或手机 runtime。


class FieldEvidenceRealMaterialResponseIntakeTest(unittest.TestCase):
    def _write_json(self, root: Path, name: str, payload: object) -> Path:
        # 临时 JSON 只服务离线围栏，不模拟真实现场 runtime。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _dispatch_summary(self, evidence_ref: str, ready: bool = True) -> dict[str, object]:
        # 样本沿用上一轮 request dispatch summary 的安全消费面。
        status = intake.READY_DISPATCH_STATUS if ready else "blocked_missing_field_evidence_rerun_execution_result_acceptance_backfill"
        return {
            "schema": "trashbot.field_evidence_real_material_request_dispatch_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_real_material_request_dispatch_gate",
            "status": status,
            "request_dispatch_status": status,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "required_materials": list(intake.REQUIRED_MATERIALS),
            "not_proven": ["not_proven"],
            "safe_copy": {
                "source": "software_proof",
                "status": status,
                "request_dispatch_status": status,
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "required_materials": list(intake.REQUIRED_MATERIALS),
                "not_proven": "not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def _accepted_response(self, evidence_ref: str) -> dict[str, object]:
        # accepted 样本只提供安全索引和 summary，不携带完整材料。
        return {
            "schema": "trashbot.field_evidence_real_material_response_packet.v1",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "materials": {
                name: {
                    "name": name,
                    "status": "accepted",
                    "safe_evidence_ref": evidence_ref,
                    "summary": f"sanitized {name} index ready for later review only",
                    "delivery_success": False,
                    "safe_to_control": False,
                    "primary_actions_enabled": False,
                }
                for name in intake.REQUIRED_MATERIALS
            },
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def _build(
        self,
        root: Path,
        dispatch_payload: dict[str, object],
        response_payload: dict[str, object] | None = None,
        evidence_ref: str = "field-run-101",
    ) -> tuple[dict[str, object], dict[str, object]]:
        # 公共 helper 让 case 聚焦分类和 fail-closed 规则。
        dispatch_path = self._write_json(root, "dispatch.json", dispatch_payload)
        response_path = ""
        if response_payload is not None:
            response_path = str(self._write_json(root, "response.json", response_payload))
        artifact, summary, exit_code = intake.build_field_evidence_real_material_response_intake(
            str(dispatch_path),
            response_path,
            evidence_ref,
        )
        self.assertEqual(exit_code, 0)
        return artifact, summary

    def test_all_safe_materials_are_accepted_for_later_review_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(
                root,
                {"payload": {"summary": self._dispatch_summary("field-run-101")}},
                {"safe_copy": self._accepted_response("field-run-101")},
            )

        self.assertEqual(artifact["schema"], "trashbot.field_evidence_real_material_response_intake.v1")
        self.assertEqual(summary["schema"], "trashbot.field_evidence_real_material_response_intake_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_field_evidence_real_material_response_intake_gate",
        )
        self.assertEqual(artifact["status"], "ready_for_field_evidence_real_material_review_not_proven")
        self.assertEqual(artifact["material_classification_counts"]["accepted"], 9)
        self.assertTrue(all(item["ready_for_later_review_only"] for item in artifact["material_responses"]))
        self.assertIn("not_proven", json.dumps(artifact, ensure_ascii=False))
        self.assertFalse(artifact["safe_to_control"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_missing_response_marks_every_material_blocked_not_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(root, self._dispatch_summary("field-run-102"), None, "field-run-102")

        self.assertEqual(artifact["status"], "blocked_missing_field_owner_response_json")
        self.assertEqual(artifact["material_classification_counts"]["blocked"], 9)
        self.assertEqual(artifact["material_classification_counts"]["accepted"], 0)
        self.assertIn("field_owner_response_json_not_provided", json.dumps(summary, ensure_ascii=False))

    def test_partial_response_classifies_accepted_missing_rejected_and_blocked(self) -> None:
        response = self._accepted_response("field-run-103")
        materials = response["materials"]
        self.assertIsInstance(materials, dict)
        materials["nav2_fixed_route_runtime_log"] = {"status": "missing", "safe_evidence_ref": "field-run-103"}
        materials["route_completion_signal"] = {"status": "rejected", "safe_evidence_ref": "field-run-103"}
        materials["elevator_door_floor_evidence"] = {"status": "blocked", "safe_evidence_ref": "field-run-103"}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, _summary = self._build(root, self._dispatch_summary("field-run-103"), response, "field-run-103")

        counts = artifact["material_classification_counts"]
        self.assertEqual(counts["accepted"], 6)
        self.assertEqual(counts["missing"], 1)
        self.assertEqual(counts["rejected"], 1)
        self.assertEqual(counts["blocked"], 1)
        self.assertEqual(artifact["status"], "blocked_rejected_field_owner_response")

    def test_mixed_ref_unsafe_copy_and_success_claim_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mixed = self._accepted_response("field-run-104")
            mixed["materials"]["task_record"]["safe_evidence_ref"] = "other-run"
            mixed_artifact, _mixed_summary = self._build(root, self._dispatch_summary("field-run-104"), mixed, "field-run-104")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe = self._accepted_response("field-run-105")
            unsafe["materials"]["task_record"]["summary"] = "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 checksum=abcdef123456"
            unsafe_artifact, unsafe_summary = self._build(root, self._dispatch_summary("field-run-105"), unsafe, "field-run-105")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            success = self._accepted_response("field-run-106")
            success["materials"]["delivery_result"]["delivery_success"] = True
            success_artifact, _success_summary = self._build(root, self._dispatch_summary("field-run-106"), success, "field-run-106")

        encoded = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertEqual(mixed_artifact["status"], "blocked_rejected_field_owner_response")
        self.assertEqual(unsafe_artifact["status"], "blocked_rejected_field_owner_response")
        self.assertEqual(success_artifact["status"], "blocked_rejected_field_owner_response")
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("Bearer abc", encoded)
        self.assertFalse(success_artifact["delivery_success"])

    def test_missing_bad_dispatch_and_not_ready_dispatch_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            response = self._accepted_response("field-run-107")
            missing_artifact, missing_summary, _ = intake.build_field_evidence_real_material_response_intake(
                str(root / "missing.json"),
                str(self._write_json(root, "response.json", response)),
                "field-run-107",
            )
            unsupported_artifact, _unsupported_summary = self._build(
                root,
                {"schema": "trashbot.unsupported.v1", "evidence_ref": "field-run-107"},
                response,
                "field-run-107",
            )
            not_ready_artifact, _not_ready_summary = self._build(
                root,
                self._dispatch_summary("field-run-107", ready=False),
                response,
                "field-run-107",
            )

        self.assertEqual(missing_artifact["status"], "blocked_missing_field_evidence_real_material_request_dispatch")
        self.assertEqual(unsupported_artifact["status"], "blocked_unsupported_request_dispatch_schema")
        self.assertEqual(not_ready_artifact["status"], "blocked_request_dispatch_not_ready")
        self.assertFalse(missing_summary["primary_actions_enabled"])

    def test_output_does_not_expose_forbidden_raw_runtime_or_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(
                root,
                self._dispatch_summary("field-run-108"),
                self._accepted_response("field-run-108"),
                "field-run-108",
            )

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB", encoded)
        self.assertNotIn("Traceback", encoded)
        self.assertNotIn("checksum=abcdef", encoded)
        self.assertIn("software_proof_docker_field_evidence_real_material_response_intake_gate", encoded)
        self.assertIn("delivery_success", encoded)
        self.assertFalse(artifact["safe_copy"]["delivery_success"])


if __name__ == "__main__":
    unittest.main()
