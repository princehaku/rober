# Sprint 2026.05.17_03-04 Hardware Sensor HIL-entry Execution Pack - Tech Plan

sprint_type: epic

## 1. 技术方案

本轮新增 `hardware_sensor_hil_entry_execution_pack` contract。它消费上一轮 `hardware_sensor_hil_entry_readiness_review` artifact/summary，把 HIL-entry readiness review 转成下一次真实 HIL-entry 的执行包、Robot diagnostics metadata-only summary 和 mobile/web 只读 panel。

输出 contract：

- artifact schema：`trashbot.hardware_sensor_hil_entry_execution_pack.v1`
- summary schema：`trashbot.hardware_sensor_hil_entry_execution_pack_summary.v1`
- boundary：`software_proof_docker_hardware_sensor_hil_entry_execution_pack_gate`
- fixed safety fields：`source=software_proof`、`hardware_material_status=hardware_material_pending`、`evidence_status=not_proven`、`delivery_success=false`、`primary_actions_enabled=false`

该 contract 不改变 robot control API，不改变 Start Delivery / Confirm Dropoff / Cancel gating，不产生 ACK、cursor、Nav2、HIL、route/elevator pass 或 delivery success。

## 2. 分工和文件范围

### Task A - Hardware Infra Engineer

允许改动：

- `pc-tools/evidence/hardware_sensor_hil_entry_execution_pack_gate.py`
- `pc-tools/evidence/test_hardware_sensor_hil_entry_execution_pack_gate.py`
- `pc-tools/README.md`
- `docs/product/production_hardware_boundary.md`

要求：

- 先读 `docs/vendor/VENDOR_INDEX.md`，并在输出中列出采用的 vendor/source boundary。
- Gate 接收 `--readiness-review-json`、`--output`、`--summary-output`、`--once-json`。
- 输出 controlled HIL-entry manifest、material templates、first-run command summary、rerun command summary、owner handoff、next required evidence。
- 支持读取 readiness review artifact 或 summary，但必须拒绝 unsupported schema、weak boundary、success/control claims、缺 SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry template、缺 owner handoff 或 unsafe raw fields。
- vendor/source boundary 只作为资料覆盖，不得写成真实采购、安装、接线、标定或 HIL proof。

验收命令：

```bash
python3 -m py_compile pc-tools/evidence/hardware_sensor_hil_entry_execution_pack_gate.py
python3 -m unittest pc-tools/evidence/test_hardware_sensor_hil_entry_execution_pack_gate.py
python3 pc-tools/evidence/hardware_sensor_hil_entry_execution_pack_gate.py --help
rg -n "hardware_sensor_hil_entry_execution_pack|software_proof_docker_hardware_sensor_hil_entry_execution_pack_gate|docs/vendor/VENDOR_INDEX.md|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence pc-tools/README.md docs/product/production_hardware_boundary.md
git diff --check -- pc-tools/evidence/hardware_sensor_hil_entry_execution_pack_gate.py pc-tools/evidence/test_hardware_sensor_hil_entry_execution_pack_gate.py pc-tools/README.md docs/product/production_hardware_boundary.md
```

### Task B - Robot Platform Engineer

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

要求：

- 新增 metadata-only diagnostics consumer：`hardware_sensor_hil_entry_execution_pack` / `_summary`。
- 支持 explicit ref、env、latest_status、diagnostics nested summary。
- 缺 summary、unsupported schema、weak boundary、success claim、unsafe raw fields 时 fail closed。
- 不改变 collect/dropoff/cancel/ACK/cursor/primary action，不触发 Nav2、HIL、route/elevator pass 或 delivery success。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "hardware_sensor_hil_entry_execution_pack|software_proof_docker_hardware_sensor_hil_entry_execution_pack_gate|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

### Task C - User Touchpoint Full-Stack Engineer

允许改动：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/fixtures/status.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

要求：

- 新增只读“传感器 HIL 执行包” panel。
- 从 status、phone_readiness、diagnostics、diagnostics.summary、diagnostics.diagnostics_summary、nested summaries 中消费 execution pack artifact 或 summary。
- UI 只展示 phone-safe 字段：schema/status、safe `evidence_ref`、manifest summary、material templates、safe command summary、owner handoff、next required evidence、boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 不展示 raw vendor docs、raw JSON、serial/UART、baudrate、WAVE ROVER 参数、绝对路径、credentials、DB/queue URL、OSS AK/SK、checksums、complete artifacts、raw robot responses。
- Start Delivery / Confirm Dropoff / Cancel gating 不变。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
node --check mobile/web/app.js
rg -n "hardware_sensor_hil_entry_execution_pack|software_proof_docker_hardware_sensor_hil_entry_execution_pack_gate|传感器 HIL 执行包|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/fixtures/status.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

## 3. 接口影响

- 新增 PC artifact/summary schema，不改变现有 readiness review schema。
- Robot diagnostics 新增只读 summary 字段，不改变任务控制 API。
- Mobile/web 新增只读 panel，不改变主操作 gating。
- `docs/vendor/VENDOR_INDEX.md` 仍是硬件资料入口；本轮不会新增真实引脚、电压、UART 设备、波特率、JSON 指令或机械尺寸假设。

## 4. OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 66%。
- 本 sprint 是否针对该 Objective：否。
- 理由：Objective 5 当前需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 等外部材料；本机只有 Docker-only 环境，继续本地 O5 wrapper 会重复消费同一外部证据 blocker。按 stop rule 转向最低可行动作 Objective 1，并同步 Objective 4 的手机安全解释面。
- final.md 收口时需复核：O5 外部材料是否仍不可用；本轮是否保持 `software_proof_docker_hardware_sensor_hil_entry_execution_pack_gate`、`hardware_material_pending`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 5. 验收边界

通过本 sprint 只能说明 HIL-entry execution pack contract、diagnostics consumer 和 mobile panel 在 Docker/local software proof 下工作。

不得写成：

- 真实 2D LiDAR / ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry 已完成。
- 真实 WAVE ROVER、Orange Pi UART JSON feedback、`T=1001`、`/odom`、`/imu/data`、`/battery` 或 `hil_pass` 已完成。
- 真实 Nav2/fixed-route、route/elevator field pass、dropoff/cancel completion 或 delivery success 已完成。
- 真实手机/browser、production app、PWA prompt/user choice 已完成。
- Objective 5 external proof 已完成。

## 6. Planning 验收命令

```bash
rg -n "sprint_type: epic|hardware_sensor_hil_entry_execution_pack|software_proof_docker_hardware_sensor_hil_entry_execution_pack_gate|OKR 最低优先级核对|Objective 5|Objective 1|PR #5|Docker-only|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.17_03-04_hardware-sensor-hil-entry-execution-pack
git diff --check -- sprints/2026.05.17_03-04_hardware-sensor-hil-entry-execution-pack/pre_start.md sprints/2026.05.17_03-04_hardware-sensor-hil-entry-execution-pack/prd.md sprints/2026.05.17_03-04_hardware-sensor-hil-entry-execution-pack/tech-plan.md
```
