#!/usr/bin/env python3
"""WAVE ROVER runtime identity/raw encoder 独占维护 runner。"""

# 本脚本只依赖 Python 标准库，避免维护窗口被本地第三方依赖阻塞。
# 真机串口依赖在远端窗口内单独盘点，并由远端 pyserial 承担。
# 维护流程固定为 Phase S→0→1→条件式2→条件式3→4。
# 任何失败都必须生成结构化 artifact，并进入恢复分支。
# 真实入口只有一次 SSH 子进程，不在 Python 内做任何自动重试。
#
# 安全合同 001：fixture 只证明 schema 与 fail-closed 逻辑，不证明现场 UART。
# 安全合同 002：fixture 的 maintenance_window_count 固定为零，不能冒充 live。
# 安全合同 003：真实模式只接受 plan 冻结的 SSH host，拒绝目标地址漂移。
# 安全合同 004：真实模式只接受 plan 冻结的 SSH port，拒绝备用端口猜测。
# 安全合同 005：authorization_id 必须显式传入，不能复用旧 v8 identity。
# 安全合同 006：attempt_id 必须显式传入，不能把两次现场窗口合并。
# 安全合同 007：本地 vendor 文件缺失时在 SSH 之前停止，避免无来源上车。
# 安全合同 008：vendor hash 使用当前工作树内容，确保现场 artifact 可追溯。
# 安全合同 009：远端 request 在发送前计算 SHA，证明唯一 stdin payload。
# 安全合同 010：SSH subprocess 只出现一次，不用循环实现 transport retry。
# 安全合同 011：SSH 超时也只落盘 blocker，禁止再次调用同一 live runner。
# 安全合同 012：远端输出必须有且只有一个 JSON marker，防止日志拼接污染。
# 安全合同 013：artifact 初始安全字段全部为 false，现场流程不能抬高。
# 安全合同 014：artifact 对缺字段 fail closed，不以 Python 默认值掩盖缺失。
# 安全合同 015：maintenance_window_count 记录窗口，不把 fixture 计入。
# 安全合同 016：inventory_invocation_count 记录一次 Phase 0 冻结。
# 安全合同 017：pre_stop_invocation_count 记录逻辑调用，不记录 HTTP retry。
# 安全合同 018：service_stop_count 最多一次，保持原始 service ownership。
# 安全合同 019：holder_termination_count 仅在 exact identity 匹配时增加。
# 安全合同 020：uart_open_count 最多一次，避免两个 reader 争抢反馈。
# 安全合同 021：t900_write_count 最多一次，避免 runtime mode 多次漂移。
# 安全合同 022：instrumentation_build_count 最多一次，禁止手工补跑构建。
# 安全合同 023：instrumentation_flash_count 最多一次，禁止手工二次上传。
# 安全合同 024：rollback_flash_count 最多一次，只允许本轮 backup 回滚。
# 安全合同 025：nonzero_motion_invocation_count 最多一次，参数不可变。
# 安全合同 026：post_stop_invocation_count 只在 nonzero 后记录逻辑 stop。
# 安全合同 027：final_stop_verification_count 固定一次，发生在 service 恢复后。
# 安全合同 028：retry_count 永远为零，失败事实不能触发自动重试。
# 安全合同 029：second_motion_count 永远为零，禁止换参数再试。
# 安全合同 030：Phase 0 先冻结 service，再执行任何 mutation。
# 安全合同 031：Phase 0 先冻结 holder PID/start/cmd hash，再允许终止。
# 安全合同 032：Phase 0 只保存 host hash prefix，不泄露完整主机名。
# 安全合同 033：Phase 0 只保存 basename/hash，不泄露无关绝对路径。
# 安全合同 034：Phase 0 toolchain 只保存 availability，不保存完整环境。
# 安全合同 035：Phase 0 health GET 不产生 motion，不提升 live_control_delta。
# 安全合同 036：Phase 0 base status GET 只做 current readback。
# 安全合同 037：pre-stop 必须看到 vendor zero 语义，HTTP 200 单独不够。
# 安全合同 038：pre-stop 不确认时禁止 stop service，保持原状态。
# 安全合同 039：service stop 后必须再次读 ActiveState，不能假定成功。
# 安全合同 040：service 仍 active 时禁止 UART open，避免并发 reader。
# 安全合同 041：lsof 缺失不等于 holder empty，继续用 fuser 交叉检查。
# 安全合同 042：fuser 只读使用，永远不传入 -k。
# 安全合同 043：禁止 killall，因为它无法证明进程 identity。
# 安全合同 044：禁止 pkill，因为名称匹配可能影响无关 ROS 进程。
# 安全合同 045：SIGTERM 前再次比对 PID/start/cmd hash。
# 安全合同 046：SIGKILL 只在 TERM 后 exact identity 仍成立时允许。
# 安全合同 047：holder PID 消失视为已释放，不继续发送 kill。
# 安全合同 048：holder PID 被复用视为 identity 漂移，禁止终止。
# 安全合同 049：串口路径必须真实存在，不能根据 vendor RPi 路径猜测。
# 安全合同 050：串口参数固定为目标现场 `/dev/ttyS5@115200`。
# 安全合同 051：pyserial 缺失时保持 motion=0，并进入恢复。
# 安全合同 052：UART write 使用 UTF-8 newline-delimited JSON。
# 安全合同 053：UART 指令形状由 allowlist 校验，禁止任意 JSON。
# 安全合同 054：T=143 只用于打开 current echo，不能证明 runtime。
# 安全合同 055：T=142 只设置 feedback interval，不证明 encoder。
# 安全合同 056：T=131 只打开 feedback flow，不证明 counter delta。
# 安全合同 057：T=900 只设置 main/module，不把 echo 解释为 readback。
# 安全合同 058：T=130 只请求 current T=1001，不代表非零反馈。
# 安全合同 059：T=11 零帧用于安全停止，不计入 nonzero motion。
# 安全合同 060：T=11 非零帧参数固定 L=164、R=164。
# 安全合同 061：唯一非零窗口固定最长 300ms，不允许延长。
# 安全合同 062：RX 普通启动文本可以忽略，但 hash 仍可追踪。
# 安全合同 063：RX 非 JSON 不能作为 runtime/counter 证据。
# 安全合同 064：RX 非 object JSON 不能作为 frame 证据。
# 安全合同 065：只有 T=1001 才进入 wheel feedback 样本。
# 安全合同 066：T=1001 的 L/R 来自 vendor speedGetA/speedGetB。
# 安全合同 067：L/R 非零只记录 feedback_nonzero，不自动判 HIL。
# 安全合同 068：raw encA 必须为非 bool 整数。
# 安全合同 069：raw encB 必须为非 bool 整数。
# 安全合同 070：raw counter 至少两样本才计算 delta。
# 安全合同 071：counter delta 为零也是有效 current 事实。
# 安全合同 072：counter delta 非零也不自动证明 safe-to-control。
# 安全合同 073：runtime mainType 必须来自 machine-readable feedback。
# 安全合同 074：源码默认 mainType=1 不能替代 runtime 观察。
# 安全合同 075：T=900 echo 的 main=1 不能替代 runtime 观察。
# 安全合同 076：moduleType 必须来自 machine-readable feedback。
# 安全合同 077：firmware build id 必须来自 machine-readable feedback。
# 安全合同 078：counter/runtime/firmware 三类同时齐全才开 observability gate。
# 安全合同 079：observability gate false 时 nonzero motion 必须为零。
# 安全合同 080：observability gate true 仍需 CLI 显式 motion 开关。
# 安全合同 081：motion 后立即写 direct UART zero，不等待分析结果。
# 安全合同 082：motion 结果不理想时禁止 retry。
# 安全合同 083：无 motion 时释放 UART 前仍写最终 zero。
# 安全合同 084：UART exception 时 finally 尝试唯一安全 zero。
# 安全合同 085：UART close 失败必须进入 errors，不得静默。
# 安全合同 086：instrumentation 只在 raw fields 缺失时标记 required。
# 安全合同 087：instrumentation required 不等于 instrumentation success。
# 安全合同 088：build success 不等于 flash success。
# 安全合同 089：flash success 不等于 runtime readback success。
# 安全合同 090：instrumentation success 不等于 HIL。
# 安全合同 091：instrumentation success 不等于 route execution。
# 安全合同 092：instrumentation success 不等于 delivery。
# 安全合同 093：instrumentation success 不等于 mission attempt。
# 安全合同 094：没有 dedicated verified upload alias 时禁止 backup/flash。
# 安全合同 095：不能把 LiDAR `/dev/ttyACM0` 猜成 ESP32 upload port。
# 安全合同 096：不能把 operational `/dev/ttyS5` 猜成 bootloader upload port。
# 安全合同 097：platformio 缺失时 build_count 保持零。
# 安全合同 098：backup gate 不绿时 build_count 保持零。
# 安全合同 099：backup gate 不绿时 flash_count 保持零。
# 安全合同 100：factory binary 只读，不作为默认 rollback image。
# 安全合同 101：本轮没有 flash 时 rollback 是显式 no-op。
# 安全合同 102：未来若 flash，rollback 必须先于 service 恢复。
# 安全合同 103：service 初始 active 时最终必须恢复 active。
# 安全合同 104：service 初始 inactive 时不能擅自长期启动。
# 安全合同 105：service start 最多一次，不循环重启。
# 安全合同 106：service state 恢复后才检查 holder 归还。
# 安全合同 107：原来有 holder 时，恢复后必须重新观察到 holder。
# 安全合同 108：holder PID 可以因 service restart 改变，但 ownership 要恢复。
# 安全合同 109：deployed hash before/after 用于识别非计划代码漂移。
# 安全合同 110：本轮不写远端仓库，因此 deployed hash 理应相等。
# 安全合同 111：final stop 发生在 service/holder 恢复之后。
# 安全合同 112：final stop HTTP success 单独不能证明 wheel stopped。
# 安全合同 113：final base status 必须包含明确 zero evidence。
# 安全合同 114：zero evidence 只接受 T=1/T=11/T=13/T=1001 语义。
# 安全合同 115：任意其它字段值为零不能误判为 stopped。
# 安全合同 116：final stop 不确认时 `final_stopped=false`。
# 安全合同 117：service 不恢复时 `service_restored=false`。
# 安全合同 118：holder 不恢复时 `holder_restored=false`。
# 安全合同 119：恢复失败时 operator 必须继续物理限位。
# 安全合同 120：run-owned residual 明确记录，不泛化删除 `/tmp`。
# 安全合同 121：只允许精确 attempt 目录作为临时目录。
# 安全合同 122：artifact 无凭证、Wi-Fi 配置或完整环境变量。
# 安全合同 123：command ledger 不保存原始敏感 stdout。
# 安全合同 124：command ledger 保存 started/ended/exit 便于复核。
# 安全合同 125：command ledger 的 summary 截断，避免无界 artifact。
# 安全合同 126：SSH stderr 只保留短摘要，避免泄露无关配置。
# 安全合同 127：artifact 输出使用稳定排序，便于 diff。
# 安全合同 128：artifact 输出使用 UTF-8，保留中文 blocker。
# 安全合同 129：JSON parse 失败使用 exit 4，不触发 live retry。
# 安全合同 130：hostile fixture 不写 output，避免伪完成。
# 安全合同 131：bool counter 明确拒绝，避免 Python int 子类陷阱。
# 安全合同 132：危险字段 true 被 validator 独立列出。
# 安全合同 133：motion_without_observability 被 validator 独立列出。
# 安全合同 134：motion_without_post_stop 被 validator 独立列出。
# 安全合同 135：retry/second motion 非零被 validator 独立列出。
# 安全合同 136：fixture 与 live 的 window count 由 validator 区分。
# 安全合同 137：fixture service/holder 只是 schema 样例，不是现场事实。
# 安全合同 138：live transport 失败时不虚构 remote restoration。
# 安全合同 139：live transport 失败仍写 current blocker artifact。
# 安全合同 140：live artifact validator errors 原样留给 Product。
# 安全合同 141：Hardware 不调整 OKR 百分比。
# 安全合同 142：Hardware 不归档 KR。
# 安全合同 143：Hardware 不创建 side2side_check。
# 安全合同 144：Hardware 不创建 final.md。
# 安全合同 145：Hardware 不 commit 或 push。
# 安全合同 146：Hardware 不修改 vendor source。
# 安全合同 147：Hardware 不覆盖 factory firmware。
# 安全合同 148：Hardware 不修改 workstation 或 Nav2。
# 安全合同 149：Hardware 最终只报告 current evidence 与风险。
# 安全合同 150：Product owner 依据 artifact 做保守验收。
# 安全合同 151：T=900 发送记录不能替代 runtime mainType readback。
# 安全合同 152：源码默认 mainType=1 不能替代目标板运行态证据。
# 安全合同 153：静止 raw counter 为零不能证明 encoder 链正常。
# 安全合同 154：counter 字段存在不能证明真实运动反馈成功。
# 安全合同 155：feedback L/R 非零不能独立证明路线执行。
# 安全合同 156：工具链可用不能独立证明 instrumentation 成功。
# 安全合同 157：build 成功不能独立证明 upload 或 flash 成功。
# 安全合同 158：flash 成功不能跳过 rollback 与 service 恢复验证。
# 安全合同 159：最终 zero 命令必须配合 current status readback。
# 安全合同 160：operator 看护不放宽 exactly-once 与 no-retry 合同。
# 安全合同 161：路线清空不放宽 UART holder identity 检查。
# 安全合同 162：物理限位不允许跳过 pre-stop 或 post-stop。
# 安全合同 163：运动授权不允许发送 allowlist 之外的 JSON 指令。
# 安全合同 164：部署授权不允许修改 vendor 或 factory binary。
# 安全合同 165：任何失败都保持五个 mission/HIL 字段为 false。

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import subprocess
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# schema 和危险字段固定，避免 fixture/live 两条路径产生语义漂移。
SCHEMA = "trashbot.wave_rover.runtime_identity_raw_encoder_maintenance.v1"
SAFETY_FALSE_FIELDS = (
    "hil_pass",
    "safe_to_control",
    "route_execution_success",
    "delivery_success",
    "mission_attempt",
)

