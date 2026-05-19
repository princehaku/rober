# Sprint 2026.05.19_10-11 Hardware Real Material Escalation Request - Tech Plan

## 1. 目标

实现 `hardware_real_material_escalation_request` software-proof chain：

- Hardware PC gate 生成真实硬件材料升级请求。
- Robot diagnostics safe alias 只读暴露 summary。
- mobile/web read-only panel 展示材料缺口和 owner handoff。
- Product closeout 更新 sprint、OKR 和 progress log。

证据边界必须保持：`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

本轮不是 HIL，不证明真实 WAVE ROVER/UART，不证明真实 2D LiDAR / ToF，不证明 PR #4 route/elevator field pass，不提高 Objective 5。

## 2. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5，约 68%。
2. 本 sprint 不针对 Objective 5 completion。
3. 具体理由：Objective 5 下一步需要真实 external proof，包括公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser 证据；当前本机没有真实硬件，只有 Docker，也没有这些外部材料。继续做本地 O5 metadata depth 不能提高真实 O5 进度。
4. 下一低项是 Objective 1，约 81%。PR #5 review closeout 已显示 mandatory sensor assumptions 仍 `blocked_pending_real_materials`，且 live OKR 明确 WAVE ROVER/UART/HIL 与 2D LiDAR / ToF 材料仍缺。本轮选择 Objective 1 / Objective 4 的 `hardware_real_material_escalation_request`，把真实材料缺口转成可执行升级请求。
5. PR #4 route/elevator material blocker 最近两轮 `08-09`、`09-10` 已连续消费，本轮不做第三个同类 wrapper。

## 3. 角色分工和文件范围

### hardware-engineer

允许改动：

- `pc-tools/evidence/hardware_real_material_escalation_request.py`
- `tests/test_hardware_real_material_escalation_request.py`
- `docs/interfaces/hardware_real_material_escalation_request.md`
- `docs/product/production_hardware_boundary.md`
- 当前 sprint `tech-done.md` 中 Hardware 段落

要求：

- 开工前读取 `docs/vendor/VENDOR_INDEX.md`，并在 docs / gate copy 中明确 vendor/source 边界。
- 输出 schema 建议：
  - `trashbot.hardware_real_material_escalation_request.v1`
  - `trashbot.hardware_real_material_escalation_request_summary.v1`
- 必须覆盖 WAVE ROVER/UART/HIL 和 PR #5 2D LiDAR / ToF 材料缺口。
- 必须 fail closed：缺 source、缺 SKU、缺 receipt/procurement、缺 installation/wiring/power/calibration/HIL-entry、unsafe copy、HIL success claim、field pass claim、delivery success claim、O5 external proof claim。

验收命令：

```bash
test -f docs/vendor/VENDOR_INDEX.md
python3 -m py_compile pc-tools/evidence/hardware_real_material_escalation_request.py
python3 -m unittest tests/test_hardware_real_material_escalation_request.py
rg -n "hardware_real_material_escalation_request|PR #5|2D LiDAR|ToF|WAVE ROVER|UART|HIL|docs/vendor/VENDOR_INDEX.md|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence tests docs/interfaces docs/product/production_hardware_boundary.md sprints/2026.05.19_10-11_hardware-real-material-escalation-request
git diff --check -- pc-tools/evidence tests docs/interfaces docs/product/production_hardware_boundary.md sprints/2026.05.19_10-11_hardware-real-material-escalation-request
```

### robot-software-engineer

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_diagnostics.md`
- 当前 sprint `tech-done.md` 中 Robot 段落

要求：

- 新增 `robot_diagnostics_hardware_real_material_escalation_request_summary` safe alias。
- 只接受 summary-only fields；不得读取 raw artifact、串口、硬件设备或 ROS graph。
- 缺 summary、unsupported schema、unsafe fields、success wording 时 fail closed 到 `not_proven`。
- 不改变 Start Delivery、Confirm Dropoff、Cancel 或任何 motion authorization。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_hardware_real_material_escalation_request_summary|hardware_real_material_escalation_request|PR #5|WAVE ROVER|UART|HIL|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces sprints/2026.05.19_10-11_hardware-real-material-escalation-request
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces sprints/2026.05.19_10-11_hardware-real-material-escalation-request
```

### full-stack-software-engineer

允许改动：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/fixtures/status.json`
- `docs/product/mobile_user_flow.md`
- 当前 sprint `tech-done.md` 中 Full-Stack 段落

要求：

