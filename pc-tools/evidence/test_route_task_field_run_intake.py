#!/usr/bin/env python3
"""route/task field-run intake crosscheck gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import route_task_field_run_intake as intake  # noqa: E402


class RouteTaskFieldRunIntakeTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 每个测试都走临时 JSON，确保工具不依赖 ROS2、Nav2 或真实上车环境。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def source_payloads(self, evidence_ref: str) -> tuple[dict, dict, dict, dict, dict]:
        # 五份材料共享同一 evidence_ref，覆盖 ready_for_review 的软件复账 happy path。
        route_status = {
            "schema": "trashbot.fixed_route_status.v1",
            "route_contract_version": "fixed_route.v1",
            "evidence_ref": evidence_ref,
            "route_progress": {"evidence_ref": evidence_ref, "checkpoint": 1, "failure_code": ""},
            "delivery_success": False,
        }
        task_record = {
            "schema": "trashbot.task_record.v1",
            "evidence_ref": evidence_ref,
            "route_progress": {"evidence_ref": evidence_ref, "current_index": 1},
            "state_transition_history": ["IDLE", "LOADED", "DELIVERING"],
            "delivery_success": False,
        }
        runtime_log = {
            "schema": "trashbot.nav2_fixed_route_runtime_log.v1",
            "evidence_ref": evidence_ref,
            "events": [{"state": "running", "checkpoint": 1}],
            "delivery_success": False,
        }
        robot_evidence = {
            "schema": "trashbot.robot_side_task_evidence.v1",
            "evidence_ref": evidence_ref,
            "task_result": {"evidence_ref": evidence_ref, "status": "processing"},
            "delivery_success": False,
        }
        mobile_summary = {
            "schema": "trashbot.support_safe_mobile_summary.v1",
            "evidence_ref": evidence_ref,
            "phone_safe_summary": {
                "evidence_ref": evidence_ref,
                "status": "accepted_or_processing_support_metadata_only",
            },
            "primary_actions_enabled": False,
            "delivery_success": False,
        }
        return route_status, task_record, runtime_log, robot_evidence, mobile_summary

    def build_with_paths(self, root: Path, evidence_ref: str) -> tuple[dict, int]:
        # 公共 helper 让测试只关注变体，减少各 case 对 CLI 参数形状的重复。
        route_status, task_record, runtime_log, robot_evidence, mobile_summary = self.source_payloads(evidence_ref)
        paths = [
            self.write_json(root, "route_status.json", route_status),
            self.write_json(root, "task_record.json", task_record),
            self.write_json(root, "runtime_log.json", runtime_log),
            self.write_json(root, "robot_evidence.json", robot_evidence),
            self.write_json(root, "mobile_summary.json", mobile_summary),
        ]
        return intake.build_intake_crosscheck(*(str(path) for path in paths), evidence_ref=evidence_ref)

    def test_ready_for_review_has_required_boundary_fields(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = str(root / "run-001.json")
            payload, exit_code = self.build_with_paths(root, evidence_ref)

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["schema"], "trashbot.route_task_field_run_intake_crosscheck.v1")
        self.assertEqual(
            payload["evidence_boundary"], "software_proof_docker_route_task_field_run_intake_crosscheck_gate"
        )
        self.assertEqual(payload["overall_status"], "ready_for_review")
        self.assertTrue(payload["same_evidence_ref_required"])
        self.assertFalse(payload["delivery_success"])
        self.assertFalse(payload["primary_actions_enabled"])
        self.assertEqual(payload["missing_materials"], [])
        self.assertEqual(payload["mismatch_reasons"], [])
        self.assertIn("real_nav2_fixed_route_run", payload["not_proven"])
        self.assertIn("real_hil_pass", payload["not_proven"])
        self.assertIn("objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof", payload["not_proven"])
        self.assertIn("commands_to_rerun", payload)
        self.assertEqual(payload["evidence_ref"], "file:run-001.json")
        self.assertEqual(payload["phone_safe_summary"]["delivery_success"], False)

    def test_missing_material_blocks_without_exception(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = "run-002"
            route_status, task_record, runtime_log, robot_evidence, _ = self.source_payloads(evidence_ref)
            paths = [
                self.write_json(root, "route_status.json", route_status),
                self.write_json(root, "task_record.json", task_record),
                self.write_json(root, "runtime_log.json", runtime_log),
                self.write_json(root, "robot_evidence.json", robot_evidence),
                root / "missing_mobile_summary.json",
            ]

            payload, _ = intake.build_intake_crosscheck(*(str(path) for path in paths), evidence_ref=evidence_ref)

        self.assertEqual(payload["overall_status"], "blocked_missing_material")
        self.assertIn("support_safe_mobile_summary:support_safe_mobile_summary_missing", payload["missing_materials"])
        self.assertFalse(payload["delivery_success"])

    def test_bad_json_blocks_without_unhandled_exception(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = "run-003"
            route_status, task_record, runtime_log, robot_evidence, mobile_summary = self.source_payloads(evidence_ref)
            route_path = self.write_json(root, "route_status.json", route_status)
            task_path = self.write_json(root, "task_record.json", task_record)
            runtime_path = root / "runtime_log.json"
            runtime_path.write_text("{bad json", encoding="utf-8")
            robot_path = self.write_json(root, "robot_evidence.json", robot_evidence)
            mobile_path = self.write_json(root, "mobile_summary.json", mobile_summary)

            payload, _ = intake.build_intake_crosscheck(
                str(route_path), str(task_path), str(runtime_path), str(robot_path), str(mobile_path), evidence_ref
            )

        self.assertEqual(payload["overall_status"], "blocked_missing_material")
        self.assertIn("runtime_log:runtime_log_read_error", payload["missing_materials"])

    def test_unsupported_schema_blocks_conservatively(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = "run-004"
            route_status, task_record, runtime_log, robot_evidence, mobile_summary = self.source_payloads(evidence_ref)
            route_status["schema"] = "trashbot.unsupported_route_status.v99"
            paths = [
                self.write_json(root, "route_status.json", route_status),
                self.write_json(root, "task_record.json", task_record),
                self.write_json(root, "runtime_log.json", runtime_log),
                self.write_json(root, "robot_evidence.json", robot_evidence),
                self.write_json(root, "mobile_summary.json", mobile_summary),
            ]

            payload, _ = intake.build_intake_crosscheck(*(str(path) for path in paths), evidence_ref=evidence_ref)

        self.assertEqual(payload["overall_status"], "blocked_unsupported_schema")
        self.assertIn("route_status:unsupported_schema", payload["missing_materials"])

    def test_mismatched_evidence_ref_reports_source_reason(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = "run-005"
            route_status, task_record, runtime_log, robot_evidence, mobile_summary = self.source_payloads(evidence_ref)
            runtime_log["evidence_ref"] = "run-other"
            paths = [
                self.write_json(root, "route_status.json", route_status),
                self.write_json(root, "task_record.json", task_record),
                self.write_json(root, "runtime_log.json", runtime_log),
                self.write_json(root, "robot_evidence.json", robot_evidence),
                self.write_json(root, "mobile_summary.json", mobile_summary),
            ]

            payload, _ = intake.build_intake_crosscheck(*(str(path) for path in paths), evidence_ref=evidence_ref)

        self.assertEqual(payload["overall_status"], "blocked_mismatch")
        self.assertIn("evidence_ref:sources_do_not_share_same_ref", payload["mismatch_reasons"])
        self.assertIn("runtime_log:evidence_ref_mismatch:run-other!=run-005", payload["mismatch_reasons"])

    def test_unsafe_mobile_summary_blocks_and_redacts_output(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = "run-006"
            route_status, task_record, runtime_log, robot_evidence, mobile_summary = self.source_payloads(evidence_ref)
            mobile_summary["phone_safe_summary"]["operator_note"] = (
                "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 baudrate=115200 raw robot response"
            )
            paths = [
                self.write_json(root, "route_status.json", route_status),
                self.write_json(root, "task_record.json", task_record),
                self.write_json(root, "runtime_log.json", runtime_log),
                self.write_json(root, "robot_evidence.json", robot_evidence),
                self.write_json(root, "mobile_summary.json", mobile_summary),
            ]

            payload, _ = intake.build_intake_crosscheck(*(str(path) for path in paths), evidence_ref=evidence_ref)

        encoded = json.dumps(payload, ensure_ascii=False)
        self.assertEqual(payload["overall_status"], "blocked_unsafe_summary")
        self.assertIn("support_safe_mobile_summary:unsafe_summary", payload["missing_materials"])
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("baudrate=115200", encoded)
        self.assertNotIn("raw robot response", encoded)


if __name__ == "__main__":
    unittest.main()
