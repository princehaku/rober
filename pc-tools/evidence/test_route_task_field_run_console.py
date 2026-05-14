#!/usr/bin/env python3
"""route/task field-run console gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import route_task_field_run_console as console  # noqa: E402


class RouteTaskFieldRunConsoleTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 临时 JSON 让测试保持 dependency-free，不依赖 ROS2、Nav2、串口或硬件。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def execution_pack(self, evidence_ref: str) -> dict:
        # execution pack 样本只保留本 console 需要消费的白名单字段。
        return {
            "schema": "trashbot.route_task_field_run_execution_pack.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_run_execution_pack_gate",
            "overall_status": "ready_for_field_run_execution_pack",
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "field_run_manifest": {
                "execution_state": "prepared_for_field_run",
                "evidence_ref": evidence_ref,
                "required_material_names": ["route_status_json", "task_record_json", "completion_signal_json"],
            },
            "first_run_commands": ["collect route status", "collect task record", "collect completion signal"],
            "rerun_commands": ["rerun all materials with same evidence_ref"],
            "not_proven": ["real_nav2_fixed_route_run", "delivery_success"],
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def route_status(self, evidence_ref: str) -> dict:
        # fixed-route status 样本覆盖 route_progress，但仍是软件材料。
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
        # task record 样本包含 dropoff 状态，但 console 仍不宣称真实 dropoff completion。
        return {
            "schema": "trashbot.task_record.v1",
            "task_id": "task-001",
            "evidence_ref": evidence_ref,
            "route_progress": {"evidence_ref": evidence_ref},
            "state_transition_history": ["IDLE", "LOADED", "DELIVERING", "DROPOFF", "RETURNING", "IDLE"],
            "task_result": {"status": "returned_idle"},
            "delivery_success": False,
        }

    def completion_signal(self, evidence_ref: str) -> dict:
        # completion signal 可以包含 completion material，但 console 边界仍固定为 not_proven。
        return {
            "schema": "trashbot.route_task_completion_signal.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_completion_signal_gate",
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "completion_verdict": "completed_not_proven",
            "dropoff_completion": {
                "material_status": "material_present_not_proven",
                "completion_claimed": True,
                "delivery_success": False,
            },
            "cancel_completion": {
                "material_status": "not_provided",
                "completion_claimed": False,
                "delivery_success": False,
            },
            "operator_next_steps": ["Review completion signal."],
            "not_proven": ["real_dropoff_completion", "delivery_success"],
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def build_with_payloads(
        self,
        root: Path,
        pack_payload: dict,
        route_payload: dict,
        task_payload: dict,
        completion_payload: dict,
        evidence_ref: str,
    ) -> dict:
        # 公共 helper 让 case 聚焦 fail-closed 规则，而不是文件读写样板。
        pack_path = self.write_json(root, "pack.json", pack_payload)
        route_path = self.write_json(root, "route.json", route_payload)
        task_path = self.write_json(root, "task.json", task_payload)
        completion_path = self.write_json(root, "completion.json", completion_payload)
        artifact, exit_code = console.build_field_run_console(
            str(pack_path),
            str(route_path),
            str(task_path),
            str(completion_path),
            evidence_ref,
        )
        self.assertEqual(exit_code, 0)
        return artifact

    def test_ready_materials_become_console_not_delivery_success(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = str(root / "run-001.json")
            artifact = self.build_with_payloads(
                root,
                self.execution_pack(evidence_ref),
                self.route_status(evidence_ref),
                self.task_record(evidence_ref),
                self.completion_signal(evidence_ref),
                evidence_ref,
            )

        self.assertEqual(artifact["schema"], "trashbot.route_task_field_run_console.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_run_console_gate",
        )
        self.assertEqual(artifact["schema_version"], 1)
        self.assertTrue(artifact["same_evidence_ref_required"])
        self.assertEqual(artifact["console_verdict"], "field_run_materials_prepared_not_proven")
        self.assertEqual(artifact["evidence_ref"], "file:run-001.json")
        self.assertIn("field_run_plan", artifact)
        self.assertIn("capture_checklist", artifact)
        self.assertEqual(artifact["execution_pack_summary"]["execution_state"], "prepared_for_field_run")
        self.assertEqual(artifact["route_status_summary"]["target"], "trash_station")
        self.assertEqual(artifact["task_record_summary"]["last_state"], "IDLE")
        self.assertEqual(artifact["completion_signal_summary"]["completion_verdict"], "completed_not_proven")
        self.assertEqual(artifact["dropoff_completion"]["material_status"], "material_present_not_proven")
        self.assertIn("real_nav2_fixed_route_run", artifact["not_proven"])
        self.assertIn("delivery_success", artifact["not_proven"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(artifact["mobile_readonly_summary"]["delivery_success"])

    def test_missing_material_bad_json_and_unsupported_schema_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = "run-002"
            pack_path = self.write_json(root, "pack.json", self.execution_pack(evidence_ref))
            route_path = root / "missing-route.json"
            task_path = self.write_json(root, "task.json", self.task_record(evidence_ref))
            completion_path = self.write_json(root, "completion.json", self.completion_signal(evidence_ref))
            missing_route, _ = console.build_field_run_console(
                str(pack_path),
                str(route_path),
                str(task_path),
                str(completion_path),
                evidence_ref,
            )
            bad_path = root / "bad.json"
            bad_path.write_text("{bad json", encoding="utf-8")
            bad_json, _ = console.build_field_run_console(
                str(pack_path),
                str(bad_path),
                str(task_path),
                str(completion_path),
                evidence_ref,
            )
            unsupported = self.route_status(evidence_ref)
            unsupported["schema"] = "trashbot.unsupported_route.v99"
            unsupported_artifact = self.build_with_payloads(
                root,
                self.execution_pack(evidence_ref),
                unsupported,
                self.task_record(evidence_ref),
                self.completion_signal(evidence_ref),
                evidence_ref,
            )

        self.assertEqual(missing_route["console_verdict"], "blocked_missing_route_status")
        self.assertEqual(bad_json["console_verdict"], "blocked_bad_json")
        self.assertEqual(unsupported_artifact["console_verdict"], "blocked_missing_route_status")
        self.assertFalse(missing_route["delivery_success"])
        self.assertFalse(bad_json["delivery_success"])

    def test_evidence_ref_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact = self.build_with_payloads(
                root,
                self.execution_pack("run-003"),
                self.route_status("run-003"),
                self.task_record("run-other"),
                self.completion_signal("run-003"),
                "run-003",
            )

        self.assertEqual(artifact["console_verdict"], "blocked_mismatch_evidence_ref")
        self.assertTrue(artifact["materials_status"]["mismatch_reasons"])
        self.assertFalse(artifact["delivery_success"])

    def test_unsafe_summary_is_redacted_and_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack_payload = self.execution_pack("run-004")
            pack_payload["first_run_commands"].append(
                "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 baudrate=115200 raw robot response"
            )
            artifact = self.build_with_payloads(
                root,
                pack_payload,
                self.route_status("run-004"),
                self.task_record("run-004"),
                self.completion_signal("run-004"),
                "run-004",
            )

        encoded = json.dumps(artifact, ensure_ascii=False)
        self.assertEqual(artifact["console_verdict"], "blocked_unsafe_summary")
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("baudrate=115200", encoded)
        self.assertNotIn("raw robot response", encoded)

    def test_delivery_success_true_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            completion_payload = self.completion_signal("run-005")
            completion_payload["delivery_success"] = True
            artifact = self.build_with_payloads(
                root,
                self.execution_pack("run-005"),
                self.route_status("run-005"),
                self.task_record("run-005"),
                completion_payload,
                "run-005",
            )

        self.assertEqual(artifact["console_verdict"], "blocked_delivery_success_claim")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["mobile_readonly_summary"]["delivery_success"])

    def test_primary_actions_enabled_input_blocks_as_unsafe_summary(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack_payload = self.execution_pack("run-006")
            pack_payload["primary_actions_enabled"] = True
            artifact = self.build_with_payloads(
                root,
                pack_payload,
                self.route_status("run-006"),
                self.task_record("run-006"),
                self.completion_signal("run-006"),
                "run-006",
            )

        self.assertEqual(artifact["console_verdict"], "blocked_unsafe_summary")
        self.assertFalse(artifact["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
