# Sprint 2026.05.16_06-07 Mobile Route Elevator Field Device Precheck - PRD

sprint_type: epic

## 1. 用户价值和产品北极星

用户价值：真实手机/现场验收前，现场操作者需要一份能在手机上读取、复制、导出、交给后续现场回填的 precheck/intake 包。它要告诉操作者当前 `mobile/web` 入口是否可用、route/elevator handoff summary 关联哪个安全 `evidence_ref`、真实设备/PWA 需要观察什么、现场 route/elevator 需要补哪些材料，以及当前哪些仍是 not_proven。

产品北极星：普通手机用户可以安全发起前置检查和材料交接，但不会因为一个本地 browser proof 或 handoff metadata 误以为机器人已经完成真实送达。`mobile_route_elevator_field_device_precheck` 是 Objective 4 的真实设备验收入口，也是 Objective 2/O3 现场材料准备的只读支撑，不是控制授权。

## 2. OKR 映射

- Objective 4：主目标。把真实设备验收入口从“已有多个只读面板”收敛为一个 first-screen precheck/export/intake 组合，明确真实手机、PWA prompt/user choice、设备观察项和 fail-closed 控制边界。
- Objective 2：支撑目标。把 route/elevator field session 的门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result 等现场材料列成同一 `evidence_ref` 的 precheck 清单，但不证明真实送达。
- Objective 3：支撑目标。把 Nav2/fixed-route runtime log、route completion signal、task record、现场回填材料作为 pre-field checklist，帮助后续路线证据回填。
- Objective 5：不推进。当前缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration；本轮不应写成 O5 external proof。
- Objective 1：不推进。没有真实 WAVE ROVER、UART、`T=1001` feedback、真实串口或 HIL。

## 3. KR 拆解或更新

- KR-O4-Device-Precheck：手机 first-screen 展示 `mobile_route_elevator_field_device_precheck` 状态、entry URL / safe entry summary、device/PWA observation checklist、route/elevator handoff reference、copy/export 状态和 `not_proven`。
- KR-O4-Whitelist-Export：导出包只允许 phone-safe 字段，不包含 token、Authorization、OSS AK/SK、root password、DB/queue URL、ROS topic、`/cmd_vel`、serial、WAVE ROVER 参数、本机路径、traceback、checksum、完整 evidence 文件或 raw robot response。
- KR-O2O3-Field-Materials：precheck summary 明确 same-evidence-ref 要求、真实 route/elevator field materials 清单、dropoff/cancel completion 仍缺、`delivery_success=false`。
- KR-Control-Fence：precheck metadata 不进入 command、ACK、remote control、cursor、persistence、Nav2、HIL、dropoff/cancel completion 或 delivery success；Start / Confirm Dropoff / Cancel 保持 fail-closed。
- KR-Closeout：工程完成后 Product Owner 更新 `OKR.md`、`docs/process/okr_progress_log.md` 和 sprint 收口文档；若只有软件 precheck 证据，最多保守推动 Objective 4，不上调 Objective 5。

## 4. 本轮核心抓手

`mobile_route_elevator_field_device_precheck`：一个 phone-safe precheck/export/intake 包，组合 current `mobile/web` 入口、route/elevator handoff summary、真实设备/PWA 观察项和现场材料清单。它的默认 evidence boundary 应保持 `software_proof_docker_mobile_route_elevator_field_device_precheck_gate`，默认 `real_device_observed=false`、`pwa_install_prompt_observed=false`、`route_elevator_field_pass=false`、`dropoff_completion=false`、`cancel_completion=false`、`delivery_success=false`、`primary_actions_enabled=false`。

## 5. 需要做什么

