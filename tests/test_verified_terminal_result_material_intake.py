#!/usr/bin/env python3
"""verified_terminal_result_material_intake gate 的离线围栏测试。"""

from __future__ import annotations

# 测试约束 01：valid bundle 只能进入人工复核，不证明 delivery/dropoff/cancel 真实完成。
# 测试约束 02：terminal_result_type 只允许 delivery、dropoff、cancel。
# 测试约束 03：顶层 evidence_ref 和 nested material refs 必须一致。
# 测试约束 04：缺 required materials 时必须 blocked，但仍输出安全 summary。
# 测试约束 05：raw artifact、本机路径、凭证、ROS/control 和 hardware details 必须拒绝。
# 测试约束 06：输出保持 software_proof、not_proven、delivery_success=false。
# 测试约束 07：输出保持 primary_actions_enabled=false 和 safe_to_control=false。
# 测试约束 08：测试不访问 ROS graph、Nav2、硬件、真实手机或云端。

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "pc-tools" / "evidence" / "verified_terminal_result_material_intake.py"
SPEC = importlib.util.spec_from_file_location("verified_terminal_result_material_intake", SCRIPT)
gate = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(gate)


def _bundle(result_type: str = "delivery", evidence_ref: str = "terminal-result-2026-05-22T04-05Z") -> dict:
    # 测试 fixture 只提供脱敏 metadata，不包含 raw route log 或真实现场文件。
    materials = {
        name: {
            "evidence_ref": evidence_ref,
            "summary": f"{name} redacted metadata for terminal result review",
            "material_ref": f"{name}-safe-ticket",
        }
        for name in gate.REQUIRED_MATERIALS[result_type]
    }
    return {
        "schema": "trashbot.verified_terminal_result_material_bundle.v1",
        "evidence_ref": evidence_ref,
        "terminal_result_type": result_type,
        "materials": materials,
    }


