"""电梯 OpenCV baseline 的 ROS-free helper。

本模块故意不依赖 ROS2 daemon，也不强制依赖 cv2。现场图片接入通过 manifest
中的真实图片路径保留；单元测试用可控 PGM fixture 跑通 ROI/rule/eval 合同。
"""

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


SCHEMA = "trashbot.elevator_opencv_baseline.v1"
EVAL_SCHEMA = "trashbot.elevator_offline_eval.v1"
PROOF_STATUS = "not_proven"
TAXONOMY_VERSION = "elevator_taxonomy_v0"
FIELD_EVAL_STATUS = "needs_real_image_manifest"

DOOR_OPEN = "open"
DOOR_CLOSED = "closed"
DOOR_UNCERTAIN = "uncertain"
INSIDE = "inside"
OUTSIDE = "outside"
LOCATION_UNCERTAIN = "uncertain"
SAFE_TO_EXIT = "safe"
UNSAFE_TO_EXIT = "unsafe"
SAFE_UNCERTAIN = "uncertain"


@dataclass(frozen=True)
class Roi:
    """ROI 用归一化坐标，避免不同分辨率样本导致规则参数不可复用。"""

    x: float
    y: float
    width: float
    height: float


DEFAULT_ROIS = {
    # 门缝 ROI 放在画面中央，目标是先捕获开门时的中间亮带/暗带变化。
    "door_gap": Roi(0.46, 0.10, 0.08, 0.78),
    # 门板 ROI 取左右两侧；它用于和门缝亮度做对比，不直接当成类别真值。
    "door_panel_left": Roi(0.12, 0.10, 0.24, 0.78),
    "door_panel_right": Roi(0.64, 0.10, 0.24, 0.78),
    # 楼层屏 ROI 只输出候选框，不做 OCR，避免把 fixture 当成真实楼层识别。
    "floor_display": Roi(0.38, 0.02, 0.24, 0.14),
    # 地面 ROI 是出门安全的低成本 guard，真实环境还需要 Nav2/障碍物证据补强。
    "exit_path": Roi(0.28, 0.72, 0.44, 0.20),
}

DEFAULT_THRESHOLDS = {
    "open_gap_delta": 38.0,
    "closed_gap_delta": 16.0,
    "dark_inside_mean": 88.0,
    "safe_exit_mean": 105.0,
    "floor_panel_delta": 28.0,
    "min_confidence": 0.58,
}

NOT_PROVEN = [
    "real_camera_elevator_recognition",
    "real_floor_ocr",
    "real_target_floor_confirmation",
    "real_safe_exit",
    "real_cross_floor_delivery",
]

TAXONOMY_SAMPLE_REQUIREMENTS = {
    # taxonomy tag 明确绑定采集要求，避免“有一张 fixture”被误写成样本集完成。
    "door_open_positive": {
        "minimum": 20,
        "positive_label": "door_state=open",
        "negative_boundary": "closed/half-open/blocked door frames must stay out of this class",
        "collection": "真实或受控电梯门完全打开、门缝清晰、含不同楼层和光照。",
    },
    "door_closed_positive": {
        "minimum": 20,
        "positive_label": "door_state=closed",
        "negative_boundary": "open bright gap and partial reflection frames must be separate negatives",
        "collection": "真实或受控电梯门关闭，保留门缝、反光、广告贴纸等干扰。",
    },
    "inside_positive": {
        "minimum": 20,
        "positive_label": "inside_outside=inside",
        "negative_boundary": "hallway/outside frames cannot be reused as inside positives",
        "collection": "轿厢内视角，覆盖门开、门关、低照度、反光内壁。",
    },
    "outside_negative": {
        "minimum": 20,
        "positive_label": "inside_outside=outside",
        "negative_boundary": "standing at elevator threshold is a hard negative or uncertain sample",
        "collection": "电梯厅外视角，覆盖门口等待、侧向角度和人流遮挡。",
    },
    "floor_target_positive": {
        "minimum": 20,
        "positive_label": "target_floor_candidate == target_floor",
        "negative_boundary": "manifest-only target floor is not OCR truth",
        "collection": "楼层屏 ROI 可见且人工标注 target/expected floor 一致。",
    },
    "safe_exit_positive": {
        "minimum": 20,
        "positive_label": "safe_to_exit=safe",
        "negative_boundary": "safe means visual guard only, not Nav2 obstacle clearance",
        "collection": "门开、目标楼层候选匹配、出口区域无遮挡的受控样本。",
    },
    "safe_exit_negative": {
        "minimum": 20,
        "positive_label": "safe_to_exit=unsafe",
        "negative_boundary": "door closed/unknown floor/exit obstacle are separate unsafe reasons",
        "collection": "门未开、目标楼层不符、出口有障碍或视野过暗的负例。",
    },
    "uncertain_or_bad_light": {
        "minimum": 10,
        "positive_label": "uncertain",
        "negative_boundary": "must not be forced into open/safe happy path",
        "collection": "强反光、低照度、遮挡、画面倾斜、楼层屏过曝等不可判定样本。",
    },
}

