"""Offline proof artifact builder for fixed-route visual gates.

This module intentionally has no ROS2 imports. It lets route/keyframe/live-frame
evidence be checked in CI, on a laptop, or by a support script before any Nav2
daemon, camera topic, or robot hardware is available.
"""

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only on minimal installs.
    yaml = None

try:
    import cv2
except ImportError:  # pragma: no cover - tests use dependency injection.
    cv2 = None

from ros2_trashbot_nav.route_utils import (
    ROUTE_CONTRACT_VERSION,
    build_elevator_assist_evidence,
    build_elevator_assist_status,
    load_waypoints_from_simple_yaml,
    load_waypoints_from_csv,
    validate_route_yaml_data,
)
from ros2_trashbot_nav.route_proof_summary import (
    build_route_proof_summary,
    summarize_checkpoints_from_visual_gate,
)


PASSED = "passed"
INVALID_ROUTE = "invalid_route"
MISSING_KEYFRAME = "missing_keyframe"
MISSING_LIVE_FRAME = "missing_live_frame"
IMAGE_UNREADABLE = "image_unreadable"
NO_DESCRIPTORS = "no_descriptors"
INSUFFICIENT_MATCHES = "insufficient_matches"


class OrbImageMatcher:
    """Small OpenCV adapter kept separate so tests can stub match results."""

    def __init__(self) -> None:
        if cv2 is None:
            raise RuntimeError("OpenCV is not available")
        self.orb = cv2.ORB_create(600)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    def _descriptors_for(self, image_path: Path) -> Tuple[Optional[Any], str]:
        image = cv2.imread(str(image_path))
        if image is None:
            return None, IMAGE_UNREADABLE
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        keypoints, descriptors = self.orb.detectAndCompute(gray, None)
        if descriptors is None or len(keypoints) == 0:
            return None, NO_DESCRIPTORS
        return descriptors, PASSED

    def __call__(
        self,
        keyframe_path: Path,
        live_frame_path: Path,
        _threshold: int,
    ) -> Tuple[str, int, str]:
        key_descriptors, key_status = self._descriptors_for(keyframe_path)
        if key_status != PASSED:
            return key_status, 0, f"keyframe {key_status}: {keyframe_path}"
        live_descriptors, live_status = self._descriptors_for(live_frame_path)
        if live_status != PASSED:
            return live_status, 0, f"live frame {live_status}: {live_frame_path}"
        matches = self.matcher.match(key_descriptors, live_descriptors)
        return PASSED, len(matches), "descriptors matched"


class UnavailableImageMatcher:
    """Matcher fallback that keeps proof JSON structured when OpenCV is absent."""

    def __init__(self, reason: str) -> None:
        self.reason = reason

    def __call__(
        self,
        _keyframe_path: Path,
        _live_frame_path: Path,
        _threshold: int,
    ) -> Tuple[str, int, str]:
        return NO_DESCRIPTORS, 0, f"image matcher unavailable: {self.reason}"


def _load_route(route_file: str) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    path = Path(route_file).expanduser()
    if not path.exists():
        return [], f"route file not found: {path}"
    try:
        if path.suffix.lower() == ".csv":
            return load_waypoints_from_csv(str(path)), None
        if yaml is None:
            return load_waypoints_from_simple_yaml(str(path)), None
        with path.open("r", encoding="utf-8") as stream:
            data = yaml.safe_load(stream)
        return validate_route_yaml_data(data, str(path)), None
    except Exception as exc:
        return [], str(exc)


def _checkpoint_paths(index: int, keyframe_dir: str, live_frame_dir: str) -> Tuple[Path, Path]:
    filename = f"{index:03d}.jpg"
    return Path(keyframe_dir).expanduser() / filename, Path(live_frame_dir).expanduser() / filename


def _checkpoint_result(
    index: int,
    keyframe_path: Path,
    live_frame_path: Path,
    threshold: int,
    matcher: Callable[[Path, Path, int], Union[Dict[str, Any], Tuple[str, int, str]]],
) -> Dict[str, Any]:
    base = {
        "index": index,
        "keyframe": str(keyframe_path),
        "live_frame": str(live_frame_path),
        "match_count": 0,
        "threshold": threshold,
    }
    if not keyframe_path.exists():
        return {
            **base,
            "status": MISSING_KEYFRAME,
            "detail": f"visual gate missing keyframe for checkpoint {index}",
        }
    if not live_frame_path.exists():
        return {
            **base,
            "status": MISSING_LIVE_FRAME,
            "detail": f"visual gate missing live frame for checkpoint {index}",
        }

    raw_result = matcher(keyframe_path, live_frame_path, threshold)
    if isinstance(raw_result, dict):
        status = str(raw_result.get("status", PASSED))
        match_count = int(raw_result.get("match_count", 0))
        detail = str(raw_result.get("detail", "matcher returned structured result"))
    else:
        status, match_count, detail = raw_result
        match_count = int(match_count)
    if status != PASSED:
        descriptor_source = "keyframe" if detail.startswith("keyframe ") else "live_frame"
        return {
            **base,
            "match_count": match_count,
            "status": status,
            "descriptor_source": descriptor_source,
            "detail": f"visual gate {detail} at checkpoint {index}",
        }
    if match_count < threshold:
        return {
            **base,
            "match_count": match_count,
            "status": INSUFFICIENT_MATCHES,
            "detail": f"visual gate matched {match_count}/{threshold} features at checkpoint {index}",
        }
    return {
        **base,
        "match_count": match_count,
        "status": PASSED,
        "detail": f"visual gate passed checkpoint {index}",
    }


