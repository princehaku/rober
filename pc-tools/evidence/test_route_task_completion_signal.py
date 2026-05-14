#!/usr/bin/env python3
"""route/task completion signal gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import route_task_completion_signal as completion_signal  # noqa: E402


class RouteTaskCompletionSignalTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 临时 JSON 让测试保持 dependency-free，不依赖 ROS2、Nav2、串口或硬件。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def route_status(self, evidence_ref: str) -> dict:
        # fixed-route status 样本只保留 route_progress 与 replay 摘要字段。
        return {
            "schema": "trashbot.fixed_route_status.v1",
            "evidence_ref": evidence_ref,
            "route_progress": {
                "evidence_ref": evidence_ref,
                "checkpoint": "station-a",
                "current_index": 3,
                "target": "trash_station",
                "failure_code": "",
            },
            "software_proof": {"status": "replay_pass"},
            "delivery_success": False,
        }

    def task_record(self, evidence_ref: str) -> dict:
        # task record 样本覆盖送达状态机，但仍不代表真实送达。
        return {
            "schema": "trashbot.task_record.v1",
            "task_id": "task-001",
            "evidence_ref": evidence_ref,
            "route_progress": {"evidence_ref": evidence_ref},
            "state_transition_history": ["IDLE", "LOADED", "DELIVERING", "DROPOFF", "RETURNING", "IDLE"],
            "task_result": {"status": "returned_idle"},
            "delivery_success": False,
        }

    def reconciliation(self, evidence_ref: str) -> dict:
        # 上一轮 reconciliation 是 required source，但本 gate 不把它升级为 delivery proof。
        return {
            "schema": "trashbot.route_task_field_run_reconciliation.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_run_reconciliation_gate",
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "reconciliation_verdict": "ready_for_route_task_field_run_reconciliation",
            "missing_materials": [],
            "mismatch_reasons": [],
            "operator_next_steps": ["Review aligned software materials."],
            "phone_safe_summary": {
                "status": "ready_for_route_task_field_run_reconciliation",
                "evidence_ref": evidence_ref,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "not_proven": ["real_nav2_fixed_route_run", "delivery_success"],
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def dropoff_completion(self, evidence_ref: str) -> dict:
        # dropoff material 可以存在，但 completion signal 仍输出 delivery_success=false。
        return {
            "schema": "trashbot.dropoff_completion.v1",
            "evidence_ref": evidence_ref,
            "dropoff_completed": True,
            "completion_status": "completed",
            "delivery_success": False,
        }

    def cancel_completion(self, evidence_ref: str) -> dict:
        # cancel material 用于失败/取消分支复核，不代表真实 cancel completion 已被本 gate 证明。
        return {
            "schema": "trashbot.cancel_completion.v1",
            "evidence_ref": evidence_ref,
            "cancel_completed": True,
            "completion_status": "completed",
            "delivery_success": False,
        }

    def build(
        self,
        root: Path,
        route_payload: dict,
        task_payload: dict,
        summary_payload: dict,
        evidence_ref: str,
        dropoff_payload: dict | None = None,
        cancel_payload: dict | None = None,
    ) -> dict:
        # 公共 helper 让 case 聚焦 fail-closed 规则，而不是文件读写样板。
        route_path = self.write_json(root, "route.json", route_payload)
        task_path = self.write_json(root, "task.json", task_payload)
        summary_path = self.write_json(root, "summary.json", summary_payload)
        drop_path = self.write_json(root, "dropoff.json", dropoff_payload) if dropoff_payload is not None else ""
        cancel_path = self.write_json(root, "cancel.json", cancel_payload) if cancel_payload is not None else ""
        artifact, exit_code = completion_signal.build_completion_signal(
            str(route_path),
            str(task_path),
            str(summary_path),
            str(drop_path),
            str(cancel_path),
            evidence_ref,
        )
        self.assertEqual(exit_code, 0)
        return artifact

    def test_completed_not_proven_with_dropoff_material(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = str(root / "run-001.json")
            artifact = self.build(
                root,
                self.route_status(evidence_ref),
                self.task_record(evidence_ref),
                self.reconciliation(evidence_ref),
                evidence_ref,
                self.dropoff_completion(evidence_ref),
            )

        self.assertEqual(artifact["schema"], "trashbot.route_task_completion_signal.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_completion_signal_gate",
        )
        self.assertEqual(artifact["schema_version"], 1)
        self.assertTrue(artifact["same_evidence_ref_required"])
        self.assertEqual(artifact["completion_verdict"], "completed_not_proven")
        self.assertEqual(artifact["evidence_ref"], "file:run-001.json")
        self.assertEqual(artifact["fixed_route_summary"]["target"], "trash_station")
        self.assertEqual(artifact["task_record_summary"]["last_state"], "IDLE")
        self.assertTrue(artifact["state_transition_summary"]["has_dropoff_state"])
        self.assertEqual(artifact["dropoff_completion"]["material_status"], "material_present_not_proven")
        self.assertEqual(artifact["cancel_completion"]["material_status"], "not_provided")
        self.assertIn("real_delivery", artifact["not_proven"])
        self.assertIn("real_dropoff_completion", artifact["not_proven"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(artifact["phone_safe_summary"]["delivery_success"])

    def test_missing_required_dropoff_material_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact = self.build(
                root,
                self.route_status("run-002"),
                self.task_record("run-002"),
                self.reconciliation("run-002"),
                "run-002",
            )

        self.assertEqual(artifact["completion_verdict"], "blocked_missing_completion_materials")
        self.assertIn("dropoff_completion:not_provided", artifact["materials_status"]["missing_materials"])
        self.assertFalse(artifact["delivery_success"])

    def test_failed_with_recovery_reason_uses_cancel_material(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            task = self.task_record("run-003")
            task["state_transition_history"] = ["IDLE", "LOADED", "DELIVERING", "ERROR", "CANCELLED"]
            task["task_result"] = {
                "status": "failed",
                "failure_reason": "navigation_timeout",
                "recovery_reason": "operator_cancelled_and_returned_to_idle",
            }
            artifact = self.build(
                root,
                self.route_status("run-003"),
                task,
                self.reconciliation("run-003"),
                "run-003",
                cancel_payload=self.cancel_completion("run-003"),
            )

        self.assertEqual(artifact["completion_verdict"], "failed_with_recovery_reason")
        self.assertEqual(artifact["failure_reason"], "navigation_timeout")
        self.assertEqual(artifact["recovery_reason"], "operator_cancelled_and_returned_to_idle")
        self.assertEqual(artifact["cancel_completion"]["material_status"], "material_present_not_proven")
        self.assertFalse(artifact["delivery_success"])

    def test_missing_required_material_and_bad_json_are_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            route_path = self.write_json(root, "route.json", self.route_status("run-004"))
            bad_path = root / "bad.json"
            bad_path.write_text("{bad json", encoding="utf-8")
            artifact, _ = completion_signal.build_completion_signal(
                str(route_path),
                str(bad_path),
                str(root / "missing-summary.json"),
                "",
                "",
                "run-004",
            )

        self.assertEqual(artifact["completion_verdict"], "blocked_bad_json")
        self.assertFalse(artifact["delivery_success"])

    def test_unsupported_schema_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            route = self.route_status("run-005")
            route["schema"] = "trashbot.unsupported_route.v99"
            artifact = self.build(
                root,
                route,
                self.task_record("run-005"),
                self.reconciliation("run-005"),
                "run-005",
                self.dropoff_completion("run-005"),
            )

        self.assertEqual(artifact["completion_verdict"], "blocked_unsupported_schema")

    def test_evidence_ref_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact = self.build(
                root,
                self.route_status("run-006"),
                self.task_record("run-other"),
                self.reconciliation("run-006"),
                "run-006",
                self.dropoff_completion("run-006"),
            )

        self.assertEqual(artifact["completion_verdict"], "blocked_mismatch_evidence_ref")
        self.assertTrue(artifact["materials_status"]["mismatch_reasons"])

    def test_unsafe_phone_summary_is_redacted_and_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            summary = self.reconciliation("run-007")
            summary["phone_safe_summary"]["operator_note"] = (
                "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 baudrate=115200 raw robot response"
            )
            artifact = self.build(
                root,
                self.route_status("run-007"),
                self.task_record("run-007"),
                summary,
                "run-007",
                self.dropoff_completion("run-007"),
            )

        encoded = json.dumps(artifact, ensure_ascii=False)
        self.assertEqual(artifact["completion_verdict"], "blocked_unsafe_phone_summary")
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("baudrate=115200", encoded)
        self.assertNotIn("raw robot response", encoded)

    def test_delivery_success_true_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            route = self.route_status("run-008")
            route["delivery_success"] = True
            artifact = self.build(
                root,
                route,
                self.task_record("run-008"),
                self.reconciliation("run-008"),
                "run-008",
                self.dropoff_completion("run-008"),
            )

        self.assertEqual(artifact["completion_verdict"], "blocked_delivery_success_claim")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["phone_safe_summary"]["delivery_success"])


if __name__ == "__main__":
    unittest.main()
