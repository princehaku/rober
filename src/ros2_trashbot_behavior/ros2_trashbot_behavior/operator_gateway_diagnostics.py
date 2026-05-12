import json
import os

from ros2_trashbot_behavior.operator_gateway_http import normalize_elevator_assist, status_payload
from ros2_trashbot_behavior.remote_cloud_relay import (
    build_phone_credential_rotation_summary,
    build_phone_network_recovery_summary,
    build_phone_oss_cdn_manifest_summary,
    build_phone_production_store_queue_summary,
    build_phone_provisioning_audit_summary,
)

# Diagnostics must stay available even when the optional vision package is not
# installed in a minimal operator-gateway environment.
try:
    from ros2_trashbot_vision.vision_sample_manifest import summarize_manifest
except ImportError:
    summarize_manifest = None


REVIEW_QUEUE_LIMIT = 5
LOW_CONFIDENCE_REVIEW_THRESHOLD = 75
HARDWARE_PROOF_STATUSES = {"software_proof", "needs_hil", "invalid_config", "read_error"}
EVIDENCE_SOURCE_SOFTWARE = "software_proof"
EVIDENCE_SOURCE_HIL = "hil_pass"
VALID_EVIDENCE_SOURCES = {EVIDENCE_SOURCE_SOFTWARE, EVIDENCE_SOURCE_HIL}
REVIEW_DECISION_VALUES = {"approved", "rejected", "needs_retry"}
REVIEW_DECISION_ORDER = ("approved", "rejected", "needs_retry")
ROUTE_PROOF_REQUIRED_FIELDS = (
    "coverage_rate",
    "covered_checkpoints",
    "total_checkpoints",
    "missing_checkpoints",
    "gate_status",
    "last_block_reason",
)
ROUTE_PROOF_WAITING_GATE_STATUSES = {
    "waiting_visual_gate",
    "waiting",
    "pending",
    "blocked_by_visual_gate",
    "waiting_camera_frame",
    "missing_live_frame",
    "keyframe_preflight_failed",
    "missing_keyframe",
    "no_live_descriptors",
    "insufficient_matches",
}
ROUTE_PROOF_READY_GATE_STATUSES = {"passed", "ready", "ok"}
ELEVATOR_ASSIST_HELP_REASONS = {
    "door_timeout",
    "door_closed_or_unknown",
    "target_floor_unconfirmed",
    "target_floor_evidence_unreliable",
    "unsafe_to_enter",
    "unsafe_to_exit",
    "manual_takeover_required",
}


def _default_hardware_proof_summary(path, status="read_error", read_error=""):
    return {
        "status": status,
        "artifact_ref": str(path or ""),
        "source_status": "",
        "exists": False,
        "read_error": str(read_error or ""),
        "summary": "Hardware diagnostics proof is not available; no hardware pass can be inferred.",
        "next_step": "Run hardware_diagnostics_proof and then complete WAVE ROVER hardware-in-loop validation.",
        "vendor_sources": [],
        "risk_flags": [],
        "hil_recipe": {},
    }


def _hardware_proof_risk_text(flag):
    if isinstance(flag, dict):
        parts = [
            flag.get("id", ""),
            flag.get("severity", ""),
            flag.get("detail", ""),
            flag.get("message", ""),
        ]
        return " ".join(str(part) for part in parts if part)
    return str(flag)


def _has_hil_risk(risk_flags):
    if not isinstance(risk_flags, list):
        return True
    for flag in risk_flags:
        text = _hardware_proof_risk_text(flag).lower()
        severity = str(flag.get("severity", "")).lower() if isinstance(flag, dict) else ""
        flag_id = str(flag.get("id", "")).lower() if isinstance(flag, dict) else text
        if flag_id == "hil_required":
            return True
        if ("hil" in text or "hardware-in-loop" in text) and severity in {"high", "critical"}:
            return True
    return False


