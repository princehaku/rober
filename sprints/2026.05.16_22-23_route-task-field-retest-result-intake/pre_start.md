# Sprint 2026.05.16_22-23 Route Task Field Retest Result Intake - Pre Start

sprint_type: epic

## 1. 开工结论

本轮启动 `route_task_field_retest_result_intake` Epic sprint，目标是把上一轮 `route_task_field_retest_session_handoff` 之后的真实现场复测结果材料，收敛成 future intake contract：PC gate 接收 artifact / summary / wrapper / nested JSON，校验同一 `evidence_ref`，检查八类结果材料摘要，并输出 Robot diagnostics 与 mobile/web 可消费的 phone-safe summary。

本轮仍然是 `software_proof_docker_route_task_field_retest_result_intake_gate`。统一边界必须保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`，不得宣称真实 field pass、真实 Nav2/fixed-route、真实电梯、真实投放、真实取消完成或真实手机/browser 通过。

## 2. 用户价值和产品北极星

用户价值：现场同学完成复测后，需要一个不会误报成功的材料入口，能把真实 Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff/cancel completion、delivery_result 等结果材料按同一 `evidence_ref` 回填。普通手机用户和支持同学只能看到安全摘要，知道哪些材料已提交、哪些仍缺、为什么还不能发车或宣称送达。

产品北极星：继续服务“普通手机用户能理解、现场支持能复测、证据链能复盘”的低成本 ROS2 自主垃圾投递机器人。本轮抓手不是堆 O5 本地 metadata，也不是第三次消费 PR #5 硬件/source/config blocker，而是把 Objective 2 / Objective 3 的现场复测结果 intake 口径变成可验证、可 fail-closed、可手机解释的合同。

## 3. OKR 映射

- Objective 2：可送垃圾任务 + 电梯 assisted delivery 必达闭环。本轮聚焦同一 `evidence_ref` 的 task record、door_state、target_floor_confirmation、human_assistance_note、dropoff/cancel completion、delivery_result 结果材料 intake。
- Objective 3：可验证导航与固定路线能力。本轮聚焦真实 Nav2/fixed-route runtime log、route completion signal 和 route/task result bundle 的结果材料 intake。
- Objective 4：手机用户体验支撑项。mobile/web 增加只读结果材料 panel，只解释 intake 状态和缺口，不改变 Start / Confirm Dropoff / Cancel gating。
- Objective 5：当前数值最低，约 66%，但本机只有 Docker。`OKR.md` 第 6 节明确需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 等外部材料才能继续推进 Objective 5 completion；本轮不再堆本地 O5 metadata depth。

## 4. 近期证据

- `OKR.md` 4.1 最新快照显示 Objective 5 约 66% 数值最低，但下一步 O5 需要真实外部云/4G/OSS/CDN/DB/queue/worker evidence；Docker-only 主机无法提供。
- GitHub PR #4 `Add elevator-assisted delivery capability to agents, registry and OKR` 已把 elevator-assisted delivery 写成主线必须能力，因此结果 intake 必须覆盖电梯门状态、目标楼层确认和人工协助材料。
- GitHub PR #5 `Make elevator-assisted delivery mandatory; update agents, OKR and hardware baseline` 已把单目 + 2D LiDAR + ToF 安全环、参数化传感器配置和证据链写成硬件/产品基线。
- `sprints/2026.05.16_21-22_route-task-field-retest-session-handoff/final.md` 已完成 `route_task_field_retest_session_handoff`，但仍缺真实 Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff/cancel completion、delivery_result。
- `sprints/2026.05.16_17-18_hardware-baseline-source-alignment` 与 `sprints/2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck` 已连续两轮消费 PR #5 硬件/source/config blocker；按 `AGENTS.md` 同一 blocker 最多消费 2 轮红线，本轮切换 Objective，不第三次继续硬件 blocker wrapper。

## 5. 本轮核心抓手

把 session handoff 推进为 result intake，不扩大证据边界：

- PC-side `route_task_field_retest_result_intake` 接收现场材料 artifact / summary / wrapper / nested JSON，校验同一 `evidence_ref` 和八类结果材料摘要。
- Robot diagnostics 只消费 metadata-only summary，任何缺失、证据号不一致、成功措辞或弱边界都 fail closed。
- mobile/web 展示只读“路线任务现场复测结果入口” panel，只允许 whitelist-safe copy，不暴露 raw artifacts、ROS topic、`/cmd_vel`、串口/UART、凭证、路径、checksum 或成功控制文案。
- Product closeout 在本轮结束后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`，并保守同步 OKR。

## 6. 责任 Engineer

- Task A Autonomy：Autonomy Algorithm Engineer。
- Task B Robot：Robot Platform Engineer。
- Task C Full-stack：User Touchpoint Full-Stack Engineer。
- Task D Product closeout：Product Manager / OKR Owner。

## 7. 风险、阻塞和证据链

- 真实材料仍缺：真实 Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff/cancel completion、delivery_result、WAVE ROVER/UART/HIL、真实手机/browser、Objective 5 external proof。
- 本机只有 Docker，本轮只能形成 `software_proof_docker_route_task_field_retest_result_intake_gate`。
- 不触碰 PR #5 硬件/source/config blocker 第三轮 wrapper；若现场无法提供真实硬件/传感器材料，Objective 1 和相关 Objective 4 hardware baseline 不上调。
- 不触碰 Objective 5 external proof；没有公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 时，Objective 5 不上调。

## 8. 本轮需创建或更新的 sprint 文档

启动阶段创建：

- `sprints/2026.05.16_22-23_route-task-field-retest-result-intake/pre_start.md`
- `sprints/2026.05.16_22-23_route-task-field-retest-result-intake/prd.md`
- `sprints/2026.05.16_22-23_route-task-field-retest-result-intake/tech-plan.md`

实现和收口阶段由 Task D 更新：

- `sprints/2026.05.16_22-23_route-task-field-retest-result-intake/tech-done.md`
- `sprints/2026.05.16_22-23_route-task-field-retest-result-intake/side2side_check.md`
- `sprints/2026.05.16_22-23_route-task-field-retest-result-intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
