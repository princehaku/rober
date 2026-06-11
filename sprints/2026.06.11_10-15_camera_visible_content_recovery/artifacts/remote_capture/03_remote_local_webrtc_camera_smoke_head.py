#!/usr/bin/env python3
"""LAN-only WebRTC camera smoke for the Orange Pi upper computer."""

from __future__ import annotations

import argparse
import asyncio
import glob
import importlib.util
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


APP_NAME = "rober-local-webrtc-camera-smoke"
DEFAULT_PORT = 8088
DEFAULT_VIDEO_SOURCE = "auto"
DEFAULT_WIDTH = 640
DEFAULT_HEIGHT = 480
DEFAULT_FPS = 15
IMPORTS = ("aiohttp", "aiortc", "cv2", "av")
TEMPERATURE_GLOBS = (
    "/sys/class/thermal/thermal_zone*/temp",
    "/sys/class/hwmon/hwmon*/temp*_input",
)


def now_ms() -> int:
    """统一用毫秒时间戳做诊断，方便 PC/browser smoke 对齐时间线。"""
    return int(time.time() * 1000)


PROCESS_STARTED_MONOTONIC = time.monotonic()
PROCESS_STARTED_WALL_MS = now_ms()


def log_event(event: str, **fields: Any) -> None:
    """服务端日志必须结构化且立即 flush，远端 nohup 日志才能定位媒体首帧缺失。"""
    payload = {"event": event, "ts_ms": now_ms(), **fields}
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)


def import_state() -> dict[str, bool]:
    """用 find_spec 做轻量探测，缺依赖时仍可启动降级诊断页。"""
    return {name: importlib.util.find_spec(name) is not None for name in IMPORTS}


def not_available(reason: str, **fields: Any) -> dict[str, Any]:
    """诊断字段必须 fail-open，缺内核文件或 Python 依赖不能把 /health 打成 500。"""
    return {"available": False, "reason": reason, **fields}


def read_float_file(path: Path) -> float | None:
    """sysfs/procfs 读取只做短路径解析，异常表示该指标不可用而不是服务失败。"""
    try:
        text = path.read_text(encoding="utf-8").strip()
        return float(text)
    except (OSError, ValueError):
        return None


def collect_temperature_diagnostics() -> dict[str, Any]:
    """温度用于 O7 短时稳定性证据；不同板卡路径不同，所以只采样可见文件。"""
    samples: list[dict[str, Any]] = []
    for pattern in TEMPERATURE_GLOBS:
        for name in sorted(glob.glob(pattern)):
            raw = read_float_file(Path(name))
            if raw is None:
                continue
            # Linux thermal/hwmon 常用毫摄氏度；若值很小则保留为摄氏度，避免误缩放。
            celsius = raw / 1000.0 if abs(raw) > 200 else raw
            samples.append({"path": name, "celsius": round(celsius, 3), "raw": raw})
    if not samples:
        return not_available("temperature_files_not_found", globs=list(TEMPERATURE_GLOBS))
    return {"available": True, "samples": samples}


def collect_cpu_diagnostics() -> dict[str, Any]:
    """CPU/load 只作为播放期间旁路观测，不参与任何控制或自动降速决策。"""
    payload: dict[str, Any] = {
        "available": True,
        "cpu_count": os.cpu_count(),
    }
    try:
        load1, load5, load15 = os.getloadavg()
        payload["load_average"] = {"1m": load1, "5m": load5, "15m": load15}
    except (AttributeError, OSError):
        payload["load_average"] = not_available("os_getloadavg_unavailable")

    psutil_spec = importlib.util.find_spec("psutil")
    if psutil_spec is None:
        payload["process_cpu_percent"] = not_available("psutil_not_installed")
        payload["system_cpu_percent"] = not_available("psutil_not_installed")
        return payload

    try:
        import psutil  # type: ignore[import-not-found]

        process = psutil.Process(os.getpid())
        # interval=None 不阻塞；首样本可能是 0.0，PC 轮询时后续样本才有趋势意义。
        payload["process_cpu_percent"] = {"available": True, "value": process.cpu_percent(interval=None)}
        payload["system_cpu_percent"] = {"available": True, "value": psutil.cpu_percent(interval=None)}
    except Exception as exc:  # noqa: BLE001 - psutil 在裁剪系统上可能因 /proc 权限失败。
        detail = {"error": type(exc).__name__, "detail": str(exc)}
        payload["process_cpu_percent"] = not_available("psutil_runtime_error", **detail)
        payload["system_cpu_percent"] = not_available("psutil_runtime_error", **detail)
    return payload


def collect_memory_diagnostics() -> dict[str, Any]:
    """内存指标用于解释短时掉帧，缺 psutil 时退回 /proc/self/status 的 RSS。"""
    psutil_spec = importlib.util.find_spec("psutil")
    if psutil_spec is not None:
        try:
            import psutil  # type: ignore[import-not-found]

            process = psutil.Process(os.getpid())
            memory = process.memory_info()
            virtual = psutil.virtual_memory()
            return {
                "available": True,
                "source": "psutil",
                "process_rss_bytes": memory.rss,
                "process_vms_bytes": memory.vms,
                "system_total_bytes": virtual.total,
                "system_available_bytes": virtual.available,
                "system_percent": virtual.percent,
            }
        except Exception as exc:  # noqa: BLE001 - 诊断路径不能因为 psutil 权限问题失败。
            return not_available("psutil_runtime_error", error=type(exc).__name__, detail=str(exc))

    rss_kb: int | None = None
    try:
        for line in Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
            if line.startswith("VmRSS:"):
                rss_kb = int(line.split()[1])
                break
    except (OSError, ValueError, IndexError):
        rss_kb = None
    if rss_kb is None:
        return not_available("psutil_and_proc_status_unavailable")
    return {"available": True, "source": "procfs", "process_rss_bytes": rss_kb * 1024}


