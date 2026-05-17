#!/usr/bin/env python3
"""route/task field retest result acceptance backfill gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import route_task_field_retest_result_acceptance_backfill as backfill  # noqa: E402


class RouteTaskFieldRetestResultAcceptanceBackfillTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 测试只写临时 JSON，保证 gate 不依赖 ROS2、Nav2、硬件、手机或外部云。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def packet_summary(self, evidence_ref: str, ready: bool = True) -> dict:
        # 样本沿用上一轮 acceptance packet 的 summary 形态。
        status = (
            "ready_for_field_retest_result_acceptance_packet_not_proven"
            if ready
            else "blocked_reconciliation_not_ready"
        )
        return {
            "schema": "trashbot.route_task_field_retest_result_acceptance_packet_summary.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_retest_result_acceptance_packet_gate",
            "status": status,
            "acceptance_packet_status": status,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "safe_lineage": {
                "source_result_intake_schema": "trashbot.route_task_field_retest_result_intake.v1",
                "source_result_intake_status": "ready_for_field_retest_result_intake_not_proven",
            },
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def write_materials(self, root: Path, evidence_ref: str, overrides: dict[str, dict | str] | None = None) -> Path:
        # 八类材料用最小 JSON 元数据，避免测试夹带 raw runtime log。
        material_dir = root / "materials"
        material_dir.mkdir()
        overrides = overrides or {}
        for name in backfill.REQUIRED_RESULT_MATERIALS:
            payload: dict | str = {
                "evidence_ref": evidence_ref,
                "status": "provided",
                "source": "software_proof",
                "review_note": f"{name} backfill material collected for metadata review",
            }
            if name in overrides:
                payload = overrides[name]
            target = material_dir / backfill.material_pack.MATERIAL_ALIASES[name][0]
            if isinstance(payload, str):
                target.write_text(payload, encoding="utf-8")
            else:
                target.write_text(json.dumps(payload), encoding="utf-8")
        return material_dir

    def build(self, root: Path, packet_payload: dict, material_dir: Path, evidence_ref: str = "run-001") -> tuple[dict, dict]:
        # 公共 helper 让 case 聚焦 schema、boundary 和 fail-closed 规则。
        packet_path = self.write_json(root, "packet.json", packet_payload)
        artifact, summary, exit_code = backfill.build_route_task_field_retest_result_acceptance_backfill(
            str(packet_path),
            str(material_dir),
            evidence_ref,
        )
        self.assertEqual(exit_code, 0)
        return artifact, summary

    def test_complete_material_dir_builds_backfill_not_proven(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            material_dir = self.write_materials(root, "run-001")
            artifact, summary = self.build(root, {"payload": {"summary": self.packet_summary("run-001")}}, material_dir)

        self.assertEqual(artifact["schema"], "trashbot.route_task_field_retest_result_acceptance_backfill.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_result_acceptance_backfill_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_result_acceptance_backfill_gate",
        )
        self.assertEqual(artifact["status"], "ready_for_field_retest_result_acceptance_backfill_not_proven")
        self.assertEqual(artifact["source_acceptance_packet"]["schema_status"], "supported")
        self.assertTrue(artifact["material_completeness"]["is_complete"])
        self.assertEqual(artifact["acceptance_backfill_gap_summary"]["gap_count"], 0)
        self.assertIn("Nav2/fixed-route runtime log", artifact["material_states"][0]["label"])
        self.assertIn("door state", json.dumps(summary, ensure_ascii=False))
        self.assertIn("delivery result", json.dumps(summary, ensure_ascii=False))
        self.assertIn("route_task_field_retest_result_acceptance_packet.py", " ".join(summary["rerun_commands"]))
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_artifact_input_and_nested_safe_copy_are_supported(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            material_dir = self.write_materials(root, "run-002")
            artifact_input = self.packet_summary("run-002")
            artifact_input["schema"] = "trashbot.route_task_field_retest_result_acceptance_packet.v1"
            artifact_input["safe_copy"] = {"evidence_ref": "run-002", "status": artifact_input["status"]}
            artifact, summary = self.build(root, {"data": {"acceptance_packet": artifact_input}}, material_dir, "run-002")

        self.assertEqual(artifact["source_acceptance_packet"]["schema"], "trashbot.route_task_field_retest_result_acceptance_packet.v1")
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertEqual(summary["safe_copy"]["material_completeness"]["accepted_count"], len(backfill.REQUIRED_RESULT_MATERIALS))

    def test_missing_packet_bad_json_unsupported_and_packet_not_ready_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            material_dir = self.write_materials(root, "run-003")
            missing_artifact, missing_summary, _ = backfill.build_route_task_field_retest_result_acceptance_backfill(
                str(root / "missing.json"),
                str(material_dir),
                "run-003",
            )
            bad_path = root / "bad.json"
            bad_path.write_text("{bad json", encoding="utf-8")
            bad_artifact, _bad_summary, _ = backfill.build_route_task_field_retest_result_acceptance_backfill(
                str(bad_path),
                str(material_dir),
                "run-003",
            )
            unsupported = self.packet_summary("run-003")
            unsupported["schema"] = "trashbot.unsupported.v1"
            unsupported_artifact, _unsupported_summary = self.build(root, unsupported, material_dir, "run-003")
            not_ready_artifact, _not_ready_summary = self.build(root, self.packet_summary("run-003", ready=False), material_dir, "run-003")

        self.assertEqual(missing_artifact["status"], "blocked_missing_route_task_field_retest_result_acceptance_packet")
        self.assertEqual(bad_artifact["status"], "blocked_bad_json")
        self.assertEqual(unsupported_artifact["status"], "blocked_unsupported_schema")
        self.assertEqual(not_ready_artifact["status"], "blocked_acceptance_packet_not_ready")
        self.assertFalse(missing_artifact["delivery_success"])
        self.assertFalse(missing_summary["primary_actions_enabled"])

    def test_missing_placeholder_mismatch_unsafe_and_success_claim_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing_dir = self.write_materials(root, "run-004")
            (missing_dir / "delivery_result.json").unlink()
            missing_artifact, _missing_summary = self.build(root, self.packet_summary("run-004"), missing_dir, "run-004")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            placeholder_dir = self.write_materials(root, "run-005", {"door_state": {"evidence_ref": "run-005", "status": "placeholder"}})
            placeholder_artifact, _placeholder_summary = self.build(root, self.packet_summary("run-005"), placeholder_dir, "run-005")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            mismatch_dir = self.write_materials(root, "run-006", {"task_record": {"evidence_ref": "other-run", "status": "provided"}})
            mismatch_artifact, _mismatch_summary = self.build(root, self.packet_summary("run-006"), mismatch_dir, "run-006")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            unsafe_dir = self.write_materials(
                root,
                "run-007",
                {"nav2_or_fixed_route_runtime_log": "evidence_ref: run-007\nAuthorization: Bearer abc\n/cmd_vel\n/dev/ttyUSB0\n"},
            )
            unsafe_artifact, _unsafe_summary = self.build(root, self.packet_summary("run-007"), unsafe_dir, "run-007")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            success_dir = self.write_materials(root, "run-008", {"delivery_result": {"evidence_ref": "run-008", "delivery_success": True}})
            success_artifact, success_summary = self.build(root, self.packet_summary("run-008"), success_dir, "run-008")

        encoded = json.dumps(unsafe_artifact, ensure_ascii=False)
        self.assertEqual(missing_artifact["status"], "blocked_missing_materials")
        self.assertEqual(placeholder_artifact["status"], "blocked_placeholder_only_materials")
        self.assertEqual(mismatch_artifact["status"], "blocked_same_evidence_ref_mismatch")
        self.assertEqual(unsafe_artifact["status"], "blocked_unsafe_material_copy")
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertEqual(success_artifact["status"], "blocked_success_or_control_claim")
        self.assertFalse(success_artifact["delivery_success"])
        self.assertFalse(success_summary["primary_actions_enabled"])

    def test_weak_same_ref_and_cli_ref_mismatch_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            material_dir = self.write_materials(root, "run-009")
            weak = self.packet_summary("run-009")
            weak["same_evidence_ref_required"] = "true"
            weak_artifact, _weak_summary = self.build(root, weak, material_dir, "run-009")
            mismatch_artifact, _mismatch_summary = self.build(root, self.packet_summary("run-009"), material_dir, "another-run")

        self.assertEqual(weak_artifact["status"], "blocked_same_evidence_ref_not_required")
        self.assertEqual(mismatch_artifact["status"], "blocked_same_evidence_ref_not_required")


if __name__ == "__main__":
    unittest.main()
