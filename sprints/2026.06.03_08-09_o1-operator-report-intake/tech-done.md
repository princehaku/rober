# O1 Operator Report Intake

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

## 已证实的硬件结论

- WAVE ROVER vendor reference 使用 UART、UTF-8 JSON、每行一个 JSON object 并以 `\n` 结束。
- vendor Raspberry Pi reference 使用 `/dev/ttyAMA0 @115200`；本项目 Orange Pi 现场底盘控制口仍以已观察到的 `/dev/ttyS5 @115200` 记录，不能从 Raspberry Pi 默认路径外推。
- `json_cmd.h` 定义 `T=1` 为底盘速度控制、`T=13` 为 ROS velocity、`T=130` 为 base feedback request、`T=131` 为 feedback flow、`T=1001` 为 base info feedback。
- 本轮只做 operator report intake 的软件合同和 dry-run 验证，不执行真实 motion，不证明 ACK、`T=1001`、ROS topic 或 HIL pass。

## 实际改动

- `onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py`
  - 新增 `--operator-report-json PATH_OR_-`。
  - 新增 operator report 读取、布尔归一化和 `operator_report_status=missing|ready_for_review|unsafe_or_incomplete`。
  - artifact 新增 `operator_report`、`operator_report_status`、`operator_report_error`。
  - 执行模式缺失或不完整 operator report 时，fail-closed 到 `failed_step=operator_report_missing_or_incomplete`，不 POST `/api/base/manual`。
  - dry-run 即使携带完整 operator report，仍保持不发送命令，且 status 读取失败时保持 `acceptance_verdict.status=dry_run_only`。
- `onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py`
  - 新增 path/stdin operator report、缺失 report、完整 report、不完整 report、execute 缺 report 阻断、dry-run 完整 report 仍不发送命令、dry-run status 失败仍为 dry-run verdict 的回归测试。
  - 既有 execute fake HTTP 测试补充完整 operator report fixture，避免绕过新增安全闸。
- `docs/hardware/o1_wave_rover_serial_feedback_probe.md`
  - 补充 operator report intake 字段、状态分类和执行模式缺报告 fail-closed 边界。
- `docs/interfaces/o7_upper_robot_api.md`
  - 补充 `--operator-report-json` dry-run/execute 用法和 8787 API 证据边界。
- `docs/interfaces/o1_o5_90_evidence_boundary.md`
  - 明确 operator report intake 是 `operator_report_intake_ready_not_hil`，不能替代同源 HIL packet。
- `sprints/2026.06.03_08-09_o1-operator-report-intake/tech-done.md`
  - 补充 Hardware Infra 复验结果，确认本轮只在允许文件范围内收口，不新增真实运动或 SSH 操作。

## 验证结果

```text
$ python3 -m py_compile onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py
exit 0
```

```text
$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py
..............
----------------------------------------------------------------------
Ran 14 tests in 0.265s

OK
```

```text
$ python3 onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py --dry-run --operator-report-json <tmp完整报告JSON> --once-json
schema=trashbot.o1.ttyS5_safe_pulse_acceptance.v1
sends_commands=false
robot_control_executed=false
manual_request=null
operator_report_status=ready_for_review
acceptance_verdict.status=dry_run_only
acceptance_verdict.safe_to_control=false
acceptance_verdict.hil_pass=false
```

```text
$ git diff --check -- onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py onboard/scripts/test_o1_ttyS5_safe_pulse_acceptance.py docs/hardware/o1_wave_rover_serial_feedback_probe.md docs/interfaces/o1_o5_90_evidence_boundary.md docs/interfaces/o7_upper_robot_api.md sprints/2026.06.03_08-09_o1-operator-report-intake/tech-done.md
exit 0
```

## 未验证项、风险敞口和下一步

- 本轮没有发送运动命令，没有 POST 远端 `/api/base/manual` 或 `/api/base/stop`，没有打开 `/dev/ttyS5`，没有发送 WAVE ROVER `T=1/T=13/T=130/T=131`，没有发送 ROS `/cmd_vel`。
- `/tmp/o1_operator_report_dryrun.json` 是本机 dry-run artifact；由于本机 `127.0.0.1:8787` 不可达，status 读取失败被记录为 `failed_step=status_request`，但 verdict 仍是 `dry_run_only`，没有运动授权。
- operator report 只能作为 HIL 前置人工观察材料；即使 `operator_report_status=ready_for_review`，也不能证明 ACK、`T=1001`、真实 `/odom`、`/imu/data`、`/battery` 或急停/断电路径。
- 下一步仍是 watched field pulse execution + ACK/`T=1001` capture：现场明确授权、物理净空、人工看护、急停/断电路径可用后，经 8787 API 采集 status/manual/stop/post-status、operator report、ACK 或 `T=1001`，再进入 HIL packet review。
