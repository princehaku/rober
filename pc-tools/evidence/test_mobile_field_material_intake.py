#!/usr/bin/env python3
"""mobile field material intake gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import mobile_field_material_intake as intake  # noqa: E402


class MobileFieldMaterialIntakeTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 临时 JSON 让测试不依赖 ROS2、Nav2、真实手机、真实电梯或云。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def precheck_payload(self, evidence_ref: str) -> dict:
        # precheck 样本只代表 software proof，不是真实 route/elevator pass。
        return {
            "schema": "trashbot.mobile_route_elevator_field_device_precheck_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_mobile_route_elevator_field_device_precheck_gate",
            "status": "ready_for_field_device_precheck_not_proven",
            "precheck_verdict": "ready_for_field_device_precheck_not_proven",
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "not_proven": ["real_phone_device_or_browser", "real_nav2_fixed_route_run", "delivery_success"],
        }

    def material_payload(self, evidence_ref: str, kind: str) -> dict:
        # 每份材料只声明可读和同 ref；不把任何现场 success 写入 gate。
        return {
            "schema": f"trashbot.test.{kind}.v1",
            "source": "software_proof",
            "evidence_ref": evidence_ref,
            "material_status": "present_not_proven",
            "notes": f"{kind} material captured for review only",
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def build_paths(self, root: Path, evidence_ref: str) -> tuple[Path, dict[str, str]]:
        # 所有 required material 都必须存在，避免 happy path 漏测缺失分支。
        precheck = self.write_json(root, "precheck.json", self.precheck_payload(evidence_ref))
        paths = {
            label: str(self.write_json(root, filename, self.material_payload(evidence_ref, label)))
            for label, filename in intake.MATERIAL_INPUTS
        }
        return precheck, paths

    def test_ready_intake_not_proven_with_same_evidence_ref(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            precheck, paths = self.build_paths(root, "run-101")
            artifact, summary, exit_code = intake.build_intake(str(precheck), "run-101", paths)

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.mobile_field_material_intake.v1")
        self.assertEqual(summary["schema"], "trashbot.mobile_field_material_intake_summary.v1")
        self.assertEqual(artifact["evidence_boundary"], "software_proof_docker_mobile_field_material_intake_gate")
        self.assertEqual(artifact["intake_verdict"], "ready_for_mobile_field_material_review_not_proven")
        self.assertEqual(artifact["same_evidence_ref_status"], "matched_same_evidence_ref")
        self.assertIn("door_state.json", summary["required_route_elevator_field_material_names"])
        self.assertIn("mobile_field_material_intake_panel_visible", summary["device_pwa_observation_checklist_names"])
        self.assertIn("real_phone_device_or_browser", artifact["not_proven"])
        self.assertIn("delivery_success", artifact["not_proven"])
        self.assertFalse(artifact["real_device_observed"])
        self.assertFalse(artifact["pwa_install_prompt_observed"])
        self.assertFalse(artifact["route_elevator_field_pass"])
        self.assertFalse(artifact["nav2_fixed_route_completed"])
        self.assertFalse(artifact["dropoff_completion"])
        self.assertFalse(artifact["cancel_completion"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertEqual(artifact["mobile_copy_summary"]["schema"], "trashbot.mobile_field_material_intake_copy.v1")

    def test_missing_precheck_and_missing_materials_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing_artifact, _, missing_exit = intake.build_intake(str(root / "missing.json"), "run-102", {})

            precheck = self.write_json(root, "precheck.json", self.precheck_payload("run-102"))
            partial_paths = {
                "device_pwa_observation": str(
                    self.write_json(root, "device.json", self.material_payload("run-102", "device_pwa_observation"))
                )
            }
            partial_artifact, _, partial_exit = intake.build_intake(str(precheck), "run-102", partial_paths)

        self.assertEqual(missing_exit, 2)
        self.assertEqual(partial_exit, 2)
        self.assertEqual(missing_artifact["intake_verdict"], "blocked_missing_inputs")
        self.assertEqual(partial_artifact["intake_verdict"], "blocked_invalid_or_missing_field_materials")
        self.assertIn("task_record_not_provided", partial_artifact["missing_or_blocked"])

    def test_evidence_ref_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            precheck, paths = self.build_paths(root, "run-source")
            artifact, summary, exit_code = intake.build_intake(str(precheck), "run-target", paths)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["intake_verdict"], "blocked_invalid_precheck")
        self.assertIn("mobile_route_elevator_field_device_precheck:evidence_ref", artifact["missing_or_blocked"])
        self.assertFalse(summary["delivery_success"])

    def test_placeholder_unsafe_copy_and_success_claim_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            precheck, paths = self.build_paths(root, "run-103")

            placeholder = self.material_payload("run-103", "task_record")
            placeholder["operator_note"] = "TODO replace_me"
            paths["task_record"] = str(self.write_json(root, "task_placeholder.json", placeholder))
            placeholder_artifact, _, placeholder_exit = intake.build_intake(str(precheck), "run-103", paths)

            precheck_104, paths = self.build_paths(root, "run-104")
            unsafe = self.material_payload("run-104", "device_pwa_observation")
            unsafe["operator_note"] = "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 baudrate=115200 raw robot response"
            paths["device_pwa_observation"] = str(self.write_json(root, "unsafe.json", unsafe))
            unsafe_artifact, _, unsafe_exit = intake.build_intake(str(precheck_104), "run-104", paths)

            precheck_105, paths = self.build_paths(root, "run-105")
            success = self.material_payload("run-105", "completion_signal")
            success["delivery_success"] = True
            paths["completion_signal"] = str(self.write_json(root, "success.json", success))
            success_artifact, _, success_exit = intake.build_intake(str(precheck_105), "run-105", paths)

        self.assertEqual(placeholder_exit, 2)
        self.assertIn("task_record:placeholder", placeholder_artifact["missing_or_blocked"])
        self.assertEqual(unsafe_exit, 2)
        self.assertIn("device_pwa_observation:unsafe_copy", unsafe_artifact["missing_or_blocked"])
        self.assertNotIn("/dev/ttyUSB0", json.dumps(unsafe_artifact, ensure_ascii=False))
        self.assertEqual(success_exit, 2)
        self.assertIn("completion_signal:success_or_control_claim", success_artifact["missing_or_blocked"])

    def test_validate_existing_summary_accepts_not_proven_and_blocks_true_flags(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            precheck, paths = self.build_paths(root, "run-106")
            ready_artifact, summary, _ = intake.build_intake(str(precheck), "run-106", paths)
            summary_path = self.write_json(root, "summary.json", summary)
            validated, validated_summary, validated_exit = intake.validate_intake(str(summary_path), "run-106")

            bad = dict(summary)
            bad["route_elevator_field_pass"] = True
            bad_path = self.write_json(root, "bad_summary.json", bad)
            blocked, _, blocked_exit = intake.validate_intake(str(bad_path), "run-106")

        self.assertEqual(ready_artifact["intake_verdict"], "ready_for_mobile_field_material_review_not_proven")
        self.assertEqual(validated_exit, 0)
        self.assertEqual(validated["intake_verdict"], "validated_mobile_field_material_intake_not_proven")
        self.assertEqual(validated_summary["same_evidence_ref_status"], "matched_same_evidence_ref")
        self.assertEqual(blocked_exit, 2)
        self.assertEqual(blocked["intake_verdict"], "blocked_invalid_intake")
        self.assertIn("intake:success_or_control_claim", blocked["missing_or_blocked"])


if __name__ == "__main__":
    unittest.main()
