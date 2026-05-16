# Sprint 2026.05.16_15-16 Hardware Sensor Procurement Receipt Intake - Tech Done

sprint_type: epic

## 1. 实际改动

### Task A Hardware PC Gate

- 改动文件：
  - `pc-tools/evidence/hardware_sensor_procurement_receipt_intake_gate.py`
  - `pc-tools/evidence/test_hardware_sensor_procurement_receipt_intake_gate.py`
  - `docs/product/production_hardware_boundary.md`
- 已读 vendor source：
  - `docs/vendor/VENDOR_INDEX.md`
  - `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
  - `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
  - `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
  - `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
  - vendor index 指向的 Orange Pi Zero 3 manual / schematic
- 结果：新增 `trashbot.hardware_sensor_procurement_receipt_intake.v1` 和 `trashbot.hardware_sensor_procurement_receipt_intake_summary.v1`，证据边界为 `software_proof_docker_hardware_sensor_procurement_receipt_intake_gate`。gate 读取 execution pack artifact / summary / wrapper，接收 redacted receipt、source、vendor、SKU、cost、install、wiring、power、calibration、HIL-entry materials，输出 accepted / missing / rejected materials、next_required_evidence 和 owner_handoff。
- Fail-closed 覆盖：unsupported schema/boundary、缺关键材料、success/control/HIL/O5 claims、credentials/token/OSS/DB/queue URL、serial/UART path、完整本机路径、checksum、raw JSON、完整 artifact copy。
- 边界：vendor docs 不证明 2D LiDAR / ToF SKU、真实 receipt、真实 procurement、真实 installation、真实 wiring、真实 power、真实 calibration、真实 HIL entry、Objective 5 external proof 或 delivery success。

### Task B Robot Diagnostics

- 改动文件：
  - `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - `docs/interfaces/ros_contracts.md`
- 结果：新增 receipt intake schema / gate constants、默认 fail-closed summary、source contract、not_proven list、sanitizer / summary function，以及 explicit ref / env / inline latest_status / diagnostics / alias consumption。
- 边界：metadata-only；固定 `delivery_success=false`、`primary_actions_enabled=false`；不触发 collect / dropoff / cancel、ACK、cursor、Nav2 或 HIL。

### Task C Full-Stack Mobile

- 改动文件：
  - `mobile/web/app.js`
  - `mobile/web/styles.css`
  - `mobile/web/test_mobile_web_entrypoint.py`
  - `mobile/web/fixtures/status.json`
  - `docs/product/mobile_user_flow.md`
- 结果：在 execution pack 之后新增只读“传感器采购收货回填”首屏 panel，展示 receipt_intake_status、material_status、missing / accepted / rejected materials、owner handoff、next required evidence、safe evidence ref、boundary 和 not_proven。
- 边界：copy / export whitelist-only；Start / Confirm Dropoff / Cancel gating 不变。本轮 fixture / software proof 只等待真实 Hardware / Robot summary materials，不是真实 ROS2、真实硬件、真实 receipt、HIL、dropoff / cancel completion 或 delivery success。

### Task D Product Closeout

- 改动文件：
  - `sprints/2026.05.16_15-16_hardware-sensor-procurement-receipt-intake/tech-done.md`
  - `sprints/2026.05.16_15-16_hardware-sensor-procurement-receipt-intake/side2side_check.md`
  - `sprints/2026.05.16_15-16_hardware-sensor-procurement-receipt-intake/final.md`
  - `OKR.md`
  - `docs/process/okr_progress_log.md`
- 结果：汇总 Task A / B / C worker 证据，更新 sprint closeout、OKR 4.1 快照和 OKR 进度日志。Objective 4 因 receipt intake 对低成本量产硬件材料链的增量软件证明，从约 84% 保守上调到约 85%；Objective 1 / 2 / 3 / 5 不上调。

## 2. 验证结果

Task A worker 验证：

```text
py_compile passed
unittest: Ran 9 tests ... OK
CLI --help passed
required rg passed
scoped git diff --check passed
```

Task B worker 验证：

```text
py_compile passed
diagnostics unittest: Ran 102 tests in 0.094s OK
required rg passed
scoped git diff --check passed
```

Task C worker 验证：

```text
mobile unittest: Ran 4 tests ... OK
node --check passed
required rg passed
scoped git diff --check passed
```

Task D closeout 验收：

```text
rg -n "hardware_sensor_procurement_receipt_intake|software_proof_docker_hardware_sensor_procurement_receipt_intake_gate|Objective 5|Docker|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.16_15-16_hardware-sensor-procurement-receipt-intake OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.16_15-16_hardware-sensor-procurement-receipt-intake OKR.md docs/process/okr_progress_log.md
```

Task D 命令结果见本轮最终回复；当前 closeout 文档预期必须命中 receipt intake schema、software proof boundary、Objective 5 stop rule、Docker、not_proven、`delivery_success=false` 和 `primary_actions_enabled=false`。

## 3. 偏差与失败定位

- 未发现 worker 报告的验证失败。
- Product closeout 没有重新运行 Task A / B / C 的 owner 级测试；按本轮 AGENTS 主节点 / Product closeout 分工，只汇总 worker 验证并运行 Task D 指定的 sprint / OKR 文档围栏。
- 本轮 closeout 只接收 worker 证据，不回滚、覆盖或格式化其他 worker 的代码改动。

## 4. 剩余风险

- 本轮不证明真实采购、真实收货、真实安装、真实接线、真实电源、真实标定、真实 HIL entry、真实 route/elevator field pass、真实手机/browser、dropoff/cancel completion、delivery success 或 Objective 5 external proof。
- 仍缺真实 2D LiDAR / ToF SKU、receipt、vendor/source document、cost、installation、wiring、power budget、calibration result 和 HIL-entry materials。
- 仍缺真实 WAVE ROVER、UART、Orange Pi 串口、`T=1001` feedback、Nav2/fixed-route runtime、真实电梯现场材料、真实 dropoff/cancel completion 和真实 delivery result。
- Objective 5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration；本轮 Docker / software proof 不改变 O5 stop rule。
