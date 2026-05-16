# Sprint 2026.05.16_14-15 Hardware Sensor Procurement Execution Pack - Tech Plan

sprint_type: epic

## 1. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的是 Objective 5，约 66%。
2. 本 sprint 不直接针对 Objective 5。
3. 理由：`OKR.md` 和最近 sprint final 均说明 Objective 5 下一步必须是真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration；本机只有 Docker，继续新增本地 O5 metadata 不能构成可接受证据。本轮选择可推进的 Objective 4 量产硬件材料执行包，同时服务 Objective 1/2/3 的真实材料前置。

## 2. 证据依据

- `OKR.md` 4.1：Objective 5 约 66% 最低但外部证据缺失；Objective 1 约 73%、Objective 2/3 约 78%、Objective 4 约 83%。
- `sprints/2026.05.16_13-14_hardware-sensor-procurement-review-decision/final.md`：上轮把 2D LiDAR / ToF intake 转成 review decision，但下一步仍缺真实 SKU/source/procurement/installation/calibration/HIL entry。
- `sprints/2026.05.16_13-14_hardware-sensor-procurement-review-decision/tech-done.md`：unsupported 顶层 schema bypass 曾被发现并修复，本轮必须把 wrapper schema / nested summary 双层校验纳入围栏。
- 近期链路：`hardware_baseline_review` -> `hardware_sensor_procurement_intake` -> `hardware_sensor_procurement_review_decision`。本轮只推进下一层 execution pack，不改主操作状态。

## 3. 文件范围与分工

### Hardware Infra Engineer

允许改动：

- `pc-tools/evidence/hardware_sensor_procurement_execution_pack_gate.py`
- `pc-tools/evidence/test_hardware_sensor_procurement_execution_pack_gate.py`
- `docs/product/production_hardware_boundary.md`

实现要求：

- 读取 `docs/vendor/VENDOR_INDEX.md` 和上轮 review decision gate。
- 新增 execution pack artifact / summary，schema 使用 `trashbot.hardware_sensor_procurement_execution_pack.v1` 与 `trashbot.hardware_sensor_procurement_execution_pack_summary.v1`。
- evidence boundary 使用 `software_proof_docker_hardware_sensor_procurement_execution_pack_gate`。
- 输出 `execution_pack_status`、`material_templates`、`owner_handoff`、`rerun_commands`、`blocked_reason`、`next_required_evidence`、`not_proven`。
- fail closed：缺 review decision、unsupported schema/boundary、unsafe success/control claim、弱类型或 raw path/credential 泄漏。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/hardware_sensor_procurement_execution_pack_gate.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_hardware_sensor_procurement_execution_pack_gate.py
python3 pc-tools/evidence/hardware_sensor_procurement_execution_pack_gate.py --help
rg -n "hardware_sensor_procurement_execution_pack|software_proof_docker_hardware_sensor_procurement_execution_pack_gate|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence docs/product/production_hardware_boundary.md
git diff --check -- pc-tools/evidence/hardware_sensor_procurement_execution_pack_gate.py pc-tools/evidence/test_hardware_sensor_procurement_execution_pack_gate.py docs/product/production_hardware_boundary.md
```

### Robot Platform Engineer

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

实现要求：

- 增加 execution pack diagnostics summary 常量、默认 summary、source contract、sanitizer 和 `summarize_hardware_sensor_procurement_execution_pack`。
- 支持显式 `hardware_sensor_procurement_execution_pack_ref` 与已内嵌 summary；缺失或 unsupported 必须 fail closed。
- 不打开 collect/dropoff/cancel、ACK、cursor、Nav2、HIL、dropoff/cancel completion 或 delivery result。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "hardware_sensor_procurement_execution_pack|software_proof_docker_hardware_sensor_procurement_execution_pack_gate|blocked_missing_hardware_sensor_procurement_execution_pack|primary_actions_enabled" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

### User Touchpoint Full-Stack Engineer

允许改动：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/status.json`
- `docs/product/mobile_user_flow.md`

实现要求：

- 增加首屏只读“传感器采购执行包” panel，位置在 review decision 之后。
- 展示 `execution_pack_status`、blocker、material template、owner handoff、safe rerun command 和 safe evidence_ref。
- copy/export whitelist-only；不得展示 raw JSON、ROS topic、串口细节、凭证、checksum、完整本机路径或成功/放行动作措辞。
- Start / Confirm Dropoff / Cancel gating 不变。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
node --check mobile/web/app.js
rg -n "hardware_sensor_procurement_execution_pack|传感器采购执行包|software_proof_docker_hardware_sensor_procurement_execution_pack_gate|hardware_material_pending|not_proven" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
```

### Product Manager / OKR Owner

允许改动：

- `sprints/2026.05.16_14-15_hardware-sensor-procurement-execution-pack/tech-done.md`
- `sprints/2026.05.16_14-15_hardware-sensor-procurement-execution-pack/side2side_check.md`
- `sprints/2026.05.16_14-15_hardware-sensor-procurement-execution-pack/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

验收命令：

```bash
rg -n "hardware_sensor_procurement_execution_pack|software_proof_docker_hardware_sensor_procurement_execution_pack_gate|Objective 5|Docker|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.16_14-15_hardware-sensor-procurement-execution-pack OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.16_14-15_hardware-sensor-procurement-execution-pack OKR.md docs/process/okr_progress_log.md
```

## 4. 接口影响

- 新增 metadata-only artifact / summary schema。
- Robot diagnostics 新增只读 summary 字段，不改变已有 status/command/ACK 契约。
- Mobile 新增只读 panel 和 copy package，不改变主操作按钮启用条件。

## 5. 风险边界

- 本轮不证明真实 2D LiDAR / ToF、WAVE ROVER、UART、HIL、Nav2/fixed-route、route/elevator field pass、真实手机、delivery success 或 O5 external proof。
- 如果 worker 发现 execution pack 只是重复上轮 review decision，没有新增可执行材料模板和 owner handoff，应停止扩大实现并回报。
