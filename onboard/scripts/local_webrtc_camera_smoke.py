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
import threading
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


class CpuPercentSampler:
    """复用进程差分基线；线程争用时跳过诊断，避免健康请求排队。"""

    def __init__(self) -> None:
        # 同一个 Process 的差分状态必须串行更新，不能交错读取并重置基线。
        self._lock = threading.Lock()
        self._reset()

    def _reset(self) -> None:
        """异常后同时清空两类窗口，下一次成功读取只建立新基线。"""
        self._process: Any = None
        self._backend: Any = None
        self._pid: int | None = None
        self._process_sample_at: float | None = None
        # psutil 系统百分比按线程保存基线，短命 HTTP 线程也必须独立预热。
        self._system_samples = threading.local()

    @staticmethod
    def _unavailable(reason: str, **detail: Any) -> dict[str, Any]:
        """保持旧字段结构，每个指标各自持有诊断对象。"""
        return {name: not_available(reason, **detail) for name in (
            "process_cpu_percent", "system_cpu_percent",
        )}

    @staticmethod
    def _metric(value: float, previous: float | None, sampled_at: float) -> dict[str, Any]:
        """只暴露已经积累时间的差分值，墙钟校时不会改变窗口。"""
        window_ms = (sampled_at - previous) * 1000.0 if previous is not None else 0.0
        timing = {"sample_window_ms": max(window_ms, 0.0), "sampled_monotonic_s": sampled_at}
        # 首次读取返回的 0 没有负载含义；零长度窗口也不能冒充有效测量。
        if previous is None or window_ms <= 0:
            return not_available("warming_up", **timing)
        return {"available": True, "value": value, **timing}

    def sample(self, psutil_module: Any) -> dict[str, Any]:
        """依赖可注入供离线计数；生产调用始终使用 interval=None。"""
        # 竞争方立即返回缺失原因，不等待另一个线程的内核查询。
        if not self._lock.acquire(blocking=False):
            return self._unavailable("sampling_in_progress")
        try:
            if psutil_module is None:
                self._reset()
                return self._unavailable("psutil_not_installed")
            pid = os.getpid()
            if self._process is None or self._pid != pid or self._backend is not psutil_module:
                # 进程身份或依赖改变时不可继续使用旧差分窗口。
                self._reset()
                self._process = psutil_module.Process(pid)
                self._pid, self._backend = pid, psutil_module
            process_value = self._process.cpu_percent(interval=None)
            # 分别记录两次读取完成时刻，窗口只描述对应指标的实际采样间隔。
            process_at = time.monotonic()
            system_value = psutil_module.cpu_percent(interval=None)
            system_at = time.monotonic()
            # 两项读取都成功才发布窗口；部分失败会统一进入重新预热。
            result = {
                "process_cpu_percent": self._metric(process_value, self._process_sample_at, process_at),
                "system_cpu_percent": self._metric(
                    system_value, getattr(self._system_samples, "sampled_at", None), system_at,
                ),
            }
            self._process_sample_at = process_at
            self._system_samples.sampled_at = system_at
            return result
        except Exception as exc:  # noqa: BLE001 - 指标采样失败不能影响健康接口。
            # 保留异常类别便于定位权限等环境问题，不把故障伪装成低负载。
            self._reset()
            return self._unavailable("psutil_runtime_error", error=type(exc).__name__, detail=str(exc))
        finally:
            # 所有失败和提前返回都释放锁，让后续请求能够恢复采样。
            self._lock.release()


# 生命周期覆盖整个服务，禁止在每次 /health 请求内重建采样器。
CPU_PERCENT_SAMPLER = CpuPercentSampler()


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
        payload.update(CPU_PERCENT_SAMPLER.sample(None))
        return payload

    try:
        import psutil  # type: ignore[import-not-found]

        # 共享实例保留差分基线，预热与争用会明确标为不可用。
        payload.update(CPU_PERCENT_SAMPLER.sample(psutil))
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
    }


def list_video_devices() -> list[dict[str, Any]]:
    """只枚举设备节点，不默认打开摄像头，避免抢占 ROS2/调试进程。"""
    devices: list[dict[str, Any]] = []
    for name in sorted(glob.glob("/dev/video*")):
        path = Path(name)
        item: dict[str, Any] = {
            "path": str(path),
            "exists": path.exists(),
            "readable": os.access(path, os.R_OK),
            "writable": os.access(path, os.W_OK),
        }
        devices.append(item)
    return devices


