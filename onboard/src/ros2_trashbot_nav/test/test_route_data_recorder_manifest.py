import importlib
import csv
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
BEHAVIOR_ROOT = PACKAGE_ROOT.parent / "ros2_trashbot_behavior"
sys.path.insert(0, str(PACKAGE_ROOT))
sys.path.insert(0, str(BEHAVIOR_ROOT))


def install_route_recorder_stubs():
    modules = {
        "cv2": types.SimpleNamespace(imwrite=lambda *_args: True),
        "cv_bridge": types.SimpleNamespace(CvBridge=lambda: object(), CvBridgeError=Exception),
        "rclpy": types.SimpleNamespace(init=lambda args=None: None, spin=lambda node: None, shutdown=lambda: None),
        "rclpy.node": types.SimpleNamespace(Node=object),
        "nav_msgs": types.ModuleType("nav_msgs"),
        "nav_msgs.msg": types.SimpleNamespace(Odometry=object),
        "sensor_msgs": types.ModuleType("sensor_msgs"),
        "sensor_msgs.msg": types.SimpleNamespace(Image=object),
    }
    sys.modules.update(modules)


class RouteDataRecorderManifestTest(unittest.TestCase):
    def setUp(self):
        install_route_recorder_stubs()
        sys.modules.pop("ros2_trashbot_nav.route_data_recorder", None)
        self.module = importlib.import_module("ros2_trashbot_nav.route_data_recorder")

    def test_route_keyframe_payload_matches_vision_sample_contract(self):
        with tempfile.TemporaryDirectory() as td:
            output_dir = Path(td)
            json_path = output_dir / "keyframes" / "000.json"
            frame_path = output_dir / "keyframes" / "000.jpg"

            payload = self.module.build_route_keyframe_sample_payload(
                sample_id="route_keyframe_000",
                output_dir=str(output_dir),
                json_path=str(json_path),
                frame_path=str(frame_path),
                stamp=123.25,
                frame_id="map",
                route_id="trash_station_route",
                checkpoint_id="0",
                pose={"x": 1.0, "y": 2.0, "z": 0.0, "qx": 0.0, "qy": 0.0, "qz": 0.0, "qw": 1.0},
            )

        self.assertEqual(payload["sample_ref"], "vision_sample://keyframes/000.json")
        self.assertEqual(payload["raw_image"], "keyframes/000.jpg")
        self.assertEqual(payload["detector"], "route_data_recorder")
        self.assertEqual(payload["context"]["event_type"], "route_keyframe")
        self.assertEqual(payload["context"]["route_id"], "trash_station_route")
        self.assertEqual(payload["context"]["checkpoint_id"], "0")
        self.assertEqual(payload["detections"], [])
        self.assertEqual(payload["route_pose"]["x"], 1.0)

    def test_route_recorder_declares_manifest_parameters(self):
        source = (PACKAGE_ROOT / "ros2_trashbot_nav" / "route_data_recorder.py").read_text(encoding="utf-8")

        for parameter in (
            "'route_id'",
            "'sample_manifest_name'",
            "'sample_manifest_max_entries'",
            "'trashbot.vision_samples.v1'",
            "'event_type': 'route_keyframe'",
            "os.replace",
        ):
            self.assertIn(parameter, source)

    def test_manifest_append_is_bounded_and_diagnostics_compatible(self):
        with tempfile.TemporaryDirectory() as td:
            output_dir = Path(td)
            manifest_path = output_dir / "manifest.json"
            first = {
                "sample_id": "route_keyframe_000",
                "sample_ref": "vision_sample://keyframes/000.json",
                "timestamp": 1.0,
                "frame_id": "map",
                "raw_image": "keyframes/000.jpg",
                "annotated_image": "",
                "context": {"event_type": "route_keyframe", "route_id": "a", "checkpoint_id": "0"},
            }
            second = dict(first, sample_id="route_keyframe_001", sample_ref="vision_sample://keyframes/001.json")

            self.module.append_vision_sample_manifest(
                manifest_path=str(manifest_path),
                output_dir=str(output_dir),
                entry=self.module.route_keyframe_manifest_entry(first),
                max_entries=1,
            )
            self.module.append_vision_sample_manifest(
                manifest_path=str(manifest_path),
                output_dir=str(output_dir),
                entry=self.module.route_keyframe_manifest_entry(second),
                max_entries=1,
            )

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            from ros2_trashbot_behavior.operator_gateway_diagnostics import summarize_vision_manifest

            summary = summarize_vision_manifest(str(manifest_path))

            self.assertEqual(manifest["schema"], "trashbot.vision_samples.v1")
            self.assertEqual(len(manifest["samples"]), 1)
            latest = manifest["samples"][0]
            self.assertEqual(latest["sample_id"], "route_keyframe_001")
            self.assertEqual(latest["json"], "keyframes/001.json")
            self.assertEqual(latest["detection_count"], 0)
            self.assertEqual(latest["max_confidence"], 0)
            self.assertEqual(latest["context"]["event_type"], "route_keyframe")
            self.assertEqual(summary["schema"], "trashbot.vision_samples.v1")
            self.assertEqual(summary["sample_count"], 1)
            self.assertEqual(summary["latest_sample_ref"], "vision_sample://keyframes/001.json")
            self.assertEqual(summary["latest_context"]["event_type"], "route_keyframe")
            self.assertEqual(summary["latest_detection_count"], 0)

    def test_manifest_append_rebuilds_corrupt_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            output_dir = Path(td)
            manifest_path = output_dir / "manifest.json"
            manifest_path.write_text("{not-json", encoding="utf-8")
            entry = {
                "sample_id": "route_keyframe_000",
                "sample_ref": "vision_sample://keyframes/000.json",
                "timestamp": 1.0,
                "frame_id": "map",
                "raw_image": "keyframes/000.jpg",
                "annotated_image": "",
                "json": "keyframes/000.json",
                "context": {"event_type": "route_keyframe", "route_id": "a", "checkpoint_id": "0"},
                "detection_count": 0,
                "max_confidence": 0,
            }

            self.module.append_vision_sample_manifest(
                manifest_path=str(manifest_path),
                output_dir=str(output_dir),
                entry=entry,
                max_entries=10,
            )

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(manifest["schema"], "trashbot.vision_samples.v1")
        self.assertEqual(manifest["samples"], [entry])

    def test_fake_callbacks_write_route_keyframe_json_and_manifest(self):
        written_frames = []

        def fake_imwrite(path, frame):
            written_frames.append((Path(path), frame))
            Path(path).write_bytes(b"fake-jpeg")
            return True

        class FakeBridge:
            def imgmsg_to_cv2(self, msg, desired_encoding="bgr8"):
                self.encoding = desired_encoding
                return {"encoding": desired_encoding, "data": msg.data}

        class FakeLogger:
            def __init__(self):
                self.messages = []

            def info(self, message):
                self.messages.append(("info", message))

            def warn(self, message):
                self.messages.append(("warn", message))

        def fake_odom(sec=12, nanosec=345000000, x=1.25, y=2.5, z=0.0):
            return types.SimpleNamespace(
                header=types.SimpleNamespace(stamp=types.SimpleNamespace(sec=sec, nanosec=nanosec)),
                pose=types.SimpleNamespace(
                    pose=types.SimpleNamespace(
                        position=types.SimpleNamespace(x=x, y=y, z=z),
                        orientation=types.SimpleNamespace(x=0.0, y=0.0, z=0.707, w=0.707),
                    )
                ),
            )

        with tempfile.TemporaryDirectory() as td:
            output_dir = Path(td)
            keyframe_dir = output_dir / "keyframes"
            keyframe_dir.mkdir()
            route_csv = output_dir / "route.csv"

            recorder = self.module.RouteDataRecorder.__new__(self.module.RouteDataRecorder)
            recorder.output_dir = str(output_dir)
            recorder.keyframe_dir = str(keyframe_dir)
            recorder.route_csv = str(route_csv)
            recorder.min_distance_m = 0.8
            recorder.route_frame_id = "map"
            recorder.route_id = "runtime_fake_route"
            recorder.sample_manifest_name = "manifest.json"
            recorder.sample_manifest_max_entries = 10
            recorder.bridge = FakeBridge()
            recorder.latest_frame = None
            recorder.last_x = None
            recorder.last_y = None
            recorder.index = 0
            recorder.csv_file = open(route_csv, "w", newline="", encoding="utf-8")
            recorder.writer = csv.writer(recorder.csv_file)
            recorder.writer.writerow(["index", "sec", "nanosec", "frame_id", "x", "y", "z", "qx", "qy", "qz", "qw", "frame"])
            logger = FakeLogger()
            recorder.get_logger = lambda: logger

            self.module.cv2.imwrite = fake_imwrite

            try:
                recorder._on_image(types.SimpleNamespace(data=b"raw-image"))
                recorder._on_odom(fake_odom())
            finally:
                recorder.csv_file.close()

            keyframe_path = keyframe_dir / "000.jpg"
            json_path = keyframe_dir / "000.json"
            manifest_path = output_dir / "manifest.json"

            with route_csv.open("r", encoding="utf-8") as f:
                route_rows = list(csv.DictReader(f))
            keyframe_payload = json.loads(json_path.read_text(encoding="utf-8"))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            keyframe_bytes = keyframe_path.read_bytes()

        self.assertEqual(len(route_rows), 1)
        self.assertEqual(route_rows[0]["index"], "0")
        self.assertEqual(route_rows[0]["sec"], "12")
        self.assertEqual(route_rows[0]["nanosec"], "345000000")
        self.assertEqual(route_rows[0]["frame_id"], "map")
        self.assertEqual(route_rows[0]["x"], "1.25")
        self.assertEqual(route_rows[0]["y"], "2.5")
        self.assertEqual(route_rows[0]["qz"], "0.707")
        self.assertEqual(route_rows[0]["qw"], "0.707")
        self.assertEqual(route_rows[0]["frame"], "000.jpg")
        self.assertEqual(written_frames, [(keyframe_path, {"encoding": "bgr8", "data": b"raw-image"})])
        self.assertEqual(keyframe_bytes, b"fake-jpeg")
        self.assertEqual(keyframe_payload["sample_id"], "route_keyframe_000")
        self.assertEqual(keyframe_payload["sample_ref"], "vision_sample://keyframes/000.json")
        self.assertEqual(keyframe_payload["timestamp"], 12.345)
        self.assertEqual(keyframe_payload["raw_image"], "keyframes/000.jpg")
        self.assertEqual(keyframe_payload["context"]["route_id"], "runtime_fake_route")
        self.assertEqual(keyframe_payload["context"]["checkpoint_id"], "0")
        self.assertEqual(keyframe_payload["route_pose"]["x"], 1.25)
        self.assertEqual(manifest["schema"], "trashbot.vision_samples.v1")
        self.assertEqual(len(manifest["samples"]), 1)
        self.assertEqual(manifest["samples"][0]["sample_ref"], "vision_sample://keyframes/000.json")
        self.assertEqual(manifest["samples"][0]["json"], "keyframes/000.json")
        self.assertEqual(manifest["samples"][0]["context"]["event_type"], "route_keyframe")
        self.assertEqual(manifest["samples"][0]["detection_count"], 0)
        self.assertEqual(manifest["samples"][0]["max_confidence"], 0)
        self.assertEqual(recorder.index, 1)
        self.assertEqual((recorder.last_x, recorder.last_y), (1.25, 2.5))
        self.assertEqual(logger.messages[-1], ("info", "Saved waypoint #1 at (1.25, 2.50)"))


if __name__ == "__main__":
    unittest.main()
