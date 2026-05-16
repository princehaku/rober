# Sprint 2026.05.16_18-19 Hardware Sensor HIL-entry Config Precheck - Tech Plan

sprint_type: epic

## 1. 技术目标

建立 `trashbot.hardware_sensor_hil_entry_config_precheck.v1` / `trashbot.hardware_sensor_hil_entry_config_precheck_summary.v1`，边界为 `software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate`。

该 contract 只验证 future HIL-entry sensor config 的参数化完整性与证据引用，不声明真实硬件通过。它必须覆盖 sensor count、thresholds、frame IDs、safety policy、evidence refs 和 vendor/source boundary，并且在 PC gate、Robot diagnostics、mobile/web 和 Product closeout 中保持同一证据语言。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 数值最低 Objective：Objective 5，约 66%。
2. 本 sprint 不直接针对 Objective 5。
3. 转向理由：Objective 5 的下一步真实进展需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 等外部材料；当前本机只有 Docker，继续做本地 Objective 5 metadata 会重复 blocked-by-design 证据，按 stop rule 不推进。
4. 本 sprint 转向 Objective 1 / Objective 4：Objective 1 约 74%，Objective 4 约 87%。在无真实手机、无真实硬件、无现场材料时，最低可行动作是把硬件传感器基线和 HIL-entry 准备链推进为参数化 config precheck contract，防止 PR #5 review 暴露的 default hardware set / mandatory sensor baseline / source attribution 问题再次进入实现。
5. Final 收口时必须回顾：如果实现只得到 software proof，Objective 5 仍不得上调；Objective 1 / Objective 4 也只能按 config-precheck 可验证性保守记录。

## 2. 背景证据约束

- GitHub PR #5 `Make elevator-assisted delivery mandatory; update agents, OKR and hardware baseline` review：
  - P1：default hardware set 与 mandatory sensor baseline 不一致。
  - P2：OKR lowest-objective claim 不一致。
  - P2：mandatory sensor assumptions 缺 `docs/vendor/` source attribution。
- 最新 sprint `2026.05.16_17-18_hardware-baseline-source-alignment` 已完成 source-alignment gate。
- 当前结论：local vendor coverage 仍不证明 2D LiDAR / ToF 已采购、安装、接线、标定、HIL 或 field pass。
- 本轮不重复 source alignment；必须落到 HIL-entry config precheck contract。

## 3. 全局证据边界

所有 task 必须保持：

- `software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate`
- `software_proof` only
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

所有 task 必须明确不证明：

- not real WAVE ROVER/UART/HIL
- not real 2D LiDAR/ToF procurement/install/calibration
- not real phone/browser
- not Objective 5 external proof

禁止写入或展示：

- 真实控制成功、HIL success、field pass、delivery success、dropoff/cancel completion。
- raw ROS topics、`/cmd_vel`、raw JSON、串口/UART 设备、baudrate、WAVE ROVER 参数。
- 凭证、DB/queue URL、OSS AK/SK、local filesystem path、traceback、checksum、完整 artifact。

## 4. 并行 Worker 任务

### Task A Hardware - HIL-entry config precheck PC gate

责任角色：Hardware Infra Engineer。

允许改动文件：

- `pc-tools/evidence/hardware_sensor_hil_entry_config_precheck_gate.py`
- `pc-tools/evidence/test_hardware_sensor_hil_entry_config_precheck_gate.py`
- `pc-tools/README.md`
- `docs/product/production_hardware_boundary.md`

实现要求：

- 新增 PC gate，contract 名为 `trashbot.hardware_sensor_hil_entry_config_precheck.v1`，summary 为 `trashbot.hardware_sensor_hil_entry_config_precheck_summary.v1`。
- 输入可以来自 future HIL-entry sensor config artifact/JSON 或命令行参数，但必须 dependency-free，可在 Docker-only 本机运行。
- 检查项必须覆盖：
  - sensor count / ToF channel count 参数化，不能硬编码单一 SKU。
  - thresholds 参数化，至少能表达近场安全阈值、confidence 或 validation threshold。
  - frame IDs 参数化，至少能表达 sensor frame、base frame、mount/calibration frame 或明确缺口。
  - safety policy 参数化，缺配置、缺 evidence、unsupported schema、unsafe copy、success claim 必须 fail closed。
  - evidence refs，至少列出 source/procurement/install-wiring/power/calibration/HIL-entry 材料引用或缺口。
- 输出必须包含 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`next_required_evidence`、`owner_handoff` 和 sanitized `safe_copy`。
- 不得读取硬件、串口、ROS graph、真实 sensor driver 或网络外部资源。

验收命令：

```bash
python3 -m py_compile pc-tools/evidence/hardware_sensor_hil_entry_config_precheck_gate.py
python3 -m unittest pc-tools/evidence/test_hardware_sensor_hil_entry_config_precheck_gate.py
python3 pc-tools/evidence/hardware_sensor_hil_entry_config_precheck_gate.py --help
rg -n "trashbot.hardware_sensor_hil_entry_config_precheck|software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate|not_proven|delivery_success=false|primary_actions_enabled=false|sensor count|thresholds|frame IDs|safety policy" pc-tools/evidence/hardware_sensor_hil_entry_config_precheck_gate.py pc-tools/evidence/test_hardware_sensor_hil_entry_config_precheck_gate.py pc-tools/README.md docs/product/production_hardware_boundary.md
git diff --check -- pc-tools/evidence/hardware_sensor_hil_entry_config_precheck_gate.py pc-tools/evidence/test_hardware_sensor_hil_entry_config_precheck_gate.py pc-tools/README.md docs/product/production_hardware_boundary.md
```

