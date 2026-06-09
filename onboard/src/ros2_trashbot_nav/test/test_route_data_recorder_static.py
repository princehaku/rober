import csv
import importlib
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))


def build_fake_cv2():
    def convert_to_lists(image):
        return image.tolist() if hasattr(image, "tolist") else image

    def cvt_color(image, code):
        # 这里显式模拟常见编码到 BGR 的通道重排，确保 fallback 测试验证的是颜色契约，而不是只验证函数被调用。
        pixels = convert_to_lists(image)
        if code == fake_cv2.COLOR_RGB2BGR:
            return FakeArray([[[pixel[2], pixel[1], pixel[0]] for pixel in row] for row in pixels])
        if code == fake_cv2.COLOR_GRAY2BGR:
            return FakeArray([[[value, value, value] for value in row] for row in pixels])
        if code == fake_cv2.COLOR_BGRA2BGR:
            return FakeArray([[[pixel[0], pixel[1], pixel[2]] for pixel in row] for row in pixels])
        if code == fake_cv2.COLOR_RGBA2BGR:
            return FakeArray([[[pixel[2], pixel[1], pixel[0]] for pixel in row] for row in pixels])
        raise AssertionError(f"unexpected color code: {code}")

    fake_cv2 = types.SimpleNamespace(
        COLOR_RGB2BGR=1,
        COLOR_GRAY2BGR=2,
        COLOR_BGRA2BGR=3,
        COLOR_RGBA2BGR=4,
        imwrite=lambda *_args: True,
        cvtColor=cvt_color,
    )
    return fake_cv2


class FakeArray:
    def __init__(self, data):
        self._data = data
        self.size = len(self._flatten(data))

    def _flatten(self, value):
        if isinstance(value, list):
            result = []
            for item in value:
                result.extend(self._flatten(item))
            return result
        return [value]

    def reshape(self, shape):
        flat = self._flatten(self._data)
        total = 1
        for dim in shape:
            total *= dim
        if total != len(flat):
            raise ValueError(f"cannot reshape {len(flat)} values into {shape}")

        def build(offset, dims):
            if len(dims) == 1:
                end = offset + dims[0]
                return flat[offset:end], end
            values = []
            cursor = offset
            for _ in range(dims[0]):
                nested, cursor = build(cursor, dims[1:])
                values.append(nested)
            return values, cursor

        nested, _ = build(0, tuple(shape))
        return FakeArray(nested)

    def copy(self):
        return FakeArray(self.tolist())

    def tolist(self):
        return json.loads(json.dumps(self._data))

    def __getitem__(self, key):
        def apply_selectors(data, selectors):
            if not selectors:
                return data
            selector = selectors[0]
            remaining = selectors[1:]
            if selector is None:
                if not isinstance(data, list):
                    raise TypeError("cannot add axis to scalar")
                return [[apply_selectors(item, remaining)] for item in data]
            if isinstance(selector, slice):
                selected = data[selector]
                if not remaining:
                    return selected
                return [apply_selectors(item, remaining) for item in selected]
            return apply_selectors(data[selector], remaining)

        data = self._data
        if not isinstance(key, tuple):
            result = data[key]
            return FakeArray(result) if isinstance(result, list) else result
        data = apply_selectors(data, list(key))
        return FakeArray(data) if isinstance(data, list) else data


class FakeNumpyModule:
    uint8 = "uint8"

    @staticmethod
    def frombuffer(buffer, dtype=None):
        del dtype
        return FakeArray(list(buffer))


def install_route_recorder_stubs_without_cv_bridge():
    modules = {
        "cv_bridge": None,
        "cv2": build_fake_cv2(),
        "numpy": FakeNumpyModule(),
        "rclpy": types.SimpleNamespace(init=lambda args=None: None, spin=lambda node: None, shutdown=lambda: None),
        "rclpy.node": types.SimpleNamespace(Node=object),
        "nav_msgs": types.ModuleType("nav_msgs"),
        "nav_msgs.msg": types.SimpleNamespace(Odometry=object),
        "sensor_msgs": types.ModuleType("sensor_msgs"),
        "sensor_msgs.msg": types.SimpleNamespace(Image=object),
    }
    return patch.dict(sys.modules, modules)


