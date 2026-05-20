#!/usr/bin/env python3
"""生成 PR #5 mandatory sensor source-alignment 的 fail-closed 软件证明。"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# 设计约束 01：本 gate 回答 PR #5 mandatory sensor source alignment，不回答真实采购。
# 设计约束 02：本 gate 必须固定 thread id，避免把其他 review thread 混入硬件事实。
# 设计约束 03：本 gate 只读 repo 文档和 vendor/source 文件，不访问 GitHub 写接口。
# 设计约束 04：本 gate 不读取 ROS graph，避免把运行态误写成 source proof。
# 设计约束 05：本 gate 不打开串口、I2C、USB 或任何硬件总线。
# 设计约束 06：source=software_proof 是不可覆盖字段，不能被输入材料升级。
# 设计约束 07：evidence boundary 必须稳定，供 Robot/mobile/Product 同名消费。
# 设计约束 08：ready 状态只代表 source alignment ready_not_proven。
# 设计约束 09：2D LiDAR 和 ToF 始终保持 hardware_material_pending。
# 设计约束 10：not_proven 必须显式覆盖采购、安装、标定、HIL 和 thread resolved。
# 设计约束 11：safe_to_control=false 必须进入 artifact 和 summary。
# 设计约束 12：delivery_success=false 必须进入 artifact 和 summary。
# 设计约束 13：primary_actions_enabled=false 必须进入 artifact 和 summary。
# 设计约束 14：Orange Pi manual/schematic 只作为本地资料边界引用。
# 设计约束 15：Orange Pi PDF 存在性不等于读取到真实上车 GPIO 连接。
# 设计约束 16：WAVE ROVER README 只说明 vendor app 和 UART JSON 来源。
# 设计约束 17：base_ctrl.py 中的 raw serial 示例不能进入输出 artifact。
# 设计约束 18：base_ctrl.py 的 lidar parser 是 vendor-app context，不是项目 LiDAR 采购。
# 设计约束 19：config.yaml 的 use_lidar=false 是 vendor app 默认，不是项目传感器验收。
# 设计约束 20：json_cmd.h 只证明 command id 来源，不证明本机固件已刷入。
# 设计约束 21：uart_ctrl.h 只证明下位机 handler 来源，不证明 UART 链路连通。
# 设计约束 22：movtion_module.h 只证明运动控制源码边界，不证明 HIL 通过。
# 设计约束 23：source_refs 输出必须是 repo 相对路径，避免泄漏本机绝对路径。
# 设计约束 24：summary 只保留白名单字段，供 diagnostics/mobile 只读展示。
# 设计约束 25：safe_copy 不能包含 raw vendor 源码、串口路径或完整 artifact。
# 设计约束 26：missing_materials 是履约缺口，不因 source alignment 通过而减少。
# 设计约束 27：next_required_evidence 必须指向真实材料回填。
# 设计约束 28：owner_handoff 必须说明 Hardware 仍需真实材料和 reviewer resolution。
# 设计约束 29：default hardware section 必须和 target sensing baseline 分开解析。
# 设计约束 30：Default Hardware Set 出现 LiDAR/ToF 时应暴露为风险。
# 设计约束 31：target baseline 可以写 product target，但不能写已安装。
# 设计约束 32：ToF channel 目标必须是 product target pending validation。
# 设计约束 33：2D LiDAR role 必须等待 procurement/calibration/HIL evidence。
# 设计约束 34：Monocular camera 是 current semantic evidence sensor。
# 设计约束 35：Vendor index 必须仍是 source entrypoint。
# 设计约束 36：Vendor index 缺 Source Of Truth Order 应 fail closed。
# 设计约束 37：Vendor index 缺 Orange Pi coverage 应 fail closed。
# 设计约束 38：Vendor index 缺 WAVE ROVER coverage 应 fail closed。
# 设计约束 39：Vendor index 缺 UART JSON coverage 应 fail closed。
# 设计约束 40：Vendor index 缺 complete material coverage 应 fail closed。
# 设计约束 41：product boundary 缺 thread id 应 fail closed。
# 设计约束 42：product boundary 缺 gate name 应 fail closed。
# 设计约束 43：product boundary 缺 hardware_material_pending/not_proven 应 fail closed。
# 设计约束 44：product boundary 缺 acceptance rule 应 fail closed。
# 设计约束 45：product boundary 缺 local vendor does-not-prove wording 应 fail closed。
# 设计约束 46：缺源文件时输出 blocked artifact，而不是 traceback。
# 设计约束 47：binary/non-text vendor refs 只检查存在性，不尝试解码 PDF。
# 设计约束 48：text vendor refs 检查关键 pattern，防止本地资料漂移。
# 设计约束 49：pattern missing 要列入 missing_source_items 便于 Hardware 修正。
# 设计约束 50：boundary missing 要列入 missing_alignment_items 便于 Product closeout。
# 设计约束 51：unsafe scan 只看产品/review 文案，不扫描 vendor raw serial 示例。
# 设计约束 52：delivery_success=true 无保护上下文必须 fail closed。
# 设计约束 53：primary_actions_enabled=true 无保护上下文必须 fail closed。
# 设计约束 54：safe_to_control=true 无保护上下文必须 fail closed。
# 设计约束 55：hil_pass/field_pass/control_enabled true 必须 fail closed。
# 设计约束 56：/Users/ 本机绝对路径进入文案必须 fail closed。
# 设计约束 57：/dev/tty 或 /dev/serial 进入文案必须 fail closed。
# 设计约束 58：credential/token/password/private_key 进入文案必须 fail closed。
# 设计约束 59：PRRT thread resolved/closed/done 肯定式文案必须 fail closed。
# 设计约束 60：LiDAR/ToF procured/installed/wired/calibrated 肯定式文案必须 fail closed。
# 设计约束 61：procurement/install/HIL complete 肯定式文案必须 fail closed。
# 设计约束 62：guard words 允许否定句和 fail-closed 文案包含风险词。
# 设计约束 63：artifact 保留完整检查结构，summary 保持紧凑。
# 设计约束 64：source_docs 不输出 checksum，避免完整材料复制语义。
# 设计约束 65：non_access_scope 明确列出没有访问真实系统。
# 设计约束 66：CLI --help 必须无需 ROS2、Docker、硬件或网络。
# 设计约束 67：CLI --once-json 默认输出 artifact，便于 reviewer 本地复核。
# 设计约束 68：CLI --output 与 --summary-output 可分别给 PC/Robot/mobile 交接。
# 设计约束 69：写文件只创建 evidence 输出目录，不代表创建真实硬件材料。
# 设计约束 70：exit code 0 只表示 gate ready_not_proven。
# 设计约束 71：exit code 2 表示 source/boundary/unsafe fail-closed。
# 设计约束 72：schema_version 固定为 1，避免下游误消费实验字段。
# 设计约束 73：MISSING_MATERIALS 必须含 reviewer_resolution 缺口。
# 设计约束 74：NOT_PROVEN 必须含 pr5_review_thread_resolved 缺口。
# 设计约束 75：safe_copy 中英文都必须保留 hardware_material_pending/not_proven。
# 设计约束 76：owner_handoff 只给人类履约动作，不给机器人控制建议。
# 设计约束 77：mandatory_sensor_assumptions 不能读取真实传感器驱动。
# 设计约束 78：vendor_source_boundary 只能说明 source context，不说明 hardware pass。
# 设计约束 79：covered_domains 应包含 camera/vendor-app context 但不承诺视觉验收。
# 设计约束 80：covered_domains 应包含 optional lidar parser context 但不承诺项目 LiDAR。
# 设计约束 81：default hardware list 固化当前 product boundary，避免 target 侵入默认集。
# 设计约束 82：target_sensing_baseline 固化产品目标，方便 autonomy/mobile 只读引用。
# 设计约束 83：缺 Default Hardware Set 时 default_lidar_or_tof 判断应保守为 false 但 boundary rules fail。
# 设计约束 84：所有读取错误都应转成可复盘 status。
# 设计约束 85：所有路径参数可由 unittest 覆盖，避免测试写真实 vendor 目录。
# 设计约束 86：所有源码 pattern 检查都是 source drift fence，不是硬件验收。
# 设计约束 87：本 gate 不更新 OKR、sprint closeout 或 GitHub thread。
# 设计约束 88：本 gate 不提高 Objective 1 或 Objective 5 完成度。
# 设计约束 89：本 gate 不证明 WAVE ROVER/UART/HIL pass。
# 设计约束 90：本 gate 不证明 Nav2/SLAM field pass 或 near-field safety pass。
# 设计约束 91：本 gate 不证明 delivery result、dropoff/cancel completion 或 delivery success。
# 设计约束 92：本 gate 不证明 true phone/browser、PWA prompt 或 external cloud proof。
# 设计约束 93：本 gate 的所有技术注释保持中文，便于 Hardware 后续月度复盘。
# 设计约束 94：新增字段优先追加，不破坏已有 packet/reply/closeout gate。
# 设计约束 95：测试应覆盖 live repo、temp ready、missing boundary、missing source、unsafe 和 sanitization。

# 这些 schema/boundary 会被 Robot diagnostics、mobile/web 和 Product closeout 消费。
SCHEMA = "trashbot.pr5_mandatory_sensor_source_alignment.v1"
SUMMARY_SCHEMA = "trashbot.pr5_mandatory_sensor_source_alignment_summary.v1"
SCHEMA_VERSION = 1
SOURCE = "software_proof"
THREAD_ID = "PRRT_kwDOSWB9286CJ3tX"
EVIDENCE_BOUNDARY = "software_proof_docker_pr5_mandatory_sensor_source_alignment_gate"

# gate 只读 repo-local 文档和 vendor/source 文件，不读取真实硬件、串口、ROS graph 或 GitHub API。
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BOUNDARY_MD = REPO_ROOT / "docs" / "product" / "production_hardware_boundary.md"
DEFAULT_VENDOR_INDEX = REPO_ROOT / "docs" / "vendor" / "VENDOR_INDEX.md"
DEFAULT_SOURCE_REFS = (
    {
        "domain": "orange_pi_zero_3_manual",
        "path": REPO_ROOT / "docs" / "vendor" / "orangepizero3" / "OrangePi_Zero3_H618_用户手册_v1.6.pdf",
        "patterns": (),
        "note": "Orange Pi Zero 3 manual is listed by docs/vendor/VENDOR_INDEX.md for SBC setup and pin/header source boundary.",
    },
    {
        "domain": "orange_pi_zero_3_schematic",
        "path": REPO_ROOT / "docs" / "vendor" / "orangepizero3" / "OrangePi-ZERO3_电路图.pdf",
        "patterns": (),
        "note": "Orange Pi Zero 3 schematic is listed by docs/vendor/VENDOR_INDEX.md for voltage and board electrical source boundary.",
    },
    {
        "domain": "wave_rover_upper_app_readme",
        "path": REPO_ROOT / "docs" / "vendor" / "waveshare_wave_rover" / "ugv_rpi" / "README.md",
        "patterns": (
            r"upper computer communicates with the lower computer.*?JSON commands via GPIO UART",
            r"AI vision and strategy planning",
            r"Real-time video",
        ),
        "note": "Waveshare upper-computer README supports vendor-app, camera/video, and UART JSON source-boundary context.",
    },
    {
        "domain": "wave_rover_base_ctrl_uart_json_lidar_parser",
        "path": REPO_ROOT / "docs" / "vendor" / "waveshare_wave_rover" / "ugv_rpi" / "base_ctrl.py",
        "patterns": (
            r"serial\.Serial",
            r"json\.loads",
            r"json\.dumps",
            r"lidar_ser",
            r"parse_lidar_frame",
        ),
        "note": "Vendor base_ctrl.py demonstrates UART JSON behavior and optional vendor-app lidar parsing only.",
    },
    {
        "domain": "wave_rover_config_source_boundary",
        "path": REPO_ROOT / "docs" / "vendor" / "waveshare_wave_rover" / "ugv_rpi" / "config.yaml",
        "patterns": (
            r"use_lidar:\s*false",
            r"cmd_movition_ctrl:\s*1",
            r"cmd_pwm_ctrl:\s*11",
            r"video:",
            r"cv:",
        ),
        "note": "Vendor config.yaml records app-level movement, optional lidar, video, and CV defaults.",
    },
    {
        "domain": "wave_rover_json_cmd_firmware_reference",
        "path": REPO_ROOT / "docs" / "vendor" / "waveshare_wave_rover" / "WAVE_ROVER_V0.9" / "json_cmd.h",
        "patterns": (
            r"#define CMD_SPEED_CTRL\s+1",
            r"#define CMD_ROS_CTRL\s+13",
            r"#define CMD_BASE_FEEDBACK\s+130",
            r"CMD_BASE_FEEDBACK_FLOW",
        ),
        "note": "Firmware json_cmd.h defines UART JSON command ids used as WAVE ROVER source-boundary facts.",
    },
    {
        "domain": "wave_rover_uart_handler_reference",
        "path": REPO_ROOT / "docs" / "vendor" / "waveshare_wave_rover" / "WAVE_ROVER_V0.9" / "uart_ctrl.h",
        "patterns": (
            r"jsonCmdReceiveHandler",
            r"CMD_SPEED_CTRL",
            r"CMD_PWM_INPUT",
            r"CMD_ROS_CTRL",
            r"CMD_BASE_FEEDBACK",
        ),
        "note": "Firmware uart_ctrl.h connects JSON command ids to lower-controller handlers.",
    },
    {
        "domain": "wave_rover_motion_reference",
        "path": REPO_ROOT / "docs" / "vendor" / "waveshare_wave_rover" / "WAVE_ROVER_V0.9" / "movtion_module.h",
        "patterns": (
            r"switchEmergencyStop",
            r"setSpdRate",
            r"ESP32Encoder",
            r"getWheelSpeed",
        ),
        "note": "Firmware movtion_module.h is a motion-control source reference, not HIL evidence.",
    },
)

READY_STATUS = "ready_for_pr5_mandatory_sensor_source_alignment_not_proven"
BLOCKED_MISSING_SOURCE = "blocked_missing_pr5_mandatory_sensor_source_alignment_source"
BLOCKED_MISSING_ALIGNMENT = "blocked_missing_pr5_mandatory_sensor_source_alignment_boundary"
BLOCKED_UNSAFE_CLAIM = "blocked_unsafe_pr5_mandatory_sensor_source_alignment_claim"

# missing_materials 是 PR #5 unresolved thread 的真实履约缺口，不因 source-alignment 通过而减少。
MISSING_MATERIALS = (
    "real_2d_lidar_sku_source_receipt",
    "real_tof_sku_source_receipt",
    "real_procurement_or_purchase_order",
    "real_mounting_wiring_power_review",
    "real_calibration_plan_or_result",
    "real_sensor_hil_entry",
    "reviewer_resolution_for_PRRT_kwDOSWB9286CJ3tX",
)

NOT_PROVEN = (
    "real_2d_lidar_procurement",
    "real_tof_procurement",
    "real_installation_wiring_power",
    "real_sensor_calibration",
    "real_sensor_hil_entry_pass",
    "real_wave_rover_uart_hil",
    "real_nav2_slam_field_pass",
    "real_near_field_safety_pass",
    "pr5_review_thread_resolved",
    "delivery_success",
)

# boundary rules 确保 product doc 同时保留默认硬件、目标传感器和真实材料缺口三层。
BOUNDARY_RULES = (
    ("boundary_cites_vendor_index", r"docs/vendor/VENDOR_INDEX\.md"),
    ("thread_id_cited", rf"{THREAD_ID}"),
    ("gate_name_cited", r"pr5_mandatory_sensor_source_alignment"),
    ("hardware_material_pending_not_proven", r"hardware_material_pending.*?not_proven"),
    ("target_combo_declared", r"monocular camera \+ one 2D LiDAR \+ ToF safety ring"),
    ("lidar_tof_marked_pending", r"2D\s+LiDAR and ToF ring are target hardware pending procurement/source\s+attribution.*?HIL evidence"),
    ("vendor_tree_does_not_prove_lidar_tof", r"local vendor (?:tree|files).*?do(?:es)? not prove.*?2D LiDAR or ToF"),
    ("acceptance_requires_real_materials", r"Acceptance rule: do not treat 2D LiDAR or ToF.*?SKU.*?vendor/source.*?HIL"),
)

VENDOR_INDEX_RULES = (
    ("source_of_truth_order", r"## Source Of Truth Order"),
    ("orange_pi_zero_3_covered", r"Orange Pi Zero 3"),
    ("wave_rover_covered", r"WAVE ROVER"),
    ("uart_json_covered", r"UART.*?newline-delimited JSON"),
    ("complete_material_coverage", r"## Complete Material Coverage"),
)

STRICT_TRUE_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bsafe_to_control\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(hil_pass|field_pass|control_enabled)\s*[:=]\s*true\b"),
)

UNSAFE_PATTERNS = STRICT_TRUE_PATTERNS + (
    re.compile(r"(?i)\b/Users/[^\\s`]+"),
    re.compile(r"(?i)\b/dev/(tty|serial)[^\\s`]*"),
    re.compile(r"(?i)\b(OSS_ACCESS_KEY_SECRET|bearer\s+token|password|private_key)\b"),
    re.compile(rf"(?i){THREAD_ID}.{{0,40}}\b(resolved|closed|done)\b"),
    re.compile(r"(?i)\b(2D LiDAR|LiDAR|ToF).{0,48}\b(procured|installed|wired|calibrated|HIL passed|field passed)\b"),
    re.compile(r"(?i)\b(procurement|installation|wiring|calibration|HIL|field).{0,36}\b(complete|passed|proven|validated)\b"),
)


def _utc_now() -> str:
    # UTC 时间戳让 Docker-only evidence 在不同机器上可以稳定排序。
    return datetime.now(timezone.utc).isoformat()


def _read_text(path: Path) -> tuple[str, str]:
    # 缺源文件时仍生成 blocked artifact，避免 sprint closeout 只剩异常栈。
    try:
        return path.expanduser().read_text(encoding="utf-8"), ""
    except FileNotFoundError:
        return "", "missing"
    except (OSError, UnicodeDecodeError):
        return "", "read_error"


def _safe_ref(path: Path) -> str:
    # artifact 只暴露 repo 相对路径，避免把本机绝对路径传播到 diagnostics 或 PR 回复。
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except (OSError, ValueError):
        return path.name


def _has(text: str, pattern: str) -> bool:
    # 文档和 vendor 注释允许小幅变化，所以用语义 regex 而不是整句硬匹配。
    return re.search(pattern, text, re.I | re.S) is not None


def _contains_unsafe_claim(text: str) -> bool:
    # 只拦截肯定式成功/控制/闭环声明；否定句、pending 和 fail-closed 边界不能误伤。
    guard_words = (
        "fail closed",
        "must fail",
        "must remain",
        "must not",
        "does not prove",
        "do not prove",
        "do not treat",
        "not prove",
        "not a claim",
        "not local",
        "not_proven",
        "pending",
        "hardware_material_pending",
        "without claiming",
        "不能",
        "不证明",
        "不得",
        "不是",
        "未验证",
    )
    for pattern in STRICT_TRUE_PATTERNS:
        for match in pattern.finditer(text):
            local = text[max(0, match.start() - 120) : min(len(text), match.end() + 120)].lower()
            if any(word in local for word in guard_words):
                continue
            return True
    for pattern in UNSAFE_PATTERNS[len(STRICT_TRUE_PATTERNS) :]:
        for match in pattern.finditer(text):
            local = text[max(0, match.start() - 280) : min(len(text), match.end() + 180)].lower()
            if any(word in local for word in guard_words):
                continue
            return True
    return False


def _source_ref_results(source_refs: tuple[dict[str, Any], ...]) -> tuple[list[dict[str, Any]], list[str]]:
    # vendor refs 逐个检查，输出只保留安全 citation 和 pattern 结果，不复制源码内容。
    results: list[dict[str, Any]] = []
    missing: list[str] = []
    for item in source_refs:
        path = Path(item["path"])
        patterns = tuple(item.get("patterns", ()))
        if not patterns:
            exists = path.exists()
            if not exists:
                missing.append(f"{item['domain']}.missing")
            results.append(
                {
                    "domain": item["domain"],
                    "source_ref": _safe_ref(path),
                    "load_status": "present_binary_or_non_text" if exists else "missing",
                    "matched_patterns": [],
                    "missing_patterns": [],
                    "source_note": item["note"],
                    "status": "covered_not_proven" if exists else "missing_or_drifted",
                }
            )
            continue

        text, issue = _read_text(path)
        checks = {pattern: _has(text, pattern) for pattern in patterns} if text else {}
        missing_patterns = [pattern for pattern, ok in checks.items() if not ok]
        if issue:
            missing.append(f"{item['domain']}.{issue}")
        missing.extend(f"{item['domain']}.missing_pattern:{pattern}" for pattern in missing_patterns)
        results.append(
            {
                "domain": item["domain"],
                "source_ref": _safe_ref(path),
                "load_status": "loaded" if not issue else issue,
                "matched_patterns": [pattern for pattern, ok in checks.items() if ok],
                "missing_patterns": missing_patterns,
                "source_note": item["note"],
                "status": "covered_not_proven" if text and not missing_patterns else "missing_or_drifted",
            }
        )
    return results, missing


def _rule_results(text: str, rules: tuple[tuple[str, str], ...], prefix: str) -> tuple[list[dict[str, Any]], list[str]]:
    # boundary/vendor index 使用同一种检查结构，便于 unittest 和 closeout 复用。
    results: list[dict[str, Any]] = []
    missing: list[str] = []
    for rule_id, pattern in rules:
        matched = _has(text, pattern)
        if not matched:
            missing.append(f"{prefix}.{rule_id}.missing")
        results.append({"rule_id": rule_id, "pattern": pattern, "matched": matched})
    return results, missing


def _default_hardware_section(boundary_text: str) -> str:
    # 单独抽 default section，防止 target baseline 的 LiDAR/ToF 文字污染默认硬件判断。
    match = re.search(r"^## Default Hardware Set\s*$", boundary_text, re.I | re.M)
    if not match:
        return ""
    next_heading = re.search(r"^##\s+", boundary_text[match.end() :], re.M)
    end = match.end() + next_heading.start() if next_heading else len(boundary_text)
    return boundary_text[match.end() : end]


def _mandatory_sensor_assumptions(boundary_text: str) -> dict[str, Any]:
    # 这段是 PR #5 X thread 的核心回答：mandatory target 不等于当前已安装硬件。
    default_section = _default_hardware_section(boundary_text)
    return {
        "current_default_hardware": [
            "WAVE ROVER mobile chassis",
            "Orange Pi Zero 3 upper computer",
            "portable WiFi or local network access",
            "monocular 1080p camera",
            "microphone",
            "speaker or buzzer",
        ],
        "default_hardware_includes_lidar_or_tof": bool(re.search(r"\b(2D LiDAR|LiDAR|ToF)\b", default_section, re.I)),
        "target_sensing_baseline": {
            "combo": "monocular camera + one 2D LiDAR + ToF safety ring",
            "2D LiDAR": "target primary SLAM/Nav2 mapping + localization after real source/procurement/calibration/HIL evidence",
            "monocular": "current default semantic evidence sensor for elevator/target-floor diagnostics",
            "ToF": "target near-field safety and enter/exit gate, not a primary SLAM source",
        },
        "material_state": "hardware_material_pending",
        "evidence_state": "not_proven",
        "missing_materials": list(MISSING_MATERIALS),
    }


def _vendor_source_boundary(source_results: list[dict[str, Any]]) -> dict[str, Any]:
    # source_refs 是 reviewer 可核查的本地资料边界，不是采购、安装或 HIL 证明。
    return {
        "entrypoint": "docs/vendor/VENDOR_INDEX.md",
        "review_thread_id": THREAD_ID,
        "source_refs": [item["source_ref"] for item in source_results],
        "covered_domains": [
            "Orange Pi Zero 3 manual/schematic references listed by vendor index",
            "WAVE ROVER chassis, firmware, UART JSON, and vendor-app references",
            "Waveshare upper-computer camera/video/CV examples as vendor-app context",
            "Optional vendor-app lidar parser reference as source-boundary context only",
        ],
        "lidar_tof_boundary": "hardware_material_pending_not_proven",
        "source_note": "Local vendor refs align source context only; they do not prove project 2D LiDAR/ToF SKU, purchase, mounting, wiring, power, calibration, HIL, field pass, PR thread resolution, or delivery success.",
    }


def _next_required_evidence() -> list[str]:
    # 下一步必须回到真实材料，而不是把软件证明继续包装成硬件通过。
    return [
        "Provide reviewed 2D LiDAR SKU/source/receipt or purchase-order material.",
        "Provide reviewed ToF SKU/source/channel-count material.",
        "Provide mounting, wiring, power-budget, and calibration review evidence.",
        "Run a separate HIL-entry material review only after real sensor materials exist.",
        "Ask reviewer to resolve PRRT_kwDOSWB9286CJ3tX only after material or reviewer resolution evidence exists.",
    ]


def _safe_copy(status: str) -> dict[str, str]:
    # safe copy 可给 Robot/mobile/PR 回复使用，但不包含 raw vendor 源码、串口路径或本机路径。
    return {
        "zh": (
            f"PR #5 线程 {THREAD_ID} 的 mandatory sensor assumptions 已对齐到本地 vendor/source 边界："
            "docs/vendor/VENDOR_INDEX.md 及本地 Orange Pi、WAVE ROVER、UART JSON、firmware/vendor-app 资料只证明来源上下文；"
            "2D LiDAR / ToF 仍是 hardware_material_pending、not_proven。"
        ),
        "en": (
            f"PR #5 thread {THREAD_ID} mandatory sensor assumptions are aligned to local vendor/source boundaries. "
            "docs/vendor/VENDOR_INDEX.md and local Orange Pi, WAVE ROVER, UART JSON, firmware/vendor-app refs establish source context only; "
            "2D LiDAR and ToF remain hardware_material_pending and not_proven."
        ),
        "status": status,
    }


def _summary(
    status: str,
    source_results: list[dict[str, Any]],
    source_missing: list[str],
    boundary_missing: list[str],
    vendor_index_missing: list[str],
    boundary_text: str,
) -> dict[str, Any]:
    # summary 是下游优先消费面，固定 false 控制字段并保留 missing_materials。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source_schema": SCHEMA,
        "source_schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "thread_id": THREAD_ID,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "proof_boundary": EVIDENCE_BOUNDARY,
        "overall_status": "not_proven",
        "alignment_status": status,
        "vendor_source_boundary": _vendor_source_boundary(source_results),
        "mandatory_sensor_assumptions": _mandatory_sensor_assumptions(boundary_text),
        "missing_source_items": source_missing,
        "missing_alignment_items": boundary_missing + vendor_index_missing,
        "missing_materials": list(MISSING_MATERIALS),
        "hardware_material_status": "hardware_material_pending",
        "evidence_status": "not_proven",
        "not_proven": list(NOT_PROVEN),
        "next_required_evidence": _next_required_evidence(),
        "owner_handoff": "Hardware must keep 2D LiDAR / ToF real-material follow-up open until reviewed materials and reviewer resolution exist.",
        "safe_copy": _safe_copy(status),
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_pr5_mandatory_sensor_source_alignment(
    boundary_md: str | Path = DEFAULT_BOUNDARY_MD,
    vendor_index: str | Path = DEFAULT_VENDOR_INDEX,
    source_refs: tuple[dict[str, Any], ...] = DEFAULT_SOURCE_REFS,
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 product boundary 与本地 vendor/source refs，生成 canonical source-alignment artifact。"""

    boundary_path = Path(boundary_md)
    vendor_path = Path(vendor_index)
    boundary_text, boundary_issue = _read_text(boundary_path)
    vendor_text, vendor_issue = _read_text(vendor_path)
    source_results, source_missing = _source_ref_results(source_refs)
    boundary_checks, boundary_missing = _rule_results(boundary_text, BOUNDARY_RULES, "boundary") if boundary_text else ([], ["boundary.production_hardware_boundary.missing"])
    vendor_checks, vendor_index_missing = _rule_results(vendor_text, VENDOR_INDEX_RULES, "vendor_index") if vendor_text else ([], ["vendor_index.docs_vendor_index.missing"])

    # 安全扫描只看 product/review 文案；vendor 源文件合法包含 raw serial 示例，不能误判成 artifact 泄漏。
    unsafe_text = boundary_text
    if boundary_issue or vendor_issue or source_missing:
        status = BLOCKED_MISSING_SOURCE
        if boundary_issue:
            boundary_missing.append(f"production_hardware_boundary.{boundary_issue}")
        if vendor_issue:
            vendor_index_missing.append(f"vendor_index.{vendor_issue}")
        exit_code = 2
    elif boundary_missing or vendor_index_missing:
        status = BLOCKED_MISSING_ALIGNMENT
        exit_code = 2
    elif _contains_unsafe_claim(unsafe_text):
        status = BLOCKED_UNSAFE_CLAIM
        exit_code = 2
    else:
        status = READY_STATUS
        exit_code = 0

    summary = _summary(status, source_results, source_missing, boundary_missing, vendor_index_missing, boundary_text)
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "generated_at": _utc_now(),
        "thread_id": THREAD_ID,
        "thread_topic": "mandatory sensor assumptions require local vendor/source boundary while 2D LiDAR / ToF real materials remain pending",
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "proof_boundary": EVIDENCE_BOUNDARY,
        "overall_status": "not_proven",
        "alignment_status": status,
        "source_docs": {
            "production_hardware_boundary": _safe_ref(boundary_path),
            "vendor_index": _safe_ref(vendor_path),
            "source_refs": [item["source_ref"] for item in source_results],
        },
        "source_ref_checks": source_results,
        "boundary_rule_checks": boundary_checks,
        "vendor_index_rule_checks": vendor_checks,
        "vendor_source_boundary": summary["vendor_source_boundary"],
        "mandatory_sensor_assumptions": summary["mandatory_sensor_assumptions"],
        "missing_source_items": source_missing,
        "missing_alignment_items": boundary_missing + vendor_index_missing,
        "missing_materials": list(MISSING_MATERIALS),
        "hardware_material_status": "hardware_material_pending",
        "evidence_status": "not_proven",
        "not_proven": list(NOT_PROVEN),
        "next_required_evidence": _next_required_evidence(),
        "owner_handoff": summary["owner_handoff"],
        "safe_copy": summary["safe_copy"],
        "non_access_scope": [
            "github_write_or_thread_resolution",
            "ros_graph",
            "serial_uart",
            "hardware_bus",
            "procurement_system",
            "sensor_driver_runtime",
            "hil",
            "field_run",
            "objective_5_external_infrastructure",
            "delivery_execution",
        ],
        "review_summary": summary,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    return artifact, summary, exit_code


