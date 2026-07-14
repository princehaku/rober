"""O3 controlled route execution gate record 的离线单测。"""

from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "o3_controlled_route_execution_gate_record.py"
SPEC = importlib.util.spec_from_file_location("o3_controlled_route_execution_gate_record", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
HELPER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HELPER)


def write_route_csv(path: Path) -> None:
    """写 28 行 route CSV；测试需要实际文件计数，而不是只伪造 summary 字段。"""
    fieldnames = ("order", "source_index", "frame_id", "x", "y", "z")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for index in range(HELPER.EXPECTED_POSE_COUNT):
            writer.writerow(
                {
                    "order": index,
                    "source_index": index,
                    "frame_id": "map",
                    "x": 0.1 + index * 0.01,
                    "y": 0.25,
                    "z": 0.0,
                }
            )


def write_jsonl(path: Path, event_name: str) -> None:
    """写 28 行 JSONL object；gate 只关心 source 行数和 hash，不复算 pose。"""
    with path.open("w", encoding="utf-8") as handle:
        for index in range(HELPER.EXPECTED_POSE_COUNT):
            handle.write(
                json.dumps(
                    {
                        "event": event_name,
                        "order": index,
                        "source_index": index,
                        "route_execution_success": False,
                        "safe_to_control": False,
                    },
                    sort_keys=True,
                )
            )
            handle.write("\n")


def base_packet_summary(root: Path, fingerprints: dict[str, str]) -> dict:
    """构造最小 05:02 packet summary，锁定 accepted identity 和 false safety fields。"""
    false_fields = {field: False for field in HELPER.SAFETY_FALSE_FIELDS}
    return {
        **false_fields,
        "schema": HELPER.PACKET_SUMMARY_SCHEMA,
        "packet_id": HELPER.EXPECTED_PACKET_ID,
        "task_id": HELPER.EXPECTED_TASK_ID,
        "route_intent_id": HELPER.EXPECTED_ROUTE_INTENT_ID,
        "same_task_identity_verified": True,
        "same_task_replay_packet_ready": True,
        "route_csv_row_count": HELPER.EXPECTED_POSE_COUNT,
        "replay_jsonl_event_count": HELPER.EXPECTED_POSE_COUNT,
        "path_structured_pose_count": HELPER.EXPECTED_POSE_COUNT,
        "source_fingerprints": fingerprints,
        "source_summary_ref": (root / "fixed_route_28_pose_consumer_summary.json").as_posix(),
        "route_csv_ref": (root / "fixed_route_28_pose_route.csv").as_posix(),
        "replay_jsonl_ref": (root / "fixed_route_28_pose_replay.jsonl").as_posix(),
        "packet_jsonl_ref": (root / "same_task_route_replay_packet.jsonl").as_posix(),
    }


