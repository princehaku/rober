"""O3 same-window route readiness precheck 的 strict no-motion 离线单测。"""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "o3_same_window_route_readiness_precheck.py"
SPEC = importlib.util.spec_from_file_location("o3_same_window_route_readiness_precheck", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
HELPER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HELPER)


def false_fields() -> dict[str, bool]:
    """统一构造所有安全字段；测试只允许显式布尔 false。"""
    return {field: False for field in HELPER.SAFETY_FALSE_FIELDS}


def base_gate_record() -> dict:
    """07:07 gate fixture：packet 已校验，但 route execution 仍 fail closed。"""
    fields = false_fields()
    return {
        **fields,
        "schema": HELPER.GATE_RECORD_SCHEMA,
        "controlled_route_execution_gate_status": HELPER.SOURCE_GATE_STATUS,
        "proof_boundary": "software_proof_o3_o1_fail_closed_controlled_route_execution_gate_record_only",
        "packet_id": HELPER.EXPECTED_PACKET_ID,
        "task_id": HELPER.EXPECTED_TASK_ID,
        "route_intent_id": HELPER.EXPECTED_ROUTE_INTENT_ID,
        "route_csv_row_count": HELPER.EXPECTED_ROUTE_ROW_COUNT,
        "replay_jsonl_event_count": HELPER.EXPECTED_ROUTE_ROW_COUNT,
        "packet_jsonl_event_count": HELPER.EXPECTED_ROUTE_ROW_COUNT,
        "path_structured_pose_count": HELPER.EXPECTED_ROUTE_ROW_COUNT,
        "identity_validation_status": "pass_exact_same_task_identity",
        "count_validation_status": "pass_exact_28_28_28",
        "source_hash_validation_status": "pass_exact_source_hashes",
        "fixed_false_fields": fields,
        "no_motion_control_guard": list(HELPER.NO_MOTION_GUARDS),
    }


def base_bounded_plan() -> dict:
    """08:09 bounded plan fixture：27 段计划存在，但仍 blocked_pending_live_safety_gate。"""
    fields = false_fields()
    return {
        **fields,
        "schema": HELPER.BOUNDED_PLAN_SCHEMA,
        "execution_plan_status": HELPER.SOURCE_PLAN_STATUS,
        "proof_boundary": "software_proof_o3_o1_no_motion_bounded_route_command_plan_only",
        "packet_id": HELPER.EXPECTED_PACKET_ID,
        "task_id": HELPER.EXPECTED_TASK_ID,
        "route_intent_id": HELPER.EXPECTED_ROUTE_INTENT_ID,
        "route_csv_row_count": HELPER.EXPECTED_ROUTE_ROW_COUNT,
        "replay_jsonl_event_count": HELPER.EXPECTED_ROUTE_ROW_COUNT,
        "packet_jsonl_event_count": HELPER.EXPECTED_ROUTE_ROW_COUNT,
        "path_structured_pose_count": HELPER.EXPECTED_ROUTE_ROW_COUNT,
        "segment_count": HELPER.EXPECTED_SEGMENT_COUNT,
        "bounded_segment_plan": [{"segment_index": index} for index in range(HELPER.EXPECTED_SEGMENT_COUNT)],
        "fixed_false_fields": fields,
        "no_motion_control_guard": list(HELPER.NO_MOTION_GUARDS),
    }


