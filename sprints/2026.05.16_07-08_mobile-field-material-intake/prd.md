# Sprint 2026.05.16_07-08 Mobile Field Material Intake - PRD

sprint_type: epic

## 1. 用户价值和产品北极星

用户价值：06-07 已经把真实设备/PWA 与 route/elevator 现场前检查做成 precheck，但现场下一步需要一个更明确的回填入口。`mobile_field_material_intake` 要让现场操作者在手机上看到要补什么、能安全复制什么、哪些材料必须保持同一 `evidence_ref`，并把真实设备/PWA observation 与 route/elevator field materials 的缺口交给 `pc-tools` fail-closed gate 校验。

产品北极星：普通手机用户和现场支持人员可以完成真实材料 intake 的前置闭环，但不会因为一个软件 gate、browser proof 或 diagnostics metadata 误以为机器人已经完成真实手机验收、真实 route/elevator field pass、Nav2/fixed-route、dropoff/cancel completion、delivery success、HIL 或 Objective 5 external proof。

## 2. OKR 映射

- Objective 4：主目标。把手机端从 precheck/export 推进到真实设备/PWA 与现场材料回填入口，仍保持 phone-safe、whitelist-only、fail-closed 和普通用户可理解。
- Objective 2：支撑目标。把电梯 assisted delivery 现场材料纳入 same-evidence-ref intake，包括真实门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result 等缺口。
- Objective 3：支撑目标。把 route/fixed-route 现场材料纳入 intake，包括 Nav2/fixed-route runtime log、task record、completion signal、route/elevator reconciliation 等缺口。
- Objective 5：不推进。缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration；本轮 not real Objective 5 external proof。
- Objective 1：不推进。没有 WAVE ROVER、UART、`T=1001` feedback、真实串口、`/odom`、`/imu/data`、`/battery` 或 HIL。

## 3. KR 拆解或更新

- KR-O4-Material-Intake：`mobile/web` first-screen 增加 `mobile_field_material_intake` 入口，展示 safe `evidence_ref`、真实设备/PWA observation、route/elevator field materials、same-evidence-ref 要求、`not_proven` 和 `delivery_success=false`。
- KR-O4-Phone-Safe-Copy：copy/export 只允许 phone-safe 字段，不包含 token、Authorization、OSS AK/SK、root password、DB/queue URL、raw ROS topic、`/cmd_vel`、serial、WAVE ROVER 参数、本机路径、traceback、checksum、完整 evidence 文件或 raw robot response。
- KR-O2O3-Same-Evidence-Ref：intake/gate 必须把 device/PWA materials、route/elevator materials、Nav2/fixed-route runtime log、task record、completion signal、dropoff/cancel result 都绑定到同一 safe `evidence_ref`；缺失或 mismatch 必须 fail closed。
- KR-Robot-Metadata-Only：Robot diagnostics 可以消费 intake summary，但只作为 metadata-only support surface；不得改变 command、ACK、control、cursor、Nav2、HIL、dropoff/cancel completion 或 delivery success。
- KR-Closeout：后续工程完成后 Product Owner 更新 `OKR.md`、`docs/process/okr_progress_log.md` 和 sprint closeout docs；若只有软件 intake/gate，证据边界保持 `software_proof_docker_mobile_field_material_intake_gate`，不推进 Objective 5。

## 4. 本轮核心抓手

`mobile_field_material_intake`：一个 phone-safe material intake surface + Robot diagnostics metadata-only consumer + `pc-tools` fail-closed gate。它从 06-07 `mobile_route_elevator_field_device_precheck` 接过真实材料清单，并将待补证据拆成可回填、可校验、可复账的 same-evidence-ref items。

默认证据边界：`software_proof_docker_mobile_field_material_intake_gate`。

默认保守状态：

