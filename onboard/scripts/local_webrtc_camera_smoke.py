#!/usr/bin/env python3
"""Orange Pi LAN-only WebRTC camera smoke service."""

from __future__ import annotations

import argparse
import asyncio
import glob
import importlib.util
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field
from fractions import Fraction
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable


SCHEMA = "trashbot.local_webrtc_camera_smoke.v1"
DEVICES_SCHEMA = "trashbot.local_webrtc_camera_devices.v1"
OFFER_SCHEMA = "trashbot.local_webrtc_camera_offer.v1"
CLOSE_SCHEMA = "trashbot.local_webrtc_camera_close.v1"
APP_NAME = "rober-local-webrtc-camera-smoke"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8088
DEFAULT_VIDEO_SOURCE = "auto"
DEFAULT_WIDTH = 640
DEFAULT_HEIGHT = 480
DEFAULT_FPS = 15
FIRST_FRAME_TIMEOUT_S = 3.0
COMMAND_TIMEOUT_S = 2.5
PEER_ID_PATTERN = re.compile(r"^[A-Za-z0-9]{1,32}$")
IMPORTS = ("aiortc", "cv2", "av")
TEMPERATURE_GLOBS = (
    "/sys/class/thermal/thermal_zone*/temp",
    "/sys/class/hwmon/hwmon*/temp*_input",
)

