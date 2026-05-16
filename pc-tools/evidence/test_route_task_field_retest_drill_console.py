#!/usr/bin/env python3
"""route_task_field_retest_drill_console 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

import route_task_field_retest_drill_console as console  # noqa: E402


class RouteTaskFieldRetestDrillConsoleTest(unittest.TestCase):
    def _write_operator_drill(self, path: Path, evidence_ref: str = "ev-console-001", **extra: object) -> dict[str, object]:
        # fixture 只写 operator drill 摘要字段，保持 Docker-only software proof 边界。
        missing = list(extra.pop("missing_materials", []))
        payload: dict[str, object] = {
            "schema": "trashbot.route_task_field_retest_operator_drill.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_retest_operator_drill_gate",
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "operator_drill_verdict": "ready_for_operator_drill_not_proven",
            "material_count": {
                "required_count": 8,
                "accepted_count": 8 - len(missing),
                "missing_count": len(missing),
                "is_complete": not missing,
            },
            "missing_materials": missing,
            "command_chain": [
                {"label": "material_pack", "command": "python3 pc-tools/evidence/route_task_field_retest_material_pack.py --material-dir <material_dir>"},
                {"label": "result_intake", "command": "python3 pc-tools/evidence/route_task_field_retest_result_intake.py --result-json <material_pack_summary.json>"},
                {
                    "label": "result_reconciliation",
                    "command": "python3 pc-tools/evidence/route_task_field_retest_result_reconciliation.py --result-json <result_intake.json>",
                },
            ],
            "missing_material_prompts": ["Confirm all material summaries keep evidence_ref=ev-console-001 before intake."],
            "operator_callback_checklist": ["Run result intake first, then result reconciliation; keep diagnostics and mobile read-only."],
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        path.write_text(json.dumps(payload), encoding="utf-8")
        return payload

    def test_ready_console_links_command_labels_and_safe_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            drill_path = root / "operator_drill.json"
            self._write_operator_drill(drill_path, evidence_ref="ev-console-001")

            artifact, summary, exit_code = console.build_route_task_field_retest_drill_console(str(drill_path), "ev-console-001")

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.route_task_field_retest_drill_console.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_drill_console_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_drill_console_gate",
        )
        self.assertEqual(artifact["console_status"], "ready_for_drill_console_not_proven")
        self.assertEqual(summary["command_labels"], ["material_pack", "result_intake", "result_reconciliation"])
        self.assertIn("material_pack", summary["safe_checklist"][0])
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_wrapper_summary_input_and_missing_material_prompts_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrapper_path = root / "wrapper.json"
            summary = {
                "schema": "trashbot.route_task_field_retest_operator_drill_summary.v1",
                "evidence_boundary": "software_proof_docker_route_task_field_retest_operator_drill_gate",
                "evidence_ref": "ev-console-002",
                "same_evidence_ref_required": True,
                "operator_drill_verdict": "ready_for_operator_drill_not_proven",
                "material_count": {"required_count": 8, "accepted_count": 6, "missing_count": 2, "is_complete": False},
                "missing_materials": ["door_state", "target_floor_confirmation"],
                "delivery_success": False,
                "primary_actions_enabled": False,
            }
            wrapper_path.write_text(json.dumps({"payload": {"summary": summary}}), encoding="utf-8")

            artifact, summary_out, _exit_code = console.build_route_task_field_retest_drill_console(str(wrapper_path), "")

        self.assertEqual(artifact["console_status"], "ready_for_drill_console_not_proven")
        self.assertEqual(summary_out["evidence_ref"], "ev-console-002")
        self.assertEqual(summary_out["missing_materials"], ["door_state", "target_floor_confirmation"])
        self.assertIn("Collect door_state metadata", summary_out["missing_material_prompts"][0])
        self.assertFalse(summary_out["safe_copy"]["material_complete"])

    def test_unsupported_schema_boundary_and_weak_same_ref_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad_schema = root / "bad_schema.json"
            self._write_operator_drill(bad_schema, schema="trashbot.other.v1")
            weak_ref = root / "weak_ref.json"
            self._write_operator_drill(weak_ref, same_evidence_ref_required="true")

            artifact_schema, _summary_schema, _ = console.build_route_task_field_retest_drill_console(str(bad_schema), "ev-console-001")
            artifact_ref, _summary_ref, _ = console.build_route_task_field_retest_drill_console(str(weak_ref), "ev-console-001")

        self.assertEqual(artifact_schema["console_status"], "blocked_unsupported_schema")
        self.assertEqual(artifact_ref["console_status"], "blocked_same_evidence_ref_not_required")

    def test_evidence_ref_mismatch_not_ready_and_unsafe_copy_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mismatch = root / "mismatch.json"
            self._write_operator_drill(mismatch, evidence_ref="source-ref")
            not_ready = root / "not_ready.json"
            self._write_operator_drill(not_ready, operator_drill_verdict="blocked_missing_material_pack")
            unsafe = root / "unsafe.json"
            self._write_operator_drill(unsafe, operator_note="raw path /Users/m4/secret.log")
            success = root / "success.json"
            self._write_operator_drill(success, delivery_success=True)

            artifact_mismatch, _summary_mismatch, _ = console.build_route_task_field_retest_drill_console(str(mismatch), "requested-ref")
            artifact_not_ready, _summary_not_ready, _ = console.build_route_task_field_retest_drill_console(str(not_ready), "ev-console-001")
            artifact_unsafe, summary_unsafe, _ = console.build_route_task_field_retest_drill_console(str(unsafe), "ev-console-001")
            artifact_success, _summary_success, _ = console.build_route_task_field_retest_drill_console(str(success), "ev-console-001")

        self.assertEqual(artifact_mismatch["console_status"], "blocked_same_evidence_ref_mismatch")
        self.assertEqual(artifact_not_ready["console_status"], "blocked_operator_drill_not_ready")
        self.assertEqual(artifact_unsafe["console_status"], "blocked_unsafe_operator_drill_copy")
        self.assertEqual(artifact_success["console_status"], "blocked_unsafe_operator_drill_copy")
        encoded_summary = json.dumps(summary_unsafe, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)
        self.assertNotIn("Authorization", encoded_summary)

    def test_missing_input_writes_blocked_not_proven_shape(self) -> None:
        artifact, summary, _exit_code = console.build_route_task_field_retest_drill_console(
            "/tmp/route_task_field_retest_drill_console_missing.json", "ev-console-003"
        )

        self.assertEqual(artifact["console_status"], "blocked_missing_operator_drill")
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
