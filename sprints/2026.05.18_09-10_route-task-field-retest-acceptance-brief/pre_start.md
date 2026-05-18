# Sprint 2026.05.18_09-10 Route Task Field Retest Acceptance Brief - Pre Start

sprint_type: epic

## 1. 启动结论

本轮启动 `route_task_field_retest_acceptance_brief` Epic sprint。目标不是继续包装 Objective 5 云证据、Objective 1 WAVE ROVER/HIL blocker 或 PR #5 硬件采购材料，而是把 PR #4 merged 后的 route/elevator assisted delivery 现场复测验收简报补成跨 PC evidence、Robot diagnostics、mobile/web 三端一致的 metadata-only software proof。

本轮只创建 planning 文档，后续实现必须由 Autonomy、Robot、Full-stack 三个 owner 并行子 agent 执行。Product Owner 本轮不修改 `OKR.md`、产品代码、测试代码、`docs/product/` 或其他 sprint。

## 2. 用户价值和产品北极星

用户价值：现场 operator / support user 在真实 route/elevator field materials 仍缺时，仍能从同一 safe `evidence_ref` 看到一份简明的现场复测验收 brief：入场前置条件、pass/fail criteria、required evidence packet、owner handoff 和 rerun note。这样现场团队知道该采什么、交给谁、如何判断是否可进入下一轮 material intake，而不会把 drill console 或 acceptance brief 误读成真实送达成功。

产品北极星保持不变：普通手机用户最终能把垃圾交给低成本 ROS2 小车，并在固定路线/电梯 assisted delivery 场景下可验证地完成送达。本轮只推进现场复测验收材料链路，不证明真实手机、真实电梯、真实 Nav2/fixed-route、真实投放或 delivery success。

## 3. OKR 映射

- Objective 5 当前约 68%，是 `OKR.md` 4.1 数字最低项；但本机只有 Docker，缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof，O5 stop rule 继续成立。本轮不消耗 O5 blocker。
- Objective 1 当前约 81%；最近 2026.05.17_20-21 到 23-24 已连续消费 WAVE ROVER/HIL 本地包装，当前仍无真实串口 `/dev/ttyUSB*`、`feedback_T1001`、`/odom`、`/imu`、`/battery` 或 operator HIL report。本轮不继续包装同一硬件 blocker。
- Objective 2 / Objective 3 / Objective 4 已接近 99%，但 PR #4 merged 后真实 route/elevator field materials 仍缺。本轮选取其中仍可 Docker-actionable 的 acceptance brief consistency gap，服务 Objective 2/O3 route/elevator field retest 证据链和 Objective 4 手机只读展示边界。
- PR #5 review 指出的 hardware baseline / 2D LiDAR / ToF / vendor-source 问题仍缺真实 SKU/source/receipt/install/wiring/calibration/HIL-entry 材料；本轮不做硬件材料包装。

## 4. 背景证据

- 最新 sprint `sprints/2026.05.18_08-09_route-task-field-retest-drill-console/final.md` 要求：若无 O5/O1 真实材料，继续 PR #4 route/elevator 真实材料回填路线。
- `docs/product/mobile_user_flow.md` 已声明 `route_task_field_retest_acceptance_brief` 可消费 `robot_diagnostics_route_task_field_retest_acceptance_brief_summary`。
- `mobile/web/app.js` 已读取 `route_task_field_retest_acceptance_brief`、`route_task_field_retest_acceptance_brief_summary` 和 `robot_diagnostics_route_task_field_retest_acceptance_brief_summary`，并保持 `software_proof_docker_route_task_field_retest_acceptance_brief_gate` 边界。
- Robot diagnostics 已有 acceptance brief summary 处理函数和 `route_task_field_retest_acceptance_brief` / `route_task_field_retest_acceptance_brief_summary` 输出，但仍需补齐 `robot_diagnostics_route_task_field_retest_acceptance_brief_summary` safe alias，避免 mobile/product contract 与 Robot 输出不一致。
- `pc-tools/evidence/test_route_task_field_retest_acceptance_brief.py` 存在，但顶层 `tests.test_route_task_field_retest_acceptance_brief` 入口缺失，导致 acceptance command 不利于稳定复用。

## 5. 本轮核心抓手

将 acceptance brief 从“PC gate 和 mobile 已声明”推进为“三端一致可验收”：

1. Autonomy 补齐顶层 unittest 入口和 PC evidence gate 文档/围栏引用，确保 `route_task_field_retest_acceptance_brief` 可用标准 `python3 -m unittest tests.test_route_task_field_retest_acceptance_brief` 运行。
2. Robot 补齐 `robot_diagnostics_route_task_field_retest_acceptance_brief_summary` alias，并保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
3. Full-stack 验证 mobile/web 只读消费 Robot alias 的默认 blocked/not_proven、safe copy、copy/export 白名单和按钮 gating 不被 acceptance brief 放开。

## 6. 优先级和验收口径

优先级 P0：跨端 contract 一致性。验收条件是 PC gate、Robot diagnostics、mobile/web 都能围绕同一 `route_task_field_retest_acceptance_brief` summary 工作，并且不产生真实 field pass、HIL、delivery success 或 Objective 5 external proof 表述。

优先级 P1：验证围栏最小化。只跑 `py_compile`、聚焦 unittest、`node --check`、聚焦 mobile unittest、必要 `rg` 和 scoped `git diff --check`，不新增大测试堆。

优先级 P2：sprint 留档真实推进。实现完成后只创建后续阶段文档：`tech-done.md`、`side2side_check.md`、`final.md`；本轮规划阶段不得预生成这些文档。

## 7. 对应责任 Engineer

- Autonomy Algorithm Engineer：负责 `pc-tools/evidence/` acceptance brief gate 的顶层测试入口、readme/contract 小幅同步和围栏验证。
- Robot Platform Engineer：负责 `operator_gateway_diagnostics.py` acceptance brief Robot alias、diagnostics 测试和 fail-closed payload 验证。
- User Touchpoint Full-Stack Engineer：负责 `mobile/web` 只读消费、fixture/test 适配和按钮 gating 验证。

Hardware Infra Engineer 不参与本轮实现；PR #5 硬件材料真实缺口保留为后续独立 sprint，避免在缺 SKU/source/receipt/install/wiring/calibration/HIL-entry 时继续包装。

## 8. 风险、阻塞和需要补齐的证据链

- 真实 O5 external proof 仍缺，不能用本轮 software proof 推动 Objective 5。
- 真实 WAVE ROVER/HIL 仍缺，不能用本轮 acceptance brief 推动 Objective 1。
- 真实 route/elevator field materials 仍缺：门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion 和 delivery result。
- 本轮只允许输出 `software_proof_docker_route_task_field_retest_acceptance_brief_gate`；所有状态必须保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 若实现阶段发现现有代码已部分满足缺口，Engineer 仍需用聚焦验证证明当前 contract，并只补最小缺失项。

## 9. 本轮 sprint 文档

本轮规划阶段创建：

- `sprints/2026.05.18_09-10_route-task-field-retest-acceptance-brief/pre_start.md`
- `sprints/2026.05.18_09-10_route-task-field-retest-acceptance-brief/prd.md`
- `sprints/2026.05.18_09-10_route-task-field-retest-acceptance-brief/tech-plan.md`

本轮规划阶段不得创建：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
