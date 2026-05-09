import asyncio
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

    class Result:
        def __init__(self):
            self.success = False
            self.items_collected = 0
            self.items_disposed = 0
            self.total_duration_sec = 0.0
            self.error_code = ""
            self.error_message = ""
            self.final_state = ""
            self.task_record_path = ""

    class Feedback:
        def __init__(self):
            self.arrived = False
            self.collected = False
            self.delivered = False
            self.status = 0
            self.percent_complete = 0.0
            self.current_step = ""
            self.state = ""
            self.event = ""
            self.message = ""
            self.elapsed_sec = 0.0

    TrashCollection = types.SimpleNamespace(Result=Result, Feedback=Feedback)

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
            TrashCollection=TrashCollection,
            Patrol=object,
        ),
        "ros2_trashbot_interfaces.msg": types.SimpleNamespace(
            TrashStatus=object,
            WaypointList=object,
        ),
        "ros2_trashbot_interfaces.srv": types.SimpleNamespace(RecordWaypoint=object),
    }
    sys.modules.update(modules)


class FakeDuration:
    nanoseconds = 1_000_000_000


class FakeNow:
    def __sub__(self, _other):
        return FakeDuration()


class FakeClock:
    def now(self):
        return FakeNow()


class FakeLogger:
    def info(self, _message):
        pass

    def warn(self, _message):
        pass

    def error(self, _message):
        pass


class FakeGoalHandle:
    def __init__(self, target="trash_station"):
        self.request = types.SimpleNamespace(trash_goal_frame=target)
        self.is_cancel_requested = False
        self.feedback = []
        self.succeeded = False
        self.aborted = False
        self.canceled_called = False

    def publish_feedback(self, feedback):
        self.feedback.append(feedback)

    def succeed(self):
        self.succeeded = True

    def abort(self):
        self.aborted = True

    def canceled(self):
        self.canceled_called = True


class TaskOrchestratorCollectionExecutionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        install_ros_stubs()
        sys.modules.pop("ros2_trashbot_behavior.task_orchestrator", None)
        cls.module = importlib.import_module("ros2_trashbot_behavior.task_orchestrator")

    def make_orchestrator(self, task_record_dir, fixed_route_status_file=""):
        node = object.__new__(self.module.TaskOrchestrator)
        node.state = self.module.RobotState.IDLE
        node.collection_count = 0
        node.task_record_dir = str(task_record_dir)
        node.delivery_target = "trash_station"
        node.delivery_mode = "dry_run"
        node.delivery_dry_run = False
        node.waypoint_file = "/tmp/waypoints.yaml"
        node.return_target = ""
        node.navigation_timeout_sec = 0.0
        node.navigation_retry_limit = 0
        node.dropoff_mode = "dry_run"
        node.dropoff_timeout_sec = 0.0
        node.fixed_route_status_file = str(fixed_route_status_file)
        node.get_clock = lambda: FakeClock()
        node.get_logger = lambda: FakeLogger()
        node._clear_collection_active = lambda: None
        return node

    def test_execute_collection_dry_run_success_sets_result_and_record(self):
        with tempfile.TemporaryDirectory() as td:
            node = self.make_orchestrator(Path(td))
            goal = FakeGoalHandle()

            result = asyncio.run(node._execute_collection(goal))
            payload = json.loads(Path(result.task_record_path).read_text(encoding="utf-8"))

        self.assertTrue(goal.succeeded)
        self.assertFalse(goal.aborted)
        self.assertTrue(result.success)
        self.assertEqual(result.items_collected, 1)
        self.assertEqual(result.items_disposed, 1)
        self.assertEqual(result.error_code, "")
        self.assertEqual(result.final_state, "idle")
        self.assertEqual(payload["final_status"], "success")
        self.assertEqual(payload["error_code"], "")
        self.assertEqual(payload["final_state"], "idle")
        self.assertEqual(payload["delivery_mode"], "dry_run")
        self.assertEqual(payload["dropoff_result"]["result_code"], "dry_run")

    def test_execute_collection_fixed_route_timeout_aborts_with_timeout_record(self):
        with tempfile.TemporaryDirectory() as td:
            status_file = Path(td) / "missing-status.json"
            node = self.make_orchestrator(Path(td), status_file)
            node.delivery_mode = "fixed_route"
            goal = FakeGoalHandle()

            result = asyncio.run(node._execute_collection(goal))
            payload = json.loads(Path(result.task_record_path).read_text(encoding="utf-8"))

        self.assertFalse(goal.succeeded)
        self.assertTrue(goal.aborted)
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "timed_out")
        self.assertEqual(result.final_state, "error")
        self.assertIn("did not report completion", result.error_message)
        self.assertEqual(payload["final_status"], "failed")
        self.assertEqual(payload["error_code"], "timed_out")
        self.assertEqual(payload["final_state"], "error")
        self.assertEqual(payload["nav_results"][0]["result_code"], "timeout")


if __name__ == "__main__":
    unittest.main()
