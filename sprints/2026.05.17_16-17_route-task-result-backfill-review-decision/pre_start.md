# Sprint 2026.05.17_16-17 Route Task Result Backfill Review Decision - Pre Start

sprint_type: epic

## 1. 开工结论

本轮启动 `route_task_field_retest_result_backfill_review_decision` Epic sprint，接在 `2026.05.17_15-16_route-task-result-acceptance-backfill` 之后。目标不是继续堆测试或本地 metadata wrapper，而是把上一轮 backfill artifact / summary 转成可执行的 review decision：`accepted`、`missing`、`rejected` material status、`owner_handoff`、`next_required_evidence` 和 `rerun_commands`，并让 Robot diagnostics 与 `mobile/web` 只读展示。

本轮证据边界固定为 `software_proof_docker_route_task_field_retest_result_backfill_review_decision_gate`。所有 artifact、diagnostics 和 phone-safe summary 必须保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. 背景证据

- `OKR.md` 4.1 在 2026-05-17 15:18 显示 Objective 5 约 68%，仍是数值最低 Objective；但当前 Docker-only 主机没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 证据。因此本轮不能继续包装 Objective 5 metadata wrapper，也不能把本地软件证明写成 O5 external proof。
- 最新 sprint `2026.05.17_15-16_route-task-result-acceptance-backfill` 已完成 `software_proof_docker_route_task_field_retest_result_acceptance_backfill_gate`，把 acceptance packet 后续材料回填入口打通。Objective 2 / Objective 3 保守推进到约 96%，但剩余风险仍是缺真实 route/elevator field pass、真实 Nav2/fixed-route、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff/cancel completion 和 delivery_result。
- PR #4 已把 elevator-assisted delivery 设为主线必须能力，因此 route/elevator 现场材料链不能停在 intake/backfill，应继续进入 review decision，让下一次真实材料补录、退回或分派有明确决策层。
- PR #5 review 指出 production hardware boundary 默认硬件与 mandatory sensor baseline 矛盾、OKR lowest narrative drift、mandatory sensor assumptions 缺本地 vendor/source citation。由于本机没有真实 2D LiDAR / ToF source、receipt、采购、安装、接线、电源、标定或 HIL-entry 材料，本轮不继续包装 PR #5 hardware blocker。
- 本机没有真实硬件，只有 Docker。所有本轮输出必须保持 software proof / not proven；不得宣称真实 route/elevator field pass、HIL、真实手机/browser、O5 external proof 或 delivery success。

## 3. 用户价值和产品北极星

用户价值：让普通手机用户和现场支持人员不需要读 raw artifact，也能知道一次 route/elevator result backfill 到底哪些材料可接受、哪些缺失、哪些被退回、下一步归谁补、应该重跑哪条命令。

产品北极星：继续服务低成本 ROS2 垃圾投递机器人闭环。小车必须把送垃圾、电梯 assisted delivery、现场材料补录和失败复盘变成可复核的交付链，而不是只留下离散脚本或无法判断的测试输出。

## 4. OKR 映射

- Objective 2：把 route/elevator task result backfill 转成决策层，明确 door state、target floor confirmation、human assistance note、dropoff/cancel completion、delivery result 等材料的 accepted/missing/rejected 状态，推动送垃圾任务闭环的现场复核链。
- Objective 3：把 Nav2/fixed-route runtime log、route completion signal、task record 与同一 `evidence_ref` 的材料状态接入 review decision，推动固定路线与导航证据从回填入口走向现场复核决策。
- Objective 4：Robot diagnostics 与 `mobile/web` 只读展示 review decision、owner handoff 和 rerun commands，帮助普通用户/支持人员理解下一步，不改变 Start / Confirm Dropoff / Cancel gating。
- Objective 5：不作为本轮推进目标。缺真实 external proof 时，继续本地 O5 metadata wrapper 不会提升真实云中转产品化。

## 5. KR 拆解