def summarize_hardware_proof(path):
    """Return a phone-safe summary of an offline WAVE ROVER proof artifact.

    Vendor/source boundary: the artifact itself is produced by the hardware
    package from docs/vendor/VENDOR_INDEX.md-backed WAVE ROVER references. This
    operator summary only reads and downgrades the artifact; it never upgrades
    software evidence into a hardware pass or invents extra hardware facts.
    """
    proof_path = os.path.expanduser(str(path or ""))
    summary = _default_hardware_proof_summary(
        proof_path,
        read_error="hardware diagnostics proof is not configured",
    )
    if not proof_path:
        return summary
    if not os.path.exists(proof_path):
        summary["read_error"] = f"hardware diagnostics proof not found: {proof_path}"
        return summary

    summary["exists"] = True
    try:
        with open(proof_path, "r", encoding="utf-8") as f:
            artifact = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        summary["read_error"] = f"failed reading hardware diagnostics proof: {exc}"
        return summary

    if not isinstance(artifact, dict):
        summary["read_error"] = "hardware diagnostics proof JSON must be an object"
        return summary

    source_status = str(artifact.get("status") or "")
    summary["source_status"] = source_status
    summary["vendor_sources"] = (
        list(artifact.get("vendor_sources")) if isinstance(artifact.get("vendor_sources"), list) else []
    )
    summary["risk_flags"] = (
        list(artifact.get("risk_flags")) if isinstance(artifact.get("risk_flags"), list) else []
    )
    summary["hil_recipe"] = artifact.get("hil_recipe") if isinstance(artifact.get("hil_recipe"), dict) else {}

    if not source_status:
        summary["read_error"] = "hardware diagnostics proof is missing status"
        return summary

    if source_status == "invalid_config":
        summary.update(
            {
                "status": "invalid_config",
                "summary": "Hardware diagnostics proof found an invalid bridge configuration.",
                "next_step": "Fix the reported bridge configuration, rerun software proof, then run WAVE ROVER HIL.",
                "read_error": str((artifact.get("config_validation") or {}).get("error", "")),
            }
        )
        return summary

    if source_status == "software_proof_ready":
        if _has_hil_risk(summary["risk_flags"]):
            summary.update(
                {
                    "status": "needs_hil",
                    "summary": "Software proof exists, hardware-in-loop still required before treating the robot as validated.",
                    "next_step": "Run the WAVE ROVER HIL recipe on a prepared robot and capture UART, motion, IMU, and battery evidence.",
                    "read_error": "",
                }
            )
            return summary
        summary.update(
            {
                "status": "software_proof",
                "summary": "Software proof is ready only; this does not validate real UART, wheel motion, IMU, battery, or HIL.",
                "next_step": "Use this artifact as software evidence, then schedule WAVE ROVER hardware-in-loop validation.",
                "read_error": "",
            }
        )
        return summary

    if source_status == "feedback_parse_failed":
        summary.update(
            {
                "status": "needs_hil",
                "summary": "Software artifact exists but feedback parsing failed; hardware-in-loop validation is still required.",
                "next_step": "Inspect the feedback sample, rerun proof with valid T=1001 feedback, then run WAVE ROVER HIL.",
                "read_error": "feedback sample did not parse as trusted hardware feedback",
            }
        )
        return summary

    summary["read_error"] = f"unsupported hardware diagnostics proof status: {source_status}"
    return summary


def normalize_log_refs(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if str(item)]
    text = str(value).strip()
    if not text:
        return []
    return [item.strip() for item in text.split(",") if item.strip()]


def default_review_decision_log(path, status="read_error", read_error=""):
    return {
        "status": status,
        "decision_log_ref": str(path or ""),
        "exists": False,
        "decision_count": 0,
        "sample_count": 0,
        "read_error": str(read_error or ""),
    }


def review_decision_entry(record):
    return {
        "decision_id": str(record.get("decision_id", "")),
        "decision": str(record.get("decision", "")),
        "comment": str(record.get("comment", "")),
        "option": str(record.get("option", "")),
        "operator": str(record.get("operator", "")),
        "timestamp": record.get("timestamp"),
    }


