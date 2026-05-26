import json
import os


# Diagnostics must stay available even when the optional vision package is not
# installed in a minimal operator-gateway environment.
try:
    from ros2_trashbot_vision.vision_sample_manifest import summarize_manifest
except ImportError:
    summarize_manifest = None


REVIEW_QUEUE_LIMIT = 5
LOW_CONFIDENCE_REVIEW_THRESHOLD = 75
REVIEW_DECISION_VALUES = {"approved", "rejected", "needs_retry"}
REVIEW_DECISION_ORDER = ("approved", "rejected", "needs_retry")


def _safe_int(value, default=0):
    # 诊断输入来自 JSON/状态文件，保持宽松转换可避免坏样本阻断整个面板。
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def sample_event_type(sample):
    # context 不是 dict 时按 unknown 处理，避免上游脏数据改变 review 队列结构。
    context = sample.get("context") if isinstance(sample.get("context"), dict) else {}
    return str(context.get("event_type") or "unknown")


def sample_review_reason(sample):
    # review reason 的优先级是接口契约，迁移时必须保持原先判定顺序。
    event_type = sample_event_type(sample)
    detection_count = _safe_int(sample.get("detection_count"))
    max_confidence = _safe_int(sample.get("max_confidence"))
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
    # last_decision 只取最后一次有效决策索引，保留 pending/decided 的兼容语义。
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
        "detection_count": _safe_int(sample.get("detection_count")),
        "max_confidence": _safe_int(sample.get("max_confidence")),
        "reason": sample_review_reason(sample),
        "review_status": "decided" if last_decision else "pending",
        "last_decision": last_decision,
    }


def build_vision_review_queue(samples, decision_index=None, limit=REVIEW_QUEUE_LIMIT):
    # 从最新样本向前取有限队列，再恢复时间顺序，兼容原有 operator UI 展示。
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
    # 输出必须包含所有合法决策，前端才能用固定 key 渲染零值分布。
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
    # progress 只统计可 review 样本，普通已标注样本不影响人工复核覆盖率。
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
    # 失败默认值保持完整字段集，调用方无需按状态分支判断字段是否存在。
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
    # error 优先于 warning，和 vision manifest checker 的原始语义保持一致。
    if checker_summary.get("errors"):
        return "error"
    if checker_summary.get("warnings"):
        return "warning"
    return "ok"


def vision_manifest_integrity_fields(path):
    # integrity checker 是可选依赖；不可用时只降级诊断，不阻断 payload 生成。
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
            "negative_sample_count": _safe_int(checker_summary.get("negative_sample_count")),
            "anomaly_sample_count": _safe_int(checker_summary.get("anomaly_sample_count")),
            "route_keyframe_sample_count": _safe_int(checker_summary.get("route_keyframe_sample_count")),
            "detection_sample_count": _safe_int(checker_summary.get("detection_sample_count")),
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
    # summary 的所有字段名和默认值都属于 operator diagnostics payload 契约。
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
    summary["latest_detection_count"] = _safe_int(latest.get("detection_count"))
    summary["latest_max_confidence"] = _safe_int(latest.get("max_confidence"))
    return summary
