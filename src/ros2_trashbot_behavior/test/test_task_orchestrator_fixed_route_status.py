import importlib
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))


def install_ros_stubs():
    class ActionServer:
        def __init__(self, *_args, **_kwargs):
            pass

    class Node:
        pass

    modules = {
        "rclpy": types.SimpleNamespace(init=lambda args=None: None, shutdown=lambda: None),
        "rclpy.node": types.SimpleNamespace(Node=Node),
        "rclpy.action": types.SimpleNamespace(
            ActionServer=ActionServer,
            CancelResponse=types.SimpleNamespace(ACCEPT=1),
            GoalResponse=types.SimpleNamespace(ACCEPT=1, REJECT=2),
        ),
        "rclpy.callback_groups": types.SimpleNamespace(MutuallyExclusiveCallbackGroup=object),
        "rclpy.executors": types.SimpleNamespace(MultiThreadedExecutor=object),
        "std_srvs": types.ModuleType("std_srvs"),
        "std_srvs.srv": types.SimpleNamespace(SetBool=object),
        "ros2_trashbot_interfaces": types.ModuleType("ros2_trashbot_interfaces"),
        "ros2_trashbot_interfaces.action": types.SimpleNamespace(
            TrashCollection=object,
            Patrol=object,
        ),
        "ros2_trashbot_interfaces.msg": types.SimpleNamespace(
            TrashStatus=object,
            WaypointList=object,
        ),
        "ros2_trashbot_interfaces.srv": types.SimpleNamespace(RecordWaypoint=object),
    }
    sys.modules.update(modules)


class GoalHandle:
    def __init__(self, canceled=False):
        self.is_cancel_requested = canceled


class TaskOrchestratorFixedRouteStatusTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        install_ros_stubs()
        sys.modules.pop("ros2_trashbot_behavior.task_orchestrator", None)
        cls.module = importlib.import_module("ros2_trashbot_behavior.task_orchestrator")

    def make_orchestrator(self, status_file, timeout_sec=0.05):
        node = object.__new__(self.module.TaskOrchestrator)
        node.fixed_route_status_file = str(status_file)
        node.navigation_timeout_sec = timeout_sec
        return node

    def test_fixed_route_completed_status_returns_success(self):
        with tempfile.TemporaryDirectory() as td:
            status_file = Path(td) / "status.json"
            status_file.write_text(
                json.dumps({"state": "completed", "last_nav_result": "dry_run_checkpoint_passed"}),
                encoding="utf-8",
            )
            node = self.make_orchestrator(status_file)

            result = node._navigate_fixed_route_status("trash_station", GoalHandle())

        self.assertTrue(result.success)
        self.assertEqual(result.result_code, "fixed_route_completed")
        self.assertEqual(result.message, "fixed_route completed")

    def test_fixed_route_error_status_returns_failure_reason(self):
        with tempfile.TemporaryDirectory() as td:
            status_file = Path(td) / "status.json"
            status_file.write_text(
                json.dumps({"state": "error", "failure_reason": "route file not found"}),
                encoding="utf-8",
            )
            node = self.make_orchestrator(status_file)

            result = node._navigate_fixed_route_status("trash_station", GoalHandle())

        self.assertFalse(result.success)
        self.assertEqual(result.result_code, "fixed_route_failed")
        self.assertEqual(result.message, "route file not found")

    def test_fixed_route_missing_terminal_status_times_out(self):
        with tempfile.TemporaryDirectory() as td:
            status_file = Path(td) / "status.json"
            node = self.make_orchestrator(status_file, timeout_sec=0.0)

            result = node._navigate_fixed_route_status("trash_station", GoalHandle())

        self.assertFalse(result.success)
        self.assertEqual(result.result_code, "timeout")
        self.assertIn("did not report completion", result.message)

    def test_fixed_route_cancel_request_returns_canceled(self):
        with tempfile.TemporaryDirectory() as td:
            status_file = Path(td) / "status.json"
            node = self.make_orchestrator(status_file)

            result = node._navigate_fixed_route_status("trash_station", GoalHandle(canceled=True))

        self.assertFalse(result.success)
        self.assertEqual(result.result_code, "canceled")
        self.assertEqual(result.message, "navigation canceled")


if __name__ == "__main__":
    unittest.main()
