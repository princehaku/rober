#!/usr/bin/env python3
"""route_task_field_retest_result_callback_intake 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

import route_task_field_retest_result_callback_intake as intake  # noqa: E402


class RouteTaskFieldRetestResultCallbackIntakeTest(unittest.TestCase):
    def _dispatch_payload(self, evidence_ref: str = "ev-result-callback-001", ready: bool = True, **extra: object) -> dict[str, object]:
        # fixture 只表达 result review dispatch 摘要，避免引入真实材料目录。
        status = "ready_for_field_retest_result_review_dispatch_not_proven" if ready else "blocked_missing_materials"
        owner_work_orders = [
            {
                "owner": "Autonomy Algorithm Engineer",
                "work_order": "stage accepted route/elevator result materials for PC-side dispatch review",
                "evidence_ref": evidence_ref,
                "status": "ready_not_proven",
            },
            {
                "owner": "Robot Platform Engineer",
                "work_order": "prepare read-only diagnostics handoff for same evidence_ref without enabling primary actions",
                "evidence_ref": evidence_ref,
                "status": "metadata_only",
            },
        ]
        requirements = [
            {
                "name": "same_evidence_ref_manifest",
                "required": True,
                "evidence_ref": evidence_ref,
                "safe_copy_only": True,
            },
            {
                "name": "accepted_materials_index",
                "required": True,
                "evidence_ref": evidence_ref,
                "safe_copy_only": True,
            },
        ]
        payload: dict[str, object] = {
            "schema": "trashbot.route_task_field_retest_result_review_dispatch.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_retest_result_review_dispatch_gate",
            "status": status,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "owner_work_orders": owner_work_orders,
            "callback_packet_requirements": requirements,
            "rerun_commands": [
                f"python3 pc-tools/evidence/route_task_field_retest_result_review_dispatch.py --review-decision-json <review_decision.json> --evidence-ref {evidence_ref}",
            ],
            "safe_copy": {
                "safe_evidence_ref": evidence_ref,
                "owner_work_orders": owner_work_orders,
                "callback_packet_requirements": requirements,
                "not_proven": "not_proven",
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        return payload

    def _callback_payload(self, evidence_ref: str = "ev-result-callback-001", **extra: object) -> dict[str, object]:
        # callback packet 逐项回应 dispatch 的 work order 与 requirement。
        payload: dict[str, object] = {
            "schema": "trashbot.route_task_field_retest_result_callback_packet.v1",
            "safe_evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "owner_work_orders": [
                {
                    "owner": "Autonomy Algorithm Engineer",
                    "work_order": "stage accepted route/elevator result materials for PC-side dispatch review",
                    "status": "accepted",
                    "safe_note": "metadata received for review callback",
                },
                {
                    "owner": "Robot Platform Engineer",
                    "work_order": "prepare read-only diagnostics handoff for same evidence_ref without enabling primary actions",
                    "status": "accepted",
                    "safe_note": "read-only handoff acknowledged",
                },
            ],
            "callback_packet_requirements": [
                {"name": "same_evidence_ref_manifest", "status": "accepted", "safe_note": "same ref checked"},
                {"name": "accepted_materials_index", "status": "accepted", "safe_note": "index included"},
            ],
            "owner_follow_up": [],
            "review_decision_handoff": {"decision": "ready_for_result_callback_review_decision_not_proven"},
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

    def _build(self, root: Path, dispatch: dict[str, object] | str, callback: dict[str, object] | str, evidence_ref: str = "ev-result-callback-001") -> tuple[dict, dict]:
        # 公共 helper 让 case 聚焦 schema、boundary 和 fail-closed 规则。
        dispatch_path = self._write_json(root, "dispatch.json", dispatch)
        callback_path = self._write_json(root, "callback.json", callback)
        artifact, summary, exit_code = intake.build_route_task_field_retest_result_callback_intake(
            str(dispatch_path),
            str(callback_path),
            evidence_ref,
        )
        self.assertEqual(exit_code, 0)
        return artifact, summary

    def test_ready_result_callback_intake_contains_safe_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(root, self._dispatch_payload(), self._callback_payload())

        self.assertEqual(artifact["schema"], "trashbot.route_task_field_retest_result_callback_intake.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_result_callback_intake_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_result_callback_intake_gate",
        )
        self.assertEqual(artifact["intake_status"], "ready_for_field_retest_result_callback_intake_not_proven")
        self.assertEqual(summary["same_evidence_ref_match"]["status"], "matched")
        self.assertEqual(len(summary["accepted_updates"]), 4)
        self.assertEqual(summary["missing_updates"], [])
        self.assertEqual(summary["rejected_updates"], [])
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertIn("route_task_field_retest_result_callback_intake.py", " ".join(summary["rerun_commands"]))
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_wrapper_dispatch_and_nested_callback_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(
                root,
                {"payload": {"summary": self._dispatch_payload("ev-result-callback-002")}},
                {"payload": {"field_callback": self._callback_payload("ev-result-callback-002")}},
                "ev-result-callback-002",
            )

        self.assertEqual(artifact["intake_status"], "ready_for_field_retest_result_callback_intake_not_proven")
        self.assertEqual(summary["safe_evidence_ref"], "ev-result-callback-002")
        self.assertEqual(summary["source_dispatch"]["schema_status"], "supported")
        self.assertEqual(summary["callback_packet"]["field_status"], "supported")

    def test_missing_bad_json_unsupported_schema_and_dispatch_not_ready_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            callback_path = self._write_json(root, "callback.json", self._callback_payload())
            dispatch_path = self._write_json(root, "dispatch.json", self._dispatch_payload())
            bad_json = self._write_json(root, "bad.json", "{bad-json")
            bad_schema = self._write_json(root, "bad_schema.json", self._dispatch_payload(schema="trashbot.unsupported.v1"))
            not_ready = self._write_json(root, "not_ready.json", self._dispatch_payload(ready=False))

            missing_artifact, _missing_summary, _ = intake.build_route_task_field_retest_result_callback_intake(
                str(root / "missing.json"),
                str(callback_path),
                "ev-result-callback-001",
            )
            bad_artifact, _bad_summary, _ = intake.build_route_task_field_retest_result_callback_intake(
                str(dispatch_path),
                str(bad_json),
                "ev-result-callback-001",
            )
            schema_artifact, _schema_summary, _ = intake.build_route_task_field_retest_result_callback_intake(
                str(bad_schema),
                str(callback_path),
                "ev-result-callback-001",
            )
            not_ready_artifact, _not_ready_summary, _ = intake.build_route_task_field_retest_result_callback_intake(
                str(not_ready),
                str(callback_path),
                "ev-result-callback-001",
            )

        self.assertEqual(missing_artifact["intake_status"], "blocked_missing_dispatch_json")
        self.assertEqual(bad_artifact["intake_status"], "blocked_bad_json")
        self.assertEqual(schema_artifact["intake_status"], "blocked_unsupported_dispatch_schema_or_boundary")
        self.assertEqual(not_ready_artifact["intake_status"], "blocked_dispatch_not_ready")

    def test_evidence_ref_mismatch_weak_bool_missing_and_rejected_updates_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mismatch_artifact, _mismatch_summary = self._build(root, self._dispatch_payload(), self._callback_payload("other-ref"))
            weak_bool_artifact, _weak_summary = self._build(
                root,
                self._dispatch_payload(same_evidence_ref_required="true"),
                self._callback_payload(same_evidence_ref_required="true"),
            )
            missing_callback = self._callback_payload()
            missing_callback["callback_packet_requirements"] = [
                {"name": "same_evidence_ref_manifest", "status": "accepted", "safe_note": "same ref checked"}
            ]
            missing_artifact, missing_summary = self._build(root, self._dispatch_payload(), missing_callback)
            rejected_callback = self._callback_payload()
            rejected_callback["owner_work_orders"] = [
                {
                    "owner": "Autonomy Algorithm Engineer",
                    "work_order": "stage accepted route/elevator result materials for PC-side dispatch review",
                    "status": "rejected",
                    "safe_note": "metadata missing required index",
                },
                {
                    "owner": "Robot Platform Engineer",
                    "work_order": "prepare read-only diagnostics handoff for same evidence_ref without enabling primary actions",
                    "status": "accepted",
                },
            ]
            rejected_artifact, rejected_summary = self._build(root, self._dispatch_payload(), rejected_callback)

        self.assertEqual(mismatch_artifact["intake_status"], "blocked_same_evidence_ref_mismatch")
        self.assertEqual(weak_bool_artifact["intake_status"], "blocked_same_evidence_ref_not_required")
        self.assertEqual(missing_artifact["intake_status"], "blocked_missing_callback_updates")
        self.assertIn("accepted_materials_index", json.dumps(missing_summary["missing_updates"], ensure_ascii=False))
        self.assertEqual(rejected_artifact["intake_status"], "blocked_rejected_callback_updates")
        self.assertIn("metadata missing required index", json.dumps(rejected_summary["rejected_updates"], ensure_ascii=False))

    def test_weak_callback_unsafe_copy_success_claim_and_unknown_field_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            weak = self._callback_payload()
            weak["owner_work_orders"] = {"Autonomy Algorithm Engineer|stage accepted route/elevator result materials for PC-side dispatch review": True}
            weak_artifact, _weak_summary = self._build(root, self._dispatch_payload(), weak)
            unsafe_artifact, unsafe_summary = self._build(
                root,
                self._dispatch_payload(),
                self._callback_payload(owner_follow_up=["raw /Users/m4/secret.log /cmd_vel checksum=abcdef123456"]),
            )
            success_artifact, _success_summary = self._build(
                root,
                self._dispatch_payload(),
                self._callback_payload(delivery_success=True),
            )
            unknown_artifact, _unknown_summary = self._build(
                root,
                self._dispatch_payload(),
                self._callback_payload(raw_log="/tmp/log.txt"),
            )

        self.assertEqual(weak_artifact["intake_status"], "blocked_weak_callback_fields")
        self.assertEqual(unsafe_artifact["intake_status"], "blocked_unsafe_copy")
        self.assertEqual(success_artifact["intake_status"], "blocked_unsafe_copy")
        self.assertEqual(unknown_artifact["intake_status"], "blocked_unsupported_callback_schema_or_fields")
        encoded = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("abcdef123456", encoded)


if __name__ == "__main__":
    unittest.main()