class VerifiedTerminalResultMaterialIntakeTest(unittest.TestCase):
    def _write_bundle(self, root: Path, payload: dict) -> Path:
        # 临时输入文件只服务 CLI/gate 测试，不进入输出 artifact。
        path = root / "bundle.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_valid_delivery_bundle_generates_not_proven_summary(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle_path = self._write_bundle(Path(td), _bundle("delivery"))
            artifact, summary, exit_code = gate.build_verified_terminal_result_material_intake(bundle_path)

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], gate.SCHEMA)
        self.assertEqual(summary["schema"], gate.SUMMARY_SCHEMA)
        self.assertEqual(artifact["intake_status"], gate.READY_STATUS)
        self.assertEqual(artifact["terminal_result_type"], "delivery")
        self.assertEqual(artifact["evidence_boundary"], gate.EVIDENCE_BOUNDARY)
        self.assertEqual(artifact["accepted_count"], len(gate.REQUIRED_MATERIALS["delivery"]))
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])
        self.assertIn("software_proof_docker_verified_terminal_result_material_intake_gate", encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("delivery_success=false", encoded)
        self.assertIn("primary_actions_enabled=false", encoded)
        self.assertIn("safe_to_control=false", encoded)

    def test_dropoff_and_cancel_required_materials_are_type_specific(self) -> None:
        for result_type in ("dropoff", "cancel"):
            with self.subTest(result_type=result_type), tempfile.TemporaryDirectory() as td:
                bundle_path = self._write_bundle(Path(td), _bundle(result_type))
                artifact, summary, exit_code = gate.build_verified_terminal_result_material_intake(bundle_path)

            self.assertEqual(exit_code, 0)
            self.assertEqual(artifact["terminal_result_type"], result_type)
            self.assertEqual(artifact["required_materials"], list(gate.REQUIRED_MATERIALS[result_type]))
            self.assertFalse(artifact["missing_materials"])
            self.assertEqual(summary["accepted_count"], len(gate.REQUIRED_MATERIALS[result_type]))
            self.assertFalse(summary["delivery_success"])
            self.assertFalse(summary["safe_to_control"])

    def test_missing_required_materials_fail_closed_without_success_claim(self) -> None:
        payload = _bundle("delivery")
        payload["materials"].pop("delivery_result")
        with tempfile.TemporaryDirectory() as td:
            bundle_path = self._write_bundle(Path(td), payload)
            artifact, summary, exit_code = gate.build_verified_terminal_result_material_intake(bundle_path)

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["intake_status"], gate.MISSING_STATUS)
        self.assertIn("delivery_result", artifact["missing_materials"])
        self.assertIn("delivery_result", summary["missing_materials"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])

    def test_invalid_type_and_nested_evidence_ref_mismatch_are_rejected(self) -> None:
        unsupported = _bundle("delivery")
        unsupported["terminal_result_type"] = "success"
        mismatch = _bundle("delivery")
        mismatch["materials"]["delivery_result"]["evidence_ref"] = "different-terminal-result-ref"
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            unsupported_path = self._write_bundle(root, unsupported)
            unsupported_artifact, _, unsupported_code = gate.build_verified_terminal_result_material_intake(unsupported_path)
            mismatch_path = self._write_bundle(root, mismatch)
            mismatch_artifact, mismatch_summary, mismatch_code = gate.build_verified_terminal_result_material_intake(mismatch_path)

        self.assertEqual(unsupported_code, 2)
        self.assertEqual(unsupported_artifact["intake_status"], gate.TYPE_STATUS)
        self.assertEqual(mismatch_code, 2)
        self.assertEqual(mismatch_artifact["intake_status"], gate.REF_STATUS)
        self.assertIn("nested_material_evidence_ref_mismatch", json.dumps(mismatch_summary, ensure_ascii=False))
        self.assertFalse(mismatch_summary["delivery_success"])
        self.assertFalse(mismatch_summary["safe_to_control"])

    def test_unsafe_raw_paths_credentials_ros_control_and_hardware_details_fail_closed(self) -> None:
        payload = _bundle("delivery")
        payload["raw_artifacts"] = {"route_log": "/tmp/raw-route.jsonl"}
        payload["materials"]["task_record"]["material_ref"] = "/Users/m4/raw/task.json"
        payload["materials"]["route_completion_signal"]["operator_note"] = "delivery_success=true"
        payload["materials"]["nav2_fixed_route_runtime_log"]["ros_topic"] = "/cmd_vel"
        payload["materials"]["elevator_door_floor_evidence"]["hardware_details"] = "WAVE ROVER UART serial device"
        payload["materials"]["diagnostics_mobile_safe_summary"]["token"] = "secret-value"
        with tempfile.TemporaryDirectory() as td:
            bundle_path = self._write_bundle(Path(td), payload)
            artifact, summary, exit_code = gate.build_verified_terminal_result_material_intake(bundle_path)

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["intake_status"], gate.UNSAFE_STATUS)
        self.assertIn("bundle_contains_forbidden_raw_control_credential_ros_or_hardware_fields", encoded)
        self.assertNotIn("/tmp/raw-route.jsonl", encoded)
        self.assertNotIn("/Users/m4/raw/task.json", encoded)
        self.assertNotIn("secret-value", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])

    def test_cli_writes_sanitized_artifact_and_summary_to_output_dir(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bundle_path = self._write_bundle(root, _bundle("cancel"))
            output_dir = root / "out"
            exit_code = gate.main(["--input", str(bundle_path), "--output-dir", str(output_dir)])
            artifact = json.loads((output_dir / "verified_terminal_result_material_intake.json").read_text(encoding="utf-8"))
            summary = json.loads((output_dir / "verified_terminal_result_material_intake_summary.json").read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["verified_terminal_result_material_intake"], gate.READY_STATUS)
        self.assertEqual(summary["terminal_result_type"], "cancel")
        self.assertTrue(summary["summary_only"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])


if __name__ == "__main__":
    unittest.main()
