# Sprint 2026.05.16_13-14 Hardware Sensor Procurement Review Decision - Tech Plan

## 1. 目标

实现 `hardware_sensor_procurement_review_decision` fail-closed gate，把上一轮 `hardware_sensor_procurement_intake` artifact / summary 中的真实 2D LiDAR / ToF 材料缺口，转成可执行采购评审决策、blocker、next_required_evidence、owner_handoff 和 rerun_commands，并让 Robot diagnostics / mobile 只读消费 sanitized summary。

本计划阶段只创建 sprint 三份文档：`pre_start.md`、`prd.md`、`tech-plan.md`。不修改产品代码、测试代码、硬件配置、`OKR.md` 或 closeout docs。

证据边界：本计划和后续本地实现最多是 `software_proof_docker_hardware_sensor_procurement_review_decision_gate`。它不是真实 2D LiDAR / ToF procurement proof，不是 HIL，不是 route/elevator field pass，不是 delivery success，也不是 Objective 5 / O5 external proof。

## 2. OKR 最低优先级核对

当前 live `OKR.md` 4.1 table：

- Objective 5：约 66%，当前数值最低。
- Objective 1：约 73%。
- Objective 2：约 78%。
- Objective 3：约 78%。
- Objective 4：约 82%。

本 sprint 不直接主攻最低 Objective 5。理由：

- Objective 5 的剩余关键缺口是真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。
- 当前开发主机只有 Docker，不能产生真实外部 O5 材料。
- 近期 sprint 已多次证明：继续叠加本地 O5 metadata 不能提高真实 O5 完成度，会重复消费同一外部证据 blocker。

本 sprint 改攻 Objective 4 / Objective 1 支撑链路：真实 sensor procurement material review decision。依据 live `OKR.md` 6，本轮最高可行动作之一是补真实 2D LiDAR / ToF SKU/vendor/procurement/installation/HIL-entry 材料；12-13 sprint final 也明确下一步应收集真实材料并重跑 intake gate。本轮先把 intake artifact/summary 推进为可执行 review decision，为真实采购材料回填建立闭环。

## 3. 接口和 schema 设计

新增或延展实现建议：

- PC gate / artifact：`hardware_sensor_procurement_review_decision`
- Artifact schema：`trashbot.hardware_sensor_procurement_review_decision.v1`
- Summary schema：`trashbot.hardware_sensor_procurement_review_decision_summary.v1`
- Evidence boundary：`software_proof_docker_hardware_sensor_procurement_review_decision_gate`
- Missing summary blocked reason：`blocked_missing_hardware_sensor_procurement_review_decision`
- Material state：`hardware_material_pending`

最小字段：

```text
schema
schema_version
evidence_ref
source_intake_schema
source_intake_status
review_decision
blockers
next_required_evidence
owner_handoff
rerun_commands
hardware_material_pending
delivery_success=false
primary_actions_enabled=false
not_proven
evidence_boundary
```

允许的 review decision 初始枚举：

- `blocked_missing_hardware_sensor_procurement_intake`
- `blocked_unsupported_hardware_sensor_procurement_intake`
- `blocked_missing_procurement_materials`
- `blocked_missing_mounting_wiring_calibration`
- `ready_for_procurement_review_not_proven`

## 4. Team 并行执行计划

### Task A - Hardware Review Decision Gate

Owner：`hardware-engineer`

文件范围：

- `pc-tools/evidence/hardware_sensor_procurement_review_decision_gate.py`
- `pc-tools/evidence/test_hardware_sensor_procurement_review_decision_gate.py`
- `docs/product/production_hardware_boundary.md`
- 必要时只改 `pc-tools/README.md` 中该 gate 的入口说明

不得改动：

- Robot diagnostics / mobile/web / `OKR.md` / sprint closeout docs。

目标：

- 新增 `hardware_sensor_procurement_review_decision` artifact/gate。
- 读取 `hardware_sensor_procurement_intake` artifact / summary，输出 procurement review decision。
- 对缺 SKU、缺 source、缺采购、缺 mounting/wiring/power/calibration/HIL entry 的 intake 生成 blocker、next_required_evidence、owner_handoff、rerun_commands。
- 明确 `docs/vendor/VENDOR_INDEX.md` 仅证明当前 vendor coverage，不证明 2D LiDAR / ToF source/procurement。

