#!/usr/bin/env python3
"""route_task_field_retest_callback_intake 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

import route_task_field_retest_callback_intake as intake  # noqa: E402


class RouteTaskFieldRetestCallbackIntakeTest(unittest.TestCase):
    def _dispatch_payload(self, evidence_ref: str = "ev-callback-001", **extra: object) -> dict[str, object]:
        # fixture 只表达 dispatch 摘要，避免把真实材料目录引入 callback intake。
        packet = [
            {"name": name, "recommended_filename": f"field_retest_packet/{evidence_ref}/{name}.json"}
            for name in intake.REQUIRED_EVIDENCE_PACKET
        ]
        payload: dict[str, object] = {
            "schema": "trashbot.route_task_field_retest_evidence_dispatch.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_retest_evidence_dispatch_gate",
            "status": "ready_for_field_retest_evidence_dispatch_not_proven",
            "dispatch_status": "ready_for_field_retest_evidence_dispatch_not_proven",
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "required_evidence_packet": packet,
            "recommended_filenames": [item["recommended_filename"] for item in packet],
            "material_owners": {
                "Autonomy Algorithm Engineer": [
                    "nav2_or_fixed_route_runtime_log",
                    "route_completion_signal",
                    "door_state",
                    "target_floor_confirmation",
                ],
                "Robot Platform Engineer": ["task_record", "dropoff_or_cancel_completion"],
                "Product Manager / OKR Owner": ["human_assistance_note", "delivery_result"],
            },
            "safe_copy": {
                "evidence_ref": evidence_ref,
                "not_proven": "not_proven",
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        return payload

    def _callback_payload(self, evidence_ref: str = "ev-callback-001", received: bool = True, **extra: object) -> dict[str, object]:
        # callback 只包含现场同学脱敏元数据；收到状态必须是严格 bool。
        received_status = {
            f"field_retest_packet/{evidence_ref}/{name}.json": received
            for name in intake.REQUIRED_EVIDENCE_PACKET
        }
        payload: dict[str, object] = {
            "schema": "trashbot.route_task_field_retest_callback.v1",
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "recommended_filename_received_status": received_status,
            "missing_material_ids": [] if received else ["delivery_result"],
            "next_backfill_action": "send_sanitized_material_summary_to_result_intake",
            "owner_callback_note": "sanitized callback metadata only",
            "callback_checklist_result": {
                "same evidence_ref checked": True,
                "no raw logs attached": True,
                "no success wording": True,
            },
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        return payload

    def test_ready_callback_intake_contains_safe_summary_and_required_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dispatch_path = root / "dispatch.json"
            callback_path = root / "callback.json"
            dispatch_path.write_text(json.dumps(self._dispatch_payload()), encoding="utf-8")
            callback_path.write_text(json.dumps(self._callback_payload()), encoding="utf-8")

            artifact, summary, exit_code = intake.build_route_task_field_retest_callback_intake(
                str(dispatch_path),
                str(callback_path),
                "ev-callback-001",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.route_task_field_retest_callback_intake.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_callback_intake_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_callback_intake_gate",
        )
        self.assertEqual(artifact["intake_status"], "ready_for_field_retest_callback_intake_not_proven")
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertEqual(summary["same_evidence_ref_match"]["status"], "matched")
        self.assertTrue(summary["received_filenames_summary"]["all_recommended_received"])
        self.assertEqual(summary["missing_materials"], [])
        packet_names = [item["name"] for item in summary["required_evidence_packet"]]
        self.assertEqual(packet_names, list(intake.REQUIRED_EVIDENCE_PACKET))

    def test_wrapper_dispatch_and_nested_callback_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dispatch_path = root / "dispatch_wrapper.json"
            callback_path = root / "callback_wrapper.json"
            dispatch_path.write_text(json.dumps({"payload": {"summary": self._dispatch_payload("ev-callback-002")}}), encoding="utf-8")
            callback_path.write_text(
                json.dumps({"payload": {"field_callback": self._callback_payload("ev-callback-002", received=False)}}),
                encoding="utf-8",
            )

            artifact, summary, _exit_code = intake.build_route_task_field_retest_callback_intake(
                str(dispatch_path),
                str(callback_path),
                "",
            )

        self.assertEqual(artifact["intake_status"], "ready_for_field_retest_callback_intake_not_proven")
        self.assertEqual(summary["evidence_ref"], "ev-callback-002")
        self.assertGreater(summary["received_filenames_summary"]["missing_count"], 0)
        self.assertIn("delivery_result", summary["missing_materials"])
        self.assertEqual(summary["next_backfill_action"], "collect_missing_materials_then_rerun_result_intake")

    def test_missing_bad_json_unsupported_schema_and_ref_mismatch_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dispatch_path = root / "dispatch.json"
            callback_path = root / "callback.json"
            bad_json = root / "bad.json"
            bad_schema = root / "bad_schema.json"
            mismatch_callback = root / "mismatch_callback.json"
            dispatch_path.write_text(json.dumps(self._dispatch_payload()), encoding="utf-8")
            callback_path.write_text(json.dumps(self._callback_payload()), encoding="utf-8")
            bad_json.write_text("{bad-json", encoding="utf-8")
            bad_schema.write_text(json.dumps(self._dispatch_payload(schema="trashbot.other.v1")), encoding="utf-8")
            mismatch_callback.write_text(json.dumps(self._callback_payload("other-ref")), encoding="utf-8")

            missing_artifact, _summary_missing, _ = intake.build_route_task_field_retest_callback_intake(
                str(root / "missing.json"),
                str(callback_path),
                "ev-callback-001",
            )
            bad_artifact, _summary_bad, _ = intake.build_route_task_field_retest_callback_intake(
                str(dispatch_path),
                str(bad_json),
                "ev-callback-001",
            )
            schema_artifact, _summary_schema, _ = intake.build_route_task_field_retest_callback_intake(
                str(bad_schema),
                str(callback_path),
                "ev-callback-001",
            )
            mismatch_artifact, _summary_mismatch, _ = intake.build_route_task_field_retest_callback_intake(
                str(dispatch_path),
                str(mismatch_callback),
                "ev-callback-001",
            )

        self.assertEqual(missing_artifact["intake_status"], "blocked_missing_dispatch_json")
        self.assertEqual(bad_artifact["intake_status"], "blocked_bad_json")
        self.assertEqual(schema_artifact["intake_status"], "blocked_unsupported_dispatch_schema")
        self.assertEqual(mismatch_artifact["intake_status"], "blocked_same_evidence_ref_mismatch")

    def test_weak_callback_unsafe_copy_and_success_claim_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dispatch_path = root / "dispatch.json"
            weak_callback = root / "weak_callback.json"
            unsafe_callback = root / "unsafe_callback.json"
            success_callback = root / "success_callback.json"
            dispatch_path.write_text(json.dumps(self._dispatch_payload()), encoding="utf-8")
            weak_payload = self._callback_payload()
            weak_payload["recommended_filename_received_status"] = {"field_retest_packet/ev-callback-001/task_record.json": "yes"}
            weak_callback.write_text(json.dumps(weak_payload), encoding="utf-8")
            unsafe_callback.write_text(
                json.dumps(self._callback_payload(owner_callback_note="raw path /Users/m4/secret.log /cmd_vel")),
                encoding="utf-8",
            )
            success_callback.write_text(json.dumps(self._callback_payload(delivery_success=True)), encoding="utf-8")

            weak_artifact, _weak_summary, _ = intake.build_route_task_field_retest_callback_intake(
                str(dispatch_path),
                str(weak_callback),
                "ev-callback-001",
            )
            unsafe_artifact, unsafe_summary, _ = intake.build_route_task_field_retest_callback_intake(
                str(dispatch_path),
                str(unsafe_callback),
                "ev-callback-001",
            )
            success_artifact, _success_summary, _ = intake.build_route_task_field_retest_callback_intake(
                str(dispatch_path),
                str(success_callback),
                "ev-callback-001",
            )

        self.assertEqual(weak_artifact["intake_status"], "blocked_weak_callback_fields")
        self.assertEqual(unsafe_artifact["intake_status"], "blocked_unsafe_copy")
        self.assertEqual(success_artifact["intake_status"], "blocked_unsafe_copy")
        encoded_summary = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)
        self.assertNotIn("Authorization", encoded_summary)

    def test_unknown_callback_field_and_material_id_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dispatch_path = root / "dispatch.json"
            unknown_field = root / "unknown_field.json"
            unknown_material = root / "unknown_material.json"
            dispatch_path.write_text(json.dumps(self._dispatch_payload()), encoding="utf-8")
            unknown_field.write_text(json.dumps(self._callback_payload(raw_log="/tmp/log.txt")), encoding="utf-8")
            unknown_material.write_text(
                json.dumps(self._callback_payload(missing_material_ids=["new_sensor_blob"])),
                encoding="utf-8",
            )

            field_artifact, _field_summary, _ = intake.build_route_task_field_retest_callback_intake(
                str(dispatch_path),
                str(unknown_field),
                "ev-callback-001",
            )
            material_artifact, _material_summary, _ = intake.build_route_task_field_retest_callback_intake(
                str(dispatch_path),
                str(unknown_material),
                "ev-callback-001",
            )

        self.assertEqual(field_artifact["intake_status"], "blocked_unsupported_callback_schema_or_fields")
        self.assertEqual(material_artifact["intake_status"], "blocked_unsupported_missing_material_ids")


if __name__ == "__main__":
    unittest.main()