### Task B Robot - Diagnostics metadata-only consumer

责任角色：Robot Platform Engineer。

允许改动文件：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

实现要求：

- 在 operator gateway diagnostics 中新增 `hardware_sensor_hil_entry_config_precheck` metadata-only consumer。
- 只消费 artifact/summary 中的安全字段：schema、status、safe evidence ref、sensor config summary、missing config/material categories、next required evidence、owner handoff、safe copy、evidence boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 缺失 summary、unsupported schema、unsafe raw fields、success claims、weak evidence boundary 必须 fail closed。
- 不改变 collect/dropoff/cancel API 授权，不发布 ROS 控制，不读取 raw artifact。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "hardware_sensor_hil_entry_config_precheck|trashbot.hardware_sensor_hil_entry_config_precheck|software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate|metadata-only|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

### Task C Full-stack - Phone-safe read-only panel

责任角色：User Touchpoint Full-Stack Engineer。

允许改动文件：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/fixtures/status.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

实现要求：

- 在 mobile/web 新增只读 “传感器 HIL 入口配置预检” panel。
- 消费 `hardware_sensor_hil_entry_config_precheck`、`hardware_sensor_hil_entry_config_precheck_summary` 或兼容 phone-safe summary。
- 展示字段仅限：precheck status、safe evidence ref、sensor count summary、threshold summary、frame IDs summary、safety policy summary、missing config/material summary、next required evidence、owner handoff、safe copy、evidence boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- copy/export whitelist-only；无 `safe_copy` 时显示 blocked copy unavailable。
- Start / Confirm Dropoff / Cancel gating 不变。
- 文案必须说明 software proof only，不是真实 HIL、真实 2D LiDAR / ToF、真实手机/browser 或 Objective 5 external proof。

验收命令：

```bash
python3 -m unittest mobile.web.test_mobile_web_entrypoint
node --check mobile/web/app.js
rg -n "hardware_sensor_hil_entry_config_precheck|trashbot.hardware_sensor_hil_entry_config_precheck|software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate|not_proven|delivery_success=false|primary_actions_enabled=false|Start|Confirm Dropoff|Cancel" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/web/fixtures/status.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### Task D Product closeout - OKR and sprint closure

责任角色：Product Manager / OKR Owner。

允许改动文件：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck/tech-done.md`
- `sprints/2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck/side2side_check.md`
- `sprints/2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck/final.md`

实现要求：

- 等 Task A/B/C 返回后再收口，不得提前写 OKR 进展。
- `tech-done.md` 必须列出实际改动、验证结果、失败定位和剩余风险。
- `side2side_check.md` 必须核对本 PR #5 review 证据是否被转成可执行 contract。
- `final.md` 必须回顾 `## OKR 最低优先级核对` 的转向理由是否仍成立。
- `OKR.md` 和 `docs/process/okr_progress_log.md` 如更新，必须保守写明 Objective 5 没有 external proof，Objective 1 / Objective 4 只得到 software-proof config precheck readiness。

验收命令：

```bash
rg -n "hardware_sensor_hil_entry_config_precheck|software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate|Objective 5|Docker|not_proven|delivery_success=false|primary_actions_enabled=false|PR #5" OKR.md docs/process/okr_progress_log.md sprints/2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck/tech-done.md sprints/2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck/side2side_check.md sprints/2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck/final.md
```

## 5. 接口影响

- 新增 PC/Robot/mobile shared summary contract，但不改变 ROS topic、action、service、collect/dropoff/cancel API。
- Robot diagnostics 只能新增 metadata field，不改变控制授权。
- mobile/web 只能新增只读 panel，不改变 Start / Confirm Dropoff / Cancel gating。
- Product closeout 只根据实际 worker 结果更新 OKR，不把 planned contract 当完成证据。

## 6. 并行启动要求

实现阶段必须同一轮并行启动 4 个 worker：

- Task A Hardware owns PC gate and hardware boundary docs.
- Task B Robot owns diagnostics consumer and ROS contract docs.
- Task C Full-stack owns mobile/web and mobile product flow docs.
- Task D Product owns OKR and sprint closeout after A/B/C evidence returns.

Task A/B/C 文件范围互不重叠，可以并行实现。Task D 先只读等待 A/B/C 结果，最后收口。

## 7. 风险与回滚边界

- 如果 Task A contract 只检查字段存在，不检查参数化语义，本轮价值不足；必须补 fail-closed case。
- 如果 Task B/C 暴露 raw hardware details、路径、topic、serial、success copy，必须回退为 blocked summary。
- 如果验证只在 docs 中出现关键词但没有 test 覆盖 fail-closed path，不得收口。
- 如果出现真实硬件、真实手机或 Objective 5 证明，应单独记录为外部材料，不混入本 software proof contract。

## 8. 本规划阶段验收命令

```bash
test -f sprints/2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck/pre_start.md && test -f sprints/2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck/prd.md && test -f sprints/2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck/tech-plan.md
rg -n "OKR 最低优先级核对|PR #5|hardware_sensor_hil_entry_config_precheck|software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate|Objective 5|Docker|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck
git diff --check -- sprints/2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck
```

