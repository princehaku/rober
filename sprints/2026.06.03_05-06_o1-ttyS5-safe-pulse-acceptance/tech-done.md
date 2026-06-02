# 2026.06.03_05-06 O1 ttyS5 Safe Pulse Acceptance

## sprint_type

micro

## Owner

robot-hardware-engineer

## 实际改动

- 新增 `onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py`：O1 `/dev/ttyS5 @115200` 短时点动验收 runner，schema 为 `trashbot.o1.ttyS5_safe_pulse_acceptance.v1`。
- 新增 `onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py`：使用 fake HTTP / monkeypatch 验证默认 dry-run 不 POST 运动、执行模式必须双确认、速度/时长限幅、manual 后追加 stop evidence、`--output` 原子写入。
- 代码审阅修复：显式 `--dry-run` 现在是最高优先级安全闸，即使同时传入 `--execute-motion --confirm-physical-clearance` 也不会 POST `/api/base/manual` 或 `/api/base/stop`；`execution_gate.reason` 会说明 dry-run blocks execution。
- 更新 `docs/hardware/o1_wave_rover_serial_feedback_probe.md`：记录 runner 的默认只读边界、执行双确认、`--output` 原子 artifact 和不直连串口规则。
- 更新 `docs/interfaces/o1_o5_90_evidence_boundary.md`：明确 runner 只能是 `ready_for_real_short_pulse_collection_not_hil`，不能提升 O1 90% HIL 证据。
- 更新 `docs/interfaces/o7_upper_robot_api.md`：补充 8787 API 下的 O1 safe pulse runner runbook。

## 已读 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/hardware/o1_wave_rover_serial_feedback_probe.md`
- `docs/interfaces/o1_o5_90_evidence_boundary.md`
- `docs/interfaces/o7_upper_robot_api.md`

## 已证实硬件结论

- WAVE ROVER vendor 上位机参考使用 UART、UTF-8 JSON、每行一个 JSON object，并以 `\n` 结尾。
- vendor Raspberry Pi reference 端口是 `/dev/ttyAMA0`、baudrate `115200`；Orange Pi 现场控制口已按既有证据收敛到 `/dev/ttyS5 @115200`，不能照抄 Raspberry Pi 端口。
- `CMD_SPEED_CTRL=1` 是左右轮速度命令，`CMD_BASE_FEEDBACK=130` 是 base feedback request，`FEEDBACK_BASE_INFO=1001` 是 base feedback 类型。
- 当前 `T=1001` / ACK 仍未证明，因此 runner 输出和文档都保持 `safe_to_control=false`、`delivery_success=false`。

## 验证结果

```bash
python3 -m py_compile onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py
```

结果：exit 0。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py
```

结果：

```text
.....
----------------------------------------------------------------------
Ran 5 tests in 0.071s

OK
```

```bash
python3 onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py --dry-run --once-json | python3 -m json.tool
```

结果：exit 0。关键输出：

```text
schema=trashbot.o1.ttyS5_safe_pulse_acceptance.v1
evidence_boundary=api_status_dry_run_not_hil
execution_gate.dry_run=true
execution_gate.authorized=false
execution_gate.reason=dry-run blocks execution even when execute/confirm flags are present
upper_api.base_url=http://127.0.0.1:8787
status_request.ok=false
status_request.error.type=URLError
status_request.error.message=<urlopen error timed out>
safe_to_control=false
sends_commands=false
sends_motion_commands=false
robot_control_executed=false
delivery_success=false
manual_request=null
stop_request=null
t1001_feedback_status=unknown
```

```bash
python3 - <<'PY'
from pathlib import Path
files = [
    'onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py',
    'onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py',
]
for f in files:
    lines = [l for l in Path(f).read_text(encoding='utf-8').splitlines() if l.strip()]
    comments = [l for l in lines if l.lstrip().startswith('#') or '"""' in l]
    print(f, len(comments), len(lines), round(len(comments)/len(lines), 3))
