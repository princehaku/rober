# Sprint 2026.05.18_15-16 Route Task Acceptance Execution Handoff Intake - Pre Start

## 1. Sprint 声明

- sprint_type: epic
- sprint_id: `2026.05.18_15-16_route-task-acceptance-execution-handoff-intake`
- 主题: `route_task_field_retest_acceptance_execution_handoff_intake`
- Product Owner: `product-okr-owner`
- 执行 owner: `autonomy-engineer`, `robot-software-engineer`, `full-stack-software-engineer`, `product-okr-owner`
- 当前时间: 2026-05-18 15:04 Asia/Shanghai
- 本轮目标: 把上一轮 `route_task_field_retest_acceptance_execution_callback_review_handoff` package 转成更严格的 owner handoff intake / acknowledgement gate，让现场 owner callback 或 intake JSON 被 fail-closed 分类为 `ready_for_controlled_field_rerun_queue`、`needs_owner_ack`、`needs_acceptance_execution_handoff_backfill`、`evidence_ref_mismatch_rerun` 或 `blocked_unsafe_handoff_intake`。

## 2. 背景证据

- 当前 `OKR.md` 4.1 显示 Objective 5 约 68%，是数字最低 Objective；但本机只有 Docker，没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 外部材料，所以 O5 stop rule 继续成立。本轮不得继续堆 O5 本地 metadata depth。
- Objective 1 约 81%，但缺真实 WAVE ROVER、UART、HIL、`feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery` 和 operator HIL report；近期 O1 sprint 已多次消费同一真实硬件 blocker，本轮不继续本地包装同一 blocker，也不声明 `hil_pass`。
- PR #4 已把 elevator-assisted delivery 设为主链必需能力；本轮 handoff intake 仍必须保留真实电梯门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record/completion signal、dropoff/cancel completion 和 delivery result 的材料缺口。
- PR #5 review 提出 `production_hardware_boundary.md` 默认硬件集与 2D LiDAR/ToF baseline 矛盾，并要求硬件材料引用 `docs/vendor` 来源；该缺口仍是真实 SKU/source、receipt、采购、安装、接线、电源、标定和 HIL-entry blocker，不能用本轮 software proof 代替。
- 最新 sprint `sprints/2026.05.18_14-15_route-task-acceptance-execution-callback-review-handoff/final.md` 已完成 `software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_handoff_gate`，但明确没有真实 route/elevator field pass、真实门状态、真实楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record/completion signal、dropoff/cancel completion 或 delivery result。

## 3. 用户价值和产品北极星

用户价值: 现场 owner 不需要在 callback review handoff summary 和可选 owner callback/intake JSON 之间人工对账；PC gate、Robot diagnostics 和 mobile/web 可以只读展示同一份 owner handoff intake 结论，清楚说明是可排队进入受控现场复跑、等待 owner ack、需要交接材料补齐、同一 `evidence_ref` 重跑，还是因 unsafe handoff intake 阻断。

产品北极星: 继续服务“普通手机用户可验证地完成低成本垃圾投递”的主线。本轮只推进 route/elevator field retest 的 owner handoff intake 可复核性，帮助未来真实现场材料回填，不把 Docker/local software proof 写成真实送达、真实电梯、真实 Nav2/fixed-route、真实手机、HIL 或云生产证明。

## 4. Blocker 与 rerank 决策

- O5 blocker: 缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser 外部材料。处理: 本轮不针对 O5。
- O1 blocker: 缺真实 WAVE ROVER、UART、HIL packet、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery` 和 operator HIL report；同一 blocker 已被近期 O1 sprint 多次消费。处理: 本轮不新增本地 O1 wrapper。
- PR #5 hardware material blocker: 缺 2D LiDAR/ToF vendor source、SKU、receipt、采购、安装、接线、电源、标定和 HIL-entry 证据。处理: 在 handoff intake 中保持缺口提示，但不冒充真实材料。
- 当前可执行抓手: 沿 PR #4 route/elevator acceptance execution handoff 链，把上一轮 callback review handoff package 转成 owner handoff intake / acknowledgement gate，保持 `software_proof_docker_route_task_field_retest_acceptance_execution_handoff_intake_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 5. 本轮核心抓手

新增 `route_task_field_retest_acceptance_execution_handoff_intake` intake layer：

- Autonomy 创建 PC gate，消费上一轮 handoff summary 和可选 owner callback/intake JSON，输出 handoff intake artifact/summary。
- Robot diagnostics 增加 safe alias，供 operator diagnostics 和 mobile 只读消费。
- Full-stack 在 `mobile/web` 增加只读“现场交接回执入口” panel，不改变 Start Delivery、Confirm Dropoff、Cancel gating。
- Product closeout 在工程返回后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md` 和必要 docs。

## 6. 证据边界

本轮固定边界:

- `software_proof_docker_route_task_field_retest_acceptance_execution_handoff_intake_gate`
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
