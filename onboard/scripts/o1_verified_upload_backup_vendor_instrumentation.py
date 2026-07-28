#!/usr/bin/env python3
"""WAVE ROVER verified upload、current backup 与 additive instrumentation runner。"""

# 安全合同 001：fixture 只验证离线 schema，不产生 current hardware 结论。
# 安全合同 002：真实模式只接受计划冻结的 SSH host、port、授权和 attempt。
# 安全合同 003：真实模式只有一个 SSH subprocess，不实现 transport retry。
# 安全合同 004：所有现场动作都包含在同一远端 runner 与同一 command ledger。
# 安全合同 005：旧 maintenance runner、T=900 和任何 motion 路径均不复用。
# 安全合同 006：normal UART `/dev/ttyS5` 不自动等于 bootloader upload port。
# 安全合同 007：upload port 只从 current `/dev/serial/by-id` stable alias 选择。
# 安全合同 008：stable alias 不唯一时 Gate U 立即红，不猜 generic tty。
# 安全合同 009：bootloader identity 只允许一次逻辑 probe。
# 安全合同 010：probe 输出只保留 chip/revision/flash 与 MAC hash prefix。
# 安全合同 011：Gate U 红时 backup/build/flash/rollback 必须全部为零。
# 安全合同 012：flash 大小只能从 current `flash_id` 输出解析。
# 安全合同 013：current full-flash backup 只允许读取一次。
# 安全合同 014：backup 大小、SHA、chip/port/tool binding 缺一即 Gate B 红。
# 安全合同 015：factory target.bin 只记录只读 hash，不能替代 current backup。
# 安全合同 016：rollback manifest 只绑定本轮 current backup 与同一 verified port。
# 安全合同 017：canonical source 只来自 top-level vendor V0.9 tree。
# 安全合同 018：vendor source 在 run-owned tree 中复制，原目录始终只读。
# 安全合同 019：additive patch 只允许修改 `ugv_advance.h`。
# 安全合同 020：patch 只能增加 feedback 字段，不能删除 T/L/R/r/p/y/v。
# 安全合同 021：generic binary-protocol `main.cpp` 不得进入 vendor image。
# 安全合同 022：PlatformIO、esptool、platform、board 与 libraries 全部冻结。
# 安全合同 023：依赖版本不匹配时 Gate V-prebuild 红。
# 安全合同 024：U/B/V-prebuild 全绿前 instrumentation build count 为零。
# 安全合同 025：build provenance 不绿时 diagnostic flash count 为零。
# 安全合同 026：diagnostic build 最多一次，不允许第二次构建。
# 安全合同 027：diagnostic flash 最多一次，不允许 upload retry。
# 安全合同 028：flash 后 readback 只允许静止 T=130 请求，不发运动指令。
# 安全合同 029：readback 只接受 additive T=1001 machine-readable 字段。
# 安全合同 030：静止 counter 值不等于 HIL 或 safe-to-control。
# 安全合同 031：diagnostic flash 一旦开始，最多执行一次 current-backup rollback。
# 安全合同 032：rollback 使用同一 chip/port/tool/offset/size 绑定。
# 安全合同 033：rollback 后使用 verify_flash 校验同一 backup。
# 安全合同 034：任何阶段失败都进入 finally 恢复 service/holder/final stop。
# 安全合同 035：service stop/start 各最多一次，不循环 mutation。
# 安全合同 036：holder 检查只用 lsof/fuser 只读模式，禁止 fuser -k。
# 安全合同 037：本 runner 不使用 killall、pkill 或宽泛 PID 匹配。
# 安全合同 038：holder 未释放时 fail closed，不强行争抢 device。
# 安全合同 039：pre-stop 与 final-stop 使用 Upper stop API，不计 motion。
# 安全合同 040：final stop 必须同时看到 stop response 和 status zero evidence。
# 安全合同 041：run-owned 临时目录必须精确匹配冻结 attempt 路径。
# 安全合同 042：cleanup 只删除本 attempt 精确目录，不碰其它 `/tmp` 内容。
# 安全合同 043：artifact 不保存完整 MAC、hostname、环境变量或凭证。
# 安全合同 044：command ledger 保存 action、argv hash、时间和 exit。
# 安全合同 045：command ledger 不保存无界 stdout/stderr。
# 安全合同 046：所有安全/任务字段从初始化到完成始终固定 false。
# 安全合同 047：build/flash/rollback 成功都不能提升 HIL 或 OKR credit。
# 安全合同 048：runner_invocation_count 在 live artifact 中必须恰好为一。
# 安全合同 049：retry_count、second_build_count、second_flash_count 永远为零。
# 安全合同 050：motion_command_count 与 t900_write_count 永远为零。
# 安全合同 051：fixture/live artifact 使用同一 validator 防止语义漂移。
# 安全合同 052：bool 不能伪装整数 count，validator 必须显式拒绝。
# 安全合同 053：任一危险字段 true 都是顶层 validation error。
# 安全合同 054：任一 gate 红而产生 build/flash/rollback 都是顶层错误。
# 安全合同 055：diagnostic flash 发生但 rollback 未尝试是顶层错误。
# 安全合同 056：live artifact 恢复三字段缺一都不得通过验收。
# 安全合同 057：artifact 输出稳定排序并使用 UTF-8，便于 scoped review。
# 安全合同 058：fixture 缺文件或 hostile payload 返回 exit 4。
# 安全合同 059：live blocker 仍返回结构化 artifact，不自动重跑。
# 安全合同 060：Hardware 不调整 OKR、不归档 KR、不创建 final 文档。
# 安全合同 061：Hardware 不修改 docs/vendor 或 factory binary。
# 安全合同 062：Hardware 不修改 generic ESP32 main.cpp。
# 安全合同 063：Hardware 不 commit/push，不覆盖并发 planning docs。
# 安全合同 064：本 runner 的唯一目标是 current maintenance evidence。
# 安全合同 065：Gate U 只接受 current stable alias，不接受历史端口记录。
# 安全合同 066：Gate U 不接受普通 UART 可读作为 bootloader 身份证明。
# 安全合同 067：Gate U 不接受单独 VID/PID 作为目标板完整身份。
# 安全合同 068：Gate U 不输出完整 USB serial，避免设备身份泄露。
# 安全合同 069：Gate U 的 sysfs 路径只参与 hash，不输出完整路径。
# 安全合同 070：Gate U 的 candidate basename 只用于现场复核。
# 安全合同 071：Gate U probe exit 非零时不读取 current flash。
# 安全合同 072：Gate U 缺 flash size 时不猜容量。
# 安全合同 073：Gate U 缺 chip family 时不接受 generic serial device。
# 安全合同 074：Gate U 缺 MAC hash 时 identity binding 不完整。
# 安全合同 075：Gate U 不因 operator 在场而放宽身份检查。
# 安全合同 076：Gate U 不因物理限位而放宽唯一端口检查。
# 安全合同 077：Gate U 不因完整维护授权而跳过只读 probe。
# 安全合同 078：Gate U 不创建宽泛 `/dev/ttyUSB*` symlink。
# 安全合同 079：Gate U 不自动部署未验证 udev rule。
# 安全合同 080：Gate U 多候选时逐一 probe 会违反 exactly-once，故停止。
# 安全合同 081：Gate B 只在同一 runner、同一 alias 上执行。
# 安全合同 082：Gate B backup offset 固定为 current flash 起点。
# 安全合同 083：Gate B backup end 由 current flash size 计算。
# 安全合同 084：Gate B 不接受 sparse、empty 或 truncated backup。
# 安全合同 085：Gate B SHA 必须覆盖完整导出字节。
# 安全合同 086：Gate B 的 chip binding 来自同窗 Gate U。
# 安全合同 087：Gate B 的 port binding 来自同窗 stable alias。
# 安全合同 088：Gate B 的 tool binding 来自冻结 esptool 版本。
# 安全合同 089：Gate B 的 rollback offset 与 backup offset 必须相同。
# 安全合同 090：Gate B 的 rollback size 与 backup size 必须相同。
# 安全合同 091：Gate B 的 rollback verification 必须明确记录。
# 安全合同 092：Gate B 不把 factory image hash 当 current image hash。
# 安全合同 093：Gate B 的 stdout export 必须由外层再次校验 SHA。
# 安全合同 094：Gate B 导出失败时不得保留不可信 local backup。
# 安全合同 095：Gate B 只输出 backup basename，不输出无关 remote path。
# 安全合同 096：Gate B current backup 只用于本轮 rollback 与审计。
# 安全合同 097：Gate B 不修改、重命名或覆盖 factory target.bin。
# 安全合同 098：Gate B 未绿时 build count 保持零。
# 安全合同 099：Gate B 未绿时 flash count 保持零。
# 安全合同 100：Gate B 未绿时 rollback count 也保持零。
# 安全合同 101：Gate V 的 canonical root 必须是 top-level V0.9。
# 安全合同 102：Gate V 不使用 duplicate nested extraction。
# 安全合同 103：Gate V 逐文件 manifest 使用相对路径。
# 安全合同 104：Gate V pristine tree hash 在 patch 前冻结。
# 安全合同 105：Gate V patched tree hash 在 patch 后冻结。
# 安全合同 106：Gate V source mismatch 时不以 patch success 掩盖。
# 安全合同 107：Gate V patch hash 必须与本地 versioned patch 一致。
# 安全合同 108：Gate V patch apply 只能发生一次。
# 安全合同 109：Gate V patch reject 不允许 fuzz 后手工修补。
# 安全合同 110：Gate V CRLF 差异只允许 whitespace-tolerant apply。
# 安全合同 111：Gate V changed source allowlist 只有 ugv_advance.h。
# 安全合同 112：Gate V platformio.ini 是生成配置，不算 vendor source diff。
# 安全合同 113：Gate V toolchain.lock 是 provenance 文件，不算 vendor diff。
# 安全合同 114：Gate V 不改 WAVE_ROVER_V0.9.ino 控制流程。
# 安全合同 115：Gate V 不改 json_cmd.h command ID。
# 安全合同 116：Gate V 不改 uart_ctrl.h dispatch。
# 安全合同 117：Gate V 不改 movtion_module.h motor/encoder 算法。
# 安全合同 118：Gate V 不改 ugv_config.h pin、电压或机械参数。
# 安全合同 119：Gate V 不改 Wi-Fi 配置或 NVS 行为。
# 安全合同 120：Gate V 不改 heartbeat/watchdog 行为。
# 安全合同 121：Gate V 不删 T 字段。
# 安全合同 122：Gate V 不删 L 字段。
# 安全合同 123：Gate V 不删 R 字段。
# 安全合同 124：Gate V 不删 roll 字段。
# 安全合同 125：Gate V 不删 pitch 字段。
# 安全合同 126：Gate V 不删 yaw 字段。
# 安全合同 127：Gate V 不删 battery voltage 字段。
# 安全合同 128：Gate V firmwareBuildId 是固定可复验字符串。
# 安全合同 129：Gate V mainType 读取 runtime global。
# 安全合同 130：Gate V moduleType 读取 runtime global。
# 安全合同 131：Gate V encA 直接读取 encoderA current count。
# 安全合同 132：Gate V encB 直接读取 encoderB current count。
# 安全合同 133：Gate V speedGetA 同帧输出当前换算结果。
# 安全合同 134：Gate V speedGetB 同帧输出当前换算结果。
# 安全合同 135：Gate V additive fields 不改变原有 field 名称。
# 安全合同 136：Gate V additive fields 不改变原有 field 类型。
# 安全合同 137：Gate V additive fields 不触发任何 motor write。
# 安全合同 138：Gate V additive fields 不触发任何 encoder reset。
# 安全合同 139：Gate V build id 不使用 hostname 或秘密信息。
# 安全合同 140：Gate V build id 不使用不可复验随机值。
# 安全合同 141：Gate V PlatformIO core 版本必须完全相等。
# 安全合同 142：Gate V esptool 版本必须完全相等。
# 安全合同 143：Gate V platform package 必须 pin 到 exact version。
# 安全合同 144：Gate V board 必须固定为 esp32dev。
# 安全合同 145：Gate V framework 必须固定为 arduino。
# 安全合同 146：Gate V environment 名称必须固定。
# 安全合同 147：Gate V library dependencies 必须逐项 pin。
# 安全合同 148：Gate V 依赖在线获取失败时不重试 build。
# 安全合同 149：Gate V tool missing 时输出 current blocker。
# 安全合同 150：Gate V tool version mismatch 时禁止 build。
# 安全合同 151：Gate V source hash mismatch 时禁止 build。
# 安全合同 152：Gate V patch mismatch 时禁止 build。
# 安全合同 153：Gate V forbidden diff 时禁止 build。
# 安全合同 154：Gate V generic main.cpp 出现时禁止 build。
# 安全合同 155：build command 只能指向 run-owned vendor_build。
# 安全合同 156：build environment 只能指向冻结 environment。
# 安全合同 157：build subprocess 只调用一次。
# 安全合同 158：build timeout 只记失败，不再次构建。
# 安全合同 159：build exit 非零时 flash count 保持零。
# 安全合同 160：build 必须产出 firmware.bin。
# 安全合同 161：build 必须产出 bootloader.bin。
# 安全合同 162：build 必须产出 partitions.bin。
# 安全合同 163：build image 每个都记录 size 和 SHA。
# 安全合同 164：build manifest 绑定 patched source tree hash。
# 安全合同 165：build manifest 绑定 patch hash。
# 安全合同 166：build manifest 绑定 toolchain lock hash。
# 安全合同 167：build success 不替代 device identity。
# 安全合同 168：build success 不替代 current backup。
# 安全合同 169：build success 不替代 stationary readback。
# 安全合同 170：flash command 只能指向同一 verified stable alias。
# 安全合同 171：flash command 只能使用同一 run-owned build tree。
# 安全合同 172：flash command 只能使用冻结 environment。
# 安全合同 173：flash count 在 subprocess 前置一，覆盖可能 mutation。
# 安全合同 174：flash timeout 视为可能 mutation，必须 rollback。
# 安全合同 175：flash exit 非零仍必须尝试 current-backup rollback。
# 安全合同 176：flash 后不发送 nonzero motion。
# 安全合同 177：flash 后不发送 zero-jog。
# 安全合同 178：flash 后不调用 manual API。
# 安全合同 179：flash 后不发布 cmd_vel。
# 安全合同 180：flash 后不发送 Nav2 goal。
# 安全合同 181：flash 后 readback 只打开 normal UART 一次。
# 安全合同 182：flash 后 readback 只写一个 T=130 request。
# 安全合同 183：T=130 request 不计 motion。
# 安全合同 184：T=130 request 不计 T=900。
# 安全合同 185：readback parser 只接受 JSON object。
# 安全合同 186：readback parser 只接受 T=1001。
# 安全合同 187：readback 需要 firmwareBuildId。
# 安全合同 188：readback 需要 runtime mainType。
# 安全合同 189：readback 需要 runtime moduleType。
# 安全合同 190：readback 需要 raw encA。
# 安全合同 191：readback 需要 raw encB。
# 安全合同 192：readback 需要 speedGetA。
# 安全合同 193：readback 需要 speedGetB。
# 安全合同 194：readback build id 必须与 toolchain lock 一致。
# 安全合同 195：readback 缺字段时 Gate V 保持红。
# 安全合同 196：readback 成功仍不证明 nonzero wheel feedback。
# 安全合同 197：readback 成功仍不证明 encoder direction。
# 安全合同 198：readback 成功仍不证明 IMU/battery 标定。
# 安全合同 199：readback 成功仍不证明 route execution。
# 安全合同 200：rollback 只在 diagnostic flash 已开始时执行。
# 安全合同 201：未 flash 时 rollback 是显式 no-op。
# 安全合同 202：rollback count 在 write 前置一，覆盖可能 mutation。
# 安全合同 203：rollback write 使用 current backup，不用 factory image。
# 安全合同 204：rollback write offset 固定 0x0。
# 安全合同 205：rollback verify 使用同一 current backup。
# 安全合同 206：rollback verify 失败时 operator 保持物理限位。
# 安全合同 207：rollback 不允许第二次 write。
# 安全合同 208：rollback 不允许换 port 再试。
# 安全合同 209：rollback 不允许换 tool version 再试。
# 安全合同 210：rollback 完成后才恢复 service。
# 安全合同 211：service 初始 active 时只 start 一次。
# 安全合同 212：service 初始 inactive 时保持原状态。
# 安全合同 213：service state 使用 current systemctl show。
# 安全合同 214：service active 不单独证明 holder 恢复。
# 安全合同 215：holder 恢复用 command hash，而不要求 PID 相同。
# 安全合同 216：holder PID 更新是 service restart 的允许结果。
# 安全合同 217：holder command identity 漂移时 fail closed。
# 安全合同 218：holder wait 只读且有界，不是 mutation retry。
# 安全合同 219：deployed hashes 前后必须完全相等。
# 安全合同 220：deployed hash 变化时不自动回滚仓库。
# 安全合同 221：final stop 在 service/holder 恢复后执行。
# 安全合同 222：final stop POST 只调用一次。
# 安全合同 223：final status GET 只调用一次。
# 安全合同 224：final status 缺 zero evidence 时 fail closed。
# 安全合同 225：final stop 不把 arbitrary zero 当安全证据。
# 安全合同 226：final stop 支持 T=1 L/R zero。
# 安全合同 227：final stop 支持 T=11 L/R zero。
# 安全合同 228：final stop 支持 T=13 X/Z zero。
# 安全合同 229：final stop 支持 T=1001 L/R zero。
# 安全合同 230：cleanup 在 final stop evidence 后执行。
# 安全合同 231：cleanup 精确删除 RUN_DIR。
# 安全合同 232：cleanup 不跟随外部 symlink 扩大删除范围。
# 安全合同 233：cleanup 失败写入 errors 与 blocker。
# 安全合同 234：local backup 由外层写入 sprint artifacts。
# 安全合同 235：local backup 不写入源代码目录。
# 安全合同 236：local backup 不写入 docs/vendor。
# 安全合同 237：local backup hash 与 remote manifest 必须一致。
# 安全合同 238：SSH request SHA 绑定完整 remote source/config。
# 安全合同 239：SSH stderr 只保留 240 字符短摘要。
# 安全合同 240：SSH stdout byte count 用于审计 backup export。
# 安全合同 241：SSH nonzero 不触发第二次 transport。
# 安全合同 242：marker parse 失败不伪造 restoration=true。
# 安全合同 243：artifact validator errors 原样落盘。
# 安全合同 244：现场 gate blocker 与 validator error 分开记录。
# 安全合同 245：first_failure 只记录最早根因。
# 安全合同 246：后续恢复错误不覆盖 first_failure。
# 安全合同 247：status blocked 仍可作为 current evidence。
# 安全合同 248：external_artifact_delta 只表示 current hardware 维护事实。
# 安全合同 249：live_control_delta 始终为零。
# 安全合同 250：user action 不在本 runner 计分。
# 安全合同 251：current gate evidence 不自动产生 OKR credit。
# 安全合同 252：当前 blocker 若未解必须诚实达到 2/2。
# 安全合同 253：下轮不得第三次包装相同 instrumentation blocker。
# 安全合同 254：Hardware 只在 tech-done 记录真实原始摘要。
# 安全合同 255：Hardware 不倒推未 live 执行的代码版本。
# 安全合同 256：runner request SHA 用于区分现场代码与后续修复。
# 安全合同 257：离线 test success 不等于 live runner success。
# 安全合同 258：fixture gate true 不等于 current gate true。
# 安全合同 259：mock backup manifest 不等于 current flash bytes。
# 安全合同 260：mock service restored 不等于现场 systemd proof。
# 安全合同 261：mock holder restored 不等于现场 UART ownership。
# 安全合同 262：mock final stopped 不等于现场底盘停止。
# 安全合同 263：测试 patch apply 不等于 firmware build success。
# 安全合同 264：toolchain lock 不等于现场 toolchain 可用。
# 安全合同 265：vendor source hash 不等于 deployed firmware identity。
# 安全合同 266：factory PDF 只证明工具流程，不证明 current chip。
# 安全合同 267：factory target hash 只作比较，不作 rollback。
# 安全合同 268：vendor wiki USB 说明不证明现场已连接 USB。
# 安全合同 269：operator 在场不证明 stable alias 已出现。
# 安全合同 270：本 runner 的最终边界始终是 maintenance evidence not HIL。

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


