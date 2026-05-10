"""Offline checks for trashbot vision sample manifests.

The helpers in this module intentionally avoid ROS2, OpenCV, and camera
dependencies. They are meant for post-run review of files produced by
``TrashDetector`` and ``RouteDataRecorder`` before diagnostics or humans trust
the sample set.
"""

import argparse
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


MANIFEST_SCHEMA = "trashbot.vision_samples.v1"
SAMPLE_URI_PREFIX = "vision_sample://"
REQUIRED_MANIFEST_FIELDS = ("schema", "samples")
REQUIRED_SAMPLE_FIELDS = ("sample_id", "sample_ref", "timestamp", "frame_id", "context")
CONTEXT_FIELDS = ("task_id", "route_id", "checkpoint_id", "event_type", "anomaly_type")
FILE_REF_FIELDS = ("json", "raw_image", "annotated_image")
REQUIRED_FILE_REF_FIELDS = ("json", "raw_image")


def summarize_manifest(manifest_path: str) -> Dict[str, Any]:
    """Load and validate a manifest, returning a stable JSON-serializable summary."""
    manifest_file = Path(manifest_path).expanduser()
    errors: List[str] = []
    warnings: List[str] = []

    manifest: Dict[str, Any] = {}
    if not manifest_file.exists():
        errors.append(f"manifest not found: {manifest_file}")
    else:
        try:
            loaded = json.loads(manifest_file.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                manifest = loaded
            else:
                errors.append("manifest root must be an object")
        except json.JSONDecodeError as exc:
            errors.append(f"manifest json decode error: {exc}")
        except OSError as exc:
            errors.append(f"manifest read error: {exc}")

    sample_output_dir = _sample_output_dir(manifest, manifest_file)
    samples = manifest.get("samples", [])
    if not isinstance(samples, list):
        errors.append("manifest.samples must be a list")
        samples = []
    elif not samples and manifest:
        warnings.append("manifest.samples is empty")

    for field in REQUIRED_MANIFEST_FIELDS:
        if field not in manifest and manifest_file.exists():
            errors.append(f"manifest missing required field: {field}")

    schema = manifest.get("schema", "")
    if schema and schema != MANIFEST_SCHEMA:
        warnings.append(f"unexpected manifest schema: {schema}")

    file_counts = _empty_file_counts()
    field_presence = Counter()
    field_missing = Counter()
    context_field_presence = Counter()
    context_field_missing = Counter()
    context_counts = Counter()
    event_counts = Counter()
    sample_type_counts = Counter()
    missing_file_refs: List[Dict[str, Any]] = []
    negative_sample_count = 0
    anomaly_sample_count = 0
    route_keyframe_sample_count = 0
    detection_sample_count = 0

    for index, sample in enumerate(samples):
        if not isinstance(sample, dict):
            errors.append(f"samples[{index}] must be an object")
            continue

        for field in REQUIRED_SAMPLE_FIELDS:
            if _has_value(sample.get(field)):
                field_presence[field] += 1
            else:
                field_missing[field] += 1
                errors.append(f"samples[{index}] missing required field: {field}")

        context = sample.get("context")
        if isinstance(context, dict):
            event_type = _string_value(context.get("event_type")) or "unknown"
            anomaly_type = _string_value(context.get("anomaly_type"))
            context_counts[event_type] += 1
            event_counts[event_type] += 1
            sample_type_counts[event_type] += 1
            for field in CONTEXT_FIELDS:
                if _has_value(context.get(field)):
                    context_field_presence[field] += 1
                else:
                    context_field_missing[field] += 1
            if event_type == "route_keyframe":
                route_keyframe_sample_count += 1
            if event_type == "detection":
                detection_sample_count += 1
            if anomaly_type:
                anomaly_sample_count += 1
        else:
            context_counts["missing"] += 1
            sample_type_counts["missing_context"] += 1
            errors.append(f"samples[{index}].context must be an object")

        detection_count = _detection_count(sample)
        if detection_count == 0:
            negative_sample_count += 1

        _check_sample_ref(index, sample, sample_output_dir, file_counts, missing_file_refs, errors)
        _check_file_refs(index, sample, sample_output_dir, file_counts, missing_file_refs, errors, warnings)

    return {
        "manifest_path": str(manifest_file),
        "schema": schema,
        "sample_output_dir": str(sample_output_dir),
        "sample_count": len(samples),
        "file_counts": file_counts,
        "context_counts": dict(sorted(context_counts.items())),
        "event_counts": dict(sorted(event_counts.items())),
        "sample_type_counts": dict(sorted(sample_type_counts.items())),
        "negative_sample_count": negative_sample_count,
        "anomaly_sample_count": anomaly_sample_count,
        "route_keyframe_sample_count": route_keyframe_sample_count,
        "detection_sample_count": detection_sample_count,
        "missing_file_refs": missing_file_refs,
        "field_coverage": {
            "present": dict(sorted(field_presence.items())),
            "missing": dict(sorted(field_missing.items())),
        },
        "context_field_coverage": {
            "present": dict(sorted(context_field_presence.items())),
            "missing": dict(sorted(context_field_missing.items())),
        },
        "errors": errors,
        "warnings": warnings,
    }


def _sample_output_dir(manifest: Dict[str, Any], manifest_file: Path) -> Path:
    configured = manifest.get("sample_output_dir")
    if isinstance(configured, str) and configured.strip():
        configured_path = Path(os.path.expanduser(configured))
        if configured_path.is_absolute():
            return configured_path
        return (manifest_file.parent / configured_path).resolve()
    return manifest_file.parent.resolve()


def _empty_file_counts() -> Dict[str, Dict[str, int]]:
    return {
        field: {"present": 0, "missing": 0, "empty": 0}
        for field in ("sample_ref",) + FILE_REF_FIELDS
    }


def _has_value(value: Any) -> bool:
    return value is not None and (not isinstance(value, str) or bool(value.strip()))


def _string_value(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _detection_count(sample: Dict[str, Any]) -> int:
    explicit_count = sample.get("detection_count")
    if isinstance(explicit_count, int) and explicit_count >= 0:
        return explicit_count
    detections = sample.get("detections")
    if isinstance(detections, list):
        return len(detections)
    return 0


def _check_sample_ref(
    index: int,
    sample: Dict[str, Any],
    sample_output_dir: Path,
    file_counts: Dict[str, Dict[str, int]],
    missing_file_refs: List[Dict[str, Any]],
    errors: List[str],
) -> None:
    sample_ref = sample.get("sample_ref")
    if not _has_value(sample_ref):
        file_counts["sample_ref"]["empty"] += 1
        return
    resolved = resolve_sample_reference(str(sample_ref), sample_output_dir)
    if resolved is None:
        file_counts["sample_ref"]["missing"] += 1
        errors.append(f"samples[{index}].sample_ref has unsupported URI: {sample_ref}")
        missing_file_refs.append(_missing_ref(index, "sample_ref", str(sample_ref), None))
        return
    _record_path_check(index, "sample_ref", str(sample_ref), resolved, file_counts, missing_file_refs, errors)


def _check_file_refs(
    index: int,
    sample: Dict[str, Any],
    sample_output_dir: Path,
    file_counts: Dict[str, Dict[str, int]],
    missing_file_refs: List[Dict[str, Any]],
    errors: List[str],
    warnings: List[str],
) -> None:
    for field in FILE_REF_FIELDS:
        value = sample.get(field)
        if not _has_value(value):
            file_counts[field]["empty"] += 1
            if field in REQUIRED_FILE_REF_FIELDS:
                errors.append(f"samples[{index}] missing required file reference: {field}")
            continue
        resolved = resolve_sample_reference(str(value), sample_output_dir)
        if resolved is None:
            file_counts[field]["missing"] += 1
            errors.append(f"samples[{index}].{field} has unsupported URI: {value}")
            missing_file_refs.append(_missing_ref(index, field, str(value), None))
            continue
        if field == "annotated_image":
            _record_path_check(index, field, str(value), resolved, file_counts, missing_file_refs, warnings)
        else:
            _record_path_check(index, field, str(value), resolved, file_counts, missing_file_refs, errors)


def _record_path_check(
    index: int,
    field: str,
    original: str,
    resolved: Path,
    file_counts: Dict[str, Dict[str, int]],
    missing_file_refs: List[Dict[str, Any]],
    problems: List[str],
) -> None:
    if resolved.exists():
        file_counts[field]["present"] += 1
        return
    file_counts[field]["missing"] += 1
    problems.append(f"samples[{index}].{field} file not found: {original}")
    missing_file_refs.append(_missing_ref(index, field, original, resolved))


def _missing_ref(index: int, field: str, original: str, resolved: Optional[Path]) -> Dict[str, Any]:
    return {
        "sample_index": index,
        "field": field,
        "value": original,
        "resolved_path": str(resolved) if resolved is not None else "",
    }


def resolve_sample_reference(value: str, sample_output_dir: Path) -> Optional[Path]:
    """Resolve manifest file references without touching ROS2 runtime state."""
    if value.startswith(SAMPLE_URI_PREFIX):
        value = value[len(SAMPLE_URI_PREFIX) :]
    elif "://" in value:
        return None

    path = Path(os.path.expanduser(value))
    if path.is_absolute():
        return path
    return sample_output_dir / path


def _json_default(value: Any) -> str:
    if isinstance(value, Path):
        return str(value)
    return str(value)


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize and validate a trashbot vision sample manifest.")
    parser.add_argument("manifest", help="Path to a trashbot.vision_samples.v1 manifest JSON file.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    summary = summarize_manifest(args.manifest)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True, default=_json_default))
    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
