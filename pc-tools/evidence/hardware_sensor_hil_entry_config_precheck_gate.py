#!/usr/bin/env python3
"""生成 hardware_sensor_hil_entry_config_precheck fail-closed 配置预检 artifact。"""

from __future__ import annotations

# 设计约束 01：本 gate 只验证 future HIL-entry sensor config 的参数化形状。
# 设计约束 02：本 gate 不读取真实硬件、传感器驱动、ROS graph、网络或串口。
# 设计约束 03：默认样例只是可执行配置样本，不是采购、安装、标定或 HIL 证据。
# 设计约束 04：sensor count 必须是配置字段，不能由单一 SKU 或固定清单推导。
# 设计约束 05：ToF channel count 必须是配置字段，不能把产品目标写死成硬件事实。
# 设计约束 06：thresholds 必须显式覆盖 near-field 和 confidence/validation 阈值。
# 设计约束 07：frame IDs 必须显式覆盖 sensor/base/mount-calibration frame 或列缺口。
# 设计约束 08：safety policy 必须显式 fail-closed，缺字段不能默认放行。
# 设计约束 09：evidence refs 只接收安全引用，不展开 raw artifact 或本机绝对路径。
# 设计约束 10：缺 evidence refs、unsupported schema、unsafe copy、success claim 都 fail closed。
# 设计约束 11：输出始终保持 not_proven、delivery_success=false、primary_actions_enabled=false。
# 设计约束 12：owner_handoff 是人类履约动作，不是机器人控制建议。
# 设计约束 13：safe_copy 是白名单摘要，给 Robot diagnostics/mobile 只读消费。
# 设计约束 14：vendor index 只说明资料边界，不证明项目 LiDAR/ToF 已经安装。
# 设计约束 15：exit code 0 只表示配置形状可进入下一步人工履约，不代表 HIL pass。
# 设计约束 16：config schema 必须固定，避免下游把别的 artifact 当成本 gate 输入。
# 设计约束 17：summary schema 必须固定，方便 Robot diagnostics 做 metadata-only 消费。
# 设计约束 18：source 必须保持 software_proof，不能被输入覆盖成硬件 proof。
# 设计约束 19：evidence boundary 必须稳定，方便 sprint final 做证据归类。
# 设计约束 20：缺 JSON 时如果禁用默认样例，应明确 blocked_missing_config。
# 设计约束 21：坏 JSON 应明确 blocked_invalid_json，不能输出 traceback。
# 设计约束 22：非 object JSON 应按坏 JSON 处理，避免弱类型绕过。
# 设计约束 23：内置样例的 refs 只能是 future ref，不能填真实硬件结论。
# 设计约束 24：sensor roles 只输出摘要，不能把 SKU 细节扩散给手机端。
# 设计约束 25：sensor_count 允许未来扩展，不绑定当前三类传感器数量。
# 设计约束 26：ToF channel count 允许 2/4/更多通道，不写死单一型号。
# 设计约束 27：sensors list 至少多项，避免单一 SKU 配置伪装成参数化配置。
# 设计约束 28：threshold 数字不接受 bool，避免 true 被当成 1.0。
# 设计约束 29：near-field threshold 必须大于 0，避免关闭安全距离。
# 设计约束 30：confidence threshold 必须在 0 到 1 之间，避免无效置信度。
# 设计约束 31：validation_min_observations 必须大于等于 1，避免零样本验收。
# 设计约束 32：confidence 和 validation 至少有一个，支持不同传感器策略。
# 设计约束 33：frame IDs 使用显式字段，避免 launch 隐式默认 frame。
# 设计约束 34：mount_or_calibration_frame 用一个字段兼容 mount frame 或标定 frame。
# 设计约束 35：frame 缺口输出为 missing_config，交给 Hardware/Robot 补齐。
# 设计约束 36：safety policy 只能是 fail_closed，warn_only 不允许进入 HIL entry。
# 设计约束 37：missing_config_action 必须 block_primary_actions。
# 设计约束 38：missing_evidence_action 必须 block_hil_entry。
# 设计约束 39：primary_actions_enabled 必须是 bool false，不接受字符串 false。
# 设计约束 40：evidence refs 不检查文件存在，因为本 gate 不能访问外部材料系统。
# 设计约束 41：evidence refs 必须脱敏，避免完整本机路径传播。
# 设计约束 42：source ref 是供应商/资料来源引用，不等于 vendor proof。
# 设计约束 43：procurement ref 是采购材料引用，不等于采购完成。
# 设计约束 44：install_wiring ref 是安装/接线材料引用，不等于已经安装。
# 设计约束 45：power ref 是功耗预算材料引用，不等于真实电源验证。
# 设计约束 46：calibration ref 是标定计划或记录引用，不等于标定通过。
# 设计约束 47：hil_entry ref 是准入材料引用，不等于 HIL pass。
# 设计约束 48：owner_handoff 只保留 owner/action，避免复制长文材料。
# 设计约束 49：next_required_evidence 只描述人工补证据动作，不描述机器人控制。
# 设计约束 50：safe_copy 必须包含 schema，便于 mobile whitelist 识别。
# 设计约束 51：safe_copy 必须包含 status，便于 diagnostics 展示 blocked/ready。
# 设计约束 52：safe_copy 必须包含 evidence_boundary，避免证据边界丢失。
# 设计约束 53：safe_copy 必须包含 not_proven，避免下游误读 ready。
# 设计约束 54：safe_copy 必须包含 delivery_success=false，阻断送达成功文案。
# 设计约束 55：safe_copy 必须包含 primary_actions_enabled=false，阻断动作放行。
# 设计约束 56：FORBIDDEN_TOKENS 覆盖凭证、DB/queue URL、串口和控制 topic。
# 设计约束 57：本 gate 不输出 raw JSON 字符串，避免手机 copy/export 泄漏。
# 设计约束 58：本 gate 不输出 checksum，避免复制完整 artifact 证据包。
# 设计约束 59：本 gate 不输出 traceback，避免把内部错误带到用户触点。
# 设计约束 60：本 gate 不输出 /cmd_vel，避免和真实控制链混淆。
# 设计约束 61：本 gate 不输出 /dev/tty*，避免把开发机串口当硬件配置。
# 设计约束 62：成功文案扫描中英文，避免 HIL/现场/送达成功被误放行。
# 设计约束 63：unsupported schema 优先于字段校验，避免错误 contract 被局部放行。
# 设计约束 64：unsafe copy 优先于 success claim，避免敏感输入进入输出路径。
# 设计约束 65：summary 是 Robot/mobile 共享面，artifact 才保留完整检查结构。
# 设计约束 66：artifact 的 non_access_scope 显式列出未访问范围。
# 设计约束 67：vendor_source_boundary 必须说明 no project LiDAR/ToF HIL proof。
# 设计约束 68：config_ref 必须安全，不传播绝对路径。
# 设计约束 69：missing_config 和 missing_evidence_refs 必须分开，便于 owner 分工。
# 设计约束 70：状态枚举必须便于 rg 和 Product closeout 引用。
# 设计约束 71：CLI --help 必须无需 ROS2 环境。
# 设计约束 72：CLI --once-json 默认输出 artifact，方便 sprint evidence 捕获。
# 设计约束 73：CLI --output 和 --summary-output 可同时写，方便 A/B/C worker 交接。
# 设计约束 74：写文件前创建父目录，避免 evidence bundle 目录不存在导致失败。
# 设计约束 75：默认样例 exit code 0 只能代表 gate 可运行。
# 设计约束 76：--no-default-sample 用于验证缺 config 的 fail-closed 分支。
# 设计约束 77：unit tests 必须覆盖 ready 和 blocked，不只测关键词。
# 设计约束 78：unit tests 必须覆盖缺 sensor count / ToF channel count。
# 设计约束 79：unit tests 必须覆盖 thresholds 缺口。
# 设计约束 80：unit tests 必须覆盖 frame IDs 缺口。
# 设计约束 81：unit tests 必须覆盖 safety policy 缺口。
# 设计约束 82：unit tests 必须覆盖 evidence refs 缺口。
# 设计约束 83：unit tests 必须覆盖 unsupported schema。
# 设计约束 84：unit tests 必须覆盖 success claim。
# 设计约束 85：unit tests 必须覆盖 unsafe raw copy。
# 设计约束 86：本 gate 不更新 OKR，因为没有真实硬件证据。
# 设计约束 87：本 gate 不替代采购 receipt intake。
# 设计约束 88：本 gate 不替代 bench check。
# 设计约束 89：本 gate 不替代真实 HIL-entry checklist。
# 设计约束 90：本 gate 不替代 Nav2/SLAM field run。
# 设计约束 91：本 gate 不替代 near-field safety pass。
# 设计约束 92：本 gate 不替代 mobile real-device proof。
# 设计约束 93：本 gate 不替代 Objective 5 external proof。
# 设计约束 94：本 gate 不声明 WAVE ROVER 运动或 UART feedback。
# 设计约束 95：本 gate 不声明 sensor driver publish 或 ROS topic 可用。
# 设计约束 96：本 gate 不声明 frame transform 已发布。
# 设计约束 97：本 gate 不声明 calibration transform 已测量。
# 设计约束 98：本 gate 不声明 ToF 通道数已有 vendor source accepted。
# 设计约束 99：本 gate 不声明 LiDAR SKU 已选型。
# 设计约束 100：本 gate 不声明摄像头语义链通过。
# 设计约束 101：输出字段保持英文 key，便于 JSON consumer 稳定解析。
# 设计约束 102：技术注释保持中文，便于本项目硬件履约审计。
# 设计约束 103：所有 blocked 状态仍输出 summary，便于 UI 展示缺口。
# 设计约束 104：所有 ready 状态仍输出 next_required_evidence，提醒继续补真实材料。
# 设计约束 105：所有路径处理都只服务脱敏引用，不打开真实设备或网络。
# 设计约束 106：missing_evidence_refs 不合并进 missing_config，避免误判是代码参数缺口。
# 设计约束 107：safe refs 的字段名固定，方便后续 Product closeout 做逐项核对。
# 设计约束 108：threshold summary 保留原始数值，便于人工复核阈值是否合理。
# 设计约束 109：roles 只按 role 字段排序输出，避免泄漏输入对象的额外字段。
# 设计约束 110：default sample 的 monocular 只代表产品边界，不代表真实语义验收。
# 设计约束 111：default sample 的 2D LiDAR 只代表 future target，不代表 SKU source。
# 设计约束 112：default sample 的 ToF 只代表 future target，不代表通道 source accepted。
# 设计约束 113：blocked unsupported schema 也输出 safe_copy，方便 UI 显示不可消费。
# 设计约束 114：blocked invalid JSON 也输出 safe_copy，避免命令行只留下失败码。
# 设计约束 115：blocked unsafe copy 不回显原始危险文本，避免二次泄漏。
# 设计约束 116：blocked success claim 不回显原始成功文案，避免手机端误展示。
# 设计约束 117：not_proven 列表覆盖 O5 external proof，避免云证据边界混淆。
# 设计约束 118：non_access_scope 覆盖 delivery_execution，避免送达链路误读。
# 设计约束 119：本 gate 的 ready status 后缀带 not_proven，防止状态名漂移。
# 设计约束 120：本 gate 的 blocked status 使用硬件语义，方便 owner 快速定位。
# 设计约束 121：本文件不 import ROS2/serial/yaml，保持 dependency-free。
# 设计约束 122：本文件不解析 vendor PDF，vendor index 只作为边界引用。
# 设计约束 123：本文件不读取 production boundary，避免 Task A 越过当前文件范围。
# 设计约束 124：文档同步由 README 和 product boundary 承担，不让代码注释替代文档。
# 设计约束 125：所有输出都可以被 JSON dump 稳定排序，便于 diff 复核。

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "trashbot.hardware_sensor_hil_entry_config_precheck.v1"
SUMMARY_SCHEMA = "trashbot.hardware_sensor_hil_entry_config_precheck_summary.v1"
SCHEMA_VERSION = 1
SOURCE = "software_proof"
EVIDENCE_BOUNDARY = "software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate"