# 实现边界说明 001：本脚本只服务实时图传 smoke，不承担底盘控制职责。
# 实现边界说明 002：`/health` 可以被 PC 高频轮询，所以它不能打开摄像头。
# 实现边界说明 003：`/health` 可以读 sysfs/procfs，因为这些读取不会改变硬件状态。
# 实现边界说明 004：`/health` 返回 no_video_source 时仍是成功诊断，不等于服务崩溃。
# 实现边界说明 005：`/devices` 只做设备枚举，不能写入任何 V4L2 control。
# 实现边界说明 006：`/devices` 不用 OpenCV 打开设备，避免抢占真实 WebRTC 会话。
# 实现边界说明 007：`v4l2-ctl --all` 在这里只作为只读能力查询使用。
# 实现边界说明 008：`v4l2-ctl --list-formats-ext` 用于识别 MJPG/YUYV 等格式。
# 实现边界说明 009：没有安装 `v4l2-ctl` 时服务仍可运行，只是诊断降级。
# 实现边界说明 010：auto 选源必须解释“为什么选中”，所以 health 暴露 ranked 摘要。
# 实现边界说明 011：Orange Pi H618 的 Cedrus 节点是 decoder，不应作为摄像头。
# 实现边界说明 012：metadata 节点不提供普通图像帧，必须从 auto 候选中剔除。
# 实现边界说明 013：`Video Capture` 是 auto 选择真实采集节点的最低正向信号。
# 实现边界说明 014：UVC/USB 只作为加分项，不能覆盖 decoder/metadata 的硬剔除。
# 实现边界说明 015：当前实板 `/dev/video1` 是 DV20 UVC capture，因此会获得最高分。
# 实现边界说明 016：显式 `--video-source` 是 operator 排障入口，不能被 auto 覆盖。
# 实现边界说明 017：显式源即使不存在，也要让 OpenCV 给出真实打开失败原因。
# 实现边界说明 018：`/offer` 是唯一会打开摄像头的 endpoint，因此必须最保守。
# 实现边界说明 019：`/offer` 收到非 object body 时不能创建 peer。
# 实现边界说明 020：`/offer` 收到非 offer type 时不能创建 peer。
# 实现边界说明 021：`/offer` 收到空 SDP 时不能创建 peer。
# 实现边界说明 022：缺少 `aiortc` 时不能返回伪 answer。
# 实现边界说明 023：缺少 `cv2` 时不能假装有真实摄像头帧。
# 实现边界说明 024：缺少 `av` 时不能构造 WebRTC video frame。
# 实现边界说明 025：依赖缺失用 HTTP 503，是运行环境未就绪而不是客户端成功。
# 实现边界说明 026：OpenCV 打不开设备时立即 release，避免残留句柄。
# 实现边界说明 027：首帧不可读时必须 release capture，避免现场反复重试卡死。
# 实现边界说明 028：首帧不可读不能发送黑帧，因为黑帧会掩盖真实输入故障。
# 实现边界说明 029：首帧不可读不能发送 placeholder，因为 PC 会误判图传可用。
# 实现边界说明 030：只有读到真实首帧后才允许创建 answer。
# 实现边界说明 031：首帧先读一帧，是为了把错误前置到 HTTP answer 之前。
# 实现边界说明 032：answer 创建失败时必须关闭 peer 并 release capture。
# 实现边界说明 033：track.recv 每次从真实 capture 读帧，不缓存伪造序列。
# 实现边界说明 034：track 读帧失败时抛错，让 WebRTC 流自然进入失败路径。
# 实现边界说明 035：frame 计数只表示真实读取次数，不代表画面内容可见。
# 实现边界说明 036：luma/可见内容判定仍由 PC canvas 或现场 artifact 完成。
# 实现边界说明 037：peer_id 限制短字母数字，避免路径注入和日志污染。
# 实现边界说明 038：close endpoint 必须可以重复被 PC 页面安全调用。
# 实现边界说明 039：peer 不存在返回 404，不应创建新的清理副作用。
# 实现边界说明 040：close 时先关闭 RTCPeerConnection，再停止 track。
# 实现边界说明 041：close 时最后 release capture，确保底层设备被释放。
# 实现边界说明 042：cleanup 的每一步都独立容错，避免前一步失败阻断后续释放。
# 实现边界说明 043：last_closed_peer 留在 health 中，方便 PC stop 后确认回收。
# 实现边界说明 044：active_peer_count 必须来自真实 peers 表，不靠前端声明。
# 实现边界说明 045：active_frames_read 必须按 peer 汇总，不用全局自增伪造。
# 实现边界说明 046：active_camera_read_failures 记录当前 active peer 的读帧失败。
# 实现边界说明 047：last_offer_error 保留最近失败根因，帮助现场区分依赖和设备问题。
# 实现边界说明 048：HTTP server 用标准库，是为了本机无 aiohttp 时仍可复现。
# 实现边界说明 049：WebRTC 本身仍严格依赖 aiortc/cv2/av，不做弱化替代。
# 实现边界说明 050：CORS 只服务 LAN 调试，不代表公网或云端安全已经完成。
# 实现边界说明 051：所有响应固定 safe_to_control=false，避免媒体状态外溢成控制许可。
# 实现边界说明 052：所有响应固定 robot_control_executed=false，本服务不执行运动。
# 实现边界说明 053：所有响应固定 delivery_success=false，图传不证明投递成功。
# 实现边界说明 054：所有响应固定 primary_actions_enabled=false，PC 首屏仍受门禁约束。
# 实现边界说明 055：脚本不导入 ROS2，因为 camera smoke 不应拉起 ROS graph。
# 实现边界说明 056：脚本不打开 `/dev/ttyS5`，避免影响 WAVE ROVER UART。
# 实现边界说明 057：脚本不发布 `/cmd_vel`，避免相机验证触发底盘运动。
# 实现边界说明 058：脚本不调用 `/api/base/manual`，避免绕过 PC HIL gate。
# 实现边界说明 059：脚本不启动雷达、地图或 Nav2，只聚焦视频服务。
# 实现边界说明 060：系统温度只解释稳定性，不参与自动降级或控制。
# 实现边界说明 061：load average 只解释进程压力，不作为业务成功条件。
# 实现边界说明 062：hostname/platform 只用于现场日志定位，不影响行为。
# 实现边界说明 063：命令输出做长度截断，避免设备 dump 把 health/devices 撑爆。
# 实现边界说明 064：错误文本做长度截断，避免无关本机上下文扩散。
# 实现边界说明 065：JSON 序列化统一走 json_safe，保证 Path 等对象不会打断响应。
# 实现边界说明 066：设备排序保留负分项，便于看出 Cedrus 为什么被跳过。
# 实现边界说明 067：`/dev/video1` 加很小分，只用于当前实板同分时稳定选择。
# 实现边界说明 068：`/dev/video1` 小加分不能覆盖 metadata/decoder 的硬负分。
# 实现边界说明 069：无正分候选时 auto 不回退到 `/dev/video0`。
# 实现边界说明 070：无正分候选时 `/offer` 返回 video_source_unavailable。
# 实现边界说明 071：no-hardware 本地开发机可以用 health/devices 验证服务框架。
# 实现边界说明 072：no-hardware 本地开发机不应尝试伪造 `/offer` 通过。
# 实现边界说明 073：单元测试用 mock 候选表达真实板端枚举事实。
# 实现边界说明 074：单元测试用缺依赖场景锁住 fail-closed contract。
# 实现边界说明 075：单元测试不打开真实设备，避免污染开发主机。
# 实现边界说明 076：`ThreadingHTTPServer` 允许 health/devices 与 close 并发响应。
# 实现边界说明 077：并发模型很轻量，当前 smoke 不做复杂 session 调度。
# 实现边界说明 078：peer 表没有持久化，服务重启后由 PC 重新建会话。
# 实现边界说明 079：服务重启不恢复旧 peer，因为旧 WebRTC connection 已不可用。
# 实现边界说明 080：server shutdown 会逐个 close peer，避免 systemd stop 后占用设备。
# 实现边界说明 081：KeyboardInterrupt 也走 shutdown cleanup，便于本地调试。
# 实现边界说明 082：日志使用 ensure_ascii=false，现场中文原因更容易读。
# 实现边界说明 083：日志 sort_keys=true，方便 diff 多次 smoke 输出。
# 实现边界说明 084：HTTP access log 结构化，便于从 journal 中筛选 endpoint。
# 实现边界说明 085：request body 限制 2MB，避免异常 SDP 或误传文件撑爆内存。
# 实现边界说明 086：坏 JSON 返回 invalid_json，不进入 offer 校验分支。
# 实现边界说明 087：unknown endpoint 返回 not_found，不做任何设备访问。
# 实现边界说明 088：OPTIONS 只返回安全字段，预检不触发 devices 枚举。
# 实现边界说明 089：`source_summary` 和 `source_candidates_summary` 同时保留，兼容不同消费者。
# 实现边界说明 090：`active_peer_connections` 保留给历史 PC readback 兼容。
# 实现边界说明 091：`requested_video_source` 明确区分 operator 输入和实际选择。
# 实现边界说明 092：`video_source` 在 auto 下返回实际 selected path，更利于排障。
# 实现边界说明 093：没有 selected path 时 `video_source` 回到 requested 值。
# 实现边界说明 094：`status=no_video_source` 只说明本机没有候选，不说明上车失败。
# 实现边界说明 095：`status=ready` 也不证明画面可见，只证明诊断入口有源。
# 实现边界说明 096：`first_frame_read=true` 只在 answer 成功时返回。
# 实现边界说明 097：远端 SDP candidate count 只解释网络协商，不代表画面可见。
# 实现边界说明 098：本地 SDP candidate count 只解释 answer 内容，不代表公网可用。
# 实现边界说明 099：没有 STUN/TURN 配置，当前服务仍是 LAN/local smoke。
# 实现边界说明 100：公网、云 relay 和鉴权不是本脚本职责。
# 实现边界说明 101：音频、录制和截图归档不是本脚本职责。
# 实现边界说明 102：媒体编码性能优化不是本轮目标，先保证可诊断。
# 实现边界说明 103：真实 `/dev/video1` first-frame timeout 仍需现场硬件动作。
# 实现边界说明 104：入仓服务只能让问题可复现，不能替代更换摄像头验证。
# 实现边界说明 105：若 known-good UVC 可读，后续可用同一 `/offer` 路径验证 PC 图传。
# 实现边界说明 106：若 known-good UVC 仍不可读，应继续查内核/USB/供电链路。
# 实现边界说明 107：`VideoCapture.set` 请求参数失败不直接判失败，以首帧为准。
# 实现边界说明 108：首帧 timeout 设置较短，避免 PC 页面长时间卡在 offer。
# 实现边界说明 109：读帧循环轻微 sleep，避免空转占满 CPU。
# 实现边界说明 110：异常路径抛回 create_answer，再统一转结构化 JSON。
# 实现边界说明 111：结构化错误带 failure_reason，PC 可以直接展示短原因。
# 实现边界说明 112：结构化错误带 schema/app，便于代理层识别来源。
# 实现边界说明 113：结构化错误同样固定安全字段，避免失败响应被误用。
# 实现边界说明 114：设备候选保留 realpath，便于现场识别 udev/symlink 漂移。
# 实现边界说明 115：设备候选保留 sysfs_name，便于无 v4l2-ctl 的极简系统排障。
# 实现边界说明 116：设备候选保留 v4l2_name，便于和现场 `--list-devices` 对照。
# 实现边界说明 117：devices 响应带 generated_at_ms，便于判断是否读到最新枚举。
# 实现边界说明 118：peer summary 带 last_frame_age_ms，便于判断流是否停滞。
# 实现边界说明 119：peer summary 带 fps_estimate，只作粗略稳定性观察。
# 实现边界说明 120：peer summary 带 last_error，便于区分读帧和连接状态问题。
# 实现边界说明 121：close summary 带 cleanup 三阶段结果，便于确认释放是否完整。
# 实现边界说明 122：本脚本的成功边界是服务可复现，不是 visible_content_proven。
# 实现边界说明 123：visible_content_proven 必须继续依赖 PC canvas 或现场样张。
# 实现边界说明 124：运动 HIL gate 仍需要外部视频、轮速反馈和 LiDAR delta。
# 实现边界说明 125：这些注释保留在代码中，是为了让后续上车修改不破坏安全边界。


