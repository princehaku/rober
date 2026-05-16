# Sprint 2026.05.17_02-03 Hardware Sensor HIL-entry Readiness Review - Tech Plan

sprint_type: epic

## 1. 技术方案

本轮新增 `hardware_sensor_hil_entry_readiness_review` contract。它是 receipt intake 与 HIL-entry config precheck 之后的合成评审 gate，只回答“是否具备进入 HIL-entry 人工材料评审的输入完整性”，不回答真实硬件是否通过。

输出 contract：

- artifact schema：`trashbot.hardware_sensor_hil_entry_readiness_review.v1`
- summary schema：`trashbot.hardware_sensor_hil_entry_readiness_review_summary.v1`
- boundary：`software_proof_docker_hardware_sensor_hil_entry_readiness_review_gate`
- fixed safety fields：`source=software_proof`、`hardware_material_status=hardware_material_pending`、`evidence_status=not_proven`、`delivery_success=false`、`primary_actions_enabled=false`

## 2. 分工和文件范围

### Task A - Hardware Infra Engineer

允许改动：

- `pc-tools/evidence/hardware_sensor_hil_entry_readiness_review_gate.py`
- `pc-tools/evidence/test_hardware_sensor_hil_entry_readiness_review_gate.py`
- `pc-tools/README.md`
- `docs/product/production_hardware_boundary.md`

要求：

- 先读 `docs/vendor/VENDOR_INDEX.md`，并在输出中列出采用的 vendor/source boundary。
- Gate 接收 `--receipt-intake-json`、`--config-precheck-json`、`--output`、`--summary-output`、`--once-json`。
- 支持读取 artifact 或 summary，但必须拒绝 unsupported schema、弱 boundary、success/control claims、缺 receipt/source/SKU、缺 config evidence refs、缺 safety policy 等。

验收命令：

```bash
python3 -m py_compile pc-tools/evidence/hardware_sensor_hil_entry_readiness_review_gate.py
python3 -m unittest pc-tools/evidence/test_hardware_sensor_hil_entry_readiness_review_gate.py
python3 pc-tools/evidence/hardware_sensor_hil_entry_readiness_review_gate.py --help
rg -n "hardware_sensor_hil_entry_readiness_review|software_proof_docker_hardware_sensor_hil_entry_readiness_review_gate|docs/vendor/VENDOR_INDEX.md|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence pc-tools/README.md docs/product/production_hardware_boundary.md
git diff --check -- pc-tools/evidence/hardware_sensor_hil_entry_readiness_review_gate.py pc-tools/evidence/test_hardware_sensor_hil_entry_readiness_review_gate.py pc-tools/README.md docs/product/production_hardware_boundary.md
```

### Task B - Robot Platform Engineer

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

要求：

- 新增 metadata-only diagnostics consumer：`hardware_sensor_hil_entry_readiness_review` / `_summary`。
- 支持 explicit ref、env、latest_status、diagnostics nested summary。
- 缺 summary、unsupported schema、weak boundary、success claim、unsafe raw fields 时 fail closed。
- 不改变 collect/dropoff/cancel/ACK/primary action。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "hardware_sensor_hil_entry_readiness_review|software_proof_docker_hardware_sensor_hil_entry_readiness_review_gate|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
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

- 新增只读“传感器 HIL 准入评审” panel。
- 从 status/readiness/diagnostics/nested summaries 中消费 readiness review artifact 或 summary。
- UI 只展示 phone-safe 字段，不展示 raw vendor docs、raw JSON、serial/UART、绝对路径、credentials、complete artifacts。
- Start Delivery / Confirm Dropoff / Cancel gating 不变。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.web.test_mobile_web_entrypoint
node --check mobile/web/app.js
rg -n "hardware_sensor_hil_entry_readiness_review|software_proof_docker_hardware_sensor_hil_entry_readiness_review_gate|传感器 HIL 准入评审|delivery_success=false|primary_actions_enabled=false" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/fixtures/status.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

## 3. 接口影响

- 新增 PC artifact/summary schema，不改变现有 schema。
- Robot diagnostics 新增只读 summary 字段，不改变任务控制 API。
- Mobile/web 新增只读 panel，不改变主操作 gating。

## 4. OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 66%。
- 本 sprint 是否针对该 Objective：否。
- 理由：Objective 5 当前需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 等外部材料；本机只有 Docker，继续本地 wrapper 会重复消费同一外部证据 blocker。按 stop rule 转向最低可行动作 Objective 1，并同步 Objective 4 的手机安全解释面。
- final.md 收口时需复核：O5 外部材料是否仍不可用；本轮是否保持 software proof 边界。

## 5. 验收边界

通过本 sprint 只能说明 HIL-entry readiness review contract、diagnostics consumer 和 mobile panel 在 Docker/local software proof 下工作；不得写成真实 HIL、真实 2D LiDAR / ToF、真实 Nav2/fixed-route、真实送达或 Objective 5 external proof。