# schema 与现场 identity 来自 planning_complete tech-plan，不允许 CLI 漂移。
SCHEMA = "trashbot.wave_rover.verified_upload_backup_vendor_instrumentation.v1"
EXPECTED_HOST = "root@192.168.1.11"
EXPECTED_PORT = 37878
EXPECTED_AUTHORIZATION_ID = "ceo_20260728_complete_motion_deploy_service_uart_firmware_maintenance"
EXPECTED_ATTEMPT_ID = "o1-verified-upload-backup-vendor-instrumentation-attempt-1"
SERVICE = "trashbot-esp32-bridge.service"
NORMAL_UART = "/dev/ttyS5"
NORMAL_BAUDRATE = 115200
REMOTE_REPO = "/root/rober"
RUN_DIR = (
    "/tmp/trashbot-o1-verified-upload-backup-vendor-instrumentation-"
    "o1-verified-upload-backup-vendor-instrumentation-attempt-1"
)

# 所有危险结论都必须显式 false，不能依赖字段缺失表达 fail closed。
SAFETY_FALSE_FIELDS = (
    "hil_pass",
    "safe_to_control",
    "route_execution_success",
    "delivery_success",
    "mission_attempt",
    "okr_credit",
)

# Product 指定的 vendor 文件逐个冻结，不使用目录存在性替代内容 provenance。
VENDOR_FILES = (
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/WAVE_ROVER_V0.9.ino",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_config.h",
    (
        "docs/vendor/waveshare_wave_rover/WAVE_ROVER_FACTORY/"
        "flash_download_tool_3.9.5/doc/Flash_Download_Tool__cn.pdf"
    ),
    (
        "docs/vendor/waveshare_wave_rover/WAVE_ROVER_FACTORY/"
        "flash_download_tool_3.9.5/combine/target.bin"
    ),
)

