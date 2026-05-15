# Sprint 2026.05.16_07-08 Mobile Field Material Intake - Pre Start

sprint_type: epic

## 1. 启动原因

本轮按 `OKR.md` 4.1 重新排序。Objective 5 约 66%，是当前数值最低 Objective；但它的下一步需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration 或其他真实外部云材料。本机没有真实硬件，只有 Docker，因此不应继续堆 O5 本地 metadata，也不能把 browser proof、precheck summary、handoff artifact、diagnostics metadata 或 ACK 写成 Objective 5 external proof。

最新 sprint `sprints/2026.05.16_06-07_mobile-route-elevator-field-device-precheck/final.md` 已完成 `mobile_route_elevator_field_device_precheck`，边界是 `software_proof_docker_mobile_route_elevator_field_device_precheck_gate`；它的下一步明确应使用 precheck 去采集真实设备/PWA 或 route/elevator field materials。前一轮 `sprints/2026.05.16_05-06_mobile-route-elevator-handoff-browser-proof/final.md` 也说明 local Chromium-family browser proof 只证明当前 `mobile/web` PWA 可见、phone-safe、fail-closed，不是真实手机或真实 route/elevator field pass。

因此本轮启动 `mobile_field_material_intake`：把 06-07 的 precheck 推进为 phone-safe 的真实设备/PWA 与 route/elevator 现场材料回填入口，同时让 Robot diagnostics 只消费 metadata-only summary，让 `pc-tools/evidence` 提供 fail-closed intake/gate。主目标是 Objective 4，支撑 Objective 2 / Objective 3 的 same-evidence-ref 材料摄取；不推进 Objective 5，除非用户提供真实外部云/4G/OSS/CDN/DB/queue 材料。

## 2. 背景证据

- `OKR.md` 4.1：Objective 5 约 66% 数值最低；主要缺口是真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration。本机 Docker-only，不应继续用本地 O5 metadata 推进完成度。
- `sprints/2026.05.16_06-07_mobile-route-elevator-field-device-precheck/final.md`：完成 `mobile_route_elevator_field_device_precheck`，证据边界为 `software_proof_docker_mobile_route_elevator_field_device_precheck_gate`；下一步应使用 precheck 去采集真实设备/PWA 或 route/elevator field materials。
- `sprints/2026.05.16_05-06_mobile-route-elevator-handoff-browser-proof/final.md`：local Chromium-family browser proof 只证明当前 `mobile/web` PWA 可见、phone-safe、fail-closed；not real 真实手机、真实 PWA prompt/user choice、真实 route/elevator field pass、Nav2/fixed-route、dropoff/cancel completion 或 delivery success。
- `docs/product/mobile_user_flow.md`：当前 `mobile/web` 已有真实手机验收交接会话、PWA 安装提示证据、route/elevator handoff、现场材料包、材料校验、完成信号等 phone-safe surfaces；这些 surface 均保持 fail-closed，并显式写明不证明真实手机、真实现场、HIL 或 Objective 5 external proof。
- 用户本轮要求：根据近期 PR 和评审，建议下一步应深入的 OKR；每条建议基于具体证据；避免泛泛建议；用 team 继续完成 OKR；功能往前走；测试只围栏；优先推进完成度低；本机没有真实硬件，只有 Docker；最后提交并推送。

## 3. 用户价值和产品北极星

用户价值：现场操作者拿到 06-07 precheck 后，需要一个手机可读、可复制、可由 PC gate 校验的真实材料回填入口，把真实设备/PWA 观察、route/elevator 现场材料、Nav2/fixed-route runtime log、task record、dropoff/cancel completion 和 delivery result 的缺口按同一 `evidence_ref` 收敛，而不是继续在聊天或分散面板中靠人工记忆补材料。

产品北极星：普通手机用户和现场支持人员可以在不接触 SSH、ROS2、串口、云凭证或 raw artifact 的情况下，把真实现场材料回填到一个 phone-safe intake flow；系统保持 fail-closed，清楚说明 `software_proof_docker_mobile_field_material_intake_gate` 不证明真实手机、真实 route/elevator field pass、Nav2/fixed-route、dropoff/cancel completion、delivery success、HIL 或 Objective 5 external proof。

## 4. Owner 和边界

- Task A `full-stack-software-engineer`：负责 `mobile/web/*`、fixture、mobile entrypoint test、`docs/product/mobile_user_flow.md`。目标是 first-screen `mobile_field_material_intake` 入口、whitelist copy/export、真实设备/PWA 与 route/elevator 材料回填文案；不得改变 Start / Confirm Dropoff / Cancel gating。
- Task B `robot-software-engineer`：负责 `operator_gateway_diagnostics.py`、诊断 unittest、`docs/interfaces/ros_contracts.md`。目标是 Robot diagnostics metadata-only 消费 `mobile_field_material_intake` summary；不得把 intake metadata 接入 command、ACK、control、cursor、Nav2、HIL、dropoff/cancel completion 或 delivery success。
- Task C `autonomy-engineer`：负责 `pc-tools/evidence/mobile_field_material_intake.py`、对应 unittest、`pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`。目标是 fail-closed intake/gate，校验同一 `evidence_ref` 的真实设备/PWA 与 route/elevator 材料缺口。
- Task D `product-okr-owner`：工程完成后负责 `OKR.md`、`docs/process/okr_progress_log.md`、本 sprint `tech-done.md`、`side2side_check.md`、`final.md` closeout；本轮 planning-only 不修改这些 closeout 文件。

## 5. 风险和阻塞

- Objective 5 继续被真实外部材料阻塞：没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/migration 时，本轮不得上调 O5。
- 本机 Docker-only，planning 和后续软件 gate 不证明真实手机、真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice、真实 route/elevator field pass、真实 Nav2/fixed-route、真实 dropoff/cancel completion、delivery success、WAVE ROVER、真实串口/UART 或 HIL。
- 现场材料回填仍需要真实设备/PWA 或 route/elevator field materials；本轮只是建立入口和 fail-closed intake/gate。

