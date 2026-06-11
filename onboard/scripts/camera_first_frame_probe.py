#!/usr/bin/env python3
"""Camera first-frame probe for real board and known-good UVC checks."""

from __future__ import annotations

import argparse
import importlib
import json
import signal
import time
from pathlib import Path
from typing import Any


SCHEMA = "trashbot.camera_first_frame_probe.v1"
DEFAULT_DEVICE = "/dev/video1"
DEFAULT_WIDTH = 640
DEFAULT_HEIGHT = 480
DEFAULT_FPS = 15
DEFAULT_TIMEOUT_S = 3.0
DEFAULT_INTERVAL_S = 0.05
DEFAULT_READ_CALL_TIMEOUT_S = 4.0
DEFAULT_DARK_THRESHOLD = 8.0


def now_ms() -> int:
    """统一用毫秒时间戳，便于和 PC/Robot API artifacts 对齐。"""
    return int(time.time() * 1000)


def proof_flags() -> dict[str, bool]:
    """相机探针只读视频帧，不能提升任何底盘控制或投递证明。"""
    return {
        "safe_to_control": False,
        "robot_control_executed": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "opens_serial": False,
        "sends_motion_commands": False,
    }


def compact_error(error: BaseException) -> dict[str, str]:
    """错误文本只保留短消息，避免现场机器路径污染 PC 展示。"""
    return {"type": type(error).__name__, "message": str(error)[:240]}


def import_cv2() -> Any:
    """延迟导入 cv2，让本地无相机环境也能做参数和单元测试。"""
    return importlib.import_module("cv2")


def frame_shape(frame: Any) -> list[int]:
    """兼容 numpy frame 与测试中的 list frame。"""
    shape = getattr(frame, "shape", None)
    if shape is not None:
        return [int(item) for item in shape]
    if isinstance(frame, list):
        height = len(frame)
        width = len(frame[0]) if height and isinstance(frame[0], list) else 0
        first_pixel = frame[0][0] if height and width and isinstance(frame[0][0], list) else None
        channels = len(first_pixel) if isinstance(first_pixel, list) else 1
        return [height, width, channels] if channels > 1 else [height, width]
    return []


def iter_luma_values(frame: Any) -> list[float]:
    """把一帧图像压成亮度数组，用于判断是否读到了非空画面信号。"""
    data = frame.tolist() if hasattr(frame, "tolist") else frame
    values: list[float] = []

    # 这里不依赖 numpy，目的是让同一脚本能在极简板端和本地测试里运行。
    for row in data:
        if not isinstance(row, list):
            values.append(float(row))
            continue
        for pixel in row:
            if isinstance(pixel, (list, tuple)) and len(pixel) >= 3:
                blue, green, red = float(pixel[0]), float(pixel[1]), float(pixel[2])
                values.append(0.114 * blue + 0.587 * green + 0.299 * red)
            elif isinstance(pixel, (int, float)):
                values.append(float(pixel))
    return values


def frame_metrics(frame: Any, dark_threshold: float = DEFAULT_DARK_THRESHOLD) -> dict[str, Any]:
    """计算最小图像质量指标，避免把黑帧或空帧误判为可见内容。"""
    luma = iter_luma_values(frame)
    if not luma:
        return {
            "shape": frame_shape(frame),
            "pixel_count": 0,
            "mean_luma": None,
            "min_luma": None,
            "max_luma": None,
            "dynamic_range_luma": None,
            "non_black_ratio": 0.0,
            "visible_content_candidate": False,
        }

    min_luma = min(luma)
    max_luma = max(luma)
    mean_luma = sum(luma) / len(luma)
    non_black = sum(1 for value in luma if value > dark_threshold)
    non_black_ratio = non_black / len(luma)

    # 这是“候选”而不是运动 gate 证明；真实放行仍需要 PC/外部视频证据。
    visible_candidate = non_black_ratio >= 0.02 and (max_luma - min_luma) >= 10.0
    return {
        "shape": frame_shape(frame),
        "pixel_count": len(luma),
        "mean_luma": round(mean_luma, 4),
        "min_luma": round(min_luma, 4),
        "max_luma": round(max_luma, 4),
        "dynamic_range_luma": round(max_luma - min_luma, 4),
        "non_black_ratio": round(non_black_ratio, 6),
        "visible_content_candidate": visible_candidate,
    }


def apply_capture_settings(cv2: Any, capture: Any, width: int, height: int, fps: float, fourcc: str | None) -> None:
    """请求采集参数但不把 set 失败当成结论，真实结论以首帧读取为准。"""
    if fourcc:
        capture.set(getattr(cv2, "CAP_PROP_FOURCC", 6), cv2.VideoWriter_fourcc(*fourcc))
    capture.set(getattr(cv2, "CAP_PROP_FRAME_WIDTH", 3), width)
    capture.set(getattr(cv2, "CAP_PROP_FRAME_HEIGHT", 4), height)
    capture.set(getattr(cv2, "CAP_PROP_FPS", 5), fps)


