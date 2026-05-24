#!/usr/bin/env python3
"""cloud external evidence review handoff follow-up escalation gate 的离线围栏测试。"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE_DIR))

import cloud_external_evidence_review_handoff_followup_escalation_status as gate  # noqa: E402


class CloudExternalEvidenceReviewHandoffFollowupEscalationStatusTest(unittest.TestCase):
    def _write_json(self, root: Path, name: str, payload: object) -> Path:
        # 临时 fixture 只模拟上一跳 safe summary，不代表真实外部云或手机证据。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _handoff_summary(self) -> dict[str, object]:
        # source 必须保持 cloud_external_evidence_review_handoff 的 Docker/local software_proof 边界。
        return {
            "schema": "trashbot.robot_diagnostics_cloud_external_evidence_review_handoff_summary.v1",
            "schema_version": 1,
            "capability": "cloud_external_evidence_review_handoff",
            "source_capability": "cloud_external_evidence_review_decision",
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_cloud_external_evidence_review_handoff_gate",
            "handoff_status": "needs_external_evidence_backfill_handoff_not_proven",
            "source_review_decision": "needs_external_evidence_backfill_not_proven",
            "safe_evidence_ref": "evidence_ref=cloud_external_evidence_review_handoff_followup_fixture_20260525_0001",
            "safe_command_ref": "command_ref=cloud_external_evidence_review_handoff_followup_fixture_command",
            "owner_route": [
                "owner_action=backfill_same_safe_evidence_ref_external_materials",
                "owner_action=report_due_status_before_reviewer_resolution",
            ],
            "support_route": [
                "support_action=keep_PRRT_kwDOSWB9286CJ3tX_visible",
                "support_action=keep_hardware_material_pending_visible",
            ],
            "reviewer_route": [
                "reviewer_action=do_not_resolve_PRRT_kwDOSWB9286CJ3tX_from_software_proof",
            ],
            "next_required_evidence": [
                "next_required_evidence=backfill_production_db_queue_safe_summary",
                "next_required_evidence=backfill_true_phone_browser_proof_without_true_claim",
            ],
            "pr5_review_context": {
                gate.PR5_THREAD_ID: "hardware_material_pending",
            },
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_to_control": False,
            "not_proven": [
                "software_proof",
                "not_proven",
                "not true phone/browser proof",
                "no OKR percentage lift",
            ],
        }

    def _build(self, root: Path, payload: dict[str, object], status: str) -> tuple[dict[str, object], dict[str, object], int]:
        # 公共 helper 通过真实 JSON path 调用 builder，覆盖 CLI 输入形态。
        input_path = self._write_json(root, "handoff.json", payload)
        return gate.build_cloud_external_evidence_review_handoff_followup_escalation_status(str(input_path), status)

    def assert_false_flags(self, summary: dict[str, object]) -> None:
        self.assertEqual(summary["source"], "software_proof")
        self.assertEqual(summary["delivery_success"], False)
        self.assertEqual(summary["primary_actions_enabled"], False)
        self.assertEqual(summary["safe_to_control"], False)
        self.assertIn("not true phone/browser proof", summary["safe_phone_copy"])
        self.assertIn("no OKR percentage lift", summary["safe_phone_copy"])

    def test_accepts_safe_handoff_and_models_due_overdue_escalated_without_control(self) -> None:
        for status in (gate.PENDING, gate.DUE, gate.OVERDUE, gate.ESCALATED):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as tmp:
                artifact, summary, exit_code = self._build(Path(tmp), self._handoff_summary(), status)

                self.assertEqual(exit_code, 0)
                self.assertEqual(artifact["cloud_external_evidence_review_handoff_followup_escalation_status"], status)
                self.assertEqual(summary["followup_status"], status)
                self.assertEqual(summary["source_handoff_status"], "needs_external_evidence_backfill_handoff_not_proven")
                self.assertIn(gate.PR5_THREAD_ID, summary["safe_phone_copy"])
                self.assertEqual(summary["pr5_material_state"], "hardware_material_pending")
                self.assertIn("owner_action", json.dumps(summary["owner_action"]))
                self.assertIn("support_action", json.dumps(summary["support_action"]))
                self.assertIn("reviewer_action", json.dumps(summary["reviewer_action"]))
                self.assert_false_flags(summary)

    def test_robot_alias_wrapper_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = {"robot_diagnostics_cloud_external_evidence_review_handoff_summary": self._handoff_summary()}
            artifact, summary, exit_code = self._build(Path(tmp), payload, gate.DUE)

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact[gate.ROBOT_ALIAS]["summary_alias"], gate.ROBOT_ALIAS)
        self.assertTrue(summary["due_status"]["is_due"])
        self.assertIn(gate.EVIDENCE_BOUNDARY, summary["boundary_note"])

    def test_missing_or_wrong_source_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing, missing_summary, missing_exit = gate.build_cloud_external_evidence_review_handoff_followup_escalation_status(
                str(Path(tmp) / "missing.json"),
                gate.OVERDUE,
            )
            wrong_payload = self._handoff_summary()
            wrong_payload["evidence_boundary"] = "software_proof_docker_cloud_external_evidence_review_decision_gate"
            wrong, wrong_summary, wrong_exit = self._build(Path(tmp), wrong_payload, gate.DUE)

        self.assertNotEqual(missing_exit, 0)
        self.assertNotEqual(wrong_exit, 0)
        self.assertEqual(missing["followup_status"], gate.BLOCKED)
        self.assertEqual(wrong["followup_status"], gate.BLOCKED)
        self.assertIn("handoff_json_missing", missing_summary["blocked_reason"])
        self.assertIn("missing_or_wrong_cloud_external_evidence_review_handoff_boundary", wrong_summary["blocked_reason"])
        self.assertFalse(missing_summary["primary_actions_enabled"])

    def test_unsafe_payload_and_true_flags_are_rejected_without_raw_copy(self) -> None:
        for key, value in (
            ("raw_artifact_body", "Authorization: Bearer abc https://example.invalid/raw /cmd_vel"),
            ("safe_phone_copy", "delivery_success=true and PRRT_kwDOSWB9286CJ3tX resolved"),
            ("github_mutation_hint", "review mutation update"),
            ("primary_actions_enabled", True),
            ("safe_to_control", True),
        ):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as tmp:
                payload = self._handoff_summary()
                payload[key] = value
                artifact, summary, exit_code = self._build(Path(tmp), payload, gate.ESCALATED)
                encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False).lower()

                self.assertNotEqual(exit_code, 0)
                self.assertEqual(summary["followup_status"], gate.BLOCKED)
                self.assertNotIn("bearer abc", encoded)
                self.assertNotIn("example.invalid", encoded)
                self.assertNotIn("/cmd_vel", encoded)
                self.assertIn("delivery_success=false", encoded)
                self.assertFalse(summary["safe_copy"]["safe_to_control"])

    def test_cli_stdout_contains_required_literals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            input_path = self._write_json(Path(tmp), "handoff.json", self._handoff_summary())
            result = subprocess.run(
                [
                    sys.executable,
                    str(EVIDENCE_DIR / "cloud_external_evidence_review_handoff_followup_escalation_status.py"),
                    "--handoff-json",
                    str(input_path),
                    "--followup-status",
                    gate.ESCALATED,
                    "--once-json",
                ],
                check=False,
                text=True,
                capture_output=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        for required in (
            gate.CAPABILITY,
            "cloud_external_evidence_review_handoff",
            gate.EVIDENCE_BOUNDARY,
            gate.ROBOT_ALIAS,
            gate.PR5_THREAD_ID,
            "hardware_material_pending",
            "source=software_proof",
            "software_proof",
            "not_proven",
            "delivery_success=false",
            "primary_actions_enabled=false",
            "safe_to_control=false",
            "not true phone/browser proof",
            "no OKR percentage lift",
        ):
            self.assertIn(required, result.stdout)


if __name__ == "__main__":
    unittest.main()
