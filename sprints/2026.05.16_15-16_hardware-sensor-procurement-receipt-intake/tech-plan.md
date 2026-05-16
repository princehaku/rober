# Sprint 2026.05.16_15-16 Hardware Sensor Procurement Receipt Intake - Tech Plan

sprint_type: epic

## 1. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的是 Objective 5，约 66%。
2. 本 sprint 不直接针对 Objective 5。
3. 理由：live `OKR.md` 和最近 sprint final 均说明 Objective 5 下一步必须是真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration。本机只有 Docker，继续新增 O5 local metadata 不能构成可接受证据。本轮选择 Objective 4 的真实传感器材料回填入口，并服务 Objective 1/2/3 后续真实硬件、导航和电梯现场材料闭环。

## 2. 证据依据

- `OKR.md` 4.1：Objective 5 约 66% 最低；Objective 1 约 73%，Objective 2/3 约 78%，Objective 4 约 84%。O5 仍缺外部云/4G/OSS/CDN/DB/queue 材料。
- PR #5 review：
  - P1 `docs/product/production_hardware_boundary.md` 的默认硬件集与 mandatory `monocular + 2D LiDAR + ToF` baseline 曾矛盾，可能误导 BOM、采购和 bringup。
  - P2 mandatory sensor assumptions 必须引用 `docs/vendor/` 来源；不能无来源声明 2D LiDAR / ToF channel、SKU、安装、电源、标定或 HIL。
  - P2 OKR 最低项叙述曾可能误导 sprint routing；本 plan 必须显式记录 O5 最低但外部证据不可本机推进。
- `sprints/2026.05.16_12-13_hardware-sensor-procurement-intake/final.md`：真实 2D LiDAR / ToF SKU、vendor/source、采购、安装、接线、电源和标定仍缺。
- `sprints/2026.05.16_13-14_hardware-sensor-procurement-review-decision/final.md`：review decision 已输出 blockers、next_required_evidence、owner_handoff 和 rerun_commands，但未获得真实材料。
- `sprints/2026.05.16_14-15_hardware-sensor-procurement-execution-pack/final.md`：execution pack 已形成 material templates 和 owner handoff，但仍没有真实 SKU/source/procurement、安装、接线、电源预算、标定、HIL entry。
- `docs/product/production_hardware_boundary.md`：当前已把 2D LiDAR / ToF 保持为 product target material with procurement validation pending；本轮 receipt intake 必须延续该边界。

## 3. 并行 owner 任务

### Task A：Hardware PC Gate

责任 Engineer：Hardware Infra Engineer。

允许改动：

- `pc-tools/evidence/hardware_sensor_procurement_receipt_intake_gate.py`
- `pc-tools/evidence/test_hardware_sensor_procurement_receipt_intake_gate.py`
- `docs/product/production_hardware_boundary.md`

实现要求：

- 先读 `docs/vendor/VENDOR_INDEX.md` 和其指向的本地 vendor 文件，写明 source boundary。
- 读取上轮 `hardware_sensor_procurement_execution_pack` artifact 或 summary；缺失时输出 `blocked_missing_hardware_sensor_procurement_execution_pack`。
- 新增 receipt intake artifact / summary：
  - artifact schema：`trashbot.hardware_sensor_procurement_receipt_intake.v1`
  - summary schema：`trashbot.hardware_sensor_procurement_receipt_intake_summary.v1`
  - evidence boundary：`software_proof_docker_hardware_sensor_procurement_receipt_intake_gate`
- 接收 receipt/source/vendor/SKU/cost/install/wiring/power/calibration/HIL-entry 字段的脱敏摘要或引用，输出 `accepted_materials`、`missing_materials`、`rejected_materials`、`next_required_evidence` 和 `owner_handoff`。
- Fail closed：
  - unsupported execution pack schema/boundary。
  - 缺 receipt/source/vendor/SKU 关键材料。
  - unsafe success/control claim。
  - raw credential、token、OSS AK/SK、DB/queue URL、raw serial/UART path、完整本机路径、checksum 或 raw JSON 泄漏。
  - 把 receipt intake 写成真实采购完成、真实 HIL、delivery success 或 O5 external proof。
- 所有新增代码技术注释必须为中文，且有意义注释比例超过 20%。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/hardware_sensor_procurement_receipt_intake_gate.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_hardware_sensor_procurement_receipt_intake_gate.py
python3 pc-tools/evidence/hardware_sensor_procurement_receipt_intake_gate.py --help
rg -n "hardware_sensor_procurement_receipt_intake|software_proof_docker_hardware_sensor_procurement_receipt_intake_gate|not_proven|delivery_success=false|primary_actions_enabled=false|docs/vendor/VENDOR_INDEX.md" pc-tools/evidence docs/product/production_hardware_boundary.md
git diff --check -- pc-tools/evidence/hardware_sensor_procurement_receipt_intake_gate.py pc-tools/evidence/test_hardware_sensor_procurement_receipt_intake_gate.py docs/product/production_hardware_boundary.md
```

输出要求：

- 实际改动文件列表。
- 已读 vendor 来源。
- 验证命令输出结果。
- 失败定位。
- 剩余风险。

### Task B：Robot Diagnostics Metadata-Only Consumer

责任 Engineer：Robot Platform Engineer。

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

实现要求：

- 增加 receipt intake diagnostics summary 常量、默认 summary、source contract、sanitizer 和 `summarize_hardware_sensor_procurement_receipt_intake`。
- 支持显式 `hardware_sensor_procurement_receipt_intake_ref`、内嵌 `hardware_sensor_procurement_receipt_intake` 和 `hardware_sensor_procurement_receipt_intake_summary`。
- 缺失、unreadable、unsupported schema/boundary、unsafe copy、weak contract 时必须 fail closed，默认 `blocked_missing_hardware_sensor_procurement_receipt_intake`。
- 输出必须保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 不触发 collect/dropoff/cancel、ACK、cursor advance、Nav2、HIL、dropoff/cancel completion 或 delivery result。
- 所有新增代码技术注释必须为中文，且有意义注释比例超过 20%。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "hardware_sensor_procurement_receipt_intake|software_proof_docker_hardware_sensor_procurement_receipt_intake_gate|blocked_missing_hardware_sensor_procurement_receipt_intake|primary_actions_enabled" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

输出要求：

- 实际改动文件列表。
- 验证命令输出结果。
- 失败定位。
- 剩余风险。

### Task C：Full-Stack Mobile Read-Only Panel

责任 Engineer：User Touchpoint Full-Stack Engineer。

允许改动：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/status.json`
- `docs/product/mobile_user_flow.md`

