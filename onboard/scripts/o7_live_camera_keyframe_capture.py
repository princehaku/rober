#!/usr/bin/env python3
"""只读发现 ROS Image publisher，并最多捕获一帧为 sprint-local PNG。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import signal
import struct
import subprocess
import sys
import tempfile
import time
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable


# 设计注释：本 helper 的唯一 live 目标是读取一条现存 Image 消息。
# 设计注释：helper 不负责启动 camera publisher，也不负责修复 camera runtime。
# 设计注释：helper 不使用历史 fixture 替代本轮 live publisher 或 live frame。
# 设计注释：inventory 与 capture 是两个显式阶段，便于独立核对 invocation count。
# 设计注释：inventory 只允许一个 SSH shell，避免重复消费现场状态。
# 设计注释：capture 只允许一个 SSH shell，timeout 或坏帧后也不重试。
# 设计注释：两个阶段都设置 ROS2CLI_NO_DAEMON，避免 CLI 启动后台 daemon。
# 设计注释：daemon pre/post 使用进程 pid 集合比较，而不是解析易漂移文案。
# 设计注释：daemon drift 一旦出现即阻断 capture，不能把污染图谱当 clean gate。
# 设计注释：inventory 同时验证 rclpy 和 sensor_msgs Image 可导入。
# 设计注释：topic list 与 topic info 都有硬 timeout，不无限等待 DDS 图谱。
# 设计注释：inventory 仅保留 Image 候选，不把整个 ROS graph 写进 artifact。
# 设计注释：artifact 不保留 SSH target，避免暴露真实板地址。
# 设计注释：artifact 不保留 stderr，避免路径、用户名或命令行泄漏。
# 设计注释：canonical topic 存在且 clean 时优先，不受其他候选影响。
# 设计注释：canonical topic 存在但类型错误时 fail closed，不旁路切换。
# 设计注释：canonical topic 存在但 publisher 为零时 fail closed，不猜 runtime。
# 设计注释：canonical 缺席时只允许唯一兼容的 Image publisher。
# 设计注释：多个兼容候选视为来源歧义，不能按名称相似度选择。
# 设计注释：topic 名在进入 SSH 参数前必须通过严格 ROS 名称白名单。
# 设计注释：publisher count 只证明 endpoint，不能外推可见内容或稳定帧率。
# 设计注释：message type 必须精确为 sensor_msgs/msg/Image。
# 设计注释：publisher count 大于等于一即可通过，不擅自要求唯一 publisher node。
# 设计注释：inventory clean 仍保持 capture count 为零，不能提前声称 keyframe。
# 设计注释：capture 订阅 sensor-data QoS，以兼容常见可靠或尽力发布者。
# 设计注释：capture callback 只接受第一帧，后续消息不会覆盖首帧 lineage。
# 设计注释：capture 内部订阅窗口最多十二秒，超时自然 fail closed。
# 设计注释：本地外层只为 SSH 建连和远端退出保留少量收尾预算。
# 设计注释：外层 timeout 只终止 helper 自己创建的进程组。
# 设计注释：helper 禁止 pkill、killall 或按进程名做 broad kill。
# 设计注释：远端脚本不写文件，避免现场留下 raw frame 或临时 artifact。
# 设计注释：远端脚本不启动 launch、service、lifecycle 或 camera 程序。
# 设计注释：远端脚本不发布 topic、不调用 action、不发送 service write。
# 设计注释：远端脚本不触碰 initialpose、cmd_vel、base manual 或 UART。
# 设计注释：远端只通过私有 stdout pipe 返回首帧 metadata 和 bytes。
# 设计注释：stdout pipe 始终由父进程捕获，绝不转发到终端日志。
# 设计注释：pipe 使用固定 magic 和 metadata length，避免二进制边界歧义。
# 设计注释：pipe raw_size 必须与实际剩余 bytes 精确一致。
# 设计注释：截断、追加或错误 prefix 都不能进入 PNG 编码。
# 设计注释：capture 发生异常后 invocation count 固定为一。
# 设计注释：capture gate 未通过时不创建 SSH 子进程，count 固定为零。
# 设计注释：失败分支没有循环，也没有第二 transport 调用。
# 设计注释：失败原因只保留稳定类别，不保存 traceback 或自由文本。
# 设计注释：原始像素只在进程内存短暂停留并转换为 canonical PNG。
# 设计注释：唯一允许落盘的二进制文件名固定为 keyframe.png。
# 设计注释：JSON 中禁止 bytes、bytearray 和 memoryview。
# 设计注释：JSON 中禁止 data、pixels、raw_bytes 等像素键。
# 设计注释：JSON 中禁止 base64 和 data URL，防止绕过二进制边界。
# 设计注释：JSON 中禁止绝对用户路径、远端地址和 HTTP URL。
# 设计注释：topic 以斜杠开头是 ROS 名称，不按绝对文件路径处理。
# 设计注释：redaction boundary 明确 raw pixels 不进入 manifest。
# 设计注释：redaction boundary 明确 API 和 UI 不内联 binary。
# 设计注释：redaction boundary 明确 UI 本轮只能显示 metadata。
# 设计注释：privacy review 保持 pending，annotation-ready 不等于隐私批准。
# 设计注释：visible content 保持 not proven，不从一帧结构完整性外推内容质量。
# 设计注释：设备型号、设备路径和实际分辨率均由本轮证据决定，不读默认值猜测。
# 设计注释：manifest 只记录 topic、stamp、尺寸、encoding 和媒体摘要。
# 设计注释：manifest 的 media_basename 不包含目录或绝对路径。
# 设计注释：manifest 的 media_byte_size 必须等于最终 PNG 字节数。
# 设计注释：manifest 的 sha256 必须由最终 PNG 重新计算。
# 设计注释：manifest 的 captured_at_utc 只在成功捕获后填写。
# 设计注释：blocked manifest 同样包含全部冻结字段，避免下游补默认值。
# 设计注释：blocked manifest 的媒体名、大小和 hash 都保持空或零。
# 设计注释：blocked manifest 的 annotation_ready 必须为 false。
# 设计注释：live manifest 的 annotation_ready 只表示 lineage 可稳定消费。
# 设计注释：live manifest 必须同时满足 inventory count 一和 capture count 一。
# 设计注释：fixture 合同不能进入 live manifest 成功分支。
# 设计注释：task id 在整个 Epic 内固定，确保 O6/O7 same-task 对齐。
# 设计注释：三层 lineage 使用 task、hash、topic、stamp、尺寸和 encoding。
# 设计注释：stamp 纳秒必须位于 ROS 合法范围内。
# 设计注释：stamp 全零缺少可复核时间身份，因此 fail closed。
# 设计注释：width 和 height 必须为正且设置合理上限。
# 设计注释：step 必须不小于单行有效像素字节数。
# 设计注释：raw length 必须精确等于 step 乘 height。
# 设计注释：驱动 row padding 可以存在，但不会进入 canonical RGB 像素。
# 设计注释：bgr8 转换时显式交换蓝红通道。
# 设计注释：rgb8 保持原通道顺序，不做隐式颜色修正。
# 设计注释：bgra8 转换时交换蓝红并丢弃 alpha。
# 设计注释：rgba8 转换时保持 RGB 并丢弃 alpha。
# 设计注释：mono8 复制为三个通道，得到统一 RGB PNG。
# 设计注释：未知 encoding 不能凭经验解释，直接标记 unsupported。
# 设计注释：八位通道无需依赖 is_bigendian 做字节交换。
# 设计注释：PNG 固定使用八位真彩色，减少下游解码分支。
# 设计注释：PNG 每行使用 filter zero，便于人工审计编码过程。
# 设计注释：PNG chunk 的 CRC 覆盖类型和 payload，损坏可被标准解码器发现。
# 设计注释：PNG 通过标准库 zlib 生成，不依赖现场 Pillow 或 OpenCV。
# 设计注释：相同有效像素和尺寸产生确定的 canonical PNG 字节。
# 设计注释：padding 不进入 PNG，因此不同驱动 padding 不改变媒体 identity。
# 设计注释：临时文件和目标位于同一目录，保证原子 replace。
# 设计注释：fsync 后再 replace，降低异常中断产生空 artifact 的概率。
# 设计注释：capture 失败会移除可能存在的旧 keyframe，避免旧图冒充本轮 live。
# 设计注释：manifest 在写入前再次执行 binary 和隐私检查。
# 设计注释：receipt 只重复安全 lineage，不增加新的媒体访问入口。
# 设计注释：receipt 明确 retry_attempted 为 false。
# 设计注释：receipt 明确 runtime_started_or_stopped 为 false。
# 设计注释：receipt 明确 topic_written 为 false。
# 设计注释：safe_to_control 在所有状态都固定为 false。
# 设计注释：robot_control_executed 在所有状态都固定为 false。
# 设计注释：route_execution_success 在所有状态都固定为 false。
# 设计注释：delivery_success 在所有状态都固定为 false。
# 设计注释：hil_pass 在所有状态都固定为 false。
# 设计注释：external artifact delta 在所有状态都固定为 false。
# 设计注释：live control delta 在所有状态都固定为 false。
# 设计注释：user action delta 在所有状态都固定为 false。
# 设计注释：只有真实首帧和 PNG/hash clean 才允许 current artifact delta 为 true。
# 设计注释：inventory-only、timeout、坏 layout 和坏 encoding 的 current delta 都为 false。
# 设计注释：四个 delta 未全满足，因此本 helper 不宣称 Mission Objective 0 完成。
# 设计注释：本 helper 不验证 RTC、WebRTC、视频流或多帧稳定性。
# 设计注释：本 helper 不验证 production annotation、云存储或 OSS 上传。
# 设计注释：本 helper 不验证人工已完成标注或审核动作。
# 设计注释：本 helper 不验证 route、delivery、operator acceptance 或 HIL。
# 设计注释：本 helper 不使用旧 camera health 或旧 keyframe 作为当前证据。
# 设计注释：本 helper 不重跑 scan inventory，也不依赖 LaserScan 状态。
# 设计注释：CLI 只打印固定状态摘要，不打印 JSON 内容。
# 设计注释：CLI 只打印 invocation 和 annotation-ready，不打印 topic 或 host。
# 设计注释：本地参数错误同样返回 fail-closed exit code 二。
# 设计注释：inventory clean 返回零，blocked 返回二，便于验收脚本区分。
# 设计注释：capture clean 返回零，blocked 返回二，且失败 artifact 仍可解析。
# 设计注释：source proof 明确区分 inventory blocked、capture failed 和 live captured。
# 设计注释：source mode 始终说明来源是 live ROS graph，不伪装 production cloud。
# 设计注释：message type 在 manifest 和 receipt 中必须逐字一致。
# 设计注释：publisher count 固化为 inventory 当时读数，不用 capture 时读数覆盖。
# 设计注释：capture 后不再执行第二次 inventory，保持本轮 invocation 上限。
# 设计注释：下游只需验证 frozen fields 与 PNG hash，无需接触 raw frame。
# 设计注释：任何安全字段被改成 true 都会被 validate_manifest 拒绝。
# 设计注释：任何 live source 与 invocation count 不一致都会被拒绝。
# 设计注释：任何 live media hash 或 size 不一致都会被拒绝。
# 设计注释：任何 redaction boundary 漂移都会被拒绝。
# 设计注释：最终文档必须继续声明 vendor 示例不能证明当前实机配置。
# 设计注释：最终证据边界由本轮 inventory/capture artifact 决定，而非历史记忆。


# schema 和 task identity 在 Epic 内冻结，避免 O6/O7 lineage 因现场重跑漂移。
MANIFEST_SCHEMA = "trashbot.o7.live_camera_keyframe_manifest.v1"
INVENTORY_SCHEMA = "trashbot.o7.read_only_camera_inventory.v1"
RECEIPT_SCHEMA = "trashbot.o7.live_camera_keyframe_capture_receipt.v1"
TASK_ID = "task_o7_live_camera_keyframe_annotation_20260715_1158"
MESSAGE_TYPE = "sensor_msgs/msg/Image"
CANONICAL_TOPIC = "/camera/image_raw"
MEDIA_BASENAME = "keyframe.png"

# 只允许 ROS graph 中结构化 topic 名，拒绝把自由文本带入 SSH 参数或 artifact。
TOPIC_RE = re.compile(r"/[A-Za-z0-9_~/]+(?:/[A-Za-z0-9_~]+)*\Z")
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
UNSAFE_TEXT_MARKERS = (
    "/root/",
    "/Users/",
    "file://",
    "http://",
    "https://",
    "data:image",
    "base64,",
    "192.168.",
    "root@",
)

# 这些字段始终为 false；捕获图像不能被误读为控制、路线、履约或 HIL 证据。
FIXED_FALSE_FIELDS = {
    "external_artifact_delta": False,
    "live_control_delta": False,
    "user_action_delta": False,
    "safe_to_control": False,
    "robot_control_executed": False,
    "route_execution_success": False,
    "delivery_success": False,
    "hil_pass": False,
}

REQUIRED_MANIFEST_FIELDS = {
    "schema",
    "task_id",
    "source_mode",
    "source_proof",
    "topic",
    "message_type",
    "publisher_count_at_inventory",
    "stamp_sec",
    "stamp_nanosec",
    "width",
    "height",
    "step",
    "encoding",
    "is_bigendian",
    "media_basename",
    "media_byte_size",
    "sha256",
    "captured_at_utc",
    "inventory_ssh_invocation_count",
    "single_frame_capture_invocation_count",
    "redaction_boundary",
    "annotation_ready",
    "blocked_reasons",
    "not_proven",
}


def utc_now() -> str:
    """返回可排序 UTC 时间，统一去掉运行主机的本地时区差异。"""

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def redaction_boundary() -> dict[str, Any]:
    """生成冻结的媒体隔离边界；manifest 只能携带 metadata。"""

    return {
        "classification": "metadata_only_pending_privacy_review",
        "raw_pixels_in_manifest": False,
        "binary_inline_in_api": False,
        "binary_logged": False,
        "absolute_path_exposed": False,
        "remote_host_exposed": False,
        "ui_metadata_only": True,
        "privacy_review_status": "pending_not_approved",
        "media_access_scope": "sprint_local_artifact_only",
    }


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    """原子替换 artifact，避免 timeout 时留下半张 PNG 或半个 JSON。"""

    path.parent.mkdir(parents=True, exist_ok=True)
    # 临时文件和目标位于同一目录，确保 os.replace 不跨文件系统。
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        temp_path = Path(handle.name)
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp_path, path)


def write_json(path: Path, value: dict[str, Any]) -> None:
    """只写 UTF-8 metadata；bytes 会在序列化前被拒绝。"""

    assert_no_binary_or_unsafe_reference(value)
    encoded = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    _atomic_write_bytes(path, encoded)


def assert_no_binary_or_unsafe_reference(value: Any, key: str = "root") -> None:
    """递归阻断 raw pixels、base64、远端地址和绝对文件路径泄漏。"""

    if isinstance(value, (bytes, bytearray, memoryview)):
        raise ValueError(f"binary_value_forbidden:{key}")
    if isinstance(value, dict):
        # 像素字段即使伪装成整数列表也禁止进入 JSON。
        forbidden_keys = {"data", "pixels", "raw_pixels", "raw_bytes", "image_bytes", "base64"}
        for child_key, child_value in value.items():
            if str(child_key).lower() in forbidden_keys:
                raise ValueError(f"binary_key_forbidden:{child_key}")
            assert_no_binary_or_unsafe_reference(child_value, str(child_key))
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            assert_no_binary_or_unsafe_reference(child, f"{key}[{index}]")
        return
    if isinstance(value, str):
        lowered = value.lower()
        if any(marker.lower() in lowered for marker in UNSAFE_TEXT_MARKERS):
            raise ValueError(f"unsafe_reference_forbidden:{key}")


def normalize_topic(value: str) -> str:
    """验证 topic，防止 shell 注入并保持 lineage 可比较。"""

    topic = value.strip()
    if not TOPIC_RE.fullmatch(topic) or "//" in topic or topic.endswith("/"):
        raise ValueError("invalid_ros_topic")
    return topic


def choose_image_topic(records: Iterable[dict[str, Any]]) -> tuple[dict[str, Any] | None, list[str]]:
    """canonical 优先；canonical 缺席时只接受唯一兼容 Image publisher。"""

    normalized: list[dict[str, Any]] = []
    for record in records:
        topic = normalize_topic(str(record.get("topic", "")))
        types = sorted({str(item) for item in record.get("types", []) if str(item)})
        publisher_count = int(record.get("publisher_count", 0))
        normalized.append({"topic": topic, "types": types, "publisher_count": publisher_count})

    # canonical 一旦存在但类型/count 不合格就 fail closed，不悄悄切换到旁路 topic。
    canonical = next((item for item in normalized if item["topic"] == CANONICAL_TOPIC), None)
    if canonical is not None:
        if canonical["types"] != [MESSAGE_TYPE]:
            return None, ["canonical_topic_wrong_type"]
        if canonical["publisher_count"] < 1:
            return None, ["canonical_topic_zero_publishers"]
        return canonical, []

    candidates = [
        item
        for item in normalized
        if item["types"] == [MESSAGE_TYPE] and item["publisher_count"] >= 1
    ]
    # 多个兼容候选无法证明唯一来源，不能按名称猜测。
    if len(candidates) > 1:
        return None, ["multiple_compatible_image_topics"]
    if len(candidates) == 1:
        return candidates[0], []
    return None, ["no_compatible_image_publisher"]


def evaluate_inventory(remote: dict[str, Any]) -> dict[str, Any]:
    """把单次 SSH 结果收敛为不含 host/原始 shell 输出的安全 inventory。"""

    blocked: list[str] = []
    if not remote.get("dependency_ok"):
        blocked.append("remote_rclpy_or_image_dependency_unavailable")
    if int(remote.get("topic_list_exit_code", 1)) != 0:
        blocked.append("bounded_topic_list_failed")
    if remote.get("daemon_pre") != remote.get("daemon_post"):
        blocked.append("ros2_daemon_process_drift")

    selected: dict[str, Any] | None = None
    if not blocked:
        try:
            selected, selection_blocked = choose_image_topic(remote.get("records", []))
            blocked.extend(selection_blocked)
        except (TypeError, ValueError):
            blocked.append("invalid_inventory_payload")

    return {
        "schema": INVENTORY_SCHEMA,
        "status": "clean_read_only_image_publisher" if not blocked else "blocked_fail_closed",
        "task_id": TASK_ID,
        "source_mode": "live_ros_graph_read_only_inventory",
        "source_proof": "live_read_only_inventory",
        "topic": selected["topic"] if selected else "",
        "message_type": MESSAGE_TYPE,
        "publisher_count_at_inventory": selected["publisher_count"] if selected else 0,
        "candidate_count": len(remote.get("records", [])),
        # 只保留 pid 数量和是否漂移，不泄漏远端命令行或 host。
        "daemon_process_count_pre": len(remote.get("daemon_pre", [])),
        "daemon_process_count_post": len(remote.get("daemon_post", [])),
        "daemon_process_drift": remote.get("daemon_pre") != remote.get("daemon_post"),
        "ros2cli_no_daemon": True,
        "inventory_ssh_invocation_count": 1,
        "single_frame_capture_invocation_count": 0,
        "runtime_started_or_stopped": False,
        "topic_written": False,
        "blocked_reasons": blocked,
        "not_proven": ["camera_device_identity", "camera_resolution", "visible_content", "privacy_approved"],
        "current_run_artifact_delta": False,
        **FIXED_FALSE_FIELDS,
    }


def _chunk(kind: bytes, payload: bytes) -> bytes:
    """生成 PNG chunk，CRC 覆盖 kind+payload。"""

    body = kind + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def image_to_rgb_rows(metadata: dict[str, Any], raw: bytes) -> tuple[int, int, bytes]:
    """校验 ROS Image layout，并去掉 row padding 后转换为 RGB。"""

    width = int(metadata.get("width", 0))
    height = int(metadata.get("height", 0))
    step = int(metadata.get("step", 0))
    encoding = str(metadata.get("encoding", "")).lower()
    if width <= 0 or height <= 0 or width > 16384 or height > 16384:
        raise ValueError("invalid_image_dimensions")

    channels_by_encoding = {"rgb8": 3, "bgr8": 3, "rgba8": 4, "bgra8": 4, "mono8": 1}
    channels = channels_by_encoding.get(encoding)
    if channels is None:
        raise ValueError("unsupported_image_encoding")
    minimum_step = width * channels
    if step < minimum_step or len(raw) != step * height:
        raise ValueError("invalid_image_layout")

    rows = bytearray()
    for row_index in range(height):
        # 每行只取有效像素，驱动 padding 不应进入 canonical PNG hash。
        row = raw[row_index * step : row_index * step + minimum_step]
        if encoding == "rgb8":
            rows.extend(row)
        elif encoding == "bgr8":
            for offset in range(0, len(row), 3):
                rows.extend((row[offset + 2], row[offset + 1], row[offset]))
        elif encoding in {"rgba8", "bgra8"}:
            for offset in range(0, len(row), 4):
                if encoding == "rgba8":
                    rows.extend(row[offset : offset + 3])
                else:
                    rows.extend((row[offset + 2], row[offset + 1], row[offset]))
        else:
            for sample in row:
                rows.extend((sample, sample, sample))
    return width, height, bytes(rows)


def encode_png(metadata: dict[str, Any], raw: bytes) -> bytes:
    """用标准库生成 deterministic RGB PNG，避免远端安装 Pillow/OpenCV。"""

    width, height, rgb = image_to_rgb_rows(metadata, raw)
    stride = width * 3
    # filter=0 保持实现可审计；压缩只影响大小，不改变像素语义。
    scanlines = b"".join(b"\x00" + rgb[row * stride : (row + 1) * stride] for row in range(height))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", zlib.compress(scanlines, 9)) + _chunk(b"IEND", b"")


def blocked_manifest(
    *, topic: str = "", publisher_count: int = 0, inventory_count: int = 1,
    capture_count: int = 0, blocked_reasons: list[str], source_proof: str,
) -> dict[str, Any]:
    """所有失败都产出完整冻结字段，避免消费端用缺字段猜成功。"""

    return {
        "schema": MANIFEST_SCHEMA,
        "status": "blocked_fail_closed",
        "proof_boundary": "live_camera_keyframe_not_captured_or_not_validated",
        "task_id": TASK_ID,
        "source_mode": "live_ros_graph_single_frame",
        "source_proof": source_proof,
        "topic": topic,
        "message_type": MESSAGE_TYPE,
        "publisher_count_at_inventory": publisher_count,
        "stamp_sec": 0,
        "stamp_nanosec": 0,
        "width": 0,
        "height": 0,
        "step": 0,
        "encoding": "",
        "is_bigendian": False,
        "media_basename": "",
        "media_byte_size": 0,
        "sha256": "",
        "captured_at_utc": "",
        "inventory_ssh_invocation_count": inventory_count,
        "single_frame_capture_invocation_count": capture_count,
        "redaction_boundary": redaction_boundary(),
        "annotation_ready": False,
        "blocked_reasons": blocked_reasons,
        "not_proven": [
            "live_single_frame_captured",
            "visible_content",
            "privacy_approved",
            "production_annotation",
            "production_cloud_or_oss",
            "route_execution",
            "delivery",
            "hil",
        ],
        "current_run_artifact_delta": False,
        **FIXED_FALSE_FIELDS,
    }


def live_manifest(inventory: dict[str, Any], metadata: dict[str, Any], png: bytes) -> dict[str, Any]:
    """只在单次 capture、layout 和 PNG hash 全部 clean 后生成 annotation-ready。"""

    stamp_sec = int(metadata.get("stamp_sec", 0))
    stamp_nanosec = int(metadata.get("stamp_nanosec", -1))
    if stamp_sec < 0 or not (0 <= stamp_nanosec < 1_000_000_000) or (stamp_sec == 0 and stamp_nanosec == 0):
        raise ValueError("invalid_image_stamp")
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "status": "live_single_frame_annotation_ready",
        "proof_boundary": "live_single_ros_image_frame_sprint_local_png_metadata_only",
        "task_id": TASK_ID,
        "source_mode": "live_ros_graph_single_frame",
        "source_proof": "live_single_frame_captured",
        "topic": normalize_topic(str(inventory["topic"])),
        "message_type": MESSAGE_TYPE,
        "publisher_count_at_inventory": int(inventory["publisher_count_at_inventory"]),
        "stamp_sec": stamp_sec,
        "stamp_nanosec": stamp_nanosec,
        "width": int(metadata["width"]),
        "height": int(metadata["height"]),
        "step": int(metadata["step"]),
        "encoding": str(metadata["encoding"]).lower(),
        "is_bigendian": bool(metadata.get("is_bigendian", False)),
        "media_basename": MEDIA_BASENAME,
        "media_byte_size": len(png),
        "sha256": hashlib.sha256(png).hexdigest(),
        "captured_at_utc": utc_now(),
        "inventory_ssh_invocation_count": 1,
        "single_frame_capture_invocation_count": 1,
        "redaction_boundary": redaction_boundary(),
        "annotation_ready": True,
        "blocked_reasons": [],
        # annotation-ready 只证明稳定 lineage，不等于内容可见或隐私已批准。
        "not_proven": [
            "visible_content",
            "privacy_approved",
            "annotation_submitted",
            "production_annotation",
            "production_cloud_or_oss",
            "external_artifact_delta",
            "live_control_delta",
            "user_action_delta",
            "route_execution",
            "delivery",
            "hil",
        ],
        "current_run_artifact_delta": True,
        **FIXED_FALSE_FIELDS,
    }
    validate_manifest(manifest, png)
    return manifest


def validate_manifest(manifest: dict[str, Any], png: bytes | None = None) -> None:
    """冻结字段、invocation、hash、redaction 和安全字段统一 fail closed。"""

    missing = sorted(REQUIRED_MANIFEST_FIELDS - manifest.keys())
    if missing:
        raise ValueError(f"missing_manifest_fields:{','.join(missing)}")
    if manifest.get("schema") != MANIFEST_SCHEMA or manifest.get("task_id") != TASK_ID:
        raise ValueError("manifest_identity_mismatch")
    if manifest.get("message_type") != MESSAGE_TYPE:
        raise ValueError("manifest_message_type_mismatch")
    if manifest.get("redaction_boundary") != redaction_boundary():
        raise ValueError("manifest_redaction_boundary_mismatch")
    for key, expected in FIXED_FALSE_FIELDS.items():
        if manifest.get(key) is not expected:
            raise ValueError(f"dangerous_field_not_false:{key}")
    assert_no_binary_or_unsafe_reference(manifest)

    live = manifest.get("source_proof") == "live_single_frame_captured"
    if live:
        if manifest.get("inventory_ssh_invocation_count") != 1 or manifest.get("single_frame_capture_invocation_count") != 1:
            raise ValueError("live_invocation_count_mismatch")
        if manifest.get("annotation_ready") is not True or manifest.get("current_run_artifact_delta") is not True:
            raise ValueError("live_annotation_delta_mismatch")
        if manifest.get("media_basename") != MEDIA_BASENAME or not SHA256_RE.fullmatch(str(manifest.get("sha256", ""))):
            raise ValueError("live_media_identity_invalid")
        if png is None or len(png) != manifest.get("media_byte_size") or hashlib.sha256(png).hexdigest() != manifest.get("sha256"):
            raise ValueError("live_png_hash_or_size_mismatch")
    else:
        if manifest.get("annotation_ready") is not False or manifest.get("current_run_artifact_delta") is not False:
            raise ValueError("blocked_manifest_claims_ready")
        if manifest.get("single_frame_capture_invocation_count") not in {0, 1}:
            raise ValueError("blocked_capture_count_invalid")


# inventory 在一个 SSH shell 内完成 source、daemon snapshot、topic list/info 和依赖导入。
REMOTE_INVENTORY_SCRIPT = r'''set -euo pipefail
source /opt/ros/humble/setup.bash >/dev/null 2>&1
if [ -f /root/rober/onboard/install/setup.bash ]; then
  source /root/rober/onboard/install/setup.bash >/dev/null 2>&1
fi
export ROS2CLI_NO_DAEMON=1
python3 - <<'PY'
import json, pathlib, re, subprocess

def daemon_snapshot():
    found = []
    for entry in pathlib.Path('/proc').iterdir():
        if not entry.name.isdigit():
            continue
        try:
            command = (entry / 'cmdline').read_bytes().replace(b'\0', b' ').decode('utf-8', 'replace')
        except (OSError, PermissionError):
            continue
        if 'ros2cli.daemon' in command or '_ros2_daemon' in command:
            found.append(int(entry.name))
    return sorted(found)

before = daemon_snapshot()
dependency_ok = True
try:
    import rclpy
    from sensor_msgs.msg import Image
except Exception:
    dependency_ok = False

try:
    listed = subprocess.run(['ros2', 'topic', 'list', '-t'], text=True, capture_output=True, timeout=7, check=False)
    list_code = listed.returncode
    lines = listed.stdout.splitlines() if listed.returncode == 0 else []
except Exception:
    list_code = 124
    lines = []

records = []
for line in lines:
    match = re.fullmatch(r'(/[^\s]+) \[(.+)\]', line.strip())
    if not match:
        continue
    topic, types_text = match.groups()
    types = [item.strip() for item in types_text.split(',') if item.strip()]
    if 'sensor_msgs/msg/Image' not in types and topic != '/camera/image_raw':
        continue
    try:
        info = subprocess.run(['ros2', 'topic', 'info', topic], text=True, capture_output=True, timeout=5, check=False)
        count_match = re.search(r'Publisher count:\s*(\d+)', info.stdout)
        publisher_count = int(count_match.group(1)) if info.returncode == 0 and count_match else 0
    except Exception:
        publisher_count = 0
    records.append({'topic': topic, 'types': types, 'publisher_count': publisher_count})

after = daemon_snapshot()
print(json.dumps({
    'dependency_ok': dependency_ok,
    'topic_list_exit_code': list_code,
    'records': records,
    'daemon_pre': before,
    'daemon_post': after,
}, separators=(',', ':')))
PY
'''


# capture 脚本只订阅首帧并通过私有 pipe 返回 metadata+raw bytes；不会写远端文件或 topic。
REMOTE_CAPTURE_SCRIPT = r'''set -euo pipefail
source /opt/ros/humble/setup.bash >/dev/null 2>&1
if [ -f /root/rober/onboard/install/setup.bash ]; then
  source /root/rober/onboard/install/setup.bash >/dev/null 2>&1
fi
export ROS2CLI_NO_DAEMON=1
python3 - "$1" "$2" <<'PY'
import json, struct, sys, time
import rclpy
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image

topic = sys.argv[1]
timeout_s = float(sys.argv[2])
frame = None
rclpy.init(args=None)
node = rclpy.create_node('o7_single_frame_capture_read_only', enable_rosout=False)

def callback(message):
    global frame
    if frame is None:
        frame = message

subscription = node.create_subscription(Image, topic, callback, qos_profile_sensor_data)
deadline = time.monotonic() + timeout_s
while frame is None and time.monotonic() < deadline:
    rclpy.spin_once(node, timeout_sec=min(0.2, max(0.0, deadline - time.monotonic())))

node.destroy_subscription(subscription)
node.destroy_node()
rclpy.shutdown()
if frame is None:
    raise SystemExit(4)

metadata = {
    'stamp_sec': int(frame.header.stamp.sec),
    'stamp_nanosec': int(frame.header.stamp.nanosec),
    'width': int(frame.width),
    'height': int(frame.height),
    'step': int(frame.step),
    'encoding': str(frame.encoding),
    'is_bigendian': bool(frame.is_bigendian),
    'raw_size': len(frame.data),
}
header = json.dumps(metadata, separators=(',', ':')).encode('utf-8')
out = sys.stdout.buffer
out.write(b'O7FRAME1\n')
out.write(struct.pack('>I', len(header)))
out.write(header)
out.write(bytes(frame.data))
out.flush()
PY
'''


def _terminate_owned_process(proc: subprocess.Popen[bytes]) -> None:
    """只终止本 helper 创建的 SSH process group，禁止 broad kill。"""

    try:
        os.killpg(proc.pid, signal.SIGTERM)
        proc.wait(timeout=2)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        if proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


def run_ssh(target: str, port: int, script: str, args: list[str], timeout_s: float) -> subprocess.CompletedProcess[bytes]:
    """执行一次 SSH；stdout 始终捕获在内存，禁止把 binary 打到终端。"""

    command = [
        "ssh", "-p", str(port), "-o", "BatchMode=yes", "-o", "ConnectTimeout=8",
        target, "bash", "-s", "--", *args,
    ]
    proc = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        stdout, stderr = proc.communicate(script.encode("utf-8"), timeout=timeout_s)
    except subprocess.TimeoutExpired:
        _terminate_owned_process(proc)
        raise TimeoutError("owned_ssh_process_timeout")
    return subprocess.CompletedProcess(command, int(proc.returncode or 0), stdout, stderr)


def parse_frame_transport(payload: bytes) -> tuple[dict[str, Any], bytes]:
    """解析私有 pipe；长度不一致即拒绝，避免截断帧被编码成有效 PNG。"""

    prefix = b"O7FRAME1\n"
    if not payload.startswith(prefix) or len(payload) < len(prefix) + 4:
        raise ValueError("invalid_frame_transport_prefix")
    offset = len(prefix)
    metadata_size = struct.unpack(">I", payload[offset : offset + 4])[0]
    offset += 4
    if metadata_size <= 0 or metadata_size > 65536 or len(payload) < offset + metadata_size:
        raise ValueError("invalid_frame_transport_metadata_size")
    metadata = json.loads(payload[offset : offset + metadata_size].decode("utf-8"))
    raw = payload[offset + metadata_size :]
    if len(raw) != int(metadata.get("raw_size", -1)):
        raise ValueError("frame_transport_raw_size_mismatch")
    return metadata, raw


def capture_with_transport(
    inventory: dict[str, Any], transport: Callable[[str, float], tuple[dict[str, Any], bytes]], timeout_s: float,
) -> tuple[dict[str, Any], bytes]:
    """gate clean 后精确调用一次 transport；任何异常直接向上抛出，不 retry。"""

    if inventory.get("status") != "clean_read_only_image_publisher" or inventory.get("blocked_reasons"):
        raise ValueError("inventory_gate_not_clean")
    if inventory.get("inventory_ssh_invocation_count") != 1:
        raise ValueError("inventory_invocation_count_not_one")
    topic = normalize_topic(str(inventory.get("topic", "")))
    metadata, raw = transport(topic, timeout_s)
    png = encode_png(metadata, raw)
    manifest = live_manifest(inventory, metadata, png)
    return manifest, png


def receipt_from_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """receipt 重复关键 lineage，但仍不包含 absolute path 或 pixel。"""

    return {
        "schema": RECEIPT_SCHEMA,
        "status": manifest["status"],
        "task_id": manifest["task_id"],
        "source_proof": manifest["source_proof"],
        "topic": manifest["topic"],
        "message_type": manifest["message_type"],
        "stamp_sec": manifest["stamp_sec"],
        "stamp_nanosec": manifest["stamp_nanosec"],
        "width": manifest["width"],
        "height": manifest["height"],
        "encoding": manifest["encoding"],
        "media_basename": manifest["media_basename"],
        "media_byte_size": manifest["media_byte_size"],
        "sha256": manifest["sha256"],
        "inventory_ssh_invocation_count": manifest["inventory_ssh_invocation_count"],
        "single_frame_capture_invocation_count": manifest["single_frame_capture_invocation_count"],
        "retry_attempted": False,
        "binary_logged": False,
        "binary_inline_in_json_or_api": False,
        "runtime_started_or_stopped": False,
        "topic_written": False,
        "annotation_ready": manifest["annotation_ready"],
        "blocked_reasons": manifest["blocked_reasons"],
        "not_proven": manifest["not_proven"],
        "current_run_artifact_delta": manifest["current_run_artifact_delta"],
        **FIXED_FALSE_FIELDS,
    }


def command_inventory(args: argparse.Namespace) -> int:
    """执行唯一 inventory SSH，并在失败时同步落 blocked manifest/receipt。"""

    if args.max_inventory_ssh_invocations != 1 or not args.ros2cli_no_daemon:
        raise ValueError("inventory_requires_exactly_one_daemon_off_invocation")
    try:
        completed = run_ssh(args.ssh_target, args.ssh_port, REMOTE_INVENTORY_SCRIPT, [], args.timeout_s)
        if completed.returncode != 0:
            raise RuntimeError("inventory_ssh_nonzero")
        remote = json.loads(completed.stdout.decode("utf-8"))
        inventory = evaluate_inventory(remote)
    except Exception as exc:
        # artifact 只记录稳定错误类别，不写 stderr/host/traceback。
        reason = "inventory_timeout" if isinstance(exc, TimeoutError) else "inventory_ssh_or_payload_failed"
        inventory = evaluate_inventory({"dependency_ok": False, "topic_list_exit_code": 1, "records": [], "daemon_pre": [], "daemon_post": []})
        inventory["blocked_reasons"] = [reason]
    write_json(Path(args.inventory_output), inventory)

    if inventory["blocked_reasons"]:
        manifest = blocked_manifest(
            topic=inventory["topic"], publisher_count=inventory["publisher_count_at_inventory"],
            capture_count=0, blocked_reasons=inventory["blocked_reasons"], source_proof="live_inventory_blocked",
        )
        validate_manifest(manifest)
        write_json(Path(args.manifest_output), manifest)
        write_json(Path(args.receipt_output), receipt_from_manifest(manifest))
        print("inventory_status=blocked_fail_closed invocation_count=1 capture_allowed=false")
        return 2
    print("inventory_status=clean invocation_count=1 capture_allowed=true")
    return 0


def command_capture_one(args: argparse.Namespace) -> int:
    """消费 inventory gate，最多一次 SSH，成功后只落 canonical PNG 和 metadata。"""

    if args.max_single_frame_capture_invocations != 1 or not (0 < args.timeout_s <= 12):
        raise ValueError("capture_requires_one_invocation_and_timeout_at_most_12s")
    inventory = json.loads(Path(args.inventory_input).read_text(encoding="utf-8"))
    if inventory.get("status") != "clean_read_only_image_publisher" or inventory.get("blocked_reasons"):
        manifest = blocked_manifest(
            topic=str(inventory.get("topic", "")),
            publisher_count=int(inventory.get("publisher_count_at_inventory", 0)),
            capture_count=0,
            blocked_reasons=list(inventory.get("blocked_reasons") or ["inventory_gate_not_clean"]),
            source_proof="live_inventory_blocked",
        )
        validate_manifest(manifest)
        write_json(Path(args.manifest_output), manifest)
        write_json(Path(args.receipt_output), receipt_from_manifest(manifest))
        print("capture_status=skipped_gate_blocked invocation_count=0 annotation_ready=false")
        return 2

    def transport(topic: str, timeout_s: float) -> tuple[dict[str, Any], bytes]:
        completed = run_ssh(
            args.ssh_target,
            args.ssh_port,
            REMOTE_CAPTURE_SCRIPT,
            [topic, str(timeout_s)],
            timeout_s + 8,
        )
        if completed.returncode != 0:
            raise RuntimeError("single_frame_capture_nonzero")
        return parse_frame_transport(completed.stdout)

    try:
        manifest, png = capture_with_transport(inventory, transport, args.timeout_s)
        _atomic_write_bytes(Path(args.media_output), png)
        write_json(Path(args.manifest_output), manifest)
        write_json(Path(args.receipt_output), receipt_from_manifest(manifest))
        print("capture_status=live_single_frame_captured invocation_count=1 annotation_ready=true")
        return 0
    except Exception as exc:
        # capture 已启动后任何失败都固定 count=1，且本函数没有 retry 分支。
        reason = "single_frame_capture_timeout" if isinstance(exc, TimeoutError) else str(exc)
        if not re.fullmatch(r"[a-z0-9_:,-]+", reason):
            reason = "single_frame_capture_failed"
        manifest = blocked_manifest(
            topic=str(inventory.get("topic", "")),
            publisher_count=int(inventory.get("publisher_count_at_inventory", 0)),
            capture_count=1,
            blocked_reasons=[reason],
            source_proof="live_single_frame_capture_failed",
        )
        validate_manifest(manifest)
        Path(args.media_output).unlink(missing_ok=True)
        write_json(Path(args.manifest_output), manifest)
        write_json(Path(args.receipt_output), receipt_from_manifest(manifest))
        print("capture_status=blocked_fail_closed invocation_count=1 annotation_ready=false retry=false")
        return 2


def build_parser() -> argparse.ArgumentParser:
    """CLI 明示所有 artifact 路径，避免 helper 写出 sprint 目录之外。"""

    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inventory = subparsers.add_parser("inventory")
    inventory.add_argument("--ssh-target", required=True)
    inventory.add_argument("--ssh-port", type=int, required=True)
    inventory.add_argument("--ros2cli-no-daemon", action="store_true")
    inventory.add_argument("--max-inventory-ssh-invocations", type=int, default=1)
    inventory.add_argument("--timeout-s", type=float, default=24.0)
    inventory.add_argument("--inventory-output", required=True)
    inventory.add_argument("--manifest-output", required=True)
    inventory.add_argument("--receipt-output", required=True)
    inventory.set_defaults(handler=command_inventory)

    capture = subparsers.add_parser("capture-one")
    capture.add_argument("--ssh-target", required=True)
    capture.add_argument("--ssh-port", type=int, required=True)
    capture.add_argument("--inventory-input", required=True)
    capture.add_argument("--max-single-frame-capture-invocations", type=int, default=1)
    capture.add_argument("--timeout-s", type=float, default=12.0)
    capture.add_argument("--media-output", required=True)
    capture.add_argument("--manifest-output", required=True)
    capture.add_argument("--receipt-output", required=True)
    capture.set_defaults(handler=command_capture_one)
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI 只打印状态，不打印 SSH 命令、host、JSON、binary 或 traceback。"""

    args = build_parser().parse_args(argv)
    try:
        return int(args.handler(args))
    except (OSError, ValueError, json.JSONDecodeError):
        print("status=blocked_fail_closed invalid_local_arguments_or_artifact", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
