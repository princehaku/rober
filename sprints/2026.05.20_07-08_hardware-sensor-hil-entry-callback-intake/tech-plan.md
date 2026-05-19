# Sprint 2026.05.20_07-08 Hardware Sensor HIL-entry Callback Intake - Tech Plan

sprint_type: epic

## 1. 技术方案

本轮 planning 定义下一步实现的 `hardware_sensor_hil_entry_callback_intake` contract。它位于既有 `hardware_sensor_hil_entry_execution_pack` 之后，消费执行包和未来现场 callback material，产出 PC artifact / summary、Robot diagnostics safe alias 和 mobile/web 只读 panel。

目标 contract：

- artifact schema：`trashbot.hardware_sensor_hil_entry_callback_intake.v1`
- summary schema：`trashbot.hardware_sensor_hil_entry_callback_intake_summary.v1`
- boundary：`software_proof_docker_hardware_sensor_hil_entry_callback_intake_gate`
- fixed safety fields：`source=software_proof`、`hardware_material_status=hardware_material_pending`、`evidence_status=not_proven`、`delivery_success=false`、`primary_actions_enabled=false`

该 contract 只承接材料回填状态，不改变 robot control API，不改变 Start Delivery / Confirm Dropoff / Cancel gating，不产生 ACK、cursor、Nav2、HIL、route/elevator pass、Objective 5 external proof 或 delivery success。

## 2. 文件结构和接口影响

### 新增或修改文件边界

implementation worker 已按以下范围落地；Product closeout 不扩大文件范围。

- Hardware PC gate：
  - `pc-tools/evidence/hardware_sensor_hil_entry_callback_intake_gate.py`
  - `pc-tools/evidence/test_hardware_sensor_hil_entry_callback_intake_gate.py`
  - `pc-tools/README.md`
  - `docs/product/production_hardware_boundary.md`