def make_image_msg(encoding, width, height, values, step=None):
    channels = {
        "bgr8": 3,
        "rgb8": 3,
        "mono8": 1,
        "bgra8": 4,
        "rgba8": 4,
    }[encoding]
    row_bytes = width * channels
    actual_step = row_bytes if step is None else step
    if actual_step < row_bytes:
        raise ValueError("step must be >= row_bytes")
    rows = []
    cursor = 0
    for _ in range(height):
        row_values = values[cursor:cursor + row_bytes]
        rows.append(bytes(row_values) + b"\x00" * (actual_step - row_bytes))
        cursor += row_bytes
    return types.SimpleNamespace(
        encoding=encoding,
        height=height,
        width=width,
        step=actual_step,
        data=b"".join(rows),
    )


def fake_odom(sec=1, nanosec=0, x=1.0, y=2.0, z=0.0):
    return types.SimpleNamespace(
        header=types.SimpleNamespace(stamp=types.SimpleNamespace(sec=sec, nanosec=nanosec)),
        pose=types.SimpleNamespace(
            pose=types.SimpleNamespace(
                position=types.SimpleNamespace(x=x, y=y, z=z),
                orientation=types.SimpleNamespace(x=0.0, y=0.0, z=0.0, w=1.0),
            )
        ),
    )


class FakeLogger:
    def __init__(self):
        self.messages = []

    def info(self, message):
        self.messages.append(("info", message))

    def warn(self, message):
        self.messages.append(("warn", message))