def now_ms() -> int:
    """所有诊断用毫秒时间戳，便于和 PC/browser 证据对齐。"""
    return int(time.time() * 1000)


PROCESS_STARTED_WALL_MS = now_ms()
PROCESS_STARTED_MONOTONIC = time.monotonic()


def proof_flags() -> dict[str, Any]:
    """相机服务永远不提升控制许可，避免媒体可用被误读成运动安全。"""
    return {
        "safe_to_control": False,
        "robot_control_executed": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def log_event(event: str, **fields: Any) -> None:
    """结构化日志直接 flush，现场 systemd/journal 才能定位首帧失败。"""
    payload = {"event": event, "ts_ms": now_ms(), **fields}
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)


def import_state() -> dict[str, bool]:
    """只探测依赖是否存在；缺依赖时仍允许 health/devices 诊断。"""
    return {name: importlib.util.find_spec(name) is not None for name in IMPORTS}


def compact_error(error: BaseException) -> dict[str, str]:
    """错误回包只暴露短文本，避免把本机无关路径扩散到 PC UI。"""
    return {"type": type(error).__name__, "message": str(error)[:240]}


def json_safe(value: Any) -> Any:
    """把 numpy/path 等潜在对象压成 JSON 可序列化形态。"""
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


def error_payload(error: str, reason: str, status: str = "error", **fields: Any) -> dict[str, Any]:
    """所有失败都显式 fail-closed，调用方不能从 HTTP 形态推导控制可用。"""
    return {
        "schema": SCHEMA,
        "app": APP_NAME,
        "status": status,
        "error": error,
        "failure_reason": reason,
        "generated_at_ms": now_ms(),
        **proof_flags(),
        **json_safe(fields),
    }