- 新增只读 “硬件真实材料升级请求” panel。
- 消费 `robot_diagnostics_hardware_real_material_escalation_request_summary` 优先；缺失时可消费 safe `hardware_real_material_escalation_request_summary`。
- 展示 safe status、safe evidence ref、missing hardware materials、next required evidence、owner handoff、evidence boundary、`not_proven`。
- 不触发 ACK、cursor、diagnostics fetch、Start Delivery、Confirm Dropoff、Cancel 或 robot command。
- 不展示 raw JSON、ROS topic、`/cmd_vel`、serial/UART path、baudrate、credential、local path、complete artifact、checksum、HIL/pass wording、delivery success wording。

验收命令：

```bash
python3 mobile/web/test_mobile_web_entrypoint.py
python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "hardware_real_material_escalation_request|robot_diagnostics_hardware_real_material_escalation_request_summary|PR #5|2D LiDAR|ToF|WAVE ROVER|UART|HIL|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|Start Delivery|Confirm Dropoff|Cancel" mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.19_10-11_hardware-real-material-escalation-request
git diff --check -- mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.19_10-11_hardware-real-material-escalation-request
```

### product-okr-owner

允许改动：

- `sprints/2026.05.19_10-11_hardware-real-material-escalation-request/tech-done.md`
- `sprints/2026.05.19_10-11_hardware-real-material-escalation-request/side2side_check.md`
- `sprints/2026.05.19_10-11_hardware-real-material-escalation-request/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

要求：

- 核对 worker 输出和验证日志。
- 收口 Objective 5 不提高，Objective 1 只记录 material escalation request 可执行性，Objective 4 只记录 phone-safe read-only visibility。
- 明确剩余风险：无真实 WAVE ROVER/UART/HIL、无真实 2D LiDAR / ToF、无真实手机、无 PR #4 route/elevator field pass、无 O5 external proof。

验收命令：

```bash
test -f sprints/2026.05.19_10-11_hardware-real-material-escalation-request/tech-done.md && test -f sprints/2026.05.19_10-11_hardware-real-material-escalation-request/side2side_check.md && test -f sprints/2026.05.19_10-11_hardware-real-material-escalation-request/final.md
rg -n "Objective 5|Objective 1|PR #5|PR #4|hardware_real_material_escalation_request|robot_diagnostics_hardware_real_material_escalation_request_summary|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.19_10-11_hardware-real-material-escalation-request
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.19_10-11_hardware-real-material-escalation-request
```

## 4. 并行启动策略

本 sprint 是 Epic，跨 Hardware、Robot、Full-Stack、Product 四个 owner。实现阶段必须并行启动 3 个 IC worker：

- `hardware-engineer`
- `robot-software-engineer`
- `full-stack-software-engineer`

Product closeout 在三个 IC worker 返回后执行。Autonomy 本轮不写文件，只作为 PR #4 route/elevator 缺口的后续 owner 保留。

## 5. 接口边界

- Hardware summary 是唯一上游事实源；Robot 和 mobile/web 只能消费 sanitized summary。
- Robot diagnostics 不得扩大为硬件执行层，不得读取真实 serial/UART，不得声明 HIL。
- mobile/web 不得把 panel 变成控制面，不得改变主按钮启用条件。
- Product closeout 不得上调 O5，也不得把 `software_proof` 写成真实硬件完成。

## 6. 风险和阻塞

- Docker-only 主机无法采集真实 `/dev/tty*`、WAVE ROVER feedback、2D LiDAR / ToF sensor sample、真实手机或 O5 external proof。
- `docs/vendor/VENDOR_INDEX.md` 当前不证明项目已采购或安装 2D LiDAR / ToF；任何传感器 baseline 必须继续标为真实材料待补。
- PR #4 route/elevator field materials 仍是独立缺口；本轮不解决真实电梯、真实 Nav2/fixed-route、真实 dropoff/cancel completion 或 delivery success。
- 若实现中发现 raw material 或 unsafe copy，只能 fail closed，不能用占位材料通过。

## 7. 本 Product planning 验收命令

Product Owner 启动文档完成后必须运行：

```bash
test -f sprints/2026.05.19_10-11_hardware-real-material-escalation-request/pre_start.md && test -f sprints/2026.05.19_10-11_hardware-real-material-escalation-request/prd.md && test -f sprints/2026.05.19_10-11_hardware-real-material-escalation-request/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|Objective 1|PR #5|PR #4|hardware_real_material_escalation_request|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|hardware-engineer|robot-software-engineer|full-stack-software-engineer" sprints/2026.05.19_10-11_hardware-real-material-escalation-request
git diff --check -- sprints/2026.05.19_10-11_hardware-real-material-escalation-request
```
