#!/usr/bin/env python3
"""reviewer ACK review-handoff gate 的离线围栏测试。"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools/evidence 不是常规包；测试显式加入目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision as decision_gate  # noqa: E402
import field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff as gate  # noqa: E402


# 测试约束 01：fixture 只表达 reviewer ACK review-decision safe summary。
# 测试约束 02：ready 只表示后续人工 handoff，不代表 reviewer resolution。
# 测试约束 03：reassignment 只表达 owner 路由变化，不启用控制。
# 测试约束 04：field-owner supplement 只表达补材料，不代表补证完成。
# 测试约束 05：缺 review-decision source 必须 blocked missing。
# 测试约束 06：unsafe success/control/hardware/PR-resolution copy 必须 rejected。
# 测试约束 07：Robot diagnostics safe alias 必须可消费。
# 测试约束 08：输出保持 source=software_proof 与 not_proven。
# 测试约束 09：输出保持 delivery_success=false。
# 测试约束 10：输出保持 primary_actions_enabled=false。
# 测试约束 11：输出保持 safe_to_control=false。
# 测试约束 12：测试不访问 ROS graph、Nav2、硬件、云、GitHub 或手机 runtime。


class FieldEvidenceRerunAcceptanceOwnerResponseReviewerAckReviewHandoffTest(unittest.TestCase):
    def _write_json(self, root: Path, name: str, payload: object) -> Path:
        # 临时 JSON 只服务离线围栏，不代表真实外部或现场材料。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _decision_summary(
        self,
        evidence_ref: str,
        review_decision: str = decision_gate.ACCEPTED,
        decision_reasons: list[str] | None = None,
        reassignment_target: str = "field-owner-b",
    ) -> dict[str, object]:
        # source 使用上一轮 reviewer ACK review-decision 的安全消费面。
        return {
            "schema": decision_gate.SUMMARY_SCHEMA,
            "schema_version": 1,
            "source": "software_proof",
            "status": "not_proven",
            "software_proof": True,
            "not_proven": True,
            "capability": decision_gate.CAPABILITY,
            "review_decision": review_decision,
            "reviewer_ack_state": "reviewer_acknowledged_not_proven",
            "evidence_boundary": decision_gate.EVIDENCE_BOUNDARY,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "decision_reasons": decision_reasons or ["reviewer ACK decision ready for handoff only"],
            "next_required_evidence": ["keep reviewer ACK handoff attached to the same safe evidence_ref"],
            "ack_owner": "reviewer",
            "acknowledged_at": "2026-05-23T11:20:00Z",
            "reassignment_target": reassignment_target,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_copy": {
                "source": "software_proof",
                "status": "not_proven",
                "software_proof": True,
                "not_proven": True,
                "review_decision": review_decision,
                "reviewer_ack_state": "reviewer_acknowledged_not_proven",
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "same_evidence_ref_required": True,
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "safety_markers": [
                "source=software_proof",
                "software_proof",
                "not_proven",
                "delivery_success=false",
                "primary_actions_enabled=false",
                "safe_to_control=false",
            ],
        }

    def _build(self, root: Path, payload: dict[str, object]) -> tuple[dict[str, object], dict[str, object], int]:
        # 公共 helper 让 case 聚焦五态映射和安全边界。
        input_path = self._write_json(root, "reviewer_ack_review_decision.json", payload)
        return gate.build_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff(
            str(input_path)
        )

    def test_accepted_review_decision_maps_to_ready_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._decision_summary("reviewer-ack-handoff-901"),
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], gate.SCHEMA)
        self.assertEqual(summary["schema"], gate.SUMMARY_SCHEMA)
        self.assertEqual(summary["summary_alias"], gate.ROBOT_ALIAS)
        self.assertEqual(artifact["handoff_status"], gate.HANDOFF_READY)
        self.assertEqual(artifact["evidence_boundary"], gate.EVIDENCE_BOUNDARY)
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(artifact["safe_to_control"])

    def test_reassignment_review_decision_maps_to_reassignment_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._decision_summary("reviewer-ack-handoff-902", decision_gate.NEEDS_REASSIGNMENT),
            )

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["handoff_status"], gate.HANDOFF_REASSIGNMENT)
        self.assertEqual(summary["reassignment_target"], "field-owner-b")
        self.assertIn("reassigned reviewer ACK handoff", summary["next_required_evidence"][0])
        self.assertFalse(summary["safe_to_control"])

    def test_field_owner_supplement_maps_to_material_supplement_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._decision_summary(
                    "reviewer-ack-handoff-903",
                    decision_gate.NEEDS_FIELD_OWNER_SUPPLEMENT,
                    ["field owner ACK material supplement required"],
                ),
            )

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["handoff_status"], gate.HANDOFF_FIELD_OWNER_SUPPLEMENT)
        self.assertIn("supplement", summary["next_required_evidence"][0])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_unsafe_review_decision_and_overclaim_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            unsafe_payload = self._decision_summary("reviewer-ack-handoff-904")
            unsafe_payload["safe_note"] = "delivery_success=true and PRRT_kwDOSWB9286CJ3tX resolved"
            artifact, summary, exit_code = self._build(Path(tmp), unsafe_payload)

        encoded = json.dumps(summary, ensure_ascii=False)
        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["handoff_status"], gate.HANDOFF_REJECTED)
        self.assertIn("delivery_success=false", encoded)
        self.assertNotIn("delivery_success=true", encoded)
        self.assertFalse(summary["support_handoff"]["delivery_success"])

    def test_evidence_ref_mismatch_inside_source_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = self._decision_summary("reviewer-ack-handoff-905")
            payload["safe_copy"]["evidence_ref"] = "reviewer-ack-handoff-other"
            artifact, summary, exit_code = self._build(Path(tmp), payload)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["handoff_status"], gate.HANDOFF_BLOCKED)
        self.assertIn("evidence_ref_mismatch", artifact["handoff_reasons"])
        self.assertFalse(summary["safe_to_control"])

    def test_missing_or_bad_decision_maps_to_blocked_missing_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing, missing_summary, missing_exit = gate.build_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff(
                str(root / "missing-decision.json")
            )
            bad_path = self._write_json(root, "unsupported.json", {"schema": "unsupported", "source": "software_proof"})
            bad, _, bad_exit = gate.build_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff(
                str(bad_path)
            )

        self.assertEqual(missing_exit, 2)
        self.assertEqual(bad_exit, 2)
        self.assertEqual(missing["handoff_status"], gate.HANDOFF_BLOCKED)
        self.assertEqual(bad["handoff_status"], gate.HANDOFF_BLOCKED)
        self.assertIn("reviewer_ack_review_decision_input_missing", missing["handoff_reasons"])
        self.assertFalse(missing_summary["primary_actions_enabled"])

    def test_robot_alias_wrapper_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = {decision_gate.ROBOT_ALIAS: self._decision_summary("reviewer-ack-handoff-908")}
            artifact, summary, exit_code = self._build(Path(tmp), payload)

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["handoff_status"], gate.HANDOFF_READY)
        self.assertEqual(artifact["safe_evidence_ref"], "reviewer-ack-handoff-908")
        self.assertEqual(summary["source_schema"], decision_gate.SUMMARY_SCHEMA)

    def test_cli_prints_ready_for_safe_review_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = self._write_json(
                root,
                "reviewer_ack_review_decision.json",
                self._decision_summary("reviewer-ack-handoff-909"),
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(
                        EVIDENCE_DIR
                        / "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff.py"
                    ),
                    "--reviewer-ack-review-decision-json",
                    str(input_path),
                ],
                check=False,
                text=True,
                capture_output=True,
            )

        self.assertEqual(result.returncode, 0)
        self.assertIn(gate.HANDOFF_READY, result.stdout)
        self.assertIn(gate.EVIDENCE_BOUNDARY, result.stdout)

    def test_output_preserves_required_boundary_literals_and_no_raw_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, _ = self._build(
                Path(tmp),
                self._decision_summary("reviewer-ack-handoff-910"),
            )

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertIn(gate.CAPABILITY, encoded)
        self.assertIn(gate.EVIDENCE_BOUNDARY, encoded)
        self.assertIn(gate.HANDOFF_READY, encoded)
        self.assertIn(gate.HANDOFF_REASSIGNMENT, encoded)
        self.assertIn(gate.HANDOFF_FIELD_OWNER_SUPPLEMENT, encoded)
        self.assertIn(gate.HANDOFF_REJECTED, encoded)
        self.assertIn(gate.HANDOFF_BLOCKED, encoded)
        self.assertIn("source=software_proof", encoded)
        self.assertIn("software_proof", encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("safe_to_control=false", encoded)
        self.assertIn("delivery_success=false", encoded)
        self.assertIn("primary_actions_enabled=false", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("Traceback", encoded)
        self.assertNotIn("raw artifact", encoded)


if __name__ == "__main__":
    unittest.main()
