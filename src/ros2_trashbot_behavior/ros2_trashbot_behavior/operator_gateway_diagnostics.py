import json
import os

from ros2_trashbot_behavior.operator_gateway_http import status_payload


def normalize_log_refs(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if str(item)]
    text = str(value).strip()
    if not text:
        return []
    return [item.strip() for item in text.split(",") if item.strip()]


def summarize_vision_manifest(path):
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
        "read_error": "",
    }
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
    latest = samples[-1] if samples and isinstance(samples[-1], dict) else {}
    summary["latest_sample_ref"] = str(latest.get("sample_ref", ""))
    summary["latest_timestamp"] = latest.get("timestamp")
    summary["latest_context"] = latest.get("context") if isinstance(latest.get("context"), dict) else {}
    summary["latest_detection_count"] = int(latest.get("detection_count") or 0)
    summary["latest_max_confidence"] = int(latest.get("max_confidence") or 0)
    return summary


def build_diagnostics_payload(
    latest_status,
    *,
    software_version,
    map_version,
    route_version,
    log_refs,
    vision_sample_manifest_ref,
    operator_status_file,
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
        vision_samples=summarize_vision_manifest(vision_sample_manifest_ref),
        operator_status_file=str(operator_status_file or ""),
    )
