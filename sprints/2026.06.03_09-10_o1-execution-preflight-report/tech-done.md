# O1 Execution Preflight Report

## sprint_type

micro

## 已读 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- 上轮 sprint：`sprints/2026.06.03_08-09_o1-operator-report-intake/tech-done.md`

## 已证实的硬件结论

- WAVE ROVER vendor reference 使用 UART、UTF-8 JSON、每行一个 JSON object 并以 `\n` 结束。
- vendor Raspberry Pi reference 使用 `/dev/ttyAMA0 @115200`；本项目 Orange Pi 现场底盘控制口仍以已观察到的 `/dev/ttyS5 @115200` 记录，不能从 Raspberry Pi 默认路径外推。
- `json_cmd.h` 定义 `T=1` 为底盘速度控制、`T=13` 为 ROS velocity、`T=130` 为 base feedback request、`T=131` 为 feedback flow、`T=1001` 为 base info feedback。
- 本轮只修复 safe pulse runner 的 operator report 两阶段软件合同，状态名为 `execution_preflight_report_ready_not_hil`；没有执行真实 motion，没有 POST 远端 `/api/base/manual` 或 `/api/base/stop`，没有打开 `/dev/ttyS5`，没有发送 WAVE ROVER JSON 或 ROS `/cmd_vel`。

## 实际改动

- `onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py`
  - 将 operator report 拆成执行前 preflight 字段和执行后 observation/review 字段。
  - `operator_report_status` 扩展为 `missing|ready_for_execution|ready_for_review|unsafe_or_incomplete`。
  - preflight 三项 `operator_present`、`physical_clearance_confirmed`、`emergency_stop_ready` 均为 true 时进入 `ready_for_execution`，允许执行模式通过 operator report gate。
  - preflight true 且 `observed_motion`、`observed_stop`、`operator_notes`、`reported_at` 完整时进入 `ready_for_review`。
  - preflight 缺失、false 或解析失败时仍 fail-closed 到 `operator_report_missing_or_incomplete`。
  - 保持 `safe_to_control=false`、`hil_pass=false`、dry-run 不发命令。
- `onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py`
  - 新增 preflight-only report 的执行路径回归测试，证明不再要求执行前先观察到运动/停止。
  - 新增 dry-run 携带 preflight-only report 仍不发送命令的回归测试。
  - 保留完整 report、缺 report、unsafe report、post-status/T=1001 不提升 HIL 的 fake HTTP 覆盖。
- `docs/hardware/o1_wave_rover_serial_feedback_probe.md`
  - 更新 operator report 两阶段合同和 `execution_preflight_report_ready_not_hil` 边界。
- `docs/interfaces/o1_o5_90_evidence_boundary.md`
  - 明确本轮只能记录为 `execution_preflight_report_ready_not_hil`，不得写成 HIL pass。
- `docs/interfaces/o7_upper_robot_api.md`
  - 更新 safe pulse runner 的 operator report status 和执行前/执行后字段分工。
- `sprints/2026.06.03_09-10_o1-execution-preflight-report/tech-done.md`
  - 新建本 micro sprint 留档。

## 验证结果

```text
$ python3 -m py_compile onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py
exit 0
```

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py
................
----------------------------------------------------------------------
Ran 16 tests in 0.310s

OK
```

```text
$ printf '%s' '{"operator_present":true,"physical_clearance_confirmed":true,"emergency_stop_ready":true}' | python3 onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py --dry-run --operator-report-json - --once-json
operator_report_status=ready_for_execution
acceptance_verdict.status=dry_run_only
acceptance_verdict.safe_to_control=false
acceptance_verdict.hil_pass=false
sends_commands=false
sends_motion_commands=false
robot_control_executed=false
manual_request=null
stop_request=null
status_request.ok=false
status_request.error.type=URLError
```

本机 `127.0.0.1:8787` 不可达，dry-run status 读取超时并 fail-closed；该结果符合默认只读、不发送命令的验收边界。

```text
$ git diff --check -- onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py docs/hardware/o1_wave_rover_serial_feedback_probe.md docs/interfaces/o1_o5_90_evidence_boundary.md docs/interfaces/o7_upper_robot_api.md sprints/2026.06.03_09-10_o1-execution-preflight-report/tech-done.md
exit 0
```

## 未验证项、风险敞口和下一步

- 本轮没有真实上车点动，没有 POST 远端 `/api/base/manual`，没有 POST 远端 `/api/base/stop`，没有打开 `/dev/ttyS5`，没有发送 `T=1/T=13/T=130/T=131`，没有发送 `/cmd_vel`。
- `ready_for_execution` 只表示执行前安全 preflight report 满足，不表示运动已经发生、停止已经观察到、ACK 已连接或 HIL pass。
- `ready_for_review` 也不能让 `safe_to_control` 或 `hil_pass` 变 true；它只表示执行后观察材料可进入复核。
- 真实 O1 下一步仍是 watched field pulse execution + ACK/`T=1001` capture：现场看护、物理净空、急停/断电路径可用后，经 8787 API 采集 status/manual/stop/post-status、operator report、ACK 或 `T=1001`，再进入 HIL packet review。
- 本轮未读取、未改写、未回滚无关脏文件 `pc-tools/workstation/test/catalog.test.ts`。

## Product / OKR 收口

- 用户价值和北极星：本轮把 O1 现场点动前的 operator report 从“必须先有运动/停止观察”修正为“执行前 preflight 满足即可进入受控执行”，服务普通手机用户可用垃圾投递机器人的可信底盘控制证据链。
- OKR 映射和方向判断：Objective 1 继续；进度文字调整为 `execution preflight report ready / watched execution pending`，仍保持约 93%，不上调。
- KR 影响：增强 KR3/KR4/KR5 的执行前报告门槛、执行后复核和 fail-closed 合同；真实 ACK、`T=1001`、HIL 和 ROS topic 未完成，因此没有 KR 进入历史完成归档。
- 本轮核心抓手：`ready_for_execution` 支持 watched execution 前通过 report gate，`ready_for_review` 支持执行后复核；dry-run 仍固定不发命令。
- 需要做什么：下一步由 `robot-hardware-engineer` 主责 watched field pulse execution + ACK/`T=1001` capture；必要时 `robot-software-engineer` 只补 ROS topic/bridge 接口事实。
- 优先级和验收口径：P0；现场看护、物理净空、急停/断电路径可用，经 8787 `/api/base/manual` 做低速短 pulse，并采集 status/manual/stop/post-status、operator report、ACK 或 `T=1001`、日志与安全复位证据。
- 风险和证据缺口：本轮不是 HIL，没有真实 motion、POST manual/stop、`/dev/ttyS5` 打开、WAVE ROVER JSON、`/cmd_vel`、ACK、`T=1001`、真实 `/odom`、`/imu/data`、`/battery` 或 delivery success。
- 历史记录位置：本轮无已完成 KR 历史归档；产品收口记录同步到 `docs/process/okr_progress_log.md` 的 `2026-06-03 09-10｜O1 execution preflight report｜Product closeout`。
