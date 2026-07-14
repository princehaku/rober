from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import time
from typing import Any


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
    TIMED_OUT = "timed_out"
    CANCELED = "canceled"
    ELEVATOR_PHASE = "elevator_phase"
    ELEVATOR_FAILED = "elevator_failed"
    ELEVATOR_COMPLETED = "elevator_completed"
    INVALID_TRANSITION = "invalid_transition"
    TERMINAL_RESULT_RECONCILED = "terminal_result_reconciled"
    LIVE_SUCCESS_GATE_EVALUATED = "delivery_state_live_success_gate"
    OPERATOR_DROPOFF_ACCEPTANCE_GATE_EVALUATED = "operator_dropoff_acceptance_gate"
    NAV_FAIL = "NAV_FAIL"
    NAV_TIMEOUT = "NAV_TIMEOUT"
    TASK_CANCEL = "TASK_CANCEL"


DELIVERY_STATE_TERMINAL_RECONCILIATION_SCHEMA = "trashbot.o5.delivery_state_terminal_reconciliation.v1"
DELIVERY_STATE_TERMINAL_RECONCILIATION_PROOF_BOUNDARY = (
    "software_proof_o5_delivery_state_terminal_reconciliation_only"
)
BOUNDED_ROUTE_TERMINAL_RESULT_BRIDGE_SCHEMA = "trashbot.o5.bounded_route_terminal_result_bridge.v1"
BOUNDED_ROUTE_TERMINAL_RESULT_BRIDGE_PROOF_BOUNDARY = (
    "software_proof_o5_bounded_route_terminal_result_bridge_only"
)
MOCK_ROUTE_TERMINAL_RESULT_CODE = "mock_route_execution_completed_not_live_delivery"
MOCK_ROUTE_TERMINAL_TASK_STATE = "mock_route_execution_completed_not_live_route_execution"
TERMINAL_RESULT_RECORDED_STATE = "terminal_result_recorded"
TERMINAL_RECONCILIATION_STATUS = "fail_closed_mock_terminal_result_not_delivery"

TERMINAL_RECONCILIATION_REQUIRED_IDENTITY_FIELDS = (
    "task_id",
    "packet_id",
    "route_intent_id",
)

TERMINAL_RECONCILIATION_REQUIRED_FALSE_FIELDS = (
    "delivery_success",
    "route_execution_success",
    "safe_to_control",
    "hil_pass",
    "robot_control_executed",
    "connects_cloud_production",
    "uses_base_uart",
    "publishes_cmd_vel",
    "calls_base_manual",
    "primary_actions_enabled",
    "real_world_delivery_proven",
    "production_cloud_ready",
)

TERMINAL_RECONCILIATION_FIXED_FALSE_FIELDS = (
    "terminal_result_accepted_for_delivery",
    "dropoff_success",
    *TERMINAL_RECONCILIATION_REQUIRED_FALSE_FIELDS,
)

TERMINAL_RECONCILIATION_FALSE_INVARIANTS = tuple(
    f"{key}=false" for key in TERMINAL_RECONCILIATION_FIXED_FALSE_FIELDS
)

TERMINAL_RECONCILIATION_REJECTED_CLAIMS = (
    "production cloud",
    "public https tls",
    "real 4g sim",
    "live route execution",
    "route execution success",
    "delivery success",
    "dropoff success",
    "delivery operator acceptance",
    "hil pass",
    "safe to control",
    "robot control execution",
)

DELIVERY_STATE_LIVE_SUCCESS_GATE_SCHEMA = "trashbot.o5.delivery_state_live_success_gate.v1"
DELIVERY_STATE_LIVE_SUCCESS_GATE_PROOF_BOUNDARY = (
    "software_proof_o5_delivery_state_live_success_gate_only"
)
OPERATOR_DROPOFF_ACCEPTANCE_GATE_SCHEMA = "trashbot.o5.operator_dropoff_acceptance_gate.v1"
OPERATOR_DROPOFF_ACCEPTANCE_GATE_PROOF_BOUNDARY = (
    "software_proof_o5_operator_dropoff_acceptance_gate_only"
)

LIVE_SUCCESS_GATE_LIVE_SOURCE_MODES = (
    "live",
    "field-live",
    "production-live",
)

LIVE_SUCCESS_GATE_REQUIRED_IDENTITY_FIELDS = (
    "task_id",
    "robot_id",
    "packet_id",
    "route_intent_id",
    "terminal_result_id",
)

LIVE_SUCCESS_GATE_REQUIRED_EVIDENCE = (
    "source_mode_live",
    "same_task_identity",
    "live_route_execution_success",
    "operator_dropoff_acceptance",
    "hil_pass",
    "safe_to_control",
    "terminal_result_recorded",
    "fresh_same_window_evidence",
)

LIVE_SUCCESS_GATE_DANGEROUS_TRUE_FIELDS = (
    "delivery_success",
    "dropoff_success",
    "route_execution_success",
    "live_route_execution_success",
    "operator_dropoff_acceptance",
    "hil_pass",
    "safe_to_control",
    "terminal_result_recorded",
    "real_world_delivery_proven",
    "delivery_success_accepted_for_state_machine",
)

LIVE_SUCCESS_GATE_CURRENT_RUN_FALSE_INVARIANTS = (
    "current_live_evidence_observed=false",
    "delivery_success_claimed_by_this_run=false",
    "real_world_delivery_proven=false",
    "safe_to_control=false",
    "hil_pass=false",
    "delivery_success_accepted_for_state_machine=false",
)