# 现场事实来自 tech-plan 冻结值，CLI 只允许再次显式传入同一组值。
EXPECTED_HOST = "root@192.168.1.11"
EXPECTED_PORT = 37878
EXPECTED_AUTHORIZATION_ID = "ceo_20260728_complete_motion_deploy_service_uart_firmware_maintenance"
EXPECTED_ATTEMPT_ID = "o1-runtime-identity-raw-encoder-maintenance-attempt-1"
SERIAL_PORT = "/dev/ttyS5"
SERIAL_BAUDRATE = 115200
SERVICE = "trashbot-esp32-bridge.service"

# 这些 vendor 文件已由 Product plan 指定，缺失或 hash 失败必须在 live 前停止。
VENDOR_FILES = (
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_config.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/WAVE_ROVER_V0.9.ino",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
)

# 只冻结 bridge/source/unit basename 与 hash，不把远端绝对路径写入 artifact。
DEPLOYED_PATHS = (
    "/root/rober/onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge_node.py",
    "/root/rober/onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_feedback.py",
    "/root/rober/onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_protocol.py",
    "/root/rober/onboard/scripts/esp32_bridge_http.sh",
    "/etc/systemd/system/trashbot-esp32-bridge.service",
)


# 远端程序通过唯一 SSH stdin 发送；它不修改仓库，只使用精确 run-owned /tmp。
# 所有远端命令都由 argv 数组执行，禁止 shell、killall、pkill 或 fuser -k。
# HTTP 操作固定为 Upper 的 health/status/stop 三个入口。
# UART 指令固定为 vendor allowlist，不接受任何运行时字符串拼接指令。
REMOTE_SCRIPT = r'''
import hashlib
import json
import os
import signal
import shutil
import stat
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CONFIG = json.loads(CONFIG_JSON)
SERVICE = CONFIG["service"]
SERIAL_PORT = CONFIG["serial_port"]
BAUDRATE = CONFIG["serial_baudrate"]
RUN_DIR = Path("/tmp") / ("trashbot-o1-runtime-encoder-" + CONFIG["attempt_id"])

# artifact 从一开始就是 fail-closed；只有现场证据允许补充事实，安全字段永不抬高。
def now():
    return datetime.now(timezone.utc).isoformat()

def blank_result():
    return {
        "schema": CONFIG["schema"],
        "attempt_id": CONFIG["attempt_id"],
        "authorization_id": CONFIG["authorization_id"],
        "captured_at": now(),
        "host_identity_hash_prefix": None,
        "vendor_source_hashes": CONFIG["vendor_source_hashes"],
        "deployed_file_hashes_before": {},
        "deployed_file_hashes_after": {},
        "firmware_identity_before": None,
        "firmware_identity_after": None,
        "runtime_main_type_before": None,
        "runtime_main_type_after": None,
        "module_type_before": None,
        "module_type_after": None,
        "raw_encoder_a_samples": [],
        "raw_encoder_b_samples": [],
        "raw_counter_delta_a": None,
        "raw_counter_delta_b": None,
        "t1001_samples": [],
        "feedback_nonzero_observed": False,
        "counter_feedback_observability_gate": False,
        "toolchain_inventory": {},
        "instrumentation_required": False,
        "instrumentation_success": False,
        "instrumented_source_hash": CONFIG["instrumented_source_hash"],
        "instrumented_build_image_hash": None,
        "flash_backup_hash": None,
        "build_count": 0,
        "flash_count": 0,
        "instrumentation_build_count": 0,
        "instrumentation_flash_count": 0,
        "diagnostic_deploy_count": 0,
        "runner_invocation_count": 1,
        "maintenance_window_count": 1,
        "inventory_invocation_count": 0,
        "pre_stop_invocation_count": 0,
        "service_stop_count": 0,
        "holder_termination_count": 0,
        "uart_open_count": 0,
        "uart_write_frame_count": 0,
        "invalid_uart_frame_count": 0,
        "raw_uart_stop_frame_count": 0,
        "t900_write_count": 0,
        "rollback_flash_count": 0,
        "nonzero_motion_invocation_count": 0,
        "post_stop_invocation_count": 0,
        "final_stop_verification_count": 0,
        "service_restore_count": 0,
        "retry_count": 0,
        "second_motion_count": 0,
        "phase_counts": {"S": 1, "0": 0, "1": 0, "2": 0, "3": 0, "4": 0},
        "command_ledger": [],
        "uart_frames": [],
        "rollback_manifest": {"required": False, "backup_hash": None},
        "rollback_result": {"attempted": False, "restored": True, "reason": "no_flash_performed"},
        "service_before": {},
        "service_after": {},
        "holder_before": [],
        "holder_after": [],
        "service_restored": False,
        "holder_restored": False,
        "final_stopped": False,
        "run_owned_residual": None,
        "current_run_artifact_delta": 1,
        "external_artifact_delta": 1,
        "live_control_delta": 0,
        "evidence_boundary": "current_exclusive_maintenance_fail_closed_not_hil",
        "status": "running",
        "blockers": [],
        "errors": [],
        "hil_pass": False,
        "safe_to_control": False,
        "route_execution_success": False,
        "delivery_success": False,
        "mission_attempt": False,
    }

RESULT = blank_result()

# 远端命令类别与 argv 必须同时匹配，不能只凭 action 名称放行。
def command_allowed(action, argv):
    exact = {
        "hostname": ["hostname"],
        "uname": ["uname", "-srm"],
        "systemctl_show": [
            "systemctl", "show", SERVICE, "--no-pager",
            "--property=ActiveState,SubState,MainPID,FragmentPath",
        ],
        "lsof_uart_readonly": ["lsof", "-t", SERIAL_PORT],
        "fuser_uart_readonly": ["fuser", SERIAL_PORT],
        "systemctl_stop": ["systemctl", "stop", SERVICE],
        "systemctl_start": ["systemctl", "start", SERVICE],
    }
    if action in exact:
        return argv == exact[action]
    if action == "sha256sum_deployed":
        return len(argv) == 2 and argv[0] == "sha256sum" and argv[1] in CONFIG["deployed_paths"]
    return False

# ledger 只保存动作分类和脱敏摘要，绝不保存完整环境变量或凭证。
def ledger(phase, action, started, exit_code, summary):
    RESULT["command_ledger"].append({
        "phase": phase,
        "action": action,
        "allowed": True,
        "started_at": started,
        "ended_at": now(),
        "exit_code": exit_code,
        "summary": str(summary)[:400],
    })

# 子进程全部有 timeout；即使某个只读工具缺失，也不能拖死 finally 恢复。
def run_cmd(phase, action, argv, timeout=8):
    started = now()
    if not command_allowed(action, argv):
        ledger(phase, action, started, 126, "command_not_allowlisted")
        raise RuntimeError("command_not_allowlisted:" + action)
    try:
        proc = subprocess.run(argv, text=True, capture_output=True, timeout=timeout, check=False)
        ledger(phase, action, started, proc.returncode, "stdout_bytes=%d stderr_bytes=%d" % (
            len(proc.stdout), len(proc.stderr)))
        return proc.returncode, proc.stdout, proc.stderr
    except Exception as exc:
        ledger(phase, action, started, 125, type(exc).__name__)
        return 125, "", str(exc)

# systemd 状态只抽取明确字段，避免把完整 ExecStart 或环境内容写入 artifact。
def service_state(phase):
    code, out, _ = run_cmd(
        phase,
        "systemctl_show",
        ["systemctl", "show", SERVICE, "--no-pager",
         "--property=ActiveState,SubState,MainPID,FragmentPath"],
    )
    values = {}
    for line in out.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            if key in {"ActiveState", "SubState", "MainPID"}:
                values[key] = value
    values["exit_code"] = code
    return values

# holder identity 同时冻结 PID、start ticks 与 cmd hash，PID 复用时绝不误杀。
def process_identity(pid):
    try:
        stat_fields = Path("/proc/%d/stat" % pid).read_text().split()
        raw_cmd = Path("/proc/%d/cmdline" % pid).read_bytes().replace(b"\0", b" ").strip()
        return {
            "pid": pid,
            "start_ticks": stat_fields[21],
            "cmd_hash_prefix": hashlib.sha256(raw_cmd).hexdigest()[:12],
            "expected_bridge": b"esp32_bridge" in raw_cmd,
        }
    except Exception:
        return None

# lsof 优先，fuser 只作补充；不执行任何带 -k 的宽泛终止。
def holders(phase):
    pids = set()
    lsof_code, out, _ = run_cmd(phase, "lsof_uart_readonly", ["lsof", "-t", SERIAL_PORT])
    if lsof_code in (0, 1):
        pids.update(int(v) for v in out.split() if v.isdigit())
    fuser_code, out, err = run_cmd(phase, "fuser_uart_readonly", ["fuser", SERIAL_PORT])
    if fuser_code in (0, 1):
        pids.update(int(v) for v in (out + " " + err).split() if v.isdigit())
    if lsof_code == 125 and fuser_code == 125:
        raise RuntimeError("uart_holder_inventory_tools_unavailable")
    return [item for item in (process_identity(pid) for pid in sorted(pids)) if item]

# hash 通过 sha256sum allowlist 获取；key 仅保留 basename。
def deployed_hashes(phase):
    found = {}
    for path in CONFIG["deployed_paths"]:
        code, out, _ = run_cmd(phase, "sha256sum_deployed", ["sha256sum", path])
        if code == 0 and out.split():
            found[Path(path).name] = out.split()[0]
    return found

# HTTP helper 对响应体设上限；stop 之外只有 GET。
def http_json(phase, action, method, path):
    started = now()
    request = urllib.request.Request(
        "http://127.0.0.1:8787" + path,
        data=b"{}" if method == "POST" else None,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            raw = response.read(2_000_000)
            payload = json.loads(raw.decode("utf-8")) if raw else {}
            ledger(phase, action, started, 0, "http_status=%d bytes=%d" % (response.status, len(raw)))
            return True, payload
    except Exception as exc:
        ledger(phase, action, started, 124, type(exc).__name__)
        return False, {"error_type": type(exc).__name__}

# 深度遍历只寻找明确的 zero vendor command/T1001，不把任意数值零当成停止证明。
def zero_evidence(value):
    if isinstance(value, dict):
        if value.get("T") in (1, 11, 1001) and value.get("L") == 0 and value.get("R") == 0:
            return True
        if value.get("T") == 13 and value.get("X") == 0 and value.get("Z") == 0:
            return True
        return any(zero_evidence(item) for item in value.values())
    if isinstance(value, list):
        return any(zero_evidence(item) for item in value)
    return False

# UART RX 允许普通启动日志存在，但只有合法 JSON object 进入结构化 frame。
def read_frames(ser, duration_s, phase):
    deadline = time.monotonic() + duration_s
    frames = []
    while time.monotonic() < deadline:
        raw = ser.readline()
        if not raw:
            continue
        text = raw.decode("utf-8", errors="replace").strip()
        item = {"observed_at": now(), "sha256": hashlib.sha256(raw).hexdigest(), "parsed": False}
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                item["parsed"] = True
                item["frame"] = parsed
                frames.append(parsed)
        except Exception:
            item["parse_error"] = True
            RESULT["invalid_uart_frame_count"] += 1
        RESULT["uart_frames"].append(item)
    return frames

# TX 只接收脚本内冻结 dict；每一帧均记录 canonical hash 与字节数。
def write_frame(ser, frame, phase, action):
    allowed = (
        {"T": 143, "cmd": 1},
        {"T": 142, "cmd": 0},
        {"T": 131, "cmd": 1},
        {"T": 130},
        {"T": 900, "main": 1, "module": 0},
        {"T": 11, "L": 0, "R": 0},
        {"T": 11, "L": 164, "R": 164},
    )
    if frame not in allowed:
        raise RuntimeError("uart_frame_not_allowlisted")
    raw = (json.dumps(frame, separators=(",", ":")) + "\n").encode("utf-8")
    started = now()
    ser.write(raw)
    ser.flush()
    RESULT["uart_write_frame_count"] += 1
    RESULT["uart_frames"].append({
        "written_at": started,
        "direction": "tx",
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "frame": frame,
    })
    ledger(phase, action, started, 0, "bytes=%d sha256=%s" % (
        len(raw), hashlib.sha256(raw).hexdigest()[:12]))

# additive 字段接受计划定义的 canonical 名称和兼容别名，但必须是同一帧 machine-readable 值。
def extract_observability(frames, sample_class):
    for frame in frames:
        if frame.get("T") != 1001:
            continue
        sample = {"observed_at": now(), "sample_class": sample_class, "frame": frame}
        RESULT["t1001_samples"].append(sample)
        left, right = frame.get("L"), frame.get("R")
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            if left != 0 or right != 0:
                RESULT["feedback_nonzero_observed"] = True
        enc_a = frame.get("encA", frame.get("rawEncoderA"))
        enc_b = frame.get("encB", frame.get("rawEncoderB"))
        if isinstance(enc_a, int) and not isinstance(enc_a, bool):
            RESULT["raw_encoder_a_samples"].append({"observed_at": sample["observed_at"], "value": enc_a, "sample_class": sample_class})
        if isinstance(enc_b, int) and not isinstance(enc_b, bool):
            RESULT["raw_encoder_b_samples"].append({"observed_at": sample["observed_at"], "value": enc_b, "sample_class": sample_class})
        runtime_main = frame.get("mainType", frame.get("main"))
        runtime_module = frame.get("moduleType", frame.get("module"))
        firmware = frame.get("firmwareBuildId", frame.get("fw"))
        if isinstance(runtime_main, int) and not isinstance(runtime_main, bool):
            RESULT["runtime_main_type_after"] = runtime_main
        if isinstance(runtime_module, int) and not isinstance(runtime_module, bool):
            RESULT["module_type_after"] = runtime_module
        if isinstance(firmware, str) and firmware:
            RESULT["firmware_identity_after"] = firmware[:120]
    a = RESULT["raw_encoder_a_samples"]
    b = RESULT["raw_encoder_b_samples"]
    if len(a) >= 2 and len(b) >= 2:
        RESULT["raw_counter_delta_a"] = a[-1]["value"] - a[0]["value"]
        RESULT["raw_counter_delta_b"] = b[-1]["value"] - b[0]["value"]
    RESULT["counter_feedback_observability_gate"] = bool(
        len(a) >= 2 and len(b) >= 2
        and RESULT["runtime_main_type_after"] == 1
        and RESULT["module_type_after"] == 0
        and RESULT["firmware_identity_after"] is not None
        and RESULT["invalid_uart_frame_count"] == 0
    )

# 工具链盘点不把 version 全文写入 artifact，只记录 availability/exit。
def toolchain_inventory():
    inventory = {}
    for name in ("python3", "platformio", "arduino-cli", "esptool.py"):
        started = now()
        resolved = shutil.which(name)
        ledger("0", "command_v_" + name, started, 0 if resolved else 1, "python_shutil_which_no_shell")
        inventory[name] = {"available": bool(resolved), "basename": Path(resolved).name if resolved else None}
    try:
        import serial
        inventory["pyserial"] = {"available": True, "version": getattr(serial, "__version__", "unknown")}
    except Exception as exc:
        inventory["pyserial"] = {"available": False, "error_type": type(exc).__name__}
    upload_alias = Path("/dev/wave_rover_esp32_upload")
    inventory["verified_upload_port"] = {
        "available": upload_alias.exists(),
        "basename": upload_alias.name if upload_alias.exists() else None,
        "verification": "dedicated_alias_only",
    }
    return inventory

# 精确 holder 终止只在 service stop 后仍持有且 identity 未漂移时发生。
def terminate_frozen_holder(frozen, service_main_pid):
    current = {item["pid"]: item for item in holders("1")}
    for old in frozen:
        same = current.get(old["pid"])
        if (
            not same
            or same != old
            or not old.get("expected_bridge")
            or old["pid"] != service_main_pid
        ):
            continue
        started = now()
        os.kill(old["pid"], signal.SIGTERM)
        RESULT["holder_termination_count"] += 1
        ledger("1", "kill_term_exact_holder", started, 0, "pid_identity_matched")
        time.sleep(1)
        again = process_identity(old["pid"])
        if again == old and old["pid"] in {item["pid"] for item in holders("1")}:
            started = now()
            os.kill(old["pid"], signal.SIGKILL)
            ledger("1", "kill_kill_exact_holder", started, 0, "pid_identity_matched_after_term")

# 恢复操作集中在一个 finally，保证 UART exception/transport exception 也走相同路径。
def main():
    serial_handle = None
    flashed = False
    service_was_active = False
    run_dir_created = False
    try:
        RESULT["phase_counts"]["0"] = 1
        RESULT["inventory_invocation_count"] = 1
        # stdin deploy 先创建唯一 run-owned 目录并冻结远端脚本合同 hash。
        RUN_DIR.mkdir(mode=0o700, parents=False, exist_ok=False)
        run_dir_created = True
        (RUN_DIR / "payload.sha256").write_text(CONFIG["remote_script_sha256"] + "\n")
        RESULT["diagnostic_deploy_count"] = 1
        host_code, host_out, _ = run_cmd("0", "hostname", ["hostname"])
        uname_code, uname_out, _ = run_cmd("0", "uname", ["uname", "-srm"])
        if host_code == 0 and uname_code == 0:
            RESULT["host_identity_hash_prefix"] = hashlib.sha256(
                (host_out + uname_out).encode()
            ).hexdigest()[:16]
        RESULT["service_before"] = service_state("0")
        service_was_active = RESULT["service_before"].get("ActiveState") == "active"
        RESULT["holder_before"] = holders("0")
        RESULT["deployed_file_hashes_before"] = deployed_hashes("0")
        RESULT["toolchain_inventory"] = toolchain_inventory()
        http_json("0", "health_get", "GET", "/api/health")
        http_json("0", "base_status_get_before", "GET", "/api/base/status")

        # pre-stop 即使 transport 失败也只调用一次；失败后禁止 service/UART mutation。
        RESULT["pre_stop_invocation_count"] = 1
        pre_ok, pre_payload = http_json("0", "pre_stop_post", "POST", "/api/base/stop")
        if not pre_ok or not zero_evidence(pre_payload):
            RESULT["blockers"].append("pre_stop_not_confirmed")
            return

        RESULT["phase_counts"]["1"] = 1
        if service_was_active:
            RESULT["service_stop_count"] = 1
            code, _, _ = run_cmd("1", "systemctl_stop", ["systemctl", "stop", SERVICE], timeout=15)
            if code != 0:
                RESULT["blockers"].append("service_stop_failed")
                return
        time.sleep(1)
        stopped_state = service_state("1")
        if stopped_state.get("ActiveState") == "active":
            RESULT["blockers"].append("service_still_active")
            return
        remaining = holders("1")
        if remaining:
            terminate_frozen_holder(
                RESULT["holder_before"],
                int(RESULT["service_before"].get("MainPID") or 0),
            )
            time.sleep(1)
            remaining = holders("1")
        if remaining:
            RESULT["blockers"].append("uart_holder_not_exclusive")
            return
        if not Path(SERIAL_PORT).exists():
            RESULT["blockers"].append("serial_port_missing")
            return
        try:
            import serial
        except Exception:
            RESULT["blockers"].append("pyserial_missing")
            return

        # 一个 maintenance window 内只打开 UART 一次。
        started = now()
        serial_handle = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=0.20, write_timeout=1)
        RESULT["uart_open_count"] = 1
        ledger("1", "uart_open_exclusive", started, 0, "device=ttyS5 baud=115200")
        before_frames = read_frames(serial_handle, 0.8, "1")
        extract_observability(before_frames, "before_t900")
        if RESULT["runtime_main_type_after"] is not None:
            RESULT["runtime_main_type_before"] = RESULT["runtime_main_type_after"]
            RESULT["module_type_before"] = RESULT["module_type_after"]
            RESULT["firmware_identity_before"] = RESULT["firmware_identity_after"]

        # T=900 echo 只记 command receipt，不把它提升为 runtime readback。
        for frame, action in (
            ({"T": 143, "cmd": 1}, "uart_echo_enable"),
            ({"T": 142, "cmd": 0}, "feedback_interval_set"),
            ({"T": 131, "cmd": 1}, "feedback_flow_enable"),
            ({"T": 900, "main": 1, "module": 0}, "t900_main_module_set"),
        ):
            write_frame(serial_handle, frame, "1", action)
            if frame["T"] == 900:
                RESULT["t900_write_count"] = 1
        # 三个独立 T=130 readback 提供足够的静止 counter sample 窗口。
        for sample_index in range(3):
            write_frame(
                serial_handle,
                {"T": 130},
                "1",
                "base_feedback_request_%d" % sample_index,
            )
        current_frames = read_frames(serial_handle, 3.0, "1")
        extract_observability(current_frames, "after_t900_no_motion")

        # 缺 raw counter/runtime/build id 时进入条件式 Phase 2，但没有 verified upload alias 就禁止 flash。
        RESULT["instrumentation_required"] = not RESULT["counter_feedback_observability_gate"]
        if RESULT["instrumentation_required"]:
            RESULT["phase_counts"]["2"] = 1
            verified = RESULT["toolchain_inventory"]["verified_upload_port"]["available"]
            platformio_ok = RESULT["toolchain_inventory"]["platformio"]["available"]
            if not CONFIG["allow_instrumentation"]:
                RESULT["blockers"].append("instrumentation_not_authorized")
            if not verified:
                RESULT["blockers"].append("verified_esp32_upload_port_not_observed")
            if not platformio_ok:
                RESULT["blockers"].append("platformio_not_available")
            # 当前 runner 没有同时满足 upload port + backup gate 时，build/flash 必须保持 0。
            RESULT["blockers"].append("instrumentation_backup_upload_gate_not_green")

        # 只有 machine-readable counter/runtime/firmware 三类事实全绿才允许唯一 300ms motion。
        if RESULT["counter_feedback_observability_gate"] and CONFIG["allow_motion"]:
            RESULT["phase_counts"]["3"] = 1
            RESULT["nonzero_motion_invocation_count"] = 1
            RESULT["live_control_delta"] = 1
            write_frame(serial_handle, {"T": 11, "L": 164, "R": 164}, "3", "minimal_motion_once")
            motion_frames = read_frames(serial_handle, 0.3, "3")
            extract_observability(motion_frames, "during_motion")
            write_frame(serial_handle, {"T": 11, "L": 0, "R": 0}, "3", "post_motion_stop")
            RESULT["post_stop_invocation_count"] = 1
            RESULT["raw_uart_stop_frame_count"] += 1
        else:
            # 即使没有 motion，也在释放 UART 前发一帧 vendor zero，防止遗留非零状态。
            write_frame(serial_handle, {"T": 11, "L": 0, "R": 0}, "1", "uart_final_zero")
            RESULT["raw_uart_stop_frame_count"] += 1
    except Exception as exc:
        RESULT["errors"].append({"phase": "runtime", "error_type": type(exc).__name__, "message": str(exc)[:240]})
    finally:
        RESULT["phase_counts"]["4"] = 1
        if serial_handle is not None:
            try:
                if RESULT["raw_uart_stop_frame_count"] == 0:
                    write_frame(serial_handle, {"T": 11, "L": 0, "R": 0}, "4", "exception_final_zero")
                    RESULT["raw_uart_stop_frame_count"] += 1
                serial_handle.close()
                ledger("4", "uart_close", now(), 0, "closed")
            except Exception as exc:
                RESULT["errors"].append({"phase": "4", "error_type": type(exc).__name__, "message": "uart_close_or_zero_failed"})

        # 本实现未进入 flash，因此 rollback 默认 no-op；一旦未来 flash，必须在这里先 rollback 再恢复 service。
        RESULT["rollback_manifest"]["required"] = flashed
        if service_was_active:
            RESULT["service_restore_count"] = 1
            run_cmd("4", "systemctl_start", ["systemctl", "start", SERVICE], timeout=20)
            for _ in range(8):
                if service_state("4").get("ActiveState") == "active":
                    break
                time.sleep(1)
        RESULT["service_after"] = service_state("4")
        RESULT["service_restored"] = (
            RESULT["service_after"].get("ActiveState") == ("active" if service_was_active else RESULT["service_before"].get("ActiveState"))
        )
        time.sleep(1)
        RESULT["holder_after"] = holders("4")
        before_holder_hashes = sorted(
            item.get("cmd_hash_prefix") for item in RESULT["holder_before"]
        )
        after_holder_hashes = sorted(
            item.get("cmd_hash_prefix") for item in RESULT["holder_after"]
        )
        RESULT["holder_restored"] = (
            before_holder_hashes == after_holder_hashes
        )
        RESULT["deployed_file_hashes_after"] = deployed_hashes("4")

        # final stop 是恢复后的唯一验证调用；必须同时看到 zero response/status 才成立。
        RESULT["final_stop_verification_count"] = 1
        stop_ok, stop_payload = http_json("4", "final_stop_post", "POST", "/api/base/stop")
        time.sleep(1)
        status_ok, status_payload = http_json("4", "base_status_get_after", "GET", "/api/base/status")
        RESULT["final_stopped"] = bool(
            stop_ok and zero_evidence(stop_payload)
            and (zero_evidence(status_payload) if status_ok else False)
        )
        # cleanup 只触碰本 attempt 创建的 marker 与精确目录，禁止递归删除。
        if run_dir_created:
            try:
                marker = RUN_DIR / "payload.sha256"
                if marker.is_file():
                    marker.unlink()
                RUN_DIR.rmdir()
            except Exception as exc:
                RESULT["errors"].append({
                    "phase": "4",
                    "error_type": type(exc).__name__,
                    "message": "run_owned_cleanup_failed",
                })
        RESULT["run_owned_residual"] = RUN_DIR.exists()
        if not RESULT["service_restored"]:
            RESULT["blockers"].append("service_not_restored")
        if not RESULT["holder_restored"]:
            RESULT["blockers"].append("holder_not_restored")
        if not RESULT["final_stopped"]:
            RESULT["blockers"].append("final_stop_not_confirmed")
        if RESULT["run_owned_residual"]:
            RESULT["blockers"].append("run_owned_residual_present")
        RESULT["blockers"] = list(dict.fromkeys(RESULT["blockers"]))
        RESULT["status"] = (
            "maintenance_complete_fail_closed"
            if not RESULT["blockers"] and not RESULT["errors"]
            else "maintenance_blocked_fail_closed"
        )
        RESULT["captured_at"] = now()

try:
    main()
except BaseException as exc:
    RESULT["errors"].append({"phase": "outer", "error_type": type(exc).__name__, "message": str(exc)[:240]})
    RESULT["status"] = "maintenance_blocked_fail_closed"
print("O1_MAINTENANCE_JSON:" + json.dumps(RESULT, separators=(",", ":"), sort_keys=True))
'''