def read_with_call_timeout(capture: Any, read_call_timeout_s: float) -> tuple[bool, Any, str | None]:
    """限制单次 read 的最长等待，避免 UVC select timeout 把 probe 拖到不可控。"""
    if read_call_timeout_s <= 0:
        ok, frame = capture.read()
        return ok, frame, None

    def handle_timeout(_signum: int, _frame: Any) -> None:
        """用 signal 打断 Linux 阻塞 read；若驱动不响应，外层仍会记录真实耗时。"""
        raise TimeoutError("capture_read_call_timeout")

    old_handler = signal.getsignal(signal.SIGALRM)
    try:
        signal.signal(signal.SIGALRM, handle_timeout)
        signal.setitimer(signal.ITIMER_REAL, read_call_timeout_s)
        ok, frame = capture.read()
        return ok, frame, None
    except TimeoutError as error:
        return False, None, str(error)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, old_handler)


def read_first_frame(
    cv2: Any,
    capture: Any,
    timeout_s: float,
    interval_s: float,
    read_call_timeout_s: float,
) -> tuple[bool, Any, int, str | None]:
    """短超时读取首帧，避免现场故障时服务或 SSH 会话长时间卡住。"""
    deadline = time.monotonic() + timeout_s
    attempts = 0
    last_failure: str | None = None
    while time.monotonic() < deadline:
        attempts += 1
        ok, frame, last_failure = read_with_call_timeout(capture, read_call_timeout_s)
        if ok and frame is not None:
            return True, frame, attempts, None
        time.sleep(interval_s)
    return False, None, attempts, last_failure


def probe_device(args: argparse.Namespace) -> dict[str, Any]:
    """打开一个视频设备并读取首帧，所有失败都用结构化 JSON 表达。"""
    started_monotonic = time.monotonic()
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "generated_at_ms": now_ms(),
        "device": args.device,
        "requested_width": args.width,
        "requested_height": args.height,
        "requested_fps": args.fps,
        "requested_fourcc": args.fourcc,
        "timeout_s": args.timeout_s,
        "read_call_timeout_s": args.read_call_timeout_s,
        "read_interval_s": args.interval_s,
        "status": "unknown",
        "open_ok": False,
        "read_ok": False,
        "first_frame_timeout": False,
        "attempts": 0,
        "sample_path": str(args.sample_path) if args.sample_path else None,
        "visible_content_proven": False,
        **proof_flags(),
    }

    try:
        cv2 = import_cv2()
    except Exception as error:  # pragma: no cover - exercised by unit tests.
        payload.update({"status": "dependency_missing", "error": compact_error(error)})
        payload["elapsed_ms"] = int((time.monotonic() - started_monotonic) * 1000)
        return payload

    try:
        capture = cv2.VideoCapture(args.device)
    except Exception as error:
        payload.update({"status": "open_error", "error": compact_error(error)})
        payload["elapsed_ms"] = int((time.monotonic() - started_monotonic) * 1000)
        return payload

    try:
        if not capture.isOpened():
            payload.update({"status": "open_failed", "open_ok": False})
            return payload

        payload["open_ok"] = True
        apply_capture_settings(cv2, capture, args.width, args.height, args.fps, args.fourcc)
        read_ok, frame, attempts, failure_reason = read_first_frame(
            cv2,
            capture,
            args.timeout_s,
            args.interval_s,
            args.read_call_timeout_s,
        )
        payload["attempts"] = attempts
        if not read_ok:
            payload.update(
                {
                    "status": "first_frame_timeout",
                    "first_frame_timeout": True,
                    "failure_reason": failure_reason or "deadline_expired",
                }
            )
            return payload

        metrics = frame_metrics(frame, args.dark_threshold)
        payload.update({"status": "frame_read", "read_ok": True, "frame_metrics": metrics})
        if args.sample_path:
            args.sample_path.parent.mkdir(parents=True, exist_ok=True)
            payload["sample_write_ok"] = bool(cv2.imwrite(str(args.sample_path), frame))
        return payload
    except Exception as error:
        payload.update({"status": "probe_error", "error": compact_error(error)})
        return payload
    finally:
        # release 放在 finally，保证首帧失败后不会残留占用 `/dev/video*`。
        try:
            capture.release()
        finally:
            payload["elapsed_ms"] = int((time.monotonic() - started_monotonic) * 1000)


def build_parser() -> argparse.ArgumentParser:
    """CLI 参数保持显式，方便现场换 known-good UVC 后直接复测。"""
    parser = argparse.ArgumentParser(description="Probe one real camera first frame and print JSON.")
    parser.add_argument("--device", default=DEFAULT_DEVICE)
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--fps", type=float, default=DEFAULT_FPS)
    parser.add_argument("--fourcc", choices=("MJPG", "YUYV"), default=None)
    parser.add_argument("--timeout-s", type=float, default=DEFAULT_TIMEOUT_S)
    parser.add_argument("--read-call-timeout-s", type=float, default=DEFAULT_READ_CALL_TIMEOUT_S)
    parser.add_argument("--interval-s", type=float, default=DEFAULT_INTERVAL_S)
    parser.add_argument("--dark-threshold", type=float, default=DEFAULT_DARK_THRESHOLD)
    parser.add_argument("--sample-path", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    """命令行入口始终打印 JSON；硬件未就绪也不把日志散落到 stderr。"""
    args = build_parser().parse_args(argv)
    result = probe_device(args)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