OPERATOR_DROPOFF_ACCEPTANCE_REQUIRED_EVIDENCE = (
    "source_mode_live",
    "same_task_identity",
    "terminal_result_recorded",
    "live_route_execution_success",
    "operator_dropoff_acceptance",
    "hil_pass",
    "safe_to_control",
    "fresh_same_window_evidence",
    "safe_evidence_ref",
)

OPERATOR_DROPOFF_ACCEPTANCE_DANGEROUS_TRUE_FIELDS = (
    "delivery_success",
    "dropoff_success",
    "route_execution_success",
    "live_route_execution_success",
    "operator_dropoff_acceptance_gate_accepted",
    "hil_pass",
    "safe_to_control",
    "terminal_result_recorded",
    "real_world_delivery_proven",
    "delivery_success_accepted_for_state_machine",
)

OPERATOR_DROPOFF_ACCEPTANCE_CURRENT_RUN_FALSE_INVARIANTS = (
    "delivery_success=false",
    "route_execution_success=false",
    "safe_to_control=false",
    "hil_pass=false",
    "operator_dropoff_acceptance_gate_accepted=false",
    "delivery_success_accepted_for_state_machine=false",
)

SAFE_EVIDENCE_REF_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
)
UNSAFE_EVIDENCE_REF_TOKENS = (
    "://",
    "token",
    "bearer",
    "authorization",
    "cookie",
    "secret",
    "traceback",
)


class TerminalResultReconciliationError(ValueError):
    """terminal result 输入不能安全解释为交付状态时抛出。"""


def _utc_now_iso() -> str:
    """统一使用 UTC 秒级时间，便于离线 artifact 稳定复核。"""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _require_equal(source: dict[str, Any], key: str, expected: Any) -> None:
    """关键字段必须精确匹配，避免把相邻 sprint 的材料错接为交付证据。"""
    actual = source.get(key)
    if actual != expected:
        raise TerminalResultReconciliationError(f"source.{key} expected {expected!r}, got {actual!r}")


def _require_false(source: dict[str, Any], key: str, label: str = "source") -> None:
    """安全字段必须是布尔 false，缺失或字符串 false 都按 fail closed 处理。"""
    actual = source.get(key)
    if actual is not False:
        raise TerminalResultReconciliationError(f"{label}.{key} must be false")


def _require_identity(source: dict[str, Any], key: str) -> str:
    """任务身份必须是非空字符串，否则 summary 不能绑定到同一条路线材料。"""
    actual = source.get(key)
    if not isinstance(actual, str) or not actual.strip():
        raise TerminalResultReconciliationError(f"source.{key} is required")
    return actual.strip()


def _normalize_source_mode(value: Any) -> str:
    """把来源模式规整成短枚举，防止大小写或下划线绕过 live gate。"""
    if not isinstance(value, str):
        return ""
    return value.strip().lower().replace("_", "-")


def _optional_identity_value(source: dict[str, Any], key: str) -> str:
    """live gate 用空字符串表示缺失身份，便于 summary 解释缺哪个字段。"""
    actual = source.get(key)
    if not isinstance(actual, str) or not actual.strip():
        return ""
    return actual.strip()


def _nested_dict(source: dict[str, Any], key: str) -> dict[str, Any]:
    """嵌套 evidence 不是 object 时按空证据处理，保持 fail-closed 输出。"""
    value = source.get(key)
    if isinstance(value, dict):
        return value
    return {}


def _strict_true(source: dict[str, Any], key: str) -> bool:
    """只接受布尔 True；字符串 true 或数字 1 都不能进入成功路径。"""
    return source.get(key) is True


def _field_true(source: dict[str, Any], key: str, section: dict[str, Any], section_key: str) -> bool:
    """同时支持顶层字段和嵌套字段，但两者都必须是严格布尔 True。"""
    return _strict_true(source, key) or _strict_true(section, section_key)


def _live_success_gate_identity(source: dict[str, Any]) -> tuple[dict[str, str], list[str]]:
    """抽取同任务身份；缺失字段留在 missing 列表而不是抛异常。"""
    identity_source = _nested_dict(source, "identity") or source
    identity = {
        key: _optional_identity_value(identity_source, key)
        for key in LIVE_SUCCESS_GATE_REQUIRED_IDENTITY_FIELDS
    }
    missing = [key for key, value in identity.items() if not value]
    return identity, missing


def _live_success_gate_identity_mismatches(
    source: dict[str, Any],
    identity: dict[str, str],
) -> list[str]:
    """要求 route、operator、HIL 和 terminal result 都绑定同一 task/window。"""
    mismatches: list[str] = []
    section_fields = {
        "route_execution": ("task_id", "robot_id", "packet_id", "route_intent_id"),
        "operator_dropoff_acceptance": ("task_id", "robot_id"),
        "hil": ("task_id", "robot_id"),
        "terminal_result": (
            "task_id",
            "robot_id",
            "packet_id",
            "route_intent_id",
            "terminal_result_id",
        ),
    }
    for section_name, fields in section_fields.items():
        section = _nested_dict(source, section_name)
        for field_name in fields:
            expected = identity.get(field_name, "")
            observed = _optional_identity_value(section, field_name)
            # 缺失的 section 身份会在对应 evidence 缺失时被拦截；有值但漂移才单独报 mismatch。
            if observed and expected and observed != expected:
                mismatches.append(f"{section_name}.{field_name}")
    return mismatches


