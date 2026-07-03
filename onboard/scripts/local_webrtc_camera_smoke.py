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
import threading
import time
import uuid
from dataclasses import dataclass, field
from fractions import Fraction
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse


SCHEMA = "trashbot.local_webrtc_camera_smoke.v1"
DEVICES_SCHEMA = "trashbot.local_webrtc_camera_devices.v1"
OFFER_SCHEMA = "trashbot.local_webrtc_camera_offer.v1"
CLOSE_SCHEMA = "trashbot.local_webrtc_camera_close.v1"
MJPEG_BOUNDARY = "roberframe"
APP_NAME = "rober-local-webrtc-camera-smoke"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8088
DEFAULT_VIDEO_SOURCE = "auto"
DEFAULT_WIDTH = 640
DEFAULT_HEIGHT = 480
DEFAULT_FPS = 15
FIRST_FRAME_TIMEOUT_S = 3.0
# 共享 MJPEG 是普通 PC 首屏默认多人预览路径；每次尝试要短，才能在首屏预算内覆盖 native 和低带宽模式。
MJPEG_FIRST_FRAME_TIMEOUT_S = 0.6
# 共享预览只做短路实时入口；完整格式矩阵交给 first-frame probe / USB recovery 诊断。
MJPEG_FIRST_FRAME_TOTAL_TIMEOUT_S = 5.0
# 先横向试关键格式；失败后仅短试 index/V4L2 打开方式，保证 PC 页面及时显示真实失败。
MJPEG_PRIMARY_SOURCE_TOTAL_TIMEOUT_S = 3.8
MJPEG_OPEN_SOURCE_FALLBACK_TOTAL_TIMEOUT_S = 1.2
FIRST_FRAME_WARMUP_INTERVAL_S = 0.05
CAMERA_CAPTURE_FOURCC_FALLBACKS: tuple[str | None, ...] = ("MJPG", "YUYV", None)
COMMAND_TIMEOUT_S = 2.5
STALE_PEER_NO_FRAME_MAX_AGE_MS = 30_000
# 共享 MJPEG/offer 首帧失败后若没有 active peer，残留 capture 会让 v4l2/ffmpeg 探针看到 busy。
STALE_SHARED_CAPTURE_NO_FRAME_MAX_AGE_MS = int((MJPEG_FIRST_FRAME_TOTAL_TIMEOUT_S + 3.0) * 1000)
# 自动 MJPEG 重试不能在已知 UVC 无首帧时持续抢设备；手动 probe 仍可立即复测。
MJPEG_FIRST_FRAME_FAILURE_RETRY_COOLDOWN_MS = 30_000
PEER_ID_PATTERN = re.compile(r"^[A-Za-z0-9]{1,32}$")
API_CAMERA_PREFIX = "/api/camera"
IMPORTS = ("aiortc", "cv2", "av")
# OpenCV 打不开设备也是首帧失败；否则 /health 会把刚失败的共享预览误报成“未探测”。
FIRST_FRAME_FAILURE_REASONS = {
    "first_frame_timeout",
    "first_frame_total_timeout",
    "capture_read_call_timeout",
    "capture_read_returned_false",
    "capture_read_no_result",
    "opencv_capture_not_opened",
}
UVC_KERNEL_ERROR_PATTERNS = (
    "error -71",
    "failed to resubmit video urb",
    "failed to query",
    "device descriptor read",
    "device not accepting address",
    "can't read configurations",
    "failed to initialize the device",
    "device firmware changed",
)
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
# 实现边界说明 095：`status=source_first_frame_failed` 说明有源但最近 offer 证明首帧不可读。
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
# 实现边界说明 126：同一视频源只能由进程打开一次，多个 WebRTC peer 共享该 capture，避免 UVC 独占。
# 实现边界说明 127：卡在 new/0 帧的旧 peer 会在新 offer 前释放，避免浏览器断开后长期占用 `/dev/video1`。
# 实现边界说明 128：共享 capture 的最后一个 peer 关闭时才 release，确保多人预览不会互相踢掉画面。
# 实现边界说明 129：首帧格式尝试必须带分辨率/fps，现场才能判断是不是卡在不兼容采集模式。
# 实现边界说明 130：最后一轮 raw-default 不写任何 capture 属性，用当前内核协商模式兜底。
# 实现边界说明 131：source_diagnosis 只翻译媒体事实，不能自动修复 USB 或改变运动门禁。
# 实现边界说明 132：no-frame 且无人占用时必须明确写“不是独占”，避免现场反复刷新浏览器误判根因。
# 实现边界说明 133：诊断建议只指向 USB/摄像头/供电/known-good UVC，不把相机失败归因到雷达或底盘。


@dataclass(frozen=True)
class CameraCaptureAttemptSpec:
    """首帧尝试规格必须可序列化展示，避免 PC 只看到 MJPG/YUYV 这种粗粒度信息。"""

    fourcc: str | None
    width: int | None
    height: int | None
    fps: int | None
    apply_settings: bool = True

    def label(self) -> str:
        """格式标签直接进入 health/PC UI，所以要短且稳定。"""
        codec = self.fourcc or "default"
        if not self.apply_settings:
            return f"{codec}@current"
        if self.width and self.height and self.fps:
            return f"{codec}@{self.width}x{self.height}@{self.fps}"
        if self.width and self.height:
            return f"{codec}@{self.width}x{self.height}"
        return codec


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


def normalize_camera_service_path(path: str) -> str:
    """同时兼容根路径和 Robot API `/api/camera/*` 路径，避免代理合同漂移。"""
    parsed_path = urlparse(path).path
    if parsed_path == API_CAMERA_PREFIX:
        return "/"
    if parsed_path.startswith(f"{API_CAMERA_PREFIX}/"):
        # 上位机对外暴露 `/api/camera/health`，本服务内部仍复用历史 `/health` 处理。
        suffix = parsed_path[len(API_CAMERA_PREFIX):] or "/"
        return suffix
    return parsed_path


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


def parse_v4l2_bus_info(candidate: dict[str, Any] | None) -> str:
    """从 v4l2 只读输出里提取 USB bus，便于把 dmesg 错误限定到当前摄像头。"""
    probe = (candidate or {}).get("readonly_probe")
    v4l2_all = probe.get("v4l2_all") if isinstance(probe, dict) else {}
    stdout = str(v4l2_all.get("stdout") or "") if isinstance(v4l2_all, dict) else ""
    match = re.search(r"Bus info\s*:\s*(\S+)", stdout)
    return match.group(1) if match else ""


def sysfs_usb_device_for_video(video_device: str | None) -> str | None:
    """从当前 video 节点反查 USB kernel 地址，避免旧端口 UVC 日志误归因。"""
    if not video_device:
        return None
    device_link = Path("/sys/class/video4linux") / Path(video_device).name / "device"
    try:
        resolved = device_link.resolve(strict=True)
    except OSError:
        return None
    for part in reversed(resolved.parts):
        # `3-1:1.0` 是接口目录，真正用于 dmesg/lsusb 对齐的是父 USB 设备 `3-1`。
        interface_match = re.fullmatch(r"(\d+-[\d.]+):\d+\.\d+", part)
        if interface_match:
            return interface_match.group(1)
        if re.fullmatch(r"\d+-[\d.]+", part):
            return part
    return None


def line_matches_usb_device(line: str, usb_device: str | None) -> bool:
    """判断 dmesg 行是否属于当前 USB 设备；接口后缀也算同一设备。"""
    if not usb_device:
        return False
    lower = line.lower()
    return (
        f"usb {usb_device}" in lower
        or f"uvcvideo {usb_device}" in lower
        or any(match.group(1) == usb_device for match in re.finditer(r"(?:uvcvideo|usb)\s+([0-9]+-[0-9][0-9.\-]*)", lower))
    )


def dmesg_line_seconds(line: str) -> float | None:
    """提取 dmesg 单调时间；同一个 USB 地址重用时要靠时间切开旧错误。"""
    match = re.match(r"\[\s*([0-9]+(?:\.[0-9]+)?)\]", line)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def is_usb_enumeration_line(line: str) -> bool:
    """这些行代表设备重新枚举完成；它们之前的同地址错误不能再算当前根因。"""
    lower = line.lower()
    return any(
        token in lower
        for token in (
            "new high-speed usb device",
            "new full-speed usb device",
            "new usb device found",
            "found uvc",
            "authorized to connect",
        )
    )


