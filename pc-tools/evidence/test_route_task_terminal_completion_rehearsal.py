#!/usr/bin/env python3
"""route/task terminal completion rehearsal gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import route_task_terminal_completion_rehearsal as rehearsal  # noqa: E402


class RouteTaskTerminalCompletionRehearsalTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 临时 JSON 让测试保持 dependency-free，不依赖 ROS2、Nav2、硬件或外部云。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def route_status(self, evidence_ref: str) -> dict:
        # route status 样本只保留固定路线复账所需的最小字段。
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
        # task record 样本覆盖 dropoff 终态，但仍不代表真实送达。
        return {
            "schema": "trashbot.task_record.v1",
            "task_id": "task-001",
            "evidence_ref": evidence_ref,
            "route_progress": {"evidence_ref": evidence_ref},
            "state_transition_history": ["IDLE", "LOADED", "DELIVERING", "DROPOFF", "RETURNING", "IDLE"],
            "task_result": {"status": "returned_idle"},
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def completion_signal(self, evidence_ref: str) -> dict:
        # completion signal 是必需上游；本 gate 只把它作为 material source 复账。
        return {
            "schema": "trashbot.route_task_completion_signal.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_completion_signal_gate",
            "evidence_ref": evidence_ref,
            "completion_verdict": "completed_not_proven",
            "dropoff_completion": {"material_status": "material_present_not_proven"},
            "cancel_completion": {"material_status": "not_provided"},
            "phone_safe_summary": {
                "status": "completed_not_proven",
                "evidence_ref": evidence_ref,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "not_proven": ["real_delivery", "real_dropoff_completion"],
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def dropoff_material(self, evidence_ref: str) -> dict:
        # dropoff material 只能说明材料存在，不让 rehearsal 升级成真实 completion。
        return {
            "schema": "trashbot.dropoff_completion.v1",
            "evidence_ref": evidence_ref,
            "dropoff_completed": True,
            "completion_status": "completed",
            "delivery_success": False,
        }

    def cancel_material(self, evidence_ref: str) -> dict:
        # cancel material 用于失败/取消分支复核，同样保持 not_proven。
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
        completion_payload: dict,
        evidence_ref: str,
        dropoff_payload: dict | None = None,
        cancel_payload: dict | None = None,
    ) -> tuple[dict, dict]:
        # 公共 helper 让 case 聚焦 fail-closed 规则，而不是文件读写样板。
        route_path = self.write_json(root, "route.json", route_payload)
        task_path = self.write_json(root, "task.json", task_payload)
        completion_path = self.write_json(root, "completion.json", completion_payload)
        drop_path = self.write_json(root, "dropoff.json", dropoff_payload) if dropoff_payload is not None else ""
        cancel_path = self.write_json(root, "cancel.json", cancel_payload) if cancel_payload is not None else ""
        artifact, summary, exit_code = rehearsal.build_terminal_completion_rehearsal(
            str(route_path),
            str(task_path),
            str(completion_path),
            str(drop_path),
            str(cancel_path),
            evidence_ref,
        )
        self.assertEqual(exit_code, 0)
        return artifact, summary

    def test_ready_not_proven_with_dropoff_material(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = str(root / "run-001.json")
            artifact, summary = self.build(
                root,
                self.route_status(evidence_ref),
                self.task_record(evidence_ref),
                self.completion_signal(evidence_ref),
                evidence_ref,
                self.dropoff_material(evidence_ref),
            )

        self.assertEqual(artifact["schema"], "trashbot.route_task_terminal_completion_rehearsal.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_terminal_completion_rehearsal_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_terminal_completion_rehearsal_gate",
        )
        self.assertEqual(artifact["terminal_verdict"], "ready_for_terminal_completion_rehearsal_not_proven")
        self.assertEqual(artifact["evidence_ref"], "file:run-001.json")
        self.assertEqual(artifact["route_status_summary"]["target"], "trash_station")
        self.assertEqual(artifact["task_record_summary"]["final_state"], "IDLE")
        self.assertEqual(artifact["dropoff"]["material_status"], "material_present_not_proven")
        self.assertEqual(artifact["cancel"]["material_status"], "not_provided")
        self.assertIn("real_terminal_completion", artifact["not_proven"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_missing_required_dropoff_material_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact, summary = self.build(
                root,
                self.route_status("run-002"),
                self.task_record("run-002"),
                self.completion_signal("run-002"),
                "run-002",
            )

        self.assertEqual(artifact["terminal_verdict"], "blocked_missing_route_task_terminal_completion_rehearsal")
        self.assertEqual(summary["terminal_verdict"], "blocked_missing_route_task_terminal_completion_rehearsal")
        self.assertIn("dropoff:not_provided", artifact["materials_status"]["missing_materials"])
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
            artifact, _summary = self.build(
                root,
                self.route_status("run-003"),
                task,
                self.completion_signal("run-003"),
                "run-003",
                cancel_payload=self.cancel_material("run-003"),
            )

        self.assertEqual(artifact["terminal_verdict"], "failed_with_recovery_reason_not_proven")
        self.assertEqual(artifact["failure_reason"], "navigation_timeout")
        self.assertEqual(artifact["recovery_reason"], "operator_cancelled_and_returned_to_idle")
        self.assertEqual(artifact["cancel"]["material_status"], "material_present_not_proven")
        self.assertFalse(artifact["delivery_success"])

    def test_missing_required_source_and_bad_json_are_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            route_path = self.write_json(root, "route.json", self.route_status("run-004"))
            bad_path = root / "bad.json"
            bad_path.write_text("{bad json", encoding="utf-8")
            artifact, _summary, _ = rehearsal.build_terminal_completion_rehearsal(
                str(route_path),
                str(bad_path),
                str(root / "missing-completion.json"),
                "",
                "",
                "run-004",
            )

        self.assertEqual(artifact["terminal_verdict"], "blocked_bad_json")
        self.assertFalse(artifact["delivery_success"])

    def test_unsupported_completion_boundary_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            completion = self.completion_signal("run-005")
            completion["evidence_boundary"] = "software_proof_docker_wrong_gate"
            artifact, _summary = self.build(
                root,
                self.route_status("run-005"),
                self.task_record("run-005"),
                completion,
                "run-005",
                self.dropoff_material("run-005"),
            )

        self.assertEqual(artifact["terminal_verdict"], "blocked_unsupported_schema")

    def test_evidence_ref_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact, _summary = self.build(
                root,
                self.route_status("run-006"),
                self.task_record("run-other"),
                self.completion_signal("run-006"),
                "run-006",
                self.dropoff_material("run-006"),
            )

        self.assertEqual(artifact["terminal_verdict"], "blocked_mismatch_evidence_ref")
        self.assertTrue(artifact["materials_status"]["mismatch_reasons"])

    def test_unsafe_phone_copy_is_redacted_and_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            completion = self.completion_signal("run-007")
            completion["phone_safe_summary"]["operator_note"] = (
                "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 baudrate=115200 "
                "raw robot response /Users/m4/private/full.json"
            )
            artifact, _summary = self.build(
                root,
                self.route_status("run-007"),
                self.task_record("run-007"),
                completion,
                "run-007",
                self.dropoff_material("run-007"),
            )

        encoded = json.dumps(artifact, ensure_ascii=False)
        self.assertEqual(artifact["terminal_verdict"], "blocked_unsafe_copy")
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("baudrate=115200", encoded)
        self.assertNotIn("raw robot response", encoded)

    def test_delivery_success_or_primary_action_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            completion = self.completion_signal("run-008")
            completion["primary_actions_enabled"] = True
            artifact, summary = self.build(
                root,
                self.route_status("run-008"),
                self.task_record("run-008"),
                completion,
                "run-008",
                self.dropoff_material("run-008"),
            )

        self.assertEqual(artifact["terminal_verdict"], "blocked_success_or_control_claim")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