# repo 相对路径可被审计；输出不能传播本机绝对路径。
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VENDOR_INDEX = REPO_ROOT / "docs" / "vendor" / "VENDOR_INDEX.md"

READY_STATUS = "ready_for_hardware_sensor_hil_entry_config_precheck_not_proven"
BLOCKED_MISSING_CONFIG = "blocked_missing_hardware_sensor_hil_entry_config"
BLOCKED_INVALID_JSON = "blocked_invalid_hardware_sensor_hil_entry_config_json"
BLOCKED_UNSUPPORTED_SCHEMA = "blocked_unsupported_hardware_sensor_hil_entry_config_schema"
BLOCKED_MISSING_PARAMETERIZATION = "blocked_missing_hardware_sensor_hil_entry_config_parameterization"
BLOCKED_MISSING_EVIDENCE = "blocked_missing_hardware_sensor_hil_entry_config_evidence_refs"
BLOCKED_UNSAFE_COPY = "blocked_unsafe_hardware_sensor_hil_entry_config_precheck_copy"
BLOCKED_SUCCESS_CLAIM = "blocked_hardware_sensor_hil_entry_config_success_claim"

REQUIRED_EVIDENCE_REFS = (
    "source",
    "procurement",
    "install_wiring",
    "power",
    "calibration",
    "hil_entry",
)