def collect_uvc_kernel_diagnostics(selected_path: str | None, selected_candidate: dict[str, Any] | None) -> dict[str, Any]:
    """只读 dmesg 中的 UVC/USB 错误；它解释无首帧根因，不会打开摄像头。"""
    bus_info = parse_v4l2_bus_info(selected_candidate)
    current_usb_device = sysfs_usb_device_for_video(selected_path)
    selected_name = str((selected_candidate or {}).get("v4l2_name") or (selected_candidate or {}).get("sysfs_name") or selected_path or "camera")
    if shutil.which("dmesg") is None:
        return {
            "status": "kernel_log_unavailable",
            "plain_hint": "未能读取内核 UVC 日志；继续按相机无首帧排查 USB、输入和供电。",
            "selected_path": selected_path or "",
            "selected_name": selected_name,
            "bus_info": bus_info,
            "current_usb_device": current_usb_device or "",
            "opens_camera": False,
            **proof_flags(),
        }
    try:
        completed = subprocess.run(["dmesg"], check=False, capture_output=True, text=True, timeout=1.5)
        dmesg_text = completed.stdout
    except (OSError, subprocess.TimeoutExpired):
        dmesg_text = ""
    if not dmesg_text:
        return {
            "status": "kernel_log_unavailable",
            "plain_hint": "未能读取内核 UVC 日志；继续按相机无首帧排查 USB、输入和供电。",
            "selected_path": selected_path or "",
            "selected_name": selected_name,
            "bus_info": bus_info,
            "current_usb_device": current_usb_device or "",
            "opens_camera": False,
            **proof_flags(),
        }

    lines = dmesg_text.splitlines()
    bus_tokens = [token for token in [bus_info, bus_info.replace("usb-", ""), "uvcvideo"] if token]
    fallback_kernel_usb_addresses: set[str] = set()
    if not current_usb_device:
        for line in lines:
            # 没有 sysfs 当前地址时保留旧兼容：先从 UVC 行学习 kernel 地址，再吸收同地址 USB 错误。
            lower = line.lower()
            if "uvc" not in lower:
                continue
            for match in re.finditer(r"(?:uvcvideo|usb)\s+([0-9]+-[0-9][0-9.\-]*)", lower):
                fallback_kernel_usb_addresses.add(match.group(1))

    matched_lines: list[str] = []
    error_lines: list[str] = []
    stale_error_lines: list[str] = []
    latest_current_enumeration_s: float | None = None
    if current_usb_device:
        for line in lines:
            if line_matches_usb_device(line, current_usb_device) and is_usb_enumeration_line(line):
                line_s = dmesg_line_seconds(line)
                if line_s is not None and (latest_current_enumeration_s is None or line_s > latest_current_enumeration_s):
                    latest_current_enumeration_s = line_s
    for line in lines:
        lower = line.lower()
        # 有当前 sysfs 地址时只把同一 USB 设备的日志算作当前根因；旧端口错误只作为残留证据。
        related = line_matches_usb_device(lower, current_usb_device) if current_usb_device else (
            any(token.lower() in lower for token in bus_tokens)
            or "uvc" in lower
            or any(f"usb {address}" in lower or f"uvcvideo {address}" in lower for address in fallback_kernel_usb_addresses)
        )
        compact_line = line[-360:]
        is_transport_error = any(pattern in lower for pattern in UVC_KERNEL_ERROR_PATTERNS)
        if related:
            matched_lines.append(compact_line)
            if is_transport_error:
                line_s = dmesg_line_seconds(line)
                if (
                    current_usb_device
                    and latest_current_enumeration_s is not None
                    and line_s is not None
                    and line_s < latest_current_enumeration_s
                ):
                    stale_error_lines.append(compact_line)
                else:
                    error_lines.append(compact_line)
        elif current_usb_device and is_transport_error and ("uvc" in lower or re.search(r"\b(?:usb|uvcvideo)\s+[0-9]+-[0-9]", lower)):
            stale_error_lines.append(compact_line)

    if error_lines:
        status = "uvc_usb_transport_errors_observed"
        plain_hint = f"{selected_name} 的内核日志出现 UVC/USB 传输错误；优先检查 USB 线、接口、供电或换 known-good UVC。"
        next_action = "check_usb_cable_port_power_or_known_good_uvc"
    elif current_usb_device and stale_error_lines:
        status = "uvc_kernel_seen_without_current_transport_errors"
        plain_hint = f"{selected_name} 当前 USB 设备 {current_usb_device} 未匹配到新的 UVC 传输错误；旧端口残留错误不再当作当前独占或传输根因。"
        next_action = "continue_first_frame_format_diagnostics"
    elif matched_lines:
        status = "uvc_kernel_seen_without_recent_transport_errors"
        plain_hint = f"{selected_name} 已在内核日志中出现，但最近未匹配到明确 UVC 传输错误；继续按无首帧和格式尝试排查。"
        next_action = "continue_first_frame_format_diagnostics"
    else:
        status = "uvc_kernel_log_not_matched"
        plain_hint = f"内核日志未匹配到 {selected_name} 的 UVC 记录；检查设备枚举和 USB 连接。"
        next_action = "check_camera_device_enumeration"

    return {
        "status": status,
        "plain_hint": plain_hint,
        "next_action": next_action,
        "selected_path": selected_path or "",
        "selected_name": selected_name,
        "bus_info": bus_info,
        "current_usb_device": current_usb_device or "",
        "latest_current_enumeration_s": latest_current_enumeration_s,
        "matched_line_count": len(matched_lines),
        "transport_error_count": len(error_lines),
        "latest_transport_error": error_lines[-1] if error_lines else "",
        "stale_transport_error_count": len(stale_error_lines),
        "latest_stale_transport_error": stale_error_lines[-1] if stale_error_lines else "",
        "tail": error_lines[-8:] if error_lines else matched_lines[-8:],
        "opens_camera": False,
        **proof_flags(),
    }


def collect_uvc_usb_topology_diagnostics(selected_path: str | None, selected_candidate: dict[str, Any] | None) -> dict[str, Any]:
    """只读 USB 拓扑，识别 UVC 是否掉到 12M full-speed；这会直接导致视频流无法稳定出帧。"""
    bus_info = parse_v4l2_bus_info(selected_candidate)
    current_usb_device = sysfs_usb_device_for_video(selected_path)
    selected_name = str((selected_candidate or {}).get("v4l2_name") or (selected_candidate or {}).get("sysfs_name") or selected_path or "camera")
    if shutil.which("lsusb") is None:
        return {
            "status": "usb_topology_unavailable",
            "plain_hint": "未安装 lsusb，无法读取 USB 速率；继续按相机无首帧排查 USB 线、接口和供电。",
            "selected_path": selected_path or "",
            "selected_name": selected_name,
            "bus_info": bus_info,
            "current_usb_device": current_usb_device or "",
            "opens_camera": False,
            **proof_flags(),
        }
    try:
        completed = subprocess.run(["lsusb", "-t"], check=False, capture_output=True, text=True, timeout=1.5)
        topology_text = completed.stdout
    except (OSError, subprocess.TimeoutExpired):
        topology_text = ""
    if not topology_text:
        return {
            "status": "usb_topology_unavailable",
            "plain_hint": "未能读取 USB 拓扑；继续按相机无首帧排查 USB 线、接口和供电。",
            "selected_path": selected_path or "",
            "selected_name": selected_name,
            "bus_info": bus_info,
            "current_usb_device": current_usb_device or "",
            "opens_camera": False,
            **proof_flags(),
        }

    current_bus = ""
    video_entries: list[dict[str, str]] = []
    for raw_line in topology_text.splitlines():
        bus_match = re.search(r"Bus\s+(\d+)", raw_line)
        if raw_line.startswith("/:") and bus_match:
            current_bus = bus_match.group(1).lstrip("0") or "0"
        if "Class=Video" not in raw_line:
            continue
        port_match = re.search(r"Port\s+(\d+):", raw_line)
        dev_match = re.search(r"Dev\s+(\d+)", raw_line)
        speed_match = re.search(r",\s*([0-9]+[MGK])\s*$", raw_line.strip())
        video_entries.append(
            {
                "bus": current_bus,
                "port": port_match.group(1) if port_match else "",
                "dev": dev_match.group(1) if dev_match else "",
                "speed": speed_match.group(1) if speed_match else "unknown",
                "kernel_usb_address": f"{current_bus}-{port_match.group(1)}" if current_bus and port_match else "",
                "line": raw_line.strip()[-260:],
            }
        )

    full_speed_entries = [entry for entry in video_entries if entry.get("speed") in {"1.5M", "12M"}]
    sysfs_matched_entries = [entry for entry in video_entries if current_usb_device and entry.get("kernel_usb_address") == current_usb_device]
    selected_entry = sysfs_matched_entries[0] if sysfs_matched_entries else (full_speed_entries[0] if full_speed_entries else (video_entries[0] if video_entries else {}))
    speed = selected_entry.get("speed") or "not_loaded"
    kernel_usb_address = selected_entry.get("kernel_usb_address") or "not_loaded"
    selected_full_speed = speed in {"1.5M", "12M"}
    if selected_full_speed:
        status = "uvc_video_on_full_speed_usb"
        plain_hint = f"{selected_name} 当前在 USB {speed} full-speed 拓扑上，视频流容易 STREAMON I/O error；换高速 USB 口/线、减少转接并确认供电后复测。"
        next_action = "move_camera_to_high_speed_usb_port_or_powered_hub"
    elif video_entries:
        status = "uvc_video_usb_speed_loaded"
        plain_hint = f"{selected_name} USB 视频拓扑已读到，当前速率 {speed}；若仍无首帧，继续看 UVC/USB 错误和格式尝试。"
        next_action = "continue_first_frame_format_diagnostics"
    else:
        status = "uvc_video_usb_topology_not_matched"
        plain_hint = f"USB 拓扑未匹配到 {selected_name} 的 Video 接口；检查摄像头枚举、线缆和接口。"
        next_action = "check_camera_usb_enumeration"

    return {
        "status": status,
        "plain_hint": plain_hint,
        "next_action": next_action,
        "selected_path": selected_path or "",
        "selected_name": selected_name,
        "bus_info": bus_info,
        "current_usb_device": current_usb_device or "",
        "video_usb_speed": speed,
        "kernel_usb_address": kernel_usb_address,
        "selected_by_sysfs_usb_device": bool(sysfs_matched_entries),
        "high_speed_observed": speed not in {"1.5M", "12M", "not_loaded", "unknown"},
        "video_interface_count": len(video_entries),
        "video_interfaces": video_entries[:6],
        "topology_tail": topology_text[-1600:],
        "opens_camera": False,
        **proof_flags(),
    }


