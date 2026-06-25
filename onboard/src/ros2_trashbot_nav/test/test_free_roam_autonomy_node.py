"""free_roam_autonomy_node 的 ROS2 接线离线测试。"""

import importlib
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))


def install_ros_stubs() -> dict[str, object]:
    """安装最小 ROS2 stub，让本机无 ROS 环境也能验证节点合同。"""

    runtime: dict[str, object] = {}

    class Parameter:
        def __init__(self, value):
            self.value = value

    class Logger:
        def info(self, message):
            runtime.setdefault("logs", []).append(message)

    class FakeFuture:
        def add_done_callback(self, callback):
            callback(self)

    class FakeClient:
        def __init__(self):
            self.calls = 0
            self.ready = True

        def service_is_ready(self):
            return self.ready

        def call_async(self, _request):
            self.calls += 1
            return FakeFuture()

    class FakePublisher:
        def __init__(self):
            self.messages = []

        def publish(self, message):
            self.messages.append(message)

    class Node:
        def __init__(self, _name):
            self._parameters = {}
            self.subscriptions = []
            self.timers = []
            self.publisher = FakePublisher()
            self.client = FakeClient()

        def declare_parameter(self, name, default_value):
            self._parameters[name] = default_value

        def get_parameter(self, name):
            return Parameter(self._parameters[name])

        def create_subscription(self, msg_type, topic, callback, qos):
            self.subscriptions.append((msg_type, topic, callback, qos))
            return object()

        def create_publisher(self, _msg_type, _topic, _qos):
            return self.publisher

        def create_client(self, _srv_type, _service):
            return self.client

        def create_timer(self, period_s, callback):
            self.timers.append((period_s, callback))
            return object()

        def get_logger(self):
            return Logger()

        def destroy_node(self):
            runtime["destroyed"] = True

    class Twist:
        def __init__(self):
            self.linear = types.SimpleNamespace(x=0.0)
            self.angular = types.SimpleNamespace(z=0.0)

    class Trigger:
        class Request:
            pass

    modules = {
        "rclpy": types.SimpleNamespace(init=lambda args=None: None, spin=lambda node: None, shutdown=lambda: None),
        "rclpy.node": types.SimpleNamespace(Node=Node),
        "geometry_msgs": types.ModuleType("geometry_msgs"),
        "geometry_msgs.msg": types.SimpleNamespace(Twist=Twist),
        "nav_msgs": types.ModuleType("nav_msgs"),
        "nav_msgs.msg": types.SimpleNamespace(OccupancyGrid=object),
        "sensor_msgs": types.ModuleType("sensor_msgs"),
        "sensor_msgs.msg": types.SimpleNamespace(LaserScan=object),
        "std_srvs": types.ModuleType("std_srvs"),
        "std_srvs.srv": types.SimpleNamespace(Trigger=Trigger),
    }
    sys.modules.update(modules)
    return runtime


class FreeRoamAutonomyNodeTest(unittest.TestCase):
    """节点测试只验证 artifact 与安全接线，不触发真实运动。"""

    def setUp(self) -> None:
        install_ros_stubs()
        sys.modules.pop("ros2_trashbot_nav.free_roam_autonomy_node", None)
        self.module = importlib.import_module("ros2_trashbot_nav.free_roam_autonomy_node")

    def test_scan_min_distance_filters_invalid_values(self) -> None:
        """雷达距离必须过滤 inf/nan/负数和非数字。"""
        distance = self.module.finite_scan_min_distance([float("inf"), "bad", -1.0, 0.0, 0.42, 1.0])

        self.assertEqual(distance, 0.42)

    def test_map_metrics_counts_free_unknown_and_occupied_cells(self) -> None:
        """地图统计直接服务覆盖率和 unknown 下降判断。"""
        metrics = self.module.occupancy_grid_metrics([-1, -1, 0, 0, 0, 55, "bad"])

        self.assertEqual(metrics["free_cells"], 3)
        self.assertEqual(metrics["unknown_cells"], 2)
        self.assertEqual(metrics["occupied_cells"], 1)
        self.assertEqual(metrics["total_cells"], 6)
        self.assertAlmostEqual(metrics["unknown_ratio"], 2 / 6)

    def test_default_tick_writes_locked_artifact_and_calls_stop_without_cmd_vel(self) -> None:
        """默认参数下节点只能写 locked artifact 和停止兜底，不能发布 Twist。"""
        with tempfile.TemporaryDirectory() as td:
            artifact_path = Path(td) / "free_roam.json"
            node = self.module.FreeRoamAutonomyNode()
            node._parameters["artifact_path"] = str(artifact_path)

            node._tick()

            payload = json.loads(artifact_path.read_text(encoding="utf-8"))
            self.assertTrue(payload["artifact_only"])
            self.assertFalse(payload["cmd_vel_publish_enabled"])
            self.assertEqual(payload["decision"]["state"], "locked")
            self.assertEqual(payload["decision"]["linear_x_mps"], 0.0)
            self.assertEqual(node.client.calls, 1)
            self.assertEqual(node.publisher.messages, [])

    def test_unlocked_motion_publishes_bounded_twist_from_scan_and_map(self) -> None:
        """双参数解锁后才会发布策略给出的受限 Twist。"""
        with tempfile.TemporaryDirectory() as td:
            artifact_path = Path(td) / "free_roam.json"
            node = self.module.FreeRoamAutonomyNode()
            node._parameters.update(
                {
                    "artifact_path": str(artifact_path),
                    "operator_confirmed": True,
                    "mapping_active": True,
                    "stop_available": True,
                    "enable_cmd_vel_publish": True,
                    "motion_hil_unlocked": True,
                }
            )
            node._on_scan(types.SimpleNamespace(ranges=[1.0, 1.5]))
            node._on_map(types.SimpleNamespace(data=[0, 0, -1, 100]))

            node._tick()

            payload = json.loads(artifact_path.read_text(encoding="utf-8"))
            self.assertFalse(payload["artifact_only"])
            self.assertEqual(payload["decision"]["state"], "running")
            self.assertEqual(payload["decision"]["linear_x_mps"], 0.12)
            self.assertEqual(len(node.publisher.messages), 1)
            self.assertEqual(node.publisher.messages[0].linear.x, 0.12)
            self.assertEqual(node.client.calls, 0)


if __name__ == "__main__":
    unittest.main()