def normalize_video_source(video_source: str) -> int | str:
    """显式 source 保持兼容：数字走 OpenCV index，路径/URL 按字符串传给后端。"""
    source = str(video_source).strip()
    return int(source) if source.isdigit() else source


def open_video_capture(cv2_module: Any, source: int | str) -> Any:
    """Linux video 节点显式走 V4L2 backend，避免 OpenCV 后端自动探测漂移。"""
    if hasattr(cv2_module, "CAP_V4L2") and (isinstance(source, int) or str(source).startswith("/dev/video")):
        return cv2_module.VideoCapture(source, cv2_module.CAP_V4L2)
    return cv2_module.VideoCapture(source)


def resolve_camera_source(
    video_source: str,
    cv2_module: Any,
    video_device_paths: list[str] | None = None,
    *,
    width: int,
    height: int,
    fps: int,
) -> tuple[int | str | None, dict[str, Any]]:
    """auto 模式逐个读首帧，避免 Orange Pi 平台视频节点被误当成 USB 摄像头。"""
    requested = str(video_source).strip()
    if requested.lower() not in ("", "auto", "autodetect"):
        selected = normalize_video_source(requested)
        return selected, {
            "mode": "explicit",
            "requested_source": requested,
            "selected_source": selected,
            "attempts": [],
        }

    candidates = video_device_paths if video_device_paths is not None else [item["path"] for item in list_video_devices()]
    diagnostics: dict[str, Any] = {
        "mode": "auto",
        "requested_source": requested or "auto",
        "candidate_sources": list(candidates),
        "selected_source": None,
        "attempts": [],
    }
    for candidate in candidates:
        attempt: dict[str, Any] = {
            "source": candidate,
            "opened": False,
            "read_ok": False,
            "backend": None,
            "frame_shape": None,
            "error": None,
        }
        cap = None
        try:
            # 选择阶段必须真实 read 一帧；只 isOpened 在某些 v4l2 节点上会误判。
            cap = open_video_capture(cv2_module, candidate)
            cap.set(cv2_module.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2_module.CAP_PROP_FRAME_HEIGHT, height)
            cap.set(cv2_module.CAP_PROP_FPS, fps)
            attempt["opened"] = bool(cap.isOpened())
            if attempt["opened"] and hasattr(cap, "getBackendName"):
                attempt["backend"] = cap.getBackendName()
            if attempt["opened"]:
                ok, frame = cap.read()
                attempt["read_ok"] = bool(ok and frame is not None)
                shape = getattr(frame, "shape", None)
                if shape is not None:
                    attempt["frame_shape"] = list(shape)
        except Exception as exc:  # noqa: BLE001 - 诊断路径要记录候选失败而不是中断整个选择。
            attempt["error"] = f"{type(exc).__name__}:{exc}"
        finally:
            if cap is not None:
                cap.release()
        diagnostics["attempts"].append(attempt)
        if attempt["opened"] and attempt["read_ok"]:
            diagnostics["selected_source"] = candidate
            return candidate, diagnostics
    diagnostics["failure_reason"] = "no_candidate_opened_and_read_first_frame"
    return None, diagnostics


def run_short_command(args: list[str], timeout_s: float = 2.0) -> dict[str, Any]:
    """外部探测都加短超时，避免异常板端命令把 smoke 卡死。"""
    try:
        completed = subprocess.run(
            args,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_s,
        )
    except FileNotFoundError:
        return {"available": False, "error": "command_not_found", "cmd": args}
    except subprocess.TimeoutExpired:
        return {"available": True, "error": "timeout", "cmd": args}
    return {
        "available": True,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "cmd": args,
    }


def print_json(payload: dict[str, Any]) -> None:
    """命令行 smoke 固定输出 JSON，方便远端脚本和 sprint 证据直接解析。"""
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def http_json(url: str, timeout_s: float, method: str = "GET", payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """自检客户端只访问 smoke HTTP 接口，不触碰 ROS2/串口/底盘控制链路。"""
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:  # noqa: S310 - 目标 URL 由本地 smoke 命令显式传入。
            data = response.read().decode("utf-8", errors="replace")
            return {
                "ok": True,
                "status": response.status,
                "json": json.loads(data) if data else None,
            }
    except urllib.error.HTTPError as exc:
        data = exc.read().decode("utf-8", errors="replace")
        try:
            parsed: Any = json.loads(data)
        except json.JSONDecodeError:
            parsed = data
        return {"ok": False, "status": exc.code, "json": parsed}
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__, "detail": str(exc)}


