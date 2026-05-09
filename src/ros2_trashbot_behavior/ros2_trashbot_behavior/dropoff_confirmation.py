import threading
import time


class DropoffConfirmationGate:
    """Thread-safe gate for an external dropoff confirmation service."""

    def __init__(self):
        self._condition = threading.Condition()
        self._pending_task_id = ""
        self._accepted = None
        self._source = ""
        self._message = ""

    def begin(self, task_id: str):
        with self._condition:
            self._pending_task_id = task_id
            self._accepted = None
            self._source = ""
            self._message = ""
            self._condition.notify_all()

    def clear(self):
        with self._condition:
            self._pending_task_id = ""
            self._accepted = None
            self._source = ""
            self._message = ""
            self._condition.notify_all()

    def confirm(self, accepted: bool, source: str, message: str = ""):
        with self._condition:
            if not self._pending_task_id:
                return False, "no dropoff confirmation is pending"
            self._accepted = bool(accepted)
            self._source = source
            self._message = message
            self._condition.notify_all()
            if accepted:
                return True, f"dropoff confirmed by {source}"
            return True, f"dropoff rejected by {source}"

    def wait(self, timeout_sec: float, cancel_requested):
        start = time.monotonic()
        deadline = start + max(0.0, float(timeout_sec))
        with self._condition:
            while self._accepted is None:
                if cancel_requested():
                    return {
                        "success": False,
                        "result_code": "canceled",
                        "message": "dropoff canceled",
                        "source": self._source,
                        "elapsed_sec": time.monotonic() - start,
                    }
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return {
                        "success": False,
                        "result_code": "manual_confirm_timeout",
                        "message": "dropoff confirmation timed out",
                        "source": self._source,
                        "elapsed_sec": time.monotonic() - start,
                    }
                self._condition.wait(min(0.1, remaining))
            accepted = self._accepted
            source = self._source
            message = self._message

        return {
            "success": accepted,
            "result_code": "manual_confirmed" if accepted else "manual_rejected",
            "message": message or (
                f"dropoff confirmed by {source}" if accepted else f"dropoff rejected by {source}"
            ),
            "source": source,
            "elapsed_sec": time.monotonic() - start,
        }
