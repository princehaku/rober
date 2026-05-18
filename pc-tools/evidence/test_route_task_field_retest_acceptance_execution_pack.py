#!/usr/bin/env python3
"""route_task_field_retest_acceptance_execution_pack 的离线围栏测试。"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

import route_task_field_retest_acceptance_execution_pack as pack  # noqa: E402


class RouteTaskFieldRetestAcceptanceExecutionPackTest(unittest.TestCase):
    def _write_review_decision(self, path: Path, evidence_ref: str = "ev-exec-001", **extra: object) -> dict[str, object]:
        # fixture 模拟上一轮 review decision summary，不读取真实现场材料。
        missing = list(extra.pop("missing_evidence_packet", []))
        payload: dict[str, object] = {
            "schema": "trashbot.route_task_field_retest_acceptance_review_decision.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_retest_acceptance_review_decision_gate",
            "evidence_ref": evidence_ref,
            "safe_evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "status": "ready_for_controlled_field_retest_not_proven",
            "review_decision": "ready_for_controlled_field_retest_not_proven",
            "material_status": "acceptance_packet_reviewed_for_controlled_retest_not_proven",
            "missing_evidence_packet": missing,
            "owner_handoff": {
                "autonomy_owner": "Keep route/elevator packet metadata aligned.",
                "robot_owner": "Consume summary only.",
                "full_stack_owner": "Render read-only panel.",
                "product_owner": "Close as software proof.",
            },
            "safe_copy": {
                "evidence_ref": evidence_ref,
                "review_decision": "ready_for_controlled_field_retest_not_proven",
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

    def test_ready_execution_pack_contains_safe_bundle_and_checklist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_path = root / "review_decision.json"
            self._write_review_decision(review_path, evidence_ref="ev-exec-001")

            artifact, summary, exit_code = pack.build_route_task_field_retest_acceptance_execution_pack(
                str(review_path),
                "ev-exec-001",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.route_task_field_retest_acceptance_execution_pack.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_acceptance_execution_pack_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_acceptance_execution_pack_gate",
        )
        self.assertEqual(
            artifact["execution_pack_status"],
            "ready_for_field_retest_acceptance_execution_pack_not_proven",
        )
        self.assertIn("door_state", summary["required_route_elevator_materials"])
        self.assertIn("target_floor_confirmation", artifact["required_route_elevator_materials"])
        self.assertIn("owner_checklist", artifact)
        self.assertIn("rerun_commands", artifact)
        self.assertEqual(summary["safe_evidence_bundle"]["not_proven"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("delivery_success=false", artifact["boundary_note"])
        self.assertIn("primary_actions_enabled=false", artifact["boundary_note"])

    def test_nested_summary_file_and_env_sources_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nested_path = root / "nested.json"
            summary = {
                "schema": "trashbot.route_task_field_retest_acceptance_review_decision_summary.v1",
                "evidence_boundary": "software_proof_docker_route_task_field_retest_acceptance_review_decision_gate",
                "evidence_ref": "ev-exec-002",
                "safe_evidence_ref": "ev-exec-002",
                "same_evidence_ref_required": True,
                "status": "ready_for_controlled_field_retest_not_proven",
                "review_decision": "ready_for_controlled_field_retest_not_proven",
                "material_status": "acceptance_packet_reviewed_for_controlled_retest_not_proven",
                "delivery_success": False,
                "primary_actions_enabled": False,
            }
            nested_path.write_text(json.dumps({"payload": {"summary": summary}}), encoding="utf-8")
            os.environ["ROBER_ACCEPTANCE_REVIEW_DECISION_JSON"] = f"file:{nested_path}"
            try:
                artifact_file, summary_file, _ = pack.build_route_task_field_retest_acceptance_execution_pack(
                    f"file:{nested_path}",
                    "ev-exec-002",
                )
                artifact_env, summary_env, _ = pack.build_route_task_field_retest_acceptance_execution_pack(
                    "env:ROBER_ACCEPTANCE_REVIEW_DECISION_JSON",
                    "ev-exec-002",
                )
            finally:
                os.environ.pop("ROBER_ACCEPTANCE_REVIEW_DECISION_JSON", None)

        self.assertEqual(artifact_file["execution_pack_status"], "ready_for_field_retest_acceptance_execution_pack_not_proven")
        self.assertEqual(summary_file["evidence_ref"], "ev-exec-002")
        self.assertEqual(artifact_env["execution_pack_status"], "ready_for_field_retest_acceptance_execution_pack_not_proven")
        self.assertEqual(summary_env["safe_evidence_bundle"]["safe_evidence_ref"], "ev-exec-002")
        self.assertEqual(artifact_env["source_acceptance_review_decision"]["source_style"], "env_source")

    def test_unsupported_schema_weak_ref_and_mismatch_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad_schema = root / "bad_schema.json"
            self._write_review_decision(bad_schema, schema="trashbot.other.v1")
            weak_ref = root / "weak_ref.json"
            self._write_review_decision(weak_ref, same_evidence_ref_required="true")
            mismatch = root / "mismatch.json"
            self._write_review_decision(mismatch, evidence_ref="source-ref")

            artifact_schema, _summary_schema, _ = pack.build_route_task_field_retest_acceptance_execution_pack(
                str(bad_schema),
                "ev-exec-001",
            )
            artifact_ref, _summary_ref, _ = pack.build_route_task_field_retest_acceptance_execution_pack(
                str(weak_ref),
                "ev-exec-001",
            )
            artifact_mismatch, _summary_mismatch, _ = pack.build_route_task_field_retest_acceptance_execution_pack(
                str(mismatch),
                "requested-ref",
            )

        self.assertEqual(artifact_schema["execution_pack_status"], "unsupported_acceptance_review_decision_schema_not_proven")
        self.assertEqual(artifact_ref["execution_pack_status"], "evidence_ref_mismatch_rerun_not_proven")
        self.assertEqual(artifact_mismatch["execution_pack_status"], "evidence_ref_mismatch_rerun_not_proven")

    def test_not_ready_missing_material_and_unsafe_copy_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            not_ready = root / "not_ready.json"
            self._write_review_decision(
                not_ready,
                review_decision="needs_route_elevator_material_backfill_not_proven",
                status="needs_route_elevator_material_backfill_not_proven",
                missing_evidence_packet=["door_state"],
            )
            unsafe = root / "unsafe.json"
            self._write_review_decision(unsafe, operator_note="raw path /Users/m4/secret.log")
            success = root / "success.json"
            self._write_review_decision(success, delivery_success=True)

            artifact_not_ready, summary_not_ready, _ = pack.build_route_task_field_retest_acceptance_execution_pack(
                str(not_ready),
                "ev-exec-001",
            )
            artifact_unsafe, summary_unsafe, _ = pack.build_route_task_field_retest_acceptance_execution_pack(
                str(unsafe),
                "ev-exec-001",
            )
            artifact_success, _summary_success, _ = pack.build_route_task_field_retest_acceptance_execution_pack(
                str(success),
                "ev-exec-001",
            )

        self.assertEqual(artifact_not_ready["execution_pack_status"], "blocked_acceptance_review_decision_not_ready")
        self.assertIn("door_state", summary_not_ready["safe_evidence_bundle"]["missing_evidence_packet"])
        self.assertEqual(artifact_unsafe["execution_pack_status"], "rejected_unsafe_acceptance_review_decision_claim_not_proven")
        self.assertEqual(artifact_success["execution_pack_status"], "rejected_unsafe_acceptance_review_decision_claim_not_proven")
        encoded_summary = json.dumps(summary_unsafe, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)
        self.assertNotIn("Authorization", encoded_summary)

    def test_missing_input_writes_blocked_not_proven_shape(self) -> None:
        artifact, summary, _exit_code = pack.build_route_task_field_retest_acceptance_execution_pack(
            "/tmp/route_task_field_retest_acceptance_execution_pack_missing.json",
            "ev-exec-003",
        )

        self.assertEqual(
            artifact["execution_pack_status"],
            "unsupported_acceptance_review_decision_schema_not_proven",
        )
        self.assertEqual(summary["safe_evidence_bundle"]["not_proven"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
