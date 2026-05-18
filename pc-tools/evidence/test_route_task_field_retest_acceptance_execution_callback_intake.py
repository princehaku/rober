#!/usr/bin/env python3
"""route_task_field_retest_acceptance_execution_callback_intake 的离线围栏测试。"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

import route_task_field_retest_acceptance_execution_callback_intake as intake  # noqa: E402


class RouteTaskFieldRetestAcceptanceExecutionCallbackIntakeTest(unittest.TestCase):
    def _pack_payload(self, evidence_ref: str = "ev-accept-callback-001", ready: bool = True, **extra: object) -> dict[str, object]:
        # fixture 只表达 execution pack 安全摘要，避免引入真实材料目录。
        status = "ready_for_field_retest_acceptance_execution_pack_not_proven" if ready else "blocked_acceptance_review_decision_not_ready"
        materials = [
            "nav2_or_fixed_route_runtime_log",
            "route_completion_signal",
            "task_record",
            "door_state",
            "target_floor_confirmation",
            "human_assistance_note",
            "dropoff_or_cancel_completion",
            "delivery_result",
            "diagnostics_mobile_safe_summary",
        ]
        payload: dict[str, object] = {
            "schema": "trashbot.route_task_field_retest_acceptance_execution_pack.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_retest_acceptance_execution_pack_gate",
            "status": status,
            "execution_pack_status": status,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "required_route_elevator_materials": materials,
            "safe_evidence_bundle": {
                "safe_evidence_ref": evidence_ref,
                "required_route_elevator_materials": materials,
                "not_proven": "not_proven",
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        return payload

    def _callback_payload(self, evidence_ref: str = "ev-accept-callback-001", **extra: object) -> dict[str, object]:
        # callback packet 逐项回应 execution pack 的 required materials。
        materials = [
            "nav2_or_fixed_route_runtime_log",
            "route_completion_signal",
            "task_record",
            "door_state",
            "target_floor_confirmation",
            "human_assistance_note",
            "dropoff_or_cancel_completion",
            "delivery_result",
            "diagnostics_mobile_safe_summary",
        ]
        payload: dict[str, object] = {
            "schema": "trashbot.route_task_field_retest_acceptance_execution_callback_packet.v1",
            "safe_evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "material_responses": [
                {"material": material, "status": "received", "safe_note": f"{material} callback metadata received"}
                for material in materials
            ],
            "owner_next_steps": [],
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

    def _build(self, root: Path, execution_pack: dict[str, object] | str, callback: dict[str, object] | str, evidence_ref: str = "ev-accept-callback-001") -> tuple[dict, dict]:
        # 公共 helper 让 case 聚焦 schema、boundary 和 fail-closed 规则。
        pack_path = self._write_json(root, "execution_pack.json", execution_pack)
        callback_path = self._write_json(root, "callback.json", callback)
        artifact, summary, exit_code = intake.build_route_task_field_retest_acceptance_execution_callback_intake(
            str(pack_path),
            str(callback_path),
            evidence_ref,
        )
        self.assertEqual(exit_code, 0)
        return artifact, summary

    def test_ready_callback_intake_contains_safe_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(root, self._pack_payload(), self._callback_payload())

        self.assertEqual(artifact["schema"], "trashbot.route_task_field_retest_acceptance_execution_callback_intake.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_acceptance_execution_callback_intake_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_acceptance_execution_callback_intake_gate",
        )
        self.assertEqual(
            artifact["callback_intake_status"],
            "ready_for_field_retest_acceptance_execution_callback_intake_not_proven",
        )
        self.assertEqual(summary["evidence_ref_status"]["status"], "matched")
        self.assertEqual(len(summary["received_materials"]), 9)
        self.assertEqual(summary["missing_materials"], [])
        self.assertEqual(summary["rejected_materials"], [])
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertIn("route_task_field_retest_acceptance_execution_callback_intake.py", " ".join(summary["rerun_commands"]))
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_nested_file_env_sources_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack_path = self._write_json(root, "nested_pack.json", {"payload": {"summary": self._pack_payload("ev-accept-callback-002")}})
            callback_path = self._write_json(
                root,
                "nested_callback.json",
                {"payload": {"safe_callback_packet": self._callback_payload("ev-accept-callback-002")}},
            )
            os.environ["ROBER_ACCEPTANCE_EXECUTION_PACK_JSON"] = f"file:{pack_path}"
            try:
                artifact, summary, _ = intake.build_route_task_field_retest_acceptance_execution_callback_intake(
                    "env:ROBER_ACCEPTANCE_EXECUTION_PACK_JSON",
                    f"file:{callback_path}",
                    "ev-accept-callback-002",
                )
            finally:
                os.environ.pop("ROBER_ACCEPTANCE_EXECUTION_PACK_JSON", None)

        self.assertEqual(artifact["callback_intake_status"], "ready_for_field_retest_acceptance_execution_callback_intake_not_proven")
        self.assertEqual(summary["safe_evidence_ref"], "ev-accept-callback-002")
        self.assertEqual(summary["source_execution_pack"]["schema_status"], "supported")
        self.assertEqual(summary["source_execution_pack"]["source_style"], "env_source")
        self.assertEqual(summary["safe_callback_packet"]["field_status"], "supported")

    def test_missing_bad_json_unsupported_schema_and_pack_not_ready_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            callback_path = self._write_json(root, "callback.json", self._callback_payload())
            pack_path = self._write_json(root, "execution_pack.json", self._pack_payload())
            bad_json = self._write_json(root, "bad.json", "{bad-json")
            bad_schema = self._write_json(root, "bad_schema.json", self._pack_payload(schema="trashbot.unsupported.v1"))
            not_ready = self._write_json(root, "not_ready.json", self._pack_payload(ready=False))

            missing_artifact, _missing_summary, _ = intake.build_route_task_field_retest_acceptance_execution_callback_intake(
                str(root / "missing.json"),
                str(callback_path),
                "ev-accept-callback-001",
            )
            bad_artifact, _bad_summary, _ = intake.build_route_task_field_retest_acceptance_execution_callback_intake(
                str(pack_path),
                str(bad_json),
                "ev-accept-callback-001",
            )
            schema_artifact, _schema_summary, _ = intake.build_route_task_field_retest_acceptance_execution_callback_intake(
                str(bad_schema),
                str(callback_path),
                "ev-accept-callback-001",
            )
            not_ready_artifact, _not_ready_summary, _ = intake.build_route_task_field_retest_acceptance_execution_callback_intake(
                str(not_ready),
                str(callback_path),
                "ev-accept-callback-001",
            )

        self.assertEqual(missing_artifact["callback_intake_status"], "blocked_missing_execution_pack_json")
        self.assertEqual(bad_artifact["callback_intake_status"], "blocked_bad_json")
        self.assertEqual(schema_artifact["callback_intake_status"], "blocked_unsupported_execution_pack_schema_or_boundary")
        self.assertEqual(not_ready_artifact["callback_intake_status"], "blocked_execution_pack_not_ready")

    def test_evidence_ref_mismatch_weak_bool_missing_and_rejected_materials_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mismatch_artifact, _mismatch_summary = self._build(root, self._pack_payload(), self._callback_payload("other-ref"))
            weak_bool_artifact, _weak_summary = self._build(
                root,
                self._pack_payload(same_evidence_ref_required="true"),
                self._callback_payload(same_evidence_ref_required="true"),
            )
            missing_callback = self._callback_payload()
            missing_callback["material_responses"] = [
                {"material": "nav2_or_fixed_route_runtime_log", "status": "received", "safe_note": "metadata received"}
            ]
            missing_artifact, missing_summary = self._build(root, self._pack_payload(), missing_callback)
            rejected_callback = self._callback_payload()
            rejected_callback["rejected_materials"] = [{"material": "door_state", "safe_note": "needs safer summary"}]
            rejected_artifact, rejected_summary = self._build(root, self._pack_payload(), rejected_callback)

        self.assertEqual(mismatch_artifact["callback_intake_status"], "blocked_same_evidence_ref_mismatch")
        self.assertEqual(weak_bool_artifact["callback_intake_status"], "blocked_same_evidence_ref_not_required")
        self.assertEqual(missing_artifact["callback_intake_status"], "blocked_missing_callback_materials")
        self.assertIn("door_state", json.dumps(missing_summary["missing_materials"], ensure_ascii=False))
        self.assertEqual(rejected_artifact["callback_intake_status"], "blocked_rejected_callback_materials")
        self.assertIn("needs safer summary", json.dumps(rejected_summary["rejected_materials"], ensure_ascii=False))

    def test_weak_callback_unsafe_copy_success_claim_and_unknown_field_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            weak = self._callback_payload()
            weak["material_responses"] = {"door_state": True}
            weak_artifact, _weak_summary = self._build(root, self._pack_payload(), weak)
            unsafe_artifact, unsafe_summary = self._build(
                root,
                self._pack_payload(),
                self._callback_payload(owner_next_steps=["raw /Users/m4/secret.log /cmd_vel checksum=abcdef123456"]),
            )
            success_artifact, _success_summary = self._build(
                root,
                self._pack_payload(),
                self._callback_payload(delivery_success=True),
            )
            unknown_artifact, _unknown_summary = self._build(
                root,
                self._pack_payload(),
                self._callback_payload(raw_log="/tmp/log.txt"),
            )

        self.assertEqual(weak_artifact["callback_intake_status"], "blocked_weak_callback_fields")
        self.assertEqual(unsafe_artifact["callback_intake_status"], "blocked_unsafe_copy")
        self.assertEqual(success_artifact["callback_intake_status"], "blocked_unsafe_copy")
        self.assertEqual(unknown_artifact["callback_intake_status"], "blocked_unsupported_callback_packet_schema_or_fields")
        encoded = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("abcdef123456", encoded)


if __name__ == "__main__":
    unittest.main()
