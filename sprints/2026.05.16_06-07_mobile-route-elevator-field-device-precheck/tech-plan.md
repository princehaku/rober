# Sprint 2026.05.16_06-07 Mobile Route Elevator Field Device Precheck - Tech Plan

sprint_type: epic

## 1. 技术方案

本轮新增 `mobile_route_elevator_field_device_precheck` 能力，但只作为 phone-safe precheck/export/intake 包。它复用 current `mobile/web` 的真实设备验收、PWA install prompt、route/elevator handoff、browser proof 和 command safety 语义，将现场前检查收敛为一个可复制、可导出、可由 `pc-tools/evidence` 生成或校验的 summary。

证据边界固定为软件证明：`software_proof_docker_mobile_route_elevator_field_device_precheck_gate`。默认输出应保守包含 `real_device_observed=false`、`pwa_install_prompt_observed=false`、`route_elevator_field_pass=false`、`dropoff_completion=false`、`cancel_completion=false`、`delivery_success=false`、`primary_actions_enabled=false` 和 `not_proven`。任何 ACK、browser proof、handoff artifact、precheck summary 或 diagnostics metadata 都不得写成真实现场通过、HIL、delivery success 或 Objective 5 external proof。

## 2. 文件范围和 owner 分工

Task A `full-stack-software-engineer` 可改：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Task A 目标：

- 新增 first-screen `mobile_route_elevator_field_device_precheck` panel。
- 支持 whitelist copy/export，只导出 phone-safe metadata。
- 显示 route/elevator handoff reference、真实设备/PWA observation checklist、现场材料清单、`delivery_success=false`、`primary_actions_enabled=false`、`not_proven`。
- 保持 Start / Confirm Dropoff / Cancel gating 不变且 fail-closed。

Task B `robot-software-engineer` 可改：

- `docs/interfaces/ros_contracts.md`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- 如必须补 runtime metadata-only sanitizer，才可改 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`

Task B 目标：

- 为 `mobile_route_elevator_field_device_precheck` 增加 diagnostics/remote protocol metadata-only fence 或 docs/interfaces fence。
- 确认 precheck metadata 不进入 command、ACK、remote control、cursor updates、persistence updates、terminal ACK、Nav2 trigger、HIL、dropoff/cancel completion 或 delivery success。
- 保持 `/api/collect`、`POST /api/dropoff/confirm`、`POST /api/cancel` 行为不因 precheck 改变。

Task C `autonomy-engineer` 可改：

- `pc-tools/evidence/mobile_route_elevator_field_device_precheck.py`
- `pc-tools/evidence/test_mobile_route_elevator_field_device_precheck.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

Task C 目标：

- 新增 helper/gate，生成或校验 route+elevator+device precheck summary。
- summary 必须用于现场前检查，只输出 software proof / not_proven。
- 明确 same-evidence-ref、required route/elevator field materials、device/PWA observation checklist、`delivery_success=false`、`primary_actions_enabled=false`。

Task D `product-okr-owner` 可改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.16_06-07_mobile-route-elevator-field-device-precheck/tech-done.md`
- `sprints/2026.05.16_06-07_mobile-route-elevator-field-device-precheck/side2side_check.md`
- `sprints/2026.05.16_06-07_mobile-route-elevator-field-device-precheck/final.md`

Task D 目标：

- 工程 closeout 后更新 OKR、okr_progress_log 和 sprint 收口文档。
- 保守判断 Objective 4 是否可上调；Objective 2/O3 仅在现场材料链路确实增强时作为支撑说明。
- Objective 5 不因本地 precheck、browser proof、handoff summary、diagnostics metadata 上调。

范围外文件不得改动。

## 3. 接口影响

- 不新增控制命令语义。
- 不改变 Start / Confirm Dropoff / Cancel gating。
- 不改变 `/api/collect`、`/api/dropoff/confirm`、`/api/cancel` 的授权路径。
- precheck 可作为 `/api/status`、`phone_readiness`、`/api/diagnostics` 或 diagnostics summary 的 phone-safe support metadata，但必须 metadata-only。
- copy/export 包必须 whitelist-only，不能包含 token、Authorization、OSS AK/SK、root password、DB/queue URL、raw ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER、local filesystem path、traceback、checksum、complete artifacts 或 raw robot responses。

## 4. 并行启动要求

本 sprint 为 epic，跨 3 个 Engineer owner 且文件范围互不重叠。进入 implementation 后，必须同一轮并行启动 Task A、Task B、Task C 三个 worker；Task D 仅在工程结果返回后做 Product closeout。禁止把 A/B/C 降级为一个 worker 串行完成，除非 final.md 写明运行时或接口阻塞原因。

## 5. 验收命令

Task A 必须运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 mobile/test_mobile_web_entrypoint.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "mobile_route_elevator_field_device_precheck|真实设备|route/elevator|delivery_success=false|primary_actions_enabled=false|not_proven|不证明" mobile/web mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

Task B 必须运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "mobile_route_elevator_field_device_precheck|metadata-only|command|ACK|control|delivery_success=false|not_proven|不证明" docs/interfaces/ros_contracts.md onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
git diff --check -- docs/interfaces/ros_contracts.md onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
```