1. Full-stack 在 `mobile/web` first-screen 增加只读 precheck panel，支持 whitelist copy/export，并更新 fixture、targeted mobile smoke 和 `docs/product/mobile_user_flow.md`。
2. Robot 在 diagnostics / remote protocol contract 上补 metadata-only fence，确保 precheck summary 只能作为 phone/support metadata，不能改变 `/api/collect`、dropoff、cancel、ACK、cursor、Nav2 或控制链路。
3. Autonomy 在 `pc-tools/evidence` 增加 helper/gate，生成或校验 route+elevator+device precheck summary，输出 software proof / not_proven，用于现场前检查。
4. Product 在 closeout 后更新 `OKR.md`、`docs/process/okr_progress_log.md`、`tech-done.md`、`side2side_check.md`、`final.md`，并明确本轮是否只推动 Objective 4，或只读支撑 Objective 2/O3。

## 6. 优先级和验收口径

P0：

- 手机 first-screen 可见 `mobile_route_elevator_field_device_precheck` panel。
- copy/export 包通过 whitelist 过滤，包含安全 entry、safe `evidence_ref`、device/PWA observation checklist、route/elevator field materials、`not_proven` 和 `delivery_success=false`。
- Start / Confirm Dropoff / Cancel 不因 precheck 变为 enabled。
- Robot diagnostics / remote protocol 明确 precheck metadata-only，不进入 command/ACK/control。
- `pc-tools/evidence` helper/gate 能生成或校验 summary，并显式输出 software proof / not_proven。

P1：

- `docs/product/mobile_user_flow.md` 和接口/导航相关文档同步说明 precheck 用途和边界。
- targeted unit / py_compile / node check / scoped browser or CLI gate 通过，若本机缺浏览器或真实设备则记录 blocked-by-design。

不得验收为完成：

- 不得声称真实手机、真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice。
- 不得声称真实 route/elevator field pass、真实 Nav2/fixed-route、真实 dropoff/cancel completion 或 delivery success。
- 不得声称 HIL、WAVE ROVER、真实串口/UART、Objective 5 external proof、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration。

## 7. 对应责任 Engineer

- Task A：`full-stack-software-engineer`，负责移动端 first-screen panel、whitelist copy/export、fixture/test/doc。
- Task B：`robot-software-engineer`，负责 diagnostics/remote protocol metadata-only fence 或 docs/interfaces fence。
- Task C：`autonomy-engineer`，负责 `pc-tools/evidence` helper/gate 和 route+elevator+device summary。
- Task D：`product-okr-owner`，负责 closeout 后 OKR、okr_progress_log 和 sprint 收口文档。

## 8. 风险、阻塞和需要补齐的证据链

- O5 阻塞：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration 均缺失，本轮不得通过本地 metadata 消费该 blocker。
- 真实设备阻塞：本机只有 Docker，本轮不可能证明真实手机、真实 PWA prompt/user choice 或 production app。
- 现场阻塞：没有真实 route/elevator field run、真实电梯门状态、真实目标楼层确认、真实人工协助记录、真实 Nav2/fixed-route runtime log、真实 task record、dropoff/cancel completion 或 delivery result。
- 硬件阻塞：没有真实 WAVE ROVER/UART/HIL、`T=1001` feedback、`/odom`、`/imu/data`、`/battery` 实机样本。
- 证据链补齐方向：后续必须把真实手机观察、PWA prompt/user choice、route/elevator field materials、Nav2/fixed-route runtime log、task record、completion signal、dropoff/cancel completion 和 delivery result 回填到同一 `evidence_ref`。

## 9. 需要创建或更新的 sprint 文档

本轮启动阶段创建：

- `sprints/2026.05.16_06-07_mobile-route-elevator-field-device-precheck/pre_start.md`
- `sprints/2026.05.16_06-07_mobile-route-elevator-field-device-precheck/prd.md`
- `sprints/2026.05.16_06-07_mobile-route-elevator-field-device-precheck/tech-plan.md`

工程完成后必须继续更新：

- `sprints/2026.05.16_06-07_mobile-route-elevator-field-device-precheck/tech-done.md`
- `sprints/2026.05.16_06-07_mobile-route-elevator-field-device-precheck/side2side_check.md`
- `sprints/2026.05.16_06-07_mobile-route-elevator-field-device-precheck/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
