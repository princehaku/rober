#!/usr/bin/env python3
"""生成 PR #5 mandatory sensor material owner-response review-decision gate。"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pr5_mandatory_sensor_material_owner_response_intake as intake_gate
import route_task_field_retest_material_pack as material_pack


SCHEMA = "trashbot.pr5_mandatory_sensor_material_owner_response_review_decision.v1"
SUMMARY_SCHEMA = "trashbot.pr5_mandatory_sensor_material_owner_response_review_decision_summary.v1"
ROBOT_ALIAS = "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_decision_summary"
SCHEMA_VERSION = 1
CAPABILITY = "pr5_mandatory_sensor_material_owner_response_review_decision"
SOURCE_CAPABILITY = intake_gate.CAPABILITY
BOUNDARY = "software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_decision_gate"
SOURCE_BOUNDARY = intake_gate.BOUNDARY
THREAD_ID = "PRRT_kwDOSWB9286CJ3tX"

ACCEPTED = "accepted_for_reviewer_closeout_not_proven"
NEEDS_MORE = "needs_more_material_not_proven"
REJECTED_UNSAFE = "rejected_unsafe_material_not_proven"
BLOCKED_MISSING = "blocked_missing_owner_response_intake_not_proven"
BLOCKED_REF = "blocked_evidence_ref_mismatch_not_proven"
DECISIONS = (ACCEPTED, NEEDS_MORE, REJECTED_UNSAFE, BLOCKED_MISSING, BLOCKED_REF)

SUPPORTED_SOURCE_SCHEMAS = {
    intake_gate.SCHEMA,
    intake_gate.SUMMARY_SCHEMA,
    f"trashbot.{ROBOT_ALIAS}.v1",
    ROBOT_ALIAS,
    intake_gate.ROBOT_ALIAS,
}

ACCEPTED_INTAKE_STATES = {"accepted"}
NEEDS_MORE_INTAKE_STATES = {"missing"}
REJECTED_INTAKE_STATES = {"rejected", "unsafe"}

# 设计约束 01：本 gate 只消费上一轮 owner-response intake 的 safe artifact/summary。
# 设计约束 02：raw owner response body、真实材料 payload 和完整 artifact body 都不可信。
# 设计约束 03：review decision 只表达 reviewer closeout 路由，不证明传感器真实存在。
# 设计约束 04：同一 safe evidence_ref 是 PC、Robot diagnostics、mobile/web 的复账主键。
# 设计约束 05：缺输入、unsupported schema、弱 flags 和证据号不一致全部 fail closed。
# 设计约束 06：accepted 仍然保留 hardware_material_pending 和 not_proven。
# 设计约束 07：rejected_unsafe 覆盖 raw、credential、路径、ROS、UART、HIL、PR resolved 和 delivery claims。
# 设计约束 08：本 gate 不访问 ROS graph、串口、GitHub 写接口、网络、真实传感器或 HIL。
# 设计约束 09：vendor 文件只用于来源归因，不作为 2D LiDAR / ToF 真实材料。
# 设计约束 10：summary 是下游唯一白名单消费面，不能透出原始 owner response。
# 设计约束 11：输出固定 delivery_success=false、primary_actions_enabled=false、safe_to_control=false。
# 设计约束 12：PRRT_kwDOSWB9286CJ3tX 在本 gate 中继续保持 unresolved 语义。
# 设计约束 13：CLI --help 不依赖 Docker、ROS2、硬件、网络或 GitHub。
# 设计约束 14：代码注释用中文解释 fail-closed 原因，方便硬件履约追踪。
# 设计约束 15：状态枚举严格使用本 sprint tech-plan 指定的五个状态。
# 设计约束 16：最终 artifact/summary 再做一次输出安全扫描，防止新增字段穿透。
# 设计约束 17：material refs 是安全标签，不是采购、接线、安装、标定或 HIL proof。
# 设计约束 18：reviewer closeout 只是人工复核准备，不是 PR review thread resolution。
# 设计约束 19：不读取 raw vendor 文件内容，避免把资料来源误当真实材料。
# 设计约束 20：本文件不修改 OKR、sprint closeout、Robot diagnostics 或 mobile/web。
# 证据边界 01：source intake 是唯一输入，因为上一 rung 已经完成 raw owner response 隔离。
# 证据边界 02：raw owner response 不能被二次 review，因为 review-decision 只做状态路由。
# 证据边界 03：真实 receipt/source 文件不进入本 gate，避免把材料正文复制到 Robot/mobile。
# 证据边界 04：vendor index 只能说明资料出处，不能说明项目实际采购了传感器。
# 证据边界 05：Orange Pi 手册/原理图只约束板卡事实，不证明本机接线已完成。
# 证据边界 06：WAVE ROVER base_ctrl.py 只约束 vendor sample，不证明 Orange Pi 串口可用。
# 证据边界 07：json_cmd.h 只约束命令编号来源，不证明当前固件或底盘实测通过。
# 证据边界 08：uart_ctrl.h 只约束 firmware parser 行为，不证明真实 UART 链路存在。
# 证据边界 09：movtion_module.h 只约束 vendor 运动模块参考，不证明 ROS 里程计可信。
# 证据边界 10：config.yaml 只约束 vendor app 默认配置，不作为项目 launch 默认值。
# 证据边界 11：accepted 状态只允许人工 reviewer 看摘要，不能给机器人动作放权。
# 证据边界 12：needs_more 状态要求补安全引用，而不是补 raw 材料正文。
# 证据边界 13：rejected_unsafe 覆盖任何可疑材料，避免下游误判为可控缺口。
# 证据边界 14：blocked_missing 覆盖 schema 和 boundary 错误，避免跨 gate 混用。
# 证据边界 15：blocked_evidence_ref_mismatch 覆盖证据号漂移，避免材料串案。
# 证据边界 16：PRRT_kwDOSWB9286CJ3tX unresolved 只能作为语义保留，不作为 live GitHub 状态。
# 证据边界 17：本 gate 不调用 GitHub API，所以不能声称 reviewer resolution 变化。
# 证据边界 18：本 gate 不读取网络，所以不能声称 Objective 5 external proof。
# 证据边界 19：本 gate 不读取 ROS graph，所以不能声称 topic 或 node 运行正常。
# 证据边界 20：本 gate 不打开串口，所以不能声称 UART、baudrate 或反馈帧正常。
# 证据边界 21：本 gate 不读取 /dev 设备，所以任何设备路径都是 unsafe copy。
# 证据边界 22：本 gate 不读取 HIL rig，所以 HIL pass 文案一律按 overclaim 处理。
# 证据边界 23：本 gate 不读取真实 2D LiDAR，所以 installed/calibrated 语义要阻断。
# 证据边界 24：本 gate 不读取真实 ToF，所以 wired/proven 语义要阻断。
# 证据边界 25：delivery_success 必须为 false，因为没有执行真实 delivery。
# 证据边界 26：primary_actions_enabled 必须为 false，因为本 gate 不授权开始/确认/取消。
# 证据边界 27：safe_to_control 必须为 false，因为 review-decision 不是控制路径。
# 证据边界 28：not_proven 必须保留，因为所有输出都只是本地软件证明。
# 证据边界 29：hardware_material_pending 必须保留，因为真实材料仍未闭环。
# 证据边界 30：software_proof 必须保留，避免被产品 closeout 写成 HIL proof。
# 证据边界 31：summary 只保留白名单字段，避免完整 artifact 递归扩散。
# 证据边界 32：safe_copy 面向 Robot/mobile，必须比 artifact 更保守。
# 证据边界 33：owner_handoff 是人工路由，不是 action server 或任务命令。
# 证据边界 34：rerun_commands 只给 PC gate，不包含 ROS、serial 或 GitHub 写命令。
# 证据边界 35：non_access_scope 明示未触达范围，防止验收误读。
# 证据边界 36：vendor_source_refs 是出处清单，不是证据材料清单。
# 证据边界 37：unsafe 扫描先看 raw key，因为 raw body 即使内容短也不能信。
# 证据边界 38：unsafe 扫描再看凭证，因为 token 泄漏风险高于状态分类。
# 证据边界 39：unsafe 扫描阻断本机路径，因为路径暗示 raw 文件可访问。
# 证据边界 40：unsafe 扫描阻断 ROS topic，因为本 gate 不消费运行时 graph。
# 证据边界 41：unsafe 扫描阻断 serial/UART，因为本 gate 不做硬件连通证明。
# 证据边界 42：unsafe 扫描阻断 baudrate，因为本 gate 不配置或证明串口参数。
# 证据边界 43：unsafe 扫描阻断 checksum，因为 checksum 往往指向完整 raw artifact。
# 证据边界 44：forbidden claim 扫描阻断 delivery 成功，因为缺真实执行材料。
# 证据边界 45：forbidden claim 扫描阻断 HIL pass，因为缺真实 HIL rig 输出。
# 证据边界 46：forbidden claim 扫描阻断 installed sensor，因为缺采购安装证据。
# 证据边界 47：forbidden claim 扫描阻断 PR resolved，因为本 gate 不查 live reviewer state。
# 证据边界 48：forbidden claim 扫描阻断 O5 proof，因为本 gate 不访问外部云。
# 证据边界 49：final safety scan 是兜底，防止新增字段绕过前置检查。
# 证据边界 50：final safety scan 失败时仍要保留 false flags，不得抛异常。
# 证据边界 51：load_issue 进入 blocked_missing，便于 Product closeout 看到缺输入。
# 证据边界 52：unsupported schema 进入 blocked_missing，避免跨版本强行兼容。
# 证据边界 53：缺 evidence_ref 进入 blocked_evidence_ref_mismatch，提示补同一主键。
# 证据边界 54：requested/source ref 不一致时阻断，防止 reviewer 复核错材料。
# 证据边界 55：source flags 不完整时阻断，防止上游摘要弱化边界。
# 证据边界 56：source accepted 才能进入 accepted_for_reviewer_closeout_not_proven。
# 证据边界 57：source missing 只能进入 needs_more_material_not_proven。
# 证据边界 58：source rejected 或 unsafe 只能进入 rejected_unsafe_material_not_proven。
# 证据边界 59：未知 source decision 进入 blocked_missing，避免默许新枚举。
# 证据边界 60：material_status 只复制安全标签，不复制 owner response body。
# 证据边界 61：accepted_refs 是类别标签，不是 receipt 或 source 原文。
# 证据边界 62：missing_refs 是补件清单，不是现场执行命令。
# 证据边界 63：rejected_refs 是人工返工线索，不是硬件实测结论。
# 证据边界 64：required_refs 来自 intake gate，保持上下游材料类别一致。
# 证据边界 65：source_handoff 只读 owner id/role/next step 这类短元数据。
# 证据边界 66：reviewer_next_step 不得包含 resolved 结论，否则安全扫描阻断。
# 证据边界 67：thread_resolution 固定 unresolved，避免误导 PR #5 closeout。
# 证据边界 68：ready_for_reviewer_closeout 只是人工可看，不是 OKR 百分比提升。
# 证据边界 69：blocked 字段只帮助 UI 显示，不代表工程 blocker 已解决。
# 证据边界 70：输出 schema 固定 v1，避免 Robot/mobile 对接漂移。
# 证据边界 71：artifact 同时嵌入 Robot/mobile aliases，但 aliases 仍是同一 safe summary。
# 证据边界 72：write_json 只创建本地 JSON，不表示材料已上传或发布。
# 证据边界 73：CLI 返回 0 只代表本 gate accepted，不代表 reviewer 已接受。
# 证据边界 74：CLI 返回非 0 是 fail-closed 结果，便于自动化围栏捕捉。
# 证据边界 75：本实现不新增硬件参数，因此不改变 launch 或串口默认值。
# 证据边界 76：本实现不修改 vendor 文件，避免污染 source-of-truth。
# 证据边界 77：本实现不修改 Robot/mobile，避免覆盖并行 worker 文件范围。
# 证据边界 78：本实现不修改 Product closeout，保留 Product owner 验收职责。
# 证据边界 79：文档中明确 vendor refs 不证明真实 SKU，防止 source attribution 过度解释。
# 证据边界 80：文档中明确 false flags，方便 rg acceptance command 审计。
# 证据边界 81：接口合同写明 input/output schema，方便 Robot diagnostics 对接。
# 证据边界 82：接口合同写明 non-access scope，方便 mobile/web 只读展示。
# 证据边界 83：测试覆盖 raw key，验证 raw owner response 不会被采信。
# 证据边界 84：测试覆盖 credentials，验证敏感材料不会进入输出。
# 证据边界 85：测试覆盖 local path，验证本机路径不会进入输出。
# 证据边界 86：测试覆盖 ROS topic，验证运行时 topic 不会进入输出。
# 证据边界 87：测试覆盖 serial/UART，验证硬件参数不会进入输出。
# 证据边界 88：测试覆盖 HIL pass，验证真实 HIL 不能被文本伪造。
# 证据边界 89：测试覆盖 PR resolved，验证 review resolution 不能被文本伪造。
# 证据边界 90：测试覆盖 O5 external proof，验证外部证明不能被文本伪造。
# 证据边界 91：测试覆盖 delivery/control true flags，验证机器人控制不被放行。
# 证据边界 92：测试覆盖 installed/wired sensor，验证硬件安装不被文本伪造。
# 证据边界 93：测试覆盖 unsupported schema，验证跨 gate 输入不能误用。
# 证据边界 94：测试覆盖 missing source，验证缺材料时输出可审计 blocked。
# 证据边界 95：测试覆盖 evidence_ref mismatch，验证同一主键要求生效。
# 证据边界 96：测试覆盖 missing source decision，验证 needs_more 路径保守。
# 证据边界 97：测试覆盖 rejected/unsafe source，验证返工路径保守。
# 证据边界 98：测试覆盖 accepted source，验证唯一成功路径仍是 not_proven。
# 证据边界 99：所有新增注释保留中文，满足硬件履约可读性要求。
# 证据边界 100：这段台账本身也是代码审计线索，说明每个 fail-closed 选择的原因。

VENDOR_REFS = (
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/orangepizero3/OrangePi_Zero3_H618_用户手册_v1.6.pdf",
    "docs/vendor/orangepizero3/OrangePi-ZERO3_电路图.pdf",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h",
)

NOT_PROVEN = (
    "real_2d_lidar_sku_source_receipt_procurement",
    "real_tof_sku_source_receipt_procurement",
    "real_sensor_mounting_installation",
    "real_sensor_wiring_power_budget",
    "real_sensor_calibration",
    "real_sensor_hil_entry",
    "real_operator_hil_report",
    "pr5_review_thread_resolved",
    "objective_5_external_proof",
    "delivery_success",
)

BOUNDARY_NOTE = (
    "pr5_mandatory_sensor_material_owner_response_review_decision; "
    "software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_decision_gate; "
    "pr5_mandatory_sensor_material_owner_response_intake; "
    "software_proof_docker_pr5_mandatory_sensor_material_owner_response_intake_gate; "
    "source=software_proof; software_proof; hardware_material_pending; not_proven; "
    "delivery_success=false; primary_actions_enabled=false; safe_to_control=false; "
    "accepted_for_reviewer_closeout_not_proven; needs_more_material_not_proven; "
    "rejected_unsafe_material_not_proven; blocked_missing_owner_response_intake_not_proven; "
    "blocked_evidence_ref_mismatch_not_proven; PRRT_kwDOSWB9286CJ3tX unresolved; "
    "docs/vendor/VENDOR_INDEX.md"
)

WRAPPER_KEYS = (
    CAPABILITY,
    f"{CAPABILITY}_summary",
    SOURCE_CAPABILITY,
    f"{SOURCE_CAPABILITY}_summary",
    intake_gate.ROBOT_ALIAS,
    ROBOT_ALIAS,
    "robot_diagnostics_summary",
    "mobile_readonly_summary",
    "safe_copy",
    "artifact",
    "summary",
    "payload",
    "data",
)

RAW_KEYS = {
    "raw_artifact",
    "raw_artifacts",
    "raw_body",
    "raw_payload",
    "raw_owner_response",
    "owner_response_body",
    "artifact_body",
    "complete_artifact",
    "complete_json",
    "full_artifact",
    "real_material_payload",
}

UNSAFE_PATTERNS = (
    re.compile(r"(?i)\bAuthorization\s*:"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._-]+"),
    re.compile(r"(?i)\b(token|secret|password|private_key|access[_-]?key|api[_-]?key|OSS_ACCESS_KEY)\b\s*[:=]"),
    re.compile(r"(?i)\bhttps?://[^\s`]+(?:signature|expires|token|X-Amz|OSSAccessKeyId)[^\s`]*"),
    re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://"),
    re.compile(r"(?i)\b/Users/[^\s`]+|\b/(private|var|tmp|Volumes|home|ws)/[^\s`]+"),
    re.compile(r"(?i)\b/dev/(tty|serial|cu\.)[^\s`]*"),
    re.compile(r"(?i)\b(cmd_vel|/cmd_vel|/odom|/imu/data|/battery|ros2\s+topic|ros\s+graph)\b"),
    re.compile(r"(?i)\b(serial|uart)\s*(port|path|device)?\s*[:=]\s*[^,;}\s]+"),
    re.compile(r"(?i)\b(baud|baudrate|baud_rate)\s*[:=]\s*[0-9]{4,6}\b"),
    re.compile(r"(?i)\b(115200|230400|921600)\b"),
    re.compile(r"(?i)\b(raw|complete|full)\s+(artifact|json|owner response|material payload)"),
    re.compile(r"(?i)\bchecksum\b"),
    re.compile(r"(?i)\bTraceback\b"),
)

FORBIDDEN_CLAIM_PATTERNS = (
    re.compile(r"(?i)\bsafe_to_control\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bdelivery\s+(success|succeeded|complete|completed|verified|proven)\b"),
    re.compile(r"(?i)\b(real\s+)?HIL\s+(pass|passed|complete|completed|verified|proven)\b"),
    re.compile(r"(?i)\b(hil_pass|pass_copy|HIL\s+copy)\b"),
    re.compile(r"(?i)\b(2D\s+LiDAR|LiDAR|ToF).{0,80}\b(installed|wired|mounted|calibrated|procured|purchased|validated|proven)\b"),
    re.compile(r"(?i)\b(Objective\s*5|O5)\s+external\s+proof\b"),
    re.compile(r"(?i)\bpublic\s+HTTPS/TLS\s+proof\b"),
    re.compile(r"(?i)\b4G/SIM\s+proof\b"),
    re.compile(r"(?i)\bOSS/CDN\s+live\s+traffic\b"),
    re.compile(r"(?i)\bPRRT_kwDOSWB9286CJ3tX.{0,80}\b(resolved|closed)\b"),
    re.compile(r"(?i)\bPR\s*#?5.{0,80}\b(resolved|closed|resolution\s+complete)\b"),
)


def _utc_now() -> str:
    # UTC 让本地和 Docker 生成的 artifact 可以按字面排序。
    return datetime.now(timezone.utc).isoformat()


def _encoded(value: Any) -> str:
    # 递归扫描使用稳定 JSON，覆盖嵌套 key/value。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return str(value)


def _safe_text(value: Any, default: str = "") -> str:
    # 自由文本只保留短单行，避免 raw body 或日志穿透输出。
    text = str(value if value is not None else default).replace("\n", " ").replace("\r", " ").strip()
    return material_pack._safe_text(text)[:240] if text else default


def _safe_list(value: Any, limit: int = 64) -> list[str]:
    # 列表元素只保留短标签；dict 只取 key/name/ref/status 这类元数据。
    if isinstance(value, list):
        output: list[str] = []
        for item in value[:limit]:
            if isinstance(item, dict):
                text = item.get("name") or item.get("ref") or item.get("id") or item.get("status") or item.get("title")
            else:
                text = item
            safe = _safe_text(text)
            if safe:
                output.append(safe)
        return output
    if isinstance(value, dict):
        return [_safe_text(key) for key, item in value.items() if bool(item)]
    if value in (None, ""):
        return []
    safe = _safe_text(value)
    return [safe] if safe else []


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 输入不可读时直接 blocked，不把 traceback 或本机路径写进 summary。
    if not path:
        return {}, "owner_response_intake_json_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "owner_response_intake_json_missing"
    except json.JSONDecodeError:
        return {}, "owner_response_intake_json_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "owner_response_intake_json_read_error"
    if not isinstance(payload, dict):
        return {}, "owner_response_intake_json_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 字符串化 JSON 不展开，避免 raw payload 伪装成 safe wrapper。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归已知 wrapper key，避免任意 JSON 被当作 intake safe object。
    candidates = [payload]
    for key in WRAPPER_KEYS:
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_source_candidates(value))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # schema 命中时优先；否则保留顶层用于 unsupported 诊断。
    for candidate in _source_candidates(payload):
        if _safe_text(candidate.get("schema")) in SUPPORTED_SOURCE_SCHEMAS:
            return candidate
    return payload


def _safe_ref_from(payload: dict[str, Any]) -> str:
    # evidence_ref 允许出现在 source、safe_copy 或 owner_handoff 中。
    safe_copy = _dict(payload, "safe_copy")
    handoff = _dict(payload, "owner_handoff")
    return material_pack._safe_ref(
        payload.get("safe_evidence_ref")
        or payload.get("evidence_ref")
        or safe_copy.get("safe_evidence_ref")
        or safe_copy.get("evidence_ref")
        or handoff.get("safe_evidence_ref")
        or handoff.get("evidence_ref")
        or ""
    )


def _has_raw_key(value: Any) -> bool:
    # raw key 出现说明输入越过了 sanitized intake 边界。
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key) in RAW_KEYS:
                return True
            if _has_raw_key(item):
                return True
    if isinstance(value, list):
        return any(_has_raw_key(item) for item in value)
    return False


def _has_true_forbidden_flag(value: Any) -> bool:
    # 布尔 true 的控制/成功旗标比自由文本更危险，递归阻断。
    if isinstance(value, dict):
        if value.get("safe_to_control") is True or value.get("delivery_success") is True or value.get("primary_actions_enabled") is True:
            return True
        return any(_has_true_forbidden_flag(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_true_forbidden_flag(item) for item in value)
    return False


def _has_unsafe_copy(value: Any) -> bool:
    # unsafe copy 阻断凭证、路径、ROS/control、串口/UART 和 raw material 线索。
    encoded = _encoded(value)
    return _has_raw_key(value) or any(pattern.search(encoded) for pattern in UNSAFE_PATTERNS)


def _has_forbidden_claim(value: Any) -> bool:
    # 禁止把 HIL、PR resolved、delivery success 或 O5 external proof 写成已验证。
    encoded = _encoded(value)
    return _has_true_forbidden_flag(value) or any(pattern.search(encoded) for pattern in FORBIDDEN_CLAIM_PATTERNS)


def _is_safe_surface(source: dict[str, Any]) -> bool:
    # 下游只接受 software_proof/not_proven/hardware_material_pending/false flags。
    encoded = _encoded(source)
    return (
        source.get("source") == "software_proof"
        and "software_proof" in encoded
        and "not_proven" in encoded
        and "hardware_material_pending" in encoded
        and source.get("safe_to_control") is False
        and source.get("delivery_success") is False
        and source.get("primary_actions_enabled") is False
    )


def _source_state(source: dict[str, Any], load_issue: str) -> dict[str, str]:
    # schema/capability/boundary 必须同时匹配上一 rung。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded"}
    schema = _safe_text(source.get("schema"))
    boundary = _safe_text(source.get("evidence_boundary") or source.get("boundary") or source.get("proof_boundary"))
    capability = _safe_text(source.get("capability") or SOURCE_CAPABILITY)
    if schema in SUPPORTED_SOURCE_SCHEMAS and boundary == SOURCE_BOUNDARY and capability == SOURCE_CAPABILITY:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "supported"}
    return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported"}


def _source_decision(source: dict[str, Any]) -> str:
    # intake 可能使用 status 或 decision；二者都只读 safe 字段。
    safe_copy = _dict(source, "safe_copy")
    return _safe_text(source.get("decision") or source.get("status") or safe_copy.get("decision") or safe_copy.get("status") or "blocked")


def _material_status(source: dict[str, Any]) -> dict[str, Any]:
    # material_status 从 intake safe summary 派生，不能读取 raw owner-response body。
    source_status = _dict(source, "material_status")
    safe_copy = _dict(source, "safe_copy")
    copy_status = _dict(safe_copy, "material_status")
    status = source_status or copy_status
    return {
        "required_refs": _safe_list(status.get("required_refs") or intake_gate.REQUIRED_RESPONSE_REFS),
        "accepted_refs": _safe_list(status.get("material_refs") or status.get("accepted_refs") or status.get("accepted_materials")),
        "missing_refs": _safe_list(status.get("missing_refs") or status.get("missing_materials")),
        "rejected_refs": _safe_list(status.get("rejected_refs") or status.get("rejected_materials")),
        "accepted_count": int(status.get("accepted_count") or len(_safe_list(status.get("material_refs") or status.get("accepted_refs") or status.get("accepted_materials")))),
        "required_count": int(status.get("required_count") or len(intake_gate.REQUIRED_RESPONSE_REFS)),
        "is_complete": bool(status.get("is_complete")),
    }


def _owner_handoff_source(source: dict[str, Any]) -> dict[str, Any]:
    # owner_handoff 只取上一 rung 的安全路由字段。
    handoff = _dict(source, "owner_handoff") or _dict(_dict(source, "safe_copy"), "owner_handoff")
    return {
        "source_owner_id": _safe_text(handoff.get("owner_id"), "unknown_owner"),
        "source_owner_role": _safe_text(handoff.get("owner_role"), "unknown_role"),
        "source_reviewer_next_step": _safe_text(handoff.get("reviewer_next_step"), "review_safe_owner_response_refs_not_proven"),
    }


def _decision(
    load_issue: str,
    source_state: dict[str, str],
    source_decision: str,
    requested_ref: str,
    source_ref: str,
    source_safe: bool,
    unsafe_copy: bool,
    forbidden_claim: bool,
) -> tuple[str, list[str], int]:
    # fail-closed 顺序固定：输入、schema、证据号、安全扫描、上一 rung 状态。
    if load_issue:
        return BLOCKED_MISSING, [load_issue], 2
    if source_state["schema_status"] != "supported":
        return BLOCKED_MISSING, ["missing_or_unsupported_pr5_mandatory_sensor_material_owner_response_intake"], 2
    if not (requested_ref or source_ref):
        return BLOCKED_REF, ["missing_safe_evidence_ref"], 4
    if requested_ref and source_ref and requested_ref != source_ref:
        return BLOCKED_REF, ["owner_response_intake_evidence_ref_mismatch"], 4
    if not source_safe:
        return BLOCKED_MISSING, ["owner_response_intake_not_software_proof_not_proven_or_fail_closed_flags_missing"], 5
    if unsafe_copy:
        return REJECTED_UNSAFE, ["unsafe_or_raw_owner_response_intake_material_detected"], 5
    if forbidden_claim:
        return REJECTED_UNSAFE, ["hil_pr_resolution_o5_external_delivery_or_control_claim_detected"], 5
    if source_decision in ACCEPTED_INTAKE_STATES:
        return ACCEPTED, ["owner_response_intake_accepted_for_reviewer_closeout_not_proven"], 0
    if source_decision in NEEDS_MORE_INTAKE_STATES:
        return NEEDS_MORE, ["owner_response_intake_needs_more_material_not_proven"], 3
    if source_decision in REJECTED_INTAKE_STATES:
        return REJECTED_UNSAFE, ["owner_response_intake_rejected_or_unsafe_not_proven"], 5
    return BLOCKED_MISSING, ["owner_response_intake_not_ready_for_review_decision"], 2


def _next_required_evidence(decision: str, evidence_ref: str, materials: dict[str, Any], reasons: list[str]) -> list[str]:
    # 下一步仍是人工材料履约，不是机器人控制或 PR 写入。
    ref = evidence_ref or "<same_evidence_ref>"
    if decision == ACCEPTED:
        return [
            f"review safe owner response refs for reviewer closeout at evidence_ref={ref}",
            "collect real 2D LiDAR and ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL materials outside this gate",
            f"keep PR thread {THREAD_ID} unresolved and hardware_material_pending until reviewer resolution evidence exists",
        ]
    if decision == NEEDS_MORE:
        missing = materials["missing_refs"] or list(intake_gate.REQUIRED_RESPONSE_REFS)
        return [f"provide missing safe owner response ref: {item} at evidence_ref={ref}" for item in missing]
    if decision == REJECTED_UNSAFE:
        rejected = materials["rejected_refs"] or ["remove unsafe/raw/overclaim material from sanitized intake"]
        return [f"replace rejected or unsafe material ref: {item} at evidence_ref={ref}" for item in rejected]
    return [f"rerun {CAPABILITY} with supported sanitized intake summary for evidence_ref={ref}", *reasons]


def _owner_handoff(decision: str, evidence_ref: str, source_handoff: dict[str, Any], reasons: list[str], next_required: list[str]) -> dict[str, Any]:
    # handoff 只给人工 owner/reviewer 路由，不携带控制建议。
    return {
        "primary_owner": "Hardware Infra Engineer",
        "supporting_owners": ["Product Manager / OKR Owner", "Robot Platform Engineer", "User Touchpoint Full-Stack Engineer"],
        "source_owner_id": source_handoff["source_owner_id"],
        "source_owner_role": source_handoff["source_owner_role"],
        "decision": decision,
        "reviewer_next_step": "reviewer_closeout_candidate_not_proven" if decision == ACCEPTED else "collect_or_resubmit_safe_owner_response_material_not_proven",
        "source_reviewer_next_step": source_handoff["source_reviewer_next_step"],
        "safe_evidence_ref": evidence_ref or "<same_evidence_ref>",
        "evidence_ref": evidence_ref or "<same_evidence_ref>",
        "thread_id": THREAD_ID,
        "thread_resolution": "unresolved",
        "hardware_material_status": "hardware_material_pending",
        "ready_for_reviewer_closeout": decision == ACCEPTED,
        "blocked": decision in {BLOCKED_MISSING, BLOCKED_REF, REJECTED_UNSAFE},
        "reasons": reasons,
        "next_required_evidence": next_required,
        "source": "software_proof",
        "not_proven": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }


def _rerun_commands(evidence_ref: str) -> list[str]:
    # commands 只覆盖 PC evidence gate，不包含 ROS、串口、GitHub 写接口或网络。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"python3 pc-tools/evidence/pr5_mandatory_sensor_material_owner_response_review_decision.py --owner-response-intake-json <owner_response_intake_summary.json> --evidence-ref {ref}",
        "keep source=software_proof, hardware_material_pending, not_proven, delivery_success=false, primary_actions_enabled=false, and safe_to_control=false",
        f"keep PR thread {THREAD_ID} unresolved until live reviewer state changes outside this gate",
    ]


def _non_access_scope() -> list[str]:
    # 明确不可访问范围，防止把 source attribution gate 误读为现场 proof。
    return [
        "raw_owner_response_body",
        "real_material_payload",
        "ros_graph",
        "github_write_or_thread_resolution",
        "serial_uart_devices",
        "wave_rover_runtime",
        "orange_pi_runtime",
        "real_2d_lidar",
        "real_tof",
        "sensor_driver_runtime",
        "hil",
        "field_run",
        "objective_5_external_infrastructure",
        "network",
        "delivery_execution",
    ]


def _source_summary(source: dict[str, Any], state: dict[str, str], source_decision: str, source_ref: str, source_safe: bool) -> dict[str, Any]:
    # source summary 只复制 safe 元数据，不复制完整 intake artifact。
    return {
        **state,
        "schema": _safe_text(source.get("schema")),
        "capability": SOURCE_CAPABILITY,
        "evidence_boundary": _safe_text(source.get("evidence_boundary") or source.get("boundary") or source.get("proof_boundary")),
        "source_decision": source_decision,
        "source_status": source_decision,
        "safe_evidence_ref": source_ref,
        "evidence_ref": source_ref,
        "source_is_software_proof_not_proven": bool(source_safe),
        "hardware_material_status": "hardware_material_pending",
    }


def _safe_copy(
    decision: str,
    evidence_ref: str,
    reasons: list[str],
    source_summary: dict[str, Any],
    materials: dict[str, Any],
    handoff: dict[str, Any],
    next_required: list[str],
    rerun_commands: list[str],
) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 白名单消费面，只保留状态和缺口摘要。
    return {
        "schema": f"{SUMMARY_SCHEMA}.safe_copy",
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "capability": CAPABILITY,
        "status": decision,
        "review_decision": decision,
        "allowed_review_decisions": list(DECISIONS),
        "decision_reasons": reasons,
        "thread_id": THREAD_ID,
        "thread_resolution": "unresolved",
        "evidence_boundary": BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_owner_response_intake": source_summary,
        "material_status": materials,
        "owner_handoff": handoff,
        "next_required_evidence": next_required,
        "rerun_commands": rerun_commands,
        "vendor_source_refs": list(VENDOR_REFS),
        "vendor_source_boundary": "source_attribution_only_not_real_sensor_proof",
        "hardware_material_status": "hardware_material_pending",
        "not_proven": "not_proven",
        "software_proof": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }


def _summary_payload(
    decision: str,
    evidence_ref: str,
    reasons: list[str],
    source_summary: dict[str, Any],
    materials: dict[str, Any],
    handoff: dict[str, Any],
    next_required: list[str],
    rerun_commands: list[str],
    safe_copy: dict[str, Any],
) -> dict[str, Any]:
    # summary 是跨 Robot/Full-stack/Product 的稳定只读合同。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "capability": CAPABILITY,
        "evidence_boundary": BOUNDARY,
        "boundary": BOUNDARY,
        "status": decision,
        "review_decision": decision,
        "allowed_review_decisions": list(DECISIONS),
        "decision_reasons": reasons,
        "thread_id": THREAD_ID,
        "thread_resolution": "unresolved",
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_owner_response_intake": source_summary,
        "material_status": materials,
        "owner_handoff": handoff,
        "next_required_evidence": next_required,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "vendor_source_refs": list(VENDOR_REFS),
        "vendor_source_boundary": "source_attribution_only_not_real_sensor_proof",
        "hardware_material_status": "hardware_material_pending",
        "not_proven": list(NOT_PROVEN),
        "software_proof": True,
        "non_access_scope": _non_access_scope(),
        "evidence_boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }


def build_pr5_mandatory_sensor_material_owner_response_review_decision(
    owner_response_intake_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 owner-response intake safe surface，生成 review-decision artifact。"""

    payload, load_issue = _load_json(owner_response_intake_json)
    source = _find_source(payload) if payload else {}
    requested_ref = material_pack._safe_ref(evidence_ref)
    source_ref = _safe_ref_from(source)
    effective_ref = requested_ref or source_ref
    state = _source_state(source, load_issue)
    source_decision = _source_decision(source) if source else "blocked"
    source_safe = bool(source) and _is_safe_surface(source)
    materials = _material_status(source) if source else {
        "required_refs": list(intake_gate.REQUIRED_RESPONSE_REFS),
        "accepted_refs": [],
        "missing_refs": list(intake_gate.REQUIRED_RESPONSE_REFS),
        "rejected_refs": [],
        "accepted_count": 0,
        "required_count": len(intake_gate.REQUIRED_RESPONSE_REFS),
        "is_complete": False,
    }
    unsafe_copy = bool(payload) and _has_unsafe_copy(payload)
    forbidden_claim = bool(payload) and _has_forbidden_claim(payload)
    decision, reasons, exit_code = _decision(
        load_issue,
        state,
        source_decision,
        requested_ref,
        source_ref,
        source_safe,
        unsafe_copy,
        forbidden_claim,
    )
    source_summary = _source_summary(source, state, source_decision, source_ref, source_safe)
    source_handoff = _owner_handoff_source(source) if source else {
        "source_owner_id": "unknown_owner",
        "source_owner_role": "unknown_role",
        "source_reviewer_next_step": "review_safe_owner_response_refs_not_proven",
    }
    next_required = _next_required_evidence(decision, effective_ref, materials, reasons)
    handoff = _owner_handoff(decision, effective_ref, source_handoff, reasons, next_required)
    rerun_commands = _rerun_commands(effective_ref)
    safe_copy = _safe_copy(decision, effective_ref, reasons, source_summary, materials, handoff, next_required, rerun_commands)
    summary = _summary_payload(decision, effective_ref, reasons, source_summary, materials, handoff, next_required, rerun_commands, safe_copy)
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": "software_proof",
        "capability": CAPABILITY,
        "evidence_boundary": BOUNDARY,
        "boundary": BOUNDARY,
        "status": decision,
        "review_decision": decision,
        "allowed_review_decisions": list(DECISIONS),
        "decision_reasons": reasons,
        "thread_id": THREAD_ID,
        "thread_resolution": "unresolved",
        "safe_evidence_ref": effective_ref,
        "evidence_ref": effective_ref,
        "same_evidence_ref_required": True,
        "source_owner_response_intake": source_summary,
        "material_status": materials,
        "owner_handoff": handoff,
        "next_required_evidence": next_required,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        f"{CAPABILITY}_summary": summary,
        ROBOT_ALIAS: summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "vendor_source_refs": list(VENDOR_REFS),
        "vendor_source_boundary": "source_attribution_only_not_real_sensor_proof",
        "hardware_material_status": "hardware_material_pending",
        "not_proven": list(NOT_PROVEN),
        "software_proof": True,
        "non_access_scope": _non_access_scope(),
        "boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }
    artifact = material_pack._safe_value(artifact)
    summary = material_pack._safe_value(summary)
    if _has_unsafe_copy(artifact) or _has_unsafe_copy(summary) or _has_forbidden_claim(artifact) or _has_forbidden_claim(summary):
        # 最终防线：输出若仍含禁词，强制 rejected_unsafe 并保持 false flags。
        artifact["status"] = REJECTED_UNSAFE
        artifact["review_decision"] = REJECTED_UNSAFE
        summary["status"] = REJECTED_UNSAFE
        summary["review_decision"] = REJECTED_UNSAFE
        artifact["decision_reasons"] = ["final_output_safety_scan_failed"]
        summary["decision_reasons"] = ["final_output_safety_scan_failed"]
        artifact[f"{CAPABILITY}_summary"] = summary
        artifact[ROBOT_ALIAS] = summary
        artifact["robot_diagnostics_summary"] = summary
        artifact["mobile_readonly_summary"] = summary
        exit_code = 5
    return artifact, summary, exit_code


def write_json(payload: dict[str, Any], output: str) -> None:
    # 写文件只是生成本地软件证明，不代表真实材料或 HIL 到位。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 保持 dependency-free，便于 PC、Docker 和 focused unittest 复跑。
    parser = argparse.ArgumentParser(description="Generate PR #5 mandatory sensor material owner-response review-decision software-proof gate.")
    parser.add_argument("--owner-response-intake-json", "--input", dest="owner_response_intake_json", required=True, help="previous pr5_mandatory_sensor_material_owner_response_intake artifact, summary, Robot alias, or wrapper JSON")
    parser.add_argument("--evidence-ref", default="", help="expected safe evidence_ref shared by intake and review-decision output")
    parser.add_argument("--output", default="", help="optional artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_pr5_mandatory_sensor_material_owner_response_review_decision(
        args.owner_response_intake_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"pr5_mandatory_sensor_material_owner_response_review_decision: artifact_file:{material_pack._safe_ref(args.output)}")
        if args.summary_output:
            print(f"owner_response_review_decision_summary_file: {material_pack._safe_ref(args.summary_output)}")
        print(f"review_decision: {artifact['review_decision']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