实现要求：

- 在 `hardware_sensor_procurement_execution_pack` 之后新增首屏只读“传感器采购收货回填” panel。
- 消费 `hardware_sensor_procurement_receipt_intake`、`hardware_sensor_procurement_receipt_intake_summary`、`phone_readiness`、`/api/diagnostics` 和 nested diagnostics summary 中的兼容字段。
- 展示 `receipt_intake_status`、`material_status`、missing/accepted/rejected material summary、owner handoff、next required evidence、safe evidence ref、evidence boundary 和 `not_proven`。
- copy/export whitelist-only；不得展示 raw JSON、ROS topic、串口细节、凭证、checksum、完整本机路径、采购成功、HIL 通过、delivery success 或 control grant 文案。
- Start / Confirm Dropoff / Cancel gating 不变，主操作继续 fail closed。
- 所有新增代码技术注释必须为中文，且有意义注释比例超过 20%。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
node --check mobile/web/app.js
rg -n "hardware_sensor_procurement_receipt_intake|传感器采购收货回填|software_proof_docker_hardware_sensor_procurement_receipt_intake_gate|hardware_material_pending|not_proven" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
```

输出要求：

- 用户旅程变化和触点收益。
- 实际改动文件列表。
- 验证命令输出结果。
- 失败定位。
- 剩余风险。

### Task D：Product Closeout

责任 Engineer：Product Manager / OKR Owner。

允许改动：

- `sprints/2026.05.16_15-16_hardware-sensor-procurement-receipt-intake/tech-done.md`
- `sprints/2026.05.16_15-16_hardware-sensor-procurement-receipt-intake/side2side_check.md`
- `sprints/2026.05.16_15-16_hardware-sensor-procurement-receipt-intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

实现要求：

- 汇总 Hardware / Robot / Full-stack worker 的实际改动、验证命令、失败定位和剩余风险。
- 核对所有 closeout 语言保留 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 明确本轮不证明真实采购、真实收货、真实安装、真实接线、真实电源、真实标定、真实 HIL entry、真实 route/elevator field pass、真实手机/browser、dropoff/cancel completion、delivery success 或 Objective 5 external proof。
- `OKR.md` 只允许按 software proof 保守更新；如果没有真实材料，不提升 Objective 1/2/3/5。Objective 4 是否上调必须只基于 receipt intake 对低成本量产边界的增量价值，并写清 remaining evidence。

验收命令：

```bash
rg -n "hardware_sensor_procurement_receipt_intake|software_proof_docker_hardware_sensor_procurement_receipt_intake_gate|Objective 5|Docker|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.16_15-16_hardware-sensor-procurement-receipt-intake OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.16_15-16_hardware-sensor-procurement-receipt-intake OKR.md docs/process/okr_progress_log.md
```

输出要求：

- 实际改动文件列表。
- 验证命令输出结果。
- 失败定位。
- 剩余风险。

## 4. 接口影响

- 新增 metadata-only PC artifact / summary schema：`trashbot.hardware_sensor_procurement_receipt_intake.v1` 与 `trashbot.hardware_sensor_procurement_receipt_intake_summary.v1`。
- Robot diagnostics 新增只读 summary 字段和 alias，不改变现有 status/command/ACK 契约。
- Mobile 新增只读 panel 和 phone-safe copy package，不改变主操作按钮启用条件。
- Product closeout 新增 receipt intake sprint 证据边界，不改变 O5 external proof 定义。

## 5. 风险边界

- 本轮不证明真实 2D LiDAR / ToF、真实 receipt、真实 procurement completion、真实 installation、真实 wiring、真实 power budget、真实 calibration、真实 HIL entry、WAVE ROVER、UART、Nav2/fixed-route、route/elevator field pass、真实手机、dropoff/cancel completion、delivery success 或 Objective 5 external proof。
- 如果 receipt/source/SKU 等真实材料缺失，正确结果是 fail closed / `hardware_material_pending` / `not_proven`，不是验证失败。
- 如果 worker 需要调整 schema 字段，必须保持 PC gate、Robot diagnostics 和 mobile panel 的字段名一致，并在 `docs/interfaces/ros_contracts.md` 与 `docs/product/mobile_user_flow.md` 同步。

## 6. Sprint 文档要求

- Planning 已创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 实现完成后补齐：`tech-done.md`、`side2side_check.md`、`final.md`。
- 所有 closeout 必须回顾 `OKR 最低优先级核对` 是否仍成立，并明确 Objective 5 没有真实外部材料时不应因本轮上调。