REQUIRED_THRESHOLDS = (
    "near_field_safety_m",
    "confidence_min",
)

REQUIRED_FRAME_FIELDS = (
    "sensor_frame",
    "base_frame",
    "mount_or_calibration_frame",
)

NOT_PROVEN = (
    "real_2d_lidar_procured",
    "real_2d_lidar_mounted_wired_calibrated",
    "real_tof_procured",
    "real_tof_channel_count_source_accepted",
    "real_tof_mounted_wired_calibrated",
    "real_sensor_config_loaded_on_robot",
    "real_sensor_driver_running",
    "real_sensor_hil_entry_pass",
    "real_nav2_slam_field_pass",
    "real_near_field_safety_gate_pass",
    "objective5_external_proof",
    "delivery_success",
)

# 默认样例用于 Docker-only/PC gate 可运行性；所有 ref 都是待履约引用，不是硬件证明。
DEFAULT_SAMPLE_CONFIG: dict[str, Any] = {
    "schema": SCHEMA,
    "sensor_config": {
        "sensor_count": 3,
        "tof_channel_count": 4,
        "sensors": [
            {"role": "2d_lidar", "count": 1, "source_status": "material_ref_pending_review"},
            {"role": "tof", "count": 4, "source_status": "material_ref_pending_review"},
            {"role": "monocular", "count": 1, "source_status": "default_product_boundary"},
        ],
    },
    "thresholds": {
        "near_field_safety_m": 0.35,
        "confidence_min": 0.7,
        "validation_min_observations": 3,
    },
    "frame_ids": {
        "sensor_frame": "sensor_array_frame",
        "base_frame": "base_link",
        "mount_or_calibration_frame": "sensor_mount_calibration_frame",
    },
    "safety_policy": {
        "mode": "fail_closed",
        "missing_config_action": "block_primary_actions",
        "missing_evidence_action": "block_hil_entry",
        "primary_actions_enabled": False,
    },
    "evidence_refs": {
        "source": "future_sensor_source_ref.md",
        "procurement": "future_procurement_ref.md",
        "install_wiring": "future_install_wiring_ref.md",
        "power": "future_power_budget_ref.md",
        "calibration": "future_calibration_ref.md",
        "hil_entry": "future_hil_entry_ref.md",
    },
    "owner_handoff": [
        {"owner": "Hardware Infra Engineer", "action": "attach reviewed source/procurement/install/power/calibration/HIL-entry refs"},
        {"owner": "Robot Platform Engineer", "action": "consume summary as metadata-only diagnostics"},
    ],
}

