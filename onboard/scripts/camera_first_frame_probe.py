#!/usr/bin/env python3
"""Camera first-frame probe for real board and known-good UVC checks."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import shutil
import signal
import subprocess
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
BACKEND_SMOKE_TIMEOUT_S = 8.0
BACKEND_INFO_TIMEOUT_S = 4.0
BACKEND_V4L2_STREAM_TIMEOUT_S = 4.0
BACKEND_FFMPEG_STREAM_TIMEOUT_S = 5.0
BACKEND_DEVICE_MODE_LIMIT = 2
BACKEND_FFMPEG_INPUT_FORMATS = {"MJPG": "mjpeg", "YUYV": "yuyv422"}
BACKEND_USERPTR_DEVICE_MODE_LIMIT = 2


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


def preview_text(value: object, limit: int = 1200) -> str:
    """统一压缩外部命令输出，PC 只需要看到关键尾部证据。"""
    if isinstance(value, bytes):
        value = value.decode(errors="replace")
    return str(value or "")[-limit:]


def has_jpeg_soi(output_path: Path | None) -> bool:
    """MJPG/ffmpeg 输出若包含 JPEG SOI，可作为比文件大小更强的首帧证据。"""
    if output_path is None or not output_path.exists() or output_path.stat().st_size < 2:
        return False
    try:
        with output_path.open("rb") as handle:
            return handle.read(2) == b"\xff\xd8"
    except OSError:
        return False


def classify_backend_attempt(timed_out: bool, returncode: int | None, output_bytes: int) -> tuple[str, str | None]:
    """把底层取帧结果压成稳定状态，避免 UI 根据 stderr 文本猜根因。"""
    if timed_out and output_bytes <= 0:
        return "no_frame_timeout", "v4l2_stream_timeout_no_bytes"
    if timed_out:
        return "partial_output_timeout", "stream_timeout_after_partial_bytes"
    if returncode not in (0, None):
        return "stream_failed", "backend_command_nonzero"
    if output_bytes > 0:
        return "frame_observed", None
    return "no_frame_output", "backend_command_zero_bytes"


def run_subprocess_group(command: list[str], timeout_s: float) -> tuple[subprocess.CompletedProcess[str], bool]:
    """外部取帧命令必须整组超时清理，避免 ffmpeg/v4l2 残留继续占用摄像头。"""
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout_s)
        return subprocess.CompletedProcess(command, process.returncode, stdout=stdout, stderr=stderr), False
    except subprocess.TimeoutExpired as exc:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except OSError:
            process.kill()
        stdout, stderr = process.communicate()
        return subprocess.CompletedProcess(
            command,
            None,
            stdout=preview_text(exc.stdout) + preview_text(stdout),
            stderr=preview_text(exc.stderr) + preview_text(stderr),
        ), True


def run_info_command(name: str, command: list[str]) -> dict[str, Any]:
    """采集 v4l2 设备静态信息；不取帧、不触碰底盘，只帮助区分枚举和格式问题。"""
    started = time.monotonic()
    if shutil.which(command[0]) is None:
        return {
            "name": name,
            "available": False,
            "executed": False,
            "ok": False,
            "returncode": None,
            "elapsed_ms": 0,
            "stdout_preview": "",
            "stderr_preview": f"{command[0]} not found",
        }
    completed, timed_out = run_subprocess_group(command, BACKEND_INFO_TIMEOUT_S)
    return {
        "name": name,
        "available": True,
        "executed": True,
        "ok": bool(not timed_out and completed.returncode == 0),
        "timed_out": timed_out,
        "returncode": completed.returncode,
        "elapsed_ms": int((time.monotonic() - started) * 1000),
        "stdout_text": str(completed.stdout or ""),
        "stdout_preview": preview_text(completed.stdout),
        "stderr_preview": preview_text(completed.stderr),
    }


def run_backend_command(name: str, command: list[str], timeout_s: float = BACKEND_SMOKE_TIMEOUT_S) -> dict[str, Any]:
    """运行固定白名单采集命令，用于区分 OpenCV 问题和 V4L2/驱动无帧。"""
    started = time.monotonic()
    if shutil.which(command[0]) is None:
        return {
            "name": name,
            "available": False,
            "executed": False,
            "ok": False,
            "returncode": None,
            "elapsed_ms": 0,
            "stdout_preview": "",
            "stderr_preview": f"{command[0]} not found",
            "output_bytes": 0,
            "jpeg_soi_observed": False,
            "status": "tool_missing",
            "failure_reason": "backend_tool_missing",
        }
    output_path = Path(command[-1]) if command[-2] in {"--stream-to", "-y"} else None
    if output_path is not None:
        try:
            output_path.unlink(missing_ok=True)
        except OSError:
            pass
    completed, timed_out = run_subprocess_group(command, timeout_s)
    output_bytes = output_path.stat().st_size if output_path is not None and output_path.exists() else 0
    status, failure_reason = classify_backend_attempt(timed_out, completed.returncode, output_bytes)
    return {
        "name": name,
        "available": True,
        "executed": True,
        "ok": bool(not timed_out and completed.returncode == 0 and output_bytes > 0),
        "status": status,
        "failure_reason": failure_reason,
        "timed_out": timed_out,
        "returncode": completed.returncode,
        "elapsed_ms": int((time.monotonic() - started) * 1000),
        "stdout_preview": preview_text(completed.stdout, limit=400),
        "stderr_preview": preview_text(completed.stderr, limit=800),
        "output_path": str(output_path) if output_path is not None else None,
        "output_bytes": output_bytes,
        "jpeg_soi_observed": has_jpeg_soi(output_path),
    }


def parse_v4l2_format_modes(v4l2_text: str) -> list[dict[str, Any]]:
    """从 v4l2-ctl 输出提取设备自报格式，避免只按固定 640x480 猜测。"""
    modes: list[dict[str, Any]] = []
    seen: set[tuple[str, int, int, float | None]] = set()
    current_fourcc: str | None = None
    pending_size: tuple[int, int] | None = None
    pending_has_interval = False

    def append_mode(fourcc: str, width: int, height: int, fps: float | None) -> None:
        """去重保留格式矩阵；fps 缺失时仍可用于 v4l2 set-fmt 低负载尝试。"""
        key = (fourcc, width, height, fps)
        if key in seen:
            return
        seen.add(key)
        modes.append({"fourcc": fourcc, "width": width, "height": height, "fps": fps})

    def flush_pending_size() -> None:
        """部分驱动不打印 interval，遇到下一段前也要保留尺寸本身。"""
        nonlocal pending_size, pending_has_interval
        if current_fourcc and pending_size and not pending_has_interval:
            append_mode(current_fourcc, pending_size[0], pending_size[1], None)
        pending_size = None
        pending_has_interval = False

    for raw_line in v4l2_text.splitlines():
        line = raw_line.strip()
        format_match = re.search(r"'([A-Za-z0-9]{4})'", line)
        if format_match and ("Pixel Format" in line or line.startswith("[")):
            flush_pending_size()
            current_fourcc = format_match.group(1).upper()
            continue

        size_match = re.search(r"Size:\s+Discrete\s+(\d+)x(\d+)", line)
        if size_match:
            flush_pending_size()
            pending_size = (int(size_match.group(1)), int(size_match.group(2)))
            pending_has_interval = False
            continue

        interval_match = re.search(r"\(([\d.]+)\s+fps\)", line)
        if interval_match and current_fourcc and pending_size:
            pending_has_interval = True
            append_mode(current_fourcc, pending_size[0], pending_size[1], float(interval_match.group(1)))

    flush_pending_size()
    return modes


def select_backend_device_modes(
    v4l2_text: str,
    requested_width: int,
    requested_height: int,
    limit: int = BACKEND_DEVICE_MODE_LIMIT,
) -> list[dict[str, Any]]:
    """优先选设备支持的低分辨率 MJPG/YUYV，降低 USB 摄像头首帧压力。"""
    requested_area = requested_width * requested_height
    candidates: list[dict[str, Any]] = []
    for mode in parse_v4l2_format_modes(v4l2_text):
        fourcc = str(mode.get("fourcc", "")).upper()
        width = int(mode.get("width") or 0)
        height = int(mode.get("height") or 0)
        if fourcc not in BACKEND_FFMPEG_INPUT_FORMATS or width <= 0 or height <= 0:
            continue
        # 固定矩阵已经覆盖请求尺寸；这里专门补更轻的设备原生尺寸。
        if width == requested_width and height == requested_height:
            continue
        if width * height > requested_area:
            continue
        candidates.append({**mode, "fourcc": fourcc, "width": width, "height": height})

    selected: list[dict[str, Any]] = []
    selected_keys: set[tuple[str, int, int]] = set()
    for fourcc in ("MJPG", "YUYV"):
        same_format = [item for item in candidates if item["fourcc"] == fourcc]
        same_format.sort(key=lambda item: (item["width"] * item["height"], -(item.get("fps") or 0.0)))
        if same_format:
            item = same_format[0]
            key = (item["fourcc"], item["width"], item["height"])
            selected.append(item)
            selected_keys.add(key)

    candidates.sort(key=lambda item: (item["width"] * item["height"], item["fourcc"], -(item.get("fps") or 0.0)))
    for item in candidates:
        if len(selected) >= limit:
            break
        key = (item["fourcc"], item["width"], item["height"])
        if key in selected_keys:
            continue
        selected.append(item)
        selected_keys.add(key)

    return selected[:limit]


def ffmpeg_command_for_mode(device: str, mode: dict[str, Any], output_path: Path) -> list[str]:
    """生成 ffmpeg 单帧命令；参数全部来自设备枚举，不引入猜测格式。"""
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "info",
        "-f",
        "v4l2",
        "-input_format",
        BACKEND_FFMPEG_INPUT_FORMATS[str(mode["fourcc"])],
        "-video_size",
        f"{mode['width']}x{mode['height']}",
    ]
    if mode.get("fps"):
        command.extend(["-framerate", str(mode["fps"])])
    command.extend(["-i", device, "-frames:v", "1", "-y", str(output_path)])
    return command


def v4l2_stream_command_for_mode(device: str, mode: dict[str, Any], io_mode: str, output_path: Path) -> list[str]:
    """生成 v4l2-ctl 单帧命令；userptr 兜底用于排除 mmap 和驱动缓冲路径问题。"""
    stream_arg = "--stream-user=3" if io_mode == "userptr" else "--stream-mmap=3"
    command = [
        "v4l2-ctl",
        "-d",
        device,
        f"--set-fmt-video=width={mode['width']},height={mode['height']},pixelformat={mode['fourcc']}",
    ]
    if mode.get("fps"):
        command.append(f"--set-parm={mode['fps']}")
    command.extend([
        stream_arg,
        "--stream-count=1",
        "--stream-to",
        str(output_path),
    ])
    return command


def backend_smoke_probe(args: argparse.Namespace) -> dict[str, Any]:
    """用 v4l2-ctl/ffmpeg 各取一帧；只读 camera，不写 controls，不碰底盘。"""
    output_dir = Path("/tmp/rober_camera_backend_smoke")
    output_dir.mkdir(parents=True, exist_ok=True)
    width = str(args.width)
    height = str(args.height)
    device = str(args.device)
    v4l2_info = [
        run_info_command("v4l2_all", ["v4l2-ctl", "-d", device, "--all"]),
        run_info_command("v4l2_formats", ["v4l2-ctl", "-d", device, "--list-formats-ext"]),
    ]
    formats_text = next(
        (
            str(item.get("stdout_text") or item.get("stdout_preview") or "")
            for item in v4l2_info
            if item.get("name") == "v4l2_formats"
        ),
        "",
    )
    attempts = [
        run_backend_command(
            "v4l2_mjpg_mmap",
            [
                "v4l2-ctl",
                "-d",
                device,
                f"--set-fmt-video=width={width},height={height},pixelformat=MJPG",
                "--stream-mmap=3",
                "--stream-count=1",
                "--stream-to",
                str(output_dir / "v4l2_mjpg.raw"),
            ],
            timeout_s=BACKEND_V4L2_STREAM_TIMEOUT_S,
        ),
        run_backend_command(
            "v4l2_yuyv_mmap",
            [
                "v4l2-ctl",
                "-d",
                device,
                f"--set-fmt-video=width={width},height={height},pixelformat=YUYV",
                "--stream-mmap=3",
                "--stream-count=1",
                "--stream-to",
                str(output_dir / "v4l2_yuyv.raw"),
            ],
            timeout_s=BACKEND_V4L2_STREAM_TIMEOUT_S,
        ),
        run_backend_command(
            "ffmpeg_mjpg",
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "info",
                "-f",
                "v4l2",
                "-input_format",
                "mjpeg",
                "-video_size",
                f"{width}x{height}",
                "-i",
                device,
                "-frames:v",
                "1",
                "-y",
                str(output_dir / "ffmpeg_mjpg.jpg"),
            ],
            timeout_s=BACKEND_FFMPEG_STREAM_TIMEOUT_S,
        ),
        run_backend_command(
            "ffmpeg_yuyv",
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "info",
                "-f",
                "v4l2",
                "-input_format",
                "yuyv422",
                "-video_size",
                f"{width}x{height}",
                "-i",
                device,
                "-frames:v",
                "1",
                "-y",
                str(output_dir / "ffmpeg_yuyv.jpg"),
            ],
            timeout_s=BACKEND_FFMPEG_STREAM_TIMEOUT_S,
        ),
        run_backend_command(
            "v4l2_current_mmap",
            [
                "v4l2-ctl",
                "-d",
                device,
                "--stream-mmap=3",
                "--stream-count=1",
                "--stream-to",
                str(output_dir / "v4l2_current.raw"),
            ],
            timeout_s=BACKEND_V4L2_STREAM_TIMEOUT_S,
        ),
    ]
    device_modes = select_backend_device_modes(formats_text, args.width, args.height)
    for mode_index, mode in enumerate(device_modes):
        slug = f"{mode['fourcc'].lower()}_{mode['width']}x{mode['height']}"
        attempts.append(
            run_backend_command(
                f"v4l2_device_{slug}_mmap",
                v4l2_stream_command_for_mode(device, mode, "mmap", output_dir / f"v4l2_device_{slug}.raw"),
                timeout_s=BACKEND_V4L2_STREAM_TIMEOUT_S,
            )
        )
        if mode_index < BACKEND_USERPTR_DEVICE_MODE_LIMIT:
            attempts.append(
                run_backend_command(
                    f"v4l2_device_{slug}_userptr",
                    v4l2_stream_command_for_mode(
                        device,
                        mode,
                        "userptr",
                        output_dir / f"v4l2_device_{slug}_userptr.raw",
                    ),
                    timeout_s=BACKEND_V4L2_STREAM_TIMEOUT_S,
                )
            )
        attempts.append(
            run_backend_command(
                f"ffmpeg_device_{slug}",
                ffmpeg_command_for_mode(device, mode, output_dir / f"ffmpeg_device_{slug}.jpg"),
                timeout_s=BACKEND_FFMPEG_STREAM_TIMEOUT_S,
            )
        )
    frame_observed = any(item.get("status") == "frame_observed" for item in attempts)
    primary_failure = next((item.get("failure_reason") for item in attempts if item.get("failure_reason")), None)
    no_frame_timeouts = [item for item in attempts if item.get("status") == "no_frame_timeout"]
    streamon_io_errors = [
        item
        for item in attempts
        if "vidioc_streamon" in str(item.get("stderr_preview") or "").lower()
        and "input/output error" in str(item.get("stderr_preview") or "").lower()
    ]
    userptr_attempts = [item for item in attempts if "userptr" in str(item.get("name") or "")]
    return {
        "executed": True,
        "frame_observed": frame_observed,
        "status": "backend_frame_observed" if frame_observed else "backend_no_frame_observed",
        "overall_status": "frame_observed" if frame_observed else "no_kernel_frame_observed",
        "failure_reason": None if frame_observed else primary_failure or "backend_no_frame_observed",
        "no_frame_timeout_count": len(no_frame_timeouts),
        # 多后端都在 VIDIOC_STREAMON 阶段 I/O error 时，根因已经低于 OpenCV/浏览器层。
        "streamon_io_error_observed": bool(streamon_io_errors),
        "streamon_io_error_count": len(streamon_io_errors),
        "latest_streamon_io_error": str(streamon_io_errors[-1].get("stderr_preview") or "")[-400:] if streamon_io_errors else "",
        # userptr 和 mmap 同时无帧时，PC 可明确显示已排除常见 V4L2 缓冲模式差异。
        "userptr_attempt_count": len(userptr_attempts),
        "userptr_frame_observed": any(item.get("status") == "frame_observed" for item in userptr_attempts),
        "v4l2_info": v4l2_info,
        "attempts": attempts,
        "output_dir": str(output_dir),
        **proof_flags(),
    }


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
            if getattr(args, "include_backend_smoke", False):
                # OpenCV open 失败时也要跑底层 V4L2/ffmpeg smoke，避免 PC 只看到泛化 open_failed。
                capture.release()
                payload["backend_smoke"] = backend_smoke_probe(args)
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
            if getattr(args, "include_backend_smoke", False):
                # 后端矩阵需要独占打开 V4L2；先释放 OpenCV，避免把自己制造的 busy 当作硬件根因。
                capture.release()
                payload["backend_smoke"] = backend_smoke_probe(args)
            return payload

        metrics = frame_metrics(frame, args.dark_threshold)
        payload.update({"status": "frame_read", "read_ok": True, "frame_metrics": metrics})
        if args.sample_path:
            args.sample_path.parent.mkdir(parents=True, exist_ok=True)
            payload["sample_write_ok"] = bool(cv2.imwrite(str(args.sample_path), frame))
            # 只有同时有可见内容指标和样张 artifact，才可作为 first-jog 的可追溯视觉材料。
            payload["visible_content_proven"] = bool(metrics.get("visible_content_candidate") and payload["sample_write_ok"])
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
    parser.add_argument("--include-backend-smoke", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """命令行入口始终打印 JSON；硬件未就绪也不把日志散落到 stderr。"""
    args = build_parser().parse_args(argv)
    result = probe_device(args)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
