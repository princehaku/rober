import importlib
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))


def install_ros_stubs(
    parameter_overrides,
    basic_navigator_calls,
    *,
    keyframe_image=None,
    orb_descriptors=None,
    match_count=0,
):
    class Parameter:
        def __init__(self, value):
            self.value = value

    class Logger:
        def info(self, _message):
            pass

        def warn(self, _message):
            pass

        def error(self, _message):
            pass

    class Clock:
        class Now:
            def to_msg(self):
                return object()

        def now(self):
            return self.Now()

    class Node:
        def __init__(self, _name):
            self._parameters = {}

        def declare_parameter(self, name, default_value):
            self._parameters[name] = parameter_overrides.get(name, default_value)

        def get_parameter(self, name):
            return Parameter(self._parameters[name])

        def create_subscription(self, *_args):
            return object()

        def create_timer(self, *_args):
            return object()

        def get_logger(self):
            return Logger()

        def get_clock(self):
            return Clock()

    class BasicNavigator:
        def __init__(self):
            basic_navigator_calls.append("constructed")
            raise AssertionError("BasicNavigator must not be constructed in dry_run")

    class PoseStamped:
        def __init__(self):
            self.header = types.SimpleNamespace(frame_id="", stamp=None)
            self.pose = types.SimpleNamespace(
                position=types.SimpleNamespace(x=0.0, y=0.0, z=0.0),
                orientation=types.SimpleNamespace(x=0.0, y=0.0, z=0.0, w=1.0),
            )

    cv2 = types.ModuleType("cv2")
    cv2.NORM_HAMMING = 6
    cv2.COLOR_BGR2GRAY = 0
    if orb_descriptors is None:
        cv2.ORB_create = lambda _count: types.SimpleNamespace(detectAndCompute=lambda *_args: ([], None))
    else:
        cv2.ORB_create = lambda _count: types.SimpleNamespace(
            detectAndCompute=lambda *_args: ([object()], orb_descriptors)
        )
    cv2.BFMatcher = lambda *_args, **_kwargs: types.SimpleNamespace(
        match=lambda *_args: [object()] * match_count
    )
    cv2.imread = lambda _path: keyframe_image
    cv2.cvtColor = lambda image, _code: image

    modules = {
        "cv2": cv2,
        "yaml": types.SimpleNamespace(
            safe_load=lambda stream: {"waypoints": [{"x": 1.0, "y": 2.0, "qw": 1.0}]},
            YAMLError=Exception,
        ),
        "cv_bridge": types.SimpleNamespace(CvBridge=lambda: object(), CvBridgeError=Exception),
        "rclpy": types.SimpleNamespace(init=lambda args=None: None, spin=lambda node: None, shutdown=lambda: None),
        "rclpy.node": types.SimpleNamespace(Node=Node),
        "sensor_msgs": types.ModuleType("sensor_msgs"),
        "sensor_msgs.msg": types.SimpleNamespace(Image=object),
        "nav2_simple_commander": types.ModuleType("nav2_simple_commander"),
        "nav2_simple_commander.robot_navigator": types.SimpleNamespace(
            BasicNavigator=BasicNavigator,
            TaskResult=types.SimpleNamespace(SUCCEEDED=1),
        ),
        "geometry_msgs": types.ModuleType("geometry_msgs"),
        "geometry_msgs.msg": types.SimpleNamespace(PoseStamped=PoseStamped),
    }
    sys.modules.update(modules)