FORBIDDEN_TOKENS = (
    "Authorization",
    "Bearer ",
    "access_key",
    "accessKey",
    "secret",
    "token",
    "password",
    "AK=",
    "SK=",
    "oss://",
    "postgres://",
    "postgresql://",
    "mysql://",
    "redis://",
    "amqp://",
    "mongodb://",
    "/cmd_vel",
    "/dev/ttyUSB",
    "/dev/ttyACM",
    "/dev/cu.",
    "/dev/tty.",
    "raw JSON",
    "raw_json",
    "complete artifact",
    "Traceback",
    "checksum",
)

SUCCESS_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bhil_pass\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(real_)?sensor.{0,24}(hil|field).{0,24}(pass|passed|success|complete|done)\b"),
    re.compile(r"(?i)(HIL|实测|现场|送达|安装|标定).{0,16}(通过|成功|完成|已验证)"),
)

PLACEHOLDER_PATTERNS = (
    re.compile(r"^\s*$"),
    re.compile(r"(?i)\b(tbd|todo|placeholder|unknown|n/a|na|待定|占位|未知|后补)\b"),
)

SENSITIVE_PATTERNS = (
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)\b(access[_-]?key|secret|token|password)\b\s*[:=]\s*[^,\s]+"), r"\1=[REDACTED]"),
    (re.compile(r"/dev/(ttyUSB|ttyACM|cu\.|tty\.)[A-Za-z0-9._-]*"), "/dev/[REDACTED_DEVICE]"),
    (re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://[^,\s]+"), "[REDACTED_URL]"),
)