def _dangerous_true_fields_for_source(source: dict[str, Any], source_mode_live: bool) -> list[str]:
    """非 live 来源携带成功/安全 true 时必须显式列出，避免被消费方误读。"""
    if source_mode_live:
        return []
    return [
        key
        for key in LIVE_SUCCESS_GATE_DANGEROUS_TRUE_FIELDS
        if source.get(key) is True
    ]


def _safe_text_value(source: dict[str, Any], key: str) -> str:
    """只保留单行短文本；空值让上层按缺失证据 fail closed。"""
    actual = source.get(key)
    if not isinstance(actual, str):
        return ""
    normalized = actual.strip()
    if not normalized or any(ch in normalized for ch in ("\n", "\r", "\t")):
        return ""
    return normalized


def _safe_evidence_ref(section: dict[str, Any]) -> tuple[str, list[str]]:
    """operator 证据引用只能是安全 basename，不能携带 URL、路径或凭证词。"""
    value = section.get("safe_evidence_ref", section.get("evidence_ref", ""))
    if not isinstance(value, str) or not value.strip():
        return "", ["safe_evidence_ref_missing"]

    candidate = value.strip()
    lowered = candidate.lower()
    reasons: list[str] = []
    if "/" in candidate or "\\" in candidate or candidate in (".", "..") or candidate.startswith("."):
        reasons.append("safe_evidence_ref_not_basename")
    if any(token in lowered for token in UNSAFE_EVIDENCE_REF_TOKENS):
        reasons.append("safe_evidence_ref_sensitive_token")
    if any(ch not in SAFE_EVIDENCE_REF_CHARS for ch in candidate):
        reasons.append("safe_evidence_ref_unsafe_chars")
    return (candidate if not reasons else ""), reasons


def _operator_gate_dangerous_true_fields(
    source: dict[str, Any],
    source_mode_live: bool,
) -> list[str]:
    """非 live 输入不能藏任何成功、HIL 或 safe-to-control true 值。"""
    if source_mode_live:
        return []

    dangerous = [
        key
        for key in OPERATOR_DROPOFF_ACCEPTANCE_DANGEROUS_TRUE_FIELDS
        if source.get(key) is True
    ]
    nested_true_fields = {
        "route_execution": "success",
        "operator_dropoff_acceptance": "accepted",
        "hil": "pass",
        "terminal_result": "recorded",
    }
    for section_name, field_name in nested_true_fields.items():
        if _strict_true(_nested_dict(source, section_name), field_name):
            dangerous.append(f"{section_name}.{field_name}")
    return dangerous


def _source_ref(source_summary_ref: str) -> str:
    """artifact 只保留 basename，避免把本地绝对路径扩散到 sprint 证据。"""
    return source_summary_ref.rsplit("/", 1)[-1]