# 时间统一输出 UTC ISO，fixture 也因此可被普通 JSON 工具直接消费。
def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# 文件 hash 使用流式读取，避免 vendor 大文件一次性载入内存。
def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


# repo root 从脚本位置稳定推导，不依赖调用者当前目录。
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


# vendor evidence 在 live SSH 之前完整冻结；缺文件时直接拒绝消耗唯一窗口。
def vendor_hashes(root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for relative in VENDOR_FILES:
        path = root / relative
        if not path.is_file():
            raise ValueError(f"missing_vendor_source:{relative}")
        hashes[Path(relative).name] = sha256_file(path)
    if len(hashes) != len(VENDOR_FILES):
        raise ValueError("vendor_source_basename_collision")
    return hashes


# 诊断 patch hash 冻结 additive 字段设计；本轮 backup/upload gate 不绿时不得 build/flash。
def instrumentation_source_hash() -> str:
    patch_contract = (
        'T1001:additive:firmwareBuildId,mainType,moduleType,encA,encB;'
        'preserve:T,L,R,r,p,y,v;source:vendor-V0.9'
    )
    return hashlib.sha256(patch_contract.encode("utf-8")).hexdigest()


# fixture artifact 明确是 mock，不能伪装 maintenance window 或外部 HIL。
def fixture_artifact(payload: dict[str, Any]) -> dict[str, Any]:
    attempt_id = str(payload.get("attempt_id") or "fixture-attempt")
    authorization_id = str(payload.get("authorization_id") or "fixture-authorization")
    raw_a = payload.get("raw_encoder_a", [10, 10])
    raw_b = payload.get("raw_encoder_b", [20, 20])
    if not all(isinstance(value, int) and not isinstance(value, bool) for value in raw_a + raw_b):
        raise ValueError("fixture_raw_counters_must_be_integers")
    result: dict[str, Any] = {
        "schema": SCHEMA,
        "attempt_id": attempt_id,
        "authorization_id": authorization_id,
        "captured_at": utc_now(),
        "host_identity_hash_prefix": "fixture",
        "vendor_source_hashes": payload.get("vendor_source_hashes", {"fixture": "0" * 64}),
        "deployed_file_hashes_before": {"fixture": "1" * 64},
        "deployed_file_hashes_after": {"fixture": "1" * 64},
        "firmware_identity_before": "fixture-fw",
        "firmware_identity_after": "fixture-fw",
        "runtime_main_type_before": 1,
        "runtime_main_type_after": 1,
        "module_type_before": 0,
        "module_type_after": 0,
        "raw_encoder_a_samples": [{"observed_at": utc_now(), "value": value, "sample_class": "fixture"} for value in raw_a],
        "raw_encoder_b_samples": [{"observed_at": utc_now(), "value": value, "sample_class": "fixture"} for value in raw_b],
        "raw_counter_delta_a": raw_a[-1] - raw_a[0],
        "raw_counter_delta_b": raw_b[-1] - raw_b[0],
        "t1001_samples": payload.get("t1001_samples", [{"frame": {"T": 1001, "L": 0, "R": 0, "encA": raw_a[0], "encB": raw_b[0]}}]),
        "feedback_nonzero_observed": False,
        "counter_feedback_observability_gate": True,
        "toolchain_inventory": {"fixture": True},
        "instrumentation_required": False,
        "instrumentation_success": False,
        "instrumented_source_hash": instrumentation_source_hash(),
        "instrumented_build_image_hash": None,
        "flash_backup_hash": None,
        "build_count": 0,
        "flash_count": 0,
        "instrumentation_build_count": 0,
        "instrumentation_flash_count": 0,
        "runner_invocation_count": 1,
        "maintenance_window_count": 0,
        "inventory_invocation_count": 1,
        "pre_stop_invocation_count": 1,
        "service_stop_count": 0,
        "holder_termination_count": 0,
        "uart_open_count": 0,
        "uart_write_frame_count": 0,
        "raw_uart_stop_frame_count": 0,
        "t900_write_count": 0,
        "rollback_flash_count": 0,
        "nonzero_motion_invocation_count": 0,
        "post_stop_invocation_count": 0,
        "final_stop_verification_count": 1,
        "service_restore_count": 0,
        "retry_count": 0,
        "second_motion_count": 0,
        "phase_counts": {"S": 1, "0": 1, "1": 1, "2": 0, "3": 0, "4": 1},
        "command_ledger": [],
        "uart_frames": [],
        "rollback_manifest": {"required": False, "backup_hash": None},
        "rollback_result": {"attempted": False, "restored": True, "reason": "fixture"},
        "service_before": {"ActiveState": "active"},
        "service_after": {"ActiveState": "active"},
        "holder_before": [{"fixture": True}],
        "holder_after": [{"fixture": True}],
        "service_restored": True,
        "holder_restored": True,
        "final_stopped": True,
        "run_owned_residual": False,
        "current_run_artifact_delta": 1,
        "external_artifact_delta": 0,
        "live_control_delta": 0,
        "evidence_boundary": "fixture_only_not_hardware",
        "status": "fixture_complete",
        "blockers": [],
        "errors": [],
        "hil_pass": False,
        "safe_to_control": False,
        "route_execution_success": False,
        "delivery_success": False,
        "mission_attempt": False,
    }
    return result


# validator 覆盖 schema、identity、exactly-once、恢复和危险真值。
def validate_artifact(data: dict[str, Any], *, live: bool) -> list[str]:
    errors: list[str] = []
    required = {
        "schema", "attempt_id", "authorization_id", "vendor_source_hashes",
        "runner_invocation_count", "maintenance_window_count", "inventory_invocation_count",
        "pre_stop_invocation_count", "retry_count", "second_motion_count",
        "nonzero_motion_invocation_count", "counter_feedback_observability_gate",
        "service_restored", "holder_restored", "final_stopped",
    }
    errors.extend(f"missing:{key}" for key in sorted(required - data.keys()))
    if data.get("schema") != SCHEMA:
        errors.append("schema_mismatch")
    if data.get("runner_invocation_count") != 1:
        errors.append("runner_count_not_one")
    if live and data.get("maintenance_window_count") != 1:
        errors.append("maintenance_window_count_not_one")
    if live and data.get("inventory_invocation_count") != 1:
        errors.append("inventory_count_not_one")
    if live and data.get("pre_stop_invocation_count") != 1:
        errors.append("pre_stop_count_not_one")
    if data.get("retry_count") != 0 or data.get("second_motion_count") != 0:
        errors.append("retry_or_second_motion_nonzero")
    bounded_counts = {
        "service_stop_count": (0, 1),
        "holder_termination_count": (0, 1),
        "uart_open_count": (0, 1),
        "t900_write_count": (0, 1),
        "instrumentation_build_count": (0, 1),
        "instrumentation_flash_count": (0, 1),
        "rollback_flash_count": (0, 1),
        "post_stop_invocation_count": (0, 1),
        "service_restore_count": (0, 1),
    }
    for key, (minimum, maximum) in bounded_counts.items():
        value = data.get(key)
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"invalid_count_type:{key}")
        elif not minimum <= value <= maximum:
            errors.append(f"count_out_of_range:{key}:{value}")
    motion = data.get("nonzero_motion_invocation_count")
    if motion not in (0, 1):
        errors.append("motion_count_invalid")
    if motion == 1 and not data.get("counter_feedback_observability_gate"):
        errors.append("motion_without_observability")
    if motion == 1 and data.get("post_stop_invocation_count") != 1:
        errors.append("motion_without_post_stop")
    if data.get("instrumentation_flash_count") == 1:
        if data.get("instrumentation_build_count") != 1:
            errors.append("flash_without_build")
        if not data.get("allow_instrumentation"):
            errors.append("flash_without_authorization")
    if live:
        if data.get("attempt_id") != EXPECTED_ATTEMPT_ID:
            errors.append("attempt_id_mismatch")
        if data.get("authorization_id") != EXPECTED_AUTHORIZATION_ID:
            errors.append("authorization_id_mismatch")
        for field in ("service_restored", "holder_restored", "final_stopped"):
            if data.get(field) is not True:
                errors.append(f"restoration_not_true:{field}")
        if data.get("final_stop_verification_count") != 1:
            errors.append("final_stop_verification_count_not_one")
        if data.get("run_owned_residual") is not False:
            errors.append("run_owned_residual_not_false")
    for field in SAFETY_FALSE_FIELDS:
        if data.get(field) is not False:
            errors.append(f"dangerous_truth:{field}")
    return errors


