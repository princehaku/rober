import unittest
from pathlib import Path
import sys


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from ros2_trashbot_behavior.delivery_state_machine import (
    BOUNDED_ROUTE_TERMINAL_RESULT_BRIDGE_PROOF_BOUNDARY,
    BOUNDED_ROUTE_TERMINAL_RESULT_BRIDGE_SCHEMA,
    DeliveryEvent,
    DeliveryState,
    DeliveryStateMachine,
    DELIVERY_STATE_LIVE_SUCCESS_GATE_PROOF_BOUNDARY,
    DELIVERY_STATE_LIVE_SUCCESS_GATE_SCHEMA,
    DELIVERY_STATE_TERMINAL_RECONCILIATION_SCHEMA,
    MOCK_ROUTE_TERMINAL_RESULT_CODE,
    MOCK_ROUTE_TERMINAL_TASK_STATE,
    OPERATOR_DROPOFF_ACCEPTANCE_GATE_PROOF_BOUNDARY,
    OPERATOR_DROPOFF_ACCEPTANCE_GATE_SCHEMA,
    TerminalResultReconciliationError,
)


def terminal_result_source_fixture():
    return {
        "schema": BOUNDED_ROUTE_TERMINAL_RESULT_BRIDGE_SCHEMA,
        "proof_boundary": BOUNDED_ROUTE_TERMINAL_RESULT_BRIDGE_PROOF_BOUNDARY,
        "result_code": MOCK_ROUTE_TERMINAL_RESULT_CODE,
        "terminal_result_state": "terminal_result_recorded",
        "reconciliation_state": "terminal_result_recorded",
        "task_terminal_state": MOCK_ROUTE_TERMINAL_TASK_STATE,
        "terminal_result_type": "delivery_terminal",
        "task_id": "task_o3_28_pose_fixed_route_consumer_20260713_0402",
        "packet_id": "packet_o3_28_pose_same_task_replay_7d57826142b0c79c",
        "route_intent_id": "route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path",
        "route_csv_row_count": 28,
        "path_structured_pose_count": 28,
        "segment_count": 27,
        "delivery_success": False,
        "route_execution_success": False,
        "safe_to_control": False,
        "hil_pass": False,
        "robot_control_executed": False,
        "connects_cloud_production": False,
        "uses_base_uart": False,
        "publishes_cmd_vel": False,
        "calls_base_manual": False,
        "primary_actions_enabled": False,
        "real_world_delivery_proven": False,
        "production_cloud_ready": False,
        "fixed_false_fields": {
            "delivery_success": False,
            "route_execution_success": False,
            "safe_to_control": False,
            "hil_pass": False,
            "robot_control_executed": False,
            "connects_cloud_production": False,
            "uses_base_uart": False,
            "publishes_cmd_vel": False,
            "calls_base_manual": False,
        },
    }


def live_success_gate_fixture() -> dict:
    """构造未来真实 live 证据的最小同任务形状。"""
    identity = {
        "task_id": "task_o3_28_pose_fixed_route_consumer_20260713_0402",
        "robot_id": "robot-live-01",
        "packet_id": "packet_o3_28_pose_same_task_replay_7d57826142b0c79c",
        "route_intent_id": "route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path",
        "terminal_result_id": "terminal_result_live_20260714_0528",
    }
    return {
        "fixture_mode": "future-live-positive",
        "source_mode": "live",
        "identity": dict(identity),
        "live_route_execution_success": True,
        "operator_dropoff_acceptance": True,
        "hil_pass": True,
        "safe_to_control": True,
        "terminal_result_recorded": True,
        "evidence_fresh": True,
        "same_evidence_window": True,
        "route_execution": {
            "task_id": identity["task_id"],
            "robot_id": identity["robot_id"],
            "packet_id": identity["packet_id"],
            "route_intent_id": identity["route_intent_id"],
            "success": True,
        },
        "operator_dropoff_acceptance": {
            "task_id": identity["task_id"],
            "robot_id": identity["robot_id"],
            "accepted": True,
        },
        "hil": {
            "task_id": identity["task_id"],
            "robot_id": identity["robot_id"],
            "pass": True,
        },
        "terminal_result": {
            "task_id": identity["task_id"],
            "robot_id": identity["robot_id"],
            "packet_id": identity["packet_id"],
            "route_intent_id": identity["route_intent_id"],
            "terminal_result_id": identity["terminal_result_id"],
            "recorded": True,
        },
    }


