# Sprint 2026.05.18_08-09 Route Task Field Retest Drill Console - Pre Start

sprint_type: epic

## 1. 启动结论

本轮启动新 sprint：`sprints/2026.05.18_08-09_route-task-field-retest-drill-console/`。

用户要求是：开始下一轮迭代，根据近期 PR 和评审，建议下一步应深入的 OKR；每条建议必须基于具体证据；用 team 继续完成 OKR；重新在功能往前走；测试只做围栏；优先推进 OKR 完成度低的部分；当前主机没有真实硬件，只有 Docker；最后由完整实现轮次提交 git 并推送远程。

Product Owner 本轮只负责启动和规划，不写产品代码、测试代码或硬件配置。实现阶段必须并行派 Autonomy、Robot、Full-stack 三个 worker；Product closeout 等实现和验证完成后再执行。

## 2. 用户价值和产品北极星

北极星：把 `rober` 做成普通手机用户可用的低成本 ROS2 自主送垃圾机器人。用户价值不是“生成更多材料清单”，而是让现场 operator 能按同一 `evidence_ref` 演练、导出、回填 route/elevator 现场材料，并清楚知道哪些证据仍缺失。

本轮核心用户价值：把上一轮 `route_task_field_retest_operator_drill` 从“操作演练命令/清单”推进成 `route_task_field_retest_drill_console`，形成一个可执行、可导出的演练控制台 software proof，让现场人员可以按控制台完成材料收集准备，同时不给用户或工程团队造成真实 field pass、delivery success 或 HIL 已完成的误解。

## 3. OKR 证据和 rerank

- `OKR.md` 4.1 显示 Objective 5 约 68%，是当前数值最低 Objective；但 Objective 5 下一步需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof。本机只有 Docker，继续堆本地 O5 metadata depth 会重复消费同一 external blocker。
- `OKR.md` 4.1 显示 Objective 1 约 81%；但 Objective 1 下一步需要真实 WAVE ROVER、UART、HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report，以及 PR #5 真实 2D LiDAR / ToF source、receipt、procurement、installation、wiring、power、calibration、HIL-entry 材料。本机没有真实硬件，不能把 Docker proof 写成 O1 进度。
- PR #5 review P1 指出 `docs/product/production_hardware_boundary.md` 的 default hardware set 与后文 `monocular + 2D LiDAR + ToF` mandatory baseline 矛盾，会让 BOM/procurement 和 bringup 计划漏掉被视为必需的传感器。
- PR #5 review P2 指出 mandatory sensor assumptions 缺少 `docs/vendor/` evidence citation；这符合当前 PR #5 硬件材料仍未闭环的风险。
- PR #4 已把 elevator-assisted delivery 写入主链路必达能力，但 PR #4 描述里也明确没有执行 runtime integration tests；因此下一步应继续补 route/elevator field material 和演练可执行层，而不是宣称能力完成。
- 最新 sprint `2026.05.18_07-08_route-task-material-review-operator-drill/final.md` 说明 `route_task_field_retest_operator_drill` 已消费 material callback review decision，但没有真实 field pass；final 明确建议若 O5 external proof 和 O1 real hardware proof 仍不可用，下一步把 operator drill 带到 PR #4 受控现场材料回填或继续现场演练层。

结论：本轮不继续 Objective 5 / Objective 1 的 blocked material wrapper；转向 Objective 2 / 3 / 4 的 PR #4 route/elevator field material 路线，做 `software_proof_docker_route_task_field_retest_drill_console_gate`。

## 4. KR 拆解和本轮核心抓手

本轮核心抓手：`route_task_field_retest_drill_console`。

KR 拆解：

- Objective 2 KR6 / KR7：把电梯 assisted delivery 的门状态、目标楼层确认、人工协助、失败接管和证据回填，变成 operator drill console 的明确演练字段，但保持 `not_proven`。
- Objective 3 KR2 / KR3 / KR5：把 Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion 和 delivery result 的 required material，变成可导出的控制台清单，不声称真实 fixed-route 或 Nav2 通过。
- Objective 4 KR1 / KR5 / KR6 / KR7：在手机/Web/diagnostics 侧只读展示和导出演练控制台摘要，不改变 Start Delivery、Confirm Dropoff、Cancel 授权，不暴露 raw JSON、ROS topic、串口、凭证或完整 artifact。

## 5. 范围边界

必须保持：

- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `evidence_boundary=software_proof_docker_route_task_field_retest_drill_console_gate`

不得声称：

- 真实 route/elevator field pass
- 真实 Nav2/fixed-route 运行
- 真实 task record/completion signal
- 真实 dropoff/cancel completion
- delivery success
- HIL、WAVE ROVER/UART、真实串口或真实反馈
- 真实手机/browser/device 行为
- Objective 5 external proof

## 6. 责任 Engineer

- Autonomy Engineer：实现 PC/CLI drill console artifact gate，把上一轮 `route_task_field_retest_operator_drill` 输出转成支持现场演练的 console artifact / summary / export metadata。
- Robot Platform Engineer：在 diagnostics/operator gateway 只读消费 drill console summary，保持 fail-closed，不启用任何 primary action。
- User Touchpoint Full-Stack Engineer：在 `mobile/web` 只读展示 drill console 摘要和安全导出，不改变 Start / Confirm / Cancel gating。
- Product Manager / OKR Owner：实现完成后核对证据边界、更新 `tech-done.md`、`side2side_check.md`、`final.md` 和 `OKR.md`，并确保 docs/ 同步状态已由对应 owner 更新。

## 7. 风险、阻塞和证据链

阻塞：

- Objective 5 external proof 缺真实公网/4G/OSS/CDN/DB/queue/worker/cutover/真实手机材料。
- Objective 1 HIL proof 缺真实 WAVE ROVER/UART/HIL 和 PR #5 2D LiDAR / ToF 实物材料。
- PR #4 runtime integration tests 仍缺；本轮只能补 Docker-local software proof 演练控制台。

证据链需要补齐：

- 同一 `evidence_ref` 下的真实电梯门状态、目标楼层确认、人工协助记录。
- Nav2/fixed-route runtime log、route completion signal、task record。
- dropoff/cancel completion 和 delivery result。
- 真实手机/browser/device 或生产 app 验收材料。
- PR #5 真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。

## 8. 需要创建或更新的 sprint 文档

已创建/本阶段更新：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实现完成后必须追加：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

Product closeout 必须最终更新 `OKR.md`，但本启动任务的允许文件范围不包含 `OKR.md`，因此只能在实现后由允许范围覆盖时执行。