def _read_proc_text(path: Path, limit: int = 240) -> str:
    """procfs 文本只用于诊断展示；读不到时返回空串而不是影响 health。"""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return text.replace("\x00", " ").strip()[:limit]


def collect_device_usage(path: str | None) -> dict[str, Any]:
    """扫描 /proc/fd 判断视频源是否被占用；该诊断不会打开摄像头。"""
    if not path:
        return {"checked": False, "reason": "no_selected_source", "opens_camera": False}
    if not os.path.exists(path):
        return {"checked": True, "device": path, "status": "source_missing", "owner_count": 0, "owners": [], "opens_camera": False}
    try:
        target_realpath = os.path.realpath(path)
    except OSError:
        target_realpath = path

    owners: list[dict[str, Any]] = []
    scan_errors = 0
    current_pid = os.getpid()
    for proc_dir in sorted(Path("/proc").glob("[0-9]*"), key=lambda item: item.name):
        pid_text = proc_dir.name
        fd_dir = proc_dir / "fd"
        try:
            fd_paths = list(fd_dir.iterdir())
        except OSError:
            scan_errors += 1
            continue
        matched_fds: list[str] = []
        for fd_path in fd_paths:
            try:
                link_target = os.readlink(fd_path)
            except OSError:
                continue
            try:
                same_device = os.path.realpath(link_target) == target_realpath
            except OSError:
                same_device = link_target == path
            if same_device or link_target == path:
                matched_fds.append(fd_path.name)
        if not matched_fds:
            continue
        command = _read_proc_text(proc_dir / "cmdline") or _read_proc_text(proc_dir / "comm")
        owners.append(
            {
                "pid": int(pid_text),
                "self": int(pid_text) == current_pid,
                "fds": matched_fds[:8],
                "command": command[:180],
            }
        )

    other_owners = [owner for owner in owners if not owner.get("self")]
    probe_owners = [
        owner
        for owner in other_owners
        if any(token in str(owner.get("command") or "") for token in ("camera_first_frame_probe", "v4l2-ctl", "ffmpeg"))
    ]
    if probe_owners:
        status = "in_use_by_probe"
    elif other_owners:
        status = "in_use_by_other_process"
    elif owners:
        status = "in_use_by_camera_service"
    else:
        status = "not_in_use"
    return {
        "checked": True,
        "device": path,
        "realpath": target_realpath,
        "status": status,
        "owner_count": len(owners),
        "other_owner_count": len(other_owners),
        "owners": owners[:8],
        "scan_error_count": scan_errors,
        "opens_camera": False,
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
    all_stdout = str(all_result.get("stdout") or "") if all_result.get("available") else ""
    formats_stdout = str(formats_result.get("stdout") or "") if formats_result.get("available") else ""
    combined_text = "\n".join(text_parts)
    lower_text = combined_text.lower()
    formats_lower = formats_stdout.lower()
    # UVC 复合设备的全局 Capabilities 可能同时包含 Metadata Capture；真正要看
    # 当前节点是否暴露图像帧格式。`/dev/video1` 有 Format Video Capture/MJPG/YUYV，
    # `/dev/video2` 只有 Format Metadata Capture，不能简单按 metadata 字样一刀切。
    has_frame_format = (
        "format video capture" in lower_text
        or "'mjpg'" in formats_lower
        or "'yuyv'" in formats_lower
        or "motion-jpeg" in formats_lower
    )
    is_metadata_only = "format metadata capture" in lower_text and not has_frame_format
    return {
        "path": path,
        "exists": os.path.exists(path),
        "realpath": os.path.realpath(path) if os.path.exists(path) else None,
        "v4l2_name": v4l2_name,
        "sysfs_name": sysfs_name,
        "capability_text_available": bool(all_result.get("available")),
        "formats_text_available": bool(formats_result.get("available")),
        "is_video_capture": "video capture" in lower_text and has_frame_format,
        "is_metadata": is_metadata_only,
        "is_decoder": "cedrus" in lower_text or "decoder" in lower_text or "mem2mem" in lower_text,
        "is_uvc_or_usb": "uvc" in lower_text or "usb" in lower_text,
        "readonly_probe": {
            "v4l2_all": all_result,
            "v4l2_formats": formats_result,
        },
        "formats_summary": summarize_v4l2_formats(formats_stdout),
    }


def summarize_v4l2_formats(formats_stdout: str) -> str:
    """把 v4l2 格式长文本压成一行，PC 普通诊断只需要知道可试哪些模式。"""
    if not formats_stdout.strip():
        return "not_loaded"
    entries: list[str] = []
    current_fourcc = ""
    current_size = ""
    for raw_line in formats_stdout.splitlines():
        line = raw_line.strip()
        fourcc_match = re.search(r"'([A-Z0-9]{4})'", line)
        if fourcc_match and line.startswith("["):
            current_fourcc = fourcc_match.group(1)
            current_size = ""
            continue
        size_match = re.search(r"Size:\s+Discrete\s+(\d+x\d+)", line)
        if size_match:
            current_size = size_match.group(1)
            continue
        fps_match = re.search(r"\((\d+(?:\.\d+)?)\s+fps\)", line)
        if current_fourcc and current_size and fps_match:
            fps_text = fps_match.group(1).rstrip("0").rstrip(".")
            entry = f"{current_fourcc}@{current_size}@{fps_text}"
            if entry not in entries:
                entries.append(entry)
    return "；".join(entries[:8]) if entries else "not_loaded"


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
                "formats_summary": candidate.get("formats_summary"),
            }
        )
    selected_path = selection.get("selected_path")
    selected_candidate = next((candidate for candidate in candidates if candidate.get("path") == selected_path), None)
    selected_siblings = sibling_video_nodes_summary(candidates, selected_path)
    return {
        "candidate_count": len(candidates),
        "candidates": candidates,
        "current_selection": {
            "mode": selection.get("mode"),
            "requested_source": selection.get("requested_source"),
            "selected_path": selected_path,
            "selected_name": selected_candidate.get("name") if selected_candidate else None,
            "selected_is_uvc_or_usb": selected_candidate.get("is_uvc_or_usb") if selected_candidate else None,
            "selected_formats_summary": selected_candidate.get("formats_summary") if selected_candidate else None,
            "selected_role": candidate_role(selected_candidate) if selected_candidate else "unknown",
            "selected_sibling_video_nodes": selected_siblings,
            "selected_sibling_video_node_count": len(selected_siblings),
            "selected_sibling_video_nodes_summary": sibling_video_nodes_text(selected_siblings),
            "ranked": selection.get("ranked", [])[:8],
        },
        "shared_preview_contract": "single_shared_capture_for_multiple_clients",
    }


def candidate_role(candidate: dict[str, Any] | None) -> str:
    """把 V4L2 节点身份压成普通诊断可读的短枚举。"""
    if not candidate:
        return "unknown"
    if candidate.get("is_video_capture"):
        return "video_capture"
    if candidate.get("is_metadata"):
        return "metadata"
    if candidate.get("is_decoder"):
        return "decoder"
    return "other"


def candidate_group_name(candidate: dict[str, Any] | None) -> str:
    """同一 USB 复合设备通常共享 v4l2_name；用它识别 video1/video2 兄弟节点。"""
    if not candidate:
        return ""
    return str(candidate.get("name") or candidate.get("v4l2_name") or candidate.get("sysfs_name") or "").strip()


def sibling_video_nodes_summary(candidates: list[dict[str, Any]], selected_path: Any) -> list[dict[str, Any]]:
    """列出同一设备下的其它 /dev/video* 节点，避免把 metadata 节点误当备用画面。"""
    selected = next((candidate for candidate in candidates if candidate.get("path") == selected_path), None)
    selected_group = candidate_group_name(selected)
    if not selected_path or not selected_group:
        return []
    siblings = []
    for candidate in candidates:
        if candidate.get("path") == selected_path or candidate_group_name(candidate) != selected_group:
            continue
        siblings.append(
            {
                "path": candidate.get("path"),
                "role": candidate_role(candidate),
                "is_video_capture": candidate.get("is_video_capture"),
                "is_metadata": candidate.get("is_metadata"),
                "formats_summary": candidate.get("formats_summary"),
            }
        )
    return siblings