def stop_peer_local_tracks(pc: Any) -> dict[str, Any]:
    """显式停止本端发送 track，避免只关 PeerConnection 时摄像头 FD 残留。"""
    stopped: list[str] = []
    errors: list[dict[str, str]] = []
    for sender in getattr(pc, "getSenders", lambda: [])():
        track = getattr(sender, "track", None)
        if track is None:
            continue
        try:
            # aiortc 的 close 不等价于业务资源释放；这里先停 track 再关连接。
            track.stop()
            stopped.append(getattr(track, "kind", type(track).__name__))
        except Exception as exc:  # noqa: BLE001 - 清理路径要继续释放其他 track。
            errors.append({"track": repr(track), "error": type(exc).__name__, "detail": str(exc)})
    return {"stopped_tracks": stopped, "track_stop_errors": errors}


async def close_peer_connection(peer_id: str, pc: Any, pcs: dict[str, Any] | None = None) -> dict[str, Any]:
    """统一 peer 清理顺序：先移出 active 表，再停本地 track，最后关闭连接。"""
    if pcs is not None:
        # 先 pop 可避免连接状态回调重入时重复清理同一个 peer。
        pcs.pop(peer_id, None)
    cleanup = stop_peer_local_tracks(pc)
    close_error: dict[str, str] | None = None
    try:
        await pc.close()
    except Exception as exc:  # noqa: BLE001 - close 失败也要把 stop 证据返回给调用方。
        close_error = {"error": type(exc).__name__, "detail": str(exc)}
    return {
        "peer_id": peer_id,
        "stopped_tracks": cleanup["stopped_tracks"],
        "track_stop_errors": cleanup["track_stop_errors"],
        "close_error": close_error,
    }