def read_float_file(path: Path) -> float | None:
    """sysfs 诊断只读且容错，缺文件不能影响服务存活。"""
    try:
        return float(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def collect_temperature_diagnostics() -> dict[str, Any]:
    """温度只用于解释编码/读帧稳定性，不参与任何自动控制决策。"""
    samples: list[dict[str, Any]] = []
    for pattern in TEMPERATURE_GLOBS:
        for name in sorted(glob.glob(pattern)):
            raw = read_float_file(Path(name))
            if raw is None:
                continue
            celsius = raw / 1000.0 if abs(raw) > 200 else raw
            samples.append({"path": name, "celsius": round(celsius, 3), "raw": raw})
    if not samples:
        return {"available": False, "reason": "temperature_files_not_found"}
    return {"available": True, "samples": samples[:12]}


def collect_system_diagnostics() -> dict[str, Any]:
    """系统诊断只读采样，用来判断服务进程是否仍健康。"""
    payload: dict[str, Any] = {
        "host": socket.gethostname(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "pid": os.getpid(),
        "process_started_wall_time_ms": PROCESS_STARTED_WALL_MS,
        "process_uptime_s": round(time.monotonic() - PROCESS_STARTED_MONOTONIC, 3),
        "cpu_count": os.cpu_count(),
        "temperature": collect_temperature_diagnostics(),
    }
    try:
        load1, load5, load15 = os.getloadavg()
        payload["load_average"] = {"1m": load1, "5m": load5, "15m": load15}
    except (AttributeError, OSError):
        payload["load_average"] = {"available": False, "reason": "os_getloadavg_unavailable"}
    return payload


def run_readonly_command(args: list[str], timeout_s: float = COMMAND_TIMEOUT_S) -> dict[str, Any]:
    """只运行枚举类命令；调用点负责保证不写 V4L2 controls。"""
    if not args or shutil.which(args[0]) is None:
        return {"available": False, "reason": "command_not_found", "args": args}
    try:
        completed = subprocess.run(
            args,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        return {"available": False, "reason": "timeout", "args": args, "timeout_s": timeout_s}
    except OSError as exc:
        return {"available": False, "reason": "os_error", "args": args, "error": compact_error(exc)}
    return {
        "available": True,
        "args": args,
        "returncode": completed.returncode,
        "stdout": completed.stdout[:12000],
        "stderr": completed.stderr[:4000],
    }


def parse_v4l2_device_names(list_devices_text: str) -> dict[str, str]:
    """把 v4l2-ctl block 输出压成 path->设备名，供 auto 选源排序。"""
    mapping: dict[str, str] = {}
    current_name = ""
    for raw_line in list_devices_text.splitlines():
        line = raw_line.rstrip()
        if not line:
            current_name = ""
            continue
        if not line.startswith((" ", "\t")):
            current_name = line.rstrip(":")
            continue
        path = line.strip()
        if path.startswith("/dev/video"):
            mapping[path] = current_name
    return mapping


def read_sysfs_video_name(path: str) -> str | None:
    """sysfs 名称是只读事实；v4l2-ctl 不可用时仍能识别 Cedrus。"""
    name_path = Path("/sys/class/video4linux") / Path(path).name / "name"
    try:
        return name_path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None


def build_device_candidate(path: str, v4l2_name: str | None = None) -> dict[str, Any]:
    """设备候选只采集只读能力，不用 OpenCV 打开设备抢占摄像头。"""
    all_result = run_readonly_command(["v4l2-ctl", "--all", "-d", path])
    formats_result = run_readonly_command(["v4l2-ctl", "--list-formats-ext", "-d", path])
    sysfs_name = read_sysfs_video_name(path)
    text_parts = [v4l2_name or "", sysfs_name or ""]
    if all_result.get("available"):
        text_parts.append(str(all_result.get("stdout") or ""))
        text_parts.append(str(all_result.get("stderr") or ""))
    if formats_result.get("available"):
        text_parts.append(str(formats_result.get("stdout") or ""))
    combined_text = "\n".join(text_parts)
    lower_text = combined_text.lower()
    return {
        "path": path,
        "exists": os.path.exists(path),
        "realpath": os.path.realpath(path) if os.path.exists(path) else None,
        "v4l2_name": v4l2_name,
        "sysfs_name": sysfs_name,
        "capability_text_available": bool(all_result.get("available")),
        "formats_text_available": bool(formats_result.get("available")),
        "is_video_capture": "video capture" in lower_text and "metadata capture" not in lower_text,
        "is_metadata": "metadata capture" in lower_text or "metadata" in lower_text,
        "is_decoder": "cedrus" in lower_text or "decoder" in lower_text or "mem2mem" in lower_text,
        "is_uvc_or_usb": "uvc" in lower_text or "usb" in lower_text,
        "readonly_probe": {
            "v4l2_all": all_result,
            "v4l2_formats": formats_result,
        },
    }


def collect_video_candidates() -> dict[str, Any]:
    """枚举 /dev/video*，不写 controls、不打开串口、不碰底盘。"""
    paths = sorted(glob.glob("/dev/video*"))
    list_devices = run_readonly_command(["v4l2-ctl", "--list-devices"])
    names = {}
    if list_devices.get("available") and list_devices.get("stdout"):
        names = parse_v4l2_device_names(str(list_devices["stdout"]))
    candidates = [build_device_candidate(path, names.get(path)) for path in paths]
    return {
        "generated_at_ms": now_ms(),
        "paths": paths,
        "v4l2_list_devices": list_devices,
        "candidates": candidates,
        "opens_serial": False,
        "writes_controls": False,
        "sends_motion_commands": False,
        **proof_flags(),
    }


def score_candidate(candidate: dict[str, Any]) -> int:
    """auto 选源优先真实采集节点，明确避开 Cedrus decoder 和 metadata。"""
    score = 0
    if candidate.get("is_video_capture"):
        score += 100
    if candidate.get("is_uvc_or_usb"):
        score += 40
    if candidate.get("exists"):
        score += 5
    path = str(candidate.get("path") or "")
    if path.endswith("video1"):
        score += 3
    if candidate.get("is_decoder"):
        score -= 1000
    if candidate.get("is_metadata"):
        score -= 1000
    if not candidate.get("is_video_capture"):
        score -= 100
    return score


def choose_auto_source(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    """自动模式只选择正分采集候选；否则 fail-closed 等现场显式指定。"""
    ranked = sorted(
        ({**candidate, "selection_score": score_candidate(candidate)} for candidate in candidates),
        key=lambda item: (int(item["selection_score"]), str(item.get("path") or "")),
        reverse=True,
    )
    selected = next((item for item in ranked if int(item["selection_score"]) > 0), None)
    return {
        "mode": "auto",
        "selected_path": selected.get("path") if selected else None,
        "selected": selected,
        "ranked": [
            {
                "path": item.get("path"),
                "score": item.get("selection_score"),
                "is_video_capture": item.get("is_video_capture"),
                "is_uvc_or_usb": item.get("is_uvc_or_usb"),
                "is_decoder": item.get("is_decoder"),
                "is_metadata": item.get("is_metadata"),
                "name": item.get("v4l2_name") or item.get("sysfs_name"),
            }
            for item in ranked
        ],
    }


def resolve_video_source(requested_source: str, device_snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
    """显式源必须尊重；auto 才根据只读候选重排。"""
    if requested_source != "auto":
        return {
            "mode": "explicit",
            "requested_source": requested_source,
            "selected_path": requested_source,
            "selected": {"path": requested_source, "explicit": True, "exists": os.path.exists(requested_source)},
            "ranked": [],
        }
    snapshot = device_snapshot or collect_video_candidates()
    selection = choose_auto_source(list(snapshot.get("candidates") or []))
    selection["requested_source"] = requested_source
    return selection


def source_candidates_summary(snapshot: dict[str, Any], selection: dict[str, Any]) -> dict[str, Any]:
    """health 只输出短摘要，完整 v4l2 文本留在 /devices。"""
    candidates = []
    for candidate in snapshot.get("candidates") or []:
        candidates.append(
            {
                "path": candidate.get("path"),
                "exists": candidate.get("exists"),
                "name": candidate.get("v4l2_name") or candidate.get("sysfs_name"),
                "is_video_capture": candidate.get("is_video_capture"),
                "is_uvc_or_usb": candidate.get("is_uvc_or_usb"),
                "is_decoder": candidate.get("is_decoder"),
                "is_metadata": candidate.get("is_metadata"),
                "selection_score": score_candidate(candidate),
            }
        )
    return {
        "candidate_count": len(candidates),
        "candidates": candidates,
        "current_selection": {
            "mode": selection.get("mode"),
            "requested_source": selection.get("requested_source"),
            "selected_path": selection.get("selected_path"),
            "ranked": selection.get("ranked", [])[:8],
        },
    }


def validate_offer_payload(payload: Any) -> tuple[bool, str | None]:
    """只接受最小 SDP offer，坏输入不创建 peer、不打开摄像头。"""
    if not isinstance(payload, dict):
        return False, "json_body_must_be_object"
    if payload.get("type") != "offer":
        return False, "type_must_be_offer"
    if not isinstance(payload.get("sdp"), str) or not payload.get("sdp", "").strip():
        return False, "sdp_must_be_non_empty_string"
    return True, None


@dataclass
class PeerRecord:
    """记录 peer 资源，close endpoint 必须能释放 capture/track/connection。"""

    peer_id: str
    pc: Any
    track: Any
    capture: Any
    source: str
    created_ts_ms: int = field(default_factory=now_ms)
    frames_read: int = 0
    camera_read_failures: int = 0
    last_frame_ts_ms: int | None = None
    last_frame_width: int | None = None
    last_frame_height: int | None = None
    last_error: str | None = None
    connection_state: str | None = None
    ice_connection_state: str | None = None
    signaling_state: str | None = None
    remote_sdp_candidate_count: int = 0
    local_sdp_candidate_count: int = 0
    track_stopped: bool = False

    def summary(self) -> dict[str, Any]:
        """peer 摘要给 health 使用，避免直接暴露 aiortc 对象。"""
        elapsed_ms = max(now_ms() - self.created_ts_ms, 1)
        return {
            "peer_id": self.peer_id,
            "source": self.source,
            "created_ts_ms": self.created_ts_ms,
            "connection_state": self.connection_state,
            "ice_connection_state": self.ice_connection_state,
            "signaling_state": self.signaling_state,
            "frames_read": self.frames_read,
            "camera_read_failures": self.camera_read_failures,
            "last_frame_age_ms": now_ms() - self.last_frame_ts_ms if self.last_frame_ts_ms else None,
            "last_frame_width": self.last_frame_width,
            "last_frame_height": self.last_frame_height,
            "last_error": self.last_error,
            "fps_estimate": round(self.frames_read * 1000.0 / elapsed_ms, 3),
            "remote_sdp_candidate_count": self.remote_sdp_candidate_count,
            "local_sdp_candidate_count": self.local_sdp_candidate_count,
            "track_stopped": self.track_stopped,
        }


class CameraServiceState:
    """进程内状态集中管理，便于 HTTP handler 和测试共享同一套逻辑。"""

    def __init__(self, video_source: str, width: int, height: int, fps: int) -> None:
        self.video_source = video_source
        self.width = width
        self.height = height
        self.fps = fps
        self.peers: dict[str, PeerRecord] = {}
        self.last_closed_peer: dict[str, Any] | None = None
        self.last_offer_error: dict[str, Any] | None = None

    def current_devices(self) -> dict[str, Any]:
        """设备接口每次只读刷新，避免缓存掩盖现场 USB 重插。"""
        snapshot = collect_video_candidates()
        selection = resolve_video_source(self.video_source, snapshot)
        return {
            "schema": DEVICES_SCHEMA,
            "app": APP_NAME,
            "status": "loaded",
            "video_source": selection.get("selected_path") or self.video_source,
            "video_source_mode": selection.get("mode"),
            "requested_video_source": self.video_source,
            "source_selection": selection,
            "source_candidates": snapshot,
            "device_probe_readonly": True,
            "writes_controls": False,
            "opens_serial": False,
            "sends_motion_commands": False,
            "generated_at_ms": now_ms(),
            **proof_flags(),
        }

    def health(self) -> dict[str, Any]:
        """health 不打开相机，只读系统和设备摘要，保证轮询安全。"""
        snapshot = collect_video_candidates()
        selection = resolve_video_source(self.video_source, snapshot)
        active_summaries = {peer_id: peer.summary() for peer_id, peer in self.peers.items()}
        active_frames = sum(int(item.get("frames_read") or 0) for item in active_summaries.values())
        active_failures = sum(int(item.get("camera_read_failures") or 0) for item in active_summaries.values())
        selected_path = selection.get("selected_path")
        return {
            "schema": SCHEMA,
            "app": APP_NAME,
            "status": "ready" if selected_path or self.video_source != "auto" else "no_video_source",
            "generated_at_ms": now_ms(),
            "video_source": selected_path or self.video_source,
            "video_source_mode": selection.get("mode"),
            "requested_video_source": self.video_source,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "active_peer_count": len(self.peers),
            "active_peer_connections": len(self.peers),
            "active_frames_read": active_frames,
            "active_camera_read_failures": active_failures,
            "dependencies": import_state(),
            "system_diagnostics": collect_system_diagnostics(),
            "media_diagnostics": {
                "active_peers": active_summaries,
                "last_closed_peer": self.last_closed_peer,
                "last_offer_error": self.last_offer_error,
            },
            "source_summary": source_candidates_summary(snapshot, selection),
            "source_candidates_summary": source_candidates_summary(snapshot, selection),
            "current_selection": {
                "mode": selection.get("mode"),
                "requested_source": selection.get("requested_source"),
                "selected_path": selected_path,
            },
            **proof_flags(),
        }

    async def close_peer(self, peer_id: str, reason: str = "client_requested") -> tuple[int, dict[str, Any]]:
        """释放 peer 时先关 RTCPeerConnection，再停 track/release capture。"""
        if not PEER_ID_PATTERN.match(peer_id):
            return HTTPStatus.BAD_REQUEST, error_payload("peer_id_invalid", "peer_id_must_be_short_alnum")
        peer = self.peers.pop(peer_id, None)
        if peer is None:
            return HTTPStatus.NOT_FOUND, error_payload("peer_not_found", "peer_id_not_active")
        cleanup: dict[str, Any] = {"reason": reason, "pc_closed": False, "track_stopped": False, "capture_released": False}
        try:
            await peer.pc.close()
            cleanup["pc_closed"] = True
        except Exception as exc:  # noqa: BLE001 - cleanup 必须尽力释放其它资源。
            cleanup["pc_close_error"] = compact_error(exc)
        try:
            peer.track.stop()
            cleanup["track_stopped"] = True
        except Exception as exc:  # noqa: BLE001 - track stop 不应阻断 capture release。
            cleanup["track_stop_error"] = compact_error(exc)
        try:
            peer.capture.release()
            cleanup["capture_released"] = True
        except Exception as exc:  # noqa: BLE001 - OpenCV release 在异常路径也要容错。
            cleanup["capture_release_error"] = compact_error(exc)
        peer.track_stopped = True
        self.last_closed_peer = {
            "peer_id": peer_id,
            "closed_ts_ms": now_ms(),
            "cleanup": cleanup,
            "summary": peer.summary(),
        }
        return HTTPStatus.OK, {
            "schema": CLOSE_SCHEMA,
            "app": APP_NAME,
            "status": "closed",
            "peer_id": peer_id,
            "last_closed_peer": self.last_closed_peer,
            "active_peer_count": len(self.peers),
            "active_peer_connections": len(self.peers),
            **proof_flags(),
        }

    async def create_answer(self, offer: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        """WebRTC offer 必须读取真实首帧后才建 answer，不能伪造画面。"""
        valid, reason = validate_offer_payload(offer)
        if not valid:
            payload = error_payload("invalid_offer", reason or "invalid_offer")
            self.last_offer_error = payload
            return HTTPStatus.BAD_REQUEST, payload

        deps = import_state()
        missing = [name for name, available in deps.items() if not available]
        if missing:
            payload = error_payload("dependency_missing", "aiortc_cv2_av_required", missing_dependencies=missing)
            self.last_offer_error = payload
            return HTTPStatus.SERVICE_UNAVAILABLE, payload

        snapshot = collect_video_candidates()
        selection = resolve_video_source(self.video_source, snapshot)
        selected_path = selection.get("selected_path")
        if not selected_path:
            payload = error_payload("video_source_unavailable", "auto_selection_found_no_capture_device", source_selection=selection)
            self.last_offer_error = payload
            return HTTPStatus.SERVICE_UNAVAILABLE, payload

        try:
            return await self._create_answer_with_dependencies(offer, str(selected_path))
        except Exception as exc:  # noqa: BLE001 - 建链失败必须结构化返回并释放中间资源。
            payload = error_payload("offer_failed", "webrtc_answer_creation_failed", detail=compact_error(exc))
            self.last_offer_error = payload
            return HTTPStatus.INTERNAL_SERVER_ERROR, payload

    async def _create_answer_with_dependencies(self, offer: dict[str, Any], source: str) -> tuple[int, dict[str, Any]]:
        """依赖 import 放在热路径，保证无依赖机器仍可 import/py_compile。"""
        import cv2  # type: ignore[import-not-found]
        from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack  # type: ignore[import-not-found]
        from av import VideoFrame  # type: ignore[import-not-found]

        capture = cv2.VideoCapture(source)
        if not capture or not capture.isOpened():
            try:
                capture.release()
            except Exception:  # noqa: BLE001 - release 失败不改变根因。
                pass
            payload = error_payload("camera_open_failed", "opencv_capture_not_opened", video_source=source)
            self.last_offer_error = payload
            return HTTPStatus.SERVICE_UNAVAILABLE, payload

        # 这里仅设置 OpenCV 请求参数；失败时仍以真实首帧读回为准。
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        capture.set(cv2.CAP_PROP_FPS, self.fps)

        first_frame = None
        first_error = None
        deadline = time.monotonic() + FIRST_FRAME_TIMEOUT_S
        while time.monotonic() < deadline:
            ok, frame = capture.read()
            if ok and frame is not None:
                first_frame = frame
                break
            first_error = "capture_read_returned_false"
            await asyncio.sleep(0.05)
        if first_frame is None:
            capture.release()
            payload = error_payload(
                "first_frame_unreadable",
                "first_frame_timeout",
                video_source=source,
                first_frame_timeout_s=FIRST_FRAME_TIMEOUT_S,
                last_read_error=first_error,
            )
            self.last_offer_error = payload
            return HTTPStatus.SERVICE_UNAVAILABLE, payload

        peer_id = uuid.uuid4().hex[:12]
        record_ref: dict[str, PeerRecord] = {}

        class CameraTrack(VideoStreamTrack):  # type: ignore[misc, valid-type]
            """每次 recv 都从真实 capture 读帧，读不到就 fail-closed 结束 track。"""

            def __init__(self, initial_frame: Any) -> None:
                super().__init__()
                self._next_initial_frame = initial_frame

            async def recv(self) -> Any:
                pts, time_base = await self.next_timestamp()
                if self._next_initial_frame is not None:
                    frame = self._next_initial_frame
                    self._next_initial_frame = None
                else:
                    ok, frame = await asyncio.to_thread(capture.read)
                    if not ok or frame is None:
                        record = record_ref.get("record")
                        if record:
                            record.camera_read_failures += 1
                            record.last_error = "capture_read_returned_false"
                        raise RuntimeError("camera frame read failed")
                record = record_ref.get("record")
                if record:
                    record.frames_read += 1
                    record.last_frame_ts_ms = now_ms()
                    record.last_frame_height = int(getattr(frame, "shape", [0, 0])[0])
                    record.last_frame_width = int(getattr(frame, "shape", [0, 0])[1])
                video_frame = VideoFrame.from_ndarray(frame, format="bgr24")
                video_frame.pts = pts
                video_frame.time_base = time_base or Fraction(1, self.fps)
                return video_frame

        pc = RTCPeerConnection()
        track = CameraTrack(first_frame)
        record = PeerRecord(peer_id=peer_id, pc=pc, track=track, capture=capture, source=source)
        record.remote_sdp_candidate_count = str(offer.get("sdp") or "").count("a=candidate")
        record_ref["record"] = record
        try:
            @pc.on("connectionstatechange")
            async def on_connection_state_change() -> None:
                """连接失败时主动清理，避免摄像头被废弃 peer 占用。"""
                record.connection_state = pc.connectionState
                if pc.connectionState in {"failed", "closed"} and peer_id in self.peers:
                    await self.close_peer(peer_id, reason=f"connection_{pc.connectionState}")

            @pc.on("iceconnectionstatechange")
            async def on_ice_connection_state_change() -> None:
                """ICE 状态只做诊断记录，不据此打开任何运动能力。"""
                record.ice_connection_state = pc.iceConnectionState

            @pc.on("signalingstatechange")
            async def on_signaling_state_change() -> None:
                """signaling 状态给 PC 高级诊断判断 SDP 是否走完。"""
                record.signaling_state = pc.signalingState

            pc.addTrack(track)
            await pc.setRemoteDescription(RTCSessionDescription(sdp=offer["sdp"], type=offer["type"]))
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)
            local_sdp = pc.localDescription.sdp
        except Exception:
            # answer 建立失败时还没有进入 peers 表，必须在这里手动释放摄像头。
            try:
                await pc.close()
            finally:
                try:
                    track.stop()
                finally:
                    capture.release()
            raise

        record.local_sdp_candidate_count = local_sdp.count("a=candidate")
        record.connection_state = pc.connectionState
        record.ice_connection_state = pc.iceConnectionState
        record.signaling_state = pc.signalingState
        self.peers[peer_id] = record
        self.last_offer_error = None
        log_event("camera_offer_answer_created", peer_id=peer_id, source=source)
        return HTTPStatus.OK, {
            "schema": OFFER_SCHEMA,
            "app": APP_NAME,
            "status": "answer_created",
            "peer_id": peer_id,
            "type": pc.localDescription.type,
            "sdp": local_sdp,
            "answer": {"type": pc.localDescription.type, "sdp": local_sdp},
            "video_source": source,
            "video_source_mode": "explicit" if self.video_source != "auto" else "auto",
            "remote_sdp_candidate_count": record.remote_sdp_candidate_count,
            "local_sdp_candidate_count": record.local_sdp_candidate_count,
            "active_peer_count": len(self.peers),
            "first_frame_read": True,
            **proof_flags(),
        }


class CameraRequestHandler(BaseHTTPRequestHandler):
    """标准库 HTTP handler，降低上车 smoke 对 aiohttp 的依赖。"""

    server_version = "TrashbotLocalWebRTCCamera/1.0"

    @property
    def state(self) -> CameraServiceState:
        """ThreadingHTTPServer 注入 state，测试和服务共用同一路径。"""
        return self.server.state  # type: ignore[attr-defined]

    def log_message(self, fmt: str, *args: Any) -> None:
        """HTTP access log 也走 JSON，避免混杂不可解析文本。"""
        log_event("http_access", client=self.client_address[0], message=fmt % args)

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        """统一 CORS 和 JSON 序列化，PC 直连和代理两种路径都能读。"""
        body = json.dumps(json_safe(payload), ensure_ascii=False, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type,Accept")
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> Any:
        """坏 JSON 直接返回 sentinel，由调用方结构化 fail-closed。"""
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0:
            return {}
        raw = self.rfile.read(min(length, 2_000_000))
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return {"__invalid_json__": True}

    def do_OPTIONS(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler 固定命名。
        """预检请求不触发任何设备访问。"""
        self._send_json({"schema": SCHEMA, "status": "ok", **proof_flags()})

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler 固定命名。
        """GET endpoint 全部只读，不打开底盘、不发送命令。"""
        if self.path == "/" or self.path == "/health":
            self._send_json(self.state.health())
            return
        if self.path == "/devices":
            self._send_json(self.state.current_devices())
            return
        self._send_json(error_payload("not_found", "unknown_get_endpoint"), status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler 固定命名。
        """POST 仅处理 WebRTC offer 和 peer close，绝不代理运动指令。"""
        body = self._read_json_body()
        if isinstance(body, dict) and body.get("__invalid_json__"):
            self._send_json(error_payload("invalid_json", "request_body_not_json"), status=HTTPStatus.BAD_REQUEST)
            return
        if self.path == "/offer":
            status, payload = asyncio.run(self.state.create_answer(body))
            self._send_json(payload, status=status)
            return
        match = re.fullmatch(r"/peers/([A-Za-z0-9]{1,32})/close", self.path)
        if match:
            status, payload = asyncio.run(self.state.close_peer(match.group(1)))
            self._send_json(payload, status=status)
            return
        self._send_json(error_payload("not_found", "unknown_post_endpoint"), status=HTTPStatus.NOT_FOUND)


class CameraHTTPServer(ThreadingHTTPServer):
    """HTTPServer 扩展一个 state 字段，避免全局变量污染测试。"""

    def __init__(self, server_address: tuple[str, int], state: CameraServiceState) -> None:
        super().__init__(server_address, CameraRequestHandler)
        self.state = state


def build_arg_parser() -> argparse.ArgumentParser:
    """CLI 参数只覆盖媒体服务，不包含任何底盘或串口入口。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--video-source", default=DEFAULT_VIDEO_SOURCE)
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--fps", type=int, default=DEFAULT_FPS)
    return parser


def main(argv: list[str] | None = None) -> int:
    """启动 LAN-only 服务；systemd/手工运行都用同一入口。"""
    args = build_arg_parser().parse_args(argv)
    state = CameraServiceState(
        video_source=args.video_source,
        width=max(1, args.width),
        height=max(1, args.height),
        fps=max(1, args.fps),
    )
    server = CameraHTTPServer((args.host, args.port), state)
    log_event(
        "camera_service_started",
        host=args.host,
        port=args.port,
        video_source=args.video_source,
        width=state.width,
        height=state.height,
        fps=state.fps,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log_event("camera_service_keyboard_interrupt")
    finally:
        for peer_id in list(state.peers):
            asyncio.run(state.close_peer(peer_id, reason="server_shutdown"))
        server.server_close()
        log_event("camera_service_stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
