# Sprint 2026.05.18_11-12 Route Task Acceptance Execution Pack - Pre Start

sprint_type: epic

## 1. 启动结论

本轮启动 `route_task_field_retest_acceptance_execution_pack` Epic sprint。产品北极星是让真实现场复跑不再依赖口头交接：operator、Robot diagnostics、mobile/web 和现场 owner 必须拿到同一份可执行清单、rerun commands、安全证据包和 fail-closed 边界。

本轮继续 Objective 2 / Objective 3 / Objective 4 的 PR #4 route/elevator 现场验收链。上一轮 `2026.05.18_10-11_route-task-acceptance-review-decision` 已完成 `software_proof_docker_route_task_field_retest_acceptance_review_decision_gate`，但 final 明确下一步若没有 Objective 5 external proof 或 Objective 1 真实硬件材料，应进入 PR #4 真实现场材料回填或执行包落地。

本轮不推进 Objective 5。`OKR.md` 4.1 显示 Objective 5 约 68%，是数字最低，但 Docker-only host 缺真实 HTTPS/TLS、公网、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 和真实手机/browser external proof，不能再堆本地 O5 metadata。

本轮不推进 Objective 1。Objective 1 约 81%，但近期 WAVE ROVER/HIL packet intake、review、execution-pack 已重复消费真实硬件 blocker；本机没有真实硬件，不能再把缺 `/dev/ttyUSB*` 或真实 packet 作为本轮主线。

## 2. Live 证据输入

- `OKR.md` 4.1：最新 sprint 是 `2026.05.18_10-11_route-task-acceptance-review-decision`；Objective 2、Objective 3、Objective 4 均约 99%，但仍缺真实 route/elevator materials。
- `sprints/2026.05.18_10-11_route-task-acceptance-review-decision/final.md`：上一轮已把 acceptance brief 推进到 review decision，下一轮若无 O5/O1 真实材料，应进入 PR #4 真实现场材料回填或执行包落地。
- PR #4：elevator-assisted delivery 已成为主 behavior chain，不是可选功能；执行包必须覆盖真实门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record/completion signal、dropoff/cancel completion 和 delivery result。
- PR #5 review：`docs/product/production_hardware_boundary.md` 曾出现 default hardware set 与 `monocular + 2D LiDAR + ToF` mandatory baseline 矛盾；新增 mandatory sensor assumptions 缺本地 `docs/vendor/` 来源。这是硬件材料缺口，但本机没有真实材料，不能在本轮闭环。

## 3. 本轮核心抓手

把上一轮 acceptance review decision 消费为现场复跑执行包：

- 产出 owner checklist：谁带什么材料、现场前置条件、失败时回填哪类证据。
- 产出 rerun commands：PC gate、Robot diagnostics、mobile/web 三端可复核命令。
- 产出 safe evidence bundle：只包含 safe `evidence_ref`、material requirements、owner handoff、next required evidence、fail-closed flags 和 copy-safe 摘要。
- 保持证据边界：`software_proof_docker_route_task_field_retest_acceptance_execution_pack_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 4. Owner 与协作边界

本轮需要 3 个 IC owner 并行，文件范围互不重叠：

- Autonomy Algorithm Engineer：新增 PC evidence execution-pack gate，消费 acceptance review decision，并输出现场复跑执行包。
- Robot Platform Engineer：新增 diagnostics safe summary consumer，把执行包转成 Robot-side read-only status。
- User Touchpoint Full-Stack Engineer：新增 mobile/web 只读 execution-pack panel，把现场 owner checklist、rerun commands 和 safe evidence bundle 展示给用户触点。

Product Owner 负责 sprint 规划、OKR 映射、验收口径、风险边界和后续收口留档；不直接修改产品代码、测试代码或硬件配置。

## 5. 风险边界

- 本轮只允许输出 `software_proof_docker_route_task_field_retest_acceptance_execution_pack_gate`。
- 本轮必须保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 本轮不访问真实电梯、真实手机、真实 WAVE ROVER、真实串口、ROS graph、Nav2 runtime、外部云、OSS/CDN、DB/queue、4G 或真实 route/elevator field materials。
- 本轮不把 PR #5 2D LiDAR / ToF vendor/source 缺口写成已解决。
- 如果 broad `git diff --check` 被无关历史 whitespace 阻塞，只允许使用 touched-file scoped diff check 并在 closeout 写明。
