# Sprint 2026.05.18_09-10 Route Task Field Retest Acceptance Brief - PRD

## 1. 产品问题

PR #4 已把 elevator assisted delivery 要求并入主链，上一轮 drill console 已把现场演练清单展示到 PC、Robot diagnostics 和 mobile/web，但 acceptance brief 仍存在跨端契约断点：mobile/product flow 声明可消费 `robot_diagnostics_route_task_field_retest_acceptance_brief_summary`，Robot diagnostics 输出仍需补齐对应 safe alias；PC evidence gate 测试也缺顶层 `tests.test_route_task_field_retest_acceptance_brief` 入口。

这个断点会让现场复测团队在进入真实 route/elevator 材料回填前，无法用一致命令和一致 diagnostics key 验收“本次 acceptance brief 到底准备好没有”。产品风险不是功能不可见，而是多个表面各自为政，导致现场回填材料继续缺门状态、楼层确认、人工协助、Nav2/fixed-route runtime log、task record 或 dropoff/cancel completion。

## 2. 用户价值和北极星

用户价值：field operator 能在手机和 diagnostics 中看到同一份 acceptance brief，明确真实复测时必须采集哪些材料、哪些条件算 pass/fail、哪些 owner 负责补齐，而不会被 raw artifact、ROS topic、串口、WAVE ROVER 细节或云凭证污染。

北极星：让普通手机用户最终能完成一次低成本 trash delivery；本轮只是给真实现场 route/elevator 复测铺设验收简报，不是交付真实送达闭环。

## 3. OKR 映射

- Objective 2：把 PR #4 route/elevator assisted delivery 的现场复测验收口径接到主链，服务门状态、目标楼层确认、人工协助记录、dropoff/cancel completion 与 delivery result 后续回填。
- Objective 3：把 Nav2/fixed-route runtime log、route completion signal、task record 这些固定路线证据要求明确纳入 acceptance brief。
- Objective 4：让 mobile/web 以只读、phone-safe 的方式消费 `robot_diagnostics_route_task_field_retest_acceptance_brief_summary`，不暴露 raw JSON、ROS topic 或控制入口。
- Objective 5：不推进。Objective 5 数字最低但缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof。
- Objective 1：不推进。Objective 1 仍缺真实 WAVE ROVER/HIL 串口和 feedback evidence，且最近多轮已消费同一 blocker。

## 4. KR 拆解

KR-A Autonomy：`route_task_field_retest_acceptance_brief` 的 PC evidence gate 可由顶层 unittest 入口运行，仍只接受 drill console artifact/summary/wrapper，输出 `software_proof_docker_route_task_field_retest_acceptance_brief_gate`。

KR-B Robot：diagnostics payload 同时输出 `route_task_field_retest_acceptance_brief`、`route_task_field_retest_acceptance_brief_summary`、`robot_diagnostics_route_task_field_retest_acceptance_brief_summary` 三个 safe alias，并在缺输入、坏 schema、unsafe copy、证据号不一致、enabled actions 或 success wording 时 fail closed。

KR-C Full-stack：mobile/web 可从 `/api/status`、`phone_readiness`、`/api/diagnostics`、nested diagnostics summary 或 Robot alias 读取 acceptance brief，展示 blocked/not_proven safe copy、pass/fail criteria、required evidence packet、owner handoff 和 boundary；Start Delivery、Confirm Dropoff、Cancel 仍不被启用。

KR-D Product/Closeout：实现完成后在 `tech-done.md`、`side2side_check.md`、`final.md` 留下实际改动、验证结果、偏差和剩余风险；若无真实材料，`OKR.md` 只能保守记录 software proof 边界，不得提升 O5/O1 或宣称真实送达。

## 5. 范围

### In Scope

- 顶层 acceptance brief unittest 入口。
- Robot diagnostics acceptance brief safe alias。
- mobile/web acceptance brief alias 消费和只读展示验证。
- 相关最小 docs/product 或 README 同步由实现阶段 owner 按文件范围执行；本规划阶段不修改这些文件。
- 软件证明边界：`software_proof_docker_route_task_field_retest_acceptance_brief_gate`。

### Out of Scope

- 真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover。
- WAVE ROVER、UART、`feedback_T1001`、`/odom`、`/imu`、`/battery` 或 HIL。
- PR #5 2D LiDAR / ToF SKU/source/receipt/install/wiring/calibration/HIL-entry 材料。
- 真实 Nav2/fixed-route runtime、真实电梯、真实手机/browser device proof、真实 dropoff/cancel completion、delivery success。
- 新增大测试堆、广域回归或重构 route/elevator ladder。

## 6. 优先级

P0：补齐 Robot alias 与顶层测试入口，使 acceptance brief 的 PC/Robot/mobile contract 可统一验收。

P1：保持 fail-closed 和证据边界。任何 `delivery_success=true`、`primary_actions_enabled=true`、raw artifact、raw path、credential、ROS topic、serial/UART、WAVE ROVER、HIL 或 Objective 5 external proof 暗示都必须被拦截。

P2：只做必要同步文档和 sprint 留档，不扩大到硬件材料或云证据。

## 7. 验收口径

- Autonomy 验收：`python3 -m unittest tests.test_route_task_field_retest_acceptance_brief` 可运行并通过；PC gate 输出包含 `route_task_field_retest_acceptance_brief`、`software_proof_docker_route_task_field_retest_acceptance_brief_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- Robot 验收：diagnostics focused unittest 证明 `robot_diagnostics_route_task_field_retest_acceptance_brief_summary` 存在且等于 sanitized safe summary，不泄露 raw artifact 或控制语义。
- Full-stack 验收：mobile/web focused unittest 证明 alias 被读取，UI 仍显示 blocked/not_proven，copy/export 只含 whitelist metadata，Start/Confirm/Cancel gating 不变。
- Product 验收：`tech-done.md` 汇总三方 worker 输出；`side2side_check.md` 对照用户价值与证据边界；`final.md` 明确未完成真实材料和是否需要更新 `OKR.md`。

## 8. 风险和阻塞

- 本轮不能替代真实现场材料回填；若没有门状态、楼层确认、人工协助、Nav2/fixed-route runtime log、task record 或 delivery result，Objective 2/O3/O4 只能保持保守进度。
- 本轮不能解决 O5 最低完成度；O5 必须等待真实 external proof。
- 本轮不能解决 O1 硬件 blocker；继续本地包装 WAVE ROVER/HIL 会违反同一 blocker 重复消费红线。
- 若实现阶段发现 existing code 已有部分 acceptance brief 支持，owner 应以最小 diff 补齐缺失项和验证证据，不做无关 refactor。

## 9. 需要创建或更新的 sprint 文档

规划阶段只创建 `pre_start.md`、`prd.md`、`tech-plan.md`。

实现阶段完成后再创建或更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