def base_mock_summary() -> dict:
    """23:23 mock summary fixture：mock completed 只能说明离线 progress 写出成功。"""
    fields = false_fields()
    return {
        **fields,
        "schema": HELPER.MOCK_SUMMARY_SCHEMA,
        "mock_execution_status": HELPER.SOURCE_MOCK_STATUS,
        "proof_boundary": "software_proof_o3_o1_bounded_route_mock_execution_only",
        "packet_id": HELPER.EXPECTED_PACKET_ID,
        "task_id": HELPER.EXPECTED_TASK_ID,
        "route_intent_id": HELPER.EXPECTED_ROUTE_INTENT_ID,
        "route_csv_row_count": HELPER.EXPECTED_ROUTE_ROW_COUNT,
        "replay_jsonl_event_count": HELPER.EXPECTED_ROUTE_ROW_COUNT,
        "packet_jsonl_event_count": HELPER.EXPECTED_ROUTE_ROW_COUNT,
        "path_structured_pose_count": HELPER.EXPECTED_ROUTE_ROW_COUNT,
        "segment_count": HELPER.EXPECTED_SEGMENT_COUNT,
        "mock_segment_progress_count": HELPER.EXPECTED_SEGMENT_COUNT,
        "progress_jsonl_event_count": HELPER.EXPECTED_SEGMENT_COUNT,
        "mock_total_distance_m": 0.723849,
        "mock_total_elapsed_s": 7.238,
        "fixed_false_fields": fields,
        "no_motion_control_guard": list(HELPER.NO_MOTION_GUARDS),
    }


def base_progress_events(count: int = HELPER.EXPECTED_SEGMENT_COUNT) -> list[dict]:
    """构造 mock_segment_completed_not_live_control events，不包含任何控制调用。"""
    events: list[dict] = []
    for index in range(count):
        events.append(
            {
                **false_fields(),
                "schema": HELPER.PROGRESS_SCHEMA,
                "event_type": "mock_segment_completed_not_live_control",
                "proof_boundary": "software_proof_o3_o1_bounded_route_mock_execution_only",
                "packet_id": HELPER.EXPECTED_PACKET_ID,
                "task_id": HELPER.EXPECTED_TASK_ID,
                "route_intent_id": HELPER.EXPECTED_ROUTE_INTENT_ID,
                "segment_index": index,
                "from_order": index,
                "to_order": index + 1,
            }
        )
    return events


