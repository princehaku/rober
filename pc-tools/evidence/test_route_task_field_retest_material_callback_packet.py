#!/usr/bin/env python3
"""route_task_field_retest_material_callback_packet 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

import route_task_field_retest_material_callback_packet as packet  # noqa: E402


# 测试约束 01：fixture 只表达 material pack，不创建材料目录。
# 测试约束 02：ready case 只能证明 callback packet metadata readiness。
# 测试约束 03：ready case 仍必须保留 delivery_success=false。
# 测试约束 04：ready case 仍必须保留 primary_actions_enabled=false。
# 测试约束 05：ready case 仍必须保留 not_proven。
# 测试约束 06：wrapper case 覆盖 material pack artifact/summary/nested diagnostics。
# 测试约束 07：unsupported case 验证 schema 或 boundary 漂移必须 fail closed。
# 测试约束 08：weak evidence_ref case 验证路径、空值和弱值不能通过。
# 测试约束 09：mismatch case 验证 CLI evidence_ref 不能静默覆盖 source。
# 测试约束 10：unsafe case 验证 raw path、credential 和 token 不进入 summary。
# 测试约束 11：success case 验证 delivery_success=true 和 action enablement 被阻断。
# 测试约束 12：单测不访问 ROS graph、Nav2 runtime、硬件或外部云。
# 测试约束 13：单测不访问 phone/browser、serial/UART 或 WAVE ROVER。
# 测试约束 14：所有断言围绕契约字段，不依赖生成时间。
# 测试约束 15：新增 callback_packet_status 必须同步文档和测试。


class RouteTaskFieldRetestMaterialCallbackPacketTest(unittest.TestCase):
    def _material_pack_payload(
        self,
        evidence_ref: str = "ev-material-callback-001",
        status: str = "ready_for_field_retest_material_collection_not_proven",
        **extra: object,
    ) -> dict[str, object]:
        # fixture 只表达上一轮 material pack 摘要，不包含真实材料正文或 raw path。
        checklist = [
            {
                "material": name,
                "safe_evidence_ref": evidence_ref,
                "collection_status": "required_not_collected",
                "not_proven": "not_proven",
                "delivery_success": False,
                "primary_actions_enabled": False,
            }
            for name in packet.FIELD_CALLBACK_MATERIALS
        ]
        payload: dict[str, object] = {
            "schema": "trashbot.route_task_field_retest_material_pack_summary.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_retest_material_pack_gate",
            "status": status,
            "material_pack_status": status,
            "material_pack_verdict": status,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "field_capture_checklist": checklist,
            "callback_payload_skeleton": {
                "safe_evidence_ref": evidence_ref,
                "materials": checklist,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "accepted_materials": [],
            "missing_materials": list(packet.FIELD_CALLBACK_MATERIALS),
            "rejected_materials": [],
            "rerun_commands": [
                "python3 pc-tools/evidence/route_task_field_retest_material_pack.py --result-review-handoff-json <handoff.json> --once-json"
            ],
            "safe_copy": {
                "material_pack_status": status,
                "safe_evidence_ref": evidence_ref,
                "same_evidence_ref_required": True,
                "not_proven": "not_proven",
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "not_proven": ["real_delivery_success"],
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        return payload

    def _write_json(self, root: Path, name: str, payload: dict[str, object] | str) -> Path:
        # 测试只写临时 JSON，保证 gate 不依赖 ROS2、Nav2、硬件或外部云。
        path = root / name
        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _build(self, root: Path, payload: dict[str, object] | str, evidence_ref: str = "ev-material-callback-001") -> tuple[dict, dict]:
        # 公共 helper 让 case 聚焦 schema、boundary 和 fail-closed 规则。
        path = self._write_json(root, "material_pack.json", payload)
        artifact, summary, exit_code = packet.build_route_task_field_retest_material_callback_packet(
            str(path),
            evidence_ref,
        )
        self.assertEqual(exit_code, 0)
        return artifact, summary

    def test_ready_material_pack_generates_callback_packet_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(root, self._material_pack_payload())

        self.assertEqual(artifact["schema"], "trashbot.route_task_field_retest_material_callback_packet.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_material_callback_packet_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_material_callback_packet_gate",
        )
        self.assertEqual(artifact["source_schema"], "trashbot.route_task_field_retest_material_pack_summary.v1")
        self.assertEqual(artifact["source_boundary"], "software_proof_docker_route_task_field_retest_material_pack_gate")
        self.assertEqual(artifact["callback_packet_status"], "ready_for_field_material_callback_not_proven")
        self.assertEqual(summary["source_schema"], "trashbot.route_task_field_retest_material_callback_packet.v1")
        self.assertEqual(len(summary["field_callback_items"]), len(packet.FIELD_CALLBACK_MATERIALS))
        self.assertEqual(summary["field_callback_items"][0]["callback_status"], "pending_owner_callback")
        self.assertEqual(summary["owner_acknowledgement"]["acknowledgement_status"], "pending_owner_acknowledgement")
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("real_delivery_success", summary["not_proven"])

    def test_artifact_wrapper_and_nested_diagnostics_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrapped_artifact = {
                "payload": {
                    "nested_diagnostics": {
                        "route_task_field_retest_material_pack": self._material_pack_payload(
                            evidence_ref="ev-material-callback-002",
                            schema="trashbot.route_task_field_retest_material_pack.v1",
                        )
                    }
                }
            }
            artifact, summary = self._build(root, wrapped_artifact, "ev-material-callback-002")

        self.assertEqual(artifact["callback_packet_status"], "ready_for_field_material_callback_not_proven")
        self.assertEqual(summary["safe_evidence_ref"], "ev-material-callback-002")
        self.assertEqual(artifact["source_schema"], "trashbot.route_task_field_retest_material_pack.v1")

    def test_missing_unsupported_bad_boundary_and_not_ready_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad_schema = self._write_json(root, "bad_schema.json", self._material_pack_payload(schema="trashbot.other.v1"))
            bad_boundary = self._write_json(root, "bad_boundary.json", self._material_pack_payload(evidence_boundary="wrong_boundary"))
            not_ready = self._write_json(
                root,
                "not_ready.json",
                self._material_pack_payload(status="needs_result_review_handoff_not_proven"),
            )
            no_items_payload = self._material_pack_payload()
            no_items_payload.pop("field_capture_checklist")
            no_items = self._write_json(root, "no_items.json", no_items_payload)

            missing_artifact, _missing_summary, _ = packet.build_route_task_field_retest_material_callback_packet(
                str(root / "missing.json"),
                "ev-material-callback-001",
            )
            schema_artifact, _schema_summary, _ = packet.build_route_task_field_retest_material_callback_packet(
                str(bad_schema),
                "ev-material-callback-001",
            )
            boundary_artifact, _boundary_summary, _ = packet.build_route_task_field_retest_material_callback_packet(
                str(bad_boundary),
                "ev-material-callback-001",
            )
            not_ready_artifact, _not_ready_summary, _ = packet.build_route_task_field_retest_material_callback_packet(
                str(not_ready),
                "ev-material-callback-001",
            )
            no_items_artifact, _no_items_summary, _ = packet.build_route_task_field_retest_material_callback_packet(
                str(no_items),
                "ev-material-callback-001",
            )

        self.assertEqual(missing_artifact["callback_packet_status"], "needs_material_pack_not_proven")
        self.assertEqual(schema_artifact["callback_packet_status"], "unsupported_material_pack_schema_not_proven")
        self.assertEqual(boundary_artifact["callback_packet_status"], "unsupported_material_pack_schema_not_proven")
        self.assertEqual(not_ready_artifact["callback_packet_status"], "needs_material_pack_not_proven")
        self.assertEqual(no_items_artifact["callback_packet_status"], "blocked_missing_callback_materials_not_proven")

    def test_mismatch_weak_same_ref_and_weak_evidence_ref_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mismatch_artifact, _mismatch_summary = self._build(root, self._material_pack_payload(), "other-ref")
            weak_same_ref_artifact, _weak_summary = self._build(
                root,
                self._material_pack_payload(same_evidence_ref_required="true"),
            )
            weak_ref_artifact, _weak_ref_summary = self._build(
                root,
                self._material_pack_payload(evidence_ref="ev"),
                "ev",
            )

        self.assertEqual(mismatch_artifact["callback_packet_status"], "evidence_ref_mismatch_rerun_not_proven")
        self.assertEqual(weak_same_ref_artifact["callback_packet_status"], "evidence_ref_mismatch_rerun_not_proven")
        self.assertEqual(weak_ref_artifact["callback_packet_status"], "evidence_ref_mismatch_rerun_not_proven")

    def test_unsafe_raw_path_credentials_token_and_success_claim_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe_path_artifact, unsafe_path_summary = self._build(
                root,
                self._material_pack_payload(owner_work_orders=[{"note": "raw /Users/m4/private.log /cmd_vel"}]),
            )
            credential_artifact, credential_summary = self._build(
                root,
                self._material_pack_payload(owner_work_orders=[{"note": "token=secret-value db_url=postgres://hidden"}]),
            )
            success_artifact, _success_summary = self._build(
                root,
                self._material_pack_payload(delivery_success=True),
            )
            enabled_artifact, _enabled_summary = self._build(
                root,
                self._material_pack_payload(primary_actions_enabled=True),
            )

        self.assertEqual(unsafe_path_artifact["callback_packet_status"], "unsupported_material_pack_schema_not_proven")
        self.assertEqual(credential_artifact["callback_packet_status"], "unsupported_material_pack_schema_not_proven")
        self.assertEqual(success_artifact["callback_packet_status"], "unsafe_success_claim_rejected_not_proven")
        self.assertEqual(enabled_artifact["callback_packet_status"], "unsafe_success_claim_rejected_not_proven")
        encoded_path = json.dumps(unsafe_path_summary, ensure_ascii=False)
        encoded_credential = json.dumps(credential_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_path)
        self.assertNotIn("/cmd_vel", encoded_path)
        self.assertNotIn("secret-value", encoded_credential)
        self.assertNotIn("postgres://hidden", encoded_credential)


if __name__ == "__main__":
    unittest.main()
