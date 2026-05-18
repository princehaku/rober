# Sprint 2026.05.18_19-20 Route Task Acceptance Execution Rerun Result Review Handoff - PRD

## 1. 用户价值和产品北极星

北极星：普通手机用户可以把垃圾交给低成本 ROS2 小车，由小车沿固定路线完成送达、电梯 assisted delivery、异常解释和可复盘证据链；用户不需要懂 ROS2、串口、raw JSON、硬件接线、云基础设施或现场材料目录。

本轮用户价值：把“受控复跑结果复核决策”推进成“owner 可执行交接”。上一轮已经能判断 ready handoff、backfill、mismatch、unsafe 或 unsupported；本轮要让现场 owner、Robot diagnostics 和手机支持人员看到同一 safe `evidence_ref` 下的下一步材料责任、回填边界和执行提示，但仍不读取真实材料目录、不触发机器人、不证明真实 route/elevator field pass。

## 2. OKR 映射

- Objective 5：约 68%，当前数字最低。缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser 外部证据；按 stop rule，不继续堆本地 O5 metadata，不把本轮 handoff 写成 O5 proof。
- Objective 1：约 81%。缺真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report；PR #5 仍缺 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。本轮不第三次包装同一硬件 blocker。
- Objective 2：推进“可送垃圾任务 + 电梯 assisted delivery 必达闭环”的 PR #4 现场回填准备层。
- Objective 3：推进“可验证导航与固定路线能力”的 route completion、task record、Nav2/fixed-route runtime log、dropoff/cancel completion 和 delivery result 回填路径。
- Objective 4：推进手机只读支持面板，让普通用户和支持人员能看懂 handoff 状态，但不开放控制。

## 3. KR 拆解或更新

- KR-A：新增 PC gate `route_task_field_retest_acceptance_execution_rerun_result_review_handoff`，消费上一轮 review decision artifact/summary，产出 owner handoff package。
- KR-B：handoff package 必须表达 handoff status、safe `evidence_ref`、owner role、next required evidence、rerun summary、blocked reason、boundary flags。
- KR-C：Robot diagnostics 新增 safe alias，只转发 sanitized metadata，不读取 raw artifact，不暴露 ROS topic、serial/UART、WAVE ROVER low-level control 或 success wording。
- KR-D：mobile/web 新增只读 handoff panel，显示 handoff status、owner、safe evidence ref、next evidence、boundary flags 和 `not_proven`，且不改变 Start / Confirm Dropoff / Cancel。
- KR-E：`pc-tools/README.md`、`docs/interfaces/evidence_contracts.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md` 同步说明本轮只是 software proof handoff，不是真实现场通过。

## 4. 本轮核心抓手

核心抓手是把 review decision 转成 owner handoff，而不是继续创建 O5/O1 包装：

- 输入：上一轮 `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_decision_gate` 的 safe summary。
- 输出：`software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_gate` 下的 sanitized handoff summary。
- 必须保留：`source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 必须禁止：raw artifact、local path、checksum、credentials、DB/queue URL、ROS topic、serial/UART、WAVE ROVER low-level control、success/control wording。

## 5. 需要做什么

1. Autonomy 建 PC handoff gate 和 tests，把 review decision 分流成可执行 handoff package。
2. Robot 加 diagnostics safe alias，确保 handoff 只作为 support metadata 转发。
3. Full-stack 加 mobile read-only handoff panel，确保 UI 只展示 owner handoff，不解锁主操作。
4. 三个 owner 分别更新对应 docs，写清 PR #4 真实现场回填准备层和 PR #5 风险保留。
5. Product 后续收口时更新 sprint `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 6. 优先级和验收口径

P0 验收：

- Autonomy、Robot、Full-stack 三个 surface 都能展示同一 handoff family。
- 所有 surface 都包含 `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_gate`。
- 所有 surface 都保留 `source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- mobile/web Start Delivery、Confirm Dropoff、Cancel gating 不因 handoff 变化。

P1 验收：

- handoff copy 明确不是 real route/elevator field pass、not delivery success、not HIL、not real phone/browser、not Objective 5 external proof。
- Robot/mobile copy 不出现 raw artifact、完整 artifact、本地路径、checksum、凭证、DB/queue URL、ROS topic、serial/UART、WAVE ROVER low-level control、success 或 control wording。
- docs/interfaces 和 docs/product 同步最新 contract。

## 7. 对应责任 Engineer

- Autonomy Algorithm Engineer：`pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_review_handoff.py`、对应 unittest、`pc-tools/README.md`、`docs/interfaces/evidence_contracts.md`。
- Robot Platform Engineer：`operator_gateway_diagnostics.py`、对应 diagnostics unittest、`docs/interfaces/ros_contracts.md`。
- User Touchpoint Full-Stack Engineer：`mobile/web/app.js`、fixture、mobile web unittest、`docs/product/mobile_user_flow.md`。
- Product Manager / OKR Owner：仅负责本 sprint PRD/tech-plan/验收/收口，后续按证据更新 OKR.md；不改实现文件。

## 8. 风险、阻塞和需要补齐的证据链

- PR #4 真实现场回填仍缺真实电梯门状态、真实楼层确认、人工协助记录、Nav2/fixed-route runtime log、同一 `evidence_ref` 的 task record/completion signal、dropoff/cancel completion 或 delivery result。
- PR #5 review 未解决点仍阻塞硬件事实闭环：默认硬件集合与 `monocular + 2D LiDAR + ToF` mandatory baseline 矛盾；新增 sensor baseline 缺 `docs/vendor/` source citation；真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料缺失。
- Objective 5 真实外部 evidence 和 Objective 1 真实硬件 evidence 均未出现，本轮不得把 software proof 写成 OKR 实物通过。
- 若 Engineer 发现上一轮 review decision summary 字段不足，只能 fail closed 输出 backfill/unsupported，不得读取真实材料目录或推测硬件事实。

## 9. 需要创建或更新的 sprint 文档

- 已创建/本阶段创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 实现完成后：`tech-done.md` 记录三 owner 实际改动、验证输出、偏差和剩余风险。
- Product 验收后：`side2side_check.md` 对照 PRD 验收。
- 收口后：`final.md` 回顾 OKR 最低优先级、PR #4 / PR #5 证据、Docker-only 边界和未完成真实证据。
