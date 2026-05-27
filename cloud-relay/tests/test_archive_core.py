import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "cloud-relay" / "src"))
sys.path.insert(0, str(REPO_ROOT / "onboard" / "src" / "ros2_trashbot_behavior"))
sys.path.insert(0, str(REPO_ROOT / "onboard" / "src" / "ros2_trashbot_nav"))

from ros2_trashbot_cloud_relay.archive_core import (
    ANNOTATION_SCHEMA,
    ARCHIVE_SCHEMA,
    INFERENCE_SCHEMA,
    ArchiveStore,
    archive_state_path,
    install_o6_archive_routes,
)
from ros2_trashbot_nav.algorithm_evidence_feed import build_offline_algorithm_archive
from ros2_trashbot_behavior.archive_event_publisher import task_record_to_archive_events
import ros2_trashbot_behavior.remote_cloud_relay as behavior_relay


class mock_env_without_o6_state:
    """临时移除 O6/remote state env，专门验证默认路径不会污染仓库根。"""

    def __enter__(self):
        self.previous_o6 = os.environ.pop("TRASHBOT_O6_ARCHIVE_STATE", None)
        self.previous_remote = os.environ.pop("TRASHBOT_REMOTE_CLOUD_STATE", None)
        return self

    def __exit__(self, exc_type, exc, tb):
        # 还原环境变量，避免同一 unittest 进程里影响后续 HTTP route 测试。
        if self.previous_o6 is not None:
            os.environ["TRASHBOT_O6_ARCHIVE_STATE"] = self.previous_o6
        if self.previous_remote is not None:
            os.environ["TRASHBOT_REMOTE_CLOUD_STATE"] = self.previous_remote
        return False


class ArchiveStoreTest(unittest.TestCase):
    def test_default_archive_state_path_uses_tmp_not_repo_root(self):
        with mock_env_without_o6_state():
            path = Path(archive_state_path())

        # 默认路径必须脱离仓库根，避免 smoke/test 在源码目录生成 runtime state。
        self.assertEqual(path.name, "o6_cloud_archive_state.json")
        self.assertNotEqual(path.parent, REPO_ROOT)
        self.assertTrue(str(path).startswith(tempfile.gettempdir()))

    def test_task_event_annotation_and_inference_are_persisted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ArchiveStore(f"{tmpdir}/archive.json")

            # 先建 task，后续事件、标注和推理都通过 robot_id/task_id 归并到详情。
            task = store.create_task(
                {
                    "robot_id": "robot-a",
                    "task_id": "task-1",
                    "date": "2026-05-27",
                    "evidence_ref": {"uri": "oss://bytegallop/rober/robot-a/2026-05-27/task-1/frame.jpg"},
                }
            )
            self.assertEqual(task["task"]["schema"], ARCHIVE_SCHEMA)
            self.assertIn("not_proven_production_db", task["not_proven"])

            # 事件只保存 evidence_ref，不把图片大对象写入本地 JSON store。
            event = store.create_event(
                {
                    "robot_id": "robot-a",
                    "task_id": "task-1",
                    "event_type": "route_frame",
                    "evidence_ref": "oss://bytegallop/rober/robot-a/2026-05-27/task-1/frame-001.jpg",
                    "payload": {"x_m": 1.0, "y_m": 2.0},
                }
            )
            self.assertEqual(event["event"]["event_type"], "route_frame")

            annotation = store.create_annotation(
                {
                    "robot_id": "robot-a",
                    "task_id": "task-1",
                    "item_id": "frame-001",
                    "label_type": "elevator_door",
                    "label_value": "open",
                }
            )
            self.assertEqual(annotation["annotation"]["schema"], ANNOTATION_SCHEMA)

            inference = store.create_inference(
                {
                    "robot_id": "robot-a",
                    "task_id": "task-1",
                    "inference_type": "elevator_door_state",
                    "result": {"state": "open", "confidence": 0.72},
                }
            )
            self.assertEqual(inference["inference"]["schema"], INFERENCE_SCHEMA)

            status, detail = store.get_task("robot-a", "task-1")
            self.assertEqual(status, 200)
            self.assertEqual(len(detail["events"]), 2)
            self.assertEqual(len(detail["annotations"]), 1)
            self.assertEqual(len(detail["inferences"]), 1)

    def test_board_publisher_and_algorithm_feed_are_archive_store_compatible(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ArchiveStore(f"{tmpdir}/archive.json")
            task_record = {
                "task_id": "compat-task",
                "final_status": "failed",
                "final_state": "error",
                "error_code": "mock_route_failed",
                "evidence_ref": "mock://board/task-record.json",
                "route_progress": {
                    "checkpoint": "cp-1",
                    "evidence_ref": "mock://board/route-frame.json",
                    "source": "software_proof",
                },
                "detection_snapshot_refs": ["mock://board/detection.jpg"],
            }
            board_events = task_record_to_archive_events(task_record, robot_id="robot-o6")
            algorithm_archive = build_offline_algorithm_archive(robot_id="robot-o6", task_id="compat-task")

            store.create_task(algorithm_archive["tasks"][0])
            # board publisher 与 algorithm feed 都走同一个 cloud event schema 入库。
            for event in board_events + algorithm_archive["events"]:
                store.create_event(event)
            for annotation in algorithm_archive["annotations"]:
                store.create_annotation(annotation)
            for inference in algorithm_archive["inferences"]:
                store.create_inference(inference)

            status, detail = store.get_task("robot-o6", "compat-task")

        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(detail["events"]), len(board_events) + len(algorithm_archive["events"]))
        self.assertEqual(len(detail["annotations"]), len(algorithm_archive["annotations"]))
        self.assertEqual(len(detail["inferences"]), len(algorithm_archive["inferences"]))
        self.assertEqual(detail["task"]["schema"], ARCHIVE_SCHEMA)
        for event in detail["events"]:
            self.assertEqual(event["schema"], ARCHIVE_SCHEMA)
            self.assertEqual(event["source"], "software_proof")
            self.assertEqual(event["proof_status"], "not_proven")


