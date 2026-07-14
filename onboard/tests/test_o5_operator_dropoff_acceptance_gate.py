"""O5 operator dropoff acceptance gate CLI 的 synthetic 合同单测。"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "o5_operator_dropoff_acceptance_gate.py"
SPEC = importlib.util.spec_from_file_location("o5_operator_dropoff_acceptance_gate", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
OPERATOR_GATE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = OPERATOR_GATE
SPEC.loader.exec_module(OPERATOR_GATE)

from ros2_trashbot_behavior.delivery_state_machine import (  # noqa: E402
    OPERATOR_DROPOFF_ACCEPTANCE_GATE_PROOF_BOUNDARY,
    OPERATOR_DROPOFF_ACCEPTANCE_GATE_SCHEMA,
)


class O5OperatorDropoffAcceptanceGateTests(unittest.TestCase):
    """验证 synthetic fixture 只能证明 gate ready，不能证明真实送达。"""

    def test_build_summary_keeps_synthetic_fixture_fail_closed(self) -> None:
        """当前 fixture 必须 ready 但 delivery/route/HIL/safe 全 false。"""
        summary = OPERATOR_GATE.build_summary(
            fixture_mode="synthetic",
            generated_at_utc="2026-07-14T07:29:00Z",
        )

        self.assertEqual(OPERATOR_DROPOFF_ACCEPTANCE_GATE_SCHEMA, summary["schema"])
        self.assertEqual(OPERATOR_DROPOFF_ACCEPTANCE_GATE_PROOF_BOUNDARY, summary["proof_boundary"])
        self.assertTrue(summary["operator_dropoff_acceptance_gate_ready"])
        self.assertFalse(summary["operator_dropoff_acceptance_gate_accepted"])
        self.assertNotEqual("live", summary["source_mode"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["route_execution_success"])
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["hil_pass"])
        self.assertEqual("blocked_missing_live_success_evidence", summary["acceptance_decision"])
        self.assertIn("source_mode_live", summary["missing_live_evidence"])

    def test_write_summary_creates_json_artifact_without_absolute_source_ref(self) -> None:
        """写出的 artifact 只保留 fixture ref，不带开发机绝对路径。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "artifacts" / "operator_dropoff_acceptance_gate_summary.json"
            summary = OPERATOR_GATE.write_summary(
                output,
                fixture_mode="synthetic",
                generated_at_utc="2026-07-14T07:30:00Z",
            )
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(summary["schema"], payload["schema"])
        self.assertEqual("synthetic_operator_dropoff_acceptance_fixture", payload["source_summary_ref"])
        self.assertNotIn(str(root), json.dumps(payload, ensure_ascii=False, sort_keys=True))

    def test_main_writes_summary_and_prints_json(self) -> None:
        """命令行成功时打印 JSON，且不依赖真实云、硬件或浏览器。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "summary.json"
            with redirect_stdout(io.StringIO()) as stdout:
                rc = OPERATOR_GATE.main(
                    [
                        "--fixture-mode",
                        "synthetic",
                        "--output",
                        str(output),
                    ]
                )
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(0, rc)
        self.assertEqual(OPERATOR_DROPOFF_ACCEPTANCE_GATE_SCHEMA, payload["schema"])
        self.assertIn("operator_dropoff_acceptance", stdout.getvalue())
        self.assertIn("software_proof_o5_operator_dropoff_acceptance_gate_only", stdout.getvalue())
        self.assertNotIn("Traceback", stdout.getvalue())

    def test_unsupported_fixture_mode_is_not_live_capture(self) -> None:
        """CLI 不能被误当成 live 采集入口；真实证据需后续独立接入。"""
        with self.assertRaises(ValueError):
            OPERATOR_GATE.evidence_for_fixture_mode("live")


if __name__ == "__main__":
    unittest.main()
