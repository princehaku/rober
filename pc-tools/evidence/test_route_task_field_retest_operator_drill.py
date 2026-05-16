#!/usr/bin/env python3
"""route_task_field_retest_operator_drill 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

import route_task_field_retest_material_pack as pack  # noqa: E402
import route_task_field_retest_operator_drill as drill  # noqa: E402


class RouteTaskFieldRetestOperatorDrillTest(unittest.TestCase):
    def _write_material_pack(self, path: Path, evidence_ref: str = "ev-drill-001", **extra: object) -> dict[str, object]:
        # fixture 只写 material pack 摘要字段，保持 Docker-only software proof 边界。
        missing = list(extra.pop("missing_materials", []))
        accepted_count = len(pack.REQUIRED_MATERIALS) - len(missing)
        payload: dict[str, object] = {
            "schema": "trashbot.route_task_field_retest_material_pack.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_retest_material_pack_gate",
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "material_pack_verdict": "ready_for_field_retest_material_pack_not_proven",
            "material_completeness": {
                "required_count": len(pack.REQUIRED_MATERIALS),
                "accepted_count": accepted_count,
                "missing_materials": missing,
                "is_complete": not missing,
            },
            "missing_materials": missing,
            "operator_next_steps": ["Run intake and reconciliation with the same evidence_ref."],
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        path.write_text(json.dumps(payload), encoding="utf-8")
        return payload

    def test_ready_drill_links_material_pack_intake_and_reconciliation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pack_path = root / "material_pack.json"
            self._write_material_pack(pack_path, evidence_ref="ev-drill-001")

            artifact, summary, exit_code = drill.build_route_task_field_retest_operator_drill(str(pack_path), "ev-drill-001")

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.route_task_field_retest_operator_drill.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_operator_drill_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_operator_drill_gate",
        )
        self.assertEqual(artifact["operator_drill_verdict"], "ready_for_operator_drill_not_proven")
        self.assertEqual([item["label"] for item in summary["command_chain"]], ["material_pack", "result_intake", "result_reconciliation"])
        self.assertIn("route_task_field_retest_result_intake.py", artifact["result_intake_command"]["command"])
        self.assertIn("route_task_field_retest_result_reconciliation.py", artifact["result_reconciliation_command"]["command"])
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_wrapper_summary_input_and_missing_material_prompts_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrapper_path = root / "wrapper.json"
            summary = {
                "schema": "trashbot.route_task_field_retest_material_pack_summary.v1",
                "evidence_boundary": "software_proof_docker_route_task_field_retest_material_pack_gate",
                "evidence_ref": "ev-drill-002",
                "same_evidence_ref_required": True,
                "status": "blocked_missing_materials",
                "material_completeness": {
                    "required_count": len(pack.REQUIRED_MATERIALS),
                    "accepted_count": 6,
                    "missing_materials": ["door_state", "target_floor_confirmation"],
                    "is_complete": False,
                },
                "delivery_success": False,
                "primary_actions_enabled": False,
            }
            wrapper_path.write_text(json.dumps({"payload": {"summary": summary}}), encoding="utf-8")

            artifact, summary_out, _exit_code = drill.build_route_task_field_retest_operator_drill(str(wrapper_path), "")

        self.assertEqual(artifact["operator_drill_verdict"], "ready_for_operator_drill_not_proven")
        self.assertEqual(summary_out["evidence_ref"], "ev-drill-002")
        self.assertEqual(summary_out["missing_materials"], ["door_state", "target_floor_confirmation"])
        self.assertIn("Collect door_state metadata", summary_out["missing_material_prompts"][0])
        self.assertFalse(summary_out["safe_copy"]["material_complete"])

    def test_unsupported_schema_boundary_and_weak_same_ref_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad_schema = root / "bad_schema.json"
            self._write_material_pack(bad_schema, schema="trashbot.other.v1")
            weak_ref = root / "weak_ref.json"
            self._write_material_pack(weak_ref, same_evidence_ref_required="true")

            artifact_schema, _summary_schema, _ = drill.build_route_task_field_retest_operator_drill(str(bad_schema), "ev-drill-001")
            artifact_ref, _summary_ref, _ = drill.build_route_task_field_retest_operator_drill(str(weak_ref), "ev-drill-001")

        self.assertEqual(artifact_schema["operator_drill_verdict"], "blocked_unsupported_schema")
        self.assertEqual(artifact_ref["operator_drill_verdict"], "blocked_same_evidence_ref_not_required")

    def test_evidence_ref_mismatch_and_unsafe_copy_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mismatch = root / "mismatch.json"
            self._write_material_pack(mismatch, evidence_ref="source-ref")
            unsafe = root / "unsafe.json"
            self._write_material_pack(unsafe, observer_note="raw path /Users/m4/secret.log")
            success = root / "success.json"
            self._write_material_pack(success, delivery_success=True)

            artifact_mismatch, _summary_mismatch, _ = drill.build_route_task_field_retest_operator_drill(str(mismatch), "requested-ref")
            artifact_unsafe, summary_unsafe, _ = drill.build_route_task_field_retest_operator_drill(str(unsafe), "ev-drill-001")
            artifact_success, _summary_success, _ = drill.build_route_task_field_retest_operator_drill(str(success), "ev-drill-001")

        self.assertEqual(artifact_mismatch["operator_drill_verdict"], "blocked_same_evidence_ref_mismatch")
        self.assertEqual(artifact_unsafe["operator_drill_verdict"], "blocked_unsafe_material_pack_copy")
        self.assertEqual(artifact_success["operator_drill_verdict"], "blocked_unsafe_material_pack_copy")
        encoded_summary = json.dumps(summary_unsafe, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)
        self.assertNotIn("Authorization", encoded_summary)

    def test_missing_input_writes_blocked_not_proven_shape(self) -> None:
        artifact, summary, _exit_code = drill.build_route_task_field_retest_operator_drill(
            "/tmp/route_task_field_retest_operator_drill_missing.json", "ev-drill-003"
        )

        self.assertEqual(artifact["operator_drill_verdict"], "blocked_missing_material_pack")
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