实现要求：

- 任何 placeholder、空 source、缺 SKU、缺采购状态、缺机械/接线/标定/HIL entry 资料都必须 blocked。
- 输出 summary 必须固定 `hardware_material_pending`、`not_proven`、`software_proof`、`delivery_success=false`、`primary_actions_enabled=false`，直到真实材料补齐。
- 代码中的技术注释必须为中文，且注释密度满足 repo 约束。

验收命令：

```bash
python3 -m py_compile pc-tools/evidence/hardware_sensor_procurement_review_decision_gate.py pc-tools/evidence/test_hardware_sensor_procurement_review_decision_gate.py
python3 pc-tools/evidence/test_hardware_sensor_procurement_review_decision_gate.py
python3 pc-tools/evidence/hardware_sensor_procurement_review_decision_gate.py --help
rg -n "hardware_sensor_procurement_review_decision|hardware_sensor_procurement_intake|2D LiDAR|ToF|docs/vendor/VENDOR_INDEX.md|hardware_material_pending|not_proven|software_proof|delivery_success=false|primary_actions_enabled=false|next_required_evidence|owner_handoff|rerun_commands" pc-tools docs/product
git diff --check -- pc-tools/evidence pc-tools/README.md docs/product/production_hardware_boundary.md
```

### Task B - Robot Diagnostics Metadata-Only Consumer

Owner：`robot-software-engineer`

文件范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

不得改动：

- PC gate / mobile/web / `OKR.md` / sprint closeout docs。

目标：

- 让 Robot diagnostics 只读消费 `hardware_sensor_procurement_review_decision` summary。
- 保持 metadata-only：不触发 collect/dropoff/cancel、ACK、cursor、Nav2、HIL、dropoff/cancel completion 或 delivery result。
- 兼容 PC gate summary schema，缺失或 unsupported schema 时 fail closed。

实现要求：

- 不透传 raw artifact、raw ROS topic、raw JSON、serial/UART、baudrate、hardware path、credential、checksum、完整 vendor/source document 或 Objective 5 external material。
- 测试要证明 metadata-only response 不触发控制路径。
- 代码技术注释必须使用中文并满足 20% 以上注释比例。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics
rg -n "hardware_sensor_procurement_review_decision|hardware_sensor_procurement_intake|hardware_material_pending|not_proven|software_proof|delivery_success=false|primary_actions_enabled=false|next_required_evidence|owner_handoff|rerun_commands|metadata-only" onboard/src/ros2_trashbot_behavior docs/interfaces
rg -n "ACK|/cmd_vel|serial|baudrate|delivery_success=true|primary_actions_enabled=true|HIL pass|field pass" onboard/src/ros2_trashbot_behavior docs/interfaces || true
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
```

### Task C - Mobile Phone-Safe Review Decision Panel

Owner：`full-stack-software-engineer`

文件范围：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/fixtures/*`
- `docs/product/mobile_user_flow.md`

不得改动：

- PC gate / Robot diagnostics / `OKR.md` / sprint closeout docs。

目标：

- 在 mobile/web 中只读展示 `hardware_sensor_procurement_review_decision` 或 compatible summary。
- 展示 review decision、missing blocker 分类、next_required_evidence、owner_handoff、safe rerun command summary、safe `evidence_ref`。
- 保持 Start / Confirm Dropoff / Cancel fail closed，不增加控制路径。

实现要求：

- copy/export whitelist-only。
- 不出现 raw ROS topic、`/cmd_vel`、raw JSON、serial/UART、baudrate、WAVE ROVER 参数、credential、DB/queue URL、OSS AK/SK、checksum、complete artifact、raw vendor document。
- 中文优先，避免“已通过”“可发车”“已采购”“已 HIL”“已送达”一类成功文案。
- 代码技术注释必须使用中文并满足 20% 以上注释比例。

验收命令：

```bash
python3 -m py_compile mobile/test_mobile_web_entrypoint.py
python3 -m unittest mobile.test_mobile_web_entrypoint
node --check mobile/web/app.js
rg -n "hardware_sensor_procurement_review_decision|hardware_sensor_procurement_intake|2D LiDAR|ToF|hardware_material_pending|not_proven|software_proof|delivery_success=false|primary_actions_enabled=false|next_required_evidence|owner_handoff|rerun_commands" mobile docs/product/mobile_user_flow.md
rg -n "已通过|可发车|已采购|已 HIL|已送达|delivery_success=true|primary_actions_enabled=true|/cmd_vel|serial|baudrate|OSS_ACCESS_KEY_SECRET" mobile docs/product/mobile_user_flow.md || true
git diff --check -- mobile docs/product/mobile_user_flow.md
```

