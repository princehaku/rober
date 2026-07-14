"""O3 28-pose same-task replay packet 的离线单测。"""

from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "o3_28_pose_same_task_replay_packet.py"
SPEC = importlib.util.spec_from_file_location("o3_28_pose_same_task_replay_packet", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
HELPER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HELPER)


def pose_rows() -> list[dict]:
    """构造 28 个 pose，模拟 04:02 route_csv 与 replay_jsonl 的共同来源。"""
    rows = []
    for index in range(28):
        rows.append(
            {
                "order": index,
                "source_index": index,
                "frame_id": "map",
                "stamp": {"sec": 1783883494, "nanosec": 997523160},
                "position": {"x": 0.1 + index * 0.025, "y": 0.25, "z": 0.0},
                "orientation": {"qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0},
                "primary_source_artifact": "sprints/source/live_full_structured_path_capture_summary.json",
            }
        )
    return rows


def source_summary(route_csv: Path, replay_jsonl: Path) -> dict:
    """构造最小 04:02 accepted summary，锁定 same-task 输入身份。"""
    false_fields = {
        "route_execution_success": False,
        "delivery_success": False,
        "hil_pass": False,
        "safe_to_control": False,
        "robot_control_executed": False,
        "publishes_cmd_vel": False,
        "calls_base_manual": False,
        "uses_base_uart": False,
    }
    return {
        **false_fields,
        "schema": HELPER.SOURCE_SUMMARY_SCHEMA,
        "route_intent_id": HELPER.EXPECTED_ROUTE_INTENT_ID,
        "task_id": HELPER.EXPECTED_TASK_ID,
        "fresh_28_pose_structured_material_consumed": True,
        "historic_21_57_artifact_primary_source": False,
        "path_structured_pose_count": 28,
        "validation_status": "pass_fresh_28_pose_structured_material",
        "material_shape": {
            "csv_material_row_count": 28,
            "replay_event_count": 28,
        },
        "route_material_refs": {
            "route_csv_ref": route_csv.as_posix(),
            "route_replay_jsonl_ref": replay_jsonl.as_posix(),
        },
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    """写测试 route_csv，保持和 04:02 artifact 相同的扁平字段。"""
    fieldnames = list(HELPER.CSV_REQUIRED_FIELDS)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for pose in rows:
            writer.writerow(
                {
                    "schema": HELPER.SOURCE_ROUTE_CSV_SCHEMA,
                    "route_intent_id": HELPER.EXPECTED_ROUTE_INTENT_ID,
                    "task_id": HELPER.EXPECTED_TASK_ID,
                    "order": pose["order"],
                    "source_index": pose["source_index"],
                    "frame_id": pose["frame_id"],
                    "stamp_sec": pose["stamp"]["sec"],
                    "stamp_nanosec": pose["stamp"]["nanosec"],
                    "x": pose["position"]["x"],
                    "y": pose["position"]["y"],
                    "z": pose["position"]["z"],
                    "qx": pose["orientation"]["qx"],
                    "qy": pose["orientation"]["qy"],
                    "qz": pose["orientation"]["qz"],
                    "qw": pose["orientation"]["qw"],
                    "primary_source_artifact": pose["primary_source_artifact"],
                    "strict_no_motion": True,
                }
            )


def write_jsonl(path: Path, rows: list[dict]) -> None:
    """写测试 replay_jsonl，一行一个 structured_pose event。"""
    with path.open("w", encoding="utf-8") as handle:
        for pose in rows:
            handle.write(
                json.dumps(
                    {
                        "schema": HELPER.SOURCE_REPLAY_SCHEMA,
                        "event": "structured_pose",
                        "route_intent_id": HELPER.EXPECTED_ROUTE_INTENT_ID,
                        "task_id": HELPER.EXPECTED_TASK_ID,
                        "order": pose["order"],
                        "source_index": pose["source_index"],
                        "frame_id": pose["frame_id"],
                        "stamp": pose["stamp"],
                        "position": pose["position"],
                        "orientation": pose["orientation"],
                        "primary_source_artifact": pose["primary_source_artifact"],
                        "strict_no_motion": True,
                        "route_execution_success": False,
                    },
                    sort_keys=True,
                )
            )
            handle.write("\n")


class O328PoseSameTaskReplayPacketTests(unittest.TestCase):
    """只验证 offline packet 读写，不启动 ROS2 或任何控制路径。"""

    def write_materials(self, root: Path) -> tuple[Path, Path, Path]:
        """生成 summary/CSV/JSONL 三份输入，确保测试真的覆盖三方读取。"""
        route_csv = root / "fixed_route_28_pose_route.csv"
        replay_jsonl = root / "fixed_route_28_pose_replay.jsonl"
        summary = root / "fixed_route_28_pose_consumer_summary.json"
        rows = pose_rows()
        write_csv(route_csv, rows)
        write_jsonl(replay_jsonl, rows)
        summary.write_text(json.dumps(source_summary(route_csv, replay_jsonl)), encoding="utf-8")
        return summary, route_csv, replay_jsonl

    def test_writes_same_task_packet_from_summary_csv_and_jsonl(self) -> None:
        """有效输入会输出 28 event packet 和 false safety summary。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            summary_path, route_csv, replay_jsonl = self.write_materials(root)
            output_dir = root / "out"

            summary = HELPER.write_outputs(
                summary_path,
                route_csv,
                replay_jsonl,
                output_dir,
                "2026-07-12T21:02:00Z",
            )

            self.assertEqual(HELPER.SUMMARY_SCHEMA, summary["schema"])
            self.assertEqual(HELPER.EXPECTED_TASK_ID, summary["task_id"])
            self.assertEqual(HELPER.EXPECTED_ROUTE_INTENT_ID, summary["route_intent_id"])
            self.assertEqual(28, summary["route_csv_row_count"])
            self.assertEqual(28, summary["replay_jsonl_event_count"])
            self.assertEqual(28, summary["path_structured_pose_count"])
            self.assertTrue(summary["same_task_identity_verified"])
            self.assertTrue(summary["same_task_replay_packet_ready"])
            for key in HELPER.SAFETY_FALSE_FIELDS:
                self.assertFalse(summary[key], key)

            events = [
                json.loads(line)
                for line in (output_dir / HELPER.PACKET_JSONL_NAME).read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(28, len(events))
            self.assertEqual(summary["packet_id"], events[0]["packet_id"])
            self.assertEqual(0, events[0]["source_index"])
            self.assertEqual(27, events[-1]["source_index"])
            self.assertFalse(events[-1]["uses_base_uart"])

    def test_rejects_replay_jsonl_identity_drift(self) -> None:
        """JSONL 的 route_intent_id 漂移时，不能只相信 summary 通过。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            summary_path, route_csv, replay_jsonl = self.write_materials(root)
            events = [json.loads(line) for line in replay_jsonl.read_text(encoding="utf-8").splitlines()]
            events[3]["route_intent_id"] = "wrong_route_intent"
            replay_jsonl.write_text("\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8")

            with self.assertRaises(HELPER.PacketInputError):
                HELPER.write_outputs(summary_path, route_csv, replay_jsonl, root / "out")

    def test_rejects_csv_jsonl_pose_mismatch(self) -> None:
        """CSV 坐标和 JSONL 坐标不一致时必须 fail closed。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            summary_path, route_csv, replay_jsonl = self.write_materials(root)
            with route_csv.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            rows[7]["x"] = "9.99"
            with route_csv.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(HELPER.CSV_REQUIRED_FIELDS))
                writer.writeheader()
                writer.writerows(rows)

            with self.assertRaises(HELPER.PacketInputError):
                HELPER.write_outputs(summary_path, route_csv, replay_jsonl, root / "out")

    def test_rejects_summary_safety_true(self) -> None:
        """summary safety 字段若变 true，packet 不能生成。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            summary_path, route_csv, replay_jsonl = self.write_materials(root)
            payload = json.loads(summary_path.read_text(encoding="utf-8"))
            payload["safe_to_control"] = True
            summary_path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaises(HELPER.PacketInputError):
                HELPER.write_outputs(summary_path, route_csv, replay_jsonl, root / "out")


if __name__ == "__main__":
    unittest.main()
