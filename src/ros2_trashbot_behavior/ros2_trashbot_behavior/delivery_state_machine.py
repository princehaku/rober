from dataclasses import dataclass, field
from enum import Enum
import time


class DeliveryState(Enum):
    IDLE = "idle"
    LOADED = "loaded"
    DELIVERING = "delivering"
    DROPOFF = "dropoff"
    RETURNING = "returning"
    ERROR = "error"


class DeliveryEvent(Enum):
    TASK_LOADED = "task_loaded"
    DELIVERY_STARTED = "delivery_started"
    NAVIGATION_SUCCEEDED = "navigation_succeeded"
    NAVIGATION_FAILED = "navigation_failed"
    DROPOFF_CONFIRMED = "dropoff_confirmed"
    DROPOFF_FAILED = "dropoff_failed"
    RETURN_SUCCEEDED = "return_succeeded"
    RETURN_FAILED = "return_failed"
    CANCELED = "canceled"
    INVALID_TRANSITION = "invalid_transition"


@dataclass
class StateTransition:
    timestamp: float
    event: DeliveryEvent
    from_state: DeliveryState
    to_state: DeliveryState
    message: str = ""


@dataclass
class DeliveryStateMachine:
    state: DeliveryState = DeliveryState.IDLE
    target: str = ""
    error_message: str = ""
    events: list[StateTransition] = field(default_factory=list)

    def _transition(self, event: DeliveryEvent, to_state: DeliveryState, message: str = ""):
        previous = self.state
        self.state = to_state
        self.events.append(StateTransition(time.time(), event, previous, to_state, message))

    def _invalid_transition(self, event: DeliveryEvent, allowed: tuple[DeliveryState, ...]):
        allowed_names = ", ".join(state.value for state in allowed)
        self.error_message = (
            f"invalid transition {event.value} from {self.state.value}; "
            f"expected one of: {allowed_names}"
        )
        self._transition(DeliveryEvent.INVALID_TRANSITION, DeliveryState.ERROR, self.error_message)
        return False

    def _require_state(self, event: DeliveryEvent, *allowed: DeliveryState):
        if self.state not in allowed:
            return self._invalid_transition(event, allowed)
        return True

    def confirm_loaded(self, target: str):
        if not self._require_state(DeliveryEvent.TASK_LOADED, DeliveryState.IDLE):
            return
        self.target = target.strip()
        self.error_message = ""
        if not self.target:
            self.error_message = "delivery target is required"
            self._transition(DeliveryEvent.TASK_LOADED, DeliveryState.ERROR, self.error_message)
            return
        self._transition(DeliveryEvent.TASK_LOADED, DeliveryState.LOADED, self.target)

    def start_delivery(self):
        if not self._require_state(DeliveryEvent.DELIVERY_STARTED, DeliveryState.LOADED):
            return
        self._transition(DeliveryEvent.DELIVERY_STARTED, DeliveryState.DELIVERING, self.target)

    def start_loaded_task(self, target: str):
        self.confirm_loaded(target)
        if self.state == DeliveryState.LOADED:
            self.start_delivery()

    def navigation_succeeded(self):
        if not self._require_state(DeliveryEvent.NAVIGATION_SUCCEEDED, DeliveryState.DELIVERING):
            return
        self._transition(DeliveryEvent.NAVIGATION_SUCCEEDED, DeliveryState.DROPOFF)

    def navigation_failed(self, message: str):
        if not self._require_state(DeliveryEvent.NAVIGATION_FAILED, DeliveryState.DELIVERING):
            return
        self.error_message = message or "navigation failed"
        self._transition(DeliveryEvent.NAVIGATION_FAILED, DeliveryState.ERROR, self.error_message)

    def dropoff_confirmed(self):
        if not self._require_state(DeliveryEvent.DROPOFF_CONFIRMED, DeliveryState.DROPOFF):
            return
        self._transition(DeliveryEvent.DROPOFF_CONFIRMED, DeliveryState.RETURNING)

    def dropoff_failed(self, message: str):
        if not self._require_state(DeliveryEvent.DROPOFF_FAILED, DeliveryState.DROPOFF):
            return
        self.error_message = message or "dropoff failed"
        self._transition(DeliveryEvent.DROPOFF_FAILED, DeliveryState.ERROR, self.error_message)

    def return_succeeded(self):
        if not self._require_state(DeliveryEvent.RETURN_SUCCEEDED, DeliveryState.RETURNING):
            return
        self._transition(DeliveryEvent.RETURN_SUCCEEDED, DeliveryState.IDLE)

    def return_failed(self, message: str):
        if not self._require_state(DeliveryEvent.RETURN_FAILED, DeliveryState.RETURNING):
            return
        self.error_message = message or "return failed"
        self._transition(DeliveryEvent.RETURN_FAILED, DeliveryState.ERROR, self.error_message)

    def cancel(self, message: str):
        if not self._require_state(
            DeliveryEvent.CANCELED,
            DeliveryState.LOADED,
            DeliveryState.DELIVERING,
            DeliveryState.DROPOFF,
            DeliveryState.RETURNING,
        ):
            return
        self._transition(DeliveryEvent.CANCELED, DeliveryState.IDLE, message)
