import threading
import time
import unittest

from ros2_trashbot_behavior.dropoff_confirmation import DropoffConfirmationGate


class DropoffConfirmationGateTest(unittest.TestCase):
    def test_confirmed_dropoff_returns_success(self):
        gate = DropoffConfirmationGate()
        gate.begin("task-1")

        def confirm_later():
            time.sleep(0.02)
            gate.confirm(True, "/trashbot/confirm_dropoff", "confirmed")

        thread = threading.Thread(target=confirm_later)
        thread.start()
        result = gate.wait(1.0, lambda: False)
        thread.join()

        self.assertTrue(result["success"])
        self.assertEqual(result["result_code"], "manual_confirmed")
        self.assertEqual(result["source"], "/trashbot/confirm_dropoff")

    def test_rejected_dropoff_returns_failure(self):
        gate = DropoffConfirmationGate()
        gate.begin("task-1")
        accepted, _message = gate.confirm(False, "/trashbot/confirm_dropoff", "rejected")

        result = gate.wait(1.0, lambda: False)

        self.assertTrue(accepted)
        self.assertFalse(result["success"])
        self.assertEqual(result["result_code"], "manual_rejected")

    def test_timeout_is_failure_not_success(self):
        gate = DropoffConfirmationGate()
        gate.begin("task-1")

        result = gate.wait(0.01, lambda: False)

        self.assertFalse(result["success"])
        self.assertEqual(result["result_code"], "manual_confirm_timeout")

    def test_confirm_without_pending_task_is_rejected(self):
        gate = DropoffConfirmationGate()

        accepted, message = gate.confirm(True, "/trashbot/confirm_dropoff")

        self.assertFalse(accepted)
        self.assertIn("no dropoff confirmation is pending", message)


if __name__ == "__main__":
    unittest.main()
