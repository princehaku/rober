#!/usr/bin/env python3
"""real_material_evidence_intake gate 的离线围栏测试。"""

from __future__ import annotations

# 测试约束 01：默认 sample manifest 只能生成 software_proof，不证明真实材料到位。
# 测试约束 02：四类 material group 必须全部输出，避免漏掉 Objective 5 / Objective 1 / PR #4 / O4。
# 测试约束 03：PR #5 `PRRT_kwDOSWB9286CJ3tX` 必须保留且保持 blocked_pending_real_materials_not_closed。
# 测试约束 04：safe evidence_ref 必须拒绝空值、不安全字符和跨组不一致。
# 测试约束 05：manifest 中出现成功、控制、凭证、绝对路径或敏感 token 必须 fail closed。
# 测试约束 06：accepted_items 只表示可人工复核，不代表真实 HIL、公网或手机通过。
# 测试约束 07：输出必须保持 delivery_success=false。
# 测试约束 08：输出必须保持 primary_actions_enabled=false 和 safe_to_control=false。

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "pc-tools" / "evidence" / "real_material_evidence_intake.py"
SPEC = importlib.util.spec_from_file_location("real_material_evidence_intake", SCRIPT)
gate = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(gate)


def _valid_manifest() -> dict:
    # 这个 manifest 只验证合同形状；summary 文案仍保持 not_proven。
    evidence_ref = "field-material-2026-05-19T21-22Z"
    groups = {}
    for group_id, spec in gate.MATERIAL_GROUPS.items():
        groups[group_id] = {
            "evidence_ref": evidence_ref,
            "items": {
                item: {
                    "summary": f"{item} metadata summary for manual review",
                    "material_ref": f"{group_id}-{item}-redacted-ref",
                }
                for item in spec["required_items"]
            },
        }
    return {"schema": "trashbot.real_material_manifest.v1", "evidence_ref": evidence_ref, "material_groups": groups}


class RealMaterialEvidenceIntakeTest(unittest.TestCase):
    def test_default_sample_manifest_fails_closed_with_missing_items(self):
        artifact, summary, exit_code = gate.build_real_material_evidence_intake()
        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        group_ids = {group["material_group"] for group in artifact["material_groups"]}

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.real_material_evidence_intake.v1")
        self.assertEqual(summary["schema"], "trashbot.real_material_evidence_intake_summary.v1")
        self.assertEqual(group_ids, {"o5_external", "o1_pr5_hardware", "pr4_route_elevator", "o4_real_phone"})
        self.assertEqual(artifact["source"], "software_proof")
        self.assertEqual(artifact["status"], "not_proven")
        self.assertTrue(artifact["not_proven"])
        self.assertEqual(artifact["intake_status"], "blocked_missing_real_material_items")
        self.assertIn("Objective 5", encoded)
        self.assertIn("Objective 1", encoded)
        self.assertIn("PR #5", encoded)
        self.assertIn("PRRT_kwDOSWB9286CJ3tX", encoded)
        self.assertIn("blocked_pending_real_materials_not_closed", encoded)
        self.assertIn("software_proof_docker_real_material_evidence_intake_gate", encoded)
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(artifact["safe_to_control"])
        self.assertFalse(summary["safe_to_control"])

    def test_valid_manifest_accepts_shape_but_remains_not_proven(self):
        with tempfile.TemporaryDirectory() as td:
            manifest_path = Path(td) / "manifest.json"
            manifest_path.write_text(json.dumps(_valid_manifest()), encoding="utf-8")
            artifact, summary, exit_code = gate.build_real_material_evidence_intake(manifest_path)

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["intake_status"], "ready_for_real_material_evidence_review_not_proven")
        self.assertEqual(summary["accepted_count"], sum(len(spec["required_items"]) for spec in gate.MATERIAL_GROUPS.values()))
        self.assertEqual(summary["missing_count"], 0)
        self.assertEqual(summary["rejected_count"], 0)
        self.assertEqual(summary["safe_evidence_ref"], "field-material-2026-05-19T21-22Z")
        for group in artifact["material_groups"]:
            self.assertEqual(group["intake_status"], "ready_for_real_material_evidence_review_not_proven")
            self.assertTrue(group["accepted_items"])
            self.assertFalse(group["missing_items"])
            self.assertFalse(group["rejected_items"])
            self.assertFalse(group["delivery_success"])
            self.assertFalse(group["primary_actions_enabled"])
            self.assertFalse(group["safe_to_control"])

    def test_cross_group_evidence_ref_mismatch_is_rejected(self):
        manifest = _valid_manifest()
        manifest["material_groups"]["o4_real_phone"]["evidence_ref"] = "different-ref-2026-05-19"
        with tempfile.TemporaryDirectory() as td:
            manifest_path = Path(td) / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            artifact, summary, exit_code = gate.build_real_material_evidence_intake(manifest_path)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["intake_status"], "blocked_unsafe_or_inconsistent_evidence_ref")
        self.assertIn("cross_group_evidence_ref_mismatch", json.dumps(summary, ensure_ascii=False))
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["safe_to_control"])

    def test_success_control_credential_or_path_fields_fail_closed(self):
        manifest = _valid_manifest()
        manifest["material_groups"]["o1_pr5_hardware"]["items"]["hil_entry"]["delivery_success"] = True
        manifest["material_groups"]["o1_pr5_hardware"]["items"]["wave_rover_uart_hil_packet"]["material_ref"] = "/dev/ttyUSB0"
        manifest["material_groups"]["o5_external"]["items"]["external_proof"]["material_ref"] = "/tmp/external-proof.json"
        with tempfile.TemporaryDirectory() as td:
            manifest_path = Path(td) / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            artifact, summary, exit_code = gate.build_real_material_evidence_intake(manifest_path)

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["intake_status"], "blocked_unsafe_real_material_manifest")
        self.assertIn("manifest_contains_forbidden_fields", encoded)
        self.assertIn("manifest_contains_unsafe_success_control_credential_path_or_token_copy", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("/tmp/external-proof.json", encoded)
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_cli_writes_artifact_and_summary(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact_path = root / "real_material_evidence_intake.json"
            summary_path = root / "real_material_evidence_intake_summary.json"
            exit_code = gate.main(["--output", str(artifact_path), "--summary-output", str(summary_path)])
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            summary = json.loads(summary_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["real_material_evidence_intake"], summary["real_material_evidence_intake"])
        self.assertEqual(summary["group_count"], 4)
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])


if __name__ == "__main__":
    unittest.main()