### Task D - Product Closeout and OKR Gate

Owner：`product-okr-owner`

文件范围：

- `sprints/2026.05.16_13-14_hardware-sensor-procurement-review-decision/tech-done.md`
- `sprints/2026.05.16_13-14_hardware-sensor-procurement-review-decision/side2side_check.md`
- `sprints/2026.05.16_13-14_hardware-sensor-procurement-review-decision/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

不得改动：

- Product closeout 不修改 PC gate / Robot diagnostics / mobile implementation 文件。

目标：

- 实施完成后更新 `tech-done.md`、`side2side_check.md`、`final.md`。
- 若证据足够，更新 `OKR.md` 和 `docs/process/okr_progress_log.md`，但只记录 software proof / review decision gate 改善。
- 继续明确 O5 外部证据未补齐，不能因本轮上调 O5。

验收命令：

```bash
rg -n "hardware_sensor_procurement_review_decision|hardware_sensor_procurement_intake|software_proof_docker_hardware_sensor_procurement_review_decision_gate|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false|Objective 5|O5|Docker|2D LiDAR|ToF|next_required_evidence|owner_handoff|rerun_commands" sprints/2026.05.16_13-14_hardware-sensor-procurement-review-decision OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.16_13-14_hardware-sensor-procurement-review-decision OKR.md docs/process/okr_progress_log.md
```

## 5. 并行启动要求

implementation 阶段必须并行启动 3 个 Engineer worker：

- `hardware-engineer`：Task A，主责 PC review decision gate。
- `robot-software-engineer`：Task B，主责 diagnostics metadata-only consumer。
- `full-stack-software-engineer`：Task C，主责 mobile phone-safe panel。

Product closeout（Task D）在三方返回后执行。不得由主节点直接写产品代码、测试代码或硬件配置；如果 runtime 无法派发子 agent，必须降级为 read-only/planning 并说明未执行实现。

## 6. 本计划阶段验收命令

本轮只创建计划文档，必须运行：

```bash
rg -n "PR #5|hardware_sensor_procurement_intake|hardware_sensor_procurement_review_decision|2D LiDAR|ToF|Objective 5|O5|Docker|software_proof|hardware_material_pending|OKR 最低优先级核对" sprints/2026.05.16_13-14_hardware-sensor-procurement-review-decision

git diff --check -- sprints/2026.05.16_13-14_hardware-sensor-procurement-review-decision
```

## 7. 风险边界

- `docs/vendor/VENDOR_INDEX.md` 不证明 2D LiDAR / ToF 已采购、接线、标定或 HIL。
- `hardware_sensor_procurement_intake` 和本轮 `hardware_sensor_procurement_review_decision` 都是 fail-closed software proof，不是真实硬件通过。
- 只有 Docker 的本机不能产生 O5 external proof。
- 后续真实材料必须链接 SKU、vendor/source document、采购状态、安装/接线/标定和 HIL entry evidence。
- 如果后续 Engineer 只能生成 local artifact，而没有真实材料，OKR 只能记录 review decision / readiness 改善，不能宣称 HIL、field pass、delivery success 或 O5 completion。

## 8. 完成前反思清单

- 是否把 Objective 5 最低但当前不可行动的理由写进 `OKR 最低优先级核对`？
- 是否明确本 sprint 承接 PR #5 和上一轮 `hardware_sensor_procurement_intake`？
- 是否把 intake 缺口转成 review decision、blocker、next_required_evidence、owner_handoff 和 rerun_commands？
- 是否列出 2D LiDAR / ToF 的 SKU、source、采购、安装、接线、标定、HIL entry 缺口？
- 是否指定 Hardware、Robot、Full-stack、Product closeout 四个 owner，并保持文件范围不重叠？
- 是否保留 `hardware_material_pending`、`not_proven`、`software_proof`、`delivery_success=false`、`primary_actions_enabled=false`？
- 是否避免修改产品代码、测试代码、硬件配置、`OKR.md` 或 closeout docs？
