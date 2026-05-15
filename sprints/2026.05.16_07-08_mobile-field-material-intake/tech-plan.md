# Sprint 2026.05.16_07-08 Mobile Field Material Intake - Tech Plan

sprint_type: epic

## 1. 技术方案

本轮只规划，不修改产品代码。后续 implementation 要新增 `mobile_field_material_intake` 能力，作为 06-07 `mobile_route_elevator_field_device_precheck` 之后的 phone-safe material intake 入口。它由三部分组成：

1. `mobile/web` first-screen intake panel：展示真实设备/PWA observation、route/elevator field materials、same-evidence-ref 状态、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`，并提供 whitelist copy/export。
2. Robot diagnostics metadata-only consumer：从 diagnostics/status 的安全字段中透出 intake summary，但不进入 command、ACK、control、cursor、Nav2、HIL、dropoff/cancel completion 或 delivery success。
3. `pc-tools/evidence` fail-closed gate：校验真实设备/PWA、route/elevator、Nav2/fixed-route、task record、completion signal、dropoff/cancel materials 是否同属一个 safe `evidence_ref`，并对缺失、placeholder、mismatch、unsafe copy、success wording fail closed。

证据边界固定为 `software_proof_docker_mobile_field_material_intake_gate`。本轮和后续软件实现均不证明真实手机、真实 route/elevator field pass、Nav2/fixed-route、dropoff/cancel completion、delivery success、HIL 或 Objective 5 external proof。

## 2. 文件范围和 owner 分工

Task A `full-stack-software-engineer` 可改：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Task A 目标：

- 新增 first-screen `mobile_field_material_intake` panel。
- 支持 whitelist copy/export，只导出 phone-safe metadata。
- 显示 safe entry、safe `evidence_ref`、真实设备/PWA observation checklist、route/elevator field materials、same-evidence-ref status、`delivery_success=false`、`primary_actions_enabled=false`、`not_proven`。
- 保持 Start / Confirm Dropoff / Cancel gating 不变且 fail-closed。
- 禁止暴露 raw ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER、credentials、DB/queue URL、OSS AK/SK、本机路径、traceback、checksum、complete artifacts 或 raw robot responses。

Task B `robot-software-engineer` 可改：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

Task B 目标：

- 为 `mobile_field_material_intake` 增加 diagnostics metadata-only 消费和 sanitizer/fence。
- 确认 intake metadata 不进入 command、ACK、remote control、cursor updates、persistence updates、terminal ACK、Nav2 trigger、HIL、dropoff/cancel completion 或 delivery success。
- 保持 `/api/collect`、`POST /api/dropoff/confirm`、`POST /api/cancel` 行为不因 intake 改变。

Task C `autonomy-engineer` 可改：

- `pc-tools/evidence/mobile_field_material_intake.py`
- `pc-tools/evidence/test_mobile_field_material_intake.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

Task C 目标：

- 新增 fail-closed intake/gate，生成或校验 `mobile_field_material_intake` summary。
- summary 必须用于现场材料回填前/回填后检查，只输出 software proof / not_proven。
- 明确 same-evidence-ref、required route/elevator field materials、device/PWA observation checklist、Nav2/fixed-route runtime log、task record、completion signal、dropoff/cancel material status、`delivery_success=false`、`primary_actions_enabled=false`。