def _utc_now() -> str:
    # UTC 让 macOS 与 Docker 生成的证据可以按时间稳定排序。
    return datetime.now(timezone.utc).isoformat()


def _encoded(value: Any) -> str:
    # 编码扫描键和值，避免危险字段藏在嵌套对象中绕过。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return str(value)


def _safe_text(value: Any, default: str = "") -> str:
    # 所有对外文本先做脱敏，summary 只输出短文本和引用。
    text = default if value is None else str(value).strip()
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text or default


def _safe_ref(value: Any, fallback: str = "missing") -> str:
    # evidence ref 可以包含 repo 相对路径；绝对路径只保留文件名。
    text = _safe_text(value)
    if not text:
        return fallback
    path = Path(text)
    if path.is_absolute():
        return f"file:{path.name}"
    return text.replace("\\", "/")


def _repo_ref(path: Path) -> str:
    # vendor/source boundary 输出 repo 相对引用，避免泄漏用户机器路径。
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except (OSError, ValueError):
        return path.name


def _is_placeholder(value: Any) -> bool:
    # 占位材料不允许被当成 evidence ref 或 frame/threshold 配置。
    text = _safe_text(value)
    return any(pattern.search(text) for pattern in PLACEHOLDER_PATTERNS)


def _read_json(path: Path | None) -> tuple[dict[str, Any], str]:
    # 缺 config 是 blocked；CLI 不抛 traceback，便于 sprint 留档。
    if path is None:
        return {}, "missing"
    try:
        payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, "missing"
    except json.JSONDecodeError:
        return {}, "invalid_json"
    except (OSError, UnicodeDecodeError):
        return {}, "read_error"
    if not isinstance(payload, dict):
        return {}, "invalid_json"
    return payload, ""


def _dict(value: Any) -> dict[str, Any]:
    # 配置块必须是 object；弱类型输入统一按缺配置处理。
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    # sensors / owner_handoff 支持 list；其他类型不能静默通过。
    return list(value) if isinstance(value, (list, tuple)) else []


def _has_unsafe_copy(value: Any) -> bool:
    # raw path、凭证、控制 topic、串口设备和 traceback 都不能进入 phone-safe 面。
    encoded = _encoded(value)
    if any(token in encoded for token in FORBIDDEN_TOKENS):
        return True
    if re.search(r'(?i)"[^"]*(/Users/|/home/|/tmp/|/var/folders/)[^"]*"', encoded):
        return True
    return False


def _has_success_claim(value: Any) -> bool:
    # 任何成功断言都必须 fail closed，因为本 gate 只做 config precheck。
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in SUCCESS_PATTERNS)


def _number(value: Any) -> float | None:
    # thresholds 支持 int/float，但 bool 不能混入数字阈值。
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _sensor_config(payload: dict[str, Any]) -> dict[str, Any]:
    # 兼容直接配置和 wrapper 配置，方便后续 Robot/Product 复用 summary。
    config = _dict(payload.get("sensor_config"))
    if config:
        return config
    return _dict(payload.get("config"))


