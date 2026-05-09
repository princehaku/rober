import asyncio
import importlib
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

    class PatrolResult:
        def __init__(self):
            self.success = False
            self.total_duration_sec = 0.0
            self.new_points_recorded = 0
            self.map_save_path = ""

    class PatrolFeedback:
        def __init__(self):
            self.current_waypoint = None
            self.distance_traveled = 0.0
            self.waypoints_visited = 0
            self.waypoints_total = 0

    class Waypoint:
        def __init__(self):
            self.name = ""
            self.pose = None
            self.type = 0
            self.visited = False
            self.last_visit_time = 0.0
            self.comment = ""

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
            Patrol=types.SimpleNamespace(Result=PatrolResult, Feedback=PatrolFeedback),
        ),
        "ros2_trashbot_interfaces.msg": types.SimpleNamespace(
            Waypoint=Waypoint,
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
    def __init__(self):
        self.request = types.SimpleNamespace(use_saved_map=True, learn_mode=False)
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


class TaskOrchestratorPatrolExecutionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        install_ros_stubs()
        sys.modules.pop("ros2_trashbot_behavior.task_orchestrator", None)
        cls.module = importlib.import_module("ros2_trashbot_behavior.task_orchestrator")

    def make_orchestrator(self, waypoint_file):
        node = object.__new__(self.module.TaskOrchestrator)
        node.state = self.module.RobotState.IDLE
        node.learn_count = 0
        node.waypoint_file = str(waypoint_file)
        node.navigation_timeout_sec = 1.0
        node.get_clock = lambda: FakeClock()
        node.get_logger = lambda: FakeLogger()
        node._pose_stamped_from_data = lambda data: types.SimpleNamespace(data=data)
        return node

    def test_execute_patrol_visits_waypoints_from_file(self):
        with tempfile.TemporaryDirectory() as td:
            waypoint_file = Path(td) / "waypoints.yaml"
            waypoint_file.write_text(
                "waypoints:\n"
                "  - name: patrol_a\n"
                "    type: 0\n"
                "    x: 1.0\n"
                "    y: 2.0\n"
                "  - name: patrol_b\n"
                "    type: 0\n"
                "    x: 3.0\n"
                "    y: 4.0\n",
                encoding="utf-8",
            )
            node = self.make_orchestrator(waypoint_file)
            visited = []

            def navigate(waypoint, _goal_handle):
                visited.append(waypoint["name"])
                return self.module.NavigationResult(True, "succeeded", "ok", 0.25)

            node._navigate_patrol_waypoint = navigate
            goal = FakeGoalHandle()

            result = asyncio.run(node._execute_patrol(goal))

        self.assertTrue(result.success)
        self.assertTrue(goal.succeeded)
        self.assertFalse(goal.aborted)
        self.assertEqual(visited, ["patrol_a", "patrol_b"])
        self.assertEqual(
            [item.current_waypoint.name for item in goal.feedback],
            ["patrol_a", "patrol_a", "patrol_b", "patrol_b"],
        )
        self.assertEqual(goal.feedback[-1].waypoints_total, 2)
        self.assertEqual(goal.feedback[-1].waypoints_visited, 2)
        self.assertEqual(result.map_save_path, str(waypoint_file))


if __name__ == "__main__":
    unittest.main()