def load_review_decision_log(path):
    decision_log_path = os.path.expanduser(str(path or ""))
    summary = default_review_decision_log(
        decision_log_path,
        status="not_configured",
        read_error="review decision log is not configured",
    )
    decision_index = {}
    if not decision_log_path:
        return summary, decision_index
    if not os.path.exists(decision_log_path):
        summary["status"] = "missing"
        summary["read_error"] = f"review decision log not found: {decision_log_path}"
        return summary, decision_index

    summary["exists"] = True
    summary["read_error"] = ""
    try:
        with open(decision_log_path, "r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, start=1):
                text = line.strip()
                if not text:
                    continue
                try:
                    record = json.loads(text)
                except json.JSONDecodeError as exc:
                    summary["status"] = "read_error"
                    summary["read_error"] = f"invalid decision JSONL at line {line_number}: {exc}"
                    return summary, {}
                if not isinstance(record, dict):
                    continue
                sample_id = str(record.get("sample_id", "")).strip()
                decision = str(record.get("decision", "")).strip()
                if not sample_id or decision not in REVIEW_DECISION_VALUES:
                    continue
                summary["decision_count"] += 1
                decision_index[sample_id] = review_decision_entry(record)
    except OSError as exc:
        summary["status"] = "read_error"
        summary["read_error"] = f"failed reading review decision log: {exc}"
        return summary, {}

    summary["sample_count"] = len(decision_index)
    summary["status"] = "ok"
    return summary, decision_index


def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _read_task_record(path):
    record_path = os.path.expanduser(str(path or ""))
    if not record_path or not os.path.exists(record_path):
        return {}
    try:
        with open(record_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _route_proof_from_task_record(task_record):
    if not isinstance(task_record, dict):
        return None, ""
    summary = task_record.get("route_proof_summary")
    if isinstance(summary, dict):
        return summary, "task_record.route_proof_summary"
    nav_results = task_record.get("nav_results")
    if not isinstance(nav_results, list):
        return None, ""
    for nav_result in reversed(nav_results):
        if not isinstance(nav_result, dict):
            continue
        candidate = nav_result.get("route_proof_summary")
        if isinstance(candidate, dict):
            return candidate, "task_record.nav_results.route_proof_summary"
        evidence = nav_result.get("evidence")
        if isinstance(evidence, dict) and isinstance(evidence.get("route_proof_summary"), dict):
            return evidence.get("route_proof_summary"), "task_record.nav_results.evidence.route_proof_summary"
    return None, ""


def _extract_route_proof_summary(latest_status, last_task):
    latest_status = latest_status if isinstance(latest_status, dict) else {}
    last_task = last_task if isinstance(last_task, dict) else {}
    for summary, source in (
        (latest_status.get("route_proof_summary"), "latest_status.route_proof_summary"),
        (last_task.get("route_proof_summary"), "last_task.route_proof_summary"),
    ):
        if isinstance(summary, dict):
            return dict(summary), source
    task_record_path = (
        latest_status.get("task_record_path")
        or last_task.get("task_record_path")
        or ""
    )
    task_record = _read_task_record(task_record_path)
    summary, source = _route_proof_from_task_record(task_record)
    if isinstance(summary, dict):
        return dict(summary), source
    return {}, ""


def normalize_evidence_source(value):
    """Normalize evidence provenance to user-facing contracts.

    Source tags are intentionally limited to two values so O2/O3 users can
    clearly distinguish offline replay evidence from real hardware-in-loop evidence:
    - hil_pass: evidence is robot-side validated with HIL/real hardware artifacts.
    - software_proof: software-only proof is available but HIL is still required.
    """
    normalized = str(value or "").strip().lower().replace("-", "_")
    if normalized in VALID_EVIDENCE_SOURCES:
        return normalized
    if normalized in {
        "task_orchestrator",
        "dry_run",
        "robot_sim",
        "simulated",
        "software",
        "software_proof",
    }:
        if normalized == "software":
            return EVIDENCE_SOURCE_SOFTWARE
        return EVIDENCE_SOURCE_SOFTWARE
    if normalized == "hil":
        return EVIDENCE_SOURCE_HIL
    return EVIDENCE_SOURCE_SOFTWARE


def _extract_traceability_field(payload, field_name, *fallbacks):
    """Read a traceability field using explicit ownership precedence.

    Priority:
    1) `payload` (authoritative task_record)
    2) each fallback payload in order
    """
    if isinstance(payload, dict) and field_name in payload:
        return payload.get(field_name)
    for fallback_payload in fallbacks:
        if isinstance(fallback_payload, dict) and field_name in fallback_payload:
            return fallback_payload.get(field_name)
    return None


def _extract_route_progress(payload, *fallbacks):
    for candidate_payload in (payload, *fallbacks):
        if not isinstance(candidate_payload, dict):
            continue
        route_progress = candidate_payload.get("route_progress")
        if isinstance(route_progress, dict) and route_progress:
            return dict(route_progress)
        nav_results = candidate_payload.get("nav_results")
        if not isinstance(nav_results, list):
            continue
        for nav_result in reversed(nav_results):
            if not isinstance(nav_result, dict):
                continue
            evidence = nav_result.get("evidence")
            if not isinstance(evidence, dict):
                continue
            route_progress = evidence.get("route_progress")
            if isinstance(route_progress, dict) and route_progress:
                return dict(route_progress)
    return {}


def coalesce_traceability_fields(latest_status, *, task_record=None, last_task=None):
    """Return one canonical traceability bundle for diagnostics and gateway status."""
    latest_status = latest_status if isinstance(latest_status, dict) else {}
    last_task = last_task if isinstance(last_task, dict) else {}
    if not isinstance(task_record, dict):
        task_record = _read_task_record(latest_status.get("task_record_path"))

    task_record_path = str(
        latest_status.get("task_record_path")
        or last_task.get("task_record_path")
        or ""
    ).strip()
    result_path = str(
        _extract_traceability_field(
            task_record,
            "result_path",
            latest_status,
            last_task,
        )
        or task_record_path
        or ""
    )
    evidence_ref = str(
        _extract_traceability_field(
            task_record,
            "evidence_ref",
            latest_status,
            last_task,
        )
        or result_path
        or task_record_path
        or ""
    )
    failure_code = str(
        _extract_traceability_field(
            task_record,
            "failure_code",
            latest_status,
            last_task,
        )
        or _extract_traceability_field(latest_status, "error_code")
        or _extract_traceability_field(last_task, "error_code")
        or ""
    )
    if "human_intervention_required" in task_record:
        human_intervention_required = bool(task_record.get("human_intervention_required"))
    elif "human_intervention_required" in latest_status:
        human_intervention_required = bool(latest_status.get("human_intervention_required"))
    elif "human_intervention_required" in last_task:
        human_intervention_required = bool(last_task.get("human_intervention_required"))
    else:
        human_intervention_required = False

    state_transition_history = task_record.get("state_transition_history")
    if not isinstance(state_transition_history, list):
        state_transition_history = task_record.get("state_transitions")
        if not isinstance(state_transition_history, list):
            state_transition_history = _extract_traceability_field(
                last_task,
                "state_transition_history",
                latest_status,
            )
            if not isinstance(state_transition_history, list):
                state_transition_history = []
    return {
        "source": normalize_evidence_source(
            _extract_traceability_field(
                task_record,
                "source",
                latest_status,
                last_task,
            )
            or ""
        ),
        "result_path": result_path,
        "evidence_ref": evidence_ref,
        "failure_code": failure_code,
        "human_intervention_required": bool(human_intervention_required),
        "state_transition_history": state_transition_history,
        "task_record_path": task_record_path,
        "route_progress": _extract_route_progress(task_record, latest_status, last_task),
    }


def _elevator_assist_from_task_record(task_record):
    if not isinstance(task_record, dict):
        return None, ""
    direct = task_record.get("elevator_assist")
    if isinstance(direct, dict):
        return direct, "task_record.elevator_assist"
    events = task_record.get("elevator_assist_events")
    if isinstance(events, list) and events:
        latest_event = events[-1] if isinstance(events[-1], dict) else {}
        return {
            "enabled": True,
            "mode": "dry_run",
            "state": latest_event.get("state") or latest_event.get("phase") or "",
            "phase": latest_event.get("phase") or latest_event.get("state") or "",
            "requires_human_help": bool(latest_event.get("requires_human_help", False)),
            "reason": latest_event.get("reason", ""),
            "target_floor": latest_event.get("target_floor", ""),
            "evidence": latest_event.get("evidence") if isinstance(latest_event.get("evidence"), dict) else {},
            "events": events,
        }, "task_record.elevator_assist_events"
    nav_results = task_record.get("nav_results")
    if not isinstance(nav_results, list):
        return None, ""
    for nav_result in reversed(nav_results):
        if not isinstance(nav_result, dict):
            continue
        candidate = nav_result.get("elevator_assist")
        if isinstance(candidate, dict):
            return candidate, "task_record.nav_results.elevator_assist"
        evidence = nav_result.get("evidence")
        if isinstance(evidence, dict) and isinstance(evidence.get("elevator_assist"), dict):
            return evidence.get("elevator_assist"), "task_record.nav_results.evidence.elevator_assist"
    return None, ""


def extract_elevator_assist(latest_status, last_task):
    latest_status = latest_status if isinstance(latest_status, dict) else {}
    last_task = last_task if isinstance(last_task, dict) else {}
    for candidate, source in (
        (latest_status.get("elevator_assist"), "latest_status.elevator_assist"),
        (last_task.get("elevator_assist"), "last_task.elevator_assist"),
    ):
        if isinstance(candidate, dict):
            return normalize_elevator_assist(candidate), source

    task_record_path = latest_status.get("task_record_path") or last_task.get("task_record_path") or ""
    candidate, source = _elevator_assist_from_task_record(_read_task_record(task_record_path))
    if isinstance(candidate, dict):
        return normalize_elevator_assist(candidate), source
    return normalize_elevator_assist({}), ""


def classify_elevator_assist(elevator_assist, source=""):
    elevator_assist = normalize_elevator_assist(elevator_assist)
    source_text = str(source or "")
    if not elevator_assist.get("enabled"):
        return {
            "state": "disabled",
            "reason": "elevator assisted delivery is not active",
            "next_step": "Continue the normal trash delivery flow.",
            "source": source_text,
        }

    phase = str(elevator_assist.get("phase") or elevator_assist.get("state") or "").strip()
    reason = str(elevator_assist.get("reason") or "").strip()
    if elevator_assist.get("requires_human_help") or phase in ELEVATOR_ASSIST_HELP_REASONS:
        return {
            "state": "needs_human_help",
            "reason": reason or elevator_assist.get("phone_copy") or "elevator assist requires human help",
            "next_step": "Ask an operator to confirm the elevator door, target floor, or safe takeover path.",
            "source": source_text,
        }
    if phase == "waiting_elevator_open":
        return {
            "state": "waiting_elevator_open",
            "reason": "waiting for the elevator door to open",
            "next_step": "Wait for door_open evidence or ask for help if the door does not open.",
            "source": source_text,
        }
    if phase == "requesting_floor_help":
        return {
            "state": "requesting_floor_help",
            "reason": "robot is asking a nearby person to press the target floor",
            "next_step": elevator_assist.get("speaker_prompt", ""),
            "source": source_text,
        }
    if phase == "waiting_target_floor":
        return {
            "state": "waiting_target_floor",
            "reason": "waiting for target floor arrival evidence",
            "next_step": "Keep the path clear and wait for target_floor_confirmed plus door_open evidence.",
            "source": source_text,
        }
    if phase == "exiting_elevator":
        return {
            "state": "exiting_elevator",
            "reason": "target floor evidence is ready and the robot is preparing to exit",
            "next_step": "Monitor safe_to_exit evidence while the robot leaves the elevator.",
            "source": source_text,
        }
    if phase == "resume_delivery":
        return {
            "state": "resume_delivery",
            "reason": "elevator segment is complete",
            "next_step": "Continue delivery to the trash station.",
            "source": source_text,
        }
    return {
        "state": "active",
        "reason": reason or elevator_assist.get("phone_copy") or "elevator assist is active",
        "next_step": elevator_assist.get("speaker_prompt", ""),
        "source": source_text,
    }


def _route_proof_missing_fields(route_proof_summary):
    return [field for field in ROUTE_PROOF_REQUIRED_FIELDS if field not in route_proof_summary]


def classify_route_proof(route_proof_summary, source=""):
    route_proof_summary = route_proof_summary if isinstance(route_proof_summary, dict) else {}
    source_text = str(source or "")
    if not route_proof_summary:
        return {
            "state": "unknown",
            "reason": "route_proof_summary is missing",
            "blocking_reason": "",
            "missing_fields": list(ROUTE_PROOF_REQUIRED_FIELDS),
            "source": source_text,
        }

    missing_fields = _route_proof_missing_fields(route_proof_summary)
    if missing_fields:
        return {
            "state": "unknown",
            "reason": f"route_proof_summary missing required fields: {', '.join(missing_fields)}",
            "blocking_reason": "",
            "missing_fields": missing_fields,
            "source": source_text,
        }

    gate_status = str(route_proof_summary.get("gate_status", "")).strip().lower()
    blocking_reason = str(route_proof_summary.get("last_block_reason", "")).strip()
    coverage_rate = safe_float(route_proof_summary.get("coverage_rate"))
    missing_checkpoints = route_proof_summary.get("missing_checkpoints")
    if not isinstance(missing_checkpoints, list):
        missing_checkpoints = []
    missing_checkpoint_values = [str(item).strip() for item in missing_checkpoints if str(item).strip()]

    if gate_status in ROUTE_PROOF_WAITING_GATE_STATUSES:
        reason = "waiting for visual gate to pass"
        if blocking_reason:
            reason = f"waiting for visual gate: {blocking_reason}"
        return {
            "state": "waiting_visual_gate",
            "reason": reason,
            "blocking_reason": "",
            "missing_fields": [],
            "source": source_text,
        }

    if blocking_reason:
        return {
            "state": "blocked",
            "reason": f"blocked: {blocking_reason}",
            "blocking_reason": blocking_reason,
            "missing_fields": [],
            "source": source_text,
        }

    if coverage_rate is None:
        return {
            "state": "unknown",
            "reason": "route_proof_summary.coverage_rate is not a number",
            "blocking_reason": "",
            "missing_fields": [],
            "source": source_text,
        }

    if coverage_rate < 1.0 or missing_checkpoint_values:
        reason = f"coverage_rate={coverage_rate:.4f} indicates incomplete route proof"
        if missing_checkpoint_values:
            reason = f"missing checkpoints: {', '.join(missing_checkpoint_values)}"
        return {
            "state": "insufficient_coverage",
            "reason": reason,
            "blocking_reason": "",
            "missing_fields": [],
            "source": source_text,
        }

    if gate_status in ROUTE_PROOF_READY_GATE_STATUSES:
        return {
            "state": "ready",
            "reason": "route proof is ready",
            "blocking_reason": "",
            "missing_fields": [],
            "source": source_text,
        }

    return {
        "state": "unknown",
        "reason": f"unsupported gate_status: {gate_status or 'empty'}",
        "blocking_reason": "",
        "missing_fields": [],
        "source": source_text,
    }


def sample_event_type(sample):
    context = sample.get("context") if isinstance(sample.get("context"), dict) else {}
    return str(context.get("event_type") or "unknown")


def sample_review_reason(sample):
    event_type = sample_event_type(sample)
    detection_count = safe_int(sample.get("detection_count"))
    max_confidence = safe_int(sample.get("max_confidence"))
    context = sample.get("context") if isinstance(sample.get("context"), dict) else {}

    if context.get("anomaly_type") or event_type == "anomaly":
        return "anomaly_sample"
    if event_type == "route_keyframe":
        return "route_keyframe_review"
    if detection_count > 0 and max_confidence < LOW_CONFIDENCE_REVIEW_THRESHOLD:
        return "low_confidence_detection"
    if not str(sample.get("label_status", "")).strip() and not str(sample.get("review_status", "")).strip():
        return "unreviewed_sample"
    return ""


def vision_sample_review_item(sample, decision_index=None):
    context = sample.get("context") if isinstance(sample.get("context"), dict) else {}
    sample_id = str(sample.get("sample_id", ""))
    last_decision = None
    if isinstance(decision_index, dict):
        last_decision = dict(decision_index.get(sample_id) or {}) or None
    return {
        "sample_id": sample_id,
        "sample_ref": str(sample.get("sample_ref", "")),
        "timestamp": sample.get("timestamp"),
        "context": context,
        "event_type": sample_event_type(sample),
        "detection_count": safe_int(sample.get("detection_count")),
        "max_confidence": safe_int(sample.get("max_confidence")),
        "reason": sample_review_reason(sample),
        "review_status": "decided" if last_decision else "pending",
        "last_decision": last_decision,
    }


def build_vision_review_queue(samples, decision_index=None, limit=REVIEW_QUEUE_LIMIT):
    queue = []
    for sample in reversed(samples):
        if not isinstance(sample, dict):
            continue
        reason = sample_review_reason(sample)
        if not reason:
            continue
        item = vision_sample_review_item(sample, decision_index=decision_index)
        queue.append(item)
        if len(queue) >= limit:
            break
    return list(reversed(queue))


def _review_decision_distribution(counts, decided):
    decided = int(decided or 0)
    distribution = {}
    for decision in REVIEW_DECISION_ORDER:
        count = int(counts.get(decision, 0))
        distribution[decision] = {
            "count": count,
            "ratio": round(count / decided, 4) if decided > 0 else 0.0,
        }
    return distribution


def summarize_review_progress(samples, decision_index=None):
    decision_index = decision_index if isinstance(decision_index, dict) else {}
    reviewable = []
    decision_counts = {decision: 0 for decision in REVIEW_DECISION_ORDER}
    decided = 0
    next_pending_sample = None

    for sample in samples:
        if not isinstance(sample, dict):
            continue
        reason = sample_review_reason(sample)
        if not reason:
            continue
        reviewable.append(sample)
        sample_id = str(sample.get("sample_id", ""))
        decision_entry = decision_index.get(sample_id) if sample_id else None
        decision = str((decision_entry or {}).get("decision", "")).strip()
        if decision in REVIEW_DECISION_VALUES:
            decided += 1
            decision_counts[decision] += 1
            continue
        if next_pending_sample is None:
            next_pending_sample = {
                "sample_id": sample_id,
                "sample_ref": str(sample.get("sample_ref", "")),
                "reason": reason,
                "event_type": sample_event_type(sample),
                "timestamp": sample.get("timestamp"),
            }

    total = len(reviewable)
    pending = max(total - decided, 0)
    progress_summary = {
        "total": total,
        "decided": decided,
        "pending": pending,
        "coverage_rate": round(decided / total, 4) if total > 0 else 0.0,
    }
    return {
        "progress_summary": progress_summary,
        "decision_distribution": _review_decision_distribution(decision_counts, decided),
        "next_pending_sample": next_pending_sample,
    }


def default_integrity_fields(status, *, error="", warning=""):
    errors = [error] if error else []
    warnings = [warning] if warning else []
    return {
        "integrity_summary": {
            "status": status,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "missing_file_ref_count": 0,
            "sample_output_dir": "",
            "negative_sample_count": 0,
            "anomaly_sample_count": 0,
            "route_keyframe_sample_count": 0,
            "detection_sample_count": 0,
        },
        "integrity_errors": errors,
        "integrity_warnings": warnings,
        "integrity_error_count": len(errors),
        "integrity_warning_count": len(warnings),
        "missing_file_ref_count": 0,
        "missing_file_refs": [],
        "context_field_coverage": {"present": {}, "missing": {}},
        "file_counts": {},
    }


def integrity_status(checker_summary):
    if checker_summary.get("errors"):
        return "error"
    if checker_summary.get("warnings"):
        return "warning"
    return "ok"


def vision_manifest_integrity_fields(path):
    if not path:
        return default_integrity_fields(
            "not_configured",
            error="vision sample manifest is not configured",
        )
    if summarize_manifest is None:
        return default_integrity_fields(
            "checker_unavailable",
            warning="ros2_trashbot_vision.vision_sample_manifest is not importable",
        )

    try:
        checker_summary = summarize_manifest(path)
    except Exception as exc:
        return default_integrity_fields(
            "checker_failed",
            error=f"vision sample manifest checker failed: {exc}",
        )

    errors = [str(item) for item in checker_summary.get("errors", [])]
    warnings = [str(item) for item in checker_summary.get("warnings", [])]
    missing_file_refs = [
        item for item in checker_summary.get("missing_file_refs", []) if isinstance(item, dict)
    ]
    status = integrity_status({"errors": errors, "warnings": warnings})
    return {
        "integrity_summary": {
            "status": status,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "missing_file_ref_count": len(missing_file_refs),
            "sample_output_dir": str(checker_summary.get("sample_output_dir", "")),
            "negative_sample_count": safe_int(checker_summary.get("negative_sample_count")),
            "anomaly_sample_count": safe_int(checker_summary.get("anomaly_sample_count")),
            "route_keyframe_sample_count": safe_int(checker_summary.get("route_keyframe_sample_count")),
            "detection_sample_count": safe_int(checker_summary.get("detection_sample_count")),
        },
        "integrity_errors": errors,
        "integrity_warnings": warnings,
        "integrity_error_count": len(errors),
        "integrity_warning_count": len(warnings),
        "missing_file_ref_count": len(missing_file_refs),
        "missing_file_refs": missing_file_refs,
        "context_field_coverage": checker_summary.get("context_field_coverage", {"present": {}, "missing": {}}),
        "file_counts": checker_summary.get("file_counts", {}),
    }


def summarize_vision_manifest(path, decision_index=None):
    path = os.path.expanduser(str(path or ""))
    summary = {
        "manifest_ref": path,
        "exists": False,
        "schema": "",
        "sample_count": 0,
        "latest_sample_ref": "",
        "latest_timestamp": None,
        "latest_context": {},
        "latest_detection_count": 0,
        "latest_max_confidence": 0,
        "event_counts": {},
        "review_queue_count": 0,
        "review_queue": [],
        "progress_summary": {
            "total": 0,
            "decided": 0,
            "pending": 0,
            "coverage_rate": 0.0,
        },
        "decision_distribution": _review_decision_distribution({}, 0),
        "next_pending_sample": None,
        "read_error": "",
    }
    summary.update(vision_manifest_integrity_fields(path))
    if not path:
        summary["read_error"] = "vision sample manifest is not configured"
        return summary
    if not os.path.exists(path):
        summary["read_error"] = f"vision sample manifest not found: {path}"
        return summary

    summary["exists"] = True
    try:
        with open(path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        summary["read_error"] = f"failed reading vision sample manifest: {exc}"
        return summary

    samples = manifest.get("samples") if isinstance(manifest, dict) else None
    if not isinstance(samples, list):
        summary["read_error"] = "vision sample manifest has no samples list"
        return summary

    summary["schema"] = str(manifest.get("schema", ""))
    summary["sample_count"] = len(samples)
    event_counts = {}
    for sample in samples:
        if not isinstance(sample, dict):
            continue
        event_type = sample_event_type(sample)
        event_counts[event_type] = event_counts.get(event_type, 0) + 1
    summary["event_counts"] = event_counts
    review_queue = build_vision_review_queue(samples, decision_index=decision_index)
    summary.update(summarize_review_progress(samples, decision_index=decision_index))
    summary["review_queue"] = review_queue
    summary["review_queue_count"] = len(review_queue)
    latest = samples[-1] if samples and isinstance(samples[-1], dict) else {}
    summary["latest_sample_ref"] = str(latest.get("sample_ref", ""))
    summary["latest_timestamp"] = latest.get("timestamp")
    summary["latest_context"] = latest.get("context") if isinstance(latest.get("context"), dict) else {}
    summary["latest_detection_count"] = safe_int(latest.get("detection_count"))
    summary["latest_max_confidence"] = safe_int(latest.get("max_confidence"))
    return summary


def build_diagnostics_payload(
    latest_status,
    *,
    software_version,
    map_version,
    route_version,
    log_refs,
    vision_sample_manifest_ref,
    review_decision_log_ref,
    operator_status_file,
    hardware_proof_ref="",
    oss_cdn_manifest_artifact_ref="",
    network_recovery_artifact_ref="",
    credential_rotation_artifact_ref="",
    provisioning_audit_artifact_ref="",
    production_store_queue_artifact_ref="",
):
    latest_status = dict(latest_status or {})
    last_task = dict(latest_status.get("last_task") or {})
    task_record_path = str(
        latest_status.get("task_record_path")
        or last_task.get("task_record_path")
        or ""
    )
    task_record = _read_task_record(task_record_path)
    route_proof_summary, route_proof_source = _extract_route_proof_summary(latest_status, last_task)
    route_proof_status = classify_route_proof(route_proof_summary, source=route_proof_source)
    elevator_assist, elevator_assist_source = extract_elevator_assist(latest_status, last_task)
    elevator_assist_status = classify_elevator_assist(elevator_assist, source=elevator_assist_source)
    traceability = coalesce_traceability_fields(
        latest_status,
        task_record=task_record,
        last_task=last_task,
    )
    source = normalize_evidence_source(traceability["source"])
    result_path = traceability["result_path"]
    evidence_ref = traceability["evidence_ref"]
    failure_code = traceability["failure_code"]
    human_intervention_required = traceability["human_intervention_required"]
    state_transition_history = traceability["state_transition_history"]
    route_progress = traceability["route_progress"]
    last_task["source"] = source
    last_task["result_path"] = result_path
    if "evidence_ref" in last_task:
        last_task["evidence_ref"] = evidence_ref
    else:
        last_task["evidence_ref"] = (
            str(task_record.get("result_path", "")).strip() or evidence_ref
        )
    last_task["failure_code"] = failure_code
    last_task["state_transition_history"] = state_transition_history
    last_task["human_intervention_required"] = human_intervention_required
    last_task["route_progress"] = route_progress
    failure = {
        "state": latest_status.get("state", ""),
        "message": latest_status.get("message", ""),
        "error_code": latest_status.get("error_code") or last_task.get("error_code", ""),
        "final_state": latest_status.get("final_state") or last_task.get("final_state", ""),
        "task_record_path": latest_status.get("task_record_path") or last_task.get("task_record_path", ""),
        "result_path": result_path,
        "source": source,
        "evidence_ref": evidence_ref,
        "failure_code": failure_code,
        "human_intervention_required": human_intervention_required,
        "state_transition_history": state_transition_history,
        "route_progress": route_progress,
    }
    review_decision_log, decision_index = load_review_decision_log(review_decision_log_ref)
    return status_payload(
        "diagnostics_ready",
        "diagnostics package ready",
        software_version=str(software_version or ""),
        map_version=str(map_version or ""),
        route_version=str(route_version or ""),
        latest_status=latest_status,
        last_task=last_task,
        source=source,
        result_path=result_path,
        evidence_ref=evidence_ref,
        failure_code=failure_code,
        human_intervention_required=human_intervention_required,
        state_transition_history=state_transition_history,
        route_progress=route_progress,
        failure=failure,
        log_refs=normalize_log_refs(log_refs),
        vision_sample_manifest_ref=str(vision_sample_manifest_ref or ""),
        review_decision_log_ref=str(review_decision_log_ref or ""),
        review_decision_log=review_decision_log,
        vision_samples=summarize_vision_manifest(
            vision_sample_manifest_ref,
            decision_index=decision_index,
        ),
        route_proof_summary=route_proof_summary,
        route_proof_status=route_proof_status,
        elevator_assist=elevator_assist,
        elevator_assist_status=elevator_assist_status,
        hardware_proof=summarize_hardware_proof(hardware_proof_ref),
        oss_cdn_manifest=build_phone_oss_cdn_manifest_summary(oss_cdn_manifest_artifact_ref),
        network_recovery_drill=build_phone_network_recovery_summary(
            network_recovery_artifact_ref
            or os.environ.get("TRASHBOT_REMOTE_CLOUD_NETWORK_RECOVERY_ARTIFACT", "")
        ),
        credential_rotation=build_phone_credential_rotation_summary(
            credential_rotation_artifact_ref
            or os.environ.get("TRASHBOT_REMOTE_CLOUD_CREDENTIAL_ROTATION_ARTIFACT", "")
        ),
        provisioning_audit=build_phone_provisioning_audit_summary(
            provisioning_audit_artifact_ref
            or os.environ.get("TRASHBOT_REMOTE_CLOUD_PROVISIONING_AUDIT_ARTIFACT", "")
        ),
        production_store_queue=build_phone_production_store_queue_summary(
            production_store_queue_artifact_ref
            or os.environ.get("TRASHBOT_REMOTE_CLOUD_PRODUCTION_STORE_QUEUE_ARTIFACT", "")
        ),
        operator_status_file=str(operator_status_file or ""),
    )
