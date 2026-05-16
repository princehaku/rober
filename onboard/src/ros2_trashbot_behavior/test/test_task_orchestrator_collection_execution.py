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
        node.elevator_assist_enabled = True
        node.elevator_assist_mode = "dry_run"
        node.elevator_assist_target_floor = "1"
        node.elevator_assist_dry_run_failure = ""
        node.elevator_assist_evidence_file = ""
        node.get_clock = lambda: FakeClock()
        node.get_logger = lambda: FakeLogger()
        node._clear_collection_active = lambda: None
        return node

    def make_elevator_rehearsal_artifact(self, evidence_ref="elevator-rehearsal-001", **overrides):
        payload = {
            "schema": "trashbot.elevator_assist_rehearsal_evidence.v1",
            "evidence_boundary": "software_proof_docker_elevator_evidence_driven_mainline_gate",
            "source": "software_proof",
            "evidence_ref": evidence_ref,
            "target_floor": "1F",
            "delivery_success": False,
            "primary_actions_enabled": False,
            "same_evidence_ref_required": True,
            "phase_evidence": {
                "waiting_elevator_open": {"status": "door_open", "source": "software_proof"},
                "entering_elevator": {"status": "entered", "source": "software_proof"},
                "requesting_floor_help": {"status": "prompt_requested", "source": "software_proof"},
                "waiting_target_floor": {"status": "target_floor_seen", "source": "software_proof"},
                "exiting_elevator": {"status": "exit_clear", "source": "software_proof"},
            },
            "not_proven": ["real_elevator", "hil", "delivery_success", "real_nav2_or_fixed_route"],
        }
        payload.update(overrides)
        return payload

    def test_execute_collection_default_elevator_assist_dry_run_success_sets_result_and_record(self):
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
        self.assertEqual(payload["elevator_assist"]["enabled"], True)
        self.assertEqual(payload["elevator_assist"]["mode"], "dry_run")
        self.assertEqual(payload["elevator_assist"]["phase"], "resume_delivery")
        self.assertEqual(
            payload["elevator_assist"]["proof_gate"],
            "software_proof_docker_elevator_assist_default_mainline_gate",
        )
        self.assertIn("not real elevator", payload["elevator_assist"]["boundary"])
        self.assertIn("不证明真实电梯", payload["elevator_assist"]["safe_phone_copy"])
        self.assertEqual(payload["elevator_assist"]["delivery_success"], False)
        self.assertEqual(payload["elevator_assist"]["primary_actions_enabled"], False)
        self.assertEqual(payload["elevator_assist"]["failure_reason"], "")
        self.assertEqual(payload["elevator_assist"]["manual_takeover_reason"], "")
        self.assertEqual(payload["source"], "software_proof")
        self.assertEqual(payload["evidence_ref"], "")
        self.assertEqual(payload["failure_code"], "")
        self.assertEqual(payload["human_intervention_required"], False)
        rehearsal = payload["route_task_terminal_completion_rehearsal"]
        self.assertEqual(
            rehearsal["evidence_boundary"],
            "software_proof_docker_route_task_terminal_completion_rehearsal_gate",
        )
        self.assertEqual(rehearsal["terminal_verdict"]["verdict"], "not_proven")
        self.assertEqual(rehearsal["dropoff_result"]["result_code"], "dry_run")
        self.assertFalse(rehearsal["delivery_success"])
        self.assertFalse(rehearsal["primary_actions_enabled"])
        self.assertIn("real_dropoff_completion", rehearsal["not_proven"])

    def test_execute_collection_elevator_assist_explicitly_disabled_records_warning_boundary(self):
        with tempfile.TemporaryDirectory() as td:
            node = self.make_orchestrator(Path(td))
            node.elevator_assist_enabled = False
            goal = FakeGoalHandle()

            result = asyncio.run(node._execute_collection(goal))
            payload = json.loads(Path(result.task_record_path).read_text(encoding="utf-8"))

        self.assertTrue(result.success)
        self.assertTrue(goal.succeeded)
        self.assertEqual(payload["elevator_assist"]["enabled"], False)
        self.assertEqual(payload["elevator_assist"]["phase"], "disabled")
        self.assertEqual(payload["elevator_assist"]["reason"], "disabled_by_operator")
        self.assertIn("explicitly disabled", payload["elevator_assist"]["warning"])
        self.assertEqual(
            payload["elevator_assist"]["proof_gate"],
            "software_proof_docker_elevator_assist_default_mainline_gate",
        )
        self.assertIn("not real elevator", payload["elevator_assist"]["boundary"])
        self.assertIn("不证明真实电梯", payload["elevator_assist"]["safe_phone_copy"])
        self.assertEqual(payload["elevator_assist"]["delivery_success"], False)
        self.assertEqual(payload["elevator_assist"]["primary_actions_enabled"], False)
        self.assertIn("elevator_assist_enabled=true", payload["elevator_assist"]["rerun_guidance"])
        self.assertEqual(
            payload["route_task_terminal_completion_rehearsal"]["terminal_verdict"]["verdict"],
            "not_proven",
        )

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
            payload["elevator_assist"]["proof_gate"],
            "software_proof_docker_elevator_assist_default_mainline_gate",
        )
        self.assertEqual(payload["elevator_assist"]["delivery_success"], False)
        self.assertEqual(payload["elevator_assist"]["primary_actions_enabled"], False)
        self.assertIn("real_nav2_or_fixed_route", payload["elevator_assist"]["not_proven"])
        self.assertEqual(
            payload["elevator_assist"]["speaker_prompt"],
            self.module.ELEVATOR_ASSIST_PROMPT,
        )
        self.assertEqual(payload["elevator_assist"]["evidence"]["waiting_elevator_open"], "door_open")
        self.assertEqual(len(elevator_events), 7)
        self.assertEqual(payload["final_status"], "success")

    def test_execute_collection_elevator_rehearsal_artifact_drives_phases_and_record_ref(self):
        with tempfile.TemporaryDirectory() as td:
            evidence_ref = "elevator:rehearsal-001"
            artifact_file = Path(td) / "elevator-artifact.json"
            artifact_file.write_text(
                json.dumps(self.make_elevator_rehearsal_artifact(evidence_ref=evidence_ref)),
                encoding="utf-8",
            )
            node = self.make_orchestrator(Path(td))
            node.elevator_assist_evidence_file = str(artifact_file)
            goal = FakeGoalHandle()

            result = asyncio.run(node._execute_collection(goal))
            payload = json.loads(Path(result.task_record_path).read_text(encoding="utf-8"))

        phases = [event["phase"] for event in payload["elevator_assist"]["events"]]
        elevator_events = [
            transition for transition in payload["state_transitions"]
            if transition["event"] == "elevator_phase"
        ]

        self.assertTrue(result.success)
        self.assertTrue(goal.succeeded)
        self.assertEqual(payload["evidence_ref"], "elevator:rehearsal-001")
        self.assertEqual(payload["result_path"], "elevator:rehearsal-001")
        self.assertEqual(payload["elevator_assist"]["schema"], "trashbot.elevator_assist_rehearsal_evidence.v1")
        self.assertEqual(
            payload["elevator_assist"]["proof_gate"],
            "software_proof_docker_elevator_evidence_driven_mainline_gate",
        )
        self.assertEqual(payload["elevator_assist"]["source"], "software_proof")
        self.assertEqual(payload["elevator_assist"]["same_evidence_ref_required"], True)
        self.assertEqual(payload["elevator_assist"]["delivery_success"], False)
        self.assertEqual(payload["elevator_assist"]["primary_actions_enabled"], False)
        self.assertEqual(payload["elevator_assist"]["target_floor"], "1F")
        self.assertEqual(
            phases,
            [
                "waiting_elevator_open",
                "entering_elevator",
                "requesting_floor_help",
                "waiting_target_floor",
                "exiting_elevator",
            ],
        )
        self.assertEqual(len(elevator_events), 5)
        self.assertEqual(
            payload["elevator_assist"]["evidence"]["waiting_elevator_open"],
            {"status": "door_open", "source": "software_proof"},
        )
        self.assertIn("不证明真实电梯", payload["elevator_assist"]["safe_phone_copy"])
        self.assertEqual(payload["final_status"], "success")

    def test_execute_collection_missing_elevator_rehearsal_artifact_uses_default_dry_run(self):
        with tempfile.TemporaryDirectory() as td:
            node = self.make_orchestrator(Path(td))
            node.elevator_assist_evidence_file = str(Path(td) / "missing-artifact.json")
            goal = FakeGoalHandle()

            result = asyncio.run(node._execute_collection(goal))
            payload = json.loads(Path(result.task_record_path).read_text(encoding="utf-8"))

        self.assertTrue(result.success)
        self.assertTrue(goal.succeeded)
        self.assertEqual(payload["elevator_assist"]["phase"], "resume_delivery")
        self.assertEqual(
            payload["elevator_assist"]["proof_gate"],
            "software_proof_docker_elevator_assist_default_mainline_gate",
        )
        self.assertEqual(payload["evidence_ref"], "")
        self.assertEqual(payload["result_path"], "")

    def test_execute_collection_elevator_rehearsal_artifact_failure_requires_manual_takeover(self):
        with tempfile.TemporaryDirectory() as td:
            artifact_file = Path(td) / "elevator-artifact-failure.json"
            artifact_file.write_text(
                json.dumps(
                    self.make_elevator_rehearsal_artifact(
                        evidence_ref="elevator-rehearsal-fail-001",
                        failure={
                            "phase": "waiting_target_floor",
                            "reason": "target floor evidence blocked by operator review",
                            "manual_takeover_reason": "target_floor_unconfirmed",
                        },
                    )
                ),
                encoding="utf-8",
            )
            node = self.make_orchestrator(Path(td))
            node.elevator_assist_evidence_file = str(artifact_file)
            goal = FakeGoalHandle()

            result = asyncio.run(node._execute_collection(goal))
            payload = json.loads(Path(result.task_record_path).read_text(encoding="utf-8"))

        self.assertFalse(result.success)
        self.assertTrue(goal.aborted)
        self.assertEqual(result.error_code, "elevator_failed")
        self.assertEqual(payload["final_status"], "failed")
        self.assertEqual(payload["failure_code"], "elevator_failed")
        self.assertEqual(payload["evidence_ref"], "elevator-rehearsal-fail-001")
        self.assertEqual(payload["result_path"], "elevator-rehearsal-fail-001")
        self.assertEqual(payload["human_intervention_required"], True)
        self.assertEqual(payload["elevator_assist"]["state"], "failed")
        self.assertEqual(payload["elevator_assist"]["phase"], "waiting_target_floor")
        self.assertEqual(payload["elevator_assist"]["manual_takeover_reason"], "target_floor_unconfirmed")
        self.assertEqual(
            payload["elevator_assist"]["proof_gate"],
            "software_proof_docker_elevator_evidence_driven_mainline_gate",
        )
        self.assertEqual(payload["elevator_assist"]["delivery_success"], False)
        self.assertEqual(payload["elevator_assist"]["primary_actions_enabled"], False)
        self.assertIn("target floor evidence", payload["error_message"])

    def test_execute_collection_invalid_elevator_rehearsal_artifact_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            artifact_file = Path(td) / "unsafe-artifact.json"
            artifact_file.write_text(
                json.dumps(
                    self.make_elevator_rehearsal_artifact(
                        evidence_ref="elevator-rehearsal-unsafe-001",
                        delivery_success=True,
                    )
                ),
                encoding="utf-8",
            )
            node = self.make_orchestrator(Path(td))
            node.elevator_assist_evidence_file = str(artifact_file)
            goal = FakeGoalHandle()

            result = asyncio.run(node._execute_collection(goal))
            payload = json.loads(Path(result.task_record_path).read_text(encoding="utf-8"))

        self.assertFalse(result.success)
        self.assertTrue(goal.aborted)
        self.assertEqual(result.error_code, "elevator_failed")
        self.assertEqual(payload["final_status"], "failed")
        self.assertEqual(payload["failure_code"], "elevator_failed")
        self.assertEqual(payload["evidence_ref"], "elevator-rehearsal-unsafe-001")
        self.assertEqual(payload["result_path"], "elevator-rehearsal-unsafe-001")
        self.assertEqual(payload["human_intervention_required"], True)
        self.assertEqual(payload["elevator_assist"]["state"], "failed")
        self.assertEqual(payload["elevator_assist"]["phase"], "elevator_rehearsal_evidence_validation")
        self.assertEqual(
            payload["elevator_assist"]["manual_takeover_reason"],
            "invalid_rehearsal_evidence_artifact",
        )
        self.assertIn("delivery_success=false", payload["elevator_assist"]["failure_reason"])
        self.assertEqual(payload["elevator_assist"]["delivery_success"], False)
        self.assertEqual(payload["elevator_assist"]["primary_actions_enabled"], False)

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
        self.assertEqual(
            payload["elevator_assist"]["proof_gate"],
            "software_proof_docker_elevator_assist_default_mainline_gate",
        )
        self.assertEqual(payload["elevator_assist"]["failure_reason"], "target floor was not confirmed by dry-run evidence")
        self.assertEqual(payload["elevator_assist"]["manual_takeover_reason"], "target_floor_unconfirmed")
        self.assertIn("不证明真实电梯", payload["elevator_assist"]["safe_phone_copy"])
        self.assertEqual(payload["elevator_assist"]["delivery_success"], False)
        self.assertEqual(payload["elevator_assist"]["primary_actions_enabled"], False)
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
            evidence_file = Path(td) / "route-replay.jsonl"
            route_progress = {
                "route_id": "fixed_route",
                "checkpoint_id": "fixed_route:002",
                "evidence_ref": str(evidence_file),
                "checkpoint": 2,
                "current_index": 2,
                "target": {"x": 1.2, "y": -0.5, "yaw": 0.0},
                "total_checkpoints": 3,
                "route_contract_version": "fixed_route.v1",
                "failure_code": "",
            }
            status_file.write_text(
                json.dumps(
                    {
                        "state": "completed",
                        "route_contract_version": "fixed_route.v1",
                        "source": "software_proof",
                        "route_file": "/tmp/routes/trash_station.json",
                        "route_id": "fixed_route",
                        "route_file_basename": "trash_station.json",
                        "checkpoint": 2,
                        "checkpoint_id": "fixed_route:002",
                        "current_index": 2,
                        "target": {"x": 1.2, "y": -0.5, "yaw": 0.0},
                        "total": 3,
                        "total_checkpoints": 3,
                        "evidence_ref": str(evidence_file),
                        "failure_code": "",
                        "route_progress": route_progress,
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
        self.assertEqual(payload["result_path"], str(evidence_file))
        self.assertEqual(payload["evidence_ref"], str(evidence_file))
        self.assertEqual(payload["route_progress"], route_progress)
        self.assertEqual(payload["nav_results"][0]["result_code"], "fixed_route_completed")
        self.assertEqual(payload["nav_results"][0]["message"], "fixed_route completed")
        self.assertEqual(
            payload["nav_results"][0]["evidence"],
            {
                "fixed_route_status_file": str(status_file),
                "state": "completed",
                "route_contract_version": "fixed_route.v1",
                "source": "software_proof",
                "route_file": "/tmp/routes/trash_station.json",
                "route_id": "fixed_route",
                "route_file_basename": "trash_station.json",
                "checkpoint": 2,
                "checkpoint_id": "fixed_route:002",
                "current_index": 2,
                "target": {"x": 1.2, "y": -0.5, "yaw": 0.0},
                "total": 3,
                "total_checkpoints": 3,
                "evidence_ref": str(evidence_file),
                "failure_code": "",
                "route_progress": route_progress,
                "last_nav_result": "dry_run_checkpoint_passed",
                "updated_at": "2026-05-10T12:30:00Z",
            },
        )

    def test_execute_collection_fixed_route_promotes_route_progress_evidence_ref(self):
        with tempfile.TemporaryDirectory() as td:
            status_file = Path(td) / "status.json"
            evidence_file = Path(td) / "route-progress-only.jsonl"
            route_progress = {
                "source": "software_proof",
                "route_contract_version": "fixed_route.v1",
                "route_id": "dock-route",
                "checkpoint_id": "dock-route:002",
                "checkpoint": "cp-2",
                "current_index": 2,
                "target": {"name": "trash_station"},
                "failure_code": "",
                "evidence_ref": str(evidence_file),
            }
            status_file.write_text(
                json.dumps(
                    {
                        "state": "completed",
                        "route_progress": route_progress,
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

        self.assertTrue(result.success)
        self.assertEqual(payload["result_path"], str(evidence_file))
        self.assertEqual(payload["evidence_ref"], str(evidence_file))
        self.assertEqual(payload["route_progress"], route_progress)
        nav_evidence = payload["nav_results"][0]["evidence"]
        self.assertEqual(nav_evidence["evidence_ref"], str(evidence_file))
        self.assertEqual(nav_evidence["source"], "software_proof")
        self.assertEqual(nav_evidence["route_contract_version"], "fixed_route.v1")
        self.assertEqual(nav_evidence["route_id"], "dock-route")
        self.assertEqual(nav_evidence["checkpoint_id"], "dock-route:002")
        self.assertEqual(nav_evidence["checkpoint"], "cp-2")
        self.assertEqual(nav_evidence["current_index"], 2)
        self.assertEqual(nav_evidence["target"], {"name": "trash_station"})
        self.assertEqual(nav_evidence["failure_code"], "")

    def test_execute_collection_fixed_route_prefers_route_progress_ref_over_empty_status_ref(self):
        with tempfile.TemporaryDirectory() as td:
            status_file = Path(td) / "status.json"
            evidence_file = Path(td) / "route-progress-ref.jsonl"
            route_progress = {
                "checkpoint": "cp-5",
                "current_index": 5,
                "target": {"name": "trash_station"},
                "failure_code": "",
                "evidence_ref": str(evidence_file),
            }
            status_file.write_text(
                json.dumps(
                    {
                        "state": "completed",
                        "evidence_ref": "",
                        "route_file": "/tmp/routes/trash_station.json",
                        "route_progress": route_progress,
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

        self.assertTrue(result.success)
        self.assertEqual(payload["evidence_ref"], str(evidence_file))
        self.assertEqual(payload["result_path"], str(evidence_file))
        self.assertEqual(payload["route_progress"]["evidence_ref"], str(evidence_file))
        self.assertEqual(
            payload["nav_results"][-1]["evidence"]["route_progress"]["evidence_ref"],
            str(evidence_file),
        )
        self.assertEqual(payload["nav_results"][-1]["evidence"]["evidence_ref"], str(evidence_file))

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
