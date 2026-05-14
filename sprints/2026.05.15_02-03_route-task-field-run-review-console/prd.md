# Sprint 2026.05.15_02-03 Route Task Field Run Review Console - PRD

sprint_type: epic

## 1. 用户价值

现场人员已经有 readiness 和 intake 工具，但仍要手动理解多份 JSON 的含义。本轮要把 `route_task_field_run_intake` 的 crosscheck 结果转成 operator/support 可以直接读取的复核报告：

- 当前材料是否足够进入人工复核。
- 哪些材料缺失或不一致。
- 下一次应重跑哪条命令或补采哪类材料。
- 为什么当前仍不是真实固定路线运行、HIL 或 delivery success。

这服务 Objective 2 的任务复盘闭环和 Objective 3 的固定路线验证流程，不服务 O5 外部云证明。

## 2. 成功标准

- 产出 `schema=trashbot.route_task_field_run_review_console.v1` 的 review report。
- 固定 `evidence_boundary=software_proof_docker_route_task_field_run_review_console_gate`。
- 输入为上一轮 `trashbot.route_task_field_run_intake_crosscheck.v1` 或兼容 summary。
- 输出至少包含：
  - `overall_status`
  - `review_decision`
  - `evidence_ref`
  - `missing_materials`
  - `mismatch_reasons`
  - `commands_to_rerun`
  - `operator_next_steps`
  - `phone_safe_summary`
  - `not_proven`
  - `primary_actions_enabled=false`
  - `delivery_success=false`
- diagnostics 与 mobile 只读消费该 summary，不触发 collect/dropoff/cancel、ACK、cursor、terminal ACK、HIL、production readiness、dropoff/cancel completion 或 delivery success。

## 3. 非目标

- 不接入真实串口、WAVE ROVER、Nav2 runtime、ROS graph、4G、公网云、OSS/CDN 或 production DB/queue。
- 不新增广泛测试套件；只加围栏级 targeted tests、`py_compile`、`node --check` 和 scoped diff check。
- 不把 `ready_for_review`、review report、diagnostics summary 或 mobile panel 写成真实送达成功。

## 4. 验收口径

Task A `autonomy-engineer`：

- 新增 review report CLI 和 targeted tests。
- CLI 能处理 pass/missing/mismatch/unsafe/unsupported schema。
- `pc-tools/README.md` 与 `docs/navigation/fixed_route_workflow.md` 说明使用方式和边界。

Task B `robot-software-engineer`：

- diagnostics 能用显式 ref 或环境变量消费 review report。
- metadata-only fence 覆盖：review report 不触发动作、ACK、cursor、terminal ACK、HIL 或 delivery success。
- `docs/interfaces/ros_contracts.md` 更新字段与边界。

Task C `full-stack-software-engineer`：

- `mobile/web` 新增只读 review panel。
- copy/display 只使用 safe summary；控制按钮 gating 不变。
- `docs/product/mobile_user_flow.md` 更新用户流程边界。

Task D `product-okr-owner`：

- 更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。
- 明确 Objective 5 仍需真实外部材料，本轮不提升 O5。
