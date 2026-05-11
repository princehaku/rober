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

    class Waypoint:
        def __init__(self):
            self.name = ""
            self.pose = None
            self.type = 0
            self.visited = False
            self.last_visit_time = 0.0
            self.comment = ""

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
        node.elevator_assist_enabled = False
        node.elevator_assist_mode = "dry_run"
        node.elevator_assist_target_floor = "1"
        node.elevator_assist_dry_run_failure = ""
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
        self.assertEqual(payload["elevator_assist"]["enabled"], False)
        self.assertEqual(payload["elevator_assist"]["phase"], "disabled")
        self.assertEqual(payload["source"], "task_orchestrator")
        self.assertEqual(payload["evidence_ref"], "")
        self.assertEqual(payload["failure_code"], "")
        self.assertEqual(payload["human_intervention_required"], False)

    def test_execute_collection_elevator_assist_dry_run_records_happy_path(self):
        with tempfile.TemporaryDirectory() as td:
            node = self.make_orchestrator(Path(td))
            node.elevator_assist_enabled = True
            goal = FakeGoalHandle()

            result = asyncio.run(node._execute_collection(goal))
            payload = json.loads(Path(result.task_record_path).read_text(encoding="utf-8"))

        phases = [event["phase"] for event in payload["elevator_assist"]["events"]]
        elevator_events = [
            transition for transition in payload["state_transitions"]
            if transition["event"] == "elevator_phase"
        ]

        self.assertTrue(result.success)
        self.assertEqual(
            phases,
            [
                "approaching_elevator",
                "waiting_elevator_open",
                "entering_elevator",
                "requesting_floor_help",
                "waiting_target_floor",
                "exiting_elevator",
                "resume_delivery",
            ],
        )
        self.assertEqual(payload["elevator_assist"]["enabled"], True)
        self.assertEqual(payload["elevator_assist"]["mode"], "dry_run")
        self.assertEqual(payload["elevator_assist"]["phase"], "resume_delivery")
        self.assertEqual(payload["elevator_assist"]["target_floor"], "1")
        self.assertEqual(
            payload["elevator_assist"]["speaker_prompt"],
            self.module.ELEVATOR_ASSIST_PROMPT,
        )
        self.assertEqual(payload["elevator_assist"]["evidence"]["waiting_elevator_open"], "door_open")
        self.assertEqual(len(elevator_events), 7)
        self.assertEqual(payload["final_status"], "success")

    def test_execute_collection_elevator_assist_failure_aborts_with_record(self):
        with tempfile.TemporaryDirectory() as td:
            node = self.make_orchestrator(Path(td))
            node.elevator_assist_enabled = True
            node.elevator_assist_dry_run_failure = "target_floor_unconfirmed"
            goal = FakeGoalHandle()

            result = asyncio.run(node._execute_collection(goal))
            payload = json.loads(Path(result.task_record_path).read_text(encoding="utf-8"))

        self.assertFalse(result.success)
        self.assertTrue(goal.aborted)
        self.assertEqual(result.error_code, "elevator_failed")
        self.assertEqual(payload["final_status"], "failed")
        self.assertEqual(payload["failure_code"], "elevator_failed")
        self.assertEqual(payload["human_intervention_required"], True)
        self.assertEqual(payload["elevator_assist"]["state"], "failed")
        self.assertEqual(payload["elevator_assist"]["phase"], "waiting_target_floor")
        self.assertEqual(payload["elevator_assist"]["evidence"]["failure"], "target_floor_unconfirmed")
        self.assertEqual(payload["result_path"], "")
        self.assertEqual(payload["evidence_ref"], "")
        self.assertIn("target floor", payload["error_message"])

    def test_execute_collection_navigation_failure_records_nav_fail(self):
        with tempfile.TemporaryDirectory() as td:
            node = self.make_orchestrator(Path(td))
            navigation_failure = self.module.NavigationResult(
                False,
                "failed",
                "simulated nav failure",
                0.1,
            )
            node._navigate_delivery_target = lambda *_args, **_kwargs: (1, [navigation_failure], navigation_failure)
            goal = FakeGoalHandle()

            result = asyncio.run(node._execute_collection(goal))
            payload = json.loads(Path(result.task_record_path).read_text(encoding="utf-8"))

        self.assertFalse(result.success)
        self.assertTrue(goal.aborted)
        self.assertEqual(result.error_code, "navigation_failed")
        self.assertEqual(result.final_state, "error")
        self.assertEqual(payload["final_status"], "failed")
        self.assertEqual(payload["error_code"], "navigation_failed")
        self.assertEqual(payload["failure_code"], "NAV_FAIL")
        self.assertEqual(payload["result_path"], "")
        self.assertEqual(payload["evidence_ref"], "")
        self.assertEqual(payload["human_intervention_required"], True)

    def test_execute_collection_cancel_while_delivering_records_cancel_code(self):
        with tempfile.TemporaryDirectory() as td:
            node = self.make_orchestrator(Path(td))
            goal = FakeGoalHandle()
            goal.is_cancel_requested = True

            result = asyncio.run(node._execute_collection(goal))
            payload = json.loads(Path(result.task_record_path).read_text(encoding="utf-8"))

        self.assertFalse(result.success)
        self.assertTrue(goal.canceled_called)
        self.assertEqual(result.error_code, "canceled")
        self.assertEqual(result.final_state, "idle")
        self.assertEqual(payload["final_status"], "canceled")
        self.assertEqual(payload["error_code"], "canceled")
        self.assertEqual(payload["failure_code"], "TASK_CANCEL")
        self.assertEqual(payload["evidence_ref"], "")
        self.assertEqual(payload["result_path"], "")
        self.assertEqual(payload["human_intervention_required"], True)

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
        self.assertEqual(payload["failure_code"], "NAV_TIMEOUT")
        self.assertEqual(payload["result_path"], str(status_file))
        self.assertEqual(payload["evidence_ref"], str(status_file))
        self.assertEqual(payload["final_state"], "error")
        self.assertEqual(payload["nav_results"][0]["result_code"], "timeout")

    def test_execute_collection_fixed_route_success_records_status_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            status_file = Path(td) / "status.json"
            status_file.write_text(
                json.dumps(
                    {
                        "state": "completed",
                        "route_contract_version": "fixed_route.v1",
                        "route_file": "/tmp/routes/trash_station.json",
                        "current_index": 2,
                        "total": 3,
                        "last_nav_result": "dry_run_checkpoint_passed",
                        "updated_at": "2026-05-10T12:30:00Z",
                    }
                ),
                encoding="utf-8",
            )
            node = self.make_orchestrator(Path(td), status_file)
            node.delivery_mode = "fixed_route"
            node.navigation_timeout_sec = 0.1
            goal = FakeGoalHandle()

            result = asyncio.run(node._execute_collection(goal))
            payload = json.loads(Path(result.task_record_path).read_text(encoding="utf-8"))

        self.assertTrue(goal.succeeded)
        self.assertFalse(goal.aborted)
        self.assertTrue(result.success)
        self.assertEqual(payload["delivery_mode"], "fixed_route")
        self.assertEqual(payload["final_status"], "success")
        self.assertEqual(payload["result_path"], "/tmp/routes/trash_station.json")
        self.assertEqual(payload["evidence_ref"], str(status_file))
        self.assertEqual(payload["nav_results"][0]["result_code"], "fixed_route_completed")
        self.assertEqual(payload["nav_results"][0]["message"], "fixed_route completed")
        self.assertEqual(
            payload["nav_results"][0]["evidence"],
            {
                "fixed_route_status_file": str(status_file),
                "state": "completed",
                "route_contract_version": "fixed_route.v1",
                "route_file": "/tmp/routes/trash_station.json",
                "current_index": 2,
                "total": 3,
                "last_nav_result": "dry_run_checkpoint_passed",
                "updated_at": "2026-05-10T12:30:00Z",
            },
        )

    def test_execute_collection_manual_dropoff_timeout_aborts_with_timeout_record(self):
        with tempfile.TemporaryDirectory() as td:
            node = self.make_orchestrator(Path(td))
            node.dropoff_mode = "manual_confirm"
            node.dropoff_timeout_sec = 0.0
            node.dropoff_gate = self.module.DropoffConfirmationGate()
            goal = FakeGoalHandle()

            result = asyncio.run(node._execute_collection(goal))
            payload = json.loads(Path(result.task_record_path).read_text(encoding="utf-8"))

        self.assertFalse(goal.succeeded)
        self.assertTrue(goal.aborted)
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "timed_out")
        self.assertEqual(result.final_state, "error")
        self.assertIn("dropoff confirmation timed out", result.error_message)
        self.assertEqual(payload["final_status"], "failed")
        self.assertEqual(payload["error_code"], "timed_out")
        self.assertEqual(payload["failure_code"], "NAV_TIMEOUT")
        self.assertEqual(payload["result_path"], "")
        self.assertEqual(payload["human_intervention_required"], True)
        self.assertEqual(payload["final_state"], "error")
        self.assertEqual(payload["dropoff_result"]["result_code"], "manual_confirm_timeout")


if __name__ == "__main__":
    unittest.main()