def _keyframe_preflight(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    missing = [item["index"] for item in results if item["status"] == MISSING_KEYFRAME]
    invalid = [
        {"index": item["index"], "reason": item["status"]}
        for item in results
        if (
            item["status"] in (IMAGE_UNREADABLE, NO_DESCRIPTORS)
            and item.get("descriptor_source") == "keyframe"
        )
    ]
    loaded = [
        item["index"]
        for item in results
        if item["status"] not in (MISSING_KEYFRAME, IMAGE_UNREADABLE, NO_DESCRIPTORS)
    ]
    return {
        "enabled": True,
        "total_checkpoints": len(results),
        "loaded_keyframes": loaded,
        "missing_keyframes": missing,
        "invalid_keyframes": invalid,
        "route_visual_ready": not missing and not invalid,
    }


def _debug_status(
    route_file: str,
    keyframe_dir: str,
    checkpoints: List[Dict[str, Any]],
    summary_status: str,
    route_error: str = "",
) -> Dict[str, Any]:
    failing = next((item for item in checkpoints if item["status"] != PASSED), None)
    latest = checkpoints[-1] if checkpoints else None
    focus = failing or latest
    visual_status = focus["status"] if focus else summary_status
    detail = focus["detail"] if focus else route_error
    checkpoint = focus["index"] if focus else None
    last_error = "" if summary_status == PASSED else (detail or route_error)
    return {
        "state": "completed" if summary_status == PASSED else "error",
        "mode": "offline_proof",
        "route_contract_version": ROUTE_CONTRACT_VERSION,
        "route_file": str(Path(route_file).expanduser()),
        "keyframe_dir": str(Path(keyframe_dir).expanduser()),
        "current_index": checkpoint,
        "total": len(checkpoints),
        "dry_run": True,
        "enable_visual_gate": True,
        "keyframe_preflight": _keyframe_preflight(checkpoints),
        "visual_gate_status": visual_status,
        "visual_gate_detail": detail,
        "visual_gate_checkpoint": checkpoint,
        "last_error": last_error,
        "failure_reason": last_error,
        "last_transition": "offline_proof",
        "last_nav_result": "not_run",
        "updated_at": time.time(),
    }


def _elevator_assist_from_visual_gate(
    summary_status: str,
    checkpoints: List[Dict[str, Any]],
    route_error: str = "",
) -> Dict[str, Any]:
    """Expose visual-gate output as elevator evidence without claiming OCR.

    A passing fixed-route visual proof only says the route checkpoint imagery is
    consistent; it does not prove door state or floor text. The normalized
    evidence therefore remains conservative until a future source supplies a
    door/floor-specific status.
    """
    failing = next((item for item in checkpoints if item["status"] != PASSED), None)
    latest = checkpoints[-1] if checkpoints else None
    focus = failing or latest
    checkpoint = focus["index"] if focus else None
    detail = route_error or (focus["detail"] if focus else "visual gate proof has no checkpoints")
    status = "door_closed_or_unknown"
    if summary_status == PASSED and checkpoints:
        detail = "visual gate passed; elevator door and floor evidence remain unconfirmed"
        status = "target_floor_unconfirmed"
    evidence = build_elevator_assist_evidence(
        status,
        source="visual_gate_offline_proof",
        confidence=0.0,
        detail=detail,
        checkpoint=checkpoint,
        metadata={
            "visual_gate_status": summary_status,
            "visual_gate_checkpoint": checkpoint,
        },
    )
    return build_elevator_assist_status(evidence, enabled=False, mode="offline_schema")


def _invalid_route_proof(route_file: str, keyframe_dir: str, live_frame_dir: str, error: str) -> Dict[str, Any]:
    debug_status = _debug_status(route_file, keyframe_dir, [], INVALID_ROUTE, error)
    debug_status["visual_gate_status"] = INVALID_ROUTE
    debug_status["visual_gate_detail"] = error
    debug_status["last_error"] = error
    debug_status["failure_reason"] = error
    route_proof_summary = build_route_proof_summary(
        total_checkpoints=0,
        covered_checkpoints=0,
        gate_status=INVALID_ROUTE,
        last_block_reason=error,
        missing_checkpoints=[],
    )
    return {
        "route": {
            "path": str(Path(route_file).expanduser()),
            "contract_version": ROUTE_CONTRACT_VERSION,
            "total_checkpoints": 0,
            "status": INVALID_ROUTE,
            "error": error,
        },
        "checkpoints": [],
        "summary": {
            "status": INVALID_ROUTE,
            "passed": 0,
            "failed": 1,
            "failure_reasons": {INVALID_ROUTE: 1},
        },
        "route_proof_summary": route_proof_summary,
        "debug_status": debug_status,
        "elevator_assist": _elevator_assist_from_visual_gate(INVALID_ROUTE, [], error),
        "inputs": {
            "keyframe_dir": str(Path(keyframe_dir).expanduser()),
            "live_frame_dir": str(Path(live_frame_dir).expanduser()),
        },
    }


def build_visual_gate_proof(
    route_file: str,
    keyframe_dir: str,
    live_frame_dir: str,
    threshold: int = 25,
    output_file: Optional[str] = None,
    matcher: Optional[Callable[[Path, Path, int], Union[Dict[str, Any], Tuple[str, int, str]]]] = None,
) -> Dict[str, Any]:
    """Build a structured offline proof for fixed-route visual gate checkpoints."""
    threshold = int(threshold)
    waypoints, route_error = _load_route(route_file)
    if route_error:
        proof = _invalid_route_proof(route_file, keyframe_dir, live_frame_dir, route_error)
        _write_json_if_requested(proof, output_file)
        return proof

    if matcher is not None:
        active_matcher = matcher
    else:
        try:
            active_matcher = OrbImageMatcher()
        except RuntimeError as exc:
            active_matcher = UnavailableImageMatcher(str(exc))
    checkpoints = []
    for index in range(len(waypoints)):
        keyframe_path, live_frame_path = _checkpoint_paths(index, keyframe_dir, live_frame_dir)
        checkpoints.append(
            _checkpoint_result(index, keyframe_path, live_frame_path, threshold, active_matcher)
        )

    failed = [item for item in checkpoints if item["status"] != PASSED]
    failure_reasons: Dict[str, int] = {}
    for item in failed:
        failure_reasons[item["status"]] = failure_reasons.get(item["status"], 0) + 1
    summary_status = PASSED if not failed else "failed"
    route_proof_summary = summarize_checkpoints_from_visual_gate(checkpoints)
    proof = {
        "route": {
            "path": str(Path(route_file).expanduser()),
            "contract_version": ROUTE_CONTRACT_VERSION,
            "total_checkpoints": len(waypoints),
        },
        "checkpoints": checkpoints,
        "summary": {
            "status": summary_status,
            "passed": len(checkpoints) - len(failed),
            "failed": len(failed),
            "failure_reasons": failure_reasons,
        },
        "route_proof_summary": route_proof_summary,
        "debug_status": _debug_status(route_file, keyframe_dir, checkpoints, summary_status),
        "elevator_assist": _elevator_assist_from_visual_gate(summary_status, checkpoints),
        "inputs": {
            "keyframe_dir": str(Path(keyframe_dir).expanduser()),
            "live_frame_dir": str(Path(live_frame_dir).expanduser()),
        },
    }
    _write_json_if_requested(proof, output_file)
    return proof


def _write_json_if_requested(proof: Dict[str, Any], output_file: Optional[str]) -> None:
    if not output_file:
        return
    output_path = Path(output_file).expanduser()
    if output_path.parent:
        os.makedirs(output_path.parent, exist_ok=True)
    temp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as stream:
        json.dump(proof, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
    os.replace(temp_path, output_path)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build offline fixed-route visual gate proof JSON")
    parser.add_argument("--route-file", required=True)
    parser.add_argument("--keyframe-dir", required=True)
    parser.add_argument("--live-frame-dir", required=True)
    parser.add_argument("--threshold", type=int, default=25)
    parser.add_argument("--output")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    proof = build_visual_gate_proof(
        route_file=args.route_file,
        keyframe_dir=args.keyframe_dir,
        live_frame_dir=args.live_frame_dir,
        threshold=args.threshold,
        output_file=args.output,
    )
    print(json.dumps(proof, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if proof["summary"]["status"] == PASSED else 1


if __name__ == "__main__":
    raise SystemExit(main())
