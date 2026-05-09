import unittest
from pathlib import Path
import sys


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from ros2_trashbot_behavior.delivery_state_machine import (
    DeliveryEvent,
    DeliveryState,
    DeliveryStateMachine,
)


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


if __name__ == "__main__":
    unittest.main()