- `real_device_observed=false`
- `pwa_install_prompt_observed=false`
- `route_elevator_field_pass=false`
- `nav2_fixed_route_runtime_observed=false`
- `dropoff_completion=false`
- `cancel_completion=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `not_proven` 包含真实手机、真实 route/elevator field pass、Nav2/fixed-route、dropoff/cancel completion、delivery success、HIL、Objective 5 external proof。

## 5. 需要做什么

1. Full-stack：在 `mobile/web` 增加 first-screen `mobile_field_material_intake` panel，消费或派生 safe intake summary，支持 whitelist copy/export；更新 fixture、targeted entrypoint test 和 `docs/product/mobile_user_flow.md`。
2. Robot：在 `operator_gateway_diagnostics.py` 与诊断 unittest 中补 `mobile_field_material_intake` metadata-only summary 消费，更新 `docs/interfaces/ros_contracts.md`；确保 intake 不影响 control/ACK/command semantics。
3. Autonomy：新增 `pc-tools/evidence/mobile_field_material_intake.py` 和 unittest，提供 fail-closed intake/gate；更新 `pc-tools/README.md` 与 `docs/navigation/fixed_route_workflow.md`。
4. Product：后续 closeout 更新 `OKR.md`、`docs/process/okr_progress_log.md`、`tech-done.md`、`side2side_check.md`、`final.md`；本轮只完成 planning docs。

## 6. 优先级和验收口径

P0：

- 手机首屏可见 `mobile_field_material_intake`。
- copy/export 包通过 whitelist 过滤，包含 safe entry、safe `evidence_ref`、真实设备/PWA observation items、route/elevator materials、same-evidence-ref status、`not_proven`、`delivery_success=false`。
- Start / Confirm Dropoff / Cancel 不因 intake 变为 enabled。
- Robot diagnostics 只消费 metadata-only intake summary，不进入 command、ACK、control、cursor、Nav2、HIL 或 completion。
- `pc-tools/evidence` gate 对缺失、placeholder、evidence-ref mismatch、unsafe copy、success wording 必须 fail closed。

P1：

- `docs/product/mobile_user_flow.md`、`docs/interfaces/ros_contracts.md`、`docs/navigation/fixed_route_workflow.md` 和 `pc-tools/README.md` 同步说明用途、输入、输出和证据边界。
- 验证只做围栏：targeted unittest、py_compile、node check、scoped `rg`、scoped `git diff --check`；不跑无关大回归。

不得验收为完成：

- 不得声称真实手机、真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice。
- 不得声称真实 route/elevator field pass、真实 Nav2/fixed-route、真实 dropoff/cancel completion 或 delivery success。
- 不得声称 HIL、WAVE ROVER、真实串口/UART、Objective 5 external proof、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration。

## 7. 对应责任 Engineer

- Task A：`full-stack-software-engineer`，负责 `mobile/web/*`、fixture、mobile test、`docs/product/mobile_user_flow.md`。
- Task B：`robot-software-engineer`，负责 Robot diagnostics metadata-only consumer、diagnostics unittest、`docs/interfaces/ros_contracts.md`。
- Task C：`autonomy-engineer`，负责 `pc-tools/evidence/mobile_field_material_intake.py`、对应 unittest、`pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`。
- Task D：`product-okr-owner`，负责工程后 closeout 的 `OKR.md`、`docs/process/okr_progress_log.md` 和 sprint closeout docs。

## 8. 风险、阻塞和需要补齐的证据链

- O5 阻塞：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration 均缺失；本轮不消费该 blocker，不上调 O5。
- 真实设备阻塞：本机只有 Docker，本轮不证明真实手机、真实 PWA prompt/user choice 或 production app。
- 现场阻塞：没有真实 route/elevator field run、真实电梯门状态、真实目标楼层确认、真实人工协助记录、真实 Nav2/fixed-route runtime log、真实 task record、dropoff/cancel completion 或 delivery result。
- 硬件阻塞：没有真实 WAVE ROVER/UART/HIL、`T=1001` feedback、`/odom`、`/imu/data`、`/battery` 实机样本。
- 证据链补齐方向：后续必须把真实手机观察、PWA prompt/user choice、route/elevator field materials、Nav2/fixed-route runtime log、task record、completion signal、dropoff/cancel completion 和 delivery result 回填到同一 `evidence_ref`，再由 gate 输出是否仍 blocked。

## 9. 需要创建或更新的 sprint 文档

本轮 planning-only 创建：

- `sprints/2026.05.16_07-08_mobile-field-material-intake/pre_start.md`
- `sprints/2026.05.16_07-08_mobile-field-material-intake/prd.md`
- `sprints/2026.05.16_07-08_mobile-field-material-intake/tech-plan.md`

后续工程完成后必须继续更新：

- `sprints/2026.05.16_07-08_mobile-field-material-intake/tech-done.md`
- `sprints/2026.05.16_07-08_mobile-field-material-intake/side2side_check.md`
- `sprints/2026.05.16_07-08_mobile-field-material-intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

