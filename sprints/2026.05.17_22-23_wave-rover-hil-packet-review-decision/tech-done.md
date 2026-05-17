# Sprint 2026.05.17_22-23 Wave Rover HIL Packet Review Decision - Tech Done

sprint_type: epic

## 1. 实际改动

本轮按 `tech-plan.md` 的 A/B/C/D 分工完成。Product closeout 只做整体验收、OKR 更新和留档；未修改 PC gate、Robot diagnostics、mobile/web 产品代码或测试代码。

### Task A - hardware-engineer

- 新增 `pc-tools/evidence/wave_rover_hil_packet_review_decision.py`。
- 新增 `pc-tools/evidence/test_wave_rover_hil_packet_review_decision.py`。
- 新增 `pc-tools/evidence/fixtures/wave_rover_hil_packet_review_decision/intake_ready.json`。
- 新增 `docs/hardware/wave_rover_hil_packet_review_decision.md`。

Task A 采用的 vendor 来源：`docs/vendor/VENDOR_INDEX.md`、`docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`、`docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`、`docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`、`docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`。

### Task B - robot-software-engineer

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`，新增 `wave_rover_hil_packet_review_decision` metadata-only diagnostics consumer。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 更新 `docs/interfaces/ros_contracts.md`。

### Task C - full-stack-software-engineer

- 更新 `mobile/web/app.js`，新增 WAVE ROVER HIL packet review decision 只读 panel。
- 更新 `mobile/fixtures/mobile_web_status.fixture.json`。
- 更新 `mobile/web/test_mobile_web_entrypoint.py`。
- 更新 `docs/product/mobile_user_flow.md`。

### Task D - product-okr-owner

- 新增本文件。
- 新增 `sprints/2026.05.17_22-23_wave-rover-hil-packet-review-decision/side2side_check.md`。
- 新增 `sprints/2026.05.17_22-23_wave-rover-hil-packet-review-decision/final.md`。
- 更新 `OKR.md`。
- 更新 `docs/process/okr_progress_log.md`。

## 2. 验证结果

Task D closeout 在 2026-05-17 22:18 Asia/Shanghai 后独立执行验收，不只引用 worker 摘要。

### 初始 closeout 检查

```text
test -f tech-done.md && test -f side2side_check.md && test -f final.md
exit 1
```

失败定位：Task D 尚未创建三份 closeout 文件，属于本轮待完成 closeout 工作，不是 A/B/C 实现失败。

### 集成围栏

```text
python3 -m py_compile pc-tools/evidence/wave_rover_hil_packet_review_decision.py pc-tools/evidence/test_wave_rover_hil_packet_review_decision.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
exit 0

python3 -m unittest pc-tools/evidence/test_wave_rover_hil_packet_review_decision.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py mobile/web/test_mobile_web_entrypoint.py
Ran 227 tests in 0.543s
OK

node --check mobile/web/app.js
exit 0

python3 pc-tools/evidence/wave_rover_hil_packet_review_decision.py --help
usage: wave_rover_hil_packet_review_decision.py [-h] [--intake-summary INTAKE_SUMMARY] [--evidence-ref EVIDENCE_REF] [--output OUTPUT] [--summary-output SUMMARY_OUTPUT] [--once-json]
exit 0

git diff --check -- A/B/C touched files
exit 0
```

### Closeout 围栏

```text
rg required closeout tokens
matched software_proof_docker_wave_rover_hil_packet_review_decision_gate, Objective 1, Objective 5, PR #4, PR #5, not_proven, delivery_success=false, primary_actions_enabled=false, hil_pass

git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_22-23_wave-rover-hil-packet-review-decision
exit 0 before closeout edits
```

最终 closeout 后的完整复验结果以 `final.md` 为准。

## 3. 偏差与失败定位

Task A worker 已修复 unsupported top-level schema 被 valid `summary_schema` 误放行的问题；Product closeout 复验后未发现该问题复现。

Task C worker 第一轮 unittest 抓到 fixture 中 `raw packet` 禁词，已改为 `unsafe packet material` 并通过；Product closeout 复验后未发现 mobile fixture / entrypoint 测试失败。

Task D 初始 file existence check 失败，原因是 closeout 文件尚未创建；本文件、`side2side_check.md` 和 `final.md` 创建后需要复验。

## 4. 剩余风险

本轮只证明 `software_proof_docker_wave_rover_hil_packet_review_decision_gate` 的 PC / Robot diagnostics / mobile read-only / Product closeout 链路可执行，且保持：

- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

未证明 `hil_pass`。未证明真实 WAVE ROVER、真实 UART、真实串口日志、真实 `feedback_T1001.log`、真实 `/odom`、真实 `/imu/data`、真实 `/battery`、真实 route/elevator field pass、真实手机/browser、Objective 5 external proof 或 delivery success。

PR #4 仍缺真实门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record、completion signal、dropoff/cancel completion 和 delivery result。PR #5 仍缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry 材料。
