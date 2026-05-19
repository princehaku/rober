# Sprint 2026.05.19_18-19 Mobile Real Device Acceptance Callback Review Decision - PRD

## 1. 用户价值和产品北极星

用户价值：现场 owner 在上一轮 callback intake 回填真实手机验收执行材料后，需要一个面向手机端和 Robot diagnostics 的只读复核决策，明确材料是否 received、missing 或 rejected，为什么仍 not proven，下一步需要补什么证据，由谁接手，以及是否需要 rerun。

产品北极星：普通手机用户不接触命令行、ROS2、串口、云凭证或硬件调试，也能完成送垃圾任务并理解失败时下一步。本轮只把真实手机验收执行回调从 intake 推进到 review decision，不把 software proof 写成真实手机验收通过。

## 2. 背景和问题

上一轮 `mobile_real_device_field_trial_acceptance_execution_callback_intake` 已经让 mobile/web 与 Robot diagnostics 展示 accepted / missing / rejected callback evidence、same safe `evidence_ref`、owner handoff、next_required_evidence 和 rerun_guidance。

当前缺口是：intake 状态还没有被转译成产品化的复核决策。现场 owner 看到 accepted / missing / rejected 后，仍缺一个统一的只读决策面来说明：

- 是否可以进入后续真实现场验收复账。
- 哪些材料仍缺失或被拒绝。
- 是否需要继续由现场 owner 重新采集。
- 为什么当前仍是 `software_proof` / `not_proven`。
- 为什么 Start Delivery、Confirm Dropoff、Cancel 仍不能因此解锁。

## 3. OKR 映射

- Objective 4：主映射。补齐真实手机验收材料链路的 review decision，让手机体验和低成本量产验收边界更清楚。
- Objective 5：不推进。仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 external proof。
- Objective 1：不推进。PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved，仍缺真实 2D LiDAR / ToF material、WAVE ROVER/UART/HIL 和 operator HIL evidence。
- Objective 2 / Objective 3：不推进。真实 route/elevator field pass、Nav2/fixed-route、route completion signal、task record、dropoff/cancel completion 和 delivery result 仍缺。

## 4. KR 拆解或更新

### KR-A Review Decision Contract

新增 canonical feature id：

- `mobile_real_device_field_trial_acceptance_execution_callback_review_decision`

必须消费上一轮 callback intake 的 received / missing / rejected 状态，并输出：

- `review_decision`
- source callback intake status
- safe `evidence_ref`
- accepted / missing / rejected callback materials summary
- decision reasons
- `owner_handoff`
- `next_required_evidence`
- `rerun_guidance`
- `software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

### KR-B Mobile Read-Only Panel

mobile/web 必须新增只读 review decision panel，展示复核决策、缺口、责任 owner 和 rerun guidance。缺 summary、schema mismatch、unsafe evidence_ref、成功/控制暗示、raw artifact 或 credentials 必须 fail closed。

### KR-C Robot Diagnostics Safe Alias

Robot diagnostics 必须新增 safe summary alias：

- `robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary`

该 alias 只能输出 phone-safe metadata，不能触发 ACK、cursor、Start Delivery、Confirm Dropoff、Cancel、diagnostics fetch 或 robot command。

### KR-D Product Closeout

实现完成后 Product 负责补齐 `tech-done.md`、`side2side_check.md`、`final.md`，并在 `OKR.md` 与 `docs/process/okr_progress_log.md` 中保守记录证据边界。无真实手机材料时不得提高 OKR 百分比。

## 5. 本轮核心抓手

核心抓手是把 callback intake 从“材料接收状态”推进为“复核决策状态”，但所有输出保持 read-only 和 fail-closed。产品上要让下一步行动更明确，工程上不扩大控制面，不新增云、硬件或路线能力声明。

## 6. 需要做什么

- Full-Stack：在 mobile/web 增加 `mobile_real_device_field_trial_acceptance_execution_callback_review_decision` 的只读展示、fixture 和 targeted tests，并同步 `docs/product/mobile_user_flow.md`。
- Robot：在 operator gateway diagnostics 增加 review decision safe alias、summary schema、targeted unittest，并同步接口文档。
- Product：收口阶段复核所有文案和 evidence boundary，确保 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` 没有被弱化。

## 7. 优先级和验收口径

优先级：P0。本轮是上一轮 callback intake 的直接后续，完成后现场 owner 才能看到材料回调的复核结果和下一步补证路径。

验收口径：

- 手机端能展示 callback review decision，但不解锁 Start Delivery、Confirm Dropoff、Cancel。
- Robot diagnostics 能输出同名 safe summary alias，但不暴露 raw artifact 或控制路径。
- received / missing / rejected 必须被转成明确 review decision、decision reasons、owner_handoff、next_required_evidence 和 rerun_guidance。
- 所有缺字段、unsafe evidence_ref、schema mismatch、success/control copy、raw ROS topic、`/cmd_vel`、serial/UART、credentials、local path、complete artifact 或 checksum 都 fail closed。
- 验证只跑围栏化命令，不跑 Docker/Humble 或 broad suite。

## 8. 对应责任 Engineer

- User Touchpoint Full-Stack Engineer：mobile/web、fixtures、targeted tests、`docs/product/mobile_user_flow.md`。
- Robot Platform Engineer：operator gateway diagnostics、targeted diagnostics unittest、diagnostics/interface docs。
- Product Manager / OKR Owner：sprint closeout、OKR / progress log 证据边界、最终验收。

## 9. 风险、阻塞和证据链

- 当前主机 Docker-only，没有真实硬件或真实手机设备。
- 本轮不能证明真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice 或 true phone/browser acceptance。
- 本轮不能证明 Objective 5 external proof：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover。
- 本轮不能关闭 PR #5 `PRRT_kwDOSWB9286CJ3tX`，也不能证明真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- 本轮不能证明 WAVE ROVER/UART/HIL、真实 route/elevator field pass、Nav2/fixed-route、dropoff/cancel completion 或 delivery success。

## 10. 需要创建或更新的 sprint 文档

本计划阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实现和收口阶段必须继续更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

