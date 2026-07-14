"""O5 bounded route terminal-result bridge 的本地/mock 主链路单测。"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "o5_bounded_route_terminal_result_bridge.py"
SPEC = importlib.util.spec_from_file_location("o5_bounded_route_terminal_result_bridge", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
BRIDGE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = BRIDGE
SPEC.loader.exec_module(BRIDGE)


def source_summary_fixture() -> dict:
    """构造 23:23 O3 source summary 的最小可信形状，便于单测覆盖 fail-closed 分支。"""
    source_false_fields = {key: False for key in BRIDGE.SOURCE_FALSE_FIELDS}
    return {
        **source_false_fields,
        "schema": BRIDGE.SOURCE_SCHEMA,
        "proof_boundary": BRIDGE.SOURCE_PROOF_BOUNDARY,
        "mock_execution_status": BRIDGE.TASK_TERMINAL_STATE,
        "mock_execution_completed": True,
        "packet_id": BRIDGE.EXPECTED_PACKET_ID,
        "task_id": BRIDGE.EXPECTED_TASK_ID,
        "route_intent_id": BRIDGE.EXPECTED_ROUTE_INTENT_ID,
        "route_csv_row_count": BRIDGE.EXPECTED_ROUTE_ROW_COUNT,
        "path_structured_pose_count": BRIDGE.EXPECTED_ROUTE_ROW_COUNT,
        "segment_count": BRIDGE.EXPECTED_SEGMENT_COUNT,
        "progress_jsonl_event_count": BRIDGE.EXPECTED_SEGMENT_COUNT,
        "mock_total_distance_m": 0.723849,
        "mock_total_elapsed_s": 7.238,
        "source_identity_verified": True,
        "source_counts_verified": True,
        "source_no_motion_guard_verified": True,
        "source_fixed_false_fields_verified": True,
        "fixed_false_fields": source_false_fields,
        "no_motion_control_guard": list(BRIDGE.NO_MOTION_GUARD_MARKERS),
    }


class O5BoundedRouteTerminalResultBridgeTests(unittest.TestCase):
    """验证 bridge 只证明 O5 relay 软件主路径，不升级 route/delivery/control 语义。"""

    def write_source(self, root: Path, payload: dict | None = None) -> Path:
        """把 source fixture 写到临时文件，模拟 CLI 消费 sprint artifact。"""
        path = root / "bounded_route_mock_execution_summary.json"
        path.write_text(json.dumps(payload or source_summary_fixture(), sort_keys=True), encoding="utf-8")
        return path

    def test_build_summary_uses_relay_command_terminal_result_and_reconciliation(self) -> None:
        """有效 source 会走三段 HTTP 主路径，并写出 terminal_result_recorded 对账状态。"""
        summary = BRIDGE.build_summary(
            source=source_summary_fixture(),
            source_summary_ref="bounded_route_mock_execution_summary.json",
            generated_at_utc="2026-07-14T00:24:00Z",
        )
        encoded = json.dumps(summary, ensure_ascii=False, sort_keys=True)

        self.assertEqual(BRIDGE.SUMMARY_SCHEMA, summary["schema"])
        self.assertEqual(BRIDGE.PROOF_BOUNDARY, summary["proof_boundary"])
        self.assertEqual(BRIDGE.SOURCE_SCHEMA, summary["source_schema"])
        self.assertEqual(BRIDGE.TERMINAL_RESULT_STATE, summary["terminal_result_state"])
        self.assertEqual(BRIDGE.TERMINAL_RESULT_STATE, summary["reconciliation_state"])
        self.assertEqual(BRIDGE.RESULT_CODE, summary["result_code"])
        self.assertEqual("cloud_command_result_reconciliation", summary["reconciliation_capability"])
        self.assertEqual(BRIDGE.EXPECTED_TASK_ID, summary["task_id"])
        self.assertIn("cloud_phone_command_api", summary["relay_capabilities"])
        self.assertIn(BRIDGE.EXPECTED_TASK_ID, summary["command_id"])
        for key in BRIDGE.FIXED_FALSE_FIELDS:
            self.assertFalse(summary[key], key)
            self.assertFalse(summary["fixed_false_fields"][key], key)
            self.assertIn(f"{key}=false", summary["fixed_false_invariants"])
        for forbidden in BRIDGE.FORBIDDEN_OUTPUT_MARKERS:
            self.assertNotIn(forbidden, encoded)

    def test_write_summary_creates_json_artifact(self) -> None:
        """CLI helper 必须可写出可 json.tool 读取的 artifact 文件。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = self.write_source(root)
            output = root / "out" / "o5_bridge_summary.json"
            summary = BRIDGE.write_summary(source, output, generated_at_utc="2026-07-14T00:25:00Z")
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(summary["schema"], payload["schema"])
        self.assertEqual(BRIDGE.TERMINAL_RESULT_STATE, payload["terminal_result_state"])
        self.assertEqual(BRIDGE.TERMINAL_RESULT_STATE, payload["reconciliation_state"])
        self.assertEqual("bounded_route_mock_execution_summary.json", payload["source_summary_ref"])

    def test_main_writes_summary_without_traceback(self) -> None:
        """命令行入口成功时打印 sanitized JSON，失败时也不会依赖 traceback。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = self.write_source(root)
            output = root / "summary.json"
            with redirect_stdout(io.StringIO()) as stdout:
                rc = BRIDGE.main(["--source-summary", str(source), "--output", str(output)])
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(0, rc)
        self.assertEqual(BRIDGE.SUMMARY_SCHEMA, payload["schema"])
        self.assertIn("bounded_route_terminal_result_bridge", stdout.getvalue())
        self.assertNotIn("Traceback", stdout.getvalue())

    def test_rejects_source_schema_drift_before_output(self) -> None:
        """source schema 漂移时不能写出 O5 bridge artifact。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            payload = source_summary_fixture()
            payload["schema"] = "trashbot.o3.other.v1"
            source = self.write_source(root, payload)
            output = root / "out.json"

            with self.assertRaises(BRIDGE.BridgeInputError):
                BRIDGE.write_summary(source, output)
            self.assertFalse(output.exists())

    def test_rejects_dangerous_true_field_before_output(self) -> None:
        """任何 route/control/delivery true 字段都不能进入 terminal-result bridge。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            payload = source_summary_fixture()
            payload["safe_to_control"] = True
            source = self.write_source(root, payload)
            output = root / "out.json"

            with self.assertRaises(BRIDGE.BridgeInputError):
                BRIDGE.write_summary(source, output)
            self.assertFalse(output.exists())

    def test_rejects_missing_source_guard_before_output(self) -> None:
        """source 未证明禁用底层控制入口时，bridge 必须 fail closed。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            payload = source_summary_fixture()
            payload["no_motion_control_guard"] = ["no low level control"]
            source = self.write_source(root, payload)
            output = root / "out.json"

            with self.assertRaises(BRIDGE.BridgeInputError):
                BRIDGE.write_summary(source, output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
