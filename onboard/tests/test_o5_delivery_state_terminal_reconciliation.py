"""O5 delivery state terminal reconciliation 的离线 fail-closed 单测。"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "o5_delivery_state_terminal_reconciliation.py"
SPEC = importlib.util.spec_from_file_location("o5_delivery_state_terminal_reconciliation", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
RECONCILE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RECONCILE
SPEC.loader.exec_module(RECONCILE)

from ros2_trashbot_behavior.delivery_state_machine import (  # noqa: E402
    BOUNDED_ROUTE_TERMINAL_RESULT_BRIDGE_PROOF_BOUNDARY,
    BOUNDED_ROUTE_TERMINAL_RESULT_BRIDGE_SCHEMA,
    DELIVERY_STATE_TERMINAL_RECONCILIATION_SCHEMA,
    MOCK_ROUTE_TERMINAL_RESULT_CODE,
    MOCK_ROUTE_TERMINAL_TASK_STATE,
    TerminalResultReconciliationError,
)


def source_summary_fixture() -> dict:
    """构造 00:24 O5 bridge summary 的最小可信形状。"""
    fixed_false_fields = {
        "delivery_success": False,
        "route_execution_success": False,
        "safe_to_control": False,
        "hil_pass": False,
        "robot_control_executed": False,
        "connects_cloud_production": False,
        "uses_base_uart": False,
        "publishes_cmd_vel": False,
        "calls_base_manual": False,
    }
    return {
        **fixed_false_fields,
        "schema": BOUNDED_ROUTE_TERMINAL_RESULT_BRIDGE_SCHEMA,
        "proof_boundary": BOUNDED_ROUTE_TERMINAL_RESULT_BRIDGE_PROOF_BOUNDARY,
        "result_code": MOCK_ROUTE_TERMINAL_RESULT_CODE,
        "terminal_result_state": "terminal_result_recorded",
        "reconciliation_state": "terminal_result_recorded",
        "task_terminal_state": MOCK_ROUTE_TERMINAL_TASK_STATE,
        "terminal_result_type": "delivery_terminal",
        "task_id": "task_o3_28_pose_fixed_route_consumer_20260713_0402",
        "packet_id": "packet_o3_28_pose_same_task_replay_7d57826142b0c79c",
        "route_intent_id": "route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path",
        "route_csv_row_count": 28,
        "path_structured_pose_count": 28,
        "segment_count": 27,
        "primary_actions_enabled": False,
        "real_world_delivery_proven": False,
        "production_cloud_ready": False,
        "fixed_false_fields": fixed_false_fields,
    }


class O5DeliveryStateTerminalReconciliationTests(unittest.TestCase):
    """验证 CLI 和状态机对 mock terminal result 的边界一致。"""

    def write_source(self, root: Path, payload: dict | None = None) -> Path:
        """把 fixture 写成临时 source summary，模拟 sprint artifact 输入。"""
        path = root / "o5_bounded_route_terminal_result_bridge_summary.json"
        path.write_text(json.dumps(payload or source_summary_fixture(), sort_keys=True), encoding="utf-8")
        return path

    def test_build_summary_accepts_mock_terminal_result_as_fail_closed_material_only(self) -> None:
        """有效 source 只进入 error/fail-closed，不产生 delivery success。"""
        summary = RECONCILE.build_summary(
            source_summary_fixture(),
            source_summary_ref="o5_bounded_route_terminal_result_bridge_summary.json",
            generated_at_utc="2026-07-14T04:27:00Z",
        )

        self.assertEqual(DELIVERY_STATE_TERMINAL_RECONCILIATION_SCHEMA, summary["schema"])
        self.assertEqual(MOCK_ROUTE_TERMINAL_RESULT_CODE, summary["result_code"])
        self.assertEqual("error", summary["final_state"])
        self.assertEqual("fail_closed_mock_terminal_result_not_delivery", summary["reconciliation_status"])
        self.assertFalse(summary["terminal_result_accepted_for_delivery"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["route_execution_success"])
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["hil_pass"])
        events = " ".join(str(event) for event in summary["state_machine_events"]).lower()
        self.assertIn("mock", events)
        self.assertIn("delivery", events)
        self.assertIn("not", events)

    def test_write_summary_creates_artifact_with_source_basename(self) -> None:
        """写出的 artifact 只保留 source basename，避免传播本地绝对路径。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = self.write_source(root)
            output = root / "out" / "delivery_state_terminal_reconciliation_summary.json"
            summary = RECONCILE.write_summary(
                source,
                output,
                generated_at_utc="2026-07-14T04:28:00Z",
            )
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(summary["schema"], payload["schema"])
        self.assertEqual(source.name, payload["source_summary_ref"])
        self.assertNotIn(str(root), json.dumps(payload, ensure_ascii=False, sort_keys=True))

    def test_main_writes_summary_without_traceback(self) -> None:
        """命令行入口成功时打印 JSON，不依赖 traceback 或外部服务。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = self.write_source(root)
            output = root / "summary.json"
            with redirect_stdout(io.StringIO()) as stdout:
                rc = RECONCILE.main(["--source-summary", str(source), "--output", str(output)])
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(0, rc)
        self.assertEqual(DELIVERY_STATE_TERMINAL_RECONCILIATION_SCHEMA, payload["schema"])
        self.assertIn("delivery_state_terminal_reconciliation", stdout.getvalue())
        self.assertNotIn("Traceback", stdout.getvalue())

    def test_rejects_dangerous_true_field_before_output(self) -> None:
        """危险 true 字段不能被降级成 warning，必须直接拒绝。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            payload = source_summary_fixture()
            payload["delivery_success"] = True
            source = self.write_source(root, payload)
            output = root / "summary.json"

            with self.assertRaises(TerminalResultReconciliationError):
                RECONCILE.write_summary(source, output)
            self.assertFalse(output.exists())

    def test_rejects_source_schema_drift_before_output(self) -> None:
        """source schema 漂移表示材料族不再匹配，必须 fail closed。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            payload = source_summary_fixture()
            payload["schema"] = "trashbot.o5.unexpected.v1"
            source = self.write_source(root, payload)
            output = root / "summary.json"

            with self.assertRaises(TerminalResultReconciliationError):
                RECONCILE.write_summary(source, output)
            self.assertFalse(output.exists())

    def test_rejects_missing_identity_before_output(self) -> None:
        """缺少 packet/task/route 身份时不能绑定到同一条路线材料。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            payload = source_summary_fixture()
            payload["packet_id"] = ""
            source = self.write_source(root, payload)
            output = root / "summary.json"

            with self.assertRaises(TerminalResultReconciliationError):
                RECONCILE.write_summary(source, output)
            self.assertFalse(output.exists())

    def test_rejects_unexpected_success_or_live_state_before_output(self) -> None:
        """source 若声称 live/success，就不再是本轮 mock fail-closed 材料。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            payload = source_summary_fixture()
            payload["task_terminal_state"] = "live_route_execution_delivery_success"
            source = self.write_source(root, payload)
            output = root / "summary.json"

            with self.assertRaises(TerminalResultReconciliationError):
                RECONCILE.write_summary(source, output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