# 远端只冻结已部署 bridge 合同 hash；不改远端仓库文件。
DEPLOYED_PATHS = (
    (
        "/root/rober/onboard/src/ros2_trashbot_hardware/"
        "ros2_trashbot_hardware/esp32_bridge_node.py"
    ),
    (
        "/root/rober/onboard/src/ros2_trashbot_hardware/"
        "ros2_trashbot_hardware/wave_rover_feedback.py"
    ),
    (
        "/root/rober/onboard/src/ros2_trashbot_hardware/"
        "ros2_trashbot_hardware/wave_rover_protocol.py"
    ),
    "/root/rober/onboard/scripts/esp32_bridge_http.sh",
    "/etc/systemd/system/trashbot-esp32-bridge.service",
)


# 远端程序只由本文件的唯一 SSH stdin transport 执行。
# 它不依赖远端仓库新增脚本，也不会在 runner 外补跑工具命令。
REMOTE_SCRIPT = r'''
import base64
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CONFIG = json.loads(CONFIG_JSON)
SERVICE = CONFIG["service"]
NORMAL_UART = CONFIG["normal_uart"]
RUN_DIR = Path(CONFIG["run_dir"])
VENDOR_ROOT = Path(CONFIG["remote_repo"]) / "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9"

# 时间使用 UTC ISO；各 phase 的 current evidence 可由 timestamp 复核。
def now():
    return datetime.now(timezone.utc).isoformat()

# 初始 artifact 已包含全部安全 false 与 exactly-once 零值。
def blank_result():
    result = {
        "schema": CONFIG["schema"],
        "attempt_id": CONFIG["attempt_id"],
        "authorization_id": CONFIG["authorization_id"],
        "captured_at": now(),
        "runner_invocation_count": 1,
        "attempt_count": 1,
        "inventory_invocation_count": 0,
        "pre_stop_invocation_count": 0,
        "service_stop_count": 0,
        "holder_termination_count": 0,
        "bootloader_identity_probe_count": 0,
        "flash_backup_read_count": 0,
        "vendor_tree_prepare_count": 0,
        "additive_patch_apply_count": 0,
        "instrumentation_build_count": 0,
        "diagnostic_flash_count": 0,
        "stationary_diagnostic_readback_count": 0,
        "rollback_flash_count": 0,
        "service_restore_count": 0,
        "final_stop_verification_count": 0,
        "motion_command_count": 0,
        "t900_write_count": 0,
        "retry_count": 0,
        "second_build_count": 0,
        "second_flash_count": 0,
        "gate_u": False,
        "gate_b": False,
        "gate_v_prebuild": False,
        "gate_v": False,
        "build_provenance_green": False,
        "first_failure": None,
        "blockers": [],
        "errors": [],
        "command_ledger": [],
        "phase_states": {},
        "port_manifest": {},
        "chip_manifest": {},
        "backup_manifest": {},
        "rollback_manifest": {},
        "source_manifest": {},
        "patch_manifest": {},
        "toolchain_manifest": {},
        "build_manifest": {},
        "diagnostic_readback": {},
        "rollback_result": {
            "attempted": False,
            "restored": True,
            "reason": "no_diagnostic_flash_started",
        },
        "service_before": {},
        "service_after": {},
        "holder_before": [],
        "holder_after": [],
        "deployed_hashes_before": {},
        "deployed_hashes_after": {},
        "service_restored": False,
        "holder_restored": False,
        "final_stopped": False,
        "run_owned_residual": None,
        "current_run_artifact_delta": 1,
        "external_artifact_delta": 1,
        "live_control_delta": 0,
        "proof_boundary": (
            "current_verified_upload_backup_vendor_instrumentation_"
            "maintenance_evidence_not_hil"
        ),
        "status": "running",
    }
    for field in CONFIG["safety_false_fields"]:
        result[field] = False
    return result

RESULT = blank_result()

# 第一个 blocker 单独冻结，避免后续恢复错误覆盖根因。
def block(reason):
    if reason not in RESULT["blockers"]:
        RESULT["blockers"].append(reason)
    if RESULT["first_failure"] is None:
        RESULT["first_failure"] = reason

# ledger 只保存 argv hash 与短摘要，不暴露完整工具输出。
def ledger(phase, action, started, exit_code, argv, summary):
    canonical = json.dumps(argv, separators=(",", ":"), ensure_ascii=True)
    RESULT["command_ledger"].append({
        "phase": phase,
        "action": action,
        "allowed": True,
        "started_at": started,
        "ended_at": now(),
        "exit_code": exit_code,
        "argv_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
        "summary": str(summary)[:300],
    })

# 只有冻结 action/argv 形状可进入 subprocess。
def command_allowed(action, argv):
    exact = {
        "systemctl_show": [
            "systemctl", "show", SERVICE, "--no-pager",
            "--property=ActiveState,SubState,MainPID,FragmentPath",
        ],
        "systemctl_stop": ["systemctl", "stop", SERVICE],
        "systemctl_start": ["systemctl", "start", SERVICE],
        "lsof_normal_uart": ["lsof", "-t", NORMAL_UART],
        "fuser_normal_uart": ["fuser", NORMAL_UART],
        "patch_apply": [
            "patch", "--batch", "--forward", "--ignore-whitespace", "-p1", "-i",
            str(RUN_DIR / "additive_diagnostic.patch"),
        ],
    }
    if action in exact:
        return argv == exact[action]
    if action == "sha256sum_deployed":
        return len(argv) == 2 and argv[0] == "sha256sum" and argv[1] in CONFIG["deployed_paths"]
    if action == "platformio_version":
        return len(argv) == 2 and argv[1] == "--version" and Path(argv[0]).name in {"platformio", "pio"}
    if action == "esptool_version":
        return argv == ["python3", "-m", "esptool", "version"]
    if action == "bootloader_flash_id":
        return (
            len(argv) == 6
            and argv[:3] == ["python3", "-m", "esptool"]
            and argv[3] == "--port"
            and Path(argv[4]).parent == Path("/dev/serial/by-id")
            and argv[5] == "flash_id"
        )
    if action == "flash_backup_read":
        return (
            len(argv) == 9
            and argv[:3] == ["python3", "-m", "esptool"]
            and argv[3] == "--port"
            and argv[5:8] == ["read_flash", "0x0", argv[7]]
            and argv[8] == str(RUN_DIR / "current_flash_backup.bin")
        )
    if action == "instrumentation_build":
        return (
            len(argv) == 6
            and Path(argv[0]).name in {"platformio", "pio"}
            and argv[1:3] == ["run", "--project-dir"]
            and argv[3] == str(RUN_DIR / "vendor_build")
            and argv[4:6] == ["--environment", CONFIG["toolchain"]["environment"]]
        )
    if action == "diagnostic_flash":
        return (
            len(argv) == 10
            and Path(argv[0]).name in {"platformio", "pio"}
            and argv[1:3] == ["run", "--project-dir"]
            and argv[3] == str(RUN_DIR / "vendor_build")
            and argv[4:6] == ["--environment", CONFIG["toolchain"]["environment"]]
            and argv[6:8] == ["--target", "upload"]
            and argv[8:10] == ["--upload-port", argv[9]]
            and Path(argv[9]).parent == Path("/dev/serial/by-id")
        )
    if action == "rollback_flash":
        return (
            len(argv) == 8
            and argv[:3] == ["python3", "-m", "esptool"]
            and argv[3] == "--port"
            and argv[5:7] == ["write_flash", "0x0"]
            and argv[7] == str(RUN_DIR / "current_flash_backup.bin")
        )
    if action == "rollback_verify":
        return (
            len(argv) == 8
            and argv[:3] == ["python3", "-m", "esptool"]
            and argv[3] == "--port"
            and argv[5:7] == ["verify_flash", "0x0"]
            and argv[7] == str(RUN_DIR / "current_flash_backup.bin")
        )
    return False

# subprocess 全部有 timeout，失败只记录并返回，不实现 retry。
def run_cmd(phase, action, argv, timeout=20, cwd=None):
    started = now()
    if not command_allowed(action, argv):
        ledger(phase, action, started, 126, argv, "command_not_allowlisted")
        raise RuntimeError("command_not_allowlisted:" + action)
    try:
        proc = subprocess.run(
            argv,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        summary = "stdout_bytes=%d stderr_bytes=%d" % (len(proc.stdout), len(proc.stderr))
        ledger(phase, action, started, proc.returncode, argv, summary)
        return proc.returncode, proc.stdout, proc.stderr
    except Exception as exc:
        ledger(phase, action, started, 125, argv, type(exc).__name__)
        return 125, "", str(exc)

# systemd 只抽取状态字段，避免保存完整 ExecStart 或环境。
def service_state(phase):
    argv = [
        "systemctl", "show", SERVICE, "--no-pager",
        "--property=ActiveState,SubState,MainPID,FragmentPath",
    ]
    code, out, _ = run_cmd(phase, "systemctl_show", argv)
    data = {"exit_code": code}
    for line in out.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key in {"ActiveState", "SubState", "MainPID"}:
            data[key] = value
    return data

# holder identity 只保留 PID、启动 tick 与 cmd hash prefix。
def process_identity(pid):
    try:
        parts = Path("/proc/%d/stat" % pid).read_text().split()
        raw = Path("/proc/%d/cmdline" % pid).read_bytes().replace(b"\0", b" ").strip()
        return {
            "pid": pid,
            "start_ticks": parts[21],
            "cmd_hash_prefix": hashlib.sha256(raw).hexdigest()[:16],
            "expected_bridge": b"esp32_bridge" in raw,
        }
    except Exception:
        return None

# lsof 与 fuser 都是只读；任一工具可用即可形成 current holder evidence。
def holders(phase):
    pids = set()
    lsof_argv = ["lsof", "-t", NORMAL_UART]
    lsof_code, out, _ = run_cmd(phase, "lsof_normal_uart", lsof_argv)
    if lsof_code in (0, 1):
        pids.update(int(item) for item in out.split() if item.isdigit())
    fuser_argv = ["fuser", NORMAL_UART]
    fuser_code, out, err = run_cmd(phase, "fuser_normal_uart", fuser_argv)
    if fuser_code in (0, 1):
        pids.update(int(item) for item in (out + " " + err).split() if item.isdigit())
    if lsof_code == 125 and fuser_code == 125:
        raise RuntimeError("holder_inventory_tools_unavailable")
    return [item for item in (process_identity(pid) for pid in sorted(pids)) if item]

# 部署 hash 只记录 basename 与 SHA，不暴露远端绝对路径。
def deployed_hashes(phase):
    found = {}
    for path in CONFIG["deployed_paths"]:
        code, out, _ = run_cmd(phase, "sha256sum_deployed", ["sha256sum", path])
        if code == 0 and out.split():
            found[Path(path).name] = out.split()[0]
    return found

# stop/readback HTTP body 有大小上限，避免无界日志进入 artifact。
def http_json(phase, action, method, path):
    started = now()
    request = urllib.request.Request(
        "http://127.0.0.1:8787" + path,
        data=b"{}" if method == "POST" else None,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = response.read(2_000_000)
            payload = json.loads(raw.decode("utf-8")) if raw else {}
            ledger(phase, action, started, 0, [method, path], "bytes=%d" % len(raw))
            return True, payload
    except Exception as exc:
        ledger(phase, action, started, 124, [method, path], type(exc).__name__)
        return False, {}

# 只识别 vendor zero command/T1001，不把任意数值零误判为 stopped。
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

# 文件 hash 使用流式读取，full flash backup 不会一次性载入 hash 内存。
def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

# tree manifest 使用相对路径排序，排除 PlatformIO 生成目录。
def tree_manifest(root):
    manifest = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or ".pio" in path.parts:
            continue
        manifest[str(path.relative_to(root))] = sha256_file(path)
    canonical = json.dumps(manifest, separators=(",", ":"), sort_keys=True)
    return manifest, hashlib.sha256(canonical.encode()).hexdigest()

# current stable alias 及其 sysfs/udev identity 只输出安全 hash。
def stable_upload_aliases():
    aliases = sorted(Path("/dev/serial/by-id").glob("*"))
    result = []
    for alias in aliases:
        try:
            canonical = alias.resolve(strict=True)
            tty_name = canonical.name
            sysfs = Path("/sys/class/tty") / tty_name / "device"
            sysfs_real = str(sysfs.resolve(strict=True))
            uevents = []
            cursor = sysfs.resolve(strict=True)
            for _ in range(5):
                uevent = cursor / "uevent"
                if uevent.is_file():
                    uevents.append(uevent.read_text(errors="replace"))
                if cursor.parent == cursor:
                    break
                cursor = cursor.parent
            identity_material = "\n".join(uevents)
            serial_match = re.search(r"(?:ID_SERIAL_SHORT|SERIAL)=([^\n]+)", identity_material)
            vid_match = re.search(r"(?:PRODUCT|PRODUCT_ID)=([0-9a-fA-F]{4})", identity_material)
            result.append({
                "alias_basename": alias.name,
                "canonical_basename": tty_name,
                "sysfs_hash_prefix": hashlib.sha256(sysfs_real.encode()).hexdigest()[:16],
                "identity_hash_prefix": hashlib.sha256(identity_material.encode()).hexdigest()[:16],
                "serial_hash_prefix": (
                    hashlib.sha256(serial_match.group(1).encode()).hexdigest()[:12]
                    if serial_match else None
                ),
                "vid_hint_present": bool(vid_match),
            })
        except Exception as exc:
            result.append({
                "alias_basename": alias.name,
                "identity_error": type(exc).__name__,
            })
    return aliases, result

# esptool `flash_id` 的 current size 必须显式解析，不能写死 4MB。
def parse_flash_size(text):
    match = re.search(r"(?:Detected flash size|Flash size):\s*(\d+)\s*(KB|MB)", text, re.I)
    if not match:
        return None
    value = int(match.group(1))
    return value * (1024 if match.group(2).upper() == "KB" else 1024 * 1024)

# bootloader 输出只投影安全字段；完整 MAC 只参与 hash。
def parse_bootloader_identity(text):
    chip = re.search(r"Chip is\s+([^\r\n]+)", text)
    revision = re.search(r"(?:Chip revision|Revision):\s*([^\r\n]+)", text, re.I)
    flash_id = re.search(r"(?:Manufacturer|Flash ID):\s*([^\r\n]+)", text, re.I)
    mac = re.search(r"\b([0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5})\b", text)
    return {
        "chip_family": chip.group(1).strip()[:100] if chip else None,
        "revision": revision.group(1).strip()[:60] if revision else None,
        "flash_identity": flash_id.group(1).strip()[:100] if flash_id else None,
        "flash_size_bytes": parse_flash_size(text),
        "mac_hash_prefix": hashlib.sha256(mac.group(1).lower().encode()).hexdigest()[:16] if mac else None,
    }

# Gate V 在 run-owned copy 上应用 patch，并冻结 source/patch/toolchain provenance。
def prepare_vendor_tree():
    RESULT["vendor_tree_prepare_count"] = 1
    RESULT["additive_patch_apply_count"] = 1
    if not VENDOR_ROOT.is_dir():
        block("canonical_vendor_tree_missing")
        return
    build_root = RUN_DIR / "vendor_build"
    shutil.copytree(VENDOR_ROOT, build_root, symlinks=False)
    pristine, pristine_hash = tree_manifest(build_root)
    expected = CONFIG["vendor_source_hashes"]
    required_mismatch = []
    for relative in CONFIG["required_vendor_source_relatives"]:
        remote_path = Path(CONFIG["remote_repo"]) / relative
        if not remote_path.is_file() or sha256_file(remote_path) != expected[relative]:
            required_mismatch.append(relative)
    patch_path = RUN_DIR / "additive_diagnostic.patch"
    patch_path.write_text(CONFIG["patch_text"])
    (build_root / "platformio.ini").write_text(CONFIG["platformio_text"])
    (build_root / "toolchain.lock").write_text(CONFIG["toolchain_lock_text"])
    # vendor header 是 CRLF；先在隔离 copy 统一 LF，避免目标机 patch 实现差异。
    patch_target = build_root / "ugv_advance.h"
    patch_target_raw = patch_target.read_bytes()
    line_endings_normalized = b"\r\n" in patch_target_raw
    if line_endings_normalized:
        patch_target.write_bytes(patch_target_raw.replace(b"\r\n", b"\n"))
    patch_argv = [
        "patch", "--batch", "--forward", "--ignore-whitespace", "-p1", "-i",
        str(patch_path),
    ]
    patch_code, _, _ = run_cmd(
        "V",
        "patch_apply",
        patch_argv,
        timeout=20,
        cwd=str(build_root),
    )
    patched, patched_hash = tree_manifest(build_root)
    changed = sorted(
        key for key in set(pristine) | set(patched)
        if pristine.get(key) != patched.get(key)
        and key not in {"platformio.ini", "toolchain.lock"}
    )
    ugv_text = (build_root / "ugv_advance.h").read_text(errors="replace")
    preserved = all(
        token in ugv_text
        for token in (
            'jsonInfoHttp["T"] = FEEDBACK_BASE_INFO',
            'jsonInfoHttp["L"] = speedGetA',
            'jsonInfoHttp["R"] = speedGetB',
            'jsonInfoHttp["r"] = icm_roll',
            'jsonInfoHttp["p"] = icm_pitch',
            'jsonInfoHttp["y"] = icm_yaw',
            'jsonInfoHttp["v"] = loadVoltage_V',
        )
    )
    additive = all(
        token in ugv_text
        for token in (
            'jsonInfoHttp["firmwareBuildId"]',
            'jsonInfoHttp["mainType"]',
            'jsonInfoHttp["moduleType"]',
            'jsonInfoHttp["encA"]',
            'jsonInfoHttp["encB"]',
            'jsonInfoHttp["speedGetA"]',
            'jsonInfoHttp["speedGetB"]',
        )
    )
    RESULT["source_manifest"] = {
        "canonical_root_basename": VENDOR_ROOT.name,
        "file_count": len(pristine),
        "pristine_tree_sha256": pristine_hash,
        "patched_tree_sha256": patched_hash,
        "required_source_hashes_match": not required_mismatch,
        "required_source_mismatches": [Path(item).name for item in required_mismatch],
        "generic_main_cpp_present": "main.cpp" in pristine,
    }
    RESULT["patch_manifest"] = {
        "patch_sha256": hashlib.sha256(CONFIG["patch_text"].encode()).hexdigest(),
        "expected_patch_sha256": CONFIG["patch_sha256"],
        "apply_exit_code": patch_code,
        "changed_source_files": changed,
        "diff_allowlist": ["ugv_advance.h"],
        "existing_feedback_fields_preserved": preserved,
        "additive_fields_present": additive,
        "isolated_copy_line_endings_normalized": line_endings_normalized,
    }

    pio = shutil.which("platformio") or shutil.which("pio")
    pio_version = None
    if pio:
        code, out, err = run_cmd("V", "platformio_version", [pio, "--version"])
        if code == 0:
            match = re.search(r"(\d+\.\d+\.\d+)", out + err)
            pio_version = match.group(1) if match else None
    esptool_version = RESULT["toolchain_manifest"].get("esptool_version")
    RESULT["toolchain_manifest"] = {
        "platformio_available": bool(pio),
        "platformio_basename": Path(pio).name if pio else None,
        "platformio_version": pio_version,
        "expected_platformio_version": CONFIG["toolchain"]["platformio_core"],
        "esptool_version": esptool_version,
        "expected_esptool_version": CONFIG["toolchain"]["esptool"],
        "platform": CONFIG["toolchain"]["platform"],
        "framework": CONFIG["toolchain"]["framework"],
        "board": CONFIG["toolchain"]["board"],
        "environment": CONFIG["toolchain"]["environment"],
        "platformio_ini_sha256": CONFIG["platformio_sha256"],
        "toolchain_lock_sha256": CONFIG["toolchain_lock_sha256"],
    }
    RESULT["gate_v_prebuild"] = bool(
        not required_mismatch
        and patch_code == 0
        and changed == ["ugv_advance.h"]
        and preserved
        and additive
        and "main.cpp" not in pristine
        and hashlib.sha256(CONFIG["patch_text"].encode()).hexdigest() == CONFIG["patch_sha256"]
        and pio_version == CONFIG["toolchain"]["platformio_core"]
        and esptool_version == CONFIG["toolchain"]["esptool"]
    )
    if not RESULT["gate_v_prebuild"]:
        block("gate_v_prebuild_provenance_not_green")

# 唯一静止 readback 可发送 T=130；它不是 motion 或 T=900。
def stationary_readback():
    RESULT["stationary_diagnostic_readback_count"] = 1
    frames = []
    try:
        import serial
        started = now()
        with serial.Serial(NORMAL_UART, CONFIG["normal_baudrate"], timeout=0.25, write_timeout=1) as ser:
            raw_request = b'{"T":130}\n'
            ser.write(raw_request)
            ser.flush()
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                raw = ser.readline()
                if not raw:
                    continue
                try:
                    item = json.loads(raw.decode("utf-8", errors="strict"))
                except Exception:
                    continue
                if isinstance(item, dict) and item.get("T") == 1001:
                    frames.append(item)
        ledger(
            "D",
            "stationary_t130_readback",
            started,
            0,
            ["serial", Path(NORMAL_UART).name, "T=130"],
            "t1001_frames=%d" % len(frames),
        )
    except Exception as exc:
        RESULT["errors"].append({
            "phase": "D",
            "error_type": type(exc).__name__,
            "message": "stationary_readback_failed",
        })
    required = (
        "firmwareBuildId", "mainType", "moduleType",
        "encA", "encB", "speedGetA", "speedGetB",
    )
    matched = [
        frame for frame in frames
        if all(key in frame for key in required)
        and frame.get("firmwareBuildId") == CONFIG["toolchain"]["build_id"]
    ]
    RESULT["diagnostic_readback"] = {
        "t1001_frame_count": len(frames),
        "additive_frame_count": len(matched),
        "schema_valid": bool(matched),
        "sample_sha256": (
            hashlib.sha256(json.dumps(matched[-1], sort_keys=True).encode()).hexdigest()
            if matched else None
        ),
    }

# runner 主流程：inventory→pre-stop→freeze→U/B/V→条件式 D→恢复。
def main():
    service_was_active = False
    diagnostic_flash_started = False
    run_dir_created = False
    upload_alias = None
    pio = None
    try:
        RESULT["phase_states"]["0"] = "running"
        RESULT["inventory_invocation_count"] = 1
        if RUN_DIR.exists():
            block("run_owned_directory_already_exists")
            return
        RUN_DIR.mkdir(mode=0o700, parents=False)
        run_dir_created = True
        (RUN_DIR / "runner.sha256").write_text(CONFIG["remote_script_sha256"] + "\n")
        RESULT["service_before"] = service_state("0")
        service_was_active = RESULT["service_before"].get("ActiveState") == "active"
        RESULT["holder_before"] = holders("0")
        RESULT["deployed_hashes_before"] = deployed_hashes("0")
        aliases, port_items = stable_upload_aliases()
        RESULT["port_manifest"] = {
            "stable_alias_count": len(aliases),
            "candidates": port_items,
            "normal_uart_basename": Path(NORMAL_UART).name,
            "normal_uart_is_upload_identity": False,
        }
        RESULT["pre_stop_invocation_count"] = 1
        pre_ok, pre_payload = http_json("0", "pre_stop_post", "POST", "/api/base/stop")
        if not pre_ok or not zero_evidence(pre_payload):
            block("pre_stop_not_confirmed")
            return
        RESULT["phase_states"]["0"] = "complete"

        RESULT["phase_states"]["U"] = "running"
        if service_was_active:
            RESULT["service_stop_count"] = 1
            code, _, _ = run_cmd("U", "systemctl_stop", ["systemctl", "stop", SERVICE])
            if code != 0:
                block("service_stop_failed")
                return
        time.sleep(1)
        if service_state("U").get("ActiveState") == "active":
            block("service_still_active")
            return
        if holders("U"):
            block("normal_uart_holder_not_released")
            return

        # Gate U 先冻结 esptool 版本，确保 first_failure 遵循 U→B→V 顺序。
        code, out, err = run_cmd("U", "esptool_version", ["python3", "-m", "esptool", "version"])
        esptool_version = None
        if code == 0:
            match = re.search(r"(\d+\.\d+(?:\.\d+)?)", out + err)
            esptool_version = match.group(1) if match else None
        RESULT["toolchain_manifest"] = {
            "esptool_version": esptool_version,
            "expected_esptool_version": CONFIG["toolchain"]["esptool"],
        }
        if len(aliases) != 1:
            block("stable_upload_alias_not_unique")
        elif esptool_version != CONFIG["toolchain"]["esptool"]:
            block("verified_esptool_version_unavailable")
        else:
            upload_alias = aliases[0]
            RESULT["bootloader_identity_probe_count"] = 1
            probe_argv = ["python3", "-m", "esptool", "--port", str(upload_alias), "flash_id"]
            code, out, err = run_cmd("U", "bootloader_flash_id", probe_argv, timeout=45)
            identity = parse_bootloader_identity(out + "\n" + err)
            RESULT["chip_manifest"] = dict(identity)
            RESULT["chip_manifest"]["probe_exit_code"] = code
            RESULT["chip_manifest"]["tool_version"] = CONFIG["toolchain"]["esptool"]
            RESULT["gate_u"] = bool(
                code == 0
                and identity["chip_family"]
                and identity["flash_identity"]
                and identity["flash_size_bytes"]
                and identity["mac_hash_prefix"]
            )
            if not RESULT["gate_u"]:
                block("bootloader_identity_probe_not_green")
        RESULT["phase_states"]["U"] = "complete" if RESULT["gate_u"] else "blocked"

        # Gate V 仍独立形成 current source/toolchain evidence，但不覆盖 U 首错。
        prepare_vendor_tree()
        pio = shutil.which("platformio") or shutil.which("pio")

        RESULT["phase_states"]["B"] = "running"
        if RESULT["gate_u"] and upload_alias is not None:
            flash_size = RESULT["chip_manifest"]["flash_size_bytes"]
            backup_path = RUN_DIR / "current_flash_backup.bin"
            RESULT["flash_backup_read_count"] = 1
            backup_argv = [
                "python3", "-m", "esptool", "--port", str(upload_alias),
                "read_flash", "0x0", hex(flash_size), str(backup_path),
            ]
            code, _, _ = run_cmd("B", "flash_backup_read", backup_argv, timeout=240)
            size = backup_path.stat().st_size if backup_path.is_file() else 0
            backup_sha = sha256_file(backup_path) if size else None
            RESULT["backup_manifest"] = {
                "read_exit_code": code,
                "offset": "0x0",
                "expected_size_bytes": flash_size,
                "actual_size_bytes": size,
                "sha256": backup_sha,
                "chip_identity_hash_prefix": hashlib.sha256(
                    json.dumps(RESULT["chip_manifest"], sort_keys=True).encode()
                ).hexdigest()[:16],
                "port_identity_hash_prefix": (
                    RESULT["port_manifest"]["candidates"][0].get("identity_hash_prefix")
                    if RESULT["port_manifest"]["candidates"] else None
                ),
                "tool_version": CONFIG["toolchain"]["esptool"],
                "factory_target_sha256": CONFIG["factory_target_sha256"],
                "factory_binary_used_as_backup": False,
            }
            RESULT["rollback_manifest"] = {
                "backup_sha256": backup_sha,
                "write_offset": "0x0",
                "write_size_bytes": flash_size,
                "tool_version": CONFIG["toolchain"]["esptool"],
                "same_verified_alias": True,
                "verification": "esptool_verify_flash_same_backup",
            }
            RESULT["gate_b"] = bool(
                code == 0
                and size == flash_size
                and backup_sha
                and RESULT["rollback_manifest"]["backup_sha256"] == backup_sha
            )
            if RESULT["gate_b"]:
                RESULT["_backup_export_b64"] = base64.b64encode(backup_path.read_bytes()).decode("ascii")
            else:
                block("current_flash_backup_not_green")
        else:
            block("gate_b_blocked_by_gate_u")
        RESULT["phase_states"]["B"] = "complete" if RESULT["gate_b"] else "blocked"

        # 三门不全绿时 build/flash/rollback 保持 0/0/0。
        if not (RESULT["gate_u"] and RESULT["gate_b"] and RESULT["gate_v_prebuild"]):
            return

        RESULT["phase_states"]["D"] = "running"
        RESULT["instrumentation_build_count"] = 1
        build_argv = [
            pio, "run", "--project-dir", str(RUN_DIR / "vendor_build"),
            "--environment", CONFIG["toolchain"]["environment"], "",
        ]
        build_argv = build_argv[:-1]
        code, _, _ = run_cmd("D", "instrumentation_build", build_argv, timeout=600)
        image_root = (
            RUN_DIR / "vendor_build" / ".pio" / "build" /
            CONFIG["toolchain"]["environment"]
        )
        images = {}
        for name in ("firmware.bin", "bootloader.bin", "partitions.bin"):
            path = image_root / name
            if path.is_file():
                images[name] = {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
        RESULT["build_manifest"] = {
            "exit_code": code,
            "images": images,
            "source_tree_sha256": RESULT["source_manifest"].get("patched_tree_sha256"),
            "patch_sha256": RESULT["patch_manifest"].get("patch_sha256"),
            "toolchain_lock_sha256": CONFIG["toolchain_lock_sha256"],
        }
        RESULT["build_provenance_green"] = bool(
            code == 0 and set(images) == {"firmware.bin", "bootloader.bin", "partitions.bin"}
        )
        if not RESULT["build_provenance_green"]:
            block("instrumentation_build_provenance_not_green")
            return

        RESULT["diagnostic_flash_count"] = 1
        diagnostic_flash_started = True
        flash_argv = [
            pio, "run", "--project-dir", str(RUN_DIR / "vendor_build"),
            "--environment", CONFIG["toolchain"]["environment"],
            "--target", "upload", "--upload-port", str(upload_alias), "",
        ]
        flash_argv = flash_argv[:-1]
        code, _, _ = run_cmd("D", "diagnostic_flash", flash_argv, timeout=300)
        if code != 0:
            block("diagnostic_flash_failed")
        else:
            stationary_readback()
            if not RESULT["diagnostic_readback"].get("schema_valid"):
                block("stationary_additive_readback_not_green")
            RESULT["gate_v"] = bool(RESULT["diagnostic_readback"].get("schema_valid"))
        RESULT["phase_states"]["D"] = "complete" if RESULT["gate_v"] else "blocked"
    except BaseException as exc:
        RESULT["errors"].append({
            "phase": "outer",
            "error_type": type(exc).__name__,
            "message": str(exc)[:240],
        })
        block("runner_exception")
    finally:
        RESULT["phase_states"]["R"] = "running"
        # flash 已开始时只允许当前 backup rollback 一次。
        if diagnostic_flash_started and upload_alias is not None:
            RESULT["rollback_flash_count"] = 1
            rollback_argv = [
                "python3", "-m", "esptool", "--port", str(upload_alias),
                "write_flash", "0x0", str(RUN_DIR / "current_flash_backup.bin"),
            ]
            write_code, _, _ = run_cmd("R", "rollback_flash", rollback_argv, timeout=300)
            verify_argv = [
                "python3", "-m", "esptool", "--port", str(upload_alias),
                "verify_flash", "0x0", str(RUN_DIR / "current_flash_backup.bin"),
            ]
            verify_code, _, _ = run_cmd("R", "rollback_verify", verify_argv, timeout=300)
            restored = write_code == 0 and verify_code == 0
            RESULT["rollback_result"] = {
                "attempted": True,
                "write_exit_code": write_code,
                "verify_exit_code": verify_code,
                "restored": restored,
                "reason": "current_backup_verified" if restored else "rollback_not_verified",
            }
            if not restored:
                block("current_backup_rollback_not_verified")

        # service 初始 active 才恢复一次；初始 inactive 保持 inactive。
        if service_was_active:
            RESULT["service_restore_count"] = 1
            run_cmd("R", "systemctl_start", ["systemctl", "start", SERVICE], timeout=30)
        for _ in range(20):
            after = service_state("R")
            expected = "active" if service_was_active else RESULT["service_before"].get("ActiveState")
            if after.get("ActiveState") == expected:
                break
            time.sleep(0.5)
        RESULT["service_after"] = service_state("R")
        expected_state = "active" if service_was_active else RESULT["service_before"].get("ActiveState")
        RESULT["service_restored"] = RESULT["service_after"].get("ActiveState") == expected_state

        # child 可能稍晚重新持有 UART，只做 bounded read-only observation。
        before_hashes = sorted(
            item["cmd_hash_prefix"] for item in RESULT["holder_before"]
            if item.get("expected_bridge")
        )
        observed = []
        for _ in range(20):
            observed = holders("R")
            after_hashes = sorted(
                item["cmd_hash_prefix"] for item in observed
                if item.get("expected_bridge")
            )
            if after_hashes == before_hashes:
                break
            time.sleep(0.5)
        RESULT["holder_after"] = observed
        after_hashes = sorted(
            item["cmd_hash_prefix"] for item in observed
            if item.get("expected_bridge")
        )
        RESULT["holder_restored"] = after_hashes == before_hashes
        RESULT["deployed_hashes_after"] = deployed_hashes("R")

        # final stop 只调用一次 POST 和一次 status readback。
        RESULT["final_stop_verification_count"] = 1
        stop_ok, stop_payload = http_json("R", "final_stop_post", "POST", "/api/base/stop")
        time.sleep(1)
        status_ok, status_payload = http_json("R", "final_status_get", "GET", "/api/base/status")
        RESULT["final_stopped"] = bool(
            stop_ok and status_ok
            and zero_evidence(stop_payload)
            and zero_evidence(status_payload)
        )
        if not RESULT["service_restored"]:
            block("service_not_restored")
        if not RESULT["holder_restored"]:
            block("holder_not_restored")
        if RESULT["deployed_hashes_before"] != RESULT["deployed_hashes_after"]:
            block("deployed_hashes_changed")
        if not RESULT["final_stopped"]:
            block("final_stop_not_confirmed")

        # backup 已通过 marker export 给外层；远端精确目录必须清理。
        if run_dir_created:
            try:
                shutil.rmtree(RUN_DIR)
            except Exception as exc:
                RESULT["errors"].append({
                    "phase": "R",
                    "error_type": type(exc).__name__,
                    "message": "run_owned_cleanup_failed",
                })
        RESULT["run_owned_residual"] = RUN_DIR.exists()
        if RESULT["run_owned_residual"]:
            block("run_owned_residual_present")
        RESULT["phase_states"]["R"] = "complete"
        RESULT["captured_at"] = now()
        RESULT["status"] = (
            "verified_instrumentation_rollback_complete_not_hil"
            if RESULT["gate_v"] and not RESULT["blockers"] and not RESULT["errors"]
            else "verified_upload_backup_vendor_instrumentation_blocked_fail_closed"
        )

main()
print(
    "O1_VERIFIED_UPLOAD_BACKUP_VENDOR_INSTRUMENTATION_JSON:"
    + json.dumps(RESULT, separators=(",", ":"), sort_keys=True)
)
'''