class RouteDataRecorderStaticTest(unittest.TestCase):
    def setUp(self):
        sys.modules.pop("ros2_trashbot_nav.route_data_recorder", None)

    def test_cv_bridge_import_is_optional(self):
        # 板上缺 cv_bridge 时，模块必须仍可 import，route recorder 才能继续等 /odom 写 route.csv。
        with install_route_recorder_stubs_without_cv_bridge():
            module = importlib.import_module("ros2_trashbot_nav.route_data_recorder")

        self.assertIsNone(module.CvBridge)
        self.assertIs(module.CvBridgeError, Exception)
        self.assertTrue(callable(module.convert_image_msg_to_bgr8_without_cv_bridge))

    def test_fallback_supports_common_encodings_and_rejects_unknown(self):
        with install_route_recorder_stubs_without_cv_bridge():
            module = importlib.import_module("ros2_trashbot_nav.route_data_recorder")

            cases = [
                (
                    "bgr8",
                    make_image_msg("bgr8", 1, 1, [11, 22, 33]),
                    [[[11, 22, 33]]],
                ),
                (
                    "rgb8",
                    make_image_msg("rgb8", 1, 1, [1, 2, 3]),
                    [[[3, 2, 1]]],
                ),
                (
                    "mono8",
                    make_image_msg("mono8", 2, 1, [7, 8]),
                    [[[7, 7, 7], [8, 8, 8]]],
                ),
                (
                    "bgra8",
                    make_image_msg("bgra8", 1, 1, [9, 10, 11, 12]),
                    [[[9, 10, 11]]],
                ),
                (
                    "rgba8",
                    make_image_msg("rgba8", 1, 1, [20, 21, 22, 23], step=6),
                    [[[22, 21, 20]]],
                ),
            ]
            for encoding, msg, expected in cases:
                with self.subTest(encoding=encoding):
                    frame, reason = module.convert_image_msg_to_bgr8_without_cv_bridge(msg)
                    self.assertEqual(reason, "")
                    self.assertEqual(frame.tolist(), expected)

            frame, reason = module.convert_image_msg_to_bgr8_without_cv_bridge(
                types.SimpleNamespace(encoding="yuv422", height=1, width=1, step=2, data=b"\x00\x00")
            )

        self.assertIsNone(frame)
        self.assertEqual(reason, "unsupported image encoding: yuv422")

    def test_bridge_failure_falls_back_to_raw_buffer_conversion(self):
        class FakeBridge:
            def imgmsg_to_cv2(self, _msg, desired_encoding="bgr8"):
                raise Exception(f"bridge failed for {desired_encoding}")

        with install_route_recorder_stubs_without_cv_bridge():
            module = importlib.import_module("ros2_trashbot_nav.route_data_recorder")
            msg = make_image_msg("rgb8", 1, 1, [4, 5, 6])
            frame, reason = module.convert_image_msg_to_bgr8(msg, bridge=FakeBridge())

        self.assertEqual(reason, "")
        self.assertEqual(frame.tolist(), [[[6, 5, 4]]])

    def test_no_image_still_writes_route_csv_and_status_file(self):
        with install_route_recorder_stubs_without_cv_bridge():
            module = importlib.import_module("ros2_trashbot_nav.route_data_recorder")

            with tempfile.TemporaryDirectory() as td:
                output_dir = Path(td)
                keyframe_dir = output_dir / "keyframes"
                keyframe_dir.mkdir()
                route_csv = output_dir / "route.csv"

                recorder = module.RouteDataRecorder.__new__(module.RouteDataRecorder)
                recorder.output_dir = str(output_dir)
                recorder.keyframe_dir = str(keyframe_dir)
                recorder.route_csv = str(route_csv)
                recorder.min_distance_m = 0.0
                recorder.route_frame_id = "map"
                recorder.route_id = "no_image_route"
                recorder.sample_manifest_name = "manifest.json"
                recorder.sample_manifest_max_entries = 10
                recorder.bridge = None
                recorder.latest_frame = None
                recorder.last_image_conversion_error = ""
                recorder.last_x = None
                recorder.last_y = None
                recorder.index = 0
                recorder.csv_file = open(route_csv, "w", newline="", encoding="utf-8")
                recorder.writer = csv.writer(recorder.csv_file)
                recorder.writer.writerow(["index", "sec", "nanosec", "frame_id", "x", "y", "z", "qx", "qy", "qz", "qw", "frame"])
                logger = FakeLogger()
                recorder.get_logger = lambda: logger

                try:
                    recorder._record_image_conversion_failure("unsupported image encoding: yuv422")
                    recorder._on_odom(fake_odom(sec=9, nanosec=125000000, x=3.5, y=4.5))
                finally:
                    recorder.csv_file.close()

                with route_csv.open("r", encoding="utf-8") as route_file:
                    rows = list(csv.DictReader(route_file))
                status = json.loads((output_dir / "image_conversion_status.json").read_text(encoding="utf-8"))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["sec"], "9")
        self.assertEqual(rows[0]["nanosec"], "125000000")
        self.assertEqual(rows[0]["frame_id"], "map")
        self.assertEqual(rows[0]["x"], "3.5")
        self.assertEqual(rows[0]["y"], "4.5")
        self.assertEqual(rows[0]["frame"], "000.jpg")
        self.assertFalse((output_dir / "manifest.json").exists())
        self.assertEqual(status["schema"], "trashbot.route_data_recorder.image_conversion.v1")
        self.assertEqual(status["status"], "degraded")
        self.assertEqual(status["reason"], "unsupported image encoding: yuv422")
        self.assertFalse(status["cv_bridge_available"])
        self.assertTrue(status["cv2_available"])
        self.assertTrue(status["numpy_available"])
        self.assertEqual(logger.messages[-1], ("info", "Saved waypoint #1 at (3.50, 4.50)"))


if __name__ == "__main__":
    unittest.main()