QUALITY_GATE_DEFAULTS = {
    # 这些阈值只用于 offline eval guard；真实上线阈值需要实景样本重新定标。
    "software_guard_max_safe_exit_fp": 0,
    "software_guard_max_door_fp": 0,
    "software_guard_min_evaluated_count": 1,
    "field_eval_required_real_images_per_class": 20,
    "field_eval_max_safe_exit_fp_rate": 0.02,
    "field_eval_max_door_fn_rate": 0.10,
}


def elevator_taxonomy() -> Dict[str, Any]:
    """输出 taxonomy 合同；字段供 docs、eval 和未来 ROS2 adapter 共用。"""
    # 每个 label 都带上不可越界说明，防止 offline baseline 被误读为现场完成。
    return {
        "taxonomy_version": TAXONOMY_VERSION,
        "schema": SCHEMA,
        "labels": {
            "door_state": [DOOR_OPEN, DOOR_CLOSED, DOOR_UNCERTAIN],
            "inside_outside": [INSIDE, OUTSIDE, LOCATION_UNCERTAIN],
            "safe_to_exit": [SAFE_TO_EXIT, UNSAFE_TO_EXIT, SAFE_UNCERTAIN],
            "target_floor_candidate": "string_or_empty",
        },
        "roi_names": sorted(DEFAULT_ROIS.keys()),
        "taxonomy_classes": TAXONOMY_SAMPLE_REQUIREMENTS,
        "not_proven": list(NOT_PROVEN),
        "sample_requirements": {
            "door_open_positive_min": 20,
            "door_closed_positive_min": 20,
            "inside_positive_min": 20,
            "outside_negative_min": 20,
            "uncertain_or_bad_light_min": 10,
            "real_image_directory_required_for_field_eval": True,
        },
        "quality_gate_defaults": QUALITY_GATE_DEFAULTS,
        "manifest_expected_fields": [
            "sample_id",
            "image",
            "target_floor",
            "expected_floor",
            "expected_door_state",
            "expected_inside_outside",
            "expected_safe_to_exit",
            "taxonomy_tags",
        ],
        "failure_boundaries": [
            "强反光、低照度、遮挡、玻璃门和画面倾斜会直接降级 uncertain。",
            "target_floor_candidate 目前只接受 manifest 人工候选或简单 ROI 明暗候选，不是 OCR。",
            "safe_to_exit 只表示画面地面 ROI 没有明显暗障碍，不等于 Nav2 可安全驶出。",
        ],
    }