def build_health(port: int, video_source: str) -> dict[str, Any]:
    """健康输出明确写 safe_to_control=false，避免被误接入控制链路。"""
    state = import_state()
    system_diagnostics = collect_system_diagnostics()
    empty_media_summary = build_media_summary({}, None)
    return {
        "schema": "trashbot.local_webrtc_camera_smoke.v1",
        "app": APP_NAME,
        "status": "ready" if all(state.values()) else "degraded",
        "host": socket.gethostname(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "port": port,
        "video_source": video_source,
        "video_source_mode": "auto" if str(video_source).strip().lower() in ("", "auto", "autodetect") else "explicit",
        "imports": state,
        "lan_only": True,
        "cloud_relay": False,
        "turn_required": False,
        "sends_commands": False,
        "safe_to_control": False,
        "robot_control_executed": False,
        "system_metrics": build_system_metrics(system_diagnostics),
        "stability_metrics": build_stability_metrics(0, empty_media_summary),
        "system_diagnostics": system_diagnostics,
        "media_stability_summary": empty_media_summary,
        "diagnostics": {
            "offer_self_test": "/offer recvonly SDP client is available via --self-test-url",
            "frame_boundary": "first_frame_received proves aiortc answer plus one decoded video frame",
            "stability_metrics": "system/media fields are read-only evidence for O7 short-run stability, not robot control inputs",
        },
        "vendor_reference": [
            "docs/vendor/VENDOR_INDEX.md",
            "docs/interfaces/o7_realtime_hardware_sources.md",
            "docs/vendor/waveshare_wave_rover/ugv_rpi/app.py",
        ],
    }


def build_devices() -> dict[str, Any]:
    """设备输出保留 v4l2 原始摘要，便于定位权限/格式/驱动问题。"""
    devices = list_video_devices()
    v4l2_path = shutil.which("v4l2-ctl")
    return {
        "schema": "trashbot.local_webrtc_camera_devices.v1",
        "devices": devices,
        "v4l2_ctl": v4l2_path or None,
        "v4l2_list_devices": run_short_command([v4l2_path, "--list-devices"]) if v4l2_path else None,
    }


def html_page(port: int, video_source: str) -> str:
    """页面只做接收视频和诊断展示，不渲染任何机器人控制入口。"""
    health = json.dumps(build_health(port, video_source), ensure_ascii=False, indent=2)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>rober LAN WebRTC Camera Smoke</title>
  <style>
    body {{ margin: 0; font-family: system-ui, sans-serif; background: #101418; color: #edf2f7; }}
    main {{ max-width: 960px; margin: 0 auto; padding: 24px; }}
    video {{ width: 100%; max-height: 70vh; background: #000; border: 1px solid #364152; }}
    button {{ padding: 10px 14px; margin: 12px 8px 12px 0; }}
    pre {{ overflow: auto; background: #18202a; padding: 12px; border: 1px solid #364152; }}
    .bad {{ color: #ffb4a8; }}
  </style>
</head>
<body>
  <main>
    <h1>rober LAN WebRTC Camera Smoke</h1>
    <p>Receive-only WebRTC video. LAN only. No cloud relay, no TURN, no robot control.</p>
    <video id="video" autoplay playsinline controls muted></video>
    <div>
      <button id="start">Start WebRTC video</button>
      <button id="stop">Stop WebRTC video</button>
      <button id="health">Refresh health/devices</button>
    </div>
    <pre id="status">{health}</pre>
  </main>
  <script>
    const video = document.getElementById('video');
    const statusBox = document.getElementById('status');
    let pc = null;
    let serverPeerId = null;
    function show(value) {{
      statusBox.textContent = typeof value === 'string' ? value : JSON.stringify(value, null, 2);
    }}
    function waitForIceGatheringComplete(peer) {{
      if (peer.iceGatheringState === 'complete') return Promise.resolve();
      // smoke 服务没有 trickle ICE 信令，offer 必须带完整候选，避免 answer 成功但 RTP 不启动。
      return new Promise(resolve => {{
        const done = () => {{
          if (peer.iceGatheringState === 'complete') {{
            peer.removeEventListener('icegatheringstatechange', done);
            resolve();
          }}
        }};
        peer.addEventListener('icegatheringstatechange', done);
        setTimeout(resolve, 2500);
      }});
    }}
    function closeServerPeer(reason) {{
      if (!serverPeerId) return;
      const url = `/peers/${{serverPeerId}}/close`;
      const body = JSON.stringify({{ reason }});
      // 页面关闭时 fetch 可能被浏览器取消，sendBeacon/keepalive 是释放板端摄像头的兜底。
      if (navigator.sendBeacon) {{
        navigator.sendBeacon(url, new Blob([body], {{ type: 'application/json' }}));
      }} else {{
        fetch(url, {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }}, body, keepalive: true }}).catch(() => null);
      }}
      serverPeerId = null;
    }}
    async function stop(reason = 'manual_stop') {{
      closeServerPeer(reason);
      if (pc) {{
        // 浏览器本地也要停 transceiver/track，避免下一次点击复用旧状态。
        pc.getSenders().forEach(sender => sender.track && sender.track.stop());
        pc.getReceivers().forEach(receiver => receiver.track && receiver.track.stop());
        pc.close();
        pc = null;
      }}
      video.srcObject = null;
      await refresh();
    }}
    async function refresh() {{
      const [health, devices] = await Promise.all([
        fetch('/health').then(r => r.json()),
        fetch('/devices').then(r => r.json()),
      ]);
      show({{ health, devices }});
    }}
    async function start() {{
      await stop('restart_before_new_offer');
      pc = new RTCPeerConnection({{ iceServers: [] }});
      pc.addTransceiver('video', {{ direction: 'recvonly' }});
      pc.ontrack = event => {{
        // aiortc addTrack 可能触发 streamless track；Chrome 收到 track 但 srcObject 为空时 readyState 会一直是 0。
        video.srcObject = event.streams && event.streams[0] ? event.streams[0] : new MediaStream([event.track]);
        video.play().catch(error => show({{ videoPlayError: String(error), serverPeerId }}));
      }};
      pc.onconnectionstatechange = () => show({{ connectionState: pc.connectionState }});
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);
      await waitForIceGatheringComplete(pc);
      const response = await fetch('/offer', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify(pc.localDescription),
      }});
      const payload = await response.json();
      if (!response.ok) throw new Error(JSON.stringify(payload));
      serverPeerId = payload.peer_id || null;
      await pc.setRemoteDescription(payload);
      show({{ connectionState: pc.connectionState, answerType: payload.type, serverPeerId }});
    }}
    document.getElementById('start').onclick = () => start().catch(err => show(String(err)));
    document.getElementById('stop').onclick = () => stop().catch(err => show(String(err)));
    document.getElementById('health').onclick = () => refresh().catch(err => show(String(err)));
    window.addEventListener('pagehide', () => closeServerPeer('pagehide'));
    window.addEventListener('beforeunload', () => closeServerPeer('beforeunload'));
    refresh().catch(err => show(String(err)));
  </script>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--video-source", default=os.getenv("ROBER_CAMERA_SOURCE", DEFAULT_VIDEO_SOURCE))
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--fps", type=int, default=DEFAULT_FPS)
    parser.add_argument(
        "--self-test-url",
        default=None,
        help="Run recvonly WebRTC offer-level client against an already running smoke base URL.",
    )
    parser.add_argument("--self-test-timeout", type=float, default=8.0)
    parser.add_argument(
        "--require-frame",
        action="store_true",
        help="Return non-zero when the self-test cannot receive a first video frame.",
    )
    return parser.parse_args()


async def self_test_client(args: argparse.Namespace) -> int:
    """本地/远端自检只做 recvonly 观看证明，不产生任何机器人动作。"""
    base_url = str(args.self_test_url).rstrip("/")
    started_at = time.monotonic()
    health = http_json(f"{base_url}/health", args.self_test_timeout)
    devices = http_json(f"{base_url}/devices", args.self_test_timeout)
    result: dict[str, Any] = {
        "schema": "trashbot.local_webrtc_camera_offer_self_test.v1",
        "target": base_url,
        "status": "starting",
        "safe_to_control": False,
        "sends_commands": False,
        "robot_control_executed": False,
        "lan_only": True,
        "turn_required": False,
        "health": health,
        "devices": devices,
        "answer_received": False,
        "first_frame_received": False,
        "connection_state": None,
    }
    peer_id: str | None = None
    state = import_state()
    result["client_imports"] = state
    if not health.get("ok"):
        result.update({"status": "failed", "reason": "health_unreachable"})
        print_json(result)
        return 2 if args.require_frame else 0
    if not state.get("aiortc") or not state.get("aiohttp"):
        result.update({"status": "degraded", "reason": "webrtc_client_dependency_missing"})
        print_json(result)
        return 2 if args.require_frame else 0

    # aiortc 只在自检模式按需导入，避免缺依赖时影响诊断 HTTP 服务。
    from aiohttp import ClientSession, ClientTimeout
    from aiortc import RTCPeerConnection, RTCSessionDescription
    from aiortc.contrib.media import MediaStreamError

    pc = RTCPeerConnection(configuration=None)
    frame_event = asyncio.Event()
    track_error: dict[str, Any] = {}

    @pc.on("track")
    def on_track(track: Any) -> None:
        async def read_first_frame() -> None:
            try:
                frame = await asyncio.wait_for(track.recv(), timeout=args.self_test_timeout)
                result["first_frame_received"] = True
                result["first_frame"] = {
                    "width": getattr(frame, "width", None),
                    "height": getattr(frame, "height", None),
                    "pts": getattr(frame, "pts", None),
                }
            except (asyncio.TimeoutError, MediaStreamError) as exc:
                track_error.update({"error": type(exc).__name__, "detail": str(exc)})
            finally:
                frame_event.set()

        asyncio.create_task(read_first_frame())

    try:
        pc.addTransceiver("video", direction="recvonly")
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        if pc.iceGatheringState != "complete":
            # aiortc 这里同样没有 trickle 信令；等候选收齐后再 POST，和真实浏览器路径保持一致。
            gather_done = asyncio.Event()

            @pc.on("icegatheringstatechange")
            async def on_icegatheringstatechange() -> None:
                if pc.iceGatheringState == "complete":
                    gather_done.set()

            try:
                await asyncio.wait_for(gather_done.wait(), timeout=min(args.self_test_timeout, 2.5))
            except asyncio.TimeoutError:
                result["client_ice_gathering_timeout"] = True
        result["client_ice_gathering_state"] = pc.iceGatheringState
        async with ClientSession(timeout=ClientTimeout(total=args.self_test_timeout)) as session:
            async with session.post(
                f"{base_url}/offer",
                json={"sdp": pc.localDescription.sdp, "type": pc.localDescription.type},
            ) as response:
                answer_payload = await response.json(content_type=None)
                result["offer_http_status"] = response.status
                if response.status >= 400:
                    result.update({"status": "failed", "reason": "offer_rejected", "offer_response": answer_payload})
                    print_json(result)
                    return 2 if args.require_frame else 0
        peer_id = answer_payload.get("peer_id")
        result["peer_id"] = peer_id
        result["answer_received"] = answer_payload.get("type") == "answer" and bool(answer_payload.get("sdp"))
        await pc.setRemoteDescription(RTCSessionDescription(sdp=answer_payload["sdp"], type=answer_payload["type"]))
        await asyncio.wait_for(frame_event.wait(), timeout=args.self_test_timeout)
        result["connection_state"] = pc.connectionState
    except Exception as exc:
        result.update({"status": "failed", "reason": type(exc).__name__, "detail": str(exc)})
        if track_error:
            result["track_error"] = track_error
    finally:
        result["duration_ms"] = int((time.monotonic() - started_at) * 1000)
        await pc.close()
        if peer_id:
            # WebRTC close 不会自动走 HTTP signaling，显式释放服务端 peer 才能连续自检。
            result["server_peer_close"] = http_json(f"{base_url}/peers/{peer_id}/close", 2.0, method="POST")
    if track_error:
        result["track_error"] = track_error
    if result.get("answer_received") and result.get("first_frame_received"):
        result["status"] = "ok"
    elif result.get("status") == "starting":
        result["status"] = "failed"
        result["reason"] = "first_frame_not_received"
    print_json(result)
    return 0 if result["status"] == "ok" or not args.require_frame else 2


def fallback_server(args: argparse.Namespace) -> None:
    """aiohttp 不存在时仍给出诊断 HTTP，方便远端无网时定位缺口。"""

    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, content_type: str, data: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:  # noqa: N802 - 标准库回调名固定为驼峰。
            if self.path == "/health":
                payload = json.dumps(build_health(args.port, args.video_source), ensure_ascii=False).encode()
                self._send(HTTPStatus.OK, "application/json", payload)
            elif self.path == "/devices":
                payload = json.dumps(build_devices(), ensure_ascii=False).encode()
                self._send(HTTPStatus.OK, "application/json", payload)
            else:
                self._send(HTTPStatus.OK, "text/html; charset=utf-8", html_page(args.port, args.video_source).encode())

        def do_POST(self) -> None:  # noqa: N802 - 标准库回调名固定为驼峰。
            payload = {
                "error": "webrtc_dependency_missing",
                "message": "aiohttp/aiortc/cv2/av must be installed before /offer can create WebRTC answer",
                "imports": import_state(),
            }
            self._send(HTTPStatus.SERVICE_UNAVAILABLE, "application/json", json.dumps(payload).encode())

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(json.dumps({"event": "fallback_server_started", "health": build_health(args.port, args.video_source)}))
    server.serve_forever()


async def aiohttp_server(args: argparse.Namespace) -> None:
    """主服务路径：aiortc 生成 answer，OpenCV 读取真实摄像头帧。"""
    from aiohttp import web
    from aiortc import RTCPeerConnection, RTCSessionDescription
    from aiortc.contrib.media import MediaStreamError
    from aiortc.mediastreams import VideoStreamTrack
    import av
    import cv2

    pcs: dict[str, RTCPeerConnection] = {}
    peer_stats: dict[str, dict[str, Any]] = {}
    closed_peer_stats: dict[str, Any] | None = None
    started_at_ms = now_ms()

    class CameraTrack(VideoStreamTrack):
        """每个 peer 单独持有摄像头，第一版限制单连接来降低设备占用风险。"""

        def __init__(self, peer_id: str, stats: dict[str, Any]) -> None:
            super().__init__()
            self.peer_id = peer_id
            self.stats = stats
            self._stopped = False
            source, source_selection = resolve_camera_source(
                args.video_source,
                cv2,
                width=args.width,
                height=args.height,
                fps=args.fps,
            )
            self.stats["source_selection"] = source_selection
            if source is None:
                self.stats["last_error"] = f"camera_auto_source_failed:{args.video_source}"
                self.stats["last_error_ts_ms"] = now_ms()
                raise RuntimeError(f"camera_auto_source_failed:{args.video_source}")
            self.cap = open_video_capture(cv2, source)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
            self.cap.set(cv2.CAP_PROP_FPS, args.fps)
            if not self.cap.isOpened():
                self.stats["last_error"] = f"camera_open_failed:{args.video_source}"
                self.stats["last_error_ts_ms"] = now_ms()
                raise RuntimeError(f"camera_open_failed:{args.video_source}")
            self.stats.update(
                {
                    "camera_opened": True,
                    "resolved_video_source": source,
                    "capture_backend": self.cap.getBackendName() if hasattr(self.cap, "getBackendName") else None,
                    "configured_width": args.width,
                    "configured_height": args.height,
                    "configured_fps": args.fps,
                    "actual_width": self.cap.get(cv2.CAP_PROP_FRAME_WIDTH),
                    "actual_height": self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT),
                    "actual_fps": self.cap.get(cv2.CAP_PROP_FPS),
                }
            )
            log_event("camera_track_opened", peer_id=self.peer_id, stats=self.stats)

        async def recv(self) -> av.VideoFrame:
            pts, time_base = await self.next_timestamp()
            ok, frame = await asyncio.to_thread(self.cap.read)
            if not ok or frame is None:
                self.stats["camera_read_failures"] += 1
                self.stats["last_error"] = "camera_frame_read_failed"
                self.stats["last_error_ts_ms"] = now_ms()
                log_event("camera_frame_read_failed", peer_id=self.peer_id, failures=self.stats["camera_read_failures"])
                raise MediaStreamError("camera_frame_read_failed")
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            video_frame = av.VideoFrame.from_ndarray(rgb, format="rgb24")
            video_frame.pts = pts
            video_frame.time_base = time_base
            self.stats["frames_read"] += 1
            self.stats["last_frame_ts_ms"] = now_ms()
            self.stats["last_frame_width"] = getattr(video_frame, "width", None)
            self.stats["last_frame_height"] = getattr(video_frame, "height", None)
            self.stats["last_frame_pts"] = pts
            if self.stats["frames_read"] <= 3 or self.stats["frames_read"] % max(args.fps, 1) == 0:
                # 前几帧和每秒采样写日志，避免 30s 首帧失败时日志仍是空的。
                log_event(
                    "camera_frame_encoded",
                    peer_id=self.peer_id,
                    frames_read=self.stats["frames_read"],
                    width=self.stats["last_frame_width"],
                    height=self.stats["last_frame_height"],
                )
            return video_frame

        def stop(self) -> None:
            if self._stopped:
                return
            self._stopped = True
            self.stats["track_stopped"] = True
            self.stats["track_stopped_ts_ms"] = now_ms()
            # OpenCV 摄像头句柄必须显式 release，给连续 browser/self-test 留出设备。
            self.cap.release()
            log_event("camera_track_stopped", peer_id=self.peer_id, stats=self.stats)
            super().stop()

    async def index(_: web.Request) -> web.Response:
        return web.Response(text=html_page(args.port, args.video_source), content_type="text/html")

    async def health(_: web.Request) -> web.Response:
        payload = build_health(args.port, args.video_source)
        payload["active_peer_connections"] = len(pcs)
        payload["active_peer_ids"] = sorted(pcs.keys())
        payload["media_stability_summary"] = build_media_summary(peer_stats, closed_peer_stats)
        payload["stability_metrics"] = build_stability_metrics(len(pcs), payload["media_stability_summary"])
        payload["media_diagnostics"] = {
            "server_started_at_ms": started_at_ms,
            "server_uptime_ms": now_ms() - started_at_ms,
            "active_peers": peer_stats,
            "last_closed_peer": closed_peer_stats,
        }
        payload["peer_cleanup"] = {
            "close_one": "/peers/{peer_id}/close",
            "reason": "health exposes peer ids only for LAN smoke cleanup after browser/test aborts",
        }
        return web.json_response(payload)

    async def devices(_: web.Request) -> web.Response:
        return web.json_response(build_devices())

    async def offer(request: web.Request) -> web.Response:
        if not all(import_state().values()):
            return web.json_response({"error": "webrtc_dependency_missing", "imports": import_state()}, status=503)
        if len(pcs) >= 1:
            return web.json_response({"error": "camera_in_use", "active_peer_connections": len(pcs)}, status=409)
        params = await request.json()
        pc = RTCPeerConnection(configuration=None)
        peer_id = uuid.uuid4().hex
        pcs[peer_id] = pc
        stats: dict[str, Any] = {
            "peer_id": peer_id,
            "created_ts_ms": now_ms(),
            "frames_read": 0,
            "camera_read_failures": 0,
            "camera_opened": False,
            "track_stopped": False,
            "connection_state": pc.connectionState,
            "ice_connection_state": pc.iceConnectionState,
            "ice_gathering_state": pc.iceGatheringState,
            "signaling_state": pc.signalingState,
            "remote_sdp_type": params.get("type"),
            "remote_sdp_has_video": "m=video" in params.get("sdp", ""),
            "remote_sdp_video_direction": next(
                (
                    line
                    for line in params.get("sdp", "").splitlines()
                    if line in ("a=sendrecv", "a=sendonly", "a=recvonly", "a=inactive")
                ),
                None,
            ),
            "remote_sdp_candidate_count": params.get("sdp", "").count("a=candidate:"),
            "remote_sdp_end_of_candidates": "a=end-of-candidates" in params.get("sdp", ""),
        }
        peer_stats[peer_id] = stats
        log_event("offer_received", peer_id=peer_id, remote_sdp_has_video=stats["remote_sdp_has_video"])

        @pc.on("connectionstatechange")
        async def on_connectionstatechange() -> None:
            nonlocal closed_peer_stats
            stats["connection_state"] = pc.connectionState
            stats["connection_state_ts_ms"] = now_ms()
            log_event("peer_connection_state", peer_id=peer_id, state=pc.connectionState)
            if pc.connectionState in ("failed", "closed", "disconnected"):
                if peer_id not in pcs and peer_id not in peer_stats:
                    # 主动 close 已经完成记录时，aiortc 仍可能再触发 closed 回调；这里避免覆盖有效统计。
                    return
                cleanup = await close_peer_connection(peer_id, pc, pcs)
                final_stats = peer_stats.pop(peer_id, {})
                closed_peer_stats = {"cleanup": cleanup, "stats": final_stats, "closed_ts_ms": now_ms()}
                log_event("peer_auto_closed", peer_id=peer_id, cleanup=cleanup, stats=final_stats)

        @pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange() -> None:
            stats["ice_connection_state"] = pc.iceConnectionState
            stats["ice_connection_state_ts_ms"] = now_ms()
            log_event("peer_ice_connection_state", peer_id=peer_id, state=pc.iceConnectionState)

        @pc.on("icegatheringstatechange")
        async def on_icegatheringstatechange() -> None:
            stats["ice_gathering_state"] = pc.iceGatheringState
            stats["ice_gathering_state_ts_ms"] = now_ms()

        @pc.on("signalingstatechange")
        async def on_signalingstatechange() -> None:
            stats["signaling_state"] = pc.signalingState
            stats["signaling_state_ts_ms"] = now_ms()

        track: CameraTrack | None = None
        try:
            track = CameraTrack(peer_id, stats)
            pc.addTrack(track)
            await pc.setRemoteDescription(RTCSessionDescription(sdp=params["sdp"], type=params["type"]))
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)
        except Exception as exc:
            stats["last_error"] = str(exc)
            stats["last_error_ts_ms"] = now_ms()
            if track is not None:
                # 如果 addTrack 前后异常，手里直接持有的 track 也要兜底释放。
                track.stop()
            await close_peer_connection(peer_id, pc, pcs)
            log_event("offer_failed", peer_id=peer_id, error=type(exc).__name__, detail=str(exc))
            return web.json_response({"error": "offer_failed", "detail": str(exc)}, status=500)
        stats["local_sdp_has_video"] = "m=video" in pc.localDescription.sdp
        stats["local_sdp_type"] = pc.localDescription.type
        log_event("offer_answered", peer_id=peer_id, local_sdp_has_video=stats["local_sdp_has_video"])
        return web.json_response({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type, "peer_id": peer_id})

    async def close_peer(request: web.Request) -> web.Response:
        nonlocal closed_peer_stats
        peer_id = request.match_info["peer_id"]
        pc = pcs.pop(peer_id, None)
        if pc is None:
            return web.json_response({"closed": False, "reason": "peer_not_found", "peer_id": peer_id}, status=404)
        # 只关闭调用方拿到的 peer_id，避免自检误杀正在人工查看的浏览器连接。
        stats = peer_stats.pop(peer_id, {})
        cleanup = await close_peer_connection(peer_id, pc, pcs)
        closed_peer_stats = {"cleanup": cleanup, "stats": stats, "closed_ts_ms": now_ms()}
        log_event("peer_closed", peer_id=peer_id, cleanup=cleanup, stats=stats)
        return web.json_response({"closed": True, **cleanup, "stats": stats, "active_peer_connections": len(pcs)})

    async def on_shutdown(_: web.Application) -> None:
        await asyncio.gather(
            *(close_peer_connection(peer_id, pc, pcs) for peer_id, pc in list(pcs.items())),
            return_exceptions=True,
        )
        pcs.clear()
        peer_stats.clear()

    app = web.Application()
    app.on_shutdown.append(on_shutdown)
    app.router.add_get("/", index)
    app.router.add_get("/health", health)
    app.router.add_get("/devices", devices)
    app.router.add_post("/offer", offer)
    app.router.add_post("/peers/{peer_id}/close", close_peer)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, args.host, args.port)
    await site.start()
    log_event("aiohttp_server_started", health=build_health(args.port, args.video_source))
    while True:
        await asyncio.sleep(3600)


def main() -> int:
    args = parse_args()
    if args.self_test_url:
        return asyncio.run(self_test_client(args))
    state = import_state()
    if not all(state.values()):
        # 依赖不完整时走标准库诊断服务，保证无网现场也能看到缺口。
        fallback_server(args)
        return 0
    try:
        asyncio.run(aiohttp_server(args))
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