- Robot diagnostics safe alias：
  - `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - `docs/interfaces/ros_contracts.md`
- Full-Stack mobile/web panel：
  - `mobile/web/app.js`
  - `mobile/web/styles.css`
  - `mobile/web/fixtures/status.json`
  - `mobile/web/test_mobile_web_entrypoint.py`
  - `docs/product/mobile_user_flow.md`

接口影响：

- 新增 PC artifact/summary schema，不改变 existing execution pack schema。
- Robot diagnostics 新增 metadata-only summary 字段，不改变 task control API。
- Mobile/web 新增只读 panel，不改变主操作 gating。
- `docs/vendor/VENDOR_INDEX.md` 仍是硬件事实入口；后续 worker 必须明确引用本地 vendor/source boundary，不能新增未证实的引脚、电压、UART 设备、波特率、JSON 指令或机械尺寸假设。

## 3. 并行 Worker 任务

### Task A - Hardware PC Gate

责任 Engineer：Hardware Infra Engineer

允许改动：

- `pc-tools/evidence/hardware_sensor_hil_entry_callback_intake_gate.py`
- `pc-tools/evidence/test_hardware_sensor_hil_entry_callback_intake_gate.py`
- `pc-tools/README.md`
- `docs/product/production_hardware_boundary.md`

要求：

- 先读 `docs/vendor/VENDOR_INDEX.md`，并在代码注释、README 或 docs 中列出采用的 vendor/source boundary。
- Gate 接收 `--execution-pack-json`、`--callback-json`、`--output`、`--summary-output`、`--once-json`。
- 支持 execution pack artifact、summary 或 nested wrapper summary。
- Callback material 只允许 sanitized references / summaries：2D LiDAR SKU/source/receipt、ToF SKU/source/receipt、mounting、wiring、power、calibration、HIL-entry operator result。
- 输出 accepted callback materials、missing required materials、rejected callback materials、operator result summary、owner handoff、next required evidence、rerun commands、safe copy。
- 必须拒绝 unsupported schema、weak boundary、evidence-ref mismatch、raw credentials、raw serial/UART、完整本地路径、complete artifacts、checksums、HIL pass / field pass / delivery success copy、`delivery_success=true`、`primary_actions_enabled=true`。
- 输出必须保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

验收命令：

```bash
python3 -m py_compile pc-tools/evidence/hardware_sensor_hil_entry_callback_intake_gate.py
python3 -m unittest pc-tools/evidence/test_hardware_sensor_hil_entry_callback_intake_gate.py
python3 pc-tools/evidence/hardware_sensor_hil_entry_callback_intake_gate.py --help
rg -n "hardware_sensor_hil_entry_callback_intake|software_proof_docker_hardware_sensor_hil_entry_callback_intake_gate|docs/vendor/VENDOR_INDEX.md|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence pc-tools/README.md docs/product/production_hardware_boundary.md
git diff --check -- pc-tools/evidence/hardware_sensor_hil_entry_callback_intake_gate.py pc-tools/evidence/test_hardware_sensor_hil_entry_callback_intake_gate.py pc-tools/README.md docs/product/production_hardware_boundary.md
```

### Task B - Robot Diagnostics Safe Alias

责任 Engineer：Robot Platform Engineer

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

要求：

- 新增 metadata-only diagnostics consumer：`hardware_sensor_hil_entry_callback_intake` / `_summary`。
- 支持 explicit ref、env、latest_status、diagnostics nested summary。
- 只消费 sanitized summary，不读取 raw callback material、raw execution pack、serial/UART、ROS graph、local files 或 credentials。
- 缺 summary、unsupported schema、weak boundary、success claim、unsafe raw fields 时 fail closed。
- 不改变 collect/dropoff/cancel/ACK/cursor/primary action，不触发 Nav2、HIL、route/elevator pass、Objective 5 external proof 或 delivery success。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "hardware_sensor_hil_entry_callback_intake|software_proof_docker_hardware_sensor_hil_entry_callback_intake_gate|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

### Task C - Full-Stack Mobile/Web Panel

责任 Engineer：User Touchpoint Full-Stack Engineer

允许改动：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/fixtures/status.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

要求：

- 新增只读 “传感器 HIL 回调入口” panel，位置建议紧跟 “传感器 HIL 准入执行包” panel。
- 从 `/api/status`、`phone_readiness`、`/api/diagnostics`、`diagnostics.summary`、`diagnostics.diagnostics_summary`、nested summaries 或 status diagnostics summary 中消费 callback intake artifact / summary。
- UI 只展示 phone-safe 字段：schema/status、safe `evidence_ref`、source execution pack status、accepted/missing/rejected materials、operator result summary、owner handoff、next required evidence、boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 不展示 raw vendor docs、raw JSON、serial/UART、baudrate、WAVE ROVER 参数、绝对路径、credentials、DB/queue URL、OSS AK/SK、checksums、complete artifacts、raw robot responses、HIL/pass wording 或 delivery success copy。
- 不新增 diagnostics fetch、ACK、cursor、Start Delivery、Confirm Dropoff、Cancel 或 robot command endpoint。
- Start Delivery / Confirm Dropoff / Cancel gating 不变。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
node --check mobile/web/app.js
rg -n "hardware_sensor_hil_entry_callback_intake|software_proof_docker_hardware_sensor_hil_entry_callback_intake_gate|传感器 HIL 回调入口|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/fixtures/status.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

## 4. OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 68%。
- 本 sprint 是否针对该最低 Objective：否。
- 不针对原因：Objective 5 当前真正缺口是真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover 和真实手机/browser 材料。最近 `cloud_command_idempotency_visibility_guard` 已证明本地 duplicate command fail-closed 可见性，但仍不是 external proof。继续做同一 O5 本地 wrapper 会重复消费外部材料 blocker。
- 本 sprint 转向的 Objective：Objective 1，约 81%。PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / material pending；已有 GitHub reply 只是 `software_proof` / `not_proven` / `hardware_material_pending`，不能 resolve thread。`hardware_sensor_hil_entry_execution_pack` 已有执行包，本轮规划它之后的 callback intake，作为真实 2D LiDAR / ToF SKU/source/receipt、mounting/wiring/power、calibration 和 HIL-entry operator result 的未来回填入口。
- 收口复核要求：final.md 必须确认本轮仍没有把 callback intake 写成真实 HIL、真实 procurement、真实 phone/browser、Objective 5 external proof、route/elevator field pass 或 delivery success。

## 5. 验收边界

通过本轮 implementation 只能说明 callback intake contract、diagnostics consumer 和 mobile panel 在 Docker/local software proof 下工作。

不得写成：

- 真实 2D LiDAR / ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry 已完成。
- 真实 WAVE ROVER、Orange Pi UART JSON feedback、`T=1001`、`/odom`、`/imu/data`、`/battery` 或 `hil_pass` 已完成。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` 已 resolved。
- 真实 Nav2/fixed-route、route/elevator field pass、dropoff/cancel completion 或 delivery success 已完成。
- 真实手机/browser、production app、PWA prompt/user choice 已完成。
- Objective 5 external proof 已完成。

## 6. 本轮 Planning 验收命令

```bash
test -f sprints/2026.05.20_07-08_hardware-sensor-hil-entry-callback-intake/pre_start.md && test -f sprints/2026.05.20_07-08_hardware-sensor-hil-entry-callback-intake/prd.md && test -f sprints/2026.05.20_07-08_hardware-sensor-hil-entry-callback-intake/tech-plan.md
rg -n "sprint_type: epic|hardware_sensor_hil_entry_callback_intake|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|OKR 最低优先级核对|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.20_07-08_hardware-sensor-hil-entry-callback-intake
git diff --check -- sprints/2026.05.20_07-08_hardware-sensor-hil-entry-callback-intake
```