# artifact 以 sort_keys/indent 稳定落盘，便于 Product 做 scoped diff。
def write_artifact(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


# fixture 只接受 fixture.json，避免目录中的无关文件被隐式合并。
def run_fixture(args: argparse.Namespace) -> int:
    fixture_path = Path(args.fixture_dir) / "fixture.json"
    if not fixture_path.is_file():
        raise ValueError(f"missing_fixture:{fixture_path}")
    payload = json.loads(fixture_path.read_text())
    if not isinstance(payload, dict):
        raise ValueError("fixture_must_be_object")
    result = fixture_artifact(payload)
    errors = validate_artifact(result, live=False)
    if errors:
        raise ValueError("fixture_validation:" + ",".join(errors))
    write_artifact(Path(args.output), result)
    print(args.output)
    print("status=fixture_complete")
    return 0


# SSH stdout 必须包含唯一 marker；任何额外日志均只计入 transport 摘要。
def parse_remote_result(stdout: str) -> dict[str, Any]:
    marker = "O1_MAINTENANCE_JSON:"
    matches = [line[len(marker):] for line in stdout.splitlines() if line.startswith(marker)]
    if len(matches) != 1:
        raise ValueError(f"remote_result_marker_count:{len(matches)}")
    data = json.loads(matches[0])
    if not isinstance(data, dict):
        raise ValueError("remote_result_not_object")
    return data


# 真实 runner 在本函数内仅调用一次 subprocess.run(ssh...)；没有循环和重试。
def run_ssh_maintenance(args: argparse.Namespace) -> int:
    if args.ssh_host != EXPECTED_HOST or args.ssh_port != EXPECTED_PORT:
        raise ValueError("ssh_target_not_frozen")
    if args.authorization_id != EXPECTED_AUTHORIZATION_ID:
        raise ValueError("authorization_id_not_frozen")
    if args.attempt_id != EXPECTED_ATTEMPT_ID:
        raise ValueError("attempt_id_not_frozen")
    root = repo_root()
    config = {
        "schema": SCHEMA,
        "authorization_id": args.authorization_id,
        "attempt_id": args.attempt_id,
        "service": SERVICE,
        "serial_port": SERIAL_PORT,
        "serial_baudrate": SERIAL_BAUDRATE,
        "vendor_source_hashes": vendor_hashes(root),
        "deployed_paths": list(DEPLOYED_PATHS),
        "instrumented_source_hash": instrumentation_source_hash(),
        "remote_script_sha256": hashlib.sha256(
            textwrap.dedent(REMOTE_SCRIPT).encode("utf-8")
        ).hexdigest(),
        "allow_instrumentation": bool(args.allow_instrumentation_build_flash),
        "allow_motion": bool(args.allow_supervised_minimal_motion_after_observability),
    }
    config_json = json.dumps(config, separators=(",", ":"), sort_keys=True)
    remote_source = "CONFIG_JSON = " + repr(config_json) + "\n" + textwrap.dedent(REMOTE_SCRIPT)
    request_sha = hashlib.sha256(remote_source.encode("utf-8")).hexdigest()
    command = [
        "ssh", "-p", str(args.ssh_port),
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=10",
        args.ssh_host, "python3", "-",
    ]

    # 这是本轮唯一真实 maintenance runner transport 调用。
    try:
        completed = subprocess.run(
            command,
            input=remote_source,
            text=True,
            capture_output=True,
            timeout=150,
            check=False,
        )
        result = parse_remote_result(completed.stdout)
        result["ssh_transport"] = {
            "invocation_count": 1,
            "exit_code": completed.returncode,
            "request_sha256": request_sha,
            "stdout_bytes": len(completed.stdout.encode("utf-8")),
            "stderr_bytes": len(completed.stderr.encode("utf-8")),
            "stderr_summary": completed.stderr.strip()[:240],
        }
        if completed.returncode != 0:
            result.setdefault("blockers", []).append("ssh_transport_nonzero")
    except Exception as exc:
        # transport 失败也落盘 current fail-closed artifact，但不虚构恢复或 stop 证据。
        result = fixture_artifact({
            "attempt_id": args.attempt_id,
            "authorization_id": args.authorization_id,
            "vendor_source_hashes": config["vendor_source_hashes"],
        })
        result.update({
            "maintenance_window_count": 1,
            "external_artifact_delta": 0,
            "evidence_boundary": "ssh_transport_failed_no_remote_maintenance_proof",
            "status": "maintenance_blocked_fail_closed",
            "service_restored": False,
            "holder_restored": False,
            "final_stopped": False,
            "blockers": ["ssh_transport_or_result_parse_failed"],
            "errors": [{"phase": "transport", "error_type": type(exc).__name__, "message": str(exc)[:240]}],
            "ssh_transport": {
                "invocation_count": 1,
                "exit_code": None,
                "request_sha256": request_sha,
            },
        })
    result["allow_instrumentation"] = bool(args.allow_instrumentation_build_flash)
    result["artifact_validation_errors"] = validate_artifact(result, live=True)
    write_artifact(Path(args.output), result)
    print(args.output)
    print(f"status={result.get('status')}")
    print(f"blockers={json.dumps(result.get('blockers', []), ensure_ascii=False)}")
    # live blocker 是现场事实，不触发第二次 runner；artifact 已可供 Product 收口。
    return 0 if not result["artifact_validation_errors"] else 7


# CLI 参数名与 tech-plan 验收命令逐字兼容。
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="O1 runtime identity/raw encoder maintenance")
    parser.add_argument("--mode", required=True, choices=("fixture", "ssh-maintenance"))
    parser.add_argument("--fixture-dir")
    parser.add_argument("--ssh-host")
    parser.add_argument("--ssh-port", type=int)
    parser.add_argument("--authorization-id")
    parser.add_argument("--attempt-id")
    parser.add_argument("--allow-instrumentation-build-flash", action="store_true")
    parser.add_argument("--allow-supervised-minimal-motion-after-observability", action="store_true")
    parser.add_argument("--output", required=True)
    return parser


# main 将 hostile 输入稳定映射为 exit 4，正常 fixture/live artifact 写入返回 0。
def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.mode == "fixture":
            if not args.fixture_dir:
                raise ValueError("fixture_dir_required")
            return run_fixture(args)
        if not args.ssh_host or args.ssh_port is None:
            raise ValueError("ssh_host_and_port_required")
        return run_ssh_maintenance(args)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR:{type(exc).__name__}:{exc}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