- KR-A：Autonomy 产出 PC gate `route_task_field_retest_result_backfill_review_decision`，只读上一轮 backfill artifact / summary，生成 review artifact / summary。
- KR-B：Robot diagnostics 只读消费 review decision summary，fail closed，并保持 task_orchestrator / action / Start / Dropoff / Cancel 控制语义不变。
- KR-C：Full-stack 在 `mobile/web` 增加只读“路线任务回填复核决策”面板，展示 safe summary、material status、owner handoff、next required evidence、rerun commands 和边界。
- KR-D：Product 完成 sprint 留档、收口验收与 OKR 更新准备，确保 `docs/` 相关产品文档在实现完成后同步反映本轮新增 review decision surface。

## 6. 本轮核心抓手

核心抓手是“决策层”，不是“再补一个测试层”。上一轮已经能判断材料回填入口；本轮要把 backfill 结果转成可执行的 review decision，让下一次现场材料补录能够直接按 accepted / missing / rejected / owner handoff / rerun commands 处理。

## 7. 需要做什么

1. 新增 PC evidence gate，输入上一轮 `route_task_field_retest_result_acceptance_backfill` artifact 或 summary，输出 `trashbot.route_task_field_retest_result_backfill_review_decision.v1` 和 summary。
2. 在 Robot diagnostics 中只读显示 review decision summary，支持 file/env/top-level/nested summary，缺失或不安全内容 fail closed。
3. 在 `mobile/web` 中只读展示 review decision，copy/export 只允许白名单 safe fields，禁止 raw artifact、local path、checksum、traceback、ROS topic、serial/UART、credentials 和成功/控制文案。
4. Product closeout 时更新当前 sprint 的 `tech-done.md`、`side2side_check.md`、`final.md`，并按真实完成情况决定是否更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。

## 8. 优先级和验收口径

P0 验收：

- evidence boundary 必须是 `software_proof_docker_route_task_field_retest_result_backfill_review_decision_gate`。
- 输出必须包含 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- review decision 必须覆盖 accepted / missing / rejected material status、owner handoff、next required evidence 和 rerun commands。
- Robot diagnostics 与 mobile/web 只能只读展示，不得改变控制动作授权。
- scoped validation 必须通过：`py_compile`、focused unittest、CLI `--help`、`node --check`、required `rg` 和 scoped `git diff --check`。

P1 验收：

- safe copy / copy export 缺失时 fail closed。
- same `evidence_ref` mismatch、unsupported schema/boundary、success claim、`delivery_success=true` 或 `primary_actions_enabled=true` 必须被 review decision 标成 blocked/rejected。

## 9. 对应责任 Engineer

- `autonomy-engineer`：PC evidence gate、artifact / summary schema、focused unittest、CLI help。
- `robot-software-engineer`：Robot diagnostics 只读 consumer、diagnostics unittest、ROS contract 文档同步。
- `full-stack-software-engineer`：`mobile/web` 只读面板、fixture、mobile tests、产品用户流程文档同步。
- `product-okr-owner`：sprint 留档、验收收口、OKR 更新准备、证据边界审查。

## 10. 风险、阻塞和需要补齐的证据链

- 当前仍缺真实 route/elevator field pass、真实 Nav2/fixed-route、真实 route completion signal、真实 task record、door_state、target_floor_confirmation、human_assistance_note、dropoff/cancel completion、delivery_result 和 delivery success。
- 当前仍缺 WAVE ROVER、真实串口/UART、HIL、真实手机/browser、production app、Objective 5 external proof、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover。
- PR #5 的真实 2D LiDAR / ToF source、receipt、采购、安装、接线、电源、标定、HIL-entry 材料仍不可得；本轮不消费该 blocker。
- 本轮只能证明 Docker/local software proof 的 review decision surface 可用，不能提升真实现场或硬件完成度。

## 11. 需要创建或更新的 sprint 文档

本轮 planning worker 创建：

- `sprints/2026.05.17_16-17_route-task-result-backfill-review-decision/pre_start.md`
- `sprints/2026.05.17_16-17_route-task-result-backfill-review-decision/prd.md`
- `sprints/2026.05.17_16-17_route-task-result-backfill-review-decision/tech-plan.md`

实现与收口阶段后续必须更新：

- `sprints/2026.05.17_16-17_route-task-result-backfill-review-decision/tech-done.md`
- `sprints/2026.05.17_16-17_route-task-result-backfill-review-decision/side2side_check.md`
- `sprints/2026.05.17_16-17_route-task-result-backfill-review-decision/final.md`