def synthetic_success_like_fixture() -> dict:
    """模拟 unsafe source 携带成功字段，验证 gate 不会误收。"""
    payload = live_success_gate_fixture()
    payload["fixture_mode"] = "synthetic-current-live"
    payload["source_mode"] = "synthetic-current-live"
    return payload


def operator_dropoff_acceptance_gate_fixture() -> dict:
    """构造未来 live operator acceptance 的完整同任务输入。"""
    identity = {
        "task_id": "task_o3_28_pose_fixed_route_consumer_20260713_0402",
        "robot_id": "robot-live-01",
        "packet_id": "packet_o3_28_pose_same_task_replay_7d57826142b0c79c",
        "route_intent_id": "route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path",
        "terminal_result_id": "terminal_result_live_20260714_0729",
    }
    return {
        "fixture_mode": "future-live-positive",
        "source_mode": "live",
        "identity": dict(identity),
        "live_route_execution_success": True,
        "safe_to_control": True,
        "hil_pass": True,
        "terminal_result_recorded": True,
        "evidence_fresh": True,
        "same_evidence_window": True,
        "delivery_success": False,
        "dropoff_success": False,
        "route_execution": {
            "task_id": identity["task_id"],
            "robot_id": identity["robot_id"],
            "packet_id": identity["packet_id"],
            "route_intent_id": identity["route_intent_id"],
            "success": True,
        },
        "operator_dropoff_acceptance": {
            "task_id": identity["task_id"],
            "robot_id": identity["robot_id"],
            "acceptance_id": "operator_acceptance_live_20260714_0729",
            "action_type": "operator_dropoff_acceptance",
            "actor_source_label": "field_operator_live",
            "occurred_at_utc": "2026-07-14T07:29:00Z",
            "safe_evidence_ref": "operator_dropoff_acceptance_live_20260714_0729.json",
            "redaction_status": "passed",
            "accepted": True,
        },
        "hil": {
            "task_id": identity["task_id"],
            "robot_id": identity["robot_id"],
            "pass": True,
        },
        "terminal_result": {
            "task_id": identity["task_id"],
            "robot_id": identity["robot_id"],
            "packet_id": identity["packet_id"],
            "route_intent_id": identity["route_intent_id"],
            "terminal_result_id": identity["terminal_result_id"],
            "recorded": True,
        },
    }


def synthetic_operator_dropoff_acceptance_fixture() -> dict:
    """构造当前 sprint synthetic 输入，所有 live/safety 条件保持 false。"""
    payload = operator_dropoff_acceptance_gate_fixture()
    payload["fixture_mode"] = "synthetic"
    payload["source_mode"] = "synthetic"
    payload["live_route_execution_success"] = False
    payload["safe_to_control"] = False
    payload["hil_pass"] = False
    payload["terminal_result_recorded"] = False
    payload["route_execution"]["success"] = False
    payload["operator_dropoff_acceptance"]["accepted"] = False
    payload["operator_dropoff_acceptance"]["acceptance_id"] = "synthetic_operator_acceptance_fixture"
    payload["operator_dropoff_acceptance"]["safe_evidence_ref"] = "operator_dropoff_acceptance_synthetic_fixture.json"
    payload["hil"]["pass"] = False
    payload["terminal_result"]["recorded"] = False
    return payload