def sibling_video_nodes_text(siblings: list[dict[str, Any]]) -> str:
    """PC summary 只需要一行事实：例如 `/dev/video2=metadata`。"""
    parts = []
    for item in siblings:
        path = str(item.get("path") or "").strip()
        role = str(item.get("role") or "unknown").strip()
        if path:
            parts.append(f"{path}={role}")
    return "；".join(parts) if parts else "none"


def build_source_diagnosis(
    selected_path: str | None,
    source_failed: bool,
    source_observed: bool,
    source_usage: dict[str, Any],
    selected_candidate: dict[str, Any] | None,
    last_offer_reason: str,
    uvc_kernel_diagnostics: dict[str, Any] | None = None,
    uvc_usb_topology: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """把 health 的工程事实压成稳定归因，PC 普通界面不用猜是不是浏览器独占。"""
    usage_status = str(source_usage.get("status") or "not_loaded")
    owner_count = int(source_usage.get("owner_count") or 0) if str(source_usage.get("owner_count") or "").isdigit() else 0
    other_owner_count = int(source_usage.get("other_owner_count") or 0) if str(source_usage.get("other_owner_count") or "").isdigit() else 0
    selected_name = str((selected_candidate or {}).get("v4l2_name") or (selected_candidate or {}).get("sysfs_name") or selected_path or "camera")
    selected_is_uvc = bool((selected_candidate or {}).get("is_uvc_or_usb"))
    kernel_status = str((uvc_kernel_diagnostics or {}).get("status") or "")
    kernel_transport_error = kernel_status == "uvc_usb_transport_errors_observed"
    usb_topology_status = str((uvc_usb_topology or {}).get("status") or "")
    usb_full_speed = usb_topology_status == "uvc_video_on_full_speed_usb"
    usb_speed = str((uvc_usb_topology or {}).get("video_usb_speed") or "12M")
    not_exclusive = usage_status in {"not_in_use", "in_use_by_camera_service"} or other_owner_count <= 0
    if not selected_path:
        status = "no_video_source"
        plain_hint = "没有选中可用摄像头源；检查 USB 摄像头枚举。"
        next_action = "check_camera_device_enumeration"
    elif source_observed:
        status = "first_frame_observed"
        plain_hint = f"{selected_name} 已读到真实首帧，可继续看实时预览。"
        next_action = "open_shared_preview"
    elif usage_status in {"in_use_by_probe", "in_use_by_other_process"}:
        status = "source_busy"
        plain_hint = f"{selected_name} 当前被其他进程占用；释放占用或重启相机服务后再打开画面。"
        next_action = "release_camera_owner_or_restart_camera_service"
    elif source_failed and not_exclusive and selected_is_uvc and usb_full_speed:
        status = "uvc_full_speed_usb_not_exclusive"
        plain_hint = f"不是页面独占：{selected_name} 当前无人占用，但摄像头挂在 USB {usb_speed} full-speed，视频流会 STREAMON I/O error；换高速 USB 口/线、减少转接并确认供电后复测。"
        next_action = "move_camera_to_high_speed_usb_port_or_powered_hub"
    elif source_failed and not_exclusive and selected_is_uvc and kernel_transport_error:
        status = "uvc_transport_error_not_exclusive"
        plain_hint = f"不是页面独占：{selected_name} 当前无人占用，但内核日志已有 UVC/USB 传输错误；检查 USB 线、接口、摄像头供电或换 known-good UVC 复测。"
        next_action = "check_usb_cable_port_power_or_known_good_uvc"
    elif source_failed and not_exclusive and selected_is_uvc:
        status = "uvc_no_frame_not_exclusive"
        plain_hint = f"不是页面独占：{selected_name} 当前没人占用，但 UVC 设备没有输出视频帧；检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测。"
        next_action = "check_usb_camera_input_power_or_known_good_uvc"
    elif source_failed and not_exclusive:
        status = "source_no_frame_not_exclusive"
        plain_hint = f"不是页面独占：{selected_name} 当前没人占用，但摄像头没有输出视频帧；检查输入源和供电。"
        next_action = "check_camera_input_or_power"
    elif source_failed:
        status = "source_first_frame_failed"
        plain_hint = f"{selected_name} 没有输出首帧；先看占用和格式尝试，再检查 USB/供电。"
        next_action = "inspect_usage_and_format_attempts"
    else:
        status = "source_selected_not_probed"
        plain_hint = f"{selected_name} 已选中但还没读过首帧；打开共享预览或运行首帧检查。"
        next_action = "open_shared_preview_or_run_first_frame_probe"
    return {
        "status": status,
        "plain_hint": plain_hint,
        "next_action": next_action,
        "not_exclusive": bool(not_exclusive),
        "selected_is_uvc_or_usb": selected_is_uvc,
        "selected_name": selected_name,
        "source_usage_status": usage_status,
        "source_usage_owner_count": owner_count,
        "source_failure_reason": last_offer_reason or "none",
        "uvc_kernel_diagnostics_status": kernel_status or "not_loaded",
        "uvc_usb_topology_status": usb_topology_status or "not_loaded",
        "uvc_usb_topology_video_usb_speed": usb_speed if usb_topology_status else "not_loaded",
        "shared_preview_contract": "single_shared_capture_for_multiple_clients",
        "opens_camera": False,
        **proof_flags(),
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


def encode_mjpeg_part(cv2: Any, frame: Any) -> bytes | None:
    """MJPEG fallback 只包装真实 OpenCV 帧；编码失败时不返回伪图片。"""
    ok, encoded = cv2.imencode(".jpg", frame)
    if not ok or encoded is None:
        return None
    jpeg = encoded.tobytes() if hasattr(encoded, "tobytes") else bytes(encoded)
    return (
        f"--{MJPEG_BOUNDARY}\r\n"
        "Content-Type: image/jpeg\r\n"
        "Cache-Control: no-store\r\n"
        f"Content-Length: {len(jpeg)}\r\n\r\n"
    ).encode("ascii") + jpeg + b"\r\n"


def camera_capture_attempt_specs(width: int, height: int, fps: int) -> list[CameraCaptureAttemptSpec]:
    """优先试配置值，再试 DV20/UVC 常见离散模式，最后保留内核当前模式兜底。"""
    raw_specs = [
        CameraCaptureAttemptSpec("MJPG", width, height, fps),
        # DV20/UVC 实板枚举显示 MJPG 是 30fps；先贴合真实离散模式，再让 OpenCV 自行协商。
        CameraCaptureAttemptSpec("MJPG", width, height, 30),
        CameraCaptureAttemptSpec("MJPG", 1280, 720, 30),
        CameraCaptureAttemptSpec("MJPG", 480, 320, 30),
        CameraCaptureAttemptSpec("YUYV", width, height, fps),
        # YUYV 640x480 是 22fps，320x240 同时有 25/20fps，不能只拿默认 15fps 试。
        CameraCaptureAttemptSpec("YUYV", width, height, 22),
        CameraCaptureAttemptSpec("YUYV", 320, 240, 25),
        CameraCaptureAttemptSpec("YUYV", 320, 240, 20),
        # 有些 UVC 在嵌入式 USB 链路上只愿意先吐极小帧；把 160x120 留作软件兜底。
        CameraCaptureAttemptSpec("MJPG", 160, 120, 30),
        # 低带宽 YUYV 对劣质 USB 线/供电更宽容；失败时会明确进入 attempts 供 PC 展示。
        CameraCaptureAttemptSpec("YUYV", 160, 120, 20),
        CameraCaptureAttemptSpec(None, None, None, None, apply_settings=False),
    ]
    specs: list[CameraCaptureAttemptSpec] = []
    seen: set[tuple[str | None, int | None, int | None, int | None, bool]] = set()
    for spec in raw_specs:
        key = (spec.fourcc, spec.width, spec.height, spec.fps, spec.apply_settings)
        if key in seen:
            continue
        seen.add(key)
        specs.append(spec)
    return specs


def mjpeg_camera_capture_attempt_specs(width: int, height: int, fps: int) -> list[CameraCaptureAttemptSpec]:
    """共享 MJPEG 首屏预算短，必须先横跨 native/MJPG/YUYV，而不是被单一路径吃完。"""
    priority_specs = [
        # 现场 DV20 枚举没有 15fps MJPG；共享首屏先试真实离散 30fps，避免把 3 秒预算花在不支持组合上。
        CameraCaptureAttemptSpec("MJPG", width, height, 30),
        # 当前 DV20 内核协商常落在 1280x720；把 native 高清模式放进短预算，避免只试小帧误判无画面。
        CameraCaptureAttemptSpec("MJPG", 1280, 720, 30),
        # 首屏预览宁可先降分辨率出画面；低带宽模式更容易绕开 USB/带宽/格式协商问题。
        CameraCaptureAttemptSpec("MJPG", 480, 320, 30),
        # 真实 DV20 枚举里 320x240 YUYV 是 25/20fps；早试小帧 YUYV 可以验证“不是只卡 MJPG”。
        CameraCaptureAttemptSpec("YUYV", 320, 240, 25),
        # 现场最需要“先出画面”，160x120 比完整清晰度更适合短预算探活。
        CameraCaptureAttemptSpec("MJPG", 160, 120, 30),
        # 继续降到 160x120，给 Jieli/DV20 这类挑 USB 链路的设备最后一个软件机会。
        CameraCaptureAttemptSpec("YUYV", 160, 120, 20),
        # 640x480 YUYV 仍保留在 default 前，方便现场判断是不是只有低分辨率可读。
        CameraCaptureAttemptSpec("YUYV", width, height, 22),
        # 不写 V4L2 属性的原生模式可绕过部分驱动对 set(fourcc/fps) 的异常协商。
        CameraCaptureAttemptSpec(None, None, None, None, apply_settings=False),
        # 配置值保留为后续兜底，兼容现场换成支持 15fps 的 UVC。
        CameraCaptureAttemptSpec("MJPG", width, height, fps),
    ]
    ordered: list[CameraCaptureAttemptSpec] = []
    seen: set[tuple[str | None, int | None, int | None, int | None, bool]] = set()
    for spec in priority_specs + camera_capture_attempt_specs(width, height, fps):
        key = (spec.fourcc, spec.width, spec.height, spec.fps, spec.apply_settings)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(spec)
    return ordered


def apply_camera_capture_settings(cv2: Any, capture: Any, width: int | None, height: int | None, fps: int | None, fourcc: str | None) -> None:
    """请求 UVC 采集格式；set 失败不算成功或失败，首帧 read 才是最终事实。"""
    if fourcc:
        capture.set(getattr(cv2, "CAP_PROP_FOURCC", 6), cv2.VideoWriter_fourcc(*fourcc))
    if width:
        capture.set(getattr(cv2, "CAP_PROP_FRAME_WIDTH", 3), width)
    if height:
        capture.set(getattr(cv2, "CAP_PROP_FRAME_HEIGHT", 4), height)
    if fps:
        capture.set(getattr(cv2, "CAP_PROP_FPS", 5), fps)


def opencv_capture_source_candidates(source: str) -> list[str | int]:
    """OpenCV 在部分板端对 `/dev/videoN` 和数字索引的打开行为不同，两个都试但仍只读取真实帧。"""
    candidates: list[str | int] = [source]
    match = re.fullmatch(r"/dev/video(\d+)", source)
    if match:
        candidates.append(int(match.group(1)))
    return candidates


def opencv_capture_open_candidates(cv2: Any, source: str, include_backend_fallbacks: bool = False) -> list[dict[str, Any]]:
    """生成 OpenCV 打开方式；MJPEG 首屏可显式试 V4L2 backend，避免 path 能 open 但 read 永远 false。"""
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    backend_options: list[tuple[str, int | None]] = [("default", None)]
    cap_v4l2 = getattr(cv2, "CAP_V4L2", None)
    if include_backend_fallbacks and cap_v4l2 is not None:
        backend_options.append(("CAP_V4L2", int(cap_v4l2)))
    for open_source in opencv_capture_source_candidates(source):
        source_label = opencv_capture_source_label(open_source)
        for backend_label, backend_id in backend_options:
            key = (source_label, backend_label)
            if key in seen:
                continue
            seen.add(key)
            candidates.append({"source": open_source, "source_label": source_label, "backend": backend_id, "backend_label": backend_label})
    return candidates


def opencv_capture_source_label(source: str | int) -> str:
    """诊断里保留打开方式，现场可区分 path 与 index fallback。"""
    return f"index:{source}" if isinstance(source, int) else str(source)


@dataclass
class SharedCameraCapture:
    """同一摄像头源的共享 OpenCV capture，避免多客户端重复独占打开设备。"""

    source: str
    capture: Any
    width: int
    height: int
    fps: int
    fourcc: str | None = None
    open_source: str | int | None = None
    open_backend: str = "default"
    created_ts_ms: int = field(default_factory=now_ms)
    ref_count: int = 0
    frames_read: int = 0
    read_failures: int = 0
    last_frame_ts_ms: int | None = None
    last_error: str | None = None
    released: bool = False
    lock: threading.Lock = field(default_factory=threading.Lock)

    def add_ref(self) -> None:
        """peer 创建成功前先占用引用，失败路径必须对应 release_ref。"""
        self.ref_count += 1

    def read_frame(self) -> tuple[bool, Any]:
        """串行化读取同一个 capture；每个 peer 收到真实连续帧，不复制假帧。"""
        with self.lock:
            if self.released:
                self.read_failures += 1
                self.last_error = "shared_capture_released"
                return False, None
            ok, frame = self.capture.read()
            if ok and frame is not None:
                self.frames_read += 1
                self.last_frame_ts_ms = now_ms()
                self.last_error = None
                return True, frame
            self.read_failures += 1
            self.last_error = "capture_read_returned_false"
            return False, None

    def read_frame_with_timeout(self, timeout_s: float) -> tuple[bool, Any]:
        """V4L2 卡死时按服务超时返回，避免 PC 页面长期停在等待画面。"""
        result: list[tuple[bool, Any]] = []

        def read_once() -> None:
            # OpenCV 的 read 可能在内核 select 中卡住；放到 daemon 线程便于主流程按时 fail-closed。
            result.append(self.read_frame())

        thread = threading.Thread(target=read_once, daemon=True)
        thread.start()
        thread.join(max(0.1, timeout_s))
        if thread.is_alive():
            self.read_failures += 1
            self.last_error = "capture_read_call_timeout"
            self.force_release()
            return False, None
        if not result:
            self.read_failures += 1
            self.last_error = "capture_read_no_result"
            return False, None
        return result[0]

    def read_frame_until_success(self, timeout_s: float) -> tuple[bool, Any, int]:
        """首帧允许短 warmup 重试；有些 UVC 刚打开会先返回几次 false。"""
        deadline = time.monotonic() + max(0.1, timeout_s)
        attempts = 0
        while time.monotonic() < deadline:
            attempts += 1
            remaining = max(0.05, deadline - time.monotonic())
            # 首帧 read 自身可能慢于普通帧；用剩余总预算，避免过早释放 UVC 句柄。
            ok, frame = self.read_frame_with_timeout(remaining)
            if ok and frame is not None:
                return True, frame, attempts
            if self.released:
                return False, None, attempts
            time.sleep(min(FIRST_FRAME_WARMUP_INTERVAL_S, max(0.0, deadline - time.monotonic())))
        if not self.last_error:
            self.last_error = "first_frame_warmup_timeout"
        return False, None, attempts

    def release_ref(self) -> bool:
        """最后一个 peer 退出时释放底层设备句柄。"""
        self.ref_count = max(self.ref_count - 1, 0)
        if self.ref_count > 0 or self.released:
            return False
        try:
            self.capture.release()
        finally:
            self.released = True
        return True

    def force_release(self) -> bool:
        """服务关闭或异常清理时强制释放底层 capture。"""
        if self.released:
            return False
        try:
            self.capture.release()
        finally:
            self.ref_count = 0
            self.released = True
        return True

    def summary(self) -> dict[str, Any]:
        """共享 capture 摘要只用于媒体诊断，不参与控制 gate。"""
        return {
            "source": self.source,
            "open_source": opencv_capture_source_label(self.open_source if self.open_source is not None else self.source),
            "open_backend": self.open_backend,
            "fourcc": self.fourcc or "default",
            "created_ts_ms": self.created_ts_ms,
            "ref_count": self.ref_count,
            "frames_read": self.frames_read,
            "read_failures": self.read_failures,
            "last_frame_age_ms": now_ms() - self.last_frame_ts_ms if self.last_frame_ts_ms else None,
            "last_error": self.last_error,
            "released": self.released,
        }


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
        self.shared_captures: dict[str, SharedCameraCapture] = {}
        self.last_closed_peer: dict[str, Any] | None = None
        self.last_offer_error: dict[str, Any] | None = None
        self.last_successful_frame: dict[str, Any] | None = None

    def mark_successful_frame(self, source: str, frame: Any, channel: str) -> None:
        """只有真实读取到帧才更新 readiness，避免设备路径存在被误当成画面 ready。"""
        shape = getattr(frame, "shape", None)
        height = int(shape[0]) if isinstance(shape, tuple) and len(shape) >= 2 else None
        width = int(shape[1]) if isinstance(shape, tuple) and len(shape) >= 2 else None
        self.last_successful_frame = {
            "source": source,
            "channel": channel,
            "observed_at_ms": now_ms(),
            "width": width,
            "height": height,
        }

    def _stale_peer_ids(self) -> list[str]:
        """找出卡在协商初期且从未读到帧的旧 peer，避免它长期占用 UVC。"""
        stale_ids: list[str] = []
        current_ms = now_ms()
        for peer_id, peer in self.peers.items():
            age_ms = current_ms - peer.created_ts_ms
            connection_state = str(peer.connection_state or "new")
            ice_state = str(peer.ice_connection_state or "new")
            no_frame = peer.frames_read <= 0 and peer.last_frame_ts_ms is None
            still_new = connection_state in {"new", "connecting"} or ice_state in {"new", "checking"}
            if no_frame and still_new and age_ms >= STALE_PEER_NO_FRAME_MAX_AGE_MS:
                stale_ids.append(peer_id)
        return stale_ids

    async def close_stale_peers(self) -> list[dict[str, Any]]:
        """新 offer 前回收陈旧 peer；失败也要继续尝试新建链路。"""
        closed: list[dict[str, Any]] = []
        for peer_id in self._stale_peer_ids():
            status, payload = await self.close_peer(peer_id, reason="stale_no_frame_peer_replaced")
            closed.append({"peer_id": peer_id, "http_status": int(status), "status": payload.get("status")})
        return closed

    def acquire_shared_capture(
        self,
        source: str,
        cv2: Any,
        fourcc: str | None = None,
        width: int | None = None,
        height: int | None = None,
        fps: int | None = None,
        apply_settings: bool = True,
        open_source_override: str | int | None = None,
        open_backend: int | None = None,
        open_backend_label: str = "default",
    ) -> tuple[SharedCameraCapture | None, dict[str, Any] | None]:
        """获取共享摄像头句柄；已有句柄可复用，避免第二个客户端再次打开 `/dev/video1`。"""
        cache_key = source if open_source_override is None and open_backend is None else f"{source}|{opencv_capture_source_label(open_source_override if open_source_override is not None else source)}|{open_backend_label}"
        shared = self.shared_captures.get(cache_key)
        if shared and not shared.released:
            shared.add_ref()
            return shared, None

        open_attempts: list[dict[str, Any]] = []
        capture = None
        opened_source: str | int | None = None
        open_candidates = (
            [{"source": open_source_override, "source_label": opencv_capture_source_label(open_source_override), "backend": open_backend, "backend_label": open_backend_label}]
            if open_source_override is not None
            else opencv_capture_open_candidates(cv2, source)
        )
        for candidate in open_candidates:
            candidate_source = candidate["source"]
            backend_id = candidate.get("backend")
            backend_label = str(candidate.get("backend_label") or "default")
            try:
                capture = cv2.VideoCapture(candidate_source, backend_id) if backend_id is not None else cv2.VideoCapture(candidate_source)
            except TypeError:
                # 部分测试 fake 或旧 OpenCV 只接受单参数；退回默认打开方式，并把事实写入诊断。
                capture = cv2.VideoCapture(candidate_source)
                backend_label = f"{backend_label}_fallback_single_arg"
            opened = bool(capture and capture.isOpened())
            open_attempts.append({"source": opencv_capture_source_label(candidate_source), "backend": backend_label, "opened": opened})
            if opened:
                opened_source = candidate_source
                open_backend_label = backend_label
                break
            try:
                if capture:
                    capture.release()
            except Exception:  # noqa: BLE001 - release 失败不改变打开失败根因。
                pass
            capture = None
        if not capture or opened_source is None:
            payload = error_payload("camera_open_failed", "opencv_capture_not_opened", video_source=source)
            payload["opencv_open_attempts"] = open_attempts
            return None, payload
        if apply_settings:
            apply_camera_capture_settings(cv2, capture, width or self.width, height or self.height, fps or self.fps, fourcc)
        shared = SharedCameraCapture(
            source=source,
            capture=capture,
            width=width or self.width,
            height=height or self.height,
            fps=fps or self.fps,
            fourcc=fourcc,
            open_source=opened_source,
            open_backend=open_backend_label,
        )
        shared.add_ref()
        self.shared_captures[cache_key] = shared
        return shared, None

    def remove_shared_capture(self, shared_capture: SharedCameraCapture) -> None:
        """按对象清理共享句柄；打开方式 fallback 后 cache key 不一定等于原始设备路径。"""
        for key, value in list(self.shared_captures.items()):
            if value is shared_capture:
                self.shared_captures.pop(key, None)

    def cleanup_stale_shared_captures(self, reason: str = "health_no_active_peer_cleanup") -> list[dict[str, Any]]:
        """无人观看且首帧从未成功的共享句柄必须回收，避免 8088 自己长期占用 UVC。"""
        released: list[dict[str, Any]] = []
        if self.peers:
            return released
        current_ms = now_ms()
        for key, shared in list(self.shared_captures.items()):
            summary = shared.summary()
            age_ms = current_ms - int(summary.get("created_ts_ms") or current_ms)
            no_frame = int(summary.get("frames_read") or 0) <= 0 and summary.get("last_frame_age_ms") is None
            # ref_count 残留可能来自已断开的 MJPEG 请求；超过首帧总预算后按 stale 处理。
            stale = no_frame and age_ms >= STALE_SHARED_CAPTURE_NO_FRAME_MAX_AGE_MS
            dangling = int(summary.get("ref_count") or 0) <= 0
            if not (stale or dangling):
                continue
            force_released = shared.force_release()
            self.shared_captures.pop(key, None)
            released.append({
                "key": key,
                "reason": reason,
                "age_ms": age_ms,
                "stale_no_frame": stale,
                "dangling_ref": dangling,
                "force_released": force_released,
                "summary": summary,
            })
        return released

    def recent_first_frame_failure(self, source: str, cooldown_ms: int = MJPEG_FIRST_FRAME_FAILURE_RETRY_COOLDOWN_MS) -> dict[str, Any] | None:
        """自动预览刚失败时短暂冷却，避免浏览器重试循环持续占用 UVC。"""
        error = self.last_offer_error if isinstance(self.last_offer_error, dict) else {}
        if not error or error.get("video_source") != source:
            return None
        reason = str(error.get("failure_reason") or "")
        if reason not in FIRST_FRAME_FAILURE_REASONS:
            return None
        generated_at_ms = int(error.get("generated_at_ms") or 0)
        if generated_at_ms <= 0:
            return None
        age_ms = max(0, now_ms() - generated_at_ms)
        if age_ms >= cooldown_ms:
            return None
        return {
            "cooldown_active": True,
            "cooldown_ms": cooldown_ms,
            "age_ms": age_ms,
            "retry_after_ms": max(0, cooldown_ms - age_ms),
            "failure_reason": reason,
            "last_error": error,
        }

    def acquire_first_frame_capture(
        self,
        source: str,
        cv2: Any,
        timeout_s: float = FIRST_FRAME_TIMEOUT_S,
        total_timeout_s: float | None = None,
        specs: list[CameraCaptureAttemptSpec] | None = None,
        include_open_source_fallbacks: bool = False,
        open_source_fallbacks_only: bool = False,
    ) -> tuple[SharedCameraCapture | None, Any, list[dict[str, Any]], dict[str, Any] | None]:
        """按多组 UVC 常见模式尝试首帧；每次失败都释放，不能长期占用坏格式。"""
        attempts: list[dict[str, Any]] = []
        last_payload: dict[str, Any] | None = None
        started = time.monotonic()
        # 调用方可为短预算共享预览传入更激进的顺序；默认 WebRTC 仍保留完整矩阵。
        for spec in specs or camera_capture_attempt_specs(self.width, self.height, self.fps):
            open_candidates = (
                opencv_capture_open_candidates(cv2, source, include_backend_fallbacks=True)
                if include_open_source_fallbacks
                else [{"source": source, "source_label": opencv_capture_source_label(source), "backend": None, "backend_label": "default"}]
            )
            if open_source_fallbacks_only:
                # 第二阶段只试真正不同的打开方式，避免把短预算浪费在刚失败的 path/default 上。
                default_source_label = opencv_capture_source_label(source)
                open_candidates = [
                    item for item in open_candidates
                    if not (
                        str(item.get("source_label") or "") == default_source_label
                        and str(item.get("backend_label") or "default") == "default"
                    )
                ]
            if not open_candidates:
                open_candidates = [{"source": source, "source_label": opencv_capture_source_label(source), "backend": None, "backend_label": "default"}]
            for open_candidate in open_candidates:
                remaining_total = None if total_timeout_s is None else total_timeout_s - (time.monotonic() - started)
                if remaining_total is not None and remaining_total <= 0:
                    last_payload = error_payload(
                        "first_frame_unreadable",
                        "first_frame_total_timeout",
                        video_source=source,
                        first_frame_timeout_s=timeout_s,
                        first_frame_total_timeout_s=total_timeout_s,
                        first_frame_elapsed_s=round(time.monotonic() - started, 3),
                        first_frame_format_attempts=attempts,
                        last_read_error=(last_payload or {}).get("last_read_error", "first_frame_total_timeout"),
                    )
                    break
                shared_capture, open_error = self.acquire_shared_capture(
                    source,
                    cv2,
                    spec.fourcc,
                    width=spec.width,
                    height=spec.height,
                    fps=spec.fps,
                    apply_settings=spec.apply_settings,
                    open_source_override=open_candidate["source"],
                    open_backend=open_candidate.get("backend"),
                    open_backend_label=str(open_candidate.get("backend_label") or "default"),
                )
                label = spec.label()
                open_source_label = str(open_candidate.get("source_label") or opencv_capture_source_label(open_candidate["source"]))
                open_backend_label = str(open_candidate.get("backend_label") or "default")
                if shared_capture is None:
                    attempts.append({
                        "fourcc": spec.fourcc or "default",
                        "label": label,
                        "width": spec.width,
                        "height": spec.height,
                        "fps": spec.fps,
                        "apply_settings": spec.apply_settings,
                        "open_source": open_source_label,
                        "open_backend": open_backend_label,
                        "status": "open_failed",
                        "failure_reason": open_error.get("failure_reason") if open_error else "opencv_capture_not_opened",
                    })
                    last_payload = open_error or error_payload("camera_open_failed", "opencv_capture_not_opened", video_source=source)
                    continue
                attempt_timeout = timeout_s if remaining_total is None else max(0.1, min(timeout_s, remaining_total))
                ok, frame, first_frame_attempts = shared_capture.read_frame_until_success(attempt_timeout)
                if ok and frame is not None:
                    attempts.append({
                        "fourcc": spec.fourcc or "default",
                        "label": label,
                        "width": spec.width,
                        "height": spec.height,
                        "fps": spec.fps,
                        "apply_settings": spec.apply_settings,
                        "open_source": shared_capture.summary()["open_source"],
                        "open_backend": shared_capture.summary()["open_backend"],
                        "status": "frame_read",
                        "attempts": first_frame_attempts,
                    })
                    return shared_capture, frame, attempts, None
                first_error = shared_capture.last_error or "capture_read_returned_false"
                attempts.append({
                    "fourcc": spec.fourcc or "default",
                    "label": label,
                    "width": spec.width,
                    "height": spec.height,
                    "fps": spec.fps,
                    "apply_settings": spec.apply_settings,
                    "open_source": shared_capture.summary()["open_source"],
                    "open_backend": shared_capture.summary()["open_backend"],
                    "status": "first_frame_unreadable",
                    "attempts": first_frame_attempts,
                    "failure_reason": first_error,
                })
                if shared_capture.release_ref() or shared_capture.released:
                    self.remove_shared_capture(shared_capture)
                last_payload = error_payload(
                    "first_frame_unreadable",
                    first_error or "first_frame_timeout",
                    video_source=source,
                    first_frame_timeout_s=timeout_s,
                    first_frame_total_timeout_s=total_timeout_s,
                    first_frame_elapsed_s=round(time.monotonic() - started, 3),
                    first_frame_attempts=first_frame_attempts,
                    first_frame_format_attempts=attempts,
                    selected_fourcc=label,
                    last_read_error=first_error,
                )
            if last_payload and last_payload.get("failure_reason") == "first_frame_total_timeout":
                break
        if last_payload is None:
            last_payload = error_payload("first_frame_unreadable", "no_capture_format_attempted", video_source=source)
        last_payload["first_frame_format_attempts"] = attempts
        return None, None, attempts, last_payload

    def acquire_mjpeg_first_frame_capture(
        self,
        source: str,
        cv2: Any,
    ) -> tuple[SharedCameraCapture | None, Any, list[dict[str, Any]], dict[str, Any] | None]:
        """MJPEG 默认预览先试低带宽格式，再试 index/V4L2 fallback，保持首屏预算可控。"""
        specs = mjpeg_camera_capture_attempt_specs(self.width, self.height, self.fps)
        shared_capture, first_frame, attempts, error = self.acquire_first_frame_capture(
            source,
            cv2,
            timeout_s=MJPEG_FIRST_FRAME_TIMEOUT_S,
            total_timeout_s=MJPEG_PRIMARY_SOURCE_TOTAL_TIMEOUT_S,
            specs=specs,
            include_open_source_fallbacks=False,
        )
        if shared_capture is not None and first_frame is not None:
            return shared_capture, first_frame, attempts, None

        fallback_shared, fallback_frame, fallback_attempts, fallback_error = self.acquire_first_frame_capture(
            source,
            cv2,
            timeout_s=min(MJPEG_FIRST_FRAME_TIMEOUT_S, MJPEG_OPEN_SOURCE_FALLBACK_TOTAL_TIMEOUT_S),
            total_timeout_s=MJPEG_OPEN_SOURCE_FALLBACK_TOTAL_TIMEOUT_S,
            specs=specs,
            include_open_source_fallbacks=True,
            open_source_fallbacks_only=True,
        )
        combined_attempts = attempts + fallback_attempts
        if fallback_shared is not None and fallback_frame is not None:
            return fallback_shared, fallback_frame, combined_attempts, None

        payload = fallback_error or error or error_payload(
            "first_frame_unreadable",
            "first_frame_format_attempts_failed",
            video_source=source,
        )
        payload["first_frame_format_attempts"] = combined_attempts
        if error:
            payload["primary_source_failure_reason"] = error.get("failure_reason")
        if fallback_error:
            payload["open_source_fallback_failure_reason"] = fallback_error.get("failure_reason")
        payload["mjpeg_open_source_fallback_attempted"] = True
        return None, None, combined_attempts, payload

    def release_peer_capture(self, peer: PeerRecord) -> dict[str, Any]:
        """释放 peer 持有的 capture 引用；兼容测试里的 FakeCapture。"""
        shared = peer.capture
        cleanup: dict[str, Any] = {"capture_released": False, "shared_capture_ref_released": False}
        try:
            if hasattr(shared, "release_ref"):
                cleanup["shared_capture_ref_released"] = True
                cleanup["capture_released"] = bool(shared.release_ref())
                if getattr(shared, "released", False):
                    self.remove_shared_capture(shared)
            else:
                shared.release()
                cleanup["capture_released"] = True
        except Exception as exc:  # noqa: BLE001 - capture release 失败不能阻断 close 响应。
            cleanup["capture_release_error"] = compact_error(exc)
        return cleanup

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
        stale_shared_captures_released = self.cleanup_stale_shared_captures()
        snapshot = collect_video_candidates()
        selection = resolve_video_source(self.video_source, snapshot)
        active_summaries = {peer_id: peer.summary() for peer_id, peer in self.peers.items()}
        active_frames = sum(int(item.get("frames_read") or 0) for item in active_summaries.values())
        active_failures = sum(int(item.get("camera_read_failures") or 0) for item in active_summaries.values())
        selected_path = selection.get("selected_path")
        last_offer_error = self.last_offer_error if isinstance(self.last_offer_error, dict) else {}
        last_offer_source = last_offer_error.get("video_source")
        last_offer_reason = str(last_offer_error.get("failure_reason") or "")
        source_failed = bool(
            selected_path
            and last_offer_source == selected_path
            and last_offer_reason in FIRST_FRAME_FAILURE_REASONS
        )
        last_success = self.last_successful_frame if isinstance(self.last_successful_frame, dict) else {}
        # 当前首帧失败必须压过历史成功帧；否则 PC 会同时看到“失败”和“已观察”的矛盾材料。
        source_observed = bool(
            selected_path
            and not source_failed
            and last_success.get("source") == selected_path
        )
        source_readiness = (
            "first_frame_failed"
            if source_failed
            else "first_frame_observed" if source_observed else ("source_selected_not_probed" if selected_path else "no_video_source")
        )
        source_usage = collect_device_usage(str(selected_path) if selected_path else None)
        selected_candidate = selection.get("selected") if isinstance(selection.get("selected"), dict) else None
        uvc_kernel_diagnostics = collect_uvc_kernel_diagnostics(
            str(selected_path) if selected_path else None,
            selected_candidate,
        )
        uvc_usb_topology = collect_uvc_usb_topology_diagnostics(
            str(selected_path) if selected_path else None,
            selected_candidate,
        )
        source_diagnosis = build_source_diagnosis(
            str(selected_path) if selected_path else None,
            source_failed,
            source_observed,
            source_usage,
            selected_candidate,
            last_offer_reason,
            uvc_kernel_diagnostics,
            uvc_usb_topology,
        )
        source_summary = source_candidates_summary(snapshot, selection)
        source_summary_selection = source_summary.get("current_selection", {})
        health_status = (
            "source_first_frame_failed"
            if source_failed
            else "ready" if source_observed else ("source_not_probed" if selected_path or self.video_source != "auto" else "no_video_source")
        )
        return {
            "schema": SCHEMA,
            "app": APP_NAME,
            "status": health_status,
            "generated_at_ms": now_ms(),
            "video_source": selected_path or self.video_source,
            "video_source_mode": selection.get("mode"),
            "requested_video_source": self.video_source,
            "source_readiness": source_readiness,
            "source_failure_reason": last_offer_reason if source_failed else "",
            "last_first_frame_error": self.last_offer_error,
            "last_first_frame_format_attempts": (
                last_offer_error.get("first_frame_format_attempts")
                if isinstance(last_offer_error.get("first_frame_format_attempts"), list)
                else []
            ),
            "last_successful_frame": self.last_successful_frame,
            "source_usage": source_usage,
            "uvc_kernel_diagnostics": uvc_kernel_diagnostics,
            "uvc_usb_topology": uvc_usb_topology,
            "source_diagnosis": source_diagnosis,
            "shared_preview_contract": "single_shared_capture_for_multiple_clients",
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
                "shared_captures": {source: shared.summary() for source, shared in self.shared_captures.items()},
                "stale_shared_captures_released": stale_shared_captures_released,
                "last_closed_peer": self.last_closed_peer,
                "last_offer_error": self.last_offer_error,
                "last_successful_frame": self.last_successful_frame,
                "source_usage": source_usage,
                "uvc_kernel_diagnostics": uvc_kernel_diagnostics,
                "uvc_usb_topology": uvc_usb_topology,
                "source_diagnosis": source_diagnosis,
                "shared_preview_contract": "single_shared_capture_for_multiple_clients",
            },
            "source_summary": source_summary,
            "source_candidates_summary": source_summary,
            "stale_shared_captures_released": stale_shared_captures_released,
            "current_selection": {
                "mode": selection.get("mode"),
                "requested_source": selection.get("requested_source"),
                "selected_path": selected_path,
                "selected_name": source_summary_selection.get("selected_name"),
                "selected_is_uvc_or_usb": source_summary_selection.get("selected_is_uvc_or_usb"),
                "selected_formats_summary": source_summary_selection.get("selected_formats_summary"),
                "selected_role": source_summary_selection.get("selected_role"),
                "selected_sibling_video_nodes": source_summary_selection.get("selected_sibling_video_nodes"),
                "selected_sibling_video_node_count": source_summary_selection.get("selected_sibling_video_node_count"),
                "selected_sibling_video_nodes_summary": source_summary_selection.get("selected_sibling_video_nodes_summary"),
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
        cleanup.update(self.release_peer_capture(peer))
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
        stale_closed = await self.close_stale_peers()
        valid, reason = validate_offer_payload(offer)
        if not valid:
            payload = error_payload("invalid_offer", reason or "invalid_offer")
            if stale_closed:
                payload["stale_peers_closed"] = stale_closed
            self.last_offer_error = payload
            return HTTPStatus.BAD_REQUEST, payload

        deps = import_state()
        missing = [name for name, available in deps.items() if not available]
        if missing:
            payload = error_payload("dependency_missing", "aiortc_cv2_av_required", missing_dependencies=missing)
            if stale_closed:
                payload["stale_peers_closed"] = stale_closed
            self.last_offer_error = payload
            return HTTPStatus.SERVICE_UNAVAILABLE, payload

        snapshot = collect_video_candidates()
        selection = resolve_video_source(self.video_source, snapshot)
        selected_path = selection.get("selected_path")
        if not selected_path:
            payload = error_payload("video_source_unavailable", "auto_selection_found_no_capture_device", source_selection=selection)
            if stale_closed:
                payload["stale_peers_closed"] = stale_closed
            self.last_offer_error = payload
            return HTTPStatus.SERVICE_UNAVAILABLE, payload

        try:
            status, payload = await self._create_answer_with_dependencies(offer, str(selected_path))
            if stale_closed:
                payload["stale_peers_closed"] = stale_closed
            return status, payload
        except Exception as exc:  # noqa: BLE001 - 建链失败必须结构化返回并释放中间资源。
            payload = error_payload("offer_failed", "webrtc_answer_creation_failed", detail=compact_error(exc))
            if stale_closed:
                payload["stale_peers_closed"] = stale_closed
            self.last_offer_error = payload
            return HTTPStatus.INTERNAL_SERVER_ERROR, payload

    async def _create_answer_with_dependencies(self, offer: dict[str, Any], source: str) -> tuple[int, dict[str, Any]]:
        """依赖 import 放在热路径，保证无依赖机器仍可 import/py_compile。"""
        import cv2  # type: ignore[import-not-found]
        from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack  # type: ignore[import-not-found]
        from av import VideoFrame  # type: ignore[import-not-found]

        shared_capture, first_frame, format_attempts, first_frame_error = await asyncio.to_thread(
            self.acquire_first_frame_capture,
            source,
            cv2,
        )
        if shared_capture is None or first_frame is None:
            payload = first_frame_error or error_payload(
                "first_frame_unreadable",
                "first_frame_format_attempts_failed",
                video_source=source,
                first_frame_timeout_s=FIRST_FRAME_TIMEOUT_S,
                first_frame_format_attempts=format_attempts,
            )
            self.last_offer_error = payload
            return HTTPStatus.SERVICE_UNAVAILABLE, payload
        self.mark_successful_frame(source, first_frame, "webrtc_offer")

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
                    ok, frame = await asyncio.to_thread(shared_capture.read_frame)
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
        record = PeerRecord(peer_id=peer_id, pc=pc, track=track, capture=shared_capture, source=source)
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
                    if shared_capture.release_ref() or shared_capture.released:
                        self.remove_shared_capture(shared_capture)
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
            "shared_capture_count": len(self.shared_captures),
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
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            # 客户端可能在首帧失败前断开，服务只记录短事件，不把栈追踪留给现场排障。
            log_event("json_response_client_disconnected", status=status, path=normalize_camera_service_path(self.path))

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
        parsed_path = normalize_camera_service_path(self.path)
        if parsed_path == "/" or parsed_path == "/health":
            self._send_json(self.state.health())
            return
        if parsed_path == "/devices":
            self._send_json(self.state.current_devices())
            return
        if parsed_path in {"/mjpeg", "/stream.mjpg"}:
            self._send_mjpeg_stream()
            return
        self._send_json(error_payload("not_found", "unknown_get_endpoint"), status=HTTPStatus.NOT_FOUND)

    def _send_mjpeg_stream(self) -> None:
        """MJPEG 兜底预览复用共享 capture，避免 WebRTC ICE 卡住时用户看不到实时画面。"""
        deps = import_state()
        if not deps.get("cv2"):
            self._send_json(error_payload("dependency_missing", "cv2_required_for_mjpeg"), status=HTTPStatus.SERVICE_UNAVAILABLE)
            return
        import cv2  # type: ignore[import-not-found]

        snapshot = collect_video_candidates()
        selection = resolve_video_source(self.state.video_source, snapshot)
        selected_path = selection.get("selected_path")
        if not selected_path:
            self._send_json(error_payload("video_source_unavailable", "auto_selection_found_no_capture_device"), status=HTTPStatus.SERVICE_UNAVAILABLE)
            return
        recent_failure = self.state.recent_first_frame_failure(str(selected_path))
        if recent_failure:
            payload = error_payload(
                "first_frame_recent_failure_cooldown",
                "mjpeg_auto_retry_cooldown_after_first_frame_failure",
                video_source=str(selected_path),
                retry_after_ms=recent_failure["retry_after_ms"],
                cooldown_ms=recent_failure["cooldown_ms"],
                last_first_frame_failure_reason=recent_failure["failure_reason"],
                opens_camera=False,
                automatic_retry_suppressed=True,
            )
            payload["last_first_frame_error"] = recent_failure["last_error"]
            self._send_json(payload, status=HTTPStatus.SERVICE_UNAVAILABLE)
            return
        shared_capture, first_frame, format_attempts, first_frame_error = self.state.acquire_mjpeg_first_frame_capture(
            str(selected_path),
            cv2,
        )
        if shared_capture is None or first_frame is None:
            payload = first_frame_error or error_payload(
                "first_frame_unreadable",
                "first_frame_format_attempts_failed",
                video_source=str(selected_path),
                first_frame_timeout_s=MJPEG_FIRST_FRAME_TIMEOUT_S,
                first_frame_total_timeout_s=MJPEG_FIRST_FRAME_TOTAL_TIMEOUT_S,
                first_frame_format_attempts=format_attempts,
            )
            self.state.last_offer_error = payload
            self._send_json(payload, status=HTTPStatus.SERVICE_UNAVAILABLE)
            return
        self.state.mark_successful_frame(str(selected_path), first_frame, "mjpeg")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"multipart/x-mixed-replace; boundary={MJPEG_BOUNDARY}")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.end_headers()
        try:
            part = encode_mjpeg_part(cv2, first_frame)
            if part is None:
                return
            self.wfile.write(part)
            self.wfile.flush()
            while True:
                ok, frame = shared_capture.read_frame_with_timeout(FIRST_FRAME_TIMEOUT_S)
                if not ok or frame is None:
                    break
                part = encode_mjpeg_part(cv2, frame)
                if part is None:
                    break
                self.wfile.write(part)
                self.wfile.flush()
                time.sleep(max(0.03, 1.0 / max(1, self.state.fps)))
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            if shared_capture.release_ref() or shared_capture.released:
                self.state.remove_shared_capture(shared_capture)

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler 固定命名。
        """POST 仅处理 WebRTC offer 和 peer close，绝不代理运动指令。"""
        body = self._read_json_body()
        if isinstance(body, dict) and body.get("__invalid_json__"):
            self._send_json(error_payload("invalid_json", "request_body_not_json"), status=HTTPStatus.BAD_REQUEST)
            return
        parsed_path = normalize_camera_service_path(self.path)
        if parsed_path == "/offer":
            status, payload = asyncio.run(self.state.create_answer(body))
            self._send_json(payload, status=status)
            return
        match = re.fullmatch(r"/peers/([A-Za-z0-9]{1,32})/close", parsed_path)
        if match:
            status, payload = asyncio.run(self.state.close_peer(match.group(1)))
            self._send_json(payload, status=status)
            return
        self._send_json(error_payload("not_found", "unknown_post_endpoint"), status=HTTPStatus.NOT_FOUND)


class CameraHTTPServer(ThreadingHTTPServer):
    """HTTPServer 扩展一个 state 字段，避免全局变量污染测试。"""

    allow_reuse_address = True

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
