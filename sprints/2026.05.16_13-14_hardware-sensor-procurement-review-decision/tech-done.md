# Sprint 2026.05.16_13-14 Hardware Sensor Procurement Review Decision - Tech Done

sprint_type: epic

## 1. 实际改动

本轮完成 `hardware_sensor_procurement_review_decision` software proof 闭环，证据边界固定为 `software_proof_docker_hardware_sensor_procurement_review_decision_gate`。

### Hardware / PC Gate

- 新增 `pc-tools/evidence/hardware_sensor_procurement_review_decision_gate.py`。
- 新增 `pc-tools/evidence/test_hardware_sensor_procurement_review_decision_gate.py`。
- gate 读取 `hardware_sensor_procurement_intake` artifact / summary，输出 `review_decision`、`blockers`、`next_required_evidence`、`owner_handoff` 和 `rerun_commands`。
- 缺真实 2D LiDAR / ToF SKU、source、采购、安装、接线、标定或 HIL entry 时保持 `hardware_material_pending`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- Hardware worker 已读取 vendor source：`docs/vendor/VENDOR_INDEX.md`、Waveshare `base_ctrl.py`、`config.yaml`、`json_cmd.h`。
- 结论：当前 vendor index 不覆盖真实 2D LiDAR / ToF SKU、采购、安装、接线、标定或 HIL；本轮不是硬件采购通过。

### Robot Diagnostics

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 更新 diagnostics tests。
- Robot diagnostics 只读消费 `hardware_sensor_procurement_review_decision` summary，保持 metadata-only。
- 缺失 summary、unsupported schema、unsafe fields 均 fail closed；不触发 collect/dropoff/cancel、ACK、cursor、Nav2、HIL、dropoff/cancel completion 或 delivery result。

### Mobile / Full-Stack

- 更新 `mobile/web`、fixture、mobile test 和相关产品文档。
- mobile 首屏新增只读“传感器采购评审决策” panel，展示 `review_decision`、blocker、`next_required_evidence`、`owner_handoff`、safe `rerun_commands` 和 safe `evidence_ref`。
- Start / Confirm Dropoff / Cancel 继续 fail closed。
- 不暴露 raw artifact、raw JSON、ROS topic、串口细节、凭证、checksum 或完整 vendor document。

### Product Closeout

- 补齐本文件、`side2side_check.md`、`final.md`。
- 更新 `OKR.md` 和 `docs/process/okr_progress_log.md`。

## 2. 验证结果

Engineer 已报告的实现验证：

- Hardware gate：`py_compile` passed。
- Hardware gate unittest：`Ran 6 tests OK`。
- Hardware gate CLI：`--help` passed。
- Hardware gate required `rg` passed。
- Hardware gate scoped `git diff --check` passed。
- 首轮发现 unsupported 顶层 schema 会被内嵌合法 summary 放行，已修复并复验。
- Robot diagnostics unittest：`Ran 98 tests OK`。
- Robot diagnostics：`py_compile`、required `rg`、scoped `git diff --check` 均通过。
- Robot diagnostics 缺失、unsupported schema、unsafe fields 均 blocked。
- Mobile unittest：`Ran 54 tests OK`。
- Mobile：`node --check`、required `rg`、scoped `git diff --check` 均通过。
- Mobile Start / Confirm Dropoff / Cancel 均保持 fail closed。

Product closeout 验收命令：

```bash
rg -n "hardware_sensor_procurement_review_decision|hardware_sensor_procurement_intake|software_proof_docker_hardware_sensor_procurement_review_decision_gate|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false|Objective 5|O5|Docker|2D LiDAR|ToF|next_required_evidence|owner_handoff|rerun_commands" sprints/2026.05.16_13-14_hardware-sensor-procurement-review-decision OKR.md docs/process/okr_progress_log.md

git diff --check -- sprints/2026.05.16_13-14_hardware-sensor-procurement-review-decision OKR.md docs/process/okr_progress_log.md
```

Product closeout 运行时间：2026-05-16 13:20 CST。

## 3. 偏差和修复

- Hardware 首轮发现 unsupported 顶层 schema 可被内嵌合法 summary 放行；已修复为 fail closed，并通过复验。
- 本轮没有真实采购、安装、接线、标定或 HIL，因此不能把 review decision 写成真实硬件材料通过。
- 本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration，因此 Objective 5 保持约 66%。

## 4. 剩余风险

- 真实 2D LiDAR SKU、vendor/source document、采购订单、收货、安装和标定仍缺。
- 真实 ToF SKU、channel count 来源、安装位、接线、电源预算和近场阈值仍缺。
- Objective 1 不上调：没有 WAVE ROVER、UART、真实串口、`T=1001` feedback 或 HIL。
- Objective 2 / Objective 3 不上调：没有真实 route/elevator field pass、Nav2/fixed-route runtime log、task record、dropoff/cancel completion 或 delivery success。
- Objective 5 不上调：没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration。
