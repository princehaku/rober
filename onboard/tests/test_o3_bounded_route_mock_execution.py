"""O3 bounded route mock execution 的 strict no-motion 离线单测。"""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "o3_bounded_route_mock_execution.py"
SPEC = importlib.util.spec_from_file_location("o3_bounded_route_mock_execution", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
HELPER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HELPER)


def bounded_segments(count: int = HELPER.EXPECTED_SEGMENT_COUNT) -> list[dict]:
    """构造 27 段 fixture；每段只含几何和 plan cap，不含任何控制命令。"""
    segments: list[dict] = []
    for index in range(count):
        segments.append(
            {
                "segment_index": index,
                "from_order": index,
                "to_order": index + 1,
                "from_source_index": index,
                "to_source_index": index + 1,
                "frame_id": "map",
                "distance_m": 0.05,
                "planned_linear_speed_cap_mps": 0.1,
                "segment_timeout_s": 3.0,
                "abort_check_ids": ["operator_stop_requested", "control_permission_not_true"],
            }
        )
    return segments


def base_plan() -> dict:
    """最小 accepted bounded plan fixture，锁定 identity、counts、guard 和 false 字段。"""
    false_fields = {field: False for field in HELPER.SAFETY_FALSE_FIELDS}
    return {
        **false_fields,
        "schema": HELPER.SOURCE_PLAN_SCHEMA,
        "execution_plan_status": HELPER.SOURCE_EXECUTION_PLAN_STATUS,
        "proof_boundary": "software_proof_o3_o1_no_motion_bounded_route_command_plan_only",
        "packet_id": HELPER.EXPECTED_PACKET_ID,
        "task_id": HELPER.EXPECTED_TASK_ID,
        "route_intent_id": HELPER.EXPECTED_ROUTE_INTENT_ID,
        "route_csv_row_count": HELPER.EXPECTED_ROUTE_ROW_COUNT,
        "segment_count": HELPER.EXPECTED_SEGMENT_COUNT,
        "replay_jsonl_event_count": HELPER.EXPECTED_ROUTE_ROW_COUNT,
        "packet_jsonl_event_count": HELPER.EXPECTED_ROUTE_ROW_COUNT,
        "path_structured_pose_count": HELPER.EXPECTED_ROUTE_ROW_COUNT,
        "bounded_segment_plan": bounded_segments(),
        "fixed_false_fields": false_fields,
        "no_motion_control_guard": list(HELPER.NO_MOTION_GUARDS),
    }


class O3BoundedRouteMockExecutionTests(unittest.TestCase):
    """验证 mock execution 只产出软件进度材料，不改变 live-control false 边界。"""

    def write_plan_fixture(self, root: Path, payload: dict | None = None) -> Path:
        """把 plan fixture 写入临时目录，模拟 CLI 消费真实 artifact path。"""
        path = root / "bounded_route_command_plan.json"
        path.write_text(json.dumps(payload or base_plan(), sort_keys=True), encoding="utf-8")
        return path

    def load_events(self, root: Path) -> list[dict]:
        """读取 progress JSONL，测试每行都是独立 JSON event。"""
        progress_path = root / "out" / HELPER.PROGRESS_OUTPUT_NAME
        return [json.loads(line) for line in progress_path.read_text(encoding="utf-8").splitlines()]

    def test_writes_summary_and_27_mock_progress_events(self) -> None:
        """有效 bounded plan 会生成 27 条 mock completion event，但所有控制字段仍 false。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan_path = self.write_plan_fixture(root)

            summary = HELPER.write_outputs(
                plan_path,
                root / "out",
                generated_at_utc="2026-07-13T15:23:00Z",
            )
            events = self.load_events(root)

            self.assertEqual(HELPER.SUMMARY_SCHEMA, summary["schema"])
            self.assertEqual(HELPER.MOCK_EXECUTION_STATUS, summary["mock_execution_status"])
            self.assertEqual(HELPER.PROOF_BOUNDARY, summary["proof_boundary"])
            self.assertEqual(HELPER.EXPECTED_PACKET_ID, summary["packet_id"])
            self.assertEqual(HELPER.EXPECTED_SEGMENT_COUNT, summary["mock_segment_progress_count"])
            self.assertEqual(HELPER.EXPECTED_SEGMENT_COUNT, summary["progress_jsonl_event_count"])
            self.assertTrue(summary["mock_execution_completed"])
            self.assertEqual(1.35, summary["mock_total_distance_m"])
            self.assertEqual(13.5, summary["mock_total_elapsed_s"])
            self.assertEqual(list(range(HELPER.EXPECTED_SEGMENT_COUNT)), [event["segment_index"] for event in events])
            self.assertEqual("mock_segment_completed_not_live_control", events[0]["event_type"])
            self.assertEqual(0, events[0]["from_order"])
            self.assertEqual(1, events[0]["to_order"])
            self.assertEqual(0.05, events[0]["distance_m"])
            self.assertEqual(0.5, events[0]["elapsed_s"])
            self.assertEqual(1.35, events[-1]["cumulative_distance_m"])
            self.assertIn("route_execution_success=false", summary["rg_acceptance_anchors"])
            self.assertIn("safe_to_control=false", summary["rg_acceptance_anchors"])
            for key in HELPER.SAFETY_FALSE_FIELDS:
                self.assertFalse(summary[key], key)
                self.assertFalse(summary["fixed_false_fields"][key], key)
                self.assertTrue(all(event[key] is False for event in events), key)

    def test_rejects_source_schema_drift_before_output(self) -> None:
        """schema 漂移时不能写出 bounded_route_mock_execution artifacts。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            payload = base_plan()
            payload["schema"] = "trashbot.o3.other.v1"
            plan_path = self.write_plan_fixture(root, payload)

            with self.assertRaises(HELPER.MockExecutionInputError):
                HELPER.write_outputs(plan_path, root / "out")
            self.assertFalse((root / "out" / HELPER.SUMMARY_OUTPUT_NAME).exists())
            self.assertFalse((root / "out" / HELPER.PROGRESS_OUTPUT_NAME).exists())

    def test_rejects_missing_no_motion_guard_before_output(self) -> None:
        """缺少任一 forbidden control literal 时必须 fail closed。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            payload = base_plan()
            payload["no_motion_control_guard"] = ["no /cmd_vel", "no /api/base/manual"]
            plan_path = self.write_plan_fixture(root, payload)

            with self.assertRaises(HELPER.MockExecutionInputError):
                HELPER.write_outputs(plan_path, root / "out")
            self.assertFalse((root / "out" / HELPER.SUMMARY_OUTPUT_NAME).exists())

    def test_rejects_safe_to_control_true_before_output(self) -> None:
        """任何 safe_to_control=true 输入都不能生成 mock completed progress。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            payload = base_plan()
            payload["safe_to_control"] = True
            plan_path = self.write_plan_fixture(root, payload)

            with self.assertRaises(HELPER.MockExecutionInputError):
                HELPER.write_outputs(plan_path, root / "out")
            self.assertFalse((root / "out" / HELPER.PROGRESS_OUTPUT_NAME).exists())

    def test_rejects_segment_sequence_drift_before_output(self) -> None:
        """segment 列表必须严格 0..26 且 from/to order 连续。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            payload = base_plan()
            payload["bounded_segment_plan"][3]["to_order"] = 9
            plan_path = self.write_plan_fixture(root, payload)

            with self.assertRaises(HELPER.MockExecutionInputError):
                HELPER.write_outputs(plan_path, root / "out")
            self.assertFalse((root / "out" / HELPER.SUMMARY_OUTPUT_NAME).exists())


if __name__ == "__main__":
    unittest.main()
