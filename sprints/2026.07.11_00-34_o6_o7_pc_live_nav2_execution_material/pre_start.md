# O6/O7 PC Live Nav2 Execution Material

## sprint_type

sprint_type: epic

## 背景

`OKR.md` 4.1 中当前最低 Objective 是 O5，约 `~85%`。但最近 O5 sprint `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/final.md` 已明确 `okr_credit_allowed=false`，原因是缺真实 external production evidence：公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic 和真实 phone/browser。

最近两个 O1 sprint 已连续把剩余缺口指向 current live HIL、same-run wheel L/R、外部视频、LiDAR motion delta、Nav2 route execution 和 safety acceptance。继续消费同一类 historical HIL 缺口会触发同一 blocker 重复消费风险。

本轮切到 O6/O7 的原因：`sprints/2026.07.03_20-46_pc_nav2_o11_tail_wasd_back_alias/tech-done.md` 已记录真实 PC 7001 live Nav2 执行材料，包含 `goal_accepted=true`、`uses_base_uart=true`、`base_command_nonzero_observed=true`、`base_command_nonzero_count=733`、`base_feedback_sample_count=5941`、`base_feedback_lr_nonzero_proven=false`、`base_feedback_imu_attitude_delta_observed=true`。该材料尚未作为结构化 additive section 进入 Algorithm -> O6 -> O7 的同 task evidence chain。

## 本轮目标

把 2026-07-03 PC live Nav2 execution material 转成安全、脱敏、fail-closed 的 additive section：

- Algorithm 生成 `trashbot.pc_live_nav2_execution_material.v1`。
- O6 archive/readback/include 回读 `trashbot.o6.pc_live_nav2_execution_material.v1`。
- O7 consumer/UI 默认展示该 material，并明确它不是 delivery success。

## Owner

- `robot-algorithm-engineer`：producer 与 manifest additive。
- `robot-software-engineer`：O6 archive/readback/include。
- `full-stack-software-engineer`：O7 consumer/UI。
- Product closeout 由主节点汇总，必要时再派 `product-okr-owner`。

## 验收口径

- 必须保留 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`route_execution_success=false`、`hil_pass=false`。
- 可以消费并展示真实执行材料字段：`goal_accepted=true`、`uses_base_uart=true`、`base_command_nonzero_observed=true`、`base_command_nonzero_count=733`、`base_feedback_imu_attitude_delta_observed=true`。
- `base_feedback_lr_nonzero_proven=false` 和 result window timeout/cancel 必须保留，不能外推为 route execution success 或送达成功。
- 本轮 proof boundary：`software_proof_pc_live_nav2_execution_material_only`。

## 风险

- 源材料来自既有 sprint `tech-done.md` 的 live 验证记录，而不是本轮重新连上车机执行。必须写成 prior live material intake，不写成 current live rerun。
- O5 仍是最低 Objective，但真实 production external evidence 不在当前环境，不能靠 support-only packet 提升 O5。
- O1 current HIL 仍需要真实 same-run HIL acceptance、wheel L/R、外部视频和 LiDAR delta。
