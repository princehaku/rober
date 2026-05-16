# Sprint 2026.05.17_00-01 Route Task Field Retest Material Pack - Pre Start

sprint_type: epic

## 1. 开工背景

本轮 Automation `skill-progression-map` 的 CEO 输入是：开始下一轮迭代，根据近期 PR 和评审建议下一步应深入的 OKR，每条建议必须基于具体证据，用 team 继续完成 OKR；本机没有真实硬件，只有 Docker；最后在实现阶段提交并推送。

本 sprint 只启动计划阶段，目标是为后续 Engineer workers 明确 `route_task_field_retest_material_pack` 的产品范围、owner 边界、验收命令和证据口径。当前任务不实现产品代码，不更新 `OKR.md`，也不声明 field pass。

## 2. 上轮证据

- `OKR.md` 4.1 显示 Objective 5 约 66%，是当前数值最低 Objective；但 `OKR.md` 第 6 节要求只有拿到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 等真实外部材料时，才继续推进 Objective 5 completion。
- 最新 sprint `sprints/2026.05.16_23-24_route-task-field-result-reconciliation/final.md` 建议：若仍无 Objective 5 外部材料，下一轮优先补同一 `evidence_ref` 的真实现场材料回填样本，至少拿到一组真实 route/task field retest material set。
- PR #4 elevator-assisted delivery 主线反复缺真实 `door_state`、`target_floor_confirmation`、`human_assistance_note`。
- PR #5 硬件 baseline / 2D LiDAR / ToF / vendor-source 风险仍缺真实 SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry；但最近两轮已消费硬件/source/config blocker，`AGENTS.md` 同一 blocker 最多消费 2 轮，不能第三次围绕同一 blocker 写 wrapper。
- 最新 route/task 链路已有 `route_task_field_retest_execution_pack`、`session_handoff`、`result_intake`、`result_reconciliation`，下一步应补现场人员可执行的材料打包和校验入口，而不是再写一个只读复账层。

## 3. 本轮用户价值和北极星

用户价值：现场人员不需要读 ROS2、SSH、raw JSON、串口或工程目录，就能把一次 route/task field retest 的八类真实材料放进一个目录，由 dependency-free PC 工具生成 sanitized artifact 和 summary，交给已有 Robot diagnostics 与 mobile/web 只读链路消费。

产品北极星：把“能跑的 Docker 软件证明”继续向“可回填、可复账、可解释的真实路线/任务现场材料”推进，同时保持 `software_proof_docker_route_task_field_retest_material_pack_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false` 边界。

## 4. 本轮核心抓手

本轮核心抓手是 `route_task_field_retest_material_pack`：

- PC 端打包真实材料目录，覆盖八类材料：
  - `nav2_or_fixed_route_runtime_log`
  - `route_completion_signal`
  - `task_record`
  - `door_state`
  - `target_floor_confirmation`
  - `human_assistance_note`
  - `dropoff_or_cancel_completion`
  - `delivery_result`
- 校验同一 `evidence_ref`，拒绝 placeholder-only、raw path、credential、unsafe success phrasing、`delivery_success=true`、`primary_actions_enabled=true`。
- 输出 `trashbot.route_task_field_retest_material_pack.v1` 与 summary，供现有 result_intake / reconciliation 后续消费。
- 没有真实材料时只允许 fixture 和软件 proof；不得声称 field pass、真实 Nav2/fixed-route、真实电梯、真实 dropoff/cancel completion、delivery success、HIL 或 Objective 5 external proof。

## 5. Owner 与执行边界

- Task A Autonomy：主责 PC dependency-free CLI 和固定路线文档。
- Task B Robot：主责 metadata-only diagnostics 消费，fail closed，不改变 collect/dropoff/cancel/ACK/Nav2/HIL/delivery success。
- Task C Full-stack：主责 mobile/web 只读“现场材料包” panel，不改变 Start/Confirm/Cancel gating。
- Task D Product closeout：三方实现完成后，主责 sprint 收口、`OKR.md` 和 `docs/process/okr_progress_log.md` 同步。

## 6. 阻塞与风险

- 当前本机只有 Docker，没有真实硬件、真实电梯、真实路线运行、真实手机设备或 Objective 5 外部云/4G/OSS/CDN/DB/queue 材料。
- 如果 Engineer 只能用 fixture 验证，则本轮最多形成 software proof，不提升为真实 field pass。
- 硬件材料链路虽然仍重要，但本轮不得第三次消费同一 PR #5 hardware/source/config blocker。
- 所有实现必须保持 phone-safe / diagnostics-safe，禁止暴露 raw path、credential、完整 artifact、traceback、checksum、raw ROS topic、`/cmd_vel`、串口/UART 或成功控制文案。

## 7. 需要创建或更新的 sprint 文档

计划阶段已创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实现后必须继续创建或更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
