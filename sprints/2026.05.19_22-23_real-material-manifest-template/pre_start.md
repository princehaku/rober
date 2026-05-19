# Sprint 2026.05.19_22-23 Real Material Manifest Template - Pre Start

## 1. Sprint 类型和启动结论

- sprint_type: epic
- 目标：把上一轮 `real_material_evidence_intake` 的隐式 sample manifest 推进为 field-owner 可交付的 `manifest template` / submission pack。
- 本轮只启动规划三文档：`pre_start.md`、`prd.md`、`tech-plan.md`。后续实现、测试、修复和 closeout 必须交给对应 Engineer 子 agent 执行。
- 当前主机只有 Docker，没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、真实 WAVE ROVER/UART/HIL、真实手机设备或真实 route/elevator field pass。
- 证据边界必须保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## 2. 上轮证据和重复 blocker 核对

- `OKR.md` 4.1 在 2026-05-19 21:18 Asia/Shanghai 显示 Objective 5 约 68%，仍是数字最低；Objective 1 约 81%，是下一低项。
- `2026.05.19_20-21_real-material-readiness-board/final.md` 已完成四类真实材料缺口看板，但明确没有真实 external、硬件、route/elevator、手机或 HIL proof。
- `2026.05.19_21-22_real-material-evidence-intake/final.md` 已完成 `real_material_evidence_intake`，但明确它只证明 repo 内 intake、diagnostics 和 mobile 展示链路可 fail closed，不证明真实材料。
- 最近两轮 final 均确认不能再重复 local metadata wrapper；下一步必须让现场 owner 能按同一 safe `evidence_ref` 提交真实材料清单，再进入 review decision / handoff / execution pack。

## 3. 本轮核心抓手

把真实材料缺口从“系统知道缺什么”推进到“现场 owner 拿到统一模板后能提交什么”：

- Objective 5 external：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、worker/migration/cutover。
- Objective 1 / PR #5 hardware：真实 WAVE ROVER/UART/HIL packet、2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- PR #5 thread：`PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `blocked_pending_real_materials`，本轮不得写成 closeable。
- PR #4 route/elevator：Nav2/fixed-route runtime log、route completion signal、field task record、elevator door state、target floor confirmation、human assistance record、dropoff/cancel material、delivery_result。
- Objective 4 real phone：真实 iPhone/Android behavior、production app、PWA prompt/user choice、true phone/browser acceptance。

## 4. 用户价值和产品北极星

产品北极星：让普通手机用户最终能让小车可靠完成送垃圾任务，并且每次失败都能被现场 owner 用统一材料包复盘，而不是让团队继续猜测缺哪类真实证据。

本轮用户价值：

- 现场 owner 不需要理解 ROS2、GitHub PR thread 或每个 gate 的内部实现，也能按材料组填写同一 safe `evidence_ref`。
- Product / Engineer / Reviewer 能用同一 submission pack 判断材料是否足以推进 Objective 5、Objective 1 / PR #5、PR #4 route/elevator 或 Objective 4。
- Docker-only 主机继续保持保守边界，不把模板、样例或 intake 结果当成真实通过。

## 5. Owner 和启动边界

- Product Manager / OKR Owner：本轮只负责规划三文档，明确 KR、范围、验收口径和后续 owner 拆分。
- Hardware Infra Engineer：后续负责 O1 / PR #5 hardware material manifest、vendor source boundary 和 WAVE ROVER/UART/HIL material 字段，执行前必须读取 `docs/vendor/VENDOR_INDEX.md`。
- Autonomy Algorithm Engineer：后续负责 PR #4 route/elevator、Nav2/fixed-route、route completion、task record 和 delivery_result 材料字段。
- User Touchpoint Full-Stack Engineer：后续负责 field-owner submission pack 的 phone-safe / web-facing 展示或下载入口，不能改变 Start Delivery / Confirm Dropoff / Cancel gating。
- Robot Platform Engineer：后续负责 Robot diagnostics 只读消费 sanitized manifest template summary，不能引入控制授权。

## 6. 风险、阻塞和证据链缺口

- 最大风险：模板被误读为真实材料已到位。所有产物必须保留 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- O5 仍 blocked 在真实公网 HTTPS/TLS、4G/SIM、OSS/CDN、production DB/queue 和 worker/cutover。
- O1 仍 blocked 在真实 WAVE ROVER/UART/HIL、真实反馈包和 PR #5 2D LiDAR / ToF materials；`PRRT_kwDOSWB9286CJ3tX` 仍不得关闭。
- PR #4 route/elevator 仍 blocked 在真实路线、电梯、投放/取消和 delivery_result 材料。
- O4 仍 blocked 在真实手机、production app、真实 PWA prompt/user choice 和 true phone/browser acceptance。

## 7. 本轮需要创建或更新的 sprint 文档

- 创建 `sprints/2026.05.19_22-23_real-material-manifest-template/pre_start.md`。
- 创建 `sprints/2026.05.19_22-23_real-material-manifest-template/prd.md`。
- 创建 `sprints/2026.05.19_22-23_real-material-manifest-template/tech-plan.md`。
- 后续实现完成后必须继续补齐 `tech-done.md`、`side2side_check.md`、`final.md`，并由 closeout agent 更新 `OKR.md` 和相关 `docs/`。
