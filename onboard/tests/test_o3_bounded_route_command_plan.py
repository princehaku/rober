"""O3 bounded route command plan 的 strict no-motion 离线单测。"""

from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "o3_bounded_route_command_plan.py"
SPEC = importlib.util.spec_from_file_location("o3_bounded_route_command_plan", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
HELPER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HELPER)


def write_route_csv(path: Path, row_count: int = HELPER.EXPECTED_POSE_COUNT) -> None:
    """写 route CSV fixture；测试用真实 CSV parser 覆盖字段和 28 行计数。"""
    fieldnames = (
        "schema",
        "route_intent_id",
        "task_id",
        "order",
        "source_index",
        "frame_id",
        "stamp_sec",
        "stamp_nanosec",
        "x",
        "y",
        "z",
        "qx",
        "qy",
        "qz",
        "qw",
        "primary_source_artifact",
        "strict_no_motion",
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for index in range(row_count):
            writer.writerow(
                {
                    "schema": "trashbot.fixed_route_28_pose_route_csv.v1",
                    "route_intent_id": HELPER.EXPECTED_ROUTE_INTENT_ID,
                    "task_id": HELPER.EXPECTED_TASK_ID,
                    "order": index,
                    "source_index": index,
                    "frame_id": "map",
                    "stamp_sec": "1783883494",
                    "stamp_nanosec": "997523160",
                    "x": f"{index * 0.05:.3f}",
                    "y": "0.25",
                    "z": "0.0",
                    "qx": "0.0",
                    "qy": "0.0",
                    "qz": "0.0",
                    "qw": "1.0",
                    "primary_source_artifact": "fixture",
                    "strict_no_motion": "True",
                }
            )


def base_gate_record(route_csv: Path) -> dict:
    """构造最小 07:07 gate record，锁定 identity、counts、guard 和 false 字段。"""
    false_fields = {field: False for field in HELPER.SAFETY_FALSE_FIELDS}
    return {
        **false_fields,
        "schema": HELPER.GATE_RECORD_SCHEMA,
        "controlled_route_execution_gate_status": "fail_closed_input_packet_validated",
        "identity_validation_status": "pass_exact_same_task_identity",
        "count_validation_status": "pass_exact_28_28_28",
        "source_hash_validation_status": "pass_exact_source_hashes",
        "packet_id": HELPER.EXPECTED_PACKET_ID,
        "task_id": HELPER.EXPECTED_TASK_ID,
        "route_intent_id": HELPER.EXPECTED_ROUTE_INTENT_ID,
        "route_csv_ref": route_csv.as_posix(),
        "route_csv_row_count": HELPER.EXPECTED_POSE_COUNT,
        "replay_jsonl_event_count": HELPER.EXPECTED_POSE_COUNT,
        "packet_jsonl_event_count": HELPER.EXPECTED_POSE_COUNT,
        "path_structured_pose_count": HELPER.EXPECTED_POSE_COUNT,
        "fixed_false_fields": false_fields,
        "no_motion_control_guard": list(HELPER.NO_MOTION_GUARDS),
    }


class O3BoundedRouteCommandPlanTests(unittest.TestCase):
    """验证 bounded plan 只描述未来受控执行参数，不触发或声明控制执行。"""

    def write_gate_fixture(self, root: Path, row_count: int = HELPER.EXPECTED_POSE_COUNT) -> Path:
        """写 gate + route CSV fixture；source 漂移测试可复用同一个最小材料。"""
        route_csv = root / "fixed_route_28_pose_route.csv"
        write_route_csv(route_csv, row_count=row_count)
        gate_record = root / "controlled_route_execution_gate_record.json"
        gate_record.write_text(json.dumps(base_gate_record(route_csv), sort_keys=True), encoding="utf-8")
        return gate_record

    def test_writes_no_motion_bounded_plan_from_valid_gate(self) -> None:
        """有效 gate record 生成 27 段计划，但所有控制和成功字段仍 false。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            gate_record = self.write_gate_fixture(root)

            plan = HELPER.write_outputs(
                gate_record,
                root / "out",
                generated_at_utc="2026-07-13T00:09:00Z",
            )

            self.assertEqual(HELPER.PLAN_SCHEMA, plan["schema"])
            self.assertEqual(HELPER.ARTIFACT_BOUNDARY, plan["proof_boundary"])
            self.assertEqual(HELPER.EXPECTED_PACKET_ID, plan["packet_id"])
            self.assertEqual("blocked_pending_live_safety_gate", plan["execution_plan_status"])
            self.assertEqual(HELPER.EXPECTED_POSE_COUNT, plan["route_csv_row_count"])
            self.assertEqual(HELPER.EXPECTED_SEGMENT_COUNT, plan["segment_count"])
            self.assertEqual(1.35, plan["segment_distance_summary"]["total_distance_m"])
            self.assertEqual(0.05, plan["segment_distance_summary"]["max_segment_distance_m"])
            self.assertEqual("future_bounded_execution_parameters_only_not_control_commands", plan["command_cap_boundary"])
            self.assertIn("no /cmd_vel", plan["no_motion_control_guard"])
            self.assertIn("no /api/base/manual", plan["no_motion_control_guard"])
            self.assertIn("no NavigateToPose", plan["no_motion_control_guard"])
            self.assertIn("no WAVE ROVER UART", plan["no_motion_control_guard"])
            self.assertIn("operator_stop_requested", plan["bounded_segment_plan"][0]["abort_check_ids"])
            self.assertIn("route_execution_success=false", plan["rg_acceptance_anchors"])
            self.assertIn("safe_to_control=false", plan["rg_acceptance_anchors"])
            for key in HELPER.SAFETY_FALSE_FIELDS:
                self.assertFalse(plan[key], key)
                self.assertFalse(plan["fixed_false_fields"][key], key)
            self.assertTrue((root / "out" / HELPER.OUTPUT_NAME).exists())

    def test_rejects_missing_no_motion_guard_before_output(self) -> None:
        """gate record 少任一 literal guard 时必须 fail closed，不写 bounded plan。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            gate_record = self.write_gate_fixture(root)
            payload = json.loads(gate_record.read_text(encoding="utf-8"))
            payload["no_motion_control_guard"] = ["no /cmd_vel", "no /api/base/manual"]
            gate_record.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

            with self.assertRaises(HELPER.PlanInputError):
                HELPER.write_outputs(gate_record, root / "out")
            self.assertFalse((root / "out" / HELPER.OUTPUT_NAME).exists())

    def test_rejects_route_csv_count_drift_before_output(self) -> None:
        """route CSV 实际行数不是 28 时，不能只信 gate record 的 count 字段。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            gate_record = self.write_gate_fixture(root, row_count=HELPER.EXPECTED_POSE_COUNT - 1)

            with self.assertRaises(HELPER.PlanInputError):
                HELPER.write_outputs(gate_record, root / "out")
            self.assertFalse((root / "out" / HELPER.OUTPUT_NAME).exists())

    def test_rejects_safe_to_control_true_before_output(self) -> None:
        """gate record 若把 safe_to_control 写成 true，bounded plan 必须拒绝生成。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            gate_record = self.write_gate_fixture(root)
            payload = json.loads(gate_record.read_text(encoding="utf-8"))
            payload["safe_to_control"] = True
            gate_record.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

            with self.assertRaises(HELPER.PlanInputError):
                HELPER.write_outputs(gate_record, root / "out")
            self.assertFalse((root / "out" / HELPER.OUTPUT_NAME).exists())


if __name__ == "__main__":
    unittest.main()