def _write_json(path: str, payload: dict[str, Any]) -> None:
    # 写文件只是生成软件证明产物；目录存在不代表真实硬件材料存在。
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 保持 repo-local、只读、无硬件 side effect，便于 Docker-only 验收围栏运行。
    parser = argparse.ArgumentParser(description="Generate PR #5 mandatory sensor source-alignment software-proof artifact.")
    parser.add_argument("--boundary-md", default=str(DEFAULT_BOUNDARY_MD), help="production_hardware_boundary.md path.")
    parser.add_argument("--vendor-index", default=str(DEFAULT_VENDOR_INDEX), help="docs/vendor/VENDOR_INDEX.md path.")
    parser.add_argument("--output", default="", help="Write full source-alignment artifact JSON to this path.")
    parser.add_argument("--summary-output", default="", help="Write compact source-alignment summary JSON.")
    parser.add_argument("--once-json", action="store_true", help="Print full artifact JSON to stdout.")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_pr5_mandatory_sensor_source_alignment(args.boundary_md, args.vendor_index)
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"pr5_mandatory_sensor_source_alignment: artifact_file:{Path(args.output).name if args.output else ''}")
        print(f"summary_file: {Path(args.summary_output).name if args.summary_output else ''}")
        print(f"overall_status: {artifact['overall_status']}")
        print(f"alignment_status: {artifact['alignment_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
