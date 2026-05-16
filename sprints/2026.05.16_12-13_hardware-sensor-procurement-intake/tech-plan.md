# Sprint 2026.05.16_12-13 Hardware Sensor Procurement Intake - Tech Plan

## 1. 目标

实现一个 `hardware_sensor_procurement_intake` fail-closed gate，把 2D LiDAR / ToF 的未来真实 SKU、vendor/source、采购、安装、接线、标定和 HIL entry 材料收敛为可验证 artifact，并让 Robot diagnostics / mobile 只读消费 sanitized summary。

本计划阶段只创建 sprint 三份文档：`pre_start.md`、`prd.md`、`tech-plan.md`。不修改产品代码、测试代码、硬件配置或 `OKR.md`。

证据边界：本计划和后续本地实现最多是 `software_proof_docker_hardware_sensor_procurement_intake_gate`。它不是真实 2D LiDAR / ToF vendor proof，不是 HIL，不是 route/elevator field pass，不是 delivery success，也不是 Objective 5 / O5 external proof。

## 2. OKR 最低优先级核对

当前 live `OKR.md` 4.1 table：

- Objective 5：约 66%，当前数值最低。
- Objective 1：约 73%。
- Objective 2：约 78%。
- Objective 3：约 78%。
- Objective 4：约 81%。

本 sprint 不直接主攻最低 Objective 5。理由：

- Objective 5 的剩余关键缺口是真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。
- 当前开发主机只有 Docker，不能产生真实外部 O5 材料。
- 最近多个 sprint 已验证：继续叠加本地 O5 metadata 不能提高真实 O5 完成度，反而会重复消费同一外部证据 blocker。

本 sprint 改攻 Objective 4 / Objective 1 / Objective 2 / Objective 3 的可行动作：真实 sensor procurement material intake。依据 live `OKR.md` 6，本轮最高可行动作之一是补真实 2D LiDAR / ToF SKU/vendor/procurement/installation/HIL-entry 材料；上一轮 `hardware_baseline_review` final 也把该缺口列为下一步。

## 3. 文件结构和职责

后续 implementation 阶段建议文件边界：

| Owner | 文件范围 | 职责 |
| --- | --- | --- |
| `hardware-engineer` | `pc-tools/evidence/hardware_sensor_procurement_intake_gate.py`、`pc-tools/evidence/test_hardware_sensor_procurement_intake_gate.py`、`docs/product/production_hardware_boundary.md`、必要 README/docs | 定义 intake artifact、fail-closed validation、hardware/source/procurement 字段 |
| `autonomy-engineer` | `pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md` 或相关 evidence docs | 对齐 2D LiDAR / ToF / monocular responsibility split，不把 ToF 写成主建图输入 |
| `robot-software-engineer` | `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`、相关 tests、`docs/interfaces/ros_contracts.md` | Robot diagnostics metadata-only consumer 和 compatibility fence |
| `full-stack-software-engineer` | `mobile/web/index.html`、`mobile/web/app.js`、`mobile/web/styles.css`、fixture/tests、`docs/product/mobile_user_flow.md` | 手机只读 panel、phone-safe copy/export whitelist |
| `product-okr-owner` | `sprints/2026.05.16_12-13_hardware-sensor-procurement-intake/*`、实施完成后 `OKR.md`、`docs/process/okr_progress_log.md` | sprint 收口、OKR 更新和证据边界 |

如果实施阶段接口强耦合，`hardware-engineer` 主责 intake source-of-truth，`robot-software-engineer` 主责最终 diagnostics compatibility，其他 owner 并行补专业事实；禁止主节点自己写产品代码、测试代码或硬件配置。

## 4. Team 并行执行计划

### Task A - Hardware Sensor Procurement Intake Gate

Owner：`hardware-engineer`

目标：

- 新增 `hardware_sensor_procurement_intake` artifact/gate。
- 对 2D LiDAR / ToF SKU、vendor/source document、采购状态、机械安装、接线、电源、标定、HIL entry 字段做 fail-closed 校验。
- 明确 `docs/vendor/VENDOR_INDEX.md` 仅证明当前 vendor coverage，不证明 LiDAR/ToF source/procurement。

实现要求：