def collect_system_diagnostics() -> dict[str, Any]:
    """统一健康采样时间，PC browser smoke 可按 monotonic 时间串起多次轮询。"""
    monotonic_now = time.monotonic()
    return {
        "sample": {
            "wall_time_ms": now_ms(),
            "monotonic_s": monotonic_now,
            "process_started_wall_time_ms": PROCESS_STARTED_WALL_MS,
            "process_uptime_s": round(monotonic_now - PROCESS_STARTED_MONOTONIC, 3),
        },
        "cpu": collect_cpu_diagnostics(),
        "memory": collect_memory_diagnostics(),
        "temperature": collect_temperature_diagnostics(),
    }


def summarize_frame_stats(stats: dict[str, Any] | None) -> dict[str, Any] | None:
    """把高频媒体字段压成稳定摘要，轮询方不用理解 aiortc 内部状态。"""
    if not stats:
        return None
    created_ts_ms = stats.get("created_ts_ms")
    last_frame_ts_ms = stats.get("last_frame_ts_ms")
    frames_read = int(stats.get("frames_read") or 0)
    elapsed_ms: int | None = None
    if isinstance(created_ts_ms, int):
        elapsed_ms = max(now_ms() - created_ts_ms, 0)
    fps_estimate = round(frames_read * 1000.0 / elapsed_ms, 3) if elapsed_ms else None
    return {
        "peer_id": stats.get("peer_id"),
        "connection_state": stats.get("connection_state"),
        "ice_connection_state": stats.get("ice_connection_state"),
        "signaling_state": stats.get("signaling_state"),
        "frames_read": frames_read,
        "camera_read_failures": int(stats.get("camera_read_failures") or 0),
        "last_frame_age_ms": now_ms() - last_frame_ts_ms if isinstance(last_frame_ts_ms, int) else None,
        "last_frame_width": stats.get("last_frame_width"),
        "last_frame_height": stats.get("last_frame_height"),
        "track_stopped": bool(stats.get("track_stopped")),
        "elapsed_ms": elapsed_ms,
        "fps_estimate": fps_estimate,
        "last_error": stats.get("last_error"),
    }


def build_media_summary(peer_stats: dict[str, dict[str, Any]], closed_peer_stats: dict[str, Any] | None) -> dict[str, Any]:
    """摘要只读展示媒体健康，不触发 offer、不开摄像头，也不改变 peer 生命周期。"""
    active = {peer_id: summarize_frame_stats(stats) for peer_id, stats in peer_stats.items()}
    last_closed = None
    if closed_peer_stats:
        last_closed = {
            "closed_ts_ms": closed_peer_stats.get("closed_ts_ms"),
            "cleanup": closed_peer_stats.get("cleanup"),
            "stats": summarize_frame_stats(closed_peer_stats.get("stats")),
        }
    totals = {
        "active_frames_read": sum((item or {}).get("frames_read", 0) for item in active.values()),
        "active_camera_read_failures": sum((item or {}).get("camera_read_failures", 0) for item in active.values()),
    }
    return {"active_peers": active, "last_closed_peer": last_closed, "totals": totals}


def build_system_metrics(system_diagnostics: dict[str, Any]) -> dict[str, Any]:
    """给 PC worker 的扁平白名单字段，避免前端摘要层绑定深层诊断结构。"""
    sample = system_diagnostics.get("sample", {})
    cpu = system_diagnostics.get("cpu", {})
    memory = system_diagnostics.get("memory", {})
    temperature = system_diagnostics.get("temperature", {})
    metrics: dict[str, Any] = {
        "process_uptime_s": sample.get("process_uptime_s"),
    }

    load_average = cpu.get("load_average")
    if isinstance(load_average, dict) and load_average.get("available") is False:
        metrics["load_unavailable_reason"] = load_average.get("reason")
    elif isinstance(load_average, dict):
        metrics["load_1m"] = load_average.get("1m")
    else:
        metrics["load_unavailable_reason"] = "load_average_missing"

    if memory.get("available"):
        metrics["process_rss_bytes"] = memory.get("process_rss_bytes")
    else:
        metrics["memory_unavailable_reason"] = memory.get("reason", "memory_missing")

    if temperature.get("available") and temperature.get("samples"):
        # PC 摘要只需要一个温度数值；完整传感器路径仍保留在 system_diagnostics。
        metrics["temperature_celsius"] = temperature["samples"][0].get("celsius")
    else:
        metrics["temperature_unavailable_reason"] = temperature.get("reason", "temperature_missing")
    return metrics


def build_stability_metrics(active_peer_count: int, media_summary: dict[str, Any]) -> dict[str, Any]:
    """PC worker 只消费白名单摘要，详细 per-peer 证据仍留在 media_stability_summary。"""
    totals = media_summary.get("totals", {})
    last_closed_stats = (media_summary.get("last_closed_peer") or {}).get("stats") or {}
    return {
        "active_peer_count": active_peer_count,
        "active_frames_read": totals.get("active_frames_read", 0),
        "active_camera_read_failures": totals.get("active_camera_read_failures", 0),
        "last_closed_frames_read": last_closed_stats.get("frames_read"),
        "last_closed_fps_estimate": last_closed_stats.get("fps_estimate"),
        "last_closed_camera_read_failures": last_closed_stats.get("camera_read_failures"),
        "last_closed_track_stopped": last_closed_stats.get("track_stopped"),
