import json
import os

from ros2_trashbot_behavior.operator_gateway_http import status_payload

# Diagnostics must stay available even when the optional vision package is not
# installed in a minimal operator-gateway environment.
try:
    from ros2_trashbot_vision.vision_sample_manifest import summarize_manifest
except ImportError:
    summarize_manifest = None


REVIEW_QUEUE_LIMIT = 5
LOW_CONFIDENCE_REVIEW_THRESHOLD = 75
HARDWARE_PROOF_STATUSES = {"software_proof", "needs_hil", "invalid_config", "read_error"}
REVIEW_DECISION_VALUES = {"approved", "rejected", "needs_retry"}


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
):
    latest_status = dict(latest_status or {})
    last_task = dict(latest_status.get("last_task") or {})
    failure = {
        "state": latest_status.get("state", ""),
        "message": latest_status.get("message", ""),
        "error_code": latest_status.get("error_code") or last_task.get("error_code", ""),
        "final_state": latest_status.get("final_state") or last_task.get("final_state", ""),
        "task_record_path": latest_status.get("task_record_path") or last_task.get("task_record_path", ""),
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
        failure=failure,
        log_refs=normalize_log_refs(log_refs),
        vision_sample_manifest_ref=str(vision_sample_manifest_ref or ""),
        review_decision_log_ref=str(review_decision_log_ref or ""),
        review_decision_log=review_decision_log,
        vision_samples=summarize_vision_manifest(
            vision_sample_manifest_ref,
            decision_index=decision_index,
        ),
        hardware_proof=summarize_hardware_proof(hardware_proof_ref),
        operator_status_file=str(operator_status_file or ""),
    )