Task D `product-okr-owner` 后续 closeout 可改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.16_07-08_mobile-field-material-intake/tech-done.md`
- `sprints/2026.05.16_07-08_mobile-field-material-intake/side2side_check.md`
- `sprints/2026.05.16_07-08_mobile-field-material-intake/final.md`

Task D 目标：

- 工程 closeout 后更新 OKR、okr_progress_log 和 sprint 收口文档。
- 保守判断 Objective 4 是否可上调；Objective 2/O3 仅作为 same-evidence-ref 材料摄取支撑说明。
- Objective 5 不因本地 intake、browser proof、precheck summary、handoff summary、diagnostics metadata 或 pc-tools gate 上调。

范围外文件不得改动。

## 3. 接口影响

- 不新增控制命令语义。
- 不改变 Start / Confirm Dropoff / Cancel gating。
- 不改变 `/api/collect`、`/api/dropoff/confirm`、`/api/cancel` 的授权路径。
- `mobile_field_material_intake` 可以作为 `/api/status`、`phone_readiness`、`/api/diagnostics` 或 diagnostics summary 的 phone-safe support metadata，但必须 metadata-only。
- copy/export 包必须 whitelist-only，不能包含 token、Authorization、OSS AK/SK、root password、DB/queue URL、raw ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER、local filesystem path、traceback、checksum、complete artifacts、raw robot responses 或 Objective 5 external proof material。

## 4. 并行启动要求

本 sprint 为 epic，跨 3 个 Engineer owner 且文件范围互不重叠。进入 implementation 后，必须同一轮并行启动 Task A、Task B、Task C 三个 worker；Task D 只在工程结果返回后做 Product closeout。禁止把 A/B/C 降级为一个 worker 串行完成，除非 `final.md` 写明运行时或接口阻塞原因。

## 5. 验收命令

Task A 必须运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 mobile/test_mobile_web_entrypoint.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "mobile_field_material_intake|真实手机|route/elevator|delivery_success=false|primary_actions_enabled=false|not_proven|不证明|not real" mobile/web mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

Task B 必须运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "mobile_field_material_intake|metadata-only|command|ACK|control|delivery_success=false|not_proven|不证明|not real" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

Task C 必须运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/mobile_field_material_intake.py pc-tools/evidence/test_mobile_field_material_intake.py
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/test_mobile_field_material_intake.py
python3 pc-tools/evidence/mobile_field_material_intake.py --help
rg -n "mobile_field_material_intake|software_proof|not_proven|delivery_success=false|route/elevator|真实手机|不证明|not real" pc-tools/evidence/mobile_field_material_intake.py pc-tools/evidence/test_mobile_field_material_intake.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
git diff --check -- pc-tools/evidence/mobile_field_material_intake.py pc-tools/evidence/test_mobile_field_material_intake.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
```

Task D 后续 closeout 必须运行：

```bash
rg -n "mobile_field_material_intake|Objective 5|Objective 4|software_proof_docker_mobile_field_material_intake_gate|真实手机|route/elevator|not real|不证明|delivery_success=false|OKR 最低优先级核对" sprints/2026.05.16_07-08_mobile-field-material-intake OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.16_07-08_mobile-field-material-intake OKR.md docs/process/okr_progress_log.md
```

计划文档启动验收命令：

```bash
rg -n "mobile_field_material_intake|OKR 最低优先级核对|Objective 5|Objective 4|software_proof_docker_mobile_field_material_intake_gate|真实手机|route/elevator|not real|不证明" sprints/2026.05.16_07-08_mobile-field-material-intake
git diff --check -- sprints/2026.05.16_07-08_mobile-field-material-intake
```

## 6. OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 66%。
- 本 sprint 是否针对该 Objective：否。本 sprint 主目标是 Objective 4，支撑 Objective 2 / Objective 3 的 same-evidence-ref 材料摄取。
- 如不针对，理由：Objective 5 下一步需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration 或真实外部云材料；当前本机 Docker-only，用户也明确说本机没有真实硬件，只有 Docker。继续堆本地 O5 metadata 会重复消费外部材料 blocker。最新 06-07 final 指向使用 precheck 采集真实设备/PWA 或 route/elevator field materials；05-06 final 也说明 browser proof not real 真实手机或真实 route/elevator field pass。因此本轮转向 Objective 4 的可执行入口，并支撑 O2/O3 的现场材料 intake。
- `final.md` 收口时需复核：是否仍无真实 O5 外部材料；是否确实只形成 `software_proof_docker_mobile_field_material_intake_gate`；是否没有把 intake/gate 上调为真实手机、真实 route/elevator field pass、Nav2/fixed-route、dropoff/cancel completion、delivery success、HIL 或 Objective 5 external proof。

## 7. 证据边界

本轮 planning 和后续 implementation 最多形成 `software_proof_docker_mobile_field_material_intake_gate` 或 blocked-by-design intake evidence。

不证明：

- 真实手机、真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice。
- 真实 route/elevator field pass、真实 Nav2/fixed-route、真实 dropoff/cancel completion、delivery success。
- WAVE ROVER、真实串口/UART、HIL、`T=1001` feedback、`/odom`、`/imu/data`、`/battery` 实机样本。
- Objective 5 external proof、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/migration。

## 8. 完成前反思清单

- 是否只改了各 owner 文件范围内的文件。
- 是否同步更新 `docs/` 下相关产品、接口或导航文档。
- 是否所有新增技术注释为中文，且复杂逻辑解释“为什么”。
- 是否保留 Start / Confirm Dropoff / Cancel fail-closed。
- 是否所有 summary 和 copy/export 均 whitelist-only。
- 是否没有把 browser proof、precheck summary、intake summary、handoff artifact、ACK、pc-tools gate 或 diagnostics metadata 写成真实现场、真实手机、HIL、delivery success 或 Objective 5 external proof。

