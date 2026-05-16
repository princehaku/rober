# Sprint 2026.05.16_21-22 Route Task Field Retest Session Handoff - Pre Start

sprint_type: epic

## 1. 开工结论

本轮启动 `route_task_field_retest_session_handoff` Epic sprint，目标是把上一轮 `route_task_field_retest_execution_pack` 转成下一次现场 session handoff artifact / summary、Robot diagnostics metadata-only consumer、mobile/web 只读 panel，并明确现场同学如何用同一 `evidence_ref` 回填真实材料。

本轮仍然是 `software_proof_docker_route_task_field_retest_session_handoff_gate`。统一边界必须保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`，不得宣称真实 field pass、真实 fixed-route/Nav2、真实电梯、真实投放或真实手机/browser 通过。

## 2. 用户价值和产品北极星

用户价值：现场复测不再停在“执行包已经生成”，而是有一份可交接的 session handoff：谁在现场执行、要带走哪些真实材料、哪些命令/材料必须沿用同一 `evidence_ref`、回填到哪里、什么仍然不能算通过。手机端和 diagnostics 只能展示只读交接状态，避免普通用户把 software proof 误解成真实送达。

产品北极星：继续服务“普通手机用户能理解、现场同学能复测、证据能复盘”的低成本 ROS2 自主垃圾投递机器人。当前抓手不是扩展云端或硬件 wrapper，而是把 Objective 2 / Objective 3 的 route-task field retest 链推进到可现场交接、可按同一证据号回填真实材料的状态。

## 3. OKR 映射

- Objective 2：可送垃圾任务 + 电梯 assisted delivery 必达闭环。本轮聚焦同一 `evidence_ref` 的真实 task record、route completion signal、dropoff/cancel completion、delivery result、门状态、目标楼层确认和人工协助记录回填路径。
- Objective 3：可验证导航与固定路线能力。本轮聚焦真实 Nav2/fixed-route runtime log、固定路线执行材料、route completion signal 和现场 session summary 的复测交接。
- Objective 4：手机用户体验支撑项。mobile/web 只读 panel 只解释 session handoff 和缺口，不改变 Start / Confirm Dropoff / Cancel gating。
- Objective 5：当前数值最低，约 66%，但本机只有 Docker。`OKR.md` 第 6 节明确需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 等外部材料才能继续推进 Objective 5 completion，因此本轮不再堆本地 O5 metadata wrapper。

## 4. 近期证据

- `OKR.md` 4.1 最新快照显示 Objective 5 约 66% 数值最低，但下一步 O5 需要真实外部云/4G/OSS/CDN/DB/queue/worker evidence；Docker-only 主机无法提供。
- `sprints/2026.05.16_20-21_route-task-field-retest-execution-pack/final.md` 已完成 `software_proof_docker_route_task_field_retest_execution_pack_gate`，O2/O3/O4 保守推进到 81/81/90；剩余缺口是真实 Nav2/fixed-route runtime log、route completion signal、task record、真实电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result、WAVE ROVER/UART/HIL、真实手机/browser 和 Objective 5 external proof。
- `sprints/2026.05.16_19-20_route-task-terminal-review-decision/final.md` 已把 terminal rehearsal 转成 review decision、owner handoff、next required evidence 和 field retest request guidance。
- PR #4 已把 elevator-assisted delivery 写成主线必须能力，因此 route-task session handoff 必须包含电梯门状态、目标楼层确认和人工协助材料的现场交接，不再把电梯作为可选 H2 支线。
- PR #5 review 曾指出 default hardware set 与 mandatory sensor baseline 矛盾、OKR lowest-objective claim drift、mandatory sensor assumptions 缺 vendor source。`2026.05.16_17-18_hardware-baseline-source-alignment` 与 `2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck` 已连续两轮消费该硬件/source/config blocker；按 `AGENTS.md` 同一 blocker 红线，本轮必须切换 Objective，而不是第三次继续硬件 blocker wrapper。

## 5. 本轮核心抓手

把 execution pack 推进为 session handoff，不扩大证据边界：

- 产出 PC-side `route_task_field_retest_session_handoff` artifact / summary，记录同一 `evidence_ref`、现场责任人、回填材料清单、运行命令、材料位置和 fail-closed 边界。
- Robot diagnostics 只消费 metadata-only summary，任何缺失、证据号不一致、成功措辞或弱边界都 fail closed。
- mobile/web 展示只读“现场复测交接” panel，只允许 whitelist-safe copy，不暴露 raw artifacts、ROS topic、`/cmd_vel`、串口/UART、凭证、路径、checksum 或成功控制文案。
- Product closeout 在 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md` 中保守同步结果。

## 6. 责任 Engineer

- Task A Autonomy：Autonomy Algorithm Engineer。
- Task B Robot：Robot Platform Engineer。
- Task C Full-stack：User Touchpoint Full-Stack Engineer。
- Task D Product closeout：Product Manager / OKR Owner。

## 7. 风险、阻塞和证据链

- 真实材料仍缺：真实 Nav2/fixed-route runtime log、route completion signal、task record、真实电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result、WAVE ROVER/UART/HIL、真实手机/browser、Objective 5 external proof。
- 本机只有 Docker，本轮只能形成 `software_proof_docker_route_task_field_retest_session_handoff_gate`。
- 不触碰 PR #5 硬件/source/config blocker 第三轮 wrapper；若现场无法提供真实硬件/传感器材料，Objective 1 和相关 Objective 4 hardware baseline 不上调。
- 不触碰 Objective 5 external proof；没有公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 时，Objective 5 不上调。

## 8. 本轮需创建或更新的 sprint 文档

启动阶段创建：

- `sprints/2026.05.16_21-22_route-task-field-retest-session-handoff/pre_start.md`
- `sprints/2026.05.16_21-22_route-task-field-retest-session-handoff/prd.md`
- `sprints/2026.05.16_21-22_route-task-field-retest-session-handoff/tech-plan.md`

实现和收口阶段由 Task D 更新：

- `sprints/2026.05.16_21-22_route-task-field-retest-session-handoff/tech-done.md`
- `sprints/2026.05.16_21-22_route-task-field-retest-session-handoff/side2side_check.md`
- `sprints/2026.05.16_21-22_route-task-field-retest-session-handoff/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
