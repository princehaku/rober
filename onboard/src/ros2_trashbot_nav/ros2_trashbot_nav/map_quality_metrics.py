"""Nav2/map quality 的 ROS-free 离线评估 helper。

本模块只读取 map YAML、PGM 和 waypoint JSON，不连接 ROS graph、不启动 Nav2。
它的价值是把“地图能不能进入实跑候选”提前变成可复验数字和失败原因。
"""

import argparse
import ast
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


SCHEMA = "trashbot.nav2_map_quality.v1"
PROOF_STATUS = "not_proven"
SOURCE = "software_proof"

NOT_PROVEN = [
    "real_slam_map_runtime",
    "real_amcl_localization",
    "real_nav2_scan_map_consumption",
    "real_fixed_route_execution",
    "real_waypoint_reachability",
]

DEFAULT_THRESHOLDS = {
    # 阈值偏保守；真实场地图要结合路线长度、净空和现场安全再重新定标。
    "occupied_pixel_max": 65,
    "unknown_pixel_min": 185,
    "unknown_pixel_max": 220,
    "free_pixel_min": 230,
    "max_unknown_ratio": 0.35,
    "min_coverage_area_m2": 1.0,
    "min_reachable_waypoint_ratio": 0.80,
}


def evaluate_map_quality(
    map_yaml_path: str,
    *,
    waypoint_path: Optional[str] = None,
    thresholds: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """输出地图覆盖率、未知区比例、waypoint 可达性和保存/加载一致性。"""
    active_thresholds = dict(DEFAULT_THRESHOLDS)
    if thresholds:
        active_thresholds.update(thresholds)

    yaml_path = Path(map_yaml_path).expanduser().resolve()
    metadata = _read_map_yaml(yaml_path)
    image_path = _resolve_image_path(metadata, yaml_path)
    pixels, width, height = _read_pgm(image_path)
    pixel_counts = _pixel_counts(pixels, active_thresholds)
    metrics = _coverage_metrics(pixel_counts, metadata, width, height)
    waypoints = _load_waypoints(waypoint_path) if waypoint_path else []
    reachability = _waypoint_reachability(waypoints, pixels, width, height, metadata, active_thresholds)
    consistency = _save_load_consistency(yaml_path, image_path, metadata, width, height)
    gates = _quality_gates(metrics, reachability, consistency, active_thresholds)
    failures = _failure_samples(reachability, metrics, consistency, active_thresholds)

    return {
        "schema": SCHEMA,
        "source": SOURCE,
        "proof_status": PROOF_STATUS,
        "map_yaml": str(yaml_path),
        "map_image": str(image_path),
        "thresholds": active_thresholds,
        "metadata": metadata,
        "metrics": metrics,
        "save_load_consistency": consistency,
        "waypoint_reachability": reachability,
        "quality_gates": gates,
        "failure_samples": failures,
        "not_proven": list(NOT_PROVEN),
    }


def _read_map_yaml(path: Path) -> Dict[str, Any]:
    """读取 map_server YAML 子集；不用 PyYAML，避免本地环境缺依赖。"""
    if not path.exists():
        raise OSError(f"map yaml not found: {path}")
    data: Dict[str, Any] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = _parse_yaml_scalar(value.strip())
    if "image" not in data:
        raise ValueError("map yaml missing image field")
    resolution = float(data.get("resolution", 0.0))
    if resolution <= 0.0:
        raise ValueError("map yaml resolution must be positive")
    origin = data.get("origin", [0.0, 0.0, 0.0])
    if not isinstance(origin, list) or len(origin) < 2:
        raise ValueError("map yaml origin must be a list with x/y")
    return {
        "image": str(data["image"]),
        "resolution": resolution,
        "origin": [float(origin[0]), float(origin[1]), float(origin[2] if len(origin) > 2 else 0.0)],
        "occupied_thresh": float(data.get("occupied_thresh", 0.65)),
        "free_thresh": float(data.get("free_thresh", 0.196)),
        "negate": int(data.get("negate", 0)),
    }


def _parse_yaml_scalar(value: str) -> Any:
    """解析简单 scalar/list；map yaml 目前只需要 image/resolution/origin。"""
    if not value:
        return ""
    try:
        return ast.literal_eval(value)
    except (SyntaxError, ValueError):
        pass
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        return float(value) if "." in value else int(value)
    except ValueError:
        return value.strip("\"'")


def _resolve_image_path(metadata: Dict[str, Any], yaml_path: Path) -> Path:
    image_value = os.path.expanduser(str(metadata["image"]))
    image_path = Path(image_value)
    if image_path.is_absolute():
        return image_path
    return (yaml_path.parent / image_path).resolve()


def _read_pgm(path: Path) -> Tuple[List[int], int, int]:
    """支持 P2/P5 PGM；SLAM Toolbox/map_server 常见 PGM 都能离线读取。"""
    if not path.exists():
        raise OSError(f"map image not found: {path}")
    data = path.read_bytes()
    magic, index = _next_token(data, 0)
    width_token, index = _next_token(data, index)
    height_token, index = _next_token(data, index)
    max_token, index = _next_token(data, index)
    width = int(width_token)
    height = int(height_token)
    max_value = int(max_token)
    if width <= 0 or height <= 0 or max_value <= 0:
        raise ValueError("PGM width/height/max value must be positive")
    expected = width * height
    if magic == b"P2":
        values = [int(token) for token in _ascii_tokens(data[index:])]
    elif magic == b"P5":
        # P5 header 后会有一个空白分隔符；跳过后直接读取二进制像素。
        while index < len(data) and data[index] in b" \t\r\n":
            index += 1
        values = list(data[index:index + expected])
    else:
        raise ValueError("only P2/P5 PGM maps are supported")
    if len(values) != expected:
        raise ValueError("PGM pixel count does not match width*height")
    if max_value != 255:
        scale = 255.0 / float(max_value)
        values = [int(round(value * scale)) for value in values]
    return values, width, height


def _next_token(data: bytes, index: int) -> Tuple[bytes, int]:
    """读取 PGM header token，并跳过 # 注释。"""
    length = len(data)
    while index < length:
        byte = data[index]
        if byte in b" \t\r\n":
            index += 1
            continue
        if byte == ord("#"):
            while index < length and data[index] not in b"\r\n":
                index += 1
            continue
        break
    start = index
    while index < length and data[index] not in b" \t\r\n":
        index += 1
    return data[start:index], index


def _ascii_tokens(data: bytes) -> List[bytes]:
    tokens: List[bytes] = []
    for line in data.splitlines():
        clean = line.split(b"#", 1)[0].strip()
        if clean:
            tokens.extend(clean.split())
    return tokens


def _pixel_counts(pixels: Sequence[int], thresholds: Dict[str, float]) -> Dict[str, int]:
    """按 map_server 常见灰度语义分类：0 墙、205 unknown、254 free。"""
    counts = {"free": 0, "occupied": 0, "unknown": 0, "ambiguous": 0}
    for value in pixels:
        label = _classify_pixel(value, thresholds)
        counts[label] += 1
    return counts


def _classify_pixel(value: int, thresholds: Dict[str, float]) -> str:
    if value <= thresholds["occupied_pixel_max"]:
        return "occupied"
    if thresholds["unknown_pixel_min"] <= value <= thresholds["unknown_pixel_max"]:
        return "unknown"
    if value >= thresholds["free_pixel_min"]:
        return "free"
    return "ambiguous"


def _coverage_metrics(
    counts: Dict[str, int],
    metadata: Dict[str, Any],
    width: int,
    height: int,
) -> Dict[str, Any]:
    """把像素数换算成面积和比例；unknown/ambiguous 都阻塞实跑候选。"""
    total = width * height
    resolution = metadata["resolution"]
    cell_area = resolution * resolution
    return {
        "width": width,
        "height": height,
        "resolution_m": resolution,
        "total_cells": total,
        "free_cells": counts["free"],
        "occupied_cells": counts["occupied"],
        "unknown_cells": counts["unknown"],
        "ambiguous_cells": counts["ambiguous"],
        "coverage_area_m2": round(counts["free"] * cell_area, 4),
        "explored_area_m2": round((counts["free"] + counts["occupied"]) * cell_area, 4),
        "free_ratio": _ratio(counts["free"], total),
        "occupied_ratio": _ratio(counts["occupied"], total),
        "unknown_ratio": _ratio(counts["unknown"] + counts["ambiguous"], total),
    }


def _load_waypoints(path_value: Optional[str]) -> List[Dict[str, Any]]:
    """读取 waypoint JSON；格式保持简单，方便 PC/route 工具复用。"""
    if not path_value:
        return []
    path = Path(path_value).expanduser().resolve()
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        waypoints = data.get("waypoints", [])
    else:
        waypoints = data
    if not isinstance(waypoints, list):
        raise ValueError("waypoints must be a list")
    return [dict(item) for item in waypoints if isinstance(item, dict)]


def _waypoint_reachability(
    waypoints: Sequence[Dict[str, Any]],
    pixels: Sequence[int],
    width: int,
    height: int,
    metadata: Dict[str, Any],
    thresholds: Dict[str, float],
) -> Dict[str, Any]:
    """检查 waypoint 是否落在 free cell；这是 map 候选过滤，不是 Nav2 实跑。"""
    items: List[Dict[str, Any]] = []
    summary = {"total": 0, "reachable": 0, "blocked": 0, "unknown": 0, "out_of_bounds": 0, "frame_mismatch": 0}
    for index, waypoint in enumerate(waypoints):
        summary["total"] += 1
        frame_id = str(waypoint.get("frame_id", "map"))
        if frame_id != "map":
            summary["frame_mismatch"] += 1
            items.append(_waypoint_item(index, waypoint, "frame_mismatch", "waypoint frame_id is not map"))
            continue
        x = float(waypoint.get("x", 0.0))
        y = float(waypoint.get("y", 0.0))
        pixel = _world_to_pixel(x, y, width, height, metadata)
        if pixel is None:
            summary["out_of_bounds"] += 1
            items.append(_waypoint_item(index, waypoint, "out_of_bounds", "waypoint is outside map image"))
            continue
        col, row = pixel
        value = pixels[row * width + col]
        label = _classify_pixel(value, thresholds)
        if label == "free":
            summary["reachable"] += 1
            reason = ""
        elif label == "occupied":
            summary["blocked"] += 1
            reason = "waypoint falls on occupied cell"
        else:
            summary["unknown"] += 1
            reason = f"waypoint falls on {label} cell"
        items.append({
            **_waypoint_item(index, waypoint, label, reason),
            "pixel": {"x": col, "y": row, "value": value},
        })
    summary["reachable_ratio"] = _ratio(summary["reachable"], summary["total"])
    return {"summary": summary, "items": items}


def _world_to_pixel(
    x: float,
    y: float,
    width: int,
    height: int,
    metadata: Dict[str, Any],
) -> Optional[Tuple[int, int]]:
    origin_x, origin_y = metadata["origin"][0], metadata["origin"][1]
    resolution = metadata["resolution"]
    col = int((x - origin_x) / resolution)
    row_from_bottom = int((y - origin_y) / resolution)
    row = height - 1 - row_from_bottom
    if col < 0 or col >= width or row < 0 or row >= height:
        return None
    return col, row


def _waypoint_item(index: int, waypoint: Dict[str, Any], status: str, reason: str) -> Dict[str, Any]:
    return {
        "index": index,
        "status": status,
        "reason": reason,
        "waypoint": {
            "frame_id": str(waypoint.get("frame_id", "map")),
            "x": float(waypoint.get("x", 0.0)),
            "y": float(waypoint.get("y", 0.0)),
        },
    }


def _save_load_consistency(
    yaml_path: Path,
    image_path: Path,
    metadata: Dict[str, Any],
    width: int,
    height: int,
) -> Dict[str, Any]:
    """检查 map artifact 的基本一致性；不代表 map_server 已启动成功。"""
    return {
        "yaml_exists": yaml_path.exists(),
        "image_exists": image_path.exists(),
        "image_ref_matches": bool(metadata.get("image")),
        "resolution_positive": metadata["resolution"] > 0.0,
        "origin_xy_present": len(metadata["origin"]) >= 2,
        "image_dimensions": {"width": width, "height": height},
        "consistent": yaml_path.exists() and image_path.exists() and metadata["resolution"] > 0.0 and width > 0 and height > 0,
    }


def _quality_gates(
    metrics: Dict[str, Any],
    reachability: Dict[str, Any],
    consistency: Dict[str, Any],
    thresholds: Dict[str, float],
) -> Dict[str, Any]:
    reachable_ratio = reachability["summary"]["reachable_ratio"]
    waypoint_gate = True if reachable_ratio is None else reachable_ratio >= thresholds["min_reachable_waypoint_ratio"]
    return {
        "software_guard_pass": (
            consistency["consistent"]
            and metrics["coverage_area_m2"] >= thresholds["min_coverage_area_m2"]
            and metrics["unknown_ratio"] <= thresholds["max_unknown_ratio"]
            and waypoint_gate
        ),
        "coverage_area_m2_min": thresholds["min_coverage_area_m2"],
        "unknown_ratio_max": thresholds["max_unknown_ratio"],
        "reachable_waypoint_ratio_min": thresholds["min_reachable_waypoint_ratio"],
        "boundary": "software_guard only; requires ROS2/Nav2 runtime before OKR progress can rise",
    }


def _failure_samples(
    reachability: Dict[str, Any],
    metrics: Dict[str, Any],
    consistency: Dict[str, Any],
    thresholds: Dict[str, float],
) -> List[Dict[str, Any]]:
    """聚合失败样例；状态页可以直接展示这些 reason。"""
    failures = []
    if not consistency["consistent"]:
        failures.append({"kind": "map_artifact", "reason": "map yaml/image consistency failed"})
    if metrics["unknown_ratio"] > thresholds["max_unknown_ratio"]:
        failures.append({"kind": "map_quality", "reason": "unknown ratio too high", "unknown_ratio": metrics["unknown_ratio"]})
    for item in reachability["items"]:
        if item["status"] != "free":
            failures.append({"kind": "waypoint", "index": item["index"], "status": item["status"], "reason": item["reason"]})
    return failures


def _ratio(numerator: int, denominator: int) -> Optional[float]:
    if denominator <= 0:
        return None
    return round(float(numerator) / float(denominator), 4)


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate offline Nav2 map quality metrics.")
    parser.add_argument("map_yaml", help="map_server YAML artifact")
    parser.add_argument("--waypoints", help="JSON file with waypoints list")
    args = parser.parse_args(list(argv) if argv is not None else None)
    report = evaluate_map_quality(args.map_yaml, waypoint_path=args.waypoints)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["quality_gates"]["software_guard_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