class O3ControlledRouteExecutionGateRecordTests(unittest.TestCase):
    """验证 gate record 是 fail-closed artifact，不会被误读成控制执行。"""

    def write_materials(self, root: Path) -> tuple[Path, dict[str, str]]:
        """生成 packet summary 指向的四份本地材料，并返回 source hash 常量。"""
        source_summary = root / "fixed_route_28_pose_consumer_summary.json"
        route_csv = root / "fixed_route_28_pose_route.csv"
        replay_jsonl = root / "fixed_route_28_pose_replay.jsonl"
        packet_jsonl = root / "same_task_route_replay_packet.jsonl"
        source_summary.write_text(json.dumps({"schema": "source", "count": 28}, sort_keys=True) + "\n", encoding="utf-8")
        write_route_csv(route_csv)
        write_jsonl(replay_jsonl, "structured_pose")
        write_jsonl(packet_jsonl, "same_task_structured_pose_readback")
        fingerprints = {
            "summary_sha256": HELPER.sha256_file(source_summary),
            "route_csv_sha256": HELPER.sha256_file(route_csv),
            "replay_jsonl_sha256": HELPER.sha256_file(replay_jsonl),
        }
        packet_summary = root / "same_task_replay_packet_summary.json"
        packet_summary.write_text(json.dumps(base_packet_summary(root, fingerprints), sort_keys=True), encoding="utf-8")
        return packet_summary, fingerprints

    def test_writes_fail_closed_gate_record_from_valid_packet(self) -> None:
        """有效 05:02 packet 只生成 fail-closed gate，不解锁任何控制字段。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            packet_summary, fingerprints = self.write_materials(root)

            record = HELPER.write_outputs(
                packet_summary,
                root / "out",
                generated_at_utc="2026-07-12T23:07:00Z",
                expected_fingerprints=fingerprints,
            )

            self.assertEqual(HELPER.GATE_RECORD_SCHEMA, record["schema"])
            self.assertEqual(HELPER.EXPECTED_PACKET_ID, record["packet_id"])
            self.assertEqual("pass_exact_same_task_identity", record["identity_validation_status"])
            self.assertEqual("pass_exact_28_28_28", record["count_validation_status"])
            self.assertEqual("pass_exact_source_hashes", record["source_hash_validation_status"])
            self.assertEqual(
                "fail_closed_input_packet_validated",
                record["controlled_route_execution_gate_status"],
            )
            self.assertIn("no /cmd_vel", record["no_motion_control_guard"])
            self.assertIn("no /api/base/manual", record["no_motion_control_guard"])
            self.assertIn("no NavigateToPose", record["no_motion_control_guard"])
            self.assertIn("no WAVE ROVER UART", record["no_motion_control_guard"])
            for key in HELPER.SAFETY_FALSE_FIELDS:
                self.assertFalse(record[key], key)
                self.assertFalse(record["fixed_false_fields"][key], key)
            self.assertTrue((root / "out" / HELPER.OUTPUT_NAME).exists())

    def test_rejects_packet_identity_drift_before_output(self) -> None:
        """packet_id 漂移时必须 fail closed，不能输出类似 ready 的 gate。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            packet_summary, fingerprints = self.write_materials(root)
            payload = json.loads(packet_summary.read_text(encoding="utf-8"))
            payload["packet_id"] = "packet_wrong"
            packet_summary.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

            with self.assertRaises(HELPER.GateInputError):
                HELPER.write_outputs(packet_summary, root / "out", expected_fingerprints=fingerprints)
            self.assertFalse((root / "out" / HELPER.OUTPUT_NAME).exists())

    def test_rejects_source_hash_drift_before_output(self) -> None:
        """source 文件在 packet summary 之后被替换时，hash 校验必须拦截。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            packet_summary, fingerprints = self.write_materials(root)
            replay_jsonl = root / "fixed_route_28_pose_replay.jsonl"
            events = [json.loads(line) for line in replay_jsonl.read_text(encoding="utf-8").splitlines()]
            events[5]["event"] = "tampered_structured_pose"
            replay_jsonl.write_text(
                "\n".join(json.dumps(event, sort_keys=True) for event in events) + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(HELPER.GateInputError):
                HELPER.write_outputs(packet_summary, root / "out", expected_fingerprints=fingerprints)
            self.assertFalse((root / "out" / HELPER.OUTPUT_NAME).exists())

    def test_rejects_summary_safety_true_before_output(self) -> None:
        """05:02 summary 若把 safe_to_control 写成 true，gate 不能生成。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            packet_summary, fingerprints = self.write_materials(root)
            payload = json.loads(packet_summary.read_text(encoding="utf-8"))
            payload["safe_to_control"] = True
            packet_summary.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

            with self.assertRaises(HELPER.GateInputError):
                HELPER.write_outputs(packet_summary, root / "out", expected_fingerprints=fingerprints)
            self.assertFalse((root / "out" / HELPER.OUTPUT_NAME).exists())


if __name__ == "__main__":
    unittest.main()