class O6HttpRoutePatchTest(unittest.TestCase):
    def test_o6_routes_require_bearer_and_leave_remote_routes_available(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            previous_archive_state = os.environ.get("TRASHBOT_O6_ARCHIVE_STATE")
            os.environ["TRASHBOT_O6_ARCHIVE_STATE"] = f"{tmpdir}/o6_archive.json"
            install_o6_archive_routes(behavior_relay)
            server = behavior_relay.build_server(
                "127.0.0.1",
                0,
                f"{tmpdir}/remote.json",
                "token-a",
                state_backend="file",
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_port}"
            try:
                # 未授权的 O6 写入必须拒绝，避免 PC/手机绕过云端 bearer gate。
                request = urllib.request.Request(
                    f"{base_url}/api/o6/archive/tasks",
                    data=json.dumps({"robot_id": "robot-a", "task_id": "task-1"}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with self.assertRaises(urllib.error.HTTPError) as exc:
                    urllib.request.urlopen(request, timeout=5)
                self.assertEqual(exc.exception.code, 401)

                # 带 bearer 后 O6 task archive 可写入，并且 remote.v1 healthz 仍保持可用。
                authed = urllib.request.Request(
                    f"{base_url}/api/o6/archive/tasks",
                    data=json.dumps({"robot_id": "robot-a", "task_id": "task-1"}).encode("utf-8"),
                    headers={"Content-Type": "application/json", "Authorization": "Bearer token-a"},
                    method="POST",
                )
                payload = json.loads(urllib.request.urlopen(authed, timeout=5).read().decode("utf-8"))
                self.assertEqual(payload["task"]["schema"], ARCHIVE_SCHEMA)
                self.assertFalse(payload["production_db_connected"])

                health = json.loads(urllib.request.urlopen(f"{base_url}/healthz", timeout=5).read().decode("utf-8"))
                self.assertEqual(health["protocol_version"], "trashbot.remote.v1")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                if previous_archive_state is None:
                    os.environ.pop("TRASHBOT_O6_ARCHIVE_STATE", None)
                else:
                    os.environ["TRASHBOT_O6_ARCHIVE_STATE"] = previous_archive_state


if __name__ == "__main__":
    unittest.main()
