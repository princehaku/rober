#!/usr/bin/env python3
"""route_task_field_retest_acceptance_review_decision 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

import route_task_field_retest_acceptance_review_decision as decision  # noqa: E402


class RouteTaskFieldRetestAcceptanceReviewDecisionTest(unittest.TestCase):
    def _write_acceptance_brief(self, path: Path, evidence_ref: str = "ev-review-001", **extra: object) -> dict[str, object]:
        # fixture 只写 acceptance brief 摘要字段，保持 Docker-only software proof 边界。
        missing = list(extra.pop("missing_evidence_packet", []))
        required_packet = []
        for name in decision.REQUIRED_EVIDENCE_PACKET:
            # missing 状态模拟上游 brief 的 packet 摘要，不读取真实材料目录。
            required_packet.append(
                {
                    "name": name,
                    "current_status": "missing_in_source_summary" if name in missing else "required_for_field_review",
                }
            )
        payload: dict[str, object] = {
            "schema": "trashbot.route_task_field_retest_acceptance_brief.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_retest_acceptance_brief_gate",
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "acceptance_status": "ready_for_field_retest_acceptance_brief_not_proven",
            "required_evidence_packet": required_packet,
            "owner_handoff": {
                "autonomy_owner": "Keep packet aligned.",
                "robot_owner": "Read-only diagnostics.",
                "full_stack_owner": "Read-only panel.",
                "product_owner": "Software proof closeout.",
            },
            "safe_copy": {
                "evidence_ref": evidence_ref,
                "acceptance_status": "ready_for_field_retest_acceptance_brief_not_proven",
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

    def test_ready_decision_contains_safe_review_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            brief_path = root / "acceptance_brief.json"
            self._write_acceptance_brief(brief_path, evidence_ref="ev-review-001")

            artifact, summary, exit_code = decision.build_route_task_field_retest_acceptance_review_decision(
                str(brief_path),
                "ev-review-001",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.route_task_field_retest_acceptance_review_decision.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_acceptance_review_decision_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_acceptance_review_decision_gate",
        )
        self.assertEqual(artifact["review_decision"], "ready_for_controlled_field_retest_not_proven")
        self.assertEqual(summary["material_status"], "acceptance_packet_reviewed_for_controlled_retest_not_proven")
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("delivery_success=false", artifact["boundary_note"])
        self.assertIn("primary_actions_enabled=false", artifact["boundary_note"])

    def test_wrapper_summary_input_and_material_backfill_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrapper_path = root / "wrapper.json"
            summary = {
                "schema": "trashbot.route_task_field_retest_acceptance_brief_summary.v1",
                "evidence_boundary": "software_proof_docker_route_task_field_retest_acceptance_brief_gate",
                "evidence_ref": "ev-review-002",
                "same_evidence_ref_required": True,
                "acceptance_status": "ready_for_field_retest_acceptance_brief_not_proven",
                "missing_evidence_packet": ["door_state", "target_floor_confirmation"],
                "owner_handoff": {"autonomy_owner": "Keep same evidence ref."},
                "delivery_success": False,
                "primary_actions_enabled": False,
            }
            wrapper_path.write_text(json.dumps({"payload": {"summary": summary}}), encoding="utf-8")

            artifact, summary_out, _exit_code = decision.build_route_task_field_retest_acceptance_review_decision(
                str(wrapper_path),
                "",
            )

        self.assertEqual(artifact["review_decision"], "needs_route_elevator_material_backfill_not_proven")
        self.assertEqual(summary_out["evidence_ref"], "ev-review-002")
        self.assertIn("door_state", summary_out["missing_evidence_packet"])
        self.assertIn("target_floor_confirmation", summary_out["missing_evidence_packet"])
        self.assertIn("Backfill missing packet metadata", summary_out["next_required_evidence"][0])

    def test_unsupported_schema_weak_ref_and_mismatch_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad_schema = root / "bad_schema.json"
            self._write_acceptance_brief(bad_schema, schema="trashbot.other.v1")
            weak_ref = root / "weak_ref.json"
            self._write_acceptance_brief(weak_ref, same_evidence_ref_required="true")
            mismatch = root / "mismatch.json"
            self._write_acceptance_brief(mismatch, evidence_ref="source-ref")

            artifact_schema, _summary_schema, _ = decision.build_route_task_field_retest_acceptance_review_decision(
                str(bad_schema),
                "ev-review-001",
            )
            artifact_ref, _summary_ref, _ = decision.build_route_task_field_retest_acceptance_review_decision(
                str(weak_ref),
                "ev-review-001",
            )
            artifact_mismatch, _summary_mismatch, _ = decision.build_route_task_field_retest_acceptance_review_decision(
                str(mismatch),
                "requested-ref",
            )

        self.assertEqual(artifact_schema["review_decision"], "unsupported_acceptance_brief_schema_not_proven")
        self.assertEqual(artifact_ref["review_decision"], "evidence_ref_mismatch_rerun_not_proven")
        self.assertEqual(artifact_mismatch["review_decision"], "evidence_ref_mismatch_rerun_not_proven")

    def test_not_ready_owner_handoff_and_unsafe_copy_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            not_ready = root / "not_ready.json"
            self._write_acceptance_brief(not_ready, acceptance_status="blocked_drill_console_not_ready")
            no_handoff = root / "no_handoff.json"
            self._write_acceptance_brief(no_handoff, owner_handoff={})
            unsafe = root / "unsafe.json"
            self._write_acceptance_brief(unsafe, operator_note="raw path /Users/m4/secret.log")
            success = root / "success.json"
            self._write_acceptance_brief(success, delivery_success=True)

            artifact_not_ready, _summary_not_ready, _ = decision.build_route_task_field_retest_acceptance_review_decision(
                str(not_ready),
                "ev-review-001",
            )
            artifact_no_handoff, _summary_no_handoff, _ = decision.build_route_task_field_retest_acceptance_review_decision(
                str(no_handoff),
                "ev-review-001",
            )
            artifact_unsafe, summary_unsafe, _ = decision.build_route_task_field_retest_acceptance_review_decision(
                str(unsafe),
                "ev-review-001",
            )
            artifact_success, _summary_success, _ = decision.build_route_task_field_retest_acceptance_review_decision(
                str(success),
                "ev-review-001",
            )

        self.assertEqual(artifact_not_ready["review_decision"], "blocked_acceptance_brief_not_ready")
        self.assertEqual(artifact_no_handoff["review_decision"], "needs_owner_handoff_not_proven")
        self.assertEqual(artifact_unsafe["review_decision"], "rejected_unsafe_acceptance_brief_claim_not_proven")
        self.assertEqual(artifact_success["review_decision"], "rejected_unsafe_acceptance_brief_claim_not_proven")
        encoded_summary = json.dumps(summary_unsafe, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)
        self.assertNotIn("Authorization", encoded_summary)

    def test_missing_input_writes_blocked_not_proven_shape(self) -> None:
        artifact, summary, _exit_code = decision.build_route_task_field_retest_acceptance_review_decision(
            "/tmp/route_task_field_retest_acceptance_review_decision_missing.json",
            "ev-review-003",
        )

        self.assertEqual(artifact["review_decision"], "unsupported_acceptance_brief_schema_not_proven")
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