def validate_delivery_terminal_result_source(source: dict[str, Any]) -> dict[str, str]:
    """只接受 00:24 O5 mock terminal-result bridge 的安全摘要。"""
    if not isinstance(source, dict):
        raise TerminalResultReconciliationError("source summary must be a JSON object")

    _require_equal(source, "schema", BOUNDED_ROUTE_TERMINAL_RESULT_BRIDGE_SCHEMA)
    _require_equal(source, "proof_boundary", BOUNDED_ROUTE_TERMINAL_RESULT_BRIDGE_PROOF_BOUNDARY)
    _require_equal(source, "result_code", MOCK_ROUTE_TERMINAL_RESULT_CODE)
    _require_equal(source, "terminal_result_state", TERMINAL_RESULT_RECORDED_STATE)
    _require_equal(source, "reconciliation_state", TERMINAL_RESULT_RECORDED_STATE)
    _require_equal(source, "task_terminal_state", MOCK_ROUTE_TERMINAL_TASK_STATE)
    _require_equal(source, "terminal_result_type", "delivery_terminal")

    identity = {
        key: _require_identity(source, key) for key in TERMINAL_RECONCILIATION_REQUIRED_IDENTITY_FIELDS
    }

    # 顶层和 fixed_false_fields 都要校验，防止危险 true 字段藏在 readback 摘要里。
    for key in TERMINAL_RECONCILIATION_REQUIRED_FALSE_FIELDS:
        _require_false(source, key)
    fixed_false_fields = source.get("fixed_false_fields")
    if not isinstance(fixed_false_fields, dict):
        raise TerminalResultReconciliationError("source.fixed_false_fields must be an object")
    for key in (
        "delivery_success",
        "route_execution_success",
        "safe_to_control",
        "hil_pass",
        "robot_control_executed",
        "connects_cloud_production",
        "uses_base_uart",
        "publishes_cmd_vel",
        "calls_base_manual",
    ):
        _require_false(fixed_false_fields, key, "source.fixed_false_fields")

    return identity


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
    failure_code: str = ""
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
        self.failure_code = "INVALID_TRANSITION"
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

    def navigation_failed(self, message: str, failure_code: str = "NAV_FAIL"):
        if not self._require_state(DeliveryEvent.NAVIGATION_FAILED, DeliveryState.DELIVERING):
            return
        self.failure_code = failure_code
        self.error_message = message or "navigation failed"
        self._transition(DeliveryEvent.NAVIGATION_FAILED, DeliveryState.ERROR, message)

    def elevator_phase(self, phase: str, message: str = ""):
        if not self._require_state(DeliveryEvent.ELEVATOR_PHASE, DeliveryState.DELIVERING):
            return
        phase = (phase or "").strip()
        if not phase:
            self.error_message = "elevator phase is required"
            self._transition(DeliveryEvent.ELEVATOR_FAILED, DeliveryState.ERROR, self.error_message)
            return
        # Keep the main delivery state in DELIVERING while recording the finer
        # grained elevator dry-run phase in the transition message for replay.
        detail = message or phase
        self._transition(DeliveryEvent.ELEVATOR_PHASE, DeliveryState.DELIVERING, detail)

    def elevator_failed(self, reason: str):
        if not self._require_state(DeliveryEvent.ELEVATOR_FAILED, DeliveryState.DELIVERING):
            return
        self.error_message = reason or "elevator assisted delivery failed"
        self._transition(DeliveryEvent.ELEVATOR_FAILED, DeliveryState.ERROR, self.error_message)

    def elevator_completed(self, message: str = "resume delivery"):
        if not self._require_state(DeliveryEvent.ELEVATOR_COMPLETED, DeliveryState.DELIVERING):
            return
        self._transition(DeliveryEvent.ELEVATOR_COMPLETED, DeliveryState.DELIVERING, message)

    def dropoff_confirmed(self):
        if not self._require_state(DeliveryEvent.DROPOFF_CONFIRMED, DeliveryState.DROPOFF):
            return
        self._transition(DeliveryEvent.DROPOFF_CONFIRMED, DeliveryState.RETURNING)

    def dropoff_failed(self, message: str):
        if not self._require_state(DeliveryEvent.DROPOFF_FAILED, DeliveryState.DROPOFF):
            return
        self.failure_code = "dropoff_failed"
        self.error_message = message or "dropoff failed"
        self._transition(DeliveryEvent.DROPOFF_FAILED, DeliveryState.ERROR, self.error_message)

    def return_succeeded(self):
        if not self._require_state(DeliveryEvent.RETURN_SUCCEEDED, DeliveryState.RETURNING):
            return
        self._transition(DeliveryEvent.RETURN_SUCCEEDED, DeliveryState.IDLE)

    def return_failed(self, message: str):
        if not self._require_state(DeliveryEvent.RETURN_FAILED, DeliveryState.RETURNING):
            return
        self.failure_code = "NAV_FAIL"
        self.error_message = message or "return failed"
        self._transition(DeliveryEvent.RETURN_FAILED, DeliveryState.ERROR, self.error_message)

    def timed_out(self, message: str, failure_code: str = "NAV_TIMEOUT"):
        if not self._require_state(
            DeliveryEvent.TIMED_OUT,
            DeliveryState.DELIVERING,
            DeliveryState.DROPOFF,
            DeliveryState.RETURNING,
        ):
            return
        self.failure_code = failure_code
        self.error_message = message or "delivery timed out"
        self._transition(DeliveryEvent.TIMED_OUT, DeliveryState.ERROR, message)

    def cancel(self, message: str, failure_code: str = "TASK_CANCEL"):
        if not self._require_state(
            DeliveryEvent.CANCELED,
            DeliveryState.LOADED,
            DeliveryState.DELIVERING,
            DeliveryState.DROPOFF,
            DeliveryState.RETURNING,
        ):
            return
        self.failure_code = failure_code
        self._transition(DeliveryEvent.CANCELED, DeliveryState.IDLE, message)

    def operator_dropoff_acceptance_gate(
        self,
        evidence: dict[str, Any],
        *,
        source_summary_ref: str = "",
        generated_at_utc: str | None = None,
    ) -> dict[str, Any]:
        """评估 operator/user dropoff acceptance 是否可作为 live success 必要输入。"""
        if not isinstance(evidence, dict):
            raise TerminalResultReconciliationError("operator dropoff evidence must be a JSON object")

        generated_at_utc = generated_at_utc or _utc_now_iso()
        raw_source_mode = evidence.get("source_mode", "")
        source_mode = _normalize_source_mode(raw_source_mode)
        source_mode_live = source_mode in LIVE_SUCCESS_GATE_LIVE_SOURCE_MODES

        identity, missing_identity_fields = _live_success_gate_identity(evidence)
        identity_mismatches = _live_success_gate_identity_mismatches(evidence, identity)
        same_task_identity = not missing_identity_fields and not identity_mismatches

        route_execution = _nested_dict(evidence, "route_execution")
        operator_acceptance = _nested_dict(evidence, "operator_dropoff_acceptance")
        hil = _nested_dict(evidence, "hil")
        terminal_result = _nested_dict(evidence, "terminal_result")

        # operator gate 是 live-success 的前置证据入口，所以同任务 section 不能只靠顶层 true 兜底。
        live_route_execution_success = (
            _strict_true(evidence, "live_route_execution_success")
            and _strict_true(route_execution, "success")
        )
        operator_acceptance_recorded = _strict_true(operator_acceptance, "accepted")
        hil_pass_input = _strict_true(evidence, "hil_pass") and _strict_true(hil, "pass")
        safe_to_control_input = _strict_true(evidence, "safe_to_control")
        terminal_result_recorded = (
            _strict_true(evidence, "terminal_result_recorded")
            and _strict_true(terminal_result, "recorded")
        )
        evidence_fresh = _strict_true(evidence, "evidence_fresh")
        same_evidence_window = _strict_true(evidence, "same_evidence_window")
        fresh_same_window_evidence = evidence_fresh and same_evidence_window
        safe_evidence_ref, unsafe_ref_reasons = _safe_evidence_ref(operator_acceptance)

        dangerous_true_fields = _operator_gate_dangerous_true_fields(evidence, source_mode_live)
        missing_live_evidence: list[str] = []
        if not source_mode_live:
            missing_live_evidence.append("source_mode_live")
        if not same_task_identity:
            missing_live_evidence.append("same_task_identity")
        if not terminal_result_recorded:
            missing_live_evidence.append("terminal_result_recorded")
        if not live_route_execution_success:
            missing_live_evidence.append("live_route_execution_success")
        if not operator_acceptance_recorded:
            missing_live_evidence.append("operator_dropoff_acceptance")
        if not hil_pass_input:
            missing_live_evidence.append("hil_pass")
        if not safe_to_control_input:
            missing_live_evidence.append("safe_to_control")
        if not fresh_same_window_evidence:
            missing_live_evidence.append("fresh_same_window_evidence")
        if unsafe_ref_reasons:
            missing_live_evidence.append("safe_evidence_ref")

        blocked_reasons = list(missing_live_evidence)
        blocked_reasons.extend(f"missing_identity.{field}" for field in missing_identity_fields)
        blocked_reasons.extend(f"identity_mismatch.{field}" for field in identity_mismatches)
        blocked_reasons.extend(f"unsafe_evidence_ref.{reason}" for reason in unsafe_ref_reasons)
        blocked_reasons.extend(f"unsafe_source_true_field.{field}" for field in dangerous_true_fields)

        accepted = not blocked_reasons
        # 这个 gate 只产出 operator acceptance 的必要证据；最终 delivery_success 仍交给 live-success gate。
        reported_route_execution_success = (
            source_mode_live and live_route_execution_success and not dangerous_true_fields
        )
        reported_hil_pass = source_mode_live and hil_pass_input and not dangerous_true_fields
        reported_safe_to_control = source_mode_live and safe_to_control_input and not dangerous_true_fields

        if accepted:
            self.failure_code = ""
            self.error_message = ""
            transition_message = "operator dropoff acceptance accepted as live success input"
            self._transition(
                DeliveryEvent.OPERATOR_DROPOFF_ACCEPTANCE_GATE_EVALUATED,
                self.state,
                transition_message,
            )
        else:
            self.failure_code = "OPERATOR_DROPOFF_ACCEPTANCE_GATE_BLOCKED"
            self.error_message = "operator dropoff acceptance gate blocked: " + ", ".join(blocked_reasons)
            self._transition(
                DeliveryEvent.OPERATOR_DROPOFF_ACCEPTANCE_GATE_EVALUATED,
                DeliveryState.ERROR,
                self.error_message,
            )

        acceptance_summary = {
            "task_id": _optional_identity_value(operator_acceptance, "task_id"),
            "robot_id": _optional_identity_value(operator_acceptance, "robot_id"),
            "acceptance_id": _safe_text_value(operator_acceptance, "acceptance_id"),
            "action_type": _safe_text_value(operator_acceptance, "action_type"),
            "actor_source_label": _safe_text_value(operator_acceptance, "actor_source_label"),
            "occurred_at_utc": _safe_text_value(operator_acceptance, "occurred_at_utc"),
            "safe_evidence_ref": safe_evidence_ref,
            "redaction_status": _safe_text_value(operator_acceptance, "redaction_status"),
            "accepted": operator_acceptance_recorded and source_mode_live,
        }

        summary: dict[str, Any] = {
            "schema": OPERATOR_DROPOFF_ACCEPTANCE_GATE_SCHEMA,
            "generated_at_utc": generated_at_utc,
            "owner_role": "robot-software-engineer",
            "proof_boundary": OPERATOR_DROPOFF_ACCEPTANCE_GATE_PROOF_BOUNDARY,
            "proof_boundary_class": "software_proof_o5_operator_acceptance_gate_only",
            "source_summary_ref": _source_ref(source_summary_ref),
            "fixture_mode": evidence.get("fixture_mode", ""),
            "source_mode": raw_source_mode,
            "normalized_source_mode": source_mode,
            "operator_dropoff_acceptance_gate_ready": True,
            "operator_dropoff_acceptance_gate_accepted": accepted,
            "source_mode_live": source_mode_live,
            "current_live_evidence_observed": accepted and source_mode_live and fresh_same_window_evidence,
            "same_task_identity_verified": same_task_identity,
            "terminal_result_recorded": terminal_result_recorded and source_mode_live,
            "live_route_execution_success": reported_route_execution_success,
            "route_execution_success": reported_route_execution_success,
            "operator_dropoff_acceptance_recorded": operator_acceptance_recorded and source_mode_live,
            "operator_dropoff_acceptance": acceptance_summary,
            "evidence_fresh": evidence_fresh,
            "same_evidence_window": same_evidence_window,
            "fresh_same_window_evidence": fresh_same_window_evidence,
            "safe_evidence_ref": safe_evidence_ref,
            "safe_evidence_ref_status": "pass" if safe_evidence_ref else "blocked",
            "delivery_success": False,
            "delivery_success_accepted_for_state_machine": False,
            "delivery_success_candidate_for_live_success_gate": accepted,
            "real_world_delivery_proven": False,
            "safe_to_control": reported_safe_to_control,
            "hil_pass": reported_hil_pass,
            "final_state": self.state.value,
            "failure_code": self.failure_code,
            "error_message": self.error_message,
            "acceptance_decision": (
                "accepted_operator_dropoff_acceptance_for_live_success_gate"
                if accepted
                else "blocked_missing_live_success_evidence"
            ),
            "task_id": identity["task_id"],
            "robot_id": identity["robot_id"],
            "packet_id": identity["packet_id"],
            "route_intent_id": identity["route_intent_id"],
            "terminal_result_id": identity["terminal_result_id"],
            "identity": identity,
            "route_execution": {
                "task_id": _optional_identity_value(route_execution, "task_id"),
                "robot_id": _optional_identity_value(route_execution, "robot_id"),
                "packet_id": _optional_identity_value(route_execution, "packet_id"),
                "route_intent_id": _optional_identity_value(route_execution, "route_intent_id"),
                "success": reported_route_execution_success,
            },
            "hil": {
                "task_id": _optional_identity_value(hil, "task_id"),
                "robot_id": _optional_identity_value(hil, "robot_id"),
                "pass": reported_hil_pass,
            },
            "terminal_result": {
                "task_id": _optional_identity_value(terminal_result, "task_id"),
                "robot_id": _optional_identity_value(terminal_result, "robot_id"),
                "packet_id": _optional_identity_value(terminal_result, "packet_id"),
                "route_intent_id": _optional_identity_value(terminal_result, "route_intent_id"),
                "terminal_result_id": _optional_identity_value(terminal_result, "terminal_result_id"),
                "recorded": terminal_result_recorded and source_mode_live,
            },
            "required_evidence": list(OPERATOR_DROPOFF_ACCEPTANCE_REQUIRED_EVIDENCE),
            "missing_live_evidence": missing_live_evidence,
            "missing_identity_fields": missing_identity_fields,
            "identity_mismatches": identity_mismatches,
            "unsafe_evidence_ref_reasons": unsafe_ref_reasons,
            "dangerous_true_fields": dangerous_true_fields,
            "blocked_reasons": blocked_reasons,
            "current_run_required_false_invariants": list(
                OPERATOR_DROPOFF_ACCEPTANCE_CURRENT_RUN_FALSE_INVARIANTS
            ),
            "next_required_evidence": (
                "feed this gate into delivery_state_live_success_gate only after source_mode=live, "
                "same-task terminal result, live route execution success, operator_dropoff_acceptance, "
                "HIL pass, safe_to_control, and same-window freshness all pass"
            ),
            "state_machine_events": [
                {
                    "event": event.event.value,
                    "from_state": event.from_state.value,
                    "to_state": event.to_state.value,
                    "message": event.message,
                }
                for event in self.events
            ],
            "checks": [
                {
                    "name": "operator_dropoff_acceptance_gate_ready",
                    "status": "pass",
                    "detail": "operator dropoff acceptance evidence can be evaluated independently",
                },
                {
                    "name": "source_mode_live",
                    "status": "pass" if source_mode_live else "blocked",
                    "detail": "source_mode=live, field-live, or production-live is required for positive acceptance",
                },
                {
                    "name": "safe_evidence_ref",
                    "status": "pass" if safe_evidence_ref else "blocked",
                    "detail": "operator evidence ref must be a sanitized basename, not a URL or local path",
                },
                {
                    "name": "delivery_success_not_claimed_here",
                    "status": "pass",
                    "detail": "this gate is necessary input only and keeps delivery_success=false",
                },
            ],
            "rg_acceptance_anchors": [
                "operator_dropoff_acceptance",
                OPERATOR_DROPOFF_ACCEPTANCE_GATE_PROOF_BOUNDARY,
                "delivery_success=false",
                "blocked_missing_live_success_evidence",
                "source_mode=live",
                "safe_to_control",
            ],
        }
        return summary

    def delivery_state_live_success_gate(
        self,
        evidence: dict[str, Any],
        *,
        source_summary_ref: str = "",
        generated_at_utc: str | None = None,
    ) -> dict[str, Any]:
        """评估未来 live delivery success 是否可进入状态机成功语义。"""
        if not isinstance(evidence, dict):
            raise TerminalResultReconciliationError("live success evidence must be a JSON object")

        generated_at_utc = generated_at_utc or _utc_now_iso()
        raw_source_mode = evidence.get("source_mode", "")
        source_mode = _normalize_source_mode(raw_source_mode)
        source_mode_live = source_mode in LIVE_SUCCESS_GATE_LIVE_SOURCE_MODES

        identity, missing_identity_fields = _live_success_gate_identity(evidence)
        identity_mismatches = _live_success_gate_identity_mismatches(evidence, identity)
        same_task_identity = not missing_identity_fields and not identity_mismatches

        route_execution = _nested_dict(evidence, "route_execution")
        operator_acceptance = _nested_dict(evidence, "operator_dropoff_acceptance")
        hil = _nested_dict(evidence, "hil")
        terminal_result = _nested_dict(evidence, "terminal_result")

        live_route_execution_success = _field_true(
            evidence,
            "live_route_execution_success",
            route_execution,
            "success",
        )
        operator_dropoff_acceptance = _field_true(
            evidence,
            "operator_dropoff_acceptance",
            operator_acceptance,
            "accepted",
        )
        hil_pass_input = _field_true(evidence, "hil_pass", hil, "pass")
        safe_to_control_input = _strict_true(evidence, "safe_to_control")
        terminal_result_recorded = _field_true(
            evidence,
            "terminal_result_recorded",
            terminal_result,
            "recorded",
        )
        evidence_fresh = _strict_true(evidence, "evidence_fresh")
        same_evidence_window = _strict_true(evidence, "same_evidence_window")
        fresh_same_window_evidence = evidence_fresh and same_evidence_window

        dangerous_true_fields = _dangerous_true_fields_for_source(evidence, source_mode_live)
        current_live_evidence_observed = source_mode_live and fresh_same_window_evidence

        missing_live_evidence: list[str] = []
        if not source_mode_live:
            missing_live_evidence.append("source_mode_live")
        if not same_task_identity:
            missing_live_evidence.append("same_task_identity")
        if not live_route_execution_success:
            missing_live_evidence.append("live_route_execution_success")
        if not operator_dropoff_acceptance:
            missing_live_evidence.append("operator_dropoff_acceptance")
        if not hil_pass_input:
            missing_live_evidence.append("hil_pass")
        if not safe_to_control_input:
            missing_live_evidence.append("safe_to_control")
        if not terminal_result_recorded:
            missing_live_evidence.append("terminal_result_recorded")
        if not fresh_same_window_evidence:
            missing_live_evidence.append("fresh_same_window_evidence")

        blocked_reasons = list(missing_live_evidence)
        blocked_reasons.extend(f"missing_identity.{field}" for field in missing_identity_fields)
        blocked_reasons.extend(f"identity_mismatch.{field}" for field in identity_mismatches)
        blocked_reasons.extend(f"unsafe_source_true_field.{field}" for field in dangerous_true_fields)

        accepted = not blocked_reasons

        # 非 live 来源即使携带 true 字段，也只能在 blocked_reasons 中暴露，顶层成功/安全字段保持 false。
        reported_hil_pass = accepted or (source_mode_live and hil_pass_input and not dangerous_true_fields)
        reported_safe_to_control = accepted or (
            source_mode_live and safe_to_control_input and not dangerous_true_fields
        )

        if accepted:
            self.failure_code = ""
            self.error_message = ""
            transition_message = "delivery live success accepted by strict evidence gate"
            self._transition(DeliveryEvent.LIVE_SUCCESS_GATE_EVALUATED, DeliveryState.IDLE, transition_message)
        else:
            self.failure_code = "LIVE_SUCCESS_GATE_BLOCKED"
            self.error_message = "delivery live success gate blocked: " + ", ".join(blocked_reasons)
            self._transition(
                DeliveryEvent.LIVE_SUCCESS_GATE_EVALUATED,
                DeliveryState.ERROR,
                self.error_message,
            )

        summary: dict[str, Any] = {
            "schema": DELIVERY_STATE_LIVE_SUCCESS_GATE_SCHEMA,
            "generated_at_utc": generated_at_utc,
            "owner_role": "robot-software-engineer",
            "proof_boundary": DELIVERY_STATE_LIVE_SUCCESS_GATE_PROOF_BOUNDARY,
            "proof_boundary_class": "software_proof_contract_only",
            "source_summary_ref": _source_ref(source_summary_ref),
            "fixture_mode": evidence.get("fixture_mode", ""),
            "source_mode": raw_source_mode,
            "normalized_source_mode": source_mode,
            "live_success_gate_contract_ready": True,
            "source_mode_live": source_mode_live,
            "current_live_evidence_observed": current_live_evidence_observed and accepted,
            "same_task_identity_verified": same_task_identity,
            "live_route_execution_success": live_route_execution_success and source_mode_live,
            "operator_dropoff_acceptance": operator_dropoff_acceptance and source_mode_live,
            "terminal_result_recorded": terminal_result_recorded and source_mode_live,
            "evidence_fresh": evidence_fresh,
            "same_evidence_window": same_evidence_window,
            "fresh_same_window_evidence": fresh_same_window_evidence,
            "delivery_success_claimed_by_this_run": accepted,
            "real_world_delivery_proven": accepted,
            "safe_to_control": reported_safe_to_control,
            "hil_pass": reported_hil_pass,
            "delivery_success_accepted_for_state_machine": accepted,
            "final_state": self.state.value,
            "failure_code": self.failure_code,
            "error_message": self.error_message,
            "acceptance_decision": (
                "accepted_live_delivery_success"
                if accepted
                else "blocked_missing_live_success_evidence"
            ),
            "task_id": identity["task_id"],
            "robot_id": identity["robot_id"],
            "packet_id": identity["packet_id"],
            "route_intent_id": identity["route_intent_id"],
            "terminal_result_id": identity["terminal_result_id"],
            "required_evidence": list(LIVE_SUCCESS_GATE_REQUIRED_EVIDENCE),
            "missing_live_evidence": missing_live_evidence,
            "missing_identity_fields": missing_identity_fields,
            "identity_mismatches": identity_mismatches,
            "dangerous_true_fields": dangerous_true_fields,
            "blocked_reasons": blocked_reasons,
            "current_run_required_false_invariants": list(
                LIVE_SUCCESS_GATE_CURRENT_RUN_FALSE_INVARIANTS
            ),
            "rejected_source_modes": [
                "synthetic-current-live",
                "synthetic",
                "mock",
                "local-replay",
                "historical",
                "readback-only",
                "wrapper-only",
            ],
            "next_required_evidence": (
                "collect same-window live route execution success, operator/dropoff acceptance, "
                "HIL pass, safe-to-control, terminal result record, and same-task identity before "
                "accepting delivery success"
            ),
            "state_machine_events": [
                {
                    "event": event.event.value,
                    "from_state": event.from_state.value,
                    "to_state": event.to_state.value,
                    "message": event.message,
                }
                for event in self.events
            ],
            "checks": [
                {
                    "name": "live_success_gate_contract_ready",
                    "status": "pass",
                    "detail": "delivery_state_live_success_gate contract exists and is evaluated fail-closed",
                },
                {
                    "name": "source_mode_live",
                    "status": "pass" if source_mode_live else "blocked",
                    "detail": "source mode must be live, field-live, or production-live",
                },
                {
                    "name": "same_task_identity",
                    "status": "pass" if same_task_identity else "blocked",
                    "detail": "task, robot, packet, route, and terminal result identity must match",
                },
                {
                    "name": "complete_live_delivery_evidence",
                    "status": "pass" if accepted else "blocked",
                    "detail": (
                        "route execution, operator/dropoff acceptance, HIL, safe-to-control, "
                        "terminal record, and fresh same-window evidence are all required"
                    ),
                },
            ],
            "rg_acceptance_anchors": [
                "delivery_state_live_success_gate",
                DELIVERY_STATE_LIVE_SUCCESS_GATE_PROOF_BOUNDARY,
                "live_success_gate_contract_ready",
                "current_live_evidence_observed=false",
                "delivery_success_claimed_by_this_run=false",
                "real_world_delivery_proven=false",
            ],
        }
        return summary

    def reconcile_terminal_result_summary(
        self,
        source: dict[str, Any],
        *,
        source_summary_ref: str = "",
        generated_at_utc: str | None = None,
    ) -> dict[str, Any]:
        """把本地/mock terminal result 离线解释成 fail-closed 交付状态。"""
        identity = validate_delivery_terminal_result_source(source)
        generated_at_utc = generated_at_utc or _utc_now_iso()

        # 这里故意进入 ERROR：mock terminal result 只能证明本地对账，不是投放/送达完成。
        self.failure_code = "MOCK_TERMINAL_RESULT_NOT_DELIVERY"
        self.error_message = (
            "mock terminal result is not delivery success, dropoff success, "
            "live route execution, operator acceptance, HIL, or safe-to-control"
        )
        self._transition(
            DeliveryEvent.TERMINAL_RESULT_RECONCILED,
            DeliveryState.ERROR,
            self.error_message,
        )

        # summary 顶层重复固定 false 字段，便于 Product gate 用简单断言 fail closed。
        summary: dict[str, Any] = {
            "schema": DELIVERY_STATE_TERMINAL_RECONCILIATION_SCHEMA,
            "generated_at_utc": generated_at_utc,
            "owner_role": "robot-software-engineer",
            "proof_boundary": DELIVERY_STATE_TERMINAL_RECONCILIATION_PROOF_BOUNDARY,
            "proof_boundary_class": "software_proof_local_mock_only",
            "source_schema": source["schema"],
            "source_proof_boundary": source["proof_boundary"],
            "source_summary_ref": source_summary_ref,
            "result_code": source["result_code"],
            "terminal_result_state": source["terminal_result_state"],
            "reconciliation_state": source["reconciliation_state"],
            "task_terminal_state": source["task_terminal_state"],
            "terminal_result_type": source["terminal_result_type"],
            "task_id": identity["task_id"],
            "packet_id": identity["packet_id"],
            "route_intent_id": identity["route_intent_id"],
            "route_csv_row_count": source.get("route_csv_row_count"),
            "path_structured_pose_count": source.get("path_structured_pose_count"),
            "segment_count": source.get("segment_count"),
            "final_state": self.state.value,
            "reconciliation_status": TERMINAL_RECONCILIATION_STATUS,
            "terminal_result_accepted_for_delivery": False,
            "dropoff_success": False,
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
            "failure_code": self.failure_code,
            "error_message": self.error_message,
            "fixed_false_fields": {key: False for key in TERMINAL_RECONCILIATION_FIXED_FALSE_FIELDS},
            "fixed_false_invariants": list(TERMINAL_RECONCILIATION_FALSE_INVARIANTS),
            "rejected_claims": list(TERMINAL_RECONCILIATION_REJECTED_CLAIMS),
            "next_required_evidence": (
                "collect live route execution, dropoff/operator acceptance, and HIL "
                "before accepting delivery success"
            ),
            "state_machine_events": [
                {
                    "event": event.event.value,
                    "from_state": event.from_state.value,
                    "to_state": event.to_state.value,
                    "message": event.message,
                }
                for event in self.events
            ],
            "checks": [
                {
                    "name": "source_terminal_result_schema",
                    "status": "pass",
                    "detail": "source schema and proof boundary matched O5 bounded route terminal-result bridge",
                },
                {
                    "name": "mock_terminal_result_fail_closed",
                    "status": "pass",
                    "detail": (
                        "mock terminal result was reconciled as error and cannot be used as delivery, "
                        "dropoff, route execution, HIL, or safe-to-control evidence"
                    ),
                },
                {
                    "name": "fixed_false_fields",
                    "status": "pass",
                    "detail": (
                        "terminal_result_accepted_for_delivery=false, delivery_success=false, "
                        "route_execution_success=false, safe_to_control=false, hil_pass=false"
                    ),
                },
            ],
            "rg_acceptance_anchors": [
                "delivery_state_terminal_reconciliation",
                MOCK_ROUTE_TERMINAL_RESULT_CODE,
                "terminal_result_accepted_for_delivery=false",
                "delivery_success=false",
                "safe_to_control=false",
                "route_execution_success=false",
                "hil_pass=false",
            ],
        }
        return summary
