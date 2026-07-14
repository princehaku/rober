"""O5 delivery state live success gate CLI 的本地合同单测。"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "o5_delivery_state_live_success_gate.py"
SPEC = importlib.util.spec_from_file_location("o5_delivery_state_live_success_gate", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
LIVE_GATE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = LIVE_GATE
SPEC.loader.exec_module(LIVE_GATE)

from ros2_trashbot_behavior.delivery_state_machine import (  # noqa: E402
    DELIVERY_STATE_LIVE_SUCCESS_GATE_PROOF_BOUNDARY,
    DELIVERY_STATE_LIVE_SUCCESS_GATE_SCHEMA,
)


class O5DeliveryStateLiveSuccessGateTests(unittest.TestCase):
    """验证 synthetic/current-live-shaped artifact 只证明 gate ready。"""

    def test_build_summary_keeps_current_run_false_fields(self) -> None:
        """默认 fixture 必须 contract-ready，但不能声明真实 delivery。"""
        summary = LIVE_GATE.build_summary(
            fixture_mode="synthetic-current-live",
            generated_at_utc="2026-07-14T05:28:00Z",
        )

        self.assertEqual(DELIVERY_STATE_LIVE_SUCCESS_GATE_SCHEMA, summary["schema"])
        self.assertEqual(DELIVERY_STATE_LIVE_SUCCESS_GATE_PROOF_BOUNDARY, summary["proof_boundary"])
        self.assertTrue(summary["live_success_gate_contract_ready"])
        self.assertFalse(summary["current_live_evidence_observed"])
        self.assertFalse(summary["delivery_success_claimed_by_this_run"])
        self.assertFalse(summary["real_world_delivery_proven"])
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["hil_pass"])
        self.assertFalse(summary["delivery_success_accepted_for_state_machine"])
        self.assertIn("source_mode_live", summary["missing_live_evidence"])
        self.assertIn("live_route_execution_success", summary["missing_live_evidence"])
        self.assertIn("operator_dropoff_acceptance", summary["missing_live_evidence"])
        self.assertIn("terminal_result_recorded", summary["missing_live_evidence"])

    def test_write_summary_creates_json_artifact_without_absolute_source_ref(self) -> None:
        """写出的 artifact 只保留 fixture basename，不传播开发机路径。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "artifacts" / "delivery_state_live_success_gate_summary.json"
            summary = LIVE_GATE.write_summary(
                output,
                fixture_mode="synthetic-current-live",
                generated_at_utc="2026-07-14T05:29:00Z",
            )
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(summary["schema"], payload["schema"])
        self.assertEqual("synthetic-current-live_fixture", payload["source_summary_ref"])
        self.assertNotIn(str(root), json.dumps(payload, ensure_ascii=False, sort_keys=True))

    def test_main_writes_summary_and_prints_json(self) -> None:
        """命令行成功时打印 JSON，且不依赖真实云、硬件或浏览器。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "summary.json"
            with redirect_stdout(io.StringIO()) as stdout:
                rc = LIVE_GATE.main(
                    [
                        "--fixture-mode",
                        "synthetic-current-live",
                        "--output",
                        str(output),
                    ]
                )
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(0, rc)
        self.assertEqual(DELIVERY_STATE_LIVE_SUCCESS_GATE_SCHEMA, payload["schema"])
        self.assertIn("delivery_state_live_success_gate", stdout.getvalue())
        self.assertIn("software_proof_o5_delivery_state_live_success_gate_only", stdout.getvalue())
        self.assertNotIn("Traceback", stdout.getvalue())

    def test_unsupported_fixture_mode_is_not_live_capture(self) -> None:
        """CLI 不能被误当成 live 采集入口；真实证据需后续独立接入。"""
        with self.assertRaises(ValueError):
            LIVE_GATE.evidence_for_fixture_mode("live")


if __name__ == "__main__":
    unittest.main()