class O3SameWindowRouteReadinessPrecheckTests(unittest.TestCase):
    """验证 precheck 只收敛 readiness blocker，不产生 live-control claim。"""

    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        """写入 source JSON fixture，模拟 CLI 消费既有 sprint artifact。"""
        path = root / name
        path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        return path

    def write_jsonl(self, root: Path, name: str, payloads: list[dict]) -> Path:
        """写入 progress JSONL fixture，保持一行一个 mock progress event。"""
        path = root / name
        path.write_text("".join(json.dumps(item, sort_keys=True) + "\n" for item in payloads), encoding="utf-8")
        return path

    def write_valid_sources(self, root: Path) -> tuple[Path, Path, Path, Path]:
        """生成一组完整有效 source，便于每个 drift 测试只改一个字段。"""
        return (
            self.write_json(root, "controlled_route_execution_gate_record.json", base_gate_record()),
            self.write_json(root, "bounded_route_command_plan.json", base_bounded_plan()),
            self.write_json(root, "bounded_route_mock_execution_summary.json", base_mock_summary()),
            self.write_jsonl(root, "bounded_route_mock_execution_progress.jsonl", base_progress_events()),
        )

    def test_writes_blocked_precheck_summary(self) -> None:
        """有效 source 会写 blocked summary，且 all live-control fields 仍 false。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            gate_path, plan_path, mock_summary_path, progress_path = self.write_valid_sources(root)

            summary = HELPER.write_outputs(
                gate_path,
                plan_path,
                mock_summary_path,
                progress_path,
                root / "out",
                generated_at_utc="2026-07-14T05:38:00Z",
            )

            self.assertTrue((root / "out" / HELPER.SUMMARY_OUTPUT_NAME).exists())
            self.assertEqual(HELPER.SUMMARY_SCHEMA, summary["schema"])
            self.assertEqual(HELPER.READINESS_STATUS, summary["same_window_route_readiness_status"])
            self.assertEqual(HELPER.PROOF_BOUNDARY, summary["proof_boundary"])
            self.assertEqual(HELPER.EXPECTED_PACKET_ID, summary["packet_id"])
            self.assertEqual(HELPER.EXPECTED_TASK_ID, summary["task_id"])
            self.assertEqual(HELPER.EXPECTED_ROUTE_INTENT_ID, summary["route_intent_id"])
            self.assertEqual(HELPER.EXPECTED_ROUTE_ROW_COUNT, summary["route_csv_row_count"])
            self.assertEqual(HELPER.EXPECTED_SEGMENT_COUNT, summary["segment_count"])
            self.assertFalse(summary["next_live_capture_allowed"])
            self.assertEqual(list(HELPER.MISSING_EVIDENCE), summary["missing_evidence"])
            self.assertIn("same_window_route_readiness_precheck", summary["rg_acceptance_anchors"])
            self.assertIn("route_execution_success=false", summary["rg_acceptance_anchors"])
            self.assertIn("no /cmd_vel", summary["no_motion_control_guard"])
            self.assertEqual(4, len(summary["source_artifacts"]))
            for key in HELPER.SAFETY_FALSE_FIELDS:
                self.assertFalse(summary[key], key)
                self.assertFalse(summary["fixed_false_fields"][key], key)

    def test_rejects_identity_drift_before_output(self) -> None:
        """任一 source 改成别的 packet_id 时必须 fail closed，不写 summary。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            gate_path, plan_path, mock_summary_path, progress_path = self.write_valid_sources(root)
            payload = base_mock_summary()
            payload["packet_id"] = "packet_wrong"
            mock_summary_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

            with self.assertRaises(HELPER.ReadinessPrecheckInputError):
                HELPER.write_outputs(gate_path, plan_path, mock_summary_path, progress_path, root / "out")
            self.assertFalse((root / "out" / HELPER.SUMMARY_OUTPUT_NAME).exists())

    def test_rejects_missing_no_motion_guard_before_output(self) -> None:
        """缺少 no NavigateToPose 或 no WAVE ROVER UART 等 literal 时不能通过。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            gate_path, plan_path, mock_summary_path, progress_path = self.write_valid_sources(root)
            payload = base_bounded_plan()
            payload["no_motion_control_guard"] = ["no /cmd_vel", "no /api/base/manual"]
            plan_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

            with self.assertRaises(HELPER.ReadinessPrecheckInputError):
                HELPER.write_outputs(gate_path, plan_path, mock_summary_path, progress_path, root / "out")
            self.assertFalse((root / "out" / HELPER.SUMMARY_OUTPUT_NAME).exists())

    def test_rejects_progress_true_safety_field_before_output(self) -> None:
        """progress event 中任何 route_execution_success=true 都不能被 readiness summary 吸收。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            gate_path, plan_path, mock_summary_path, progress_path = self.write_valid_sources(root)
            events = base_progress_events()
            events[2]["route_execution_success"] = True
            self.write_jsonl(root, progress_path.name, events)

            with self.assertRaises(HELPER.ReadinessPrecheckInputError):
                HELPER.write_outputs(gate_path, plan_path, mock_summary_path, progress_path, root / "out")
            self.assertFalse((root / "out" / HELPER.SUMMARY_OUTPUT_NAME).exists())

    def test_rejects_progress_count_drift_before_output(self) -> None:
        """progress JSONL 必须正好 27 行；少一段不能生成 readiness precheck。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            gate_path, plan_path, mock_summary_path, progress_path = self.write_valid_sources(root)
            self.write_jsonl(root, progress_path.name, base_progress_events(count=HELPER.EXPECTED_SEGMENT_COUNT - 1))

            with self.assertRaises(HELPER.ReadinessPrecheckInputError):
                HELPER.write_outputs(gate_path, plan_path, mock_summary_path, progress_path, root / "out")
            self.assertFalse((root / "out" / HELPER.SUMMARY_OUTPUT_NAME).exists())


if __name__ == "__main__":
    unittest.main()
