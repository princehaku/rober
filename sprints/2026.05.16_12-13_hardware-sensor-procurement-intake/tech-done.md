# Sprint 2026.05.16_12-13 Hardware Sensor Procurement Intake - Tech Done

sprint_type: epic

## 1. 实际改动

本轮完成 `hardware_sensor_procurement_intake` software proof 闭环，证据边界固定为 `software_proof_docker_hardware_sensor_procurement_intake_gate`。

### Hardware / PC Gate

- 新增 `pc-tools/evidence/hardware_sensor_procurement_intake_gate.py`。
- 新增 `pc-tools/evidence/test_hardware_sensor_procurement_intake_gate.py`。
- 更新 `docs/product/production_hardware_boundary.md`，明确真实 2D LiDAR / ToF SKU、采购、接线、安装、标定和 HIL entry 仍是 `hardware_material_pending`。
- Hardware worker 已读取 vendor source：`docs/vendor/VENDOR_INDEX.md`、Waveshare `base_ctrl.py`、`config.yaml`、`json_cmd.h`。
- 结论：当前 vendor index 不覆盖真实 2D LiDAR / ToF SKU、采购、接线、标定或 HIL。

### Autonomy / Navigation Docs

- 更新 `pc-tools/README.md`。
- 更新 `docs/navigation/fixed_route_workflow.md`。
- 修复 schema handoff drift，统一 artifact schema 为 `trashbot.hardware_sensor_procurement_intake_gate.v1`，summary schema 为 `trashbot.hardware_sensor_procurement_intake_summary.v1`。
- 保持 2D LiDAR 为 SLAM/Nav2 target，ToF 为近场 safety target，不把 ToF 写成主建图输入。

### Robot Diagnostics

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 更新 diagnostics tests。
- 更新 `docs/interfaces/ros_contracts.md`。
- Robot diagnostics 只读消费 summary，保持 metadata-only：no collect/dropoff/cancel、ACK、cursor、Nav2、HIL、completion、delivery result。

### Mobile / Full-Stack

- 更新 `mobile/web`、fixture、mobile test 和 `docs/product/mobile_user_flow.md`。
- 新增 phone-safe read-only panel / copy / export whitelist。
- Start / Confirm Dropoff / Cancel 继续 fail closed。
- 不暴露 raw artifact、raw JSON、ROS topic、串口细节、凭证、checksum 或完整 vendor document。

### Product Closeout

- 补齐本文件、`side2side_check.md`、`final.md`。
- 更新 `OKR.md` 和 `docs/process/okr_progress_log.md`。

## 2. 验证结果

Engineer 已报告的实现验证：

- Hardware gate unittest：`Ran 6 tests OK`。
- Hardware gate：`py_compile`、CLI `--help`、required `rg`、scoped `git diff --check` 均通过。
- Robot diagnostics unittest：`Ran 96 tests OK`。
- Mobile unittest：`Ran 53 tests OK`。
- Integration combined tests：`Ran 149 tests OK`。
- PC gate 无 intake JSON 时返回 exit 2，并输出 `blocked_missing_hardware_sensor_procurement_intake`，符合 fail-closed 预期。
- Inline diagnostics 输出 `trashbot.hardware_sensor_procurement_intake_summary.v1`、status `blocked_missing_hardware_sensor_procurement_intake`、`delivery_success=False`、`primary_actions_enabled=False`。

Product closeout 验收命令：

```bash
rg -n "hardware_sensor_procurement_intake|software_proof_docker_hardware_sensor_procurement_intake_gate|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false|Objective 5|O5|Docker|2D LiDAR|ToF|blocked_missing_hardware_sensor_procurement_intake" sprints/2026.05.16_12-13_hardware-sensor-procurement-intake OKR.md docs/process/okr_progress_log.md

git diff --check -- sprints/2026.05.16_12-13_hardware-sensor-procurement-intake OKR.md docs/process/okr_progress_log.md
```

Product closeout 运行时间：2026-05-16 12:24 CST。

## 3. 偏差和修复

- 实施中出现 PC summary -> Robot diagnostics -> mobile handoff schema drift，Integration worker 已统一为 `trashbot.hardware_sensor_procurement_intake_summary.v1`。
- gate 在缺少 intake JSON 时 fail closed，并返回 `blocked_missing_hardware_sensor_procurement_intake`；这是预期状态，不是验证失败。
- 本轮没有采购、安装、接线、标定或 HIL，因此不能把 intake summary 写成真实硬件材料通过。

## 4. 剩余风险

- 真实 2D LiDAR SKU、vendor/source document、采购订单、收货、安装和标定仍缺。
- 真实 ToF SKU、channel count 来源、安装位、接线、电源预算和近场阈值仍缺。
- Objective 1 不上调：没有 WAVE ROVER、UART、真实串口、`T=1001` feedback 或 HIL。
- Objective 2 / Objective 3 不上调：没有真实 route/elevator field pass、Nav2/fixed-route runtime log、task record、dropoff/cancel completion 或 delivery success。
- Objective 5 不上调：没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration。