class DeliveryStateMachineTest(unittest.TestCase):
    def test_successful_delivery_returns_to_idle(self):
        machine = DeliveryStateMachine()
        machine.confirm_loaded("bin_a")
        machine.start_delivery()
        machine.navigation_succeeded()
        machine.dropoff_confirmed()
        machine.return_succeeded()

        self.assertEqual(machine.state, DeliveryState.IDLE)
        self.assertEqual(machine.error_message, "")

    def test_missing_target_enters_error(self):
        machine = DeliveryStateMachine()
        machine.confirm_loaded("")

        self.assertEqual(machine.state, DeliveryState.ERROR)
        self.assertEqual(machine.error_message, "delivery target is required")

    def test_confirm_loaded_and_start_delivery_are_separate_steps(self):
        machine = DeliveryStateMachine()

        machine.confirm_loaded("bin_a")

        self.assertEqual(machine.state, DeliveryState.LOADED)
        machine.start_delivery()
        self.assertEqual(machine.state, DeliveryState.DELIVERING)

    def test_invalid_public_transition_enters_error(self):
        machine = DeliveryStateMachine()

        machine.navigation_succeeded()

        self.assertEqual(machine.state, DeliveryState.ERROR)
        self.assertEqual(machine.events[-1].event.value, "invalid_transition")
        self.assertIn("navigation_succeeded", machine.error_message)

    def test_navigation_failure_enters_error(self):
        machine = DeliveryStateMachine()
        machine.confirm_loaded("bin_a")
        machine.start_delivery()
        machine.navigation_failed("nav timeout")

        self.assertEqual(machine.state, DeliveryState.ERROR)
        self.assertEqual(machine.error_message, "nav timeout")

    def test_timeout_enters_error_with_timeout_event(self):
        machine = DeliveryStateMachine()
        machine.confirm_loaded("bin_a")
        machine.start_delivery()

        machine.timed_out("navigation timed out")

        self.assertEqual(machine.state, DeliveryState.ERROR)
        self.assertEqual(machine.error_message, "navigation timed out")
        self.assertEqual(machine.events[-1].event, DeliveryEvent.TIMED_OUT)

    def test_elevator_phases_record_without_leaving_delivery(self):
        machine = DeliveryStateMachine()
        machine.confirm_loaded("bin_a")
        machine.start_delivery()

        machine.elevator_phase("approaching_elevator")
        machine.elevator_phase("waiting_elevator_open")
        machine.elevator_completed()

        self.assertEqual(machine.state, DeliveryState.DELIVERING)
        self.assertEqual(machine.error_message, "")
        self.assertEqual(machine.events[-3].event, DeliveryEvent.ELEVATOR_PHASE)
        self.assertEqual(machine.events[-3].message, "approaching_elevator")
        self.assertEqual(machine.events[-1].event, DeliveryEvent.ELEVATOR_COMPLETED)

    def test_elevator_failure_enters_error(self):
        machine = DeliveryStateMachine()
        machine.confirm_loaded("bin_a")
        machine.start_delivery()

        machine.elevator_failed("target floor was not confirmed")

        self.assertEqual(machine.state, DeliveryState.ERROR)
        self.assertEqual(machine.error_message, "target floor was not confirmed")
        self.assertEqual(machine.events[-1].event, DeliveryEvent.ELEVATOR_FAILED)

    def test_dropoff_failure_enters_error(self):
        machine = DeliveryStateMachine()
        machine.confirm_loaded("bin_a")
        machine.start_delivery()
        machine.navigation_succeeded()
        machine.dropoff_failed("operator did not confirm")

        self.assertEqual(machine.state, DeliveryState.ERROR)
        self.assertEqual(machine.error_message, "operator did not confirm")

    def test_cancel_enters_idle_with_cancel_event(self):
        machine = DeliveryStateMachine()
        machine.confirm_loaded("bin_a")
        machine.cancel("user canceled")

        self.assertEqual(machine.state, DeliveryState.IDLE)
        self.assertEqual(machine.events[-1].event, DeliveryEvent.CANCELED)

    def test_cancel_from_idle_is_invalid(self):
        machine = DeliveryStateMachine()

        machine.cancel("nothing to cancel")

        self.assertEqual(machine.state, DeliveryState.ERROR)
        self.assertEqual(machine.events[-1].event.value, "invalid_transition")

    def test_live_success_gate_accepts_complete_live_same_task_evidence(self):
        machine = DeliveryStateMachine()

        summary = machine.delivery_state_live_success_gate(
            live_success_gate_fixture(),
            source_summary_ref="/tmp/live_delivery_success_summary.json",
            generated_at_utc="2026-07-14T05:28:00Z",
        )

        self.assertEqual(DELIVERY_STATE_LIVE_SUCCESS_GATE_SCHEMA, summary["schema"])
        self.assertEqual(DELIVERY_STATE_LIVE_SUCCESS_GATE_PROOF_BOUNDARY, summary["proof_boundary"])
        self.assertTrue(summary["live_success_gate_contract_ready"])
        self.assertTrue(summary["current_live_evidence_observed"])
        self.assertTrue(summary["delivery_success_claimed_by_this_run"])
        self.assertTrue(summary["real_world_delivery_proven"])
        self.assertTrue(summary["safe_to_control"])
        self.assertTrue(summary["hil_pass"])
        self.assertTrue(summary["delivery_success_accepted_for_state_machine"])
        self.assertEqual("accepted_live_delivery_success", summary["acceptance_decision"])
        self.assertEqual(DeliveryState.IDLE, machine.state)
        self.assertEqual(DeliveryEvent.LIVE_SUCCESS_GATE_EVALUATED, machine.events[-1].event)

    def test_live_success_gate_synthetic_current_fixture_is_contract_only(self):
        payload = live_success_gate_fixture()
        payload["fixture_mode"] = "synthetic-current-live"
        payload["source_mode"] = "synthetic-current-live"
        payload["live_route_execution_success"] = False
        payload["operator_dropoff_acceptance"] = False
        payload["hil_pass"] = False
        payload["safe_to_control"] = False
        payload["terminal_result_recorded"] = False
        payload["route_execution"] = {"success": False}
        payload["operator_dropoff_acceptance"] = {"accepted": False}
        payload["hil"] = {"pass": False}
        payload["terminal_result"] = {"recorded": False}

        summary = DeliveryStateMachine().delivery_state_live_success_gate(payload)

        self.assertTrue(summary["live_success_gate_contract_ready"])
        self.assertFalse(summary["current_live_evidence_observed"])
        self.assertFalse(summary["delivery_success_claimed_by_this_run"])
        self.assertFalse(summary["real_world_delivery_proven"])
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["hil_pass"])
        self.assertFalse(summary["delivery_success_accepted_for_state_machine"])
        self.assertIn("current_live_evidence_observed=false", summary["current_run_required_false_invariants"])
        self.assertIn("source_mode_live", summary["missing_live_evidence"])

    def test_live_success_gate_negative_cases_fail_closed(self):
        cases = [
            (
                "missing_live_route_execution",
                lambda payload: payload.update(
                    {
                        "live_route_execution_success": False,
                        "route_execution": {"success": False},
                    }
                ),
                "live_route_execution_success",
            ),
            (
                "missing_operator_dropoff_acceptance",
                lambda payload: payload.update({"operator_dropoff_acceptance": {"accepted": False}}),
                "operator_dropoff_acceptance",
            ),
            (
                "missing_hil",
                lambda payload: payload.update({"hil_pass": False, "hil": {"pass": False}}),
                "hil_pass",
            ),
            (
                "missing_safe_to_control",
                lambda payload: payload.update({"safe_to_control": False}),
                "safe_to_control",
            ),
            (
                "missing_terminal_result",
                lambda payload: payload.update(
                    {
                        "terminal_result_recorded": False,
                        "terminal_result": {"recorded": False},
                    }
                ),
                "terminal_result_recorded",
            ),
            (
                "same_task_identity_mismatch",
                lambda payload: payload["terminal_result"].update({"task_id": "other-task"}),
                "same_task_identity",
            ),
            (
                "mock_source_carrying_success_like_fields",
                lambda payload: payload.update({"source_mode": "mock", "delivery_success": True}),
                "source_mode_live",
            ),
            (
                "stale_historical_evidence",
                lambda payload: payload.update(
                    {
                        "source_mode": "historical",
                        "evidence_fresh": False,
                        "same_evidence_window": False,
                    }
                ),
                "fresh_same_window_evidence",
            ),
            (
                "dangerous_true_unsafe_source",
                lambda payload: payload.update(
                    {
                        "source_mode": "synthetic-current-live",
                        "delivery_success_accepted_for_state_machine": True,
                    }
                ),
                "source_mode_live",
            ),
        ]

        for name, mutate, expected_missing in cases:
            with self.subTest(name=name):
                payload = live_success_gate_fixture()
                mutate(payload)
                summary = DeliveryStateMachine().delivery_state_live_success_gate(payload)

                self.assertFalse(summary["delivery_success_accepted_for_state_machine"])
                self.assertFalse(summary["delivery_success_claimed_by_this_run"])
                self.assertFalse(summary["real_world_delivery_proven"])
                self.assertEqual("blocked_missing_live_success_evidence", summary["acceptance_decision"])
                self.assertIn(expected_missing, summary["missing_live_evidence"])

    def test_live_success_gate_reports_unsafe_true_fields_without_accepting(self):
        payload = synthetic_success_like_fixture()
        payload["delivery_success"] = True
        payload["safe_to_control"] = True
        payload["hil_pass"] = True

        summary = DeliveryStateMachine().delivery_state_live_success_gate(payload)

        self.assertFalse(summary["delivery_success_accepted_for_state_machine"])
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["hil_pass"])
        self.assertIn("delivery_success", summary["dangerous_true_fields"])
        self.assertIn("safe_to_control", summary["dangerous_true_fields"])

    def test_operator_dropoff_acceptance_gate_accepts_future_live_complete_input(self):
        machine = DeliveryStateMachine()

        summary = machine.operator_dropoff_acceptance_gate(
            operator_dropoff_acceptance_gate_fixture(),
            source_summary_ref="/tmp/operator_dropoff_acceptance_live.json",
            generated_at_utc="2026-07-14T07:29:00Z",
        )

        self.assertEqual(OPERATOR_DROPOFF_ACCEPTANCE_GATE_SCHEMA, summary["schema"])
        self.assertEqual(OPERATOR_DROPOFF_ACCEPTANCE_GATE_PROOF_BOUNDARY, summary["proof_boundary"])
        self.assertTrue(summary["operator_dropoff_acceptance_gate_ready"])
        self.assertTrue(summary["operator_dropoff_acceptance_gate_accepted"])
        self.assertTrue(summary["route_execution_success"])
        self.assertTrue(summary["safe_to_control"])
        self.assertTrue(summary["hil_pass"])
        self.assertTrue(summary["operator_dropoff_acceptance"]["accepted"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["delivery_success_accepted_for_state_machine"])
        self.assertEqual(
            "accepted_operator_dropoff_acceptance_for_live_success_gate",
            summary["acceptance_decision"],
        )
        self.assertEqual(
            DeliveryEvent.OPERATOR_DROPOFF_ACCEPTANCE_GATE_EVALUATED,
            machine.events[-1].event,
        )

    def test_operator_dropoff_acceptance_gate_output_can_feed_live_success_gate(self):
        operator_summary = DeliveryStateMachine().operator_dropoff_acceptance_gate(
            operator_dropoff_acceptance_gate_fixture()
        )

        live_summary = DeliveryStateMachine().delivery_state_live_success_gate(operator_summary)

        self.assertTrue(operator_summary["operator_dropoff_acceptance_gate_accepted"])
        self.assertTrue(live_summary["delivery_success_accepted_for_state_machine"])
        self.assertEqual("accepted_live_delivery_success", live_summary["acceptance_decision"])

    def test_operator_dropoff_acceptance_gate_synthetic_fixture_fails_closed(self):
        summary = DeliveryStateMachine().operator_dropoff_acceptance_gate(
            synthetic_operator_dropoff_acceptance_fixture()
        )

        self.assertEqual(OPERATOR_DROPOFF_ACCEPTANCE_GATE_SCHEMA, summary["schema"])
        self.assertTrue(summary["operator_dropoff_acceptance_gate_ready"])
        self.assertFalse(summary["operator_dropoff_acceptance_gate_accepted"])
        self.assertNotEqual("live", summary["source_mode"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["route_execution_success"])
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["hil_pass"])
        self.assertEqual("blocked_missing_live_success_evidence", summary["acceptance_decision"])
        self.assertIn("source_mode_live", summary["missing_live_evidence"])
        self.assertIn("live_route_execution_success", summary["missing_live_evidence"])

    def test_operator_dropoff_acceptance_gate_negative_cases_fail_closed(self):
        cases = [
            (
                "missing_route_execution",
                lambda payload: payload["route_execution"].update({"success": False}),
                "live_route_execution_success",
            ),
            (
                "missing_terminal_result",
                lambda payload: payload["terminal_result"].update({"recorded": False}),
                "terminal_result_recorded",
            ),
            (
                "missing_operator_dropoff_acceptance",
                lambda payload: payload["operator_dropoff_acceptance"].update({"accepted": False}),
                "operator_dropoff_acceptance",
            ),
            (
                "missing_hil",
                lambda payload: payload["hil"].update({"pass": False}),
                "hil_pass",
            ),
            (
                "missing_safe_to_control",
                lambda payload: payload.update({"safe_to_control": False}),
                "safe_to_control",
            ),
            (
                "identity_mismatch",
                lambda payload: payload["operator_dropoff_acceptance"].update({"task_id": "other-task"}),
                "same_task_identity",
            ),
            (
                "stale_evidence",
                lambda payload: payload.update({"evidence_fresh": False, "same_evidence_window": False}),
                "fresh_same_window_evidence",
            ),
            (
                "unsafe_evidence_ref",
                lambda payload: payload["operator_dropoff_acceptance"].update(
                    {"safe_evidence_ref": "https://example.invalid/raw?token=x"}
                ),
                "safe_evidence_ref",
            ),
        ]

        for name, mutate, expected_missing in cases:
            with self.subTest(name=name):
                payload = operator_dropoff_acceptance_gate_fixture()
                mutate(payload)
                summary = DeliveryStateMachine().operator_dropoff_acceptance_gate(payload)

                self.assertFalse(summary["operator_dropoff_acceptance_gate_accepted"])
                self.assertFalse(summary["delivery_success"])
                self.assertFalse(summary["delivery_success_accepted_for_state_machine"])
                self.assertEqual("blocked_missing_live_success_evidence", summary["acceptance_decision"])
                self.assertIn(expected_missing, summary["missing_live_evidence"])

    def test_operator_dropoff_acceptance_gate_rejects_non_live_dangerous_true_fields(self):
        payload = operator_dropoff_acceptance_gate_fixture()
        payload["source_mode"] = "mock"
        payload["delivery_success"] = True
        payload["operator_dropoff_acceptance_gate_accepted"] = True

        summary = DeliveryStateMachine().operator_dropoff_acceptance_gate(payload)

        self.assertFalse(summary["operator_dropoff_acceptance_gate_accepted"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["hil_pass"])
        self.assertIn("delivery_success", summary["dangerous_true_fields"])
        self.assertIn("operator_dropoff_acceptance.accepted", summary["dangerous_true_fields"])

    def test_terminal_result_reconcile_accepts_mock_only_as_fail_closed_error(self):
        machine = DeliveryStateMachine()

        summary = machine.reconcile_terminal_result_summary(
            terminal_result_source_fixture(),
            source_summary_ref="o5_bounded_route_terminal_result_bridge_summary.json",
            generated_at_utc="2026-07-14T04:27:00Z",
        )

        self.assertEqual(DELIVERY_STATE_TERMINAL_RECONCILIATION_SCHEMA, summary["schema"])
        self.assertEqual(MOCK_ROUTE_TERMINAL_RESULT_CODE, summary["result_code"])
        self.assertEqual(DeliveryState.ERROR, machine.state)
        self.assertEqual("error", summary["final_state"])
        self.assertFalse(summary["terminal_result_accepted_for_delivery"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["route_execution_success"])
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["hil_pass"])
        self.assertIn("terminal_result_accepted_for_delivery=false", summary["fixed_false_invariants"])
        self.assertIn("delivery_success=false", summary["fixed_false_invariants"])
        self.assertEqual(DeliveryEvent.TERMINAL_RESULT_RECONCILED, machine.events[-1].event)
        self.assertIn("mock terminal result", summary["error_message"])
        self.assertIn("not delivery success", summary["error_message"])

    def test_terminal_result_reconcile_rejects_dangerous_true_field(self):
        payload = terminal_result_source_fixture()
        payload["safe_to_control"] = True

        with self.assertRaises(TerminalResultReconciliationError):
            DeliveryStateMachine().reconcile_terminal_result_summary(payload)

    def test_terminal_result_reconcile_rejects_unexpected_live_success_state(self):
        payload = terminal_result_source_fixture()
        payload["result_code"] = "live_route_execution_delivery_success"

        with self.assertRaises(TerminalResultReconciliationError):
            DeliveryStateMachine().reconcile_terminal_result_summary(payload)


if __name__ == "__main__":
    unittest.main()
