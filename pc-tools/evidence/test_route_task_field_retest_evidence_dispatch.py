#!/usr/bin/env python3
"""route_task_field_retest_evidence_dispatch 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

import route_task_field_retest_evidence_dispatch as dispatch  # noqa: E402


class RouteTaskFieldRetestEvidenceDispatchTest(unittest.TestCase):
    def _write_acceptance_brief(self, path: Path, evidence_ref: str = "ev-dispatch-001", **extra: object) -> dict[str, object]:
        # fixture 只写 acceptance brief 摘要字段，保持 Docker/local software proof 边界。
        required_packet = [
            {"name": "nav2_or_fixed_route_runtime_log"},
            {"name": "route_completion_signal"},
            {"name": "task_record"},
            {"name": "door_state"},
            {"name": "target_floor_confirmation"},
            {"name": "human_assistance_note"},
            {"name": "dropoff_or_cancel_completion"},
            {"name": "delivery_result"},
        ]
        payload: dict[str, object] = {
            "schema": "trashbot.route_task_field_retest_acceptance_brief.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_retest_acceptance_brief_gate",
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "acceptance_status": "ready_for_field_retest_acceptance_brief_not_proven",
            "required_evidence_packet": required_packet,
            "safe_copy": {
                "evidence_ref": evidence_ref,
                "required_evidence_packet": [item["name"] for item in required_packet],
                "not_proven": "not_proven",
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        path.write_text(json.dumps(payload), encoding="utf-8")
        return payload

    def test_ready_dispatch_contains_owner_files_and_required_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief_path = root / "acceptance_brief.json"
            self._write_acceptance_brief(brief_path, evidence_ref="ev-dispatch-001")

            artifact, summary, exit_code = dispatch.build_route_task_field_retest_evidence_dispatch(
                str(brief_path),
                "ev-dispatch-001",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.route_task_field_retest_evidence_dispatch.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_evidence_dispatch_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_evidence_dispatch_gate",
        )
        self.assertEqual(artifact["dispatch_status"], "ready_for_field_retest_evidence_dispatch_not_proven")
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
        self.assertIn("Autonomy Algorithm Engineer", summary["material_owners"])
        self.assertIn("field_retest_packet/ev-dispatch-001/delivery_result.json", summary["recommended_filenames"])
        self.assertTrue(summary["same_evidence_ref_rule"]["same_evidence_ref_required"])

    def test_wrapper_summary_input_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrapper_path = root / "wrapper.json"
            summary = {
                "schema": "trashbot.route_task_field_retest_acceptance_brief_summary.v1",
                "evidence_boundary": "software_proof_docker_route_task_field_retest_acceptance_brief_gate",
                "evidence_ref": "ev-dispatch-002",
                "same_evidence_ref_required": True,
                "acceptance_status": "ready_for_field_retest_acceptance_brief_not_proven",
                "required_evidence_packet": list(dispatch.REQUIRED_EVIDENCE_PACKET),
                "delivery_success": False,
                "primary_actions_enabled": False,
            }
            wrapper_path.write_text(json.dumps({"payload": {"summary": summary}}), encoding="utf-8")

            artifact, summary_out, _exit_code = dispatch.build_route_task_field_retest_evidence_dispatch(str(wrapper_path), "")

        self.assertEqual(artifact["dispatch_status"], "ready_for_field_retest_evidence_dispatch_not_proven")
        self.assertEqual(summary_out["evidence_ref"], "ev-dispatch-002")
        self.assertIn("route_completion_signal", summary_out["backfill_order"])
        self.assertIn("delivery_success=false", summary_out["fail_closed_rerun_notes"][-1])
        self.assertIn("primary_actions_enabled=false", summary_out["fail_closed_rerun_notes"][-1])

    def test_unsupported_schema_boundary_mismatch_and_weak_same_ref_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad_schema = root / "bad_schema.json"
            self._write_acceptance_brief(bad_schema, schema="trashbot.other.v1")
            bad_boundary = root / "bad_boundary.json"
            self._write_acceptance_brief(bad_boundary, evidence_boundary="wrong_boundary")
            weak_ref = root / "weak_ref.json"
            self._write_acceptance_brief(weak_ref, same_evidence_ref_required="true")
            mismatch = root / "mismatch.json"
            self._write_acceptance_brief(mismatch, evidence_ref="source-ref")

            artifact_schema, _summary_schema, _ = dispatch.build_route_task_field_retest_evidence_dispatch(str(bad_schema), "ev-dispatch-001")
            artifact_boundary, _summary_boundary, _ = dispatch.build_route_task_field_retest_evidence_dispatch(
                str(bad_boundary),
                "ev-dispatch-001",
            )
            artifact_ref, _summary_ref, _ = dispatch.build_route_task_field_retest_evidence_dispatch(str(weak_ref), "ev-dispatch-001")
            artifact_mismatch, _summary_mismatch, _ = dispatch.build_route_task_field_retest_evidence_dispatch(
                str(mismatch),
                "requested-ref",
            )

        self.assertEqual(artifact_schema["dispatch_status"], "blocked_unsupported_schema")
        self.assertEqual(artifact_boundary["dispatch_status"], "blocked_unsupported_schema")
        self.assertEqual(artifact_ref["dispatch_status"], "blocked_same_evidence_ref_not_required")
        self.assertEqual(artifact_mismatch["dispatch_status"], "blocked_same_evidence_ref_mismatch")

    def test_not_ready_missing_packet_and_unsafe_copy_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            not_ready = root / "not_ready.json"
            self._write_acceptance_brief(not_ready, acceptance_status="blocked_acceptance_brief_not_ready")
            missing_packet = root / "missing_packet.json"
            self._write_acceptance_brief(missing_packet, required_evidence_packet=[{"name": "task_record"}])
            unsafe = root / "unsafe.json"
            self._write_acceptance_brief(unsafe, operator_note="raw path /Users/m4/secret.log /cmd_vel")
            success = root / "success.json"
            self._write_acceptance_brief(success, delivery_success=True)

            artifact_not_ready, _summary_not_ready, _ = dispatch.build_route_task_field_retest_evidence_dispatch(
                str(not_ready),
                "ev-dispatch-001",
            )
            artifact_missing, _summary_missing, _ = dispatch.build_route_task_field_retest_evidence_dispatch(
                str(missing_packet),
                "ev-dispatch-001",
            )
            artifact_unsafe, summary_unsafe, _ = dispatch.build_route_task_field_retest_evidence_dispatch(
                str(unsafe),
                "ev-dispatch-001",
            )
            artifact_success, _summary_success, _ = dispatch.build_route_task_field_retest_evidence_dispatch(
                str(success),
                "ev-dispatch-001",
            )

        self.assertEqual(artifact_not_ready["dispatch_status"], "blocked_acceptance_brief_not_ready")
        self.assertEqual(artifact_missing["dispatch_status"], "blocked_missing_required_evidence_packet")
        self.assertEqual(artifact_unsafe["dispatch_status"], "blocked_unsafe_acceptance_brief_copy")
        self.assertEqual(artifact_success["dispatch_status"], "blocked_unsafe_acceptance_brief_copy")
        encoded_summary = json.dumps(summary_unsafe, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)
        self.assertNotIn("Authorization", encoded_summary)

    def test_missing_input_writes_blocked_not_proven_shape(self) -> None:
        artifact, summary, _exit_code = dispatch.build_route_task_field_retest_evidence_dispatch(
            "/tmp/route_task_field_retest_evidence_dispatch_missing.json",
            "ev-dispatch-003",
        )

        self.assertEqual(artifact["dispatch_status"], "blocked_missing_acceptance_brief")
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