- 任何 placeholder、空 source、缺 SKU、缺采购状态、缺机械/接线/标定/HIL entry 资料都必须 blocked。
- ToF channel count 必须有来源或被标为 product target pending validation。
- 输出 summary 必须固定 `hardware_material_pending`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`，直到真实材料补齐。

建议验收命令：

```bash
python3 -m py_compile pc-tools/evidence/hardware_sensor_procurement_intake_gate.py pc-tools/evidence/test_hardware_sensor_procurement_intake_gate.py
python3 pc-tools/evidence/test_hardware_sensor_procurement_intake_gate.py
python3 pc-tools/evidence/hardware_sensor_procurement_intake_gate.py --help
rg -n "hardware_sensor_procurement_intake|2D LiDAR|ToF|docs/vendor/VENDOR_INDEX.md|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools docs/product
git diff --check -- pc-tools/evidence docs/product/production_hardware_boundary.md
```

### Task B - Autonomy Sensor Responsibility Alignment

Owner：`autonomy-engineer`

目标：

- 把 intake summary 与 Nav2/SLAM、fixed-route、电梯 evidence chain 对齐。
- 2D LiDAR 只作为采购/安装/标定后进入 SLAM/Nav2 主链的 target。
- ToF 只作为近场 safety gate target，不作为主建图输入。
- Monocular camera 保留 elevator door / target-floor semantic evidence role。

实现要求：

- 不出现 real field pass、delivery success、HIL pass 文案。
- 如果只改 docs，仍需通过 `rg` 和 scoped `git diff --check`。

建议验收命令：

```bash
rg -n "hardware_sensor_procurement_intake|2D LiDAR|ToF|SLAM|Nav2|monocular|elevator|not_proven|software_proof" docs/navigation docs/product pc-tools
rg -n "delivery_success=true|field pass|HIL pass|LiDAR.*proven|ToF.*proven" docs/navigation docs/product pc-tools || true
git diff --check -- docs/navigation docs/product pc-tools
```

### Task C - Robot Diagnostics Metadata-Only Consumer

Owner：`robot-software-engineer`

目标：

- 让 Robot diagnostics 只读消费 `hardware_sensor_procurement_intake` summary。
- 保持 metadata-only：不触发 collect/dropoff/cancel、ACK、cursor、Nav2、HIL、dropoff/cancel completion 或 delivery result。
- 兼容 PC gate summary schema，缺失或 unsupported schema 时 fail closed。

实现要求：

- 不透传 raw artifact、raw ROS topic、raw JSON、serial/UART、baudrate、hardware path、credential、checksum、complete vendor/source document。
- 测试要证明 metadata-only response 不触发控制路径。

建议验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics
rg -n "hardware_sensor_procurement_intake|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false|ACK|metadata-only" onboard/src/ros2_trashbot_behavior docs/interfaces
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
```

### Task D - Mobile Phone-Safe Read-Only Panel

Owner：`full-stack-software-engineer`

目标：

- 在 mobile/web 中只读展示 `hardware_sensor_procurement_intake` 或 compatible summary。
- 展示 procurement status、missing source/procurement/mounting/wiring/calibration/HIL entry、owner next action、safe `evidence_ref`。
- 保持 Start / Confirm Dropoff / Cancel fail closed，不增加控制路径。

实现要求：

- copy/export whitelist-only。
- 不出现 raw ROS topic、`/cmd_vel`、raw JSON、serial/UART、baudrate、WAVE ROVER 参数、credential、DB/queue URL、OSS AK/SK、checksum、complete artifact、raw vendor document。
- 中文优先，避免“已通过”“可发车”“已采购”“已 HIL”一类成功文案。

建议验收命令：

```bash
python3 -m py_compile mobile/test_mobile_web_entrypoint.py
python3 -m unittest mobile.test_mobile_web_entrypoint
node --check mobile/web/app.js
rg -n "hardware_sensor_procurement_intake|2D LiDAR|ToF|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false" mobile docs/product/mobile_user_flow.md
git diff --check -- mobile docs/product/mobile_user_flow.md
```

### Task E - Product Closeout and OKR Gate

Owner：`product-okr-owner`

目标：

- 实施完成后更新 `tech-done.md`、`side2side_check.md`、`final.md`。
- 若证据足够，更新 `OKR.md` 和 `docs/process/okr_progress_log.md`，但只记录 software proof / intake gate 改善。
- 继续明确 O5 外部证据未补齐，不能因本轮上调 O5。

建议验收命令：

```bash
rg -n "hardware_sensor_procurement_intake|software_proof_docker_hardware_sensor_procurement_intake_gate|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false|Objective 5|O5|Docker|2D LiDAR|ToF" sprints/2026.05.16_12-13_hardware-sensor-procurement-intake OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.16_12-13_hardware-sensor-procurement-intake OKR.md docs/process/okr_progress_log.md
```

## 5. 本计划阶段验收命令

本轮只创建计划文档，必须运行：

```bash
rg -n "PR #5|hardware_baseline_review|hardware_sensor_procurement_intake|2D LiDAR|ToF|docs/vendor/VENDOR_INDEX.md|Objective 5|O5|Docker|software_proof|hardware_material_pending|OKR 最低优先级核对" sprints/2026.05.16_12-13_hardware-sensor-procurement-intake

git diff --check -- sprints/2026.05.16_12-13_hardware-sensor-procurement-intake
```

## 6. 风险边界

- `docs/vendor/VENDOR_INDEX.md` 不证明 2D LiDAR / ToF 已采购、接线、标定或 HIL。
- `hardware_baseline_review` 和本轮 `hardware_sensor_procurement_intake` 都是 fail-closed software proof，不是真实硬件通过。
- 只有 Docker 的本机不能产生 O5 外部 proof。
- 后续真实材料必须链接 SKU、vendor/source document、采购状态、安装/接线/标定和 HIL entry evidence。
- 如果后续 Engineer 只能生成 local artifact，而没有真实材料，OKR 只能记录 intake/readiness 改善，不能宣称 HIL、field pass、delivery success 或 O5 completion。

## 7. 完成前反思清单

- 是否把 Objective 5 最低但当前不可行动的理由写进 `OKR 最低优先级核对`？
- 是否明确本 sprint 针对 PR #5 P2 source/procurement material gap？
- 是否把 `docs/vendor/VENDOR_INDEX.md` 的 coverage 与 LiDAR/ToF proof 区分开？
- 是否列出 2D LiDAR / ToF 的 SKU、source、采购、安装、接线、标定、HIL entry 缺口？
- 是否指定 2-4 个并行 Engineer owner，并保持文件范围不重叠？
- 是否保留 `hardware_material_pending`、`not_proven`、`software_proof`、`delivery_success=false`、`primary_actions_enabled=false`？
- 是否避免修改产品代码、测试代码、硬件配置或 `OKR.md`？
