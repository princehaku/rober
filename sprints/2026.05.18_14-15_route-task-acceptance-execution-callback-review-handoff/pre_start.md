# Sprint 2026.05.18_14-15 Route Task Acceptance Execution Callback Review Handoff - Pre Start

## 1. Sprint 声明

- sprint_type: epic
- sprint_id: `2026.05.18_14-15_route-task-acceptance-execution-callback-review-handoff`
- 主题: `route_task_field_retest_acceptance_execution_callback_review_handoff`
- Product Owner: `product-okr-owner`
- 执行 owner: `autonomy-engineer`, `robot-software-engineer`, `full-stack-software-engineer`, `product-okr-owner`
- 本轮目标: 把上一轮 `route_task_field_retest_acceptance_execution_callback_review_decision` 的 review decision 转成可交接的 handoff package，让现场 owner 明确下一步是进入受控现场复跑、补材料、同一 `evidence_ref` 重跑，还是因 unsafe review handoff 阻断。

## 2. 背景证据

- 当前 `OKR.md` 4.1 显示 Objective 5 约 68%，是数字最低 Objective；但本机只有 Docker，没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 外部材料，所以 O5 stop rule 成立。本轮不得继续堆 O5 本地 metadata depth。
- Objective 1 约 81%，但近期 WAVE ROVER feedback replay、HIL packet intake、HIL packet review decision、HIL packet execution pack 等 sprint 已重复消费同一真实 WAVE ROVER/UART/HIL blocker。本机无真实硬件，本轮不继续本地包装同一 blocker，也不声明 `hil_pass`。
- PR #4 已把 elevator-assisted delivery 写入主链，要求电梯状态和证据链进入工程路线；因此 route/elevator acceptance execution callback 的 handoff 必须继续保留门状态、楼层确认、人工协助、Nav2/fixed-route runtime log、task record/completion signal、dropoff/cancel completion 和 delivery result 等材料口径。
- PR #5 review 指出 hardware baseline/default set 与 2D LiDAR/ToF/vendor source/material 缺口；该缺口仍是真实材料 blocker，不能用本轮 software proof 代替真实 SKU/source、receipt、采购、安装、接线、电源、标定或 HIL-entry 材料。
- 最新 sprint `sprints/2026.05.18_13-14_route-task-acceptance-execution-callback-review-decision/final.md` 已完成 `route_task_field_retest_acceptance_execution_callback_review_decision`。下一步应把 review decision 转成 handoff package，而不是宣称真实现场通过。

## 3. 用户价值和产品北极星

用户价值: 现场 owner 和支持同学不需要从 review decision 原始材料里手工推断下一步；手机、Robot diagnostics 和 PC gate 能展示同一份只读交接摘要，说明该准备复跑、补材料、同一 evidence_ref 重跑，还是因 unsafe handoff 阻断。

产品北极星: 继续服务“普通手机用户可验证地完成低成本垃圾投递”的主线。本轮只推进现场材料复核后的交接闭环，帮助未来真实 route/elevator field run 准备材料，不把 Docker/local software proof 写成真实送达、真实电梯、真实 Nav2/fixed-route、真实手机或云生产证明。

## 4. Blocker 与 rerank 决策

- O5 blocker: 缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser 外部材料。处理: 本轮不针对 O5。
- O1 blocker: 缺真实 WAVE ROVER、UART、HIL packet、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery` 和 operator HIL report；同一 blocker 已被近期 O1 sprint 多次消费。处理: 本轮不新增本地 O1 wrapper。
- PR #5 hardware material blocker: 缺 2D LiDAR/ToF vendor source、SKU、receipt、采购、安装、接线、电源、标定和 HIL-entry 证据。处理: 在 handoff 中保持缺口提示，但不冒充真实材料。
- 当前可执行抓手: 沿 PR #4 route/elevator acceptance execution callback 链，把上一轮 review decision 变成 handoff package，保持 `software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_handoff_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 5. 本轮核心抓手

新增 `route_task_field_retest_acceptance_execution_callback_review_handoff` handoff layer：

- Autonomy 生成 PC gate，读取上一轮 review decision artifact/summary，输出 handoff artifact/summary。
- Robot diagnostics 暴露 safe alias，供 operator diagnostics 和 mobile 只读消费。
- Full-stack 在 `mobile/web` 增加只读“现场复核交接” panel，不改变 Start Delivery、Confirm Dropoff、Cancel gating。
- Product closeout 收口 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md` 和必要 docs。

## 6. 证据边界

本轮固定边界:

- `software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_handoff_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

本轮明确不证明:

- real route/elevator field pass
- Nav2/fixed-route proof
- task record/completion signal
- dropoff/cancel completion
- delivery result
- delivery success
- HIL
- 真实手机/browser
- Objective 5 external proof

## 7. 需要创建或更新的 sprint 文档

本轮 Epic sprint 需要完整六文档链路:

- 已创建计划阶段: `pre_start.md`, `prd.md`, `tech-plan.md`
- 执行后由 Product closeout 更新: `tech-done.md`, `side2side_check.md`, `final.md`