class FixedRouteDryRunOfflineTest(unittest.TestCase):
    def test_missing_route_file_writes_error_not_completed(self):
        with tempfile.TemporaryDirectory() as td:
            status_file = Path(td) / "status.json"
            basic_navigator_calls = []
            install_ros_stubs(
                {
                    "route_file": str(Path(td) / "missing.yaml"),
                    "keyframe_dir": str(Path(td) / "keyframes"),
                    "dry_run": True,
                    "enable_visual_gate": False,
                    "debug_status_file": str(status_file),
                },
                basic_navigator_calls,
            )
            sys.modules.pop("ros2_trashbot_nav.fixed_route_autonomy", None)
            module = importlib.import_module("ros2_trashbot_nav.fixed_route_autonomy")

            node = module.FixedRouteAutonomy()
            node._run_route()

            payload = json.loads(status_file.read_text(encoding="utf-8"))
            self.assertEqual(payload["state"], "error")
            self.assertNotEqual(payload["state"], "completed")
            self.assertIn("route file not found", payload["failure_reason"])
            self.assertEqual(payload["total"], 0)
            summary = payload["route_proof_summary"]
            self.assertEqual(summary["coverage_rate"], 0.0)
            self.assertEqual(summary["covered_checkpoints"], 0)
            self.assertEqual(summary["total_checkpoints"], 0)
            self.assertEqual(summary["missing_checkpoints"], [])
            self.assertEqual(summary["gate_status"], "not_checked")
            self.assertIn("route file not found", summary["last_block_reason"])

    def test_empty_route_file_writes_error_not_completed(self):
        with tempfile.TemporaryDirectory() as td:
            route_file = Path(td) / "empty.yaml"
            status_file = Path(td) / "status.json"
            route_file.write_text("waypoints: []\n", encoding="utf-8")
            basic_navigator_calls = []
            install_ros_stubs(
                {
                    "route_file": str(route_file),
                    "keyframe_dir": str(Path(td) / "keyframes"),
                    "dry_run": True,
                    "enable_visual_gate": False,
                    "debug_status_file": str(status_file),
                },
                basic_navigator_calls,
            )
            sys.modules.pop("ros2_trashbot_nav.fixed_route_autonomy", None)
            module = importlib.import_module("ros2_trashbot_nav.fixed_route_autonomy")

            original_validate = module.validate_route_yaml_data
            module.validate_route_yaml_data = lambda _data, source: original_validate(
                {"waypoints": []},
                source,
            )
            try:
                node = module.FixedRouteAutonomy()
                node._run_route()
            finally:
                module.validate_route_yaml_data = original_validate

            payload = json.loads(status_file.read_text(encoding="utf-8"))
            self.assertEqual(payload["state"], "error")
            self.assertNotEqual(payload["state"], "completed")
            self.assertIn("route must not be empty", payload["failure_reason"])
            self.assertEqual(payload["total"], 0)
            summary = payload["route_proof_summary"]
            self.assertEqual(summary["coverage_rate"], 0.0)
            self.assertEqual(summary["covered_checkpoints"], 0)
            self.assertEqual(summary["total_checkpoints"], 0)
            self.assertEqual(summary["missing_checkpoints"], [])
            self.assertEqual(summary["gate_status"], "not_checked")
            self.assertIn("route must not be empty", summary["last_block_reason"])

    def test_dry_run_does_not_create_basic_navigator_and_writes_contract_status(self):
        with tempfile.TemporaryDirectory() as td:
            route_file = Path(td) / "fixed_route.yaml"
            status_file = Path(td) / "status.json"
            route_file.write_text(
                "waypoints:\n"
                "  - frame_id: map\n"
                "    x: 1.0\n"
                "    y: 2.0\n"
                "    qw: 1.0\n",
                encoding="utf-8",
            )
            basic_navigator_calls = []
            install_ros_stubs(
                {
                    "route_file": str(route_file),
                    "keyframe_dir": str(Path(td) / "keyframes"),
                    "dry_run": True,
                    "enable_visual_gate": False,
                    "debug_status_file": str(status_file),
                },
                basic_navigator_calls,
            )
            sys.modules.pop("ros2_trashbot_nav.fixed_route_autonomy", None)
            module = importlib.import_module("ros2_trashbot_nav.fixed_route_autonomy")

            node = module.FixedRouteAutonomy()
            node._run_route()

            self.assertEqual(basic_navigator_calls, [])
            self.assertIsNone(node.navigator)
            payload = json.loads(status_file.read_text(encoding="utf-8"))
            self.assertEqual(payload["mode"], "dry_run")
            self.assertEqual(payload["route_contract_version"], "fixed_route.v1")
            self.assertEqual(payload["failure_reason"], "")
            self.assertEqual(payload["last_transition"], "running->completed")
            self.assertEqual(payload["current_index"], 1)
            self.assertEqual(payload["last_nav_result"], "dry_run_checkpoint_passed")
            self.assertEqual(payload["visual_gate_status"], "disabled")
            self.assertEqual(payload["visual_gate_checkpoint"], 0)
            summary = payload["route_proof_summary"]
            self.assertEqual(summary["coverage_rate"], 1.0)
            self.assertEqual(summary["covered_checkpoints"], 1)
            self.assertEqual(summary["total_checkpoints"], 1)
            self.assertEqual(summary["missing_checkpoints"], [])
            self.assertEqual(summary["gate_status"], "passed")
            self.assertEqual(summary["last_block_reason"], "")

    def test_dry_run_waits_for_visual_gate_when_no_camera_or_keyframes_exist(self):
        with tempfile.TemporaryDirectory() as td:
            route_file = Path(td) / "fixed_route.yaml"
            status_file = Path(td) / "status.json"
            route_file.write_text(
                "waypoints:\n"
                "  - frame_id: map\n"
                "    x: 1.0\n"
                "    y: 2.0\n"
                "    qw: 1.0\n",
                encoding="utf-8",
            )
            basic_navigator_calls = []
            install_ros_stubs(
                {
                    "route_file": str(route_file),
                    "keyframe_dir": str(Path(td) / "missing_keyframes"),
                    "dry_run": True,
                    "enable_visual_gate": True,
                    "debug_status_file": str(status_file),
                },
                basic_navigator_calls,
            )
            sys.modules.pop("ros2_trashbot_nav.fixed_route_autonomy", None)
            module = importlib.import_module("ros2_trashbot_nav.fixed_route_autonomy")

            node = module.FixedRouteAutonomy()
            node._run_route()

            payload = json.loads(status_file.read_text(encoding="utf-8"))
            self.assertEqual(payload["state"], "waiting_visual_gate")
            self.assertEqual(payload["current_index"], 0)
            self.assertEqual(payload["last_nav_result"], "")
            self.assertIn("missing keyframes: [0]", payload["last_error"])
            self.assertIn("missing keyframes: [0]", payload["failure_reason"])
            self.assertEqual(payload["visual_gate_status"], "keyframe_preflight_failed")
            self.assertIn("missing keyframes: [0]", payload["visual_gate_detail"])
            self.assertEqual(payload["visual_gate_checkpoint"], 0)
            self.assertEqual(payload["keyframe_preflight"]["missing_keyframes"], [0])
            self.assertFalse(payload["keyframe_preflight"]["route_visual_ready"])
            summary = payload["route_proof_summary"]
            self.assertEqual(summary["coverage_rate"], 0.0)
            self.assertEqual(summary["covered_checkpoints"], 0)
            self.assertEqual(summary["total_checkpoints"], 1)
            self.assertEqual(summary["missing_checkpoints"], [0])
            self.assertEqual(summary["gate_status"], "keyframe_preflight_failed")
            self.assertIn("missing keyframes: [0]", summary["last_block_reason"])

    def test_dry_run_waits_for_camera_frame_when_keyframe_exists(self):
        with tempfile.TemporaryDirectory() as td:
            route_file = Path(td) / "fixed_route.yaml"
            status_file = Path(td) / "status.json"
            route_file.write_text(
                "waypoints:\n"
                "  - frame_id: map\n"
                "    x: 1.0\n"
                "    y: 2.0\n"
                "    qw: 1.0\n",
                encoding="utf-8",
            )
            keyframe_dir = Path(td) / "keyframes"
            keyframe_dir.mkdir()
            (keyframe_dir / "000.jpg").write_bytes(b"stub")
            basic_navigator_calls = []
            install_ros_stubs(
                {
                    "route_file": str(route_file),
                    "keyframe_dir": str(keyframe_dir),
                    "dry_run": True,
                    "enable_visual_gate": True,
                    "debug_status_file": str(status_file),
                },
                basic_navigator_calls,
                keyframe_image=object(),
                orb_descriptors=["keyframe-descriptor"],
            )
            sys.modules.pop("ros2_trashbot_nav.fixed_route_autonomy", None)
            module = importlib.import_module("ros2_trashbot_nav.fixed_route_autonomy")

            node = module.FixedRouteAutonomy()
            node._run_route()

            payload = json.loads(status_file.read_text(encoding="utf-8"))
            self.assertEqual(payload["state"], "waiting_visual_gate")
            self.assertEqual(payload["current_index"], 0)
            self.assertEqual(payload["visual_gate_status"], "waiting_camera_frame")
            self.assertIn("waiting for camera frame", payload["failure_reason"])
            summary = payload["route_proof_summary"]
            self.assertEqual(summary["coverage_rate"], 0.0)
            self.assertEqual(summary["covered_checkpoints"], 0)
            self.assertEqual(summary["total_checkpoints"], 1)
            self.assertEqual(summary["missing_checkpoints"], [0])
            self.assertEqual(summary["gate_status"], "waiting_camera_frame")
            self.assertIn("waiting for camera frame", summary["last_block_reason"])

    def test_dry_run_blocks_before_progress_when_later_keyframe_is_missing(self):
        with tempfile.TemporaryDirectory() as td:
            route_file = Path(td) / "fixed_route.yaml"
            status_file = Path(td) / "status.json"
            route_file.write_text(
                "waypoints:\n"
                "  - frame_id: map\n"
                "    x: 1.0\n"
                "    y: 2.0\n"
                "    qw: 1.0\n"
                "  - frame_id: map\n"
                "    x: 2.0\n"
                "    y: 3.0\n"
                "    qw: 1.0\n",
                encoding="utf-8",
            )
            keyframe_dir = Path(td) / "keyframes"
            keyframe_dir.mkdir()
            (keyframe_dir / "000.jpg").write_bytes(b"stub")
            basic_navigator_calls = []
            install_ros_stubs(
                {
                    "route_file": str(route_file),
                    "keyframe_dir": str(keyframe_dir),
                    "dry_run": True,
                    "enable_visual_gate": True,
                    "debug_status_file": str(status_file),
                },
                basic_navigator_calls,
                keyframe_image=object(),
                orb_descriptors=["keyframe-descriptor"],
            )
            sys.modules.pop("ros2_trashbot_nav.fixed_route_autonomy", None)
            module = importlib.import_module("ros2_trashbot_nav.fixed_route_autonomy")

            original_validate = module.validate_route_yaml_data
            module.validate_route_yaml_data = lambda _data, _source: [
                {"x": 1.0, "y": 2.0, "qw": 1.0},
                {"x": 2.0, "y": 3.0, "qw": 1.0},
            ]
            try:
                node = module.FixedRouteAutonomy()
                node.latest_frame = object()
                node._run_route()
            finally:
                module.validate_route_yaml_data = original_validate

            payload = json.loads(status_file.read_text(encoding="utf-8"))
            self.assertEqual(payload["state"], "waiting_visual_gate")
            self.assertEqual(payload["current_index"], 0)
            self.assertEqual(payload["total"], 2)
            self.assertEqual(payload["visual_gate_status"], "keyframe_preflight_failed")
            self.assertIn("missing keyframes: [1]", payload["failure_reason"])
            self.assertEqual(payload["keyframe_preflight"]["loaded_keyframes"], [0])
            self.assertEqual(payload["keyframe_preflight"]["missing_keyframes"], [1])
            self.assertFalse(payload["keyframe_preflight"]["route_visual_ready"])
            summary = payload["route_proof_summary"]
            self.assertEqual(summary["coverage_rate"], 0.0)
            self.assertEqual(summary["covered_checkpoints"], 0)
            self.assertEqual(summary["total_checkpoints"], 2)
            self.assertEqual(summary["missing_checkpoints"], [0, 1])
            self.assertEqual(summary["gate_status"], "keyframe_preflight_failed")
            self.assertIn("missing keyframes: [1]", summary["last_block_reason"])

    def test_dry_run_advances_after_visual_gate_passes(self):
        with tempfile.TemporaryDirectory() as td:
            route_file = Path(td) / "fixed_route.yaml"
            status_file = Path(td) / "status.json"
            route_file.write_text(
                "waypoints:\n"
                "  - frame_id: map\n"
                "    x: 1.0\n"
                "    y: 2.0\n"
                "    qw: 1.0\n",
                encoding="utf-8",
            )
            keyframe_dir = Path(td) / "keyframes"
            keyframe_dir.mkdir()
            (keyframe_dir / "000.jpg").write_bytes(b"stub")
            basic_navigator_calls = []
            install_ros_stubs(
                {
                    "route_file": str(route_file),
                    "keyframe_dir": str(keyframe_dir),
                    "dry_run": True,
                    "enable_visual_gate": True,
                    "visual_match_threshold": 2,
                    "debug_status_file": str(status_file),
                },
                basic_navigator_calls,
                keyframe_image=object(),
                orb_descriptors=["shared-descriptor"],
                match_count=2,
            )
            sys.modules.pop("ros2_trashbot_nav.fixed_route_autonomy", None)
            module = importlib.import_module("ros2_trashbot_nav.fixed_route_autonomy")

            node = module.FixedRouteAutonomy()
            node.latest_frame = object()
            node._run_route()

            payload = json.loads(status_file.read_text(encoding="utf-8"))
            self.assertEqual(payload["state"], "completed")
            self.assertEqual(payload["current_index"], 1)
            self.assertEqual(payload["visual_gate_status"], "passed")
            self.assertIn("passed checkpoint 0", payload["visual_gate_detail"])
            self.assertEqual(payload["last_nav_result"], "dry_run_checkpoint_passed")
            summary = payload["route_proof_summary"]
            self.assertEqual(summary["coverage_rate"], 1.0)
            self.assertEqual(summary["covered_checkpoints"], 1)
            self.assertEqual(summary["total_checkpoints"], 1)
            self.assertEqual(summary["missing_checkpoints"], [])
            self.assertEqual(summary["gate_status"], "passed")
            self.assertEqual(summary["last_block_reason"], "")


if __name__ == "__main__":
    unittest.main()