# 本地时间只用于 fixture 与 transport metadata。
def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# 文件 hash 流式计算，factory binary 与 PDF 不会整体载入内存。
def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


# repo root 从脚本路径推导，避免验收命令 cwd 差异。
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


# Product 指定来源必须在 live 前全部存在并冻结 SHA。
def vendor_hashes(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for relative in VENDOR_FILES:
        path = root / relative
        if not path.is_file():
            raise ValueError(f"missing_vendor_source:{relative}")
        result[relative] = sha256_file(path)
    return result


# 简单 key=value lock parser 对重复 key 和空值 fail closed。
def parse_toolchain_lock(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if "=" not in line:
            raise ValueError("invalid_toolchain_lock_line")
        key, value = line.split("=", 1)
        if not key or not value or key in values:
            raise ValueError("invalid_toolchain_lock_entry")
        values[key] = value
    required = {
        "schema",
        "platformio_core",
        "esptool",
        "platform",
        "framework",
        "board",
        "environment",
        "build_id",
    }
    if set(values) != required:
        raise ValueError("toolchain_lock_keys_mismatch")
    return values


# 本地 patch contract 在 SSH 前证明只修改允许文件并保留关键字段。
def validate_patch_contract(text: str) -> list[str]:
    errors: list[str] = []
    if "--- a/ugv_advance.h" not in text or "+++ b/ugv_advance.h" not in text:
        errors.append("patch_target_not_ugv_advance")
    if "--- a/" in text.replace("--- a/ugv_advance.h", ""):
        errors.append("patch_has_multiple_targets")
    required = (
        'jsonInfoHttp["firmwareBuildId"]',
        'jsonInfoHttp["mainType"]',
        'jsonInfoHttp["moduleType"]',
        'jsonInfoHttp["encA"]',
        'jsonInfoHttp["encB"]',
        'jsonInfoHttp["speedGetA"]',
        'jsonInfoHttp["speedGetB"]',
    )
    errors.extend(f"patch_missing:{item}" for item in required if item not in text)
    forbidden = ("T=900", "CMD_PWM_INPUT", "leftCtrl(", "rightCtrl(", "setGoalSpeed(")
    errors.extend(f"patch_forbidden:{item}" for item in forbidden if item in text)
    return errors


# fixture 具有完整 schema，但明确不包含 live invocation。
def fixture_artifact(payload: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema": SCHEMA,
        "attempt_id": str(payload.get("attempt_id") or "fixture-attempt"),
        "authorization_id": str(payload.get("authorization_id") or "fixture-authorization"),
        "captured_at": utc_now(),
        "runner_invocation_count": 0,
        "attempt_count": 0,
        "inventory_invocation_count": 0,
        "pre_stop_invocation_count": 0,
        "service_stop_count": 0,
        "holder_termination_count": 0,
        "bootloader_identity_probe_count": 0,
        "flash_backup_read_count": 0,
        "vendor_tree_prepare_count": 1,
        "additive_patch_apply_count": 1,
        "instrumentation_build_count": 0,
        "diagnostic_flash_count": 0,
        "stationary_diagnostic_readback_count": 0,
        "rollback_flash_count": 0,
        "service_restore_count": 0,
        "final_stop_verification_count": 0,
        "motion_command_count": 0,
        "t900_write_count": 0,
        "retry_count": 0,
        "second_build_count": 0,
        "second_flash_count": 0,
        "gate_u": bool(payload.get("gate_u")),
        "gate_b": bool(payload.get("gate_b")),
        "gate_v_prebuild": bool(payload.get("gate_v_prebuild")),
        "gate_v": False,
        "build_provenance_green": bool(payload.get("build_provenance_green")),
        "first_failure": None,
        "blockers": [],
        "errors": [],
        "command_ledger": [],
        "phase_states": {"S": "fixture_complete"},
        "port_manifest": {"fixture": True},
        "chip_manifest": {"fixture": True},
        "backup_manifest": {"fixture": True},
        "rollback_manifest": {"fixture": True},
        "source_manifest": {"fixture": True},
        "patch_manifest": {"fixture": True},
        "toolchain_manifest": {"fixture": True},
        "build_manifest": {},
        "diagnostic_readback": {},
        "rollback_result": {"attempted": False, "restored": True, "reason": "fixture"},
        "service_before": {"fixture": True},
        "service_after": {"fixture": True},
        "holder_before": [],
        "holder_after": [],
        "deployed_hashes_before": {"fixture": "0" * 64},
        "deployed_hashes_after": {"fixture": "0" * 64},
        "service_restored": True,
        "holder_restored": True,
        "final_stopped": True,
        "run_owned_residual": False,
        "current_run_artifact_delta": 0,
        "external_artifact_delta": 0,
        "live_control_delta": 0,
        "proof_boundary": "fixture_only_not_hardware",
        "status": "fixture_complete",
    }
    for field in SAFETY_FALSE_FIELDS:
        result[field] = False
    return result


# validator 同时约束 count 类型、gate ordering、安全字段和恢复。
def validate_artifact(data: dict[str, Any], *, live: bool) -> list[str]:
    errors: list[str] = []
    required = {
        "schema",
        "runner_invocation_count",
        "motion_command_count",
        "t900_write_count",
        "retry_count",
        "instrumentation_build_count",
        "diagnostic_flash_count",
        "rollback_flash_count",
        "gate_u",
        "gate_b",
        "gate_v_prebuild",
        "service_restored",
        "holder_restored",
        "final_stopped",
        "run_owned_residual",
    }
    errors.extend(f"missing:{key}" for key in sorted(required - set(data)))
    if data.get("schema") != SCHEMA:
        errors.append("schema_mismatch")
    count_fields = (
        "runner_invocation_count",
        "attempt_count",
        "inventory_invocation_count",
        "pre_stop_invocation_count",
        "service_stop_count",
        "holder_termination_count",
        "bootloader_identity_probe_count",
        "flash_backup_read_count",
        "vendor_tree_prepare_count",
        "additive_patch_apply_count",
        "instrumentation_build_count",
        "diagnostic_flash_count",
        "stationary_diagnostic_readback_count",
        "rollback_flash_count",
        "service_restore_count",
        "final_stop_verification_count",
        "motion_command_count",
        "t900_write_count",
        "retry_count",
        "second_build_count",
        "second_flash_count",
    )
    for key in count_fields:
        value = data.get(key)
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"invalid_count_type:{key}")
        elif value < 0 or value > 1:
            errors.append(f"count_out_of_range:{key}:{value}")
    for key in ("motion_command_count", "t900_write_count", "retry_count", "second_build_count", "second_flash_count"):
        if data.get(key) != 0:
            errors.append(f"forbidden_count_nonzero:{key}")
    if data.get("instrumentation_build_count") or data.get("diagnostic_flash_count"):
        if not (data.get("gate_u") and data.get("gate_b") and data.get("gate_v_prebuild")):
            errors.append("build_or_flash_without_all_prebuild_gates")
    if not (data.get("gate_u") and data.get("gate_b") and data.get("gate_v_prebuild")):
        for key in ("instrumentation_build_count", "diagnostic_flash_count", "rollback_flash_count"):
            if data.get(key) != 0:
                errors.append(f"gate_red_but_count_nonzero:{key}")
    if data.get("diagnostic_flash_count") == 1 and data.get("rollback_flash_count") != 1:
        errors.append("diagnostic_flash_without_exactly_one_rollback")
    if data.get("diagnostic_flash_count") == 1 and not data.get("build_provenance_green"):
        errors.append("diagnostic_flash_without_build_provenance")
    for field in SAFETY_FALSE_FIELDS:
        if data.get(field) is not False:
            errors.append(f"dangerous_truth:{field}")
    if live:
        if data.get("runner_invocation_count") != 1:
            errors.append("runner_invocation_count_not_one")
        if data.get("attempt_count") != 1:
            errors.append("attempt_count_not_one")
        if data.get("inventory_invocation_count") != 1:
            errors.append("inventory_invocation_count_not_one")
        if data.get("pre_stop_invocation_count") != 1:
            errors.append("pre_stop_invocation_count_not_one")
        if data.get("final_stop_verification_count") != 1:
            errors.append("final_stop_verification_count_not_one")
        if data.get("attempt_id") != EXPECTED_ATTEMPT_ID:
            errors.append("attempt_id_mismatch")
        if data.get("authorization_id") != EXPECTED_AUTHORIZATION_ID:
            errors.append("authorization_id_mismatch")
        for field in ("service_restored", "holder_restored", "final_stopped"):
            if data.get(field) is not True:
                errors.append(f"restoration_not_true:{field}")
        if data.get("run_owned_residual") is not False:
            errors.append("run_owned_residual_not_false")
    return errors


# artifact 使用稳定缩进与排序，供 Product 精确核对。
def write_artifact(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


# fixture 只读取单一 fixture.json，不隐式合并目录其它内容。
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
    print(f"status={result['status']}")
    return 0


# SSH stdout 必须恰好包含一个 marker，避免日志拼接成伪 artifact。
def parse_remote_result(stdout: str) -> dict[str, Any]:
    marker = "O1_VERIFIED_UPLOAD_BACKUP_VENDOR_INSTRUMENTATION_JSON:"
    matches = [line[len(marker):] for line in stdout.splitlines() if line.startswith(marker)]
    if len(matches) != 1:
        raise ValueError(f"remote_result_marker_count:{len(matches)}")
    data = json.loads(matches[0])
    if not isinstance(data, dict):
        raise ValueError("remote_result_not_object")
    return data


# 本地 preflight 冻结 source/patch/toolchain 内容，SSH 后不可改变。
def local_contract(root: Path) -> dict[str, Any]:
    diagnostic_root = root / "onboard/src/esp32_firmware/wave_rover_v0_9_diagnostic"
    platformio_path = diagnostic_root / "platformio.ini"
    patch_path = diagnostic_root / "patches/additive_diagnostic.patch"
    lock_path = diagnostic_root / "toolchain.lock"
    for path in (platformio_path, patch_path, lock_path):
        if not path.is_file():
            raise ValueError(f"missing_diagnostic_contract:{path.name}")
    platformio_text = platformio_path.read_text()
    patch_text = patch_path.read_text()
    lock_text = lock_path.read_text()
    patch_errors = validate_patch_contract(patch_text)
    if patch_errors:
        raise ValueError("patch_contract:" + ",".join(patch_errors))
    toolchain = parse_toolchain_lock(lock_text)
    if f"platform = {toolchain['platform']}" not in platformio_text:
        raise ValueError("platformio_platform_not_locked")
    if f"board = {toolchain['board']}" not in platformio_text:
        raise ValueError("platformio_board_not_locked")
    if f"framework = {toolchain['framework']}" not in platformio_text:
        raise ValueError("platformio_framework_not_locked")
    return {
        "platformio_text": platformio_text,
        "patch_text": patch_text,
        "toolchain_lock_text": lock_text,
        "platformio_sha256": sha256_file(platformio_path),
        "patch_sha256": sha256_file(patch_path),
        "toolchain_lock_sha256": sha256_file(lock_path),
        "toolchain": toolchain,
    }


# full backup 若存在，由唯一 runner stdout 自动导出到本 sprint artifacts。
def persist_backup_export(output_path: Path, result: dict[str, Any]) -> None:
    encoded = result.pop("_backup_export_b64", None)
    if encoded is None:
        return
    backup = base64.b64decode(encoded, validate=True)
    expected = result.get("backup_manifest", {}).get("sha256")
    actual = hashlib.sha256(backup).hexdigest()
    if not expected or expected != actual:
        raise ValueError("backup_export_hash_mismatch")
    backup_path = output_path.parent / "current_flash_backup.bin"
    backup_path.write_bytes(backup)
    result["backup_manifest"]["local_artifact_basename"] = backup_path.name
    result["backup_manifest"]["local_artifact_sha256"] = actual


# 真实入口只有此处一次 subprocess.run(ssh)，无循环和补跑。
def run_ssh_maintenance(args: argparse.Namespace) -> int:
    if args.ssh_host != EXPECTED_HOST or args.ssh_port != EXPECTED_PORT:
        raise ValueError("ssh_target_not_frozen")
    if args.authorization_id != EXPECTED_AUTHORIZATION_ID:
        raise ValueError("authorization_id_not_frozen")
    if args.attempt_id != EXPECTED_ATTEMPT_ID:
        raise ValueError("attempt_id_not_frozen")
    if not args.strict_no_motion:
        raise ValueError("strict_no_motion_required")
    if not args.allow_exactly_one_diagnostic_build_flash_after_all_gates:
        raise ValueError("conditional_build_flash_authorization_required")

    root = repo_root()
    hashes = vendor_hashes(root)
    contract = local_contract(root)
    required_relatives = [
        relative for relative in VENDOR_FILES
        if "/WAVE_ROVER_V0.9/" in relative
    ]
    config = {
        "schema": SCHEMA,
        "authorization_id": args.authorization_id,
        "attempt_id": args.attempt_id,
        "service": SERVICE,
        "normal_uart": NORMAL_UART,
        "normal_baudrate": NORMAL_BAUDRATE,
        "remote_repo": REMOTE_REPO,
        "run_dir": RUN_DIR,
        "vendor_source_hashes": hashes,
        "required_vendor_source_relatives": required_relatives,
        "factory_target_sha256": hashes[VENDOR_FILES[-1]],
        "deployed_paths": list(DEPLOYED_PATHS),
        "safety_false_fields": list(SAFETY_FALSE_FIELDS),
        **contract,
    }
    config["remote_script_sha256"] = hashlib.sha256(
        textwrap.dedent(REMOTE_SCRIPT).encode("utf-8")
    ).hexdigest()
    config_json = json.dumps(config, separators=(",", ":"), sort_keys=True)
    remote_source = "CONFIG_JSON = " + repr(config_json) + "\n" + textwrap.dedent(REMOTE_SCRIPT)
    request_sha = hashlib.sha256(remote_source.encode("utf-8")).hexdigest()
    command = [
        "ssh",
        "-p",
        str(args.ssh_port),
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=10",
        args.ssh_host,
        "python3",
        "-",
    ]
    completed = subprocess.run(
        command,
        input=remote_source,
        text=True,
        capture_output=True,
        timeout=900,
        check=False,
    )
    result = parse_remote_result(completed.stdout)
    output_path = Path(args.output)
    persist_backup_export(output_path, result)
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
        if result.get("first_failure") is None:
            result["first_failure"] = "ssh_transport_nonzero"
    result["artifact_validation_errors"] = validate_artifact(result, live=True)
    write_artifact(output_path, result)
    print(f"status={result.get('status')}")
    print(f"first_failure={result.get('first_failure')}")
    print(f"gate_u/gate_b/gate_v_prebuild={result.get('gate_u')}/{result.get('gate_b')}/{result.get('gate_v_prebuild')}")
    return 0 if not result["artifact_validation_errors"] else 7


# 参数名与 tech-plan Engineer 验收命令逐字对齐。
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="O1 verified upload/backup/vendor instrumentation runner"
    )
    parser.add_argument("--mode", required=True, choices=("fixture", "ssh-maintenance"))
    parser.add_argument("--fixture-dir")
    parser.add_argument("--ssh-host")
    parser.add_argument("--ssh-port", type=int)
    parser.add_argument("--authorization-id")
    parser.add_argument("--attempt-id")
    parser.add_argument("--strict-no-motion", action="store_true")
    parser.add_argument(
        "--allow-exactly-one-diagnostic-build-flash-after-all-gates",
        action="store_true",
    )
    parser.add_argument("--output", required=True)
    return parser


# hostile 本地输入稳定返回 exit 4；live artifact validator 失败返回 7。
def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.mode == "fixture":
            if not args.fixture_dir:
                raise ValueError("fixture_dir_required")
            return run_fixture(args)
        if not args.ssh_host or args.ssh_port is None:
            raise ValueError("ssh_target_required")
        return run_ssh_maintenance(args)
    except (ValueError, OSError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print(f"ERROR:{type(exc).__name__}:{exc}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
