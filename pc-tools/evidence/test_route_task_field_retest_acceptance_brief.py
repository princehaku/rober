#!/usr/bin/env python3
"""route_task_field_retest_acceptance_brief 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

import route_task_field_retest_acceptance_brief as brief  # noqa: E402


class RouteTaskFieldRetestAcceptanceBriefTest(unittest.TestCase):
    def _write_drill_console(self, path: Path, evidence_ref: str = "ev-brief-001", **extra: object) -> dict[str, object]:
        # fixture 只写 drill console 摘要字段，保持 Docker-only software proof 边界。
        missing = list(extra.pop("missing_materials", []))
        payload: dict[str, object] = {
            "schema": "trashbot.route_task_field_retest_drill_console.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_retest_drill_console_gate",
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "console_status": "ready_for_drill_console_not_proven",
            "command_labels": ["material_pack", "result_intake", "result_reconciliation"],
            "missing_materials": missing,
            "safe_checklist": ["Keep delivery_success=false and primary_actions_enabled=false until real review closes."],
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        path.write_text(json.dumps(payload), encoding="utf-8")
        return payload

    def test_ready_brief_contains_acceptance_summary_and_required_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            console_path = root / "drill_console.json"
            self._write_drill_console(console_path, evidence_ref="ev-brief-001")

            artifact, summary, exit_code = brief.build_route_task_field_retest_acceptance_brief(str(console_path), "ev-brief-001")

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.route_task_field_retest_acceptance_brief.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_acceptance_brief_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_acceptance_brief_gate",
        )
        self.assertEqual(artifact["acceptance_status"], "ready_for_field_retest_acceptance_brief_not_proven")
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        packet_names = [item["name"] for item in summary["required_evidence_packet"]]
        self.assertEqual(
            packet_names,
            [
                "nav2_or_fixed_route_runtime_log",
                "route_completion_signal",
                "task_record",
                "door_state",
                "target_floor_confirmation",
                "human_assistance_note",
                "dropoff_or_cancel_completion",
                "delivery_result",
            ],
        )
        self.assertIn("delivery_success=false", summary["execution_checklist"][-1])
        self.assertIn("primary_actions_enabled=false", summary["execution_checklist"][-1])

    def test_wrapper_summary_input_and_missing_packet_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrapper_path = root / "wrapper.json"
            summary = {
                "schema": "trashbot.route_task_field_retest_drill_console_summary.v1",
                "evidence_boundary": "software_proof_docker_route_task_field_retest_drill_console_gate",
                "evidence_ref": "ev-brief-002",
                "same_evidence_ref_required": True,
                "console_status": "ready_for_drill_console_not_proven",
                "missing_materials": ["door_state", "target_floor_confirmation"],
                "delivery_success": False,
                "primary_actions_enabled": False,
            }
            wrapper_path.write_text(json.dumps({"payload": {"summary": summary}}), encoding="utf-8")

            artifact, summary_out, _exit_code = brief.build_route_task_field_retest_acceptance_brief(str(wrapper_path), "")

        self.assertEqual(artifact["acceptance_status"], "ready_for_field_retest_acceptance_brief_not_proven")
        self.assertEqual(summary_out["evidence_ref"], "ev-brief-002")
        self.assertIn("door_state", summary_out["field_entry_prerequisites"][-1])
        packet_status = {item["name"]: item["current_status"] for item in summary_out["required_evidence_packet"]}
        self.assertEqual(packet_status["door_state"], "missing_in_source_summary")
        self.assertEqual(packet_status["target_floor_confirmation"], "missing_in_source_summary")

    def test_unsupported_schema_boundary_and_weak_same_ref_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad_schema = root / "bad_schema.json"
            self._write_drill_console(bad_schema, schema="trashbot.other.v1")
            weak_ref = root / "weak_ref.json"
            self._write_drill_console(weak_ref, same_evidence_ref_required="true")

            artifact_schema, _summary_schema, _ = brief.build_route_task_field_retest_acceptance_brief(str(bad_schema), "ev-brief-001")
            artifact_ref, _summary_ref, _ = brief.build_route_task_field_retest_acceptance_brief(str(weak_ref), "ev-brief-001")

        self.assertEqual(artifact_schema["acceptance_status"], "blocked_unsupported_schema")
        self.assertEqual(artifact_ref["acceptance_status"], "blocked_same_evidence_ref_not_required")

    def test_evidence_ref_mismatch_not_ready_and_unsafe_copy_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mismatch = root / "mismatch.json"
            self._write_drill_console(mismatch, evidence_ref="source-ref")
            not_ready = root / "not_ready.json"
            self._write_drill_console(not_ready, console_status="blocked_operator_drill_not_ready")
            unsafe = root / "unsafe.json"
            self._write_drill_console(unsafe, operator_note="raw path /Users/m4/secret.log")
            success = root / "success.json"
            self._write_drill_console(success, delivery_success=True)

            artifact_mismatch, _summary_mismatch, _ = brief.build_route_task_field_retest_acceptance_brief(str(mismatch), "requested-ref")
            artifact_not_ready, _summary_not_ready, _ = brief.build_route_task_field_retest_acceptance_brief(str(not_ready), "ev-brief-001")
            artifact_unsafe, summary_unsafe, _ = brief.build_route_task_field_retest_acceptance_brief(str(unsafe), "ev-brief-001")
            artifact_success, _summary_success, _ = brief.build_route_task_field_retest_acceptance_brief(str(success), "ev-brief-001")

        self.assertEqual(artifact_mismatch["acceptance_status"], "blocked_same_evidence_ref_mismatch")
        self.assertEqual(artifact_not_ready["acceptance_status"], "blocked_drill_console_not_ready")
        self.assertEqual(artifact_unsafe["acceptance_status"], "blocked_unsafe_drill_console_copy")
        self.assertEqual(artifact_success["acceptance_status"], "blocked_unsafe_drill_console_copy")
        encoded_summary = json.dumps(summary_unsafe, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)
        self.assertNotIn("Authorization", encoded_summary)

    def test_missing_input_writes_blocked_not_proven_shape(self) -> None:
        artifact, summary, _exit_code = brief.build_route_task_field_retest_acceptance_brief(
            "/tmp/route_task_field_retest_acceptance_brief_missing.json", "ev-brief-003"
        )

        self.assertEqual(artifact["acceptance_status"], "blocked_missing_drill_console")
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
