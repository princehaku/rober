# Sprint 2026.05.17_21-22 Wave Rover HIL Packet Intake - Tech Done

sprint_type: epic

## 1. 实际改动

本轮按 `tech-plan.md` 的 A/B/C/D 分工完成，Product closeout 只做整体验收、OKR 更新和留档，不修改产品代码、测试代码、PC gate、mobile 或 diagnostics。

### Task A - hardware-engineer

- 新增 `pc-tools/evidence/wave_rover_hil_packet_intake.py`。
- 新增 `pc-tools/evidence/test_wave_rover_hil_packet_intake.py`。
- 新增 `pc-tools/evidence/fixtures/wave_rover_hil_packet_intake/` synthetic pass / fail_mismatch packet fixtures。
- 新增 `docs/hardware/wave_rover_hil_packet_intake.md`。

Task A 采用的 vendor 来源：`docs/vendor/VENDOR_INDEX.md`、`docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`、`docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`、`docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`、`docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`。

### Task B - robot-software-engineer

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`，新增 `wave_rover_hil_packet_intake` metadata-only diagnostics consumer。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 更新 `docs/interfaces/ros_contracts.md`。

### Task C - full-stack-software-engineer

- 更新 `mobile/web/app.js`，新增 WAVE ROVER HIL packet intake 只读 panel。
- 更新 `mobile/fixtures/mobile_web_status.fixture.json`。
- 更新 `mobile/web/test_mobile_web_entrypoint.py`。
- 更新 `docs/product/mobile_user_flow.md`。

### Task D - product-okr-owner

- 新增本文件。
- 新增 `sprints/2026.05.17_21-22_wave-rover-hil-packet-intake/side2side_check.md`。
- 新增 `sprints/2026.05.17_21-22_wave-rover-hil-packet-intake/final.md`。
- 更新 `OKR.md`。
- 更新 `docs/process/okr_progress_log.md`。

## 2. 验证结果

整体验收在 2026-05-17 21:22 Asia/Shanghai 后执行。结果：

```text
python3 -m py_compile ...wave_rover_hil_packet_intake.py ...test_wave_rover_hil_packet_intake.py ...operator_gateway_diagnostics.py ...test_operator_gateway_diagnostics.py
exit 0

python3 -m unittest pc-tools/evidence/test_wave_rover_hil_packet_intake.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py mobile/web/test_mobile_web_entrypoint.py
Ran 225 tests in 0.549s
OK

python3 pc-tools/evidence/wave_rover_hil_packet_intake.py --help
usage: wave_rover_hil_packet_intake.py [-h] [--evidence-ref EVIDENCE_REF] [--summary-output SUMMARY_OUTPUT] [--once-json] [packet_dir]
exit 0

node --check mobile/web/app.js
exit 0

test -f tech-done.md && test -f side2side_check.md && test -f final.md
exit 0

rg required boundary checks
matched software_proof_docker_wave_rover_hil_packet_intake_gate, Objective 1, Objective 5, PR #4, PR #5, not_proven, delivery_success=false, primary_actions_enabled=false, hil_pass

rg implementation contract checks
matched wave_rover_hil_packet_intake, trashbot.wave_rover_hil_packet_intake, trashbot.wave_rover_hil_packet_intake_summary

git diff --check -- scoped sprint files
exit 0
```

Pre-commit checks:

```text
git diff --cached --check
exit 0

git status --short --branch
## master...origin/master
staged relevant sprint files only
```

## 3. 偏差与失败定位

未发现需要阻塞 Task D 的失败。整体验收没有要求真实硬件验证，本轮也没有真实 WAVE ROVER、真实 UART、真实串口设备或真实 HIL packet 输入。

本轮验证只证明 `software_proof_docker_wave_rover_hil_packet_intake_gate` 的 PC / Robot diagnostics / mobile read-only / Product closeout 链路可执行，且保持：

- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

## 4. 剩余风险

- 未证明 `hil_pass`。
- 未证明真实 WAVE ROVER、真实 UART、真实 `/odom`、真实 `/imu/data`、真实 `/battery`。
- 未证明真实 route/elevator field pass、真实手机/browser、Objective 5 external proof 或 delivery success。
- PR #4 仍缺真实门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record、completion signal、dropoff/cancel completion 和 delivery result。
- PR #5 仍缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry 材料。
