# Sprint 2026.05.18_10-11 Route Task Acceptance Review Decision - Pre Start

sprint_type: epic

## 1. 启动结论

本轮启动 `route_task_field_retest_acceptance_review_decision` Epic sprint。目标不是继续包装 Objective 5 云证据、Objective 1 WAVE ROVER/HIL blocker，或 PR #5 2D LiDAR / ToF 真实硬件材料；本轮选择 PR #4 route/elevator assisted delivery 的下一步可执行软件链路：把上一轮 `route_task_field_retest_acceptance_brief` 转成现场验收前的 review decision。

该 decision 只回答一个问题：基于 acceptance brief 的 safe summary，下一步应该进入受控现场复跑、材料回填、owner handoff，还是因为 schema、`evidence_ref`、unsafe copy、success/control wording 被 fail closed。它仍然是 Docker-local software proof，不证明真实 route/elevator field pass、Nav2/fixed-route proof、task record/completion signal、dropoff/cancel completion、delivery success、HIL/WAVE ROVER/UART、真实手机/browser/device 或 O5 external proof。

## 2. 上轮输入

- `OKR.md` 4.1：Objective 5 约 68%，仍是数字最低；但真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover 或真实手机/browser external proof 均不可用。
- `sprints/2026.05.18_09-10_route-task-field-retest-acceptance-brief/final.md`：上一轮完成 PC/Robot/mobile acceptance brief contract 对齐，但明确没有真实 route/elevator field pass，也没有真实 task record/completion signal 或 delivery result。
- PR #4：已把 elevator assisted delivery 写入主链，现场材料必须覆盖真实门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record/completion signal、dropoff/cancel completion 和 delivery result。
- PR #5：硬件 baseline / 2D LiDAR / ToF / vendor-source 风险仍缺真实 SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料，本轮不得用 software proof 代替。

## 3. 本轮 owner

并行启动 3 个 IC owner，文件范围互不重叠：

- Autonomy Algorithm Engineer：新增 PC evidence gate 和顶层 unittest wrapper。
- Robot Platform Engineer：新增 diagnostics safe summary consumer。
- User Touchpoint Full-Stack Engineer：新增 mobile/web 只读 decision panel 和 phone-safe fixture/test。

Product Owner 只做本轮方向、验收口径、OKR 保守收口和 sprint 留档，不直接修改产品代码或测试代码。

## 4. 风险边界

- 本轮只允许输出 `software_proof_docker_route_task_field_retest_acceptance_review_decision_gate`。
- 所有产物必须保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 不读取真实材料目录，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser。
- 如果 broad `git diff --check` 被无关历史 whitespace 阻塞，只使用 touched-file scoped diff check 并在 closeout 写明。
