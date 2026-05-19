#!/usr/bin/env python3
"""hardware_real_material_escalation_request gate 的离线围栏测试。"""

from __future__ import annotations

# 测试约束 01：ready case 只是 software_proof 升级请求，不证明 HIL。
# 测试约束 02：ready case 必须覆盖 WAVE ROVER/UART/HIL 缺口。
# 测试约束 03：ready case 必须覆盖 PR #5 2D LiDAR / ToF 缺口。
# 测试约束 04：summary 必须保持 phone-safe 与 summary-only。
# 测试约束 05：缺 docs/vendor/VENDOR_INDEX.md 必须 fail closed。
# 测试约束 06：缺 production boundary 必须 fail closed。
# 测试约束 07：输出必须保持 delivery_success=false。
# 测试约束 08：输出必须保持 primary_actions_enabled=false。

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "pc-tools" / "evidence" / "hardware_real_material_escalation_request.py"
SPEC = importlib.util.spec_from_file_location("hardware_real_material_escalation_request", SCRIPT)
gate = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(gate)


class HardwareRealMaterialEscalationRequestTest(unittest.TestCase):
    def test_ready_request_is_summary_only_and_not_proven(self):
        artifact, summary, exit_code = gate.build_hardware_real_material_escalation_request()

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.hardware_real_material_escalation_request.v1")
        self.assertEqual(summary["schema"], "trashbot.hardware_real_material_escalation_request_summary.v1")
        self.assertEqual(artifact["source"], "software_proof")
        self.assertEqual(artifact["evidence_status"], "not_proven")
        self.assertEqual(artifact["hardware_material_status"], "hardware_material_pending")
        self.assertTrue(summary["summary_only"])
        self.assertTrue(summary["phone_safe"])
        self.assertIn("docs/vendor/VENDOR_INDEX.md", encoded)
        self.assertIn("WAVE ROVER", encoded)
        self.assertIn("UART", encoded)
        self.assertIn("HIL", encoded)
        self.assertIn("PR #5", encoded)
        self.assertIn("2D LiDAR", encoded)
        self.assertIn("ToF", encoded)
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_missing_vendor_index_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            product_boundary = root / "production_hardware_boundary.md"
            product_boundary.write_text("Production Hardware Boundary\n", encoding="utf-8")

            artifact, summary, exit_code = gate.build_hardware_real_material_escalation_request(
                vendor_index=root / "missing_vendor.md",
                product_boundary=product_boundary,
            )

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["status"], "blocked_missing_vendor_index")
        self.assertEqual(summary["hardware_material_status"], "hardware_material_pending")
        self.assertEqual(summary["evidence_status"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_missing_product_boundary_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            vendor_index = root / "VENDOR_INDEX.md"
            vendor_index.write_text("Vendor Hardware and Software Reference Index\n", encoding="utf-8")

            artifact, summary, exit_code = gate.build_hardware_real_material_escalation_request(
                vendor_index=vendor_index,
                product_boundary=root / "missing_boundary.md",
            )

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["status"], "blocked_missing_production_hardware_boundary")
        self.assertTrue(summary["summary_only"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_cli_writes_artifact_and_summary(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact_path = root / "artifact.json"
            summary_path = root / "summary.json"
            exit_code = gate.main(["--output", str(artifact_path), "--summary-output", str(summary_path)])
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            summary = json.loads(summary_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["hardware_real_material_escalation_request"], summary["status"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