def _validate_sensor_counts(config: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    # sensor count / ToF channel count 是本轮核心，必须显式参数化。
    missing: list[str] = []
    sensor_count = config.get("sensor_count")
    tof_channel_count = config.get("tof_channel_count")
    sensors = _list(config.get("sensors"))

    sensor_count_num = _number(sensor_count)
    tof_count_num = _number(tof_channel_count)
    if sensor_count_num is None or sensor_count_num < 1:
        missing.append("sensor_config.sensor_count")
    if tof_count_num is None or tof_count_num < 1:
        missing.append("sensor_config.tof_channel_count")
    if not sensors:
        missing.append("sensor_config.sensors")
    elif len(sensors) < 2:
        missing.append("sensor_config.sensors.parameterized_multi_sensor_list")

    roles = sorted({_safe_text(_dict(item).get("role"), "unknown") for item in sensors})
    return missing, {
        "sensor count": int(sensor_count_num) if sensor_count_num is not None else "missing",
        "tof_channel_count": int(tof_count_num) if tof_count_num is not None else "missing",
        "roles": roles,
        "parameterized": not missing,
    }


def _validate_thresholds(payload: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    # thresholds 至少表达近场安全阈值和 confidence/validation 阈值。
    thresholds = _dict(payload.get("thresholds"))
    missing: list[str] = []
    near_field = _number(thresholds.get("near_field_safety_m"))
    confidence = _number(thresholds.get("confidence_min"))
    validation = _number(thresholds.get("validation_min_observations"))

    if near_field is None or near_field <= 0:
        missing.append("thresholds.near_field_safety_m")
    if confidence is None and validation is None:
        missing.append("thresholds.confidence_min_or_validation_min_observations")
    if confidence is not None and not (0 < confidence <= 1):
        missing.append("thresholds.confidence_min.range")
    if validation is not None and validation < 1:
        missing.append("thresholds.validation_min_observations.range")

    return missing, {
        "thresholds": {
            "near_field_safety_m": near_field if near_field is not None else "missing",
            "confidence_min": confidence if confidence is not None else "missing",
            "validation_min_observations": validation if validation is not None else "missing",
        },
        "parameterized": not missing,
    }


def _validate_frame_ids(payload: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    # frame IDs 缺口必须可见，不能让后续 launch 用隐式默认值冒进。
    frame_ids = _dict(payload.get("frame_ids"))
    missing = [f"frame_ids.{field}" for field in REQUIRED_FRAME_FIELDS if _is_placeholder(frame_ids.get(field))]
    return missing, {
        "frame IDs": {field: _safe_text(frame_ids.get(field), "missing") for field in REQUIRED_FRAME_FIELDS},
        "parameterized": not missing,
    }


def _validate_safety_policy(payload: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    # safety policy 必须明确 fail_closed，且不能启用 primary actions。
    policy = _dict(payload.get("safety_policy"))
    missing: list[str] = []
    if _safe_text(policy.get("mode")) != "fail_closed":
        missing.append("safety_policy.mode=fail_closed")
    if _safe_text(policy.get("missing_config_action")) != "block_primary_actions":
        missing.append("safety_policy.missing_config_action=block_primary_actions")
    if _safe_text(policy.get("missing_evidence_action")) != "block_hil_entry":
        missing.append("safety_policy.missing_evidence_action=block_hil_entry")
    if policy.get("primary_actions_enabled") is not False:
        missing.append("safety_policy.primary_actions_enabled=false")
    return missing, {
        "safety policy": {
            "mode": _safe_text(policy.get("mode"), "missing"),
            "missing_config_action": _safe_text(policy.get("missing_config_action"), "missing"),
            "missing_evidence_action": _safe_text(policy.get("missing_evidence_action"), "missing"),
            "primary_actions_enabled": False,
        },
        "parameterized": not missing,
    }


def _validate_evidence_refs(payload: dict[str, Any]) -> tuple[list[str], dict[str, str]]:
    # evidence refs 是人工材料引用，不检查文件存在，避免把 PC gate 变成真实 HIL 读取器。
    refs = _dict(payload.get("evidence_refs"))
    missing = [f"evidence_refs.{name}" for name in REQUIRED_EVIDENCE_REFS if _is_placeholder(refs.get(name))]
    safe_refs = {name: _safe_ref(refs.get(name)) for name in REQUIRED_EVIDENCE_REFS}
    return missing, safe_refs


def _owner_handoff(payload: dict[str, Any], missing: list[str]) -> list[dict[str, str]]:
    # owner_handoff 输出短 action，指导下一步补材料而不是给机器人动作。
    handoff = []
    for item in _list(payload.get("owner_handoff")):
        data = _dict(item)
        owner = _safe_text(data.get("owner"))
        action = _safe_text(data.get("action"))
        if owner and action:
            handoff.append({"owner": owner, "action": action})
    if handoff:
        return handoff[:6]
    return [
        {
            "owner": "Hardware Infra Engineer",
            "action": f"fill reviewed config/evidence refs for {', '.join(missing[:4]) or 'future HIL-entry sensor config'}",
        }
    ]


def _next_required_evidence(missing: list[str], missing_evidence: list[str]) -> list[str]:
    # next_required_evidence 保持履约语言，明确还需要真实材料。
    if missing_evidence:
        return [
            "Attach source/procurement/install-wiring/power/calibration/HIL-entry material refs.",
            "Run this gate again with the same sanitized evidence_ref set.",
        ]
    if missing:
        return [
            "Parameterize sensor count, ToF channel count, thresholds, frame IDs, and safety policy.",
            "Keep Start/Dropoff/Cancel and HIL-entry disabled until reviewed evidence exists.",
        ]
    return [
        "Review the precheck summary with Robot diagnostics and mobile read-only consumers.",
        "Collect real bench/HIL-entry materials before claiming any hardware pass.",
    ]


def _safe_copy(
    status: str,
    sensor_summary: dict[str, Any],
    threshold_summary: dict[str, Any],
    frame_summary: dict[str, Any],
    safety_summary: dict[str, Any],
    evidence_refs: dict[str, str],
) -> dict[str, Any]:
    # safe_copy 是手机/diagnostics 白名单，不包含 raw artifact、串口、topic 或路径。
    return {
        "schema": f"{SUMMARY_SCHEMA}.safe_copy",
        "status": status,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "sensor count": sensor_summary.get("sensor count"),
        "tof_channel_count": sensor_summary.get("tof_channel_count"),
        "thresholds": threshold_summary.get("thresholds", {}),
        "frame IDs": frame_summary.get("frame IDs", {}),
        "safety policy": safety_summary.get("safety policy", {}),
        "safe_evidence_refs": evidence_refs,
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
        "copy_note": "software proof only; delivery_success=false; primary_actions_enabled=false; not_proven",
    }


def build_hardware_sensor_hil_entry_config_precheck(
    config_json: str | Path | None = None,
    vendor_index: str | Path = DEFAULT_VENDOR_INDEX,
    use_default_sample: bool = True,
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 sensor config JSON，生成 fail-closed HIL-entry config precheck artifact。"""

    config_path = Path(config_json) if config_json else None
    if config_path is None and use_default_sample:
        payload, read_issue = dict(DEFAULT_SAMPLE_CONFIG), ""
        config_ref = "builtin_default_sample_not_hardware_evidence"
    else:
        payload, read_issue = _read_json(config_path)
        config_ref = _safe_ref(config_path) if config_path else "missing"

    vendor_ref = _repo_ref(Path(vendor_index))
    missing: list[str] = []
    missing_evidence: list[str] = []

    if not read_issue and payload.get("schema", SCHEMA) != SCHEMA:
        status = BLOCKED_UNSUPPORTED_SCHEMA
    elif read_issue == "missing":
        status = BLOCKED_MISSING_CONFIG
    elif read_issue:
        status = BLOCKED_INVALID_JSON
    elif _has_unsafe_copy(payload):
        status = BLOCKED_UNSAFE_COPY
    elif _has_success_claim(payload):
        status = BLOCKED_SUCCESS_CLAIM
    else:
        config = _sensor_config(payload)
        sensor_missing, sensor_summary = _validate_sensor_counts(config)
        threshold_missing, threshold_summary = _validate_thresholds(payload)
        frame_missing, frame_summary = _validate_frame_ids(payload)
        safety_missing, safety_summary = _validate_safety_policy(payload)
        missing_evidence, evidence_refs = _validate_evidence_refs(payload)
        missing = sensor_missing + threshold_missing + frame_missing + safety_missing
        if missing:
            status = BLOCKED_MISSING_PARAMETERIZATION
        elif missing_evidence:
            status = BLOCKED_MISSING_EVIDENCE
        else:
            status = READY_STATUS

    if "sensor_summary" not in locals():
        sensor_summary = {"sensor count": "missing", "tof_channel_count": "missing", "roles": [], "parameterized": False}
        threshold_summary = {"thresholds": {}, "parameterized": False}
        frame_summary = {"frame IDs": {}, "parameterized": False}
        safety_summary = {"safety policy": {}, "parameterized": False}
        evidence_refs = {name: "missing" for name in REQUIRED_EVIDENCE_REFS}

    next_required = _next_required_evidence(missing, missing_evidence)
    owner_handoff = _owner_handoff(payload, missing + missing_evidence)
    safe_copy = _safe_copy(status, sensor_summary, threshold_summary, frame_summary, safety_summary, evidence_refs)

    summary = {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source_schema": SCHEMA,
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "source_evidence_boundary": EVIDENCE_BOUNDARY,
        "status": status,
        "hardware_sensor_hil_entry_config_precheck": status,
        "config_ref": config_ref,
        "vendor_source_boundary": {
            "source": vendor_ref,
            "coverage": "Orange Pi Zero 3 / WAVE ROVER / UART / camera vendor boundary only; no project LiDAR/ToF HIL proof",
            "lidar_tof_hil_proof": "not_proven",
        },
        "sensor_config_summary": sensor_summary,
        "threshold_summary": threshold_summary,
        "frame_id_summary": frame_summary,
        "safety_policy_summary": safety_summary,
        "missing_config": missing,
        "missing_evidence_refs": missing_evidence,
        "next_required_evidence": next_required,
        "owner_handoff": owner_handoff,
        "safe_copy": safe_copy,
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
        "boundary_note": "software proof only; delivery_success=false; primary_actions_enabled=false; not_proven",
    }

    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "generated_at": _utc_now(),
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "overall_status": status,
        "hardware_sensor_hil_entry_config_precheck": status,
        "config_ref": config_ref,
        "vendor_source_boundary": summary["vendor_source_boundary"],
        "parameterization_checks": {
            "sensor count": sensor_summary,
            "thresholds": threshold_summary,
            "frame IDs": frame_summary,
            "safety policy": safety_summary,
        },
        "evidence_refs": evidence_refs,
        "missing_config": missing,
        "missing_evidence_refs": missing_evidence,
        "next_required_evidence": next_required,
        "owner_handoff": owner_handoff,
        "safe_copy": safe_copy,
        "summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "real_hardware",
            "serial_uart",
            "ros_graph",
            "sensor_driver_runtime",
            "network",
            "hil",
            "delivery_execution",
        ],
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    return artifact, summary, 0 if status == READY_STATUS else 2


def _write_json(path: str, payload: dict[str, Any]) -> None:
    # 显式创建父目录，支持 sprint evidence bundle 输出。
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 只做 dependency-free PC gate；--help 也应可在无 ROS2 环境运行。
    parser = argparse.ArgumentParser(
        description=(
            "Generate trashbot.hardware_sensor_hil_entry_config_precheck.v1 "
            "software-proof artifact for sensor count, thresholds, frame IDs, safety policy, and evidence refs."
        )
    )
    parser.add_argument("--config-json", default="", help="Optional future HIL-entry sensor config JSON.")
    parser.add_argument(
        "--no-default-sample",
        action="store_true",
        help="Fail closed when --config-json is missing instead of using the built-in not-proven sample.",
    )
    parser.add_argument(
        "--vendor-index",
        default=str(DEFAULT_VENDOR_INDEX),
        help="Vendor index path used only to record source boundary.",
    )
    parser.add_argument("--output", default="", help="Write full hardware sensor HIL-entry config precheck artifact JSON.")
    parser.add_argument("--summary-output", default="", help="Write compact hardware sensor HIL-entry config precheck summary JSON.")
    parser.add_argument("--once-json", action="store_true", help="Print full artifact JSON to stdout.")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_hardware_sensor_hil_entry_config_precheck(
        args.config_json or None,
        vendor_index=args.vendor_index,
        use_default_sample=not args.no_default_sample,
    )
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"hardware_sensor_hil_entry_config_precheck: artifact_file:{Path(args.output).name if args.output else ''}")
        print(f"overall_status: {artifact['overall_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