def analyze_image_path(
    image_path: str,
    *,
    target_floor: str = "",
    expected_floor: str = "",
    rois: Optional[Dict[str, Roi]] = None,
    thresholds: Optional[Dict[str, float]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """读取图片并执行 baseline；真实图片路径和 fixture 路径走同一入口。"""
    matrix = _read_grayscale_image(Path(image_path))
    return analyze_grayscale_matrix(
        matrix,
        sample_id=Path(image_path).stem,
        image_ref=str(image_path),
        target_floor=target_floor,
        expected_floor=expected_floor,
        rois=rois,
        thresholds=thresholds,
        metadata=metadata,
    )


def analyze_grayscale_matrix(
    matrix: Sequence[Sequence[int]],
    *,
    sample_id: str,
    image_ref: str,
    target_floor: str = "",
    expected_floor: str = "",
    rois: Optional[Dict[str, Roi]] = None,
    thresholds: Optional[Dict[str, float]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """对灰度矩阵跑 ROI rule，并返回稳定 JSON schema。"""
    # 规则只使用均值/对比度，便于在没有 cv2 的 CI 中复现和解释。
    checked = _validate_matrix(matrix)
    active_rois = dict(DEFAULT_ROIS if rois is None else rois)
    active_thresholds = dict(DEFAULT_THRESHOLDS)
    if thresholds:
        active_thresholds.update(thresholds)

    roi_stats = {
        name: _roi_stats(checked, roi)
        for name, roi in active_rois.items()
    }
    door_state, door_confidence, door_reasons = _classify_door(roi_stats, active_thresholds)
    inside_outside, inside_confidence, inside_reasons = _classify_inside_outside(roi_stats, active_thresholds)
    floor_candidate, floor_confidence, floor_reasons = _classify_floor_candidate(
        roi_stats,
        active_thresholds,
        target_floor=target_floor,
        expected_floor=expected_floor,
    )
    safe_to_exit, safe_confidence, safe_reasons = _classify_safe_to_exit(
        door_state,
        inside_outside,
        roi_stats,
        active_thresholds,
        floor_candidate=floor_candidate,
        target_floor=target_floor,
    )

    # 总置信度取最弱环节；电梯状态链宁可 uncertain，也不能 happy path 放大风险。
    confidence = min(door_confidence, inside_confidence, floor_confidence, safe_confidence)
    uncertain_reasons = door_reasons + inside_reasons + floor_reasons + safe_reasons
    return {
        "schema": SCHEMA,
        "taxonomy_version": TAXONOMY_VERSION,
        "proof_status": PROOF_STATUS,
        "sample_id": sample_id,
        "image_ref": image_ref,
        "door_state": door_state,
        "inside_outside": inside_outside,
        "floor_roi": _roi_to_dict(active_rois["floor_display"]),
        "target_floor_candidate": floor_candidate,
        "safe_to_exit": safe_to_exit,
        "confidence": round(confidence, 4),
        "roi_stats": roi_stats,
        "thresholds": active_thresholds,
        "not_proven": list(NOT_PROVEN),
        "uncertain_reasons": uncertain_reasons,
        "metadata": dict(metadata or {}),
    }


def evaluate_manifest(manifest_path: str) -> Dict[str, Any]:
    """执行离线 manifest eval，汇总 door/safe 的 FP/FN 和不可判定。"""
    manifest_file = Path(manifest_path).expanduser()
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    image_root = _resolve_image_root(manifest, manifest_file)
    samples = manifest.get("samples", [])
    if not isinstance(samples, list):
        raise ValueError("manifest.samples must be a list")

    predictions: List[Dict[str, Any]] = []
    confusion = _empty_confusion()
    errors: List[str] = []
    for index, sample in enumerate(samples):
        if not isinstance(sample, dict):
            errors.append(f"samples[{index}] must be an object")
            continue
        try:
            prediction = _predict_manifest_sample(sample, image_root)
        except (OSError, ValueError, KeyError) as exc:
            errors.append(f"samples[{index}] eval failed: {exc}")
            continue
        predictions.append(prediction)
        _update_confusion(confusion, prediction, sample)

    sample_coverage = _manifest_sample_coverage(samples, predictions)
    quality_metrics = _quality_metrics(confusion, sample_coverage, errors)
    return {
        "schema": EVAL_SCHEMA,
        "baseline_schema": SCHEMA,
        "manifest_path": str(manifest_file),
        "image_root": str(image_root),
        "sample_count": len(samples),
        "evaluated_count": len(predictions),
        "predictions": predictions,
        "confusion": confusion,
        "sample_coverage": sample_coverage,
        "quality_metrics": quality_metrics,
        "acceptance_gates": _acceptance_gates(quality_metrics, sample_coverage),
        "errors": errors,
        "not_proven": list(NOT_PROVEN),
        "operator_summary": _operator_summary(confusion, errors, quality_metrics),
    }


def _predict_manifest_sample(sample: Dict[str, Any], image_root: Path) -> Dict[str, Any]:
    image_value = sample.get("image") or sample.get("image_path") or sample.get("raw_image")
    if not isinstance(image_value, str) or not image_value.strip():
        raise ValueError("sample image path is required")
    image_path = _resolve_path(image_value, image_root)
    target_floor = str(sample.get("target_floor", ""))
    expected_floor = str(sample.get("expected_floor", ""))
    sample_id = str(sample.get("sample_id", image_path.stem))
    metadata = {"manifest_sample": sample_id, "taxonomy_tags": _sample_tags(sample)}
    prediction = analyze_image_path(
        str(image_path),
        target_floor=target_floor,
        expected_floor=expected_floor,
        metadata=metadata,
    )
    # manifest sample_id 是人工/采样系统的稳定主键，不能被图片文件名覆盖。
    prediction["sample_id"] = sample_id
    prediction["manifest_tags"] = _sample_tags(sample)
    prediction["expected"] = {
        "door_state": str(sample.get("expected_door_state", "")),
        "inside_outside": str(sample.get("expected_inside_outside", "")),
        "safe_to_exit": str(sample.get("expected_safe_to_exit", "")),
        "target_floor": target_floor,
        "expected_floor": expected_floor,
    }
    prediction["image_kind"] = _image_kind(image_path)
    return prediction


def _empty_confusion() -> Dict[str, Any]:
    return {
        "door_state": {"tp": 0, "tn": 0, "fp": 0, "fn": 0, "uncertain": 0},
        "safe_to_exit": {"tp": 0, "tn": 0, "fp": 0, "fn": 0, "uncertain": 0},
        "inside_outside": {"matches": 0, "mismatches": 0, "uncertain": 0},
    }


def _update_confusion(confusion: Dict[str, Any], prediction: Dict[str, Any], sample: Dict[str, Any]) -> None:
    expected_door = str(sample.get("expected_door_state", ""))
    expected_safe = str(sample.get("expected_safe_to_exit", ""))
    expected_location = str(sample.get("expected_inside_outside", ""))
    _update_binary_confusion(confusion["door_state"], prediction["door_state"], expected_door, positive=DOOR_OPEN)
    _update_binary_confusion(confusion["safe_to_exit"], prediction["safe_to_exit"], expected_safe, positive=SAFE_TO_EXIT)
    if expected_location:
        if prediction["inside_outside"] == LOCATION_UNCERTAIN:
            confusion["inside_outside"]["uncertain"] += 1
        elif prediction["inside_outside"] == expected_location:
            confusion["inside_outside"]["matches"] += 1
        else:
            confusion["inside_outside"]["mismatches"] += 1


def _update_binary_confusion(bucket: Dict[str, int], predicted: str, expected: str, *, positive: str) -> None:
    if not expected:
        return
    if predicted == DOOR_UNCERTAIN or predicted == SAFE_UNCERTAIN:
        bucket["uncertain"] += 1
        return
    expected_positive = expected == positive
    predicted_positive = predicted == positive
    if predicted_positive and expected_positive:
        bucket["tp"] += 1
    elif predicted_positive and not expected_positive:
        bucket["fp"] += 1
    elif not predicted_positive and expected_positive:
        bucket["fn"] += 1
    else:
        bucket["tn"] += 1


def _operator_summary(
    confusion: Dict[str, Any],
    errors: Sequence[str],
    quality_metrics: Dict[str, Any],
) -> Dict[str, Any]:
    # summary 给 PC/手机安全提示消费，避免用户看到模型术语后误判为现场通过。
    return {
        "status": "needs_real_image_review" if errors else "offline_fixture_eval_complete",
        "door_fp": confusion["door_state"]["fp"],
        "door_fn": confusion["door_state"]["fn"],
        "safe_exit_fp": confusion["safe_to_exit"]["fp"],
        "safe_exit_fn": confusion["safe_to_exit"]["fn"],
        "uncertain_total": (
            confusion["door_state"]["uncertain"]
            + confusion["safe_to_exit"]["uncertain"]
            + confusion["inside_outside"]["uncertain"]
        ),
        "software_guard_pass": quality_metrics["software_guard_pass"],
        "field_eval_ready": quality_metrics["field_eval_ready"],
        "field_eval_status": FIELD_EVAL_STATUS,
        "not_proven": list(NOT_PROVEN),
    }


def _manifest_sample_coverage(
    samples: Sequence[Any],
    predictions: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    """统计 manifest 覆盖；coverage 是采集进度，不是模型准确率。"""
    counts = {tag: 0 for tag in TAXONOMY_SAMPLE_REQUIREMENTS}
    image_kinds = {"fixture": 0, "real_or_controlled": 0, "missing_or_invalid": 0}
    for sample in samples:
        if not isinstance(sample, dict):
            image_kinds["missing_or_invalid"] += 1
            continue
        for tag in _sample_tags(sample):
            if tag in counts:
                counts[tag] += 1
    for prediction in predictions:
        kind = prediction.get("image_kind")
        if kind in image_kinds:
            image_kinds[kind] += 1

    missing = {
        tag: max(0, spec["minimum"] - counts[tag])
        for tag, spec in TAXONOMY_SAMPLE_REQUIREMENTS.items()
    }
    return {
        "taxonomy_version": TAXONOMY_VERSION,
        "counts": counts,
        "minimums": {tag: spec["minimum"] for tag, spec in TAXONOMY_SAMPLE_REQUIREMENTS.items()},
        "missing_to_field_minimum": missing,
        "field_minimum_met": all(value == 0 for value in missing.values()),
        "image_kinds": image_kinds,
        "real_image_directory_required_for_field_eval": True,
    }


def _quality_metrics(
    confusion: Dict[str, Any],
    sample_coverage: Dict[str, Any],
    errors: Sequence[str],
) -> Dict[str, Any]:
    """把 FP/FN 转成可验收数字；缺分母时返回 None，不伪造准确率。"""
    door = confusion["door_state"]
    safe = confusion["safe_to_exit"]
    evaluated_count = sum(door.values())
    safe_eval_count = sum(safe.values())
    software_guard_pass = (
        not errors
        and evaluated_count >= QUALITY_GATE_DEFAULTS["software_guard_min_evaluated_count"]
        and door["fp"] <= QUALITY_GATE_DEFAULTS["software_guard_max_door_fp"]
        and safe["fp"] <= QUALITY_GATE_DEFAULTS["software_guard_max_safe_exit_fp"]
    )
    field_eval_ready = (
        sample_coverage["field_minimum_met"]
        and sample_coverage["image_kinds"]["real_or_controlled"] >= sum(sample_coverage["minimums"].values())
    )
    return {
        "door_state_precision": _rate(door["tp"], door["tp"] + door["fp"]),
        "door_state_recall": _rate(door["tp"], door["tp"] + door["fn"]),
        "door_state_fp_rate": _rate(door["fp"], evaluated_count),
        "door_state_fn_rate": _rate(door["fn"], evaluated_count),
        "safe_exit_precision": _rate(safe["tp"], safe["tp"] + safe["fp"]),
        "safe_exit_recall": _rate(safe["tp"], safe["tp"] + safe["fn"]),
        "safe_exit_fp_rate": _rate(safe["fp"], safe_eval_count),
        "safe_exit_fn_rate": _rate(safe["fn"], safe_eval_count),
        "uncertain_total": door["uncertain"] + safe["uncertain"] + confusion["inside_outside"]["uncertain"],
        "software_guard_pass": software_guard_pass,
        "field_eval_ready": field_eval_ready,
        "field_eval_status": FIELD_EVAL_STATUS,
    }


def _acceptance_gates(
    quality_metrics: Dict[str, Any],
    sample_coverage: Dict[str, Any],
) -> Dict[str, Any]:
    """输出 gate 条件和当前状态，供 coordinator 写 tech-done 时直接引用。"""
    return {
        "software_guard": {
            "pass": quality_metrics["software_guard_pass"],
            "requires": {
                "errors": 0,
                "door_fp_max": QUALITY_GATE_DEFAULTS["software_guard_max_door_fp"],
                "safe_exit_fp_max": QUALITY_GATE_DEFAULTS["software_guard_max_safe_exit_fp"],
                "evaluated_count_min": QUALITY_GATE_DEFAULTS["software_guard_min_evaluated_count"],
            },
            "boundary": "software_guard only; fixture/offline eval is not field elevator completion",
        },
        "field_eval": {
            "pass": quality_metrics["field_eval_ready"],
            "requires": {
                "real_or_controlled_images": True,
                "minimums": sample_coverage["minimums"],
                "max_safe_exit_fp_rate": QUALITY_GATE_DEFAULTS["field_eval_max_safe_exit_fp_rate"],
                "max_door_fn_rate": QUALITY_GATE_DEFAULTS["field_eval_max_door_fn_rate"],
            },
            "boundary": "requires real/control image manifest and later ROS2 state integration evidence",
        },
    }


def _sample_tags(sample: Dict[str, Any]) -> List[str]:
    """从 manifest expected 字段推导 taxonomy tag；允许采集端显式补充。"""
    tags = []
    explicit = sample.get("taxonomy_tags", [])
    if isinstance(explicit, list):
        tags.extend(str(item) for item in explicit)
    expected_door = str(sample.get("expected_door_state", ""))
    expected_location = str(sample.get("expected_inside_outside", ""))
    expected_safe = str(sample.get("expected_safe_to_exit", ""))
    target_floor = str(sample.get("target_floor", ""))
    expected_floor = str(sample.get("expected_floor", ""))
    if expected_door == DOOR_OPEN:
        tags.append("door_open_positive")
    elif expected_door == DOOR_CLOSED:
        tags.append("door_closed_positive")
    elif expected_door == DOOR_UNCERTAIN:
        tags.append("uncertain_or_bad_light")
    if expected_location == INSIDE:
        tags.append("inside_positive")
    elif expected_location == OUTSIDE:
        tags.append("outside_negative")
    if target_floor and expected_floor and target_floor == expected_floor:
        tags.append("floor_target_positive")
    if expected_safe == SAFE_TO_EXIT:
        tags.append("safe_exit_positive")
    elif expected_safe == UNSAFE_TO_EXIT:
        tags.append("safe_exit_negative")
    return sorted(set(tag for tag in tags if tag in TAXONOMY_SAMPLE_REQUIREMENTS))


def _image_kind(image_path: Path) -> str:
    # PGM 是本仓库离线 fixture 主格式；JPEG/PNG 等才可能进入真实/受控图片评估。
    return "fixture" if image_path.suffix.lower() == ".pgm" else "real_or_controlled"


def _rate(numerator: int, denominator: int) -> Optional[float]:
    if denominator <= 0:
        return None
    return round(float(numerator) / float(denominator), 4)


def _classify_door(roi_stats: Dict[str, Dict[str, float]], thresholds: Dict[str, float]) -> Tuple[str, float, List[str]]:
    gap_mean = roi_stats["door_gap"]["mean"]
    panel_mean = (roi_stats["door_panel_left"]["mean"] + roi_stats["door_panel_right"]["mean"]) / 2.0
    delta = abs(gap_mean - panel_mean)
    if delta >= thresholds["open_gap_delta"]:
        return DOOR_OPEN, _confidence(delta, thresholds["open_gap_delta"], 82.0), []
    if delta <= thresholds["closed_gap_delta"]:
        return DOOR_CLOSED, _confidence(thresholds["closed_gap_delta"] - delta, 0.0, 22.0), []
    return DOOR_UNCERTAIN, 0.42, [f"door_gap_delta_uncertain:{delta:.2f}"]


def _classify_inside_outside(roi_stats: Dict[str, Dict[str, float]], thresholds: Dict[str, float]) -> Tuple[str, float, List[str]]:
    panel_mean = (roi_stats["door_panel_left"]["mean"] + roi_stats["door_panel_right"]["mean"]) / 2.0
    if panel_mean <= thresholds["dark_inside_mean"]:
        return INSIDE, _confidence(thresholds["dark_inside_mean"] - panel_mean, 0.0, 68.0), []
    if panel_mean >= thresholds["dark_inside_mean"] + 42.0:
        return OUTSIDE, _confidence(panel_mean - thresholds["dark_inside_mean"], 42.0, 110.0), []
    return LOCATION_UNCERTAIN, 0.45, [f"inside_outside_lighting_uncertain:{panel_mean:.2f}"]


def _classify_floor_candidate(
    roi_stats: Dict[str, Dict[str, float]],
    thresholds: Dict[str, float],
    *,
    target_floor: str,
    expected_floor: str,
) -> Tuple[str, float, List[str]]:
    floor_mean = roi_stats["floor_display"]["mean"]
    panel_mean = (roi_stats["door_panel_left"]["mean"] + roi_stats["door_panel_right"]["mean"]) / 2.0
    if expected_floor:
        return expected_floor, 0.76, []
    if target_floor and abs(floor_mean - panel_mean) >= thresholds["floor_panel_delta"]:
        return target_floor, _confidence(abs(floor_mean - panel_mean), thresholds["floor_panel_delta"], 88.0), []
    return "", 0.52, ["target_floor_not_confirmed"]


def _classify_safe_to_exit(
    door_state: str,
    inside_outside: str,
    roi_stats: Dict[str, Dict[str, float]],
    thresholds: Dict[str, float],
    *,
    floor_candidate: str,
    target_floor: str,
) -> Tuple[str, float, List[str]]:
    reasons: List[str] = []
    if door_state != DOOR_OPEN:
        reasons.append(f"door_not_open:{door_state}")
    if inside_outside != INSIDE:
        reasons.append(f"not_inside_elevator:{inside_outside}")
    if target_floor and floor_candidate != target_floor:
        reasons.append("target_floor_not_matched")
    exit_mean = roi_stats["exit_path"]["mean"]
    if exit_mean < thresholds["safe_exit_mean"]:
        reasons.append(f"exit_path_too_dark:{exit_mean:.2f}")
    if reasons:
        # 只要任一安全前提缺失，输出 unsafe/uncertain，供状态机 fail-closed。
        return UNSAFE_TO_EXIT if door_state != DOOR_UNCERTAIN else SAFE_UNCERTAIN, 0.48, reasons
    return SAFE_TO_EXIT, _confidence(exit_mean, thresholds["safe_exit_mean"], 180.0), []


def _confidence(value: float, lower: float, upper: float) -> float:
    if upper <= lower:
        return 0.5
    ratio = max(0.0, min(1.0, (value - lower) / (upper - lower)))
    return round(0.58 + ratio * 0.37, 4)


def _roi_stats(matrix: Sequence[Sequence[int]], roi: Roi) -> Dict[str, float]:
    height = len(matrix)
    width = len(matrix[0])
    x0 = _clamp_int(int(round(roi.x * width)), 0, width - 1)
    y0 = _clamp_int(int(round(roi.y * height)), 0, height - 1)
    x1 = _clamp_int(int(round((roi.x + roi.width) * width)), x0 + 1, width)
    y1 = _clamp_int(int(round((roi.y + roi.height) * height)), y0 + 1, height)
    values = [matrix[y][x] for y in range(y0, y1) for x in range(x0, x1)]
    mean = sum(values) / float(len(values))
    return {
        "x0": float(x0),
        "y0": float(y0),
        "x1": float(x1),
        "y1": float(y1),
        "mean": round(mean, 4),
        "min": float(min(values)),
        "max": float(max(values)),
    }


def _validate_matrix(matrix: Sequence[Sequence[int]]) -> Sequence[Sequence[int]]:
    if not matrix or not matrix[0]:
        raise ValueError("image matrix must not be empty")
    width = len(matrix[0])
    for row in matrix:
        if len(row) != width:
            raise ValueError("image matrix rows must have equal width")
        for value in row:
            if value < 0 or value > 255:
                raise ValueError("image matrix values must be 0..255")
    return matrix


def _read_grayscale_image(path: Path) -> List[List[int]]:
    """优先读 PGM fixture；真实 JPEG/PNG 环境有 cv2 时走 cv2 灰度读取。"""
    if not path.exists():
        raise OSError(f"image not found: {path}")
    if path.suffix.lower() == ".pgm":
        return _read_pgm(path)
    try:
        import cv2  # type: ignore
    except ImportError as exc:
        raise OSError(f"cv2 is required for non-PGM image input: {path}") from exc
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise OSError(f"cv2 failed to read image: {path}")
    return image.astype("uint8").tolist()


def _read_pgm(path: Path) -> List[List[int]]:
    data = path.read_bytes()
    tokens = _pgm_tokens(data)
    if len(tokens) < 4 or tokens[0] != b"P2":
        raise ValueError("only ASCII P2 PGM fixtures are supported without cv2")
    width = int(tokens[1])
    height = int(tokens[2])
    max_value = int(tokens[3])
    if max_value <= 0:
        raise ValueError("PGM max value must be positive")
    values = [int(token) for token in tokens[4:]]
    if len(values) != width * height:
        raise ValueError("PGM pixel count does not match width*height")
    scale = 255.0 / float(max_value)
    return [
        [int(round(values[y * width + x] * scale)) for x in range(width)]
        for y in range(height)
    ]


def _pgm_tokens(data: bytes) -> List[bytes]:
    tokens: List[bytes] = []
    for line in data.splitlines():
        # PGM 注释以 # 开头；测试 fixture 用它记录样本语义不会影响像素解析。
        clean = line.split(b"#", 1)[0].strip()
        if clean:
            tokens.extend(clean.split())
    return tokens


def _resolve_image_root(manifest: Dict[str, Any], manifest_file: Path) -> Path:
    image_dir = manifest.get("image_dir") or manifest.get("sample_output_dir") or "."
    return _resolve_path(str(image_dir), manifest_file.parent)


def _resolve_path(value: str, root: Path) -> Path:
    expanded = Path(os.path.expanduser(value))
    if expanded.is_absolute():
        return expanded
    return (root / expanded).resolve()


def _roi_to_dict(roi: Roi) -> Dict[str, float]:
    return {"x": roi.x, "y": roi.y, "width": roi.width, "height": roi.height}


def _clamp_int(value: int, lower: int, upper: int) -> int:
    return max(lower, min(value, upper))


def _json_default(value: Any) -> str:
    return str(value)


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run offline elevator OpenCV baseline evaluation.")
    parser.add_argument("manifest", help="JSON manifest with image_dir and samples.")
    parser.add_argument("--taxonomy", action="store_true", help="Print taxonomy instead of running eval.")
    args = parser.parse_args(list(argv) if argv is not None else None)
    output = elevator_taxonomy() if args.taxonomy else evaluate_manifest(args.manifest)
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True, default=_json_default))
    return 1 if output.get("errors") else 0


if __name__ == "__main__":
    raise SystemExit(main())