PY
```

结果：

```text
onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py 62 310 0.2
onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py 29 143 0.203
```

```bash
git diff --check -- onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py docs/hardware/o1_wave_rover_serial_feedback_probe.md docs/interfaces/o1_o5_90_evidence_boundary.md docs/interfaces/o7_upper_robot_api.md sprints/2026.06.03_05-06_o1-ttyS5-safe-pulse-acceptance/tech-done.md
```

结果：exit 0，无输出。

## 是否发送运动命令

本轮没有发送任何运动命令。没有执行远端 `/api/base/manual`，没有执行远端 `/api/base/stop`，没有打开 `/dev/ttyS5`，没有发送 `T=1/T=13/T=130/T=131`，没有发送 `/cmd_vel`。

## 剩余风险

- 本轮只完成 runner、fake HTTP 单测和本地 dry-run 护栏；未进行真实现场点动。
- 8787 远端 status 和 `/api/base/manual` 的真实材料仍需现场有人看护且 CEO 明确授权后采集。
- `T=1001` / ACK、真实 `/odom`、`/imu/data`、`/battery`、急停路径和 HIL packet 仍为 `not_proven`。
- Micro sprint 软提醒：本轮直接针对当前最低 Objective O1。

## Product closeout / OKR verdict

用户价值：本轮把 O1 从 8787 upper API guardrail ready 推进到 safe pulse acceptance runner ready / watched execution pending。现场点动前置条件从“临时手工命令”变成可复验 runner：默认 dry-run/read-only，显式 `--dry-run` 会覆盖 execute/confirm，只有同时传入 `--execute-motion --confirm-physical-clearance` 且非 dry-run 时才允许经 8787 `/api/base/manual` 做低速短 pulse，runner 不直接打开 `/dev/ttyS5`。

OKR 映射和方向判断：Objective 1 继续推进，但进度保持约 93%。本轮新增的是受控现场执行前置和验收合同，不是真实 HIL、ACK 或 ROS topic 证据，因此不能上调为 HIL pass、闭环安全控制、真实 `/cmd_vel` 接入或 delivery success。

KR 更新：O1 当前口径从 `upper API guardrail ready` 更新为 `safe pulse acceptance runner ready / watched execution pending`。O1 KR3 的 `T=1001` 反馈、真实 `/imu/data`、`/battery`、`/odom` 仍未完成；KR4/验收护栏获得 runner fake HTTP 单测、dry-run fail-closed JSON 和 diff-check 支撑；没有 KR 进入历史归档区。

本轮核心抓手：用 runner 把下一次现场 watched field pulse execution 的安全门槛、证据 schema、dry-run 默认行为和双确认执行条件固定下来。已验证：`py_compile` pass、5 focused tests pass、dry-run JSON valid 且 fail-closed、scoped diff-check pass。

下一步优先级：最高优先级仍是 O1 watched field pulse execution + ACK/`T=1001` capture。验收口径必须包含现场看护、物理净空、人工急停可用、经 8787 `/api/base/manual` 低速短 pulse、自动 stop 复位、status/manual/stop 同源日志、ACK 或 `T=1001` 采集，以及失败时 fail-closed 记录。

责任 Engineer：下一轮主责仍为 `rober-hardware-engineer` / `robot-hardware-engineer`。如需要把结果接入 PC Live Operator 或 ROS topic 展示，再由 `full-stack-software-engineer` 或 `robot-software-engineer` 做后续切片，不在本轮扩大范围。

风险和证据缺口：本轮没有发送任何运动命令，没有 POST `/api/base/manual` 或 stop，没有打开 `/dev/ttyS5`，没有发送 `T=1/T=13/T=130/T=131` 或 `/cmd_vel`。真实短 pulse、auto-stop 现场材料、ACK/`T=1001`、真实 `/odom`、`/imu/data`、`/battery`、急停路径、HIL packet 和完整 delivery success 仍为 `not_proven`。

文档同步：本轮 Product closeout 已同步更新 `OKR.md` 和 `docs/process/okr_progress_log.md`，本 `tech-done.md` 追加 OKR verdict。历史记录位置为 `docs/process/okr_progress_log.md` 的 `2026-06-03 05-06｜O1 ttyS5 safe pulse acceptance runner｜Product closeout` 小节；剩余风险继续留在当前推进区。
