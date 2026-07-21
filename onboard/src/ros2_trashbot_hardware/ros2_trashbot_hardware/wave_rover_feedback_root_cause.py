"""WAVE ROVER 轮速零反馈的离线根因诊断。

本模块只消费本地 vendor 源、已经冻结的 v8 artifacts，以及可选的严格只读
runtime inventory。它不会 import ROS2、打开 UART、发送控制或改变 service。

Vendor 来源：
- docs/vendor/VENDOR_INDEX.md
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_config.h
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/WAVE_ROVER_V0.9.ino
- docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any


# 诊断设计不变量：输入只来自调用方显式给出的本地路径。
# 诊断设计不变量：模块不解析 SSH 地址，也不建立网络连接。
# 诊断设计不变量：模块不 import rclpy，避免隐式启动 ROS graph。
# 诊断设计不变量：模块不 import serial，避免误开 WAVE ROVER UART。
# 诊断设计不变量：模块不构造 T=11、T=13、T=130、T=131 或 T=900 写帧。
# 诊断设计不变量：历史 v8 nonzero 只作为不可变输入，绝不作为重放指令。
# 诊断设计不变量：任何输入冲突都压过候选排序并返回非零。
# 诊断设计不变量：任何安全字段缺失与危险 true 等价处理。
# 诊断设计不变量：源码默认值与 runtime 观察值必须分栏保存。
# 诊断设计不变量：bridge 配置 mainType 不等于 ESP32 runtime mainType。
# 诊断设计不变量：本地 vendor 源不等于 deployed firmware binary。
# 诊断设计不变量：bridge debug frame 不等于 byte-for-byte raw UART。
# 诊断设计不变量：同窗时序用 command/feedback timestamp 重新计算。
# 诊断设计不变量：normalized alias 必须逐帧等于 vendor_frame L/R。
# 诊断设计不变量：JSONL 坏行不能被其他好行抵消。
# 诊断设计不变量：空 JSONL 行也视为证据链断裂。
# 诊断设计不变量：所有 hash 使用 SHA-256 且只记录相对 source ref。
# 诊断设计不变量：候选顺序固定，便于 Product 做稳定对照。
# 诊断设计不变量：primary classification 只在全部输入通过后生成。
# 诊断设计不变量：正常 exit 0 仍不代表 HIL pass。
# 诊断设计不变量：CLI 唯一写操作是调用方指定的本地 JSON output。
# 诊断设计不变量：当前运行所有控制和 mutation 计数恒为零。
# 诊断设计不变量：下一维护动作不能隐含新的运动授权。
# 诊断设计不变量：未观察事实必须显式写入 not_proven。
# 诊断设计不变量：输出不得把推断措辞伪装成硬件确认。

# 输出 schema 固定，便于 Product 与后续维护工具做 fail-closed assertion。
SCHEMA = "trashbot.wave_rover.feedback_root_cause_diagnostic.v1"

# 该边界只接受离线诊断，不把源码推断升级为当前板固件事实。
PROOF_BOUNDARY = "offline_vendor_v8_diagnostic_with_optional_readonly_inventory_only"

# v8 已封存且不可 retry；这里只读校验其身份，不重放任何动作。
EXPECTED_AUTHORIZATION_ID = "ceo_20260721_0651_current_wheel_feedback_hil_v8"
EXPECTED_ATTEMPT_ID = "o1-current-wheel-feedback-hil-v8-attempt-1"

# runtime inventory 也使用显式 schema，避免把任意远端文本冒充当前事实。
RUNTIME_INVENTORY_SCHEMA = "trashbot.wave_rover.readonly_runtime_inventory.v1"

# 当前 sprint 的所有 mutation/control 计数必须保持为零。
CURRENT_RUN_ZERO_COUNTERS = {
    "motion_command_count": 0,
    "control_command_count": 0,
    "stop_command_count": 0,
    "nonzero_command_count": 0,
    "service_mutation_count": 0,
    "uart_write_count": 0,
    "firmware_mutation_count": 0,
    "retry_count": 0,
}

# v8 的最小输入集来自 PRD；遗漏任一文件都不能给出正常诊断结论。
V8_JSON_FILES = (
    "acceptance_summary.json",
    "during_motion_t1001.json",
    "post_stop_t1001.json",
    "final_base_status.json",
)
V8_JSONL_FILES = (
    "live_bridge_command_delta.jsonl",
    "live_bridge_feedback_delta.jsonl",
)

# 这些字段如果在冻结 acceptance 中变成 true，必须拒绝输入。
REQUIRED_FALSE_FIELDS = (
    "hil_pass",
    "safe_to_control",
    "route_execution_success",
    "delivery_success",
)

# 只读 inventory 允许的命令类别与 tech-plan 完全一致。
READONLY_COMMAND_CATEGORIES = {
    "systemctl_status",
    "systemctl_show",
    "systemctl_cat",
    "ps",
    "ss",
    "lsof",
    "fuser",
    "sha256sum",
    "ros2_param_get",
    "ros2_param_list",
    "journalctl",
    "cat",
    "tail",
    "http_get",
}

# category 只是声明；命令文本还必须匹配只读前缀，防止伪装类别。
READONLY_COMMAND_PREFIXES = {
    "systemctl_status": ("systemctl status ",),
    "systemctl_show": ("systemctl show ",),
    "systemctl_cat": ("systemctl cat ",),
    "ps": ("ps ",),
    "ss": ("ss ",),
    "lsof": ("lsof ",),
    "fuser": ("fuser ",),
    "sha256sum": ("sha256sum ",),
    "ros2_param_get": ("ros2 param get ",),
    "ros2_param_list": ("ros2 param list",),
    "journalctl": ("journalctl ",),
    "cat": ("cat ",),
    "tail": ("tail ",),
    "http_get": ("curl ",),
}

# 任一 shell 组合或已知 mutation/control token 出现时都拒绝 inventory。
UNSAFE_COMMAND_TOKENS = (
    ";",
    "&&",
    "||",
    "`",
    "$(",
    ">",
    "systemctl stop",
    "systemctl restart",
    "systemctl start",
    "systemctl enable",
    "systemctl disable",
    "ros2 param set",
    "ros2 topic pub",
    "/cmd_vel",
    "/api/base/manual",
    "/api/base/stop",
    " -X POST",
    " -X PUT",
    " -X PATCH",
    " -X DELETE",
)

# 定义值核验避免只凭注释或文件名推断协议。
DEFINE_FACTS = (
    ("json_cmd.h", "FEEDBACK_BASE_INFO", "1001", "vendor_feedback_type_t1001"),
    ("json_cmd.h", "CMD_PWM_INPUT", "11", "vendor_pwm_command_t11"),
    ("json_cmd.h", "CMD_ROS_CTRL", "13", "vendor_ros_command_t13"),
    ("json_cmd.h", "CMD_BASE_FEEDBACK", "130", "vendor_feedback_request_t130"),
    ("json_cmd.h", "CMD_BASE_FEEDBACK_FLOW", "131", "vendor_feedback_flow_t131"),
    ("json_cmd.h", "CMD_MM_TYPE_SET", "900", "vendor_main_module_type_command_t900"),
)

# 代码路径核验同时覆盖命令分发、encoder 更新与 T=1001 采样来源。
NEEDLE_FACTS = (
    ("uart_ctrl.h", "case CMD_PWM_INPUT:", "pwm_dispatch_branch"),
    ("uart_ctrl.h", 'leftCtrl(jsonCmdReceive["L"]);', "pwm_left_dispatch"),
    ("uart_ctrl.h", 'rightCtrl(jsonCmdReceive["R"]);', "pwm_right_dispatch"),
    ("movtion_module.h", "void initEncoders()", "encoder_init_function"),
    ("movtion_module.h", "void getLeftSpeed()", "left_encoder_update_function"),
    ("movtion_module.h", "void getRightSpeed()", "right_encoder_update_function"),
    ("movtion_module.h", "if (mainType != 3)", "main_type_feedback_branch"),
    ("movtion_module.h", "speedGetA = pwmIntA;", "left_pwm_value_assignment"),
    ("movtion_module.h", "speedGetB = pwmIntB;", "right_pwm_value_assignment"),
    ("ugv_advance.h", 'jsonInfoHttp["L"] = speedGetA;', "t1001_left_source"),
    ("ugv_advance.h", 'jsonInfoHttp["R"] = speedGetB;', "t1001_right_source"),
    ("ugv_config.h", "byte mainType = 1;", "source_default_main_type_wave_rover"),
    ("WAVE_ROVER_V0.9.ino", "initEncoders();", "setup_initializes_encoders"),
    ("WAVE_ROVER_V0.9.ino", "getLeftSpeed();", "loop_refreshes_left_encoder"),
    ("WAVE_ROVER_V0.9.ino", "getRightSpeed();", "loop_refreshes_right_encoder"),
    ("WAVE_ROVER_V0.9.ino", "if (baseFeedbackFlow)", "loop_feedback_flow_gate"),
    ("base_ctrl.py", 'self.ser.write((json.dumps(data) + \'\\n\').encode("utf-8"))', "newline_json_uart_write"),
)

# 输出使用项目相对路径，避免把本机绝对路径写进 artifact。
CANONICAL_VENDOR_REFS = {
    "json_cmd.h": "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
    "uart_ctrl.h": "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
    "movtion_module.h": "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h",
    "ugv_advance.h": "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h",
    "ugv_config.h": "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_config.h",
    "WAVE_ROVER_V0.9.ino": "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/WAVE_ROVER_V0.9.ino",
    "base_ctrl.py": "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
}


def _sha256(path: Path) -> str:
    """计算输入 hash，保证诊断引用的是确定内容。"""
    # 分块读取避免未来 artifact 增大时产生不必要内存峰值。
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _finite_number(value: Any) -> bool:
    """只接受有限且非布尔数值，避免 true 被当成 1。"""
    # Python 的 bool 是 int 子类，因此必须单独排除。
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _read_json(path: Path, errors: list[str]) -> dict[str, Any] | None:
    """读取 object JSON；任何格式问题都进入统一错误列表。"""
    # 输入错误不抛出到 CLI 外，保证仍能产出结构化 fail-closed JSON。
    if not path.is_file():
        errors.append(f"missing_input:{path.name}")
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"invalid_json:{path.name}:{type(exc).__name__}")
        return None
    if not isinstance(value, dict):
        errors.append(f"invalid_json_object:{path.name}")
        return None
    return value


def _read_jsonl(path: Path, errors: list[str]) -> list[dict[str, Any]]:
    """严格读取 JSONL，不允许坏行被静默跳过。"""
    # 坏行即代表时序或计数证据不完整，所以整体 fail closed。
    if not path.is_file():
        errors.append(f"missing_input:{path.name}")
        return []
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        errors.append(f"invalid_jsonl_read:{path.name}:{type(exc).__name__}")
        return []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            errors.append(f"blank_jsonl_line:{path.name}:{line_number}")
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            errors.append(f"invalid_jsonl:{path.name}:{line_number}")
            continue
        if not isinstance(value, dict):
            errors.append(f"invalid_jsonl_object:{path.name}:{line_number}")
            continue
        rows.append(value)
    return rows


def _line_numbers(text: str, needle: str) -> list[int]:
    """返回包含 exact needle 的 1-based 行号。"""
    # 行号只做 source evidence，不把它当 runtime binary identity。
    return [index for index, line in enumerate(text.splitlines(), start=1) if needle in line]


def _vendor_paths(vendor_source_root: Path) -> dict[str, Path]:
    """从 canonical firmware root 推导本地 vendor 文件。"""
    # Raspberry Pi 参考在 firmware root 的同级目录，不能误当 firmware 文件。
    paths = {name: vendor_source_root / name for name in CANONICAL_VENDOR_REFS if name != "base_ctrl.py"}
    paths["base_ctrl.py"] = vendor_source_root.parent / "ugv_rpi" / "base_ctrl.py"
    return paths


def _validate_vendor_sources(vendor_source_root: Path) -> dict[str, Any]:
    """核验 vendor symbol 与关键赋值/采样分支。"""
    # 每个事实都保留具体 source_ref、symbol 与 line，便于维护窗口复核。
    # Vendor 核验：先确认文件存在，再做 symbol 检查。
    # Vendor 核验：文件读取失败不能退化为零个匹配的普通状态。
    # Vendor 核验：每个采用文件都计算独立 hash。
    # Vendor 核验：hash key 固定为项目相对路径。
    # Vendor 核验：宏值来自有效 define，不从注释示例提取。
    # Vendor 核验：宏必须恰好定义一次。
    # Vendor 核验：重复相同 define 也视为 source 冲突。
    # Vendor 核验：宏冲突必须列出全部观察值与行号。
    # Vendor 核验：代码 needle 使用 exact text，避免宽松正则误命中。
    # Vendor 核验：needle 缺失会阻止硬件候选排序。
    # Vendor 核验：uart_ctrl 负责确认 T=11 分发到左右控制函数。
    # Vendor 核验：movtion_module 负责确认 encoder 初始化入口。
    # Vendor 核验：movtion_module 负责确认左右 encoder 更新函数。
    # Vendor 核验：movtion_module 负责确认 PWM 临时赋值分支。
    # Vendor 核验：ugv_advance 负责确认 T=1001 的 L/R 数据源。
    # Vendor 核验：ugv_config 只确认源码默认 mainType。
    # Vendor 核验：ino setup 负责确认 initEncoders 实际被调用。
    # Vendor 核验：ino loop 负责确认左右速度在 feedback 前刷新。
    # Vendor 核验：ino feedback flow 只确认采样入口存在。
    # Vendor 核验：base_ctrl 只确认 newline-delimited JSON transport。
    # Vendor 核验：Raspberry Pi 参考路径不用于推断 Orange Pi 设备名。
    # Vendor 核验：本模块不读取 factory firmware binary。
    # Vendor 核验：本模块不比较或改写厂商二进制。
    # Vendor 核验：所有 line evidence 使用 1-based 编号。
    # Vendor 核验：多处合法 needle 会全部保留，而不擅自选唯一行。
    errors: list[str] = []
    source_hashes: dict[str, str] = {}
    texts: dict[str, str] = {}
    facts: list[dict[str, Any]] = []
    paths = _vendor_paths(vendor_source_root)

    # 先一次性读取所有源，避免部分事实验证后才发现文件缺失。
    for name, path in paths.items():
        if not path.is_file():
            errors.append(f"missing_vendor_source:{name}")
            continue
        try:
            texts[name] = path.read_text(encoding="utf-8")
            source_hashes[CANONICAL_VENDOR_REFS[name]] = _sha256(path)
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"unreadable_vendor_source:{name}:{type(exc).__name__}")

    # 宏定义必须只有一个且等于期望值；重复或冲突都不能择一采用。
    for filename, symbol, expected, fact_id in DEFINE_FACTS:
        text = texts.get(filename, "")
        pattern = re.compile(rf"^\s*#define\s+{re.escape(symbol)}\s+([^\s/]+)", re.MULTILINE)
        matches = [(match.group(1), text[: match.start()].count("\n") + 1) for match in pattern.finditer(text)]
        status = "verified" if len(matches) == 1 and matches[0][0] == expected else "invalid"
        if status != "verified":
            status = "invalid"
            errors.append(f"vendor_define_conflict:{symbol}:expected={expected}:observed={matches}")
        facts.append(
            {
                "fact_id": fact_id,
                "status": status,
                "source_ref": CANONICAL_VENDOR_REFS[filename],
                "symbol": symbol,
                "expected_value": expected,
                "observed_definitions": [{"value": value, "line": line} for value, line in matches],
            }
        )

    # 关键代码 needle 至少出现一次；多处合法赋值会全部保留行号。
    for filename, needle, fact_id in NEEDLE_FACTS:
        lines = _line_numbers(texts.get(filename, ""), needle)
        status = "verified" if lines else "missing"
        if not lines:
            errors.append(f"vendor_code_path_missing:{fact_id}")
        facts.append(
            {
                "fact_id": fact_id,
                "status": status,
                "source_ref": CANONICAL_VENDOR_REFS[filename],
                "symbol": needle,
                "lines": lines,
            }
        )

    return {
        "valid": not errors,
        "errors": errors,
        "source_hashes": dict(sorted(source_hashes.items())),
        "facts": facts,
    }


def _pair_from_feedback_row(row: dict[str, Any]) -> list[float] | None:
    """从 bridge feedback debug row 取 vendor T=1001 L/R。"""
    # 只信 vendor_frame，normalized alias 仅用于一致性对照。
    frame = row.get("vendor_frame")
    if not isinstance(frame, dict) or frame.get("T") != 1001:
        return None
    left = frame.get("L")
    right = frame.get("R")
    if not _finite_number(left) or not _finite_number(right):
        return None
    return [float(left), float(right)]


def _validate_v8(v8_artifact_dir: Path) -> dict[str, Any]:
    """校验 v8 身份、计数、同窗时序与最终安全字段。"""
    # 诊断读取历史动作证据，但当前运行绝不复用该授权或发送动作。
    # v8 核验：authorization id 必须与已封存 v8 一致。
    # v8 核验：attempt id 防止误读其他 HIL 窗口。
    # v8 核验：authorization status 必须是 consumed_no_retry。
    # v8 核验：pre-stop 计数必须为一次。
    # v8 核验：nonzero request 计数必须为一次。
    # v8 核验：post-stop 计数必须为一次。
    # v8 核验：retry 计数必须为零。
    # v8 核验：no_retry 必须是布尔 true。
    # v8 核验：四个安全字段必须逐个为布尔 false。
    # v8 核验：transport accepted 只证明发送链，不证明轮速。
    # v8 核验：during-motion observed 只证明同窗收到 feedback。
    # v8 核验：during-motion nonzero 必须保持 false。
    # v8 核验：post-stop zero 必须保持 true。
    # v8 核验：direct T=130 仍须保持未观察。
    # v8 核验：T=13 wire 仍须保持未观察。
    # v8 核验：raw UART capture 仍须保持 false。
    # v8 核验：final stopped 必须保持 true。
    # v8 核验：command row 必须是 object 且 T=11。
    # v8 核验：command timestamp 必须是有限数值。
    # v8 核验：command L/R 必须是有限数值。
    # v8 核验：command row 必须明确 sent=true。
    # v8 核验：六个 bridge nonzero frame 属于同一历史 request 展开。
    # v8 核验：当前运行不能把六个历史 frame 计入 motion counter。
    # v8 核验：第一个后续零速 frame 定义 command window 结束。
    # v8 核验：窗口使用左闭右开，避免 stop 同时刻 feedback 歧义。
    # v8 核验：feedback 必须带 vendor_frame T=1001。
    # v8 核验：feedback normalized L 必须等于 vendor L。
    # v8 核验：feedback normalized R 必须等于 vendor R。
    # v8 核验：同窗应恰有三帧，不接受摘要替代重算。
    # v8 核验：三帧任一非零都会与 frozen acceptance 冲突。
    # v8 核验：during 单帧 artifact 必须落在重算窗口。
    # v8 核验：post-stop 单帧 artifact 必须为 0/0。
    # v8 核验：final latest command 必须是 T=11 L/R=0。
    # v8 核验：final latest feedback 必须是 T=1001 L/R=0。
    # v8 核验：最终 nonzero feedback 计数必须为零。
    errors: list[str] = []
    inputs: dict[str, dict[str, Any]] = {}
    json_values: dict[str, dict[str, Any] | None] = {}
    jsonl_values: dict[str, list[dict[str, Any]]] = {}

    # 所有存在的输入都记录 hash 与大小，便于后续检测 artifact 漂移。
    for name in (*V8_JSON_FILES, *V8_JSONL_FILES):
        path = v8_artifact_dir / name
        if path.is_file():
            inputs[name] = {"sha256": _sha256(path), "size_bytes": path.stat().st_size}

    # JSON 与 JSONL 分开严格解析，任何坏行都保留成错误。
    for name in V8_JSON_FILES:
        json_values[name] = _read_json(v8_artifact_dir / name, errors)
    for name in V8_JSONL_FILES:
        jsonl_values[name] = _read_jsonl(v8_artifact_dir / name, errors)

    acceptance = json_values["acceptance_summary.json"] or {}
    during = json_values["during_motion_t1001.json"] or {}
    post_stop = json_values["post_stop_t1001.json"] or {}
    final_status = json_values["final_base_status.json"] or {}
    commands = jsonl_values["live_bridge_command_delta.jsonl"]
    feedback = jsonl_values["live_bridge_feedback_delta.jsonl"]

    # 身份与 exactly-once 计数必须匹配已接受 closeout。
    expected_values = {
        "schema": "trashbot.o1.current_wheel_feedback_hil.acceptance.v1",
        "authorization_id": EXPECTED_AUTHORIZATION_ID,
        "authorization_status": "consumed_no_retry",
        "attempt_id": EXPECTED_ATTEMPT_ID,
        "pre_stop": 1,
        "nonzero": 1,
        "post_stop": 1,
        "retry": 0,
        "no_retry": True,
    }
    for key, expected in expected_values.items():
        if acceptance.get(key) != expected:
            errors.append(f"v8_identity_or_count_conflict:{key}:expected={expected}:observed={acceptance.get(key)}")

    # 四个安全 false 字段不能被历史 artifact 改成危险真值。
    for key in REQUIRED_FALSE_FIELDS:
        if acceptance.get(key) is not False:
            errors.append(f"dangerous_or_missing_v8_safety_field:{key}:{acceptance.get(key)}")

    # 传输 receipt、同窗失败和 final stop 是 v8 被接受的最小事实。
    required_acceptance_facts = {
        "nonzero_transport_response_accepted": True,
        "during_motion_t1001_observed": True,
        "during_motion_t1001_lr_nonzero_proven": False,
        "post_stop_t1001_observed": True,
        "post_stop_t1001_lr_zero_proven": True,
        "t130_request_observed": False,
        "t13_wire_observed": False,
        "raw_serial_byte_capture": False,
        "final_stopped": True,
    }
    for key, expected in required_acceptance_facts.items():
        if acceptance.get(key) is not expected:
            errors.append(f"v8_fact_conflict:{key}:expected={expected}:observed={acceptance.get(key)}")

    # command debug 必须明确包含六个已发送 T=11 nonzero frame 与后续零速 frame。
    nonzero_commands: list[dict[str, Any]] = []
    zero_commands: list[dict[str, Any]] = []
    for index, row in enumerate(commands):
        vendor_command = row.get("vendor_command")
        timestamp = row.get("observed_at_unix_s")
        if not isinstance(vendor_command, dict) or vendor_command.get("T") != 11 or not _finite_number(timestamp):
            errors.append(f"invalid_bridge_command_row:{index}")
            continue
        left = vendor_command.get("L")
        right = vendor_command.get("R")
        if not _finite_number(left) or not _finite_number(right) or row.get("sent") is not True:
            errors.append(f"invalid_bridge_command_payload:{index}")
            continue
        if float(left) != 0.0 or float(right) != 0.0:
            nonzero_commands.append(row)
        else:
            zero_commands.append(row)
    if len(nonzero_commands) != 6:
        errors.append(f"v8_nonzero_transport_frame_count_conflict:expected=6:observed={len(nonzero_commands)}")
    if not zero_commands:
        errors.append("v8_missing_zero_command_after_nonzero")

    # 由 command timestamps 重建 during-motion window，而不是只信摘要字段。
    window_start: float | None = None
    window_stop: float | None = None
    if nonzero_commands:
        window_start = min(float(row["observed_at_unix_s"]) for row in nonzero_commands)
        later_zero_times = [
            float(row["observed_at_unix_s"])
            for row in zero_commands
            if float(row["observed_at_unix_s"]) >= window_start
        ]
        if later_zero_times:
            window_stop = min(later_zero_times)
        else:
            errors.append("v8_missing_window_stop_timestamp")

    # feedback alias 必须与 vendor_frame 一致，防止 parser 层制造 0/0。
    parser_consistent = True
    during_pairs: list[list[float]] = []
    for index, row in enumerate(feedback):
        pair = _pair_from_feedback_row(row)
        timestamp = row.get("observed_at_unix_s")
        if pair is None or not _finite_number(timestamp):
            errors.append(f"invalid_bridge_feedback_row:{index}")
            parser_consistent = False
            continue
        if not _finite_number(row.get("left_speed")) or not _finite_number(row.get("right_speed")):
            errors.append(f"invalid_bridge_feedback_alias:{index}")
            parser_consistent = False
            continue
        if [float(row["left_speed"]), float(row["right_speed"])] != pair:
            errors.append(f"bridge_parser_vendor_frame_conflict:{index}")
            parser_consistent = False
        if window_start is not None and window_stop is not None and window_start <= float(timestamp) < window_stop:
            during_pairs.append(pair)
    if not parser_consistent:
        errors.append("bridge_parser_consistency_not_proven")

    # 真实 v8 窗内应恰有三帧且全部 0/0。
    if during_pairs != [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]]:
        errors.append(f"v8_during_window_pair_conflict:{during_pairs}")
    accepted_pairs = acceptance.get("during_motion_t1001_observed_pairs")
    if accepted_pairs != [[0, 0], [0, 0], [0, 0]]:
        errors.append(f"v8_acceptance_pair_conflict:{accepted_pairs}")

    # 单帧 during artifact 也必须落在重建窗口内并保持 0/0。
    during_timestamp = during.get("observed_at_unix_s")
    if (
        during.get("T") != 1001
        or during.get("L") != 0
        or during.get("R") != 0
        or not _finite_number(during_timestamp)
        or window_start is None
        or window_stop is None
        or not (window_start <= float(during_timestamp) < window_stop)
    ):
        errors.append("v8_during_motion_artifact_conflict")

    # post-stop 与 final status 都必须显示零反馈和已发送零命令。
    if post_stop.get("T") != 1001 or post_stop.get("L") != 0 or post_stop.get("R") != 0:
        errors.append("v8_post_stop_feedback_conflict")
    latest_command = final_status.get("latest_command")
    latest_feedback = final_status.get("latest_t1001")
    if not isinstance(latest_command, dict) or latest_command.get("vendor_command") != {"L": 0, "R": 0, "T": 11}:
        errors.append("v8_final_zero_command_conflict")
    if not isinstance(latest_feedback, dict) or latest_feedback.get("L") != 0 or latest_feedback.get("R") != 0:
        errors.append("v8_final_zero_feedback_conflict")
    if final_status.get("final_stopped") is not True or final_status.get("wheel_feedback_nonzero_frame_count") != 0:
        errors.append("v8_final_status_conflict")

    return {
        "valid": not errors,
        "errors": errors,
        "input_artifacts": dict(sorted(inputs.items())),
        "authorization_id": acceptance.get("authorization_id"),
        "authorization_status": acceptance.get("authorization_status"),
        "attempt_id": acceptance.get("attempt_id"),
        "historical_exactly_once_counts": {
            "pre_stop": acceptance.get("pre_stop"),
            "nonzero": acceptance.get("nonzero"),
            "post_stop": acceptance.get("post_stop"),
            "retry": acceptance.get("retry"),
        },
        "historical_bridge_command_counts": {
            "nonzero_t11_frames": len(nonzero_commands),
            "zero_t11_frames": len(zero_commands),
        },
        "historical_feedback_counts": {
            "total_t1001_frames": len(feedback),
            "during_window_t1001_frames": len(during_pairs),
            "during_window_nonzero_pairs": sum(1 for left, right in during_pairs if left != 0 or right != 0),
        },
        "command_window": {"start_unix_s": window_start, "stop_unix_s": window_stop},
        "during_window_pairs": during_pairs,
        "bridge_parser_consistent_with_vendor_frame": parser_consistent and bool(feedback),
        "feedback_evidence_source_class": acceptance.get("feedback_evidence_source_class"),
        "raw_serial_byte_capture": acceptance.get("raw_serial_byte_capture"),
        "final_stopped": acceptance.get("final_stopped"),
    }


def _validate_runtime_inventory(runtime_inventory_json: Path | None) -> dict[str, Any]:
    """校验可选严格只读 runtime inventory。"""
    # 未提供不是错误，只会让 firmware/mainType 保持 not_observed。
    # Runtime 核验：inventory 必须显式声明 readonly_only=true。
    # Runtime 核验：schema 防止普通 shell log 被误当结构化证据。
    # Runtime 核验：allowlist 必须是批准类别的非空子集。
    # Runtime 核验：未知命令类别一律拒绝。
    # Runtime 核验：每条命令必须保留完整命令文本。
    # Runtime 核验：每条命令必须保留 exit code。
    # Runtime 核验：每条命令必须保留脱敏 stdout 摘要。
    # Runtime 核验：每条命令必须保留 stderr 摘要。
    # Runtime 核验：systemctl 只接受 status/show/cat 类别。
    # Runtime 核验：ps 与 ss 只用于读取既有 process/listener。
    # Runtime 核验：sha256sum 只用于冻结 deployed file identity。
    # Runtime 核验：ros2 param 只允许 get/list，不允许 set。
    # Runtime 核验：HTTP 类别只允许 GET。
    # Runtime 核验：motion 计数必须为零。
    # Runtime 核验：control 与 stop 计数必须为零。
    # Runtime 核验：service mutation 计数必须为零。
    # Runtime 核验：UART write 计数必须为零。
    # Runtime 核验：firmware mutation 计数必须为零。
    # Runtime 核验：runtime mainType 缺失必须显式为 null。
    # Runtime 核验：firmware identity 缺失必须显式为 null。
    # Runtime 核验：类别声明不能替代命令文本前缀检查。
    # Runtime 核验：shell 组合符可能隐藏第二条写命令，因此全部拒绝。
    # Runtime 核验：systemctl start/stop/restart/enable/disable 全部拒绝。
    # Runtime 核验：ros2 param set 与 topic pub 全部拒绝。
    # Runtime 核验：base manual/stop endpoint 全部拒绝。
    # Runtime 核验：HTTP POST/PUT/PATCH/DELETE 全部拒绝。
    if runtime_inventory_json is None:
        return {
            "provided": False,
            "valid": True,
            "status": "not_provided",
            "errors": [],
            "input_artifact": None,
            "observations": {"runtime_main_type": None, "firmware_identity": None},
        }

    errors: list[str] = []
    value = _read_json(runtime_inventory_json, errors)
    inventory = value or {}
    required_top_level = ("schema", "readonly_only", "readonly_allowlist", "commands", "observations", "safety_counters")
    for key in required_top_level:
        if key not in inventory:
            errors.append(f"runtime_inventory_missing_field:{key}")
    if inventory.get("schema") != RUNTIME_INVENTORY_SCHEMA:
        errors.append(f"runtime_inventory_schema_conflict:{inventory.get('schema')}")
    if inventory.get("readonly_only") is not True:
        errors.append("runtime_inventory_not_readonly")

    # artifact 自报 allowlist 必须是已批准类别的非空子集。
    allowlist = inventory.get("readonly_allowlist")
    if not isinstance(allowlist, list) or not allowlist:
        errors.append("runtime_inventory_invalid_allowlist")
        allowlist_set: set[str] = set()
    else:
        allowlist_set = {item for item in allowlist if isinstance(item, str)}
        if len(allowlist_set) != len(allowlist) or not allowlist_set <= READONLY_COMMAND_CATEGORIES:
            errors.append(f"runtime_inventory_unapproved_allowlist:{sorted(allowlist_set - READONLY_COMMAND_CATEGORIES)}")

    # 每条远端命令都必须有类别、命令文本、exit code 与脱敏摘要。
    commands = inventory.get("commands")
    if not isinstance(commands, list):
        errors.append("runtime_inventory_commands_not_list")
        commands = []
    for index, command in enumerate(commands):
        if not isinstance(command, dict):
            errors.append(f"runtime_inventory_command_not_object:{index}")
            continue
        category = command.get("category")
        if category not in allowlist_set or category not in READONLY_COMMAND_CATEGORIES:
            errors.append(f"runtime_inventory_command_category_rejected:{index}:{category}")
        command_text = command.get("command")
        prefixes = READONLY_COMMAND_PREFIXES.get(category, ())
        if (
            not isinstance(command_text, str)
            or not any(command_text.strip().startswith(prefix) for prefix in prefixes)
            or any(token in command_text for token in UNSAFE_COMMAND_TOKENS)
        ):
            errors.append(f"runtime_inventory_command_text_rejected:{index}:{category}")
        for field in ("command", "exit_code", "stdout_summary", "stderr_summary"):
            if field not in command:
                errors.append(f"runtime_inventory_command_missing:{index}:{field}")

    # 所有 mutation/control 计数必须精确为零。
    safety_counters = inventory.get("safety_counters")
    if not isinstance(safety_counters, dict):
        errors.append("runtime_inventory_safety_counters_not_object")
        safety_counters = {}
    for key in (
        "motion",
        "control",
        "stop",
        "nonzero",
        "service_mutation",
        "uart_write",
        "firmware_mutation",
    ):
        if safety_counters.get(key) != 0:
            errors.append(f"runtime_inventory_nonzero_safety_counter:{key}:{safety_counters.get(key)}")

    # observations 必须显式保留 null，不能把字段缺失解释成未观察。
    observations = inventory.get("observations")
    if not isinstance(observations, dict):
        errors.append("runtime_inventory_observations_not_object")
        observations = {}
    for key in ("runtime_main_type", "firmware_identity", "bridge_command_mode", "deployed_bridge_sha256"):
        if key not in observations:
            errors.append(f"runtime_inventory_observation_missing:{key}")
    runtime_main_type = observations.get("runtime_main_type")
    if runtime_main_type is not None and runtime_main_type not in (1, 2, 3):
        errors.append(f"runtime_inventory_invalid_main_type:{runtime_main_type}")
    firmware_identity = observations.get("firmware_identity")
    if firmware_identity is not None and (not isinstance(firmware_identity, str) or not firmware_identity.strip()):
        errors.append("runtime_inventory_invalid_firmware_identity")

    input_artifact = None
    if runtime_inventory_json.is_file():
        input_artifact = {
            "name": runtime_inventory_json.name,
            "sha256": _sha256(runtime_inventory_json),
            "size_bytes": runtime_inventory_json.stat().st_size,
        }
    return {
        "provided": True,
        "valid": not errors,
        "status": "valid_readonly_inventory" if not errors else "artifact_inconsistent_or_invalid",
        "errors": errors,
        "input_artifact": input_artifact,
        "readonly_allowlist": allowlist if isinstance(allowlist, list) else [],
        "commands": commands,
        "safety_counters": safety_counters,
        "observations": observations,
    }


def _candidate(
    candidate_id: str,
    priority: int,
    status: str,
    evidence_refs: list[str],
    confidence_boundary: str,
    requires_maintenance: bool,
    next_action: str,
) -> dict[str, Any]:
    """构建稳定 candidate 结构，避免字段随分支漂移。"""
    # 每个 candidate 都有自己的边界与动作，顶层再只选一个下一动作。
    return {
        "candidate_id": candidate_id,
        "priority": priority,
        "status": status,
        "evidence_refs": evidence_refs,
        "confidence_boundary": confidence_boundary,
        "requires_maintenance": requires_maintenance,
        "next_readonly_or_maintenance_action": next_action,
    }


def _build_candidates(
    vendor: dict[str, Any],
    v8: dict[str, Any],
    runtime: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """按证据强度排序根因候选并给出唯一下一维护动作。"""
    # v8 已证明 command transport 和 bridge-parser 同窗 0/0；encoder 更新链最靠近未证根因。
    # 候选排序：encoder 更新链距离零反馈事实最近，因此优先级最高。
    # 候选排序：mainType 影响参数和控制分支，但当前没有 ESP32 runtime 值。
    # 候选排序：firmware identity 决定本地源码能否代表板上实现。
    # 候选排序：sampling 已有三帧同窗证据，所以不排在 encoder 前。
    # 候选排序：parser 逐帧一致，因此当前不是优先修复对象。
    # 候选排序：artifact invalid 仅在所有输入通过时才能排除。
    # 证据边界：vendor function 存在不代表 encoder counter 发生变化。
    # 证据边界：bridge configured mainType 不代表 ESP32 runtime mainType。
    # 证据边界：source version 字符串不代表 deployed build hash。
    # 证据边界：bridge timestamp 不等于 raw UART byte timestamp。
    # 证据边界：normalized alias 一致只排除已观察 frame 的 parser 映射冲突。
    # 维护约束：读取 runtime identity 需要独立维护授权。
    # 维护约束：UART 独占不能由普通运动授权推导。
    # 维护约束：firmware instrumentation 不能由本 CLI 自动执行。
    # 维护约束：encoder counter 可观测前不得发起新 motion retry。
    # 维护约束：即使 runtime mainType=1，也仍需观察 raw counter delta。
    # 维护约束：即使 firmware hash 匹配，也不能自动判定 encoder 正常。
    # 维护约束：raw UART 采样只在 encoder counter 非零后成为次级入口。
    # 维护约束：parser 保持不变，除非 raw bytes 与 bridge frame 冲突。
    # 维护约束：唯一下一动作同时冻结 identity 并建立 counter 可观测性。
    observations = runtime.get("observations", {})
    runtime_main_type = observations.get("runtime_main_type") if isinstance(observations, dict) else None
    firmware_identity = observations.get("firmware_identity") if isinstance(observations, dict) else None

    # runtime inventory 未观察到的字段必须保持 not_observed，不能从 source default 补齐。
    main_type_status = "observed" if runtime_main_type in (1, 2, 3) else "not_observed"
    firmware_status = "observed" if isinstance(firmware_identity, str) and firmware_identity.strip() else "not_observed"

    candidates = [
        _candidate(
            "encoder_update_path_not_observed",
            1,
            "highest_priority_unconfirmed",
            [
                "vendor:setup_initializes_encoders",
                "vendor:loop_refreshes_left_encoder",
                "vendor:loop_refreshes_right_encoder",
                "v8:during_window_t1001_frames=3",
                "v8:during_window_pairs=0/0,0/0,0/0",
            ],
            "Vendor source proves the reference update path exists; v8 proves zero output, not why encoder counters stayed zero.",
            True,
            "在独占维护窗口先冻结 runtime firmware/mainType，再增加或读取 raw encoder A/B counter delta；不得先重试运动。",
        ),
        _candidate(
            "runtime_main_type_not_observed",
            2,
            main_type_status,
            ["vendor:source_default_main_type_wave_rover", "runtime:runtime_main_type"],
            "Source default mainType=1 is not proof of the value running on the ESP32.",
            runtime_main_type is None,
            "在获批维护窗口读取或由受控 firmware instrumentation 回报 runtime mainType。",
        ),
        _candidate(
            "runtime_firmware_identity_not_observed",
            3,
            firmware_status,
            ["vendor:WAVE_ROVER_V0.9.ino", "runtime:firmware_identity"],
            "Local V0.9 source is a reference until the deployed ESP32 binary/build identity is matched.",
            firmware_identity is None,
            "在获批维护窗口冻结 ESP32 deployed firmware build/hash identity，不刷写 firmware。",
        ),
        _candidate(
            "feedback_sampling_alignment_not_proven",
            4,
            "partially_excluded_bridge_debug_only",
            [
                "v8:command_window_timestamps",
                "v8:during_window_t1001_frames=3",
                "v8:raw_serial_byte_capture=false",
            ],
            "Bridge-debug timestamps align three frames with the command window, but byte-for-byte UART timing is absent.",
            True,
            "若 encoder counters 非零，再在独占 UART 维护窗口获取只读 raw frame timing；此前不优先消费该候选。",
        ),
        _candidate(
            "bridge_parser_consistent_with_vendor_frame",
            5,
            "observed",
            ["v8:normalized_left_right_equal_vendor_frame", "vendor:t1001_left_source", "vendor:t1001_right_source"],
            "Consistency is proven for frozen bridge debug rows, not for unseen raw serial bytes.",
            False,
            "保留现有 parser；除非 raw UART 与 bridge debug 冲突，不修改 parser。",
        ),
        _candidate(
            "artifact_inconsistent_or_invalid",
            6,
            "excluded_inputs_valid" if vendor.get("valid") and v8.get("valid") and runtime.get("valid") else "confirmed",
            ["vendor:validation", "v8:validation", "runtime:validation"],
            "This candidate is excluded only when every required input and safety assertion passes.",
            False,
            "修复输入一致性后重新离线运行诊断；不得用坏 artifact 推动维护或运动。",
        ),
    ]

    # 唯一动作先解决 runtime identity 与 encoder counter 可观测性，避免再猜 sampling/parser。
    unique_action = {
        "action_id": "maintenance_freeze_runtime_identity_then_observe_raw_encoder_counters",
        "requires_explicit_service_uart_firmware_maintenance_authorization": True,
        "motion_authorized_by_this_diagnostic": False,
        "action": (
            "取得独占 service/UART/firmware 维护授权后，先冻结 deployed ESP32 firmware identity 与 runtime mainType，"
            "再增加或读取 raw encoder A/B counter delta；在 counter path 可观测前不批准新的 motion retry。"
        ),
    }
    return candidates, unique_action


def build_root_cause_diagnostic(
    v8_artifact_dir: str | Path,
    vendor_source_root: str | Path,
    runtime_inventory_json: str | Path | None = None,
) -> dict[str, Any]:
    """构建离线/fail-closed root-cause diagnostic。"""
    # 三类输入独立验证，最终错误统一决定顶层 status 与退出码。
    v8 = _validate_v8(Path(v8_artifact_dir))
    vendor = _validate_vendor_sources(Path(vendor_source_root))
    runtime = _validate_runtime_inventory(Path(runtime_inventory_json) if runtime_inventory_json is not None else None)
    all_errors = [*vendor["errors"], *v8["errors"], *runtime["errors"]]
    inputs_valid = not all_errors

    # 输入无效时只保留 artifact 根因，不继续输出伪精确硬件排序。
    if inputs_valid:
        candidates, unique_action = _build_candidates(vendor, v8, runtime)
        status = "diagnostic_complete_fail_closed"
        primary_classification = "encoder_update_path_not_observed"
    else:
        candidates = [
            _candidate(
                "artifact_inconsistent_or_invalid",
                1,
                "confirmed",
                ["diagnostic:validation_errors"],
                "No hardware root-cause ranking is valid until all required inputs pass.",
                False,
                "修复缺失、冲突或危险输入后只重跑离线 CLI；不要执行维护或运动。",
            )
        ]
        unique_action = {
            "action_id": "repair_diagnostic_inputs_only",
            "requires_explicit_service_uart_firmware_maintenance_authorization": False,
            "motion_authorized_by_this_diagnostic": False,
            "action": "修复缺失、冲突或危险输入后只重跑离线 CLI；不要执行维护或运动。",
        }
        status = "artifact_inconsistent_or_invalid"
        primary_classification = "artifact_inconsistent_or_invalid"

    # 安全字段与当前运行计数无论输入是否有效都固定 fail closed。
    result: dict[str, Any] = {
        "schema": SCHEMA,
        "status": status,
        "proof_boundary": PROOF_BOUNDARY,
        "input_valid": inputs_valid,
        "validation_errors": all_errors,
        "primary_classification": primary_classification,
        "hil_pass": False,
        "safe_to_control": False,
        "route_execution_success": False,
        "delivery_success": False,
        **CURRENT_RUN_ZERO_COUNTERS,
        "vendor_validation": vendor,
        "v8_validation": v8,
        "runtime_inventory_validation": runtime,
        "root_cause_candidates": candidates,
        "unique_next_maintenance_action": unique_action,
        "not_proven": [
            "deployed_esp32_firmware_matches_local_vendor_source",
            "runtime_main_type",
            "raw_encoder_counter_delta",
            "raw_uart_byte_timing",
            "nonzero_wheel_feedback",
            "hil_pass",
            "safe_to_control",
        ],
    }
    return result


def main(argv: list[str] | None = None) -> int:
    """CLI 入口：只读输入并写出结构化诊断。"""
    # 参数不包含 host、UART 或 control endpoint，结构上避免误触硬件。
    parser = argparse.ArgumentParser(description="Diagnose frozen WAVE ROVER zero wheel feedback artifacts.")
    parser.add_argument("--v8-artifact-dir", required=True)
    parser.add_argument("--vendor-source-root", required=True)
    parser.add_argument("--runtime-inventory-json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)

    # 输出文件是唯一写操作，且由调用方显式指定到本地 sprint artifacts。
    result = build_root_cause_diagnostic(
        v8_artifact_dir=args.v8_artifact_dir,
        vendor_source_root=args.vendor_source_root,
        runtime_inventory_json=args.runtime_inventory_json,
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(args.output)

    # 正常诊断即便成功也保持 HIL false；输入错误使用稳定非零 exit。
    return 0 if result["input_valid"] else 4


if __name__ == "__main__":
    raise SystemExit(main())
