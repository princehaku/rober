# Sprint 2026.05.18_13-14 Route Task Acceptance Execution Callback Review Decision - PRD

## 1. 用户价值和产品北极星

用户价值：当现场 owner 按 execution pack 回传 callback packet 后，系统要把“材料收到了什么、缺了什么、拒了什么”进一步转成明确执行判断，帮助团队决定是否能进入受控现场复跑，还是必须材料回填或同一 `evidence_ref` 重跑。

产品北极星：服务低成本 ROS2 自主垃圾投递机器人在楼宇 route/elevator 场景里的可验证交付链路。本轮只做 acceptance execution callback review decision 的 repo-local software proof，不把材料复核写成真实 route/elevator field pass、Nav2/fixed-route proof、task record/completion signal、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## 2. OKR 映射

| Objective | 本轮关系 | 口径 |
| --- | --- | --- |
| Objective 2：可送垃圾任务 + 电梯 assisted delivery 必达闭环 | 主目标 | 把 PR #4 route/elevator execution callback intake 结果转成复跑/回填/重跑决策，但不证明真实送达或真实电梯。 |
| Objective 3：可验证导航与固定路线 | 主目标 | 把 Nav2/fixed-route runtime log、route completion signal、task record 等材料的 callback 状态转成下一步复核决策，但不证明真实路线执行。 |
| Objective 4：手机用户体验与低成本量产边界 | 支撑目标 | mobile/web 只读展示 review decision，让支持人员看懂材料状态和 owner handoff，但不启用控制动作。 |
| Objective 5：云中转 + OSS/CDN 数据通路产品化 | 本轮不推进 | Objective 5 数值最低，但外部材料阻塞，O5 stop rule 继续成立。 |
| Objective 1：硬件协议可信底盘 | 本轮不推进 | Objective 1 缺真实 WAVE ROVER/UART/HIL packet，且同一硬件 blocker 已重复消费。 |

## 3. KR 拆解

### KR-A：Callback review decision gate

- 输入：上一轮 `route_task_field_retest_acceptance_execution_callback_intake` artifact 或 summary。
- 输出：`route_task_field_retest_acceptance_execution_callback_review_decision` artifact / summary。
- 决策枚举：
  - `ready_for_controlled_field_rerun`
  - `needs_material_backfill`
  - `evidence_ref_mismatch_rerun`
  - fail-closed invalid / unsafe / unsupported 状态
- 必须输出 owner handoff、next required evidence、safe rerun command summary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

### KR-B：Robot diagnostics safe alias

- Robot diagnostics 增加 phone-safe alias，例如 `robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_decision_summary`。
- alias 只暴露 schema、status / review decision、safe `evidence_ref`、owner handoff、next required evidence、evidence boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 不暴露 raw ROS topics、`/cmd_vel`、serial/UART、WAVE ROVER 参数、凭证、local paths、完整 artifact、checksums 或 tracebacks。

### KR-C：Mobile/web read-only panel

- mobile/web 增加只读 “现场回执复核决策” panel。
- panel 消费主 summary 或 Robot diagnostics safe alias。
- panel 展示 review decision、callback intake 状态摘要、owner handoff、next required evidence、safe rerun hint、evidence boundary、`not_proven`。
- panel 不改变 Start Delivery、Confirm Dropoff、Cancel gating；继续保持 `primary_actions_enabled=false` 和 `delivery_success=false`。

### KR-D：Product closeout

- 实现完成后 Product 更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和必要 docs / progress log。
- closeout 必须复核证据边界是否仍为 `software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_decision_gate`。

## 4. 本轮核心抓手

核心抓手是把 “callback intake 状态” 变成 “callback review decision”：不再停留在材料列表，而是形成 owner 可执行的下一步判断。

本轮不是：

- 真实 route/elevator field pass
- 真实 Nav2/fixed-route proof
- 真实 task record/completion signal
- 真实 dropoff/cancel completion
- delivery success
- HIL
- 真实手机/browser
- Objective 5 external proof

## 5. 需要做什么

1. Autonomy PC gate：实现 callback review decision gate 和 focused unittest。
2. Robot diagnostics：加入 safe alias 和 diagnostics focused unittest。
3. Full-stack mobile/web：加入只读 panel、fixture 和 focused unittest，`node --check` 必须通过。
4. Product closeout：验收三端边界，更新 sprint closeout、OKR progress 和必要 docs。

## 6. 优先级和验收口径

优先级：

1. PC gate fail-closed 决策正确性。
2. Robot diagnostics safe alias 与主 summary 一致。
3. mobile/web 只读展示准确且不启用动作。
4. Product closeout 不扩大证据边界。

验收口径：

- 只能使用围栏命令：`py_compile`、focused unittest、`node --check`、required `rg`、scoped `git diff --check`。
- 不运行 broad test，不要求真实硬件、真实电梯、真实手机、真实云或外部网络材料。
- 任何 ready 文案必须带 `not_proven`，并且不得移除 `delivery_success=false` 或 `primary_actions_enabled=false`。

## 7. 对应责任 Engineer

| Owner | 责任 |
| --- | --- |
| Autonomy Algorithm Engineer | PC gate、artifact / summary schema、decision policy、focused unittest。 |
| Robot Platform Engineer | diagnostics safe alias、sanitized output、diagnostics focused unittest。 |
| User Touchpoint Full-Stack Engineer | mobile/web read-only panel、fixture、mobile focused unittest、`node --check`。 |
| Product Manager / OKR Owner | sprint closeout、OKR.md 进展、docs/product 或 process 文档同步复核。 |

## 8. 风险、阻塞和证据链

- O5 external proof 阻塞：没有公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser。
- O1 hardware proof 阻塞：没有真实 WAVE ROVER、UART、HIL packet 或底盘反馈样本。
- PR #5 hardware material 阻塞：2D LiDAR / ToF 的 source、receipt、采购、安装、接线、电源、标定和 HIL-entry 仍缺。
- callback review decision 只能消费 safe intake artifact / summary；不能读取 raw 现场文件、ROS graph、serial/UART、外部云或真实设备。
- 所有输出必须保留 `software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_decision_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 9. 需要创建或更新的 sprint 文档

- 本轮 planning：`pre_start.md`、`prd.md`、`tech-plan.md`
- 实现后：`tech-done.md`
- 验收后：`side2side_check.md`
- 收口后：`final.md`