Task C 必须运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/mobile_route_elevator_field_device_precheck.py pc-tools/evidence/test_mobile_route_elevator_field_device_precheck.py
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/test_mobile_route_elevator_field_device_precheck.py
python3 pc-tools/evidence/mobile_route_elevator_field_device_precheck.py --help
rg -n "mobile_route_elevator_field_device_precheck|software_proof|not_proven|delivery_success=false|route/elevator|真实设备|不证明" pc-tools/evidence/mobile_route_elevator_field_device_precheck.py pc-tools/evidence/test_mobile_route_elevator_field_device_precheck.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
git diff --check -- pc-tools/evidence/mobile_route_elevator_field_device_precheck.py pc-tools/evidence/test_mobile_route_elevator_field_device_precheck.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
```

Task D 必须运行：

```bash
rg -n "mobile_route_elevator_field_device_precheck|Objective 5|Objective 4|真实设备|route/elevator|not real|不证明|delivery_success=false|OKR 最低优先级核对" sprints/2026.05.16_06-07_mobile-route-elevator-field-device-precheck OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.16_06-07_mobile-route-elevator-field-device-precheck OKR.md docs/process/okr_progress_log.md
```

计划文档启动验收命令：

```bash
rg -n "mobile_route_elevator_field_device_precheck|Objective 5|Objective 4|真实设备|route/elevator|not real|不证明|delivery_success=false|OKR 最低优先级核对" sprints/2026.05.16_06-07_mobile-route-elevator-field-device-precheck
git diff --check -- sprints/2026.05.16_06-07_mobile-route-elevator-field-device-precheck
```

## 6. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 数值最低 Objective：Objective 5，约 66%。
2. 本 sprint 不直接针对 Objective 5；主目标是 Objective 4，且只读支撑 Objective 2 / Objective 3 的现场材料准备。
3. 理由：Objective 5 当前下一步需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或真实外部材料。本机只有 Docker，继续本地 O5 metadata 会重复消费同一 blocker。Objective 4 约 76%，且最新 final 明确还缺真实手机、真实 PWA prompt/user choice、真实设备验收入口；本轮 `mobile_route_elevator_field_device_precheck` 正是把 browser proof 变成出发前检查和导出入口，而不是把 browser proof 写成真实现场通过。

## 7. 风险边界

本轮最多形成 `software_proof_docker_mobile_route_elevator_field_device_precheck_gate` 或 blocked-by-design precheck evidence。它不是真实手机、真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice、真实 route/elevator field pass、真实 Nav2/fixed-route、真实 dropoff/cancel completion、delivery success、WAVE ROVER、真实串口/UART、HIL、Objective 5 external proof、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration。

## 8. 完成前反思清单

- 是否只改了各 owner 文件范围内的文件。
- 是否同步更新 `docs/` 下相关产品、接口或导航文档。
- 是否所有新增技术注释为中文，且复杂逻辑解释“为什么”。
- 是否保留 Start / Confirm Dropoff / Cancel fail-closed。
- 是否所有 summary 和 copy/export 均 whitelist-only。
- 是否没有把 browser proof、precheck summary、handoff artifact、ACK 或 diagnostics metadata 写成真实现场、真实手机、HIL、delivery success 或 Objective 5 external proof。
