# O3 Runtime Graph TF Probe Hardening PRD

## 用户价值和产品北极星

产品北极星不变：普通手机用户把垃圾交给机器人后，机器人能沿固定路线稳定完成送达。当前最缺的不是新的状态包装，而是让真实板 no-motion localization chain 真正进入 planner-only path generation attempt。本 sprint 的价值是把 runtime graph、AMCL inventory runtime 和 TF source fallback 修到可复验状态，再决定是否允许 planner-only path attempt，为后续真实 route execution 和 delivery evidence 铺路。

## OKR 对齐和方向判断

- O5 当前约 `85%`，仍是最低 Objective，但缺口是明确的真实 production/external evidence。最近 O5 已固定 `okr_credit_allowed=false`；没有新 external material 时继续做 wrapper/readback/support-only 不计主 OKR 增量。
- O1、O6、O7 当前约 `93%`。本轮不是追表面百分比，而是继续补 mission chain 的 no-motion 前置门槛。
- 方向判断：
  - `继续` O3/O1 strict no-motion supporting lane
  - `暂停` O5 support-only
  - `不调整` O5/O1/O6/O7 百分比
  - `不归档` KR

## 问题定义

截至 `22-48` final，真实板已经证明：

- `board_source_preflight_ready`
- `cli_ready=true`
- `runtime_ready=true`
- `managed_runtime_started=true`

但最终 live artifact 仍然是：

- `managed_runtime_wait_timeout`
- `rclpy_node_names_failed`
- `map_server_active=false`
- `amcl_active=false`
- `amcl_pose_observed=false`
- `/tf_topic_missing`
- `tf_source_root_cause_detail.amcl_param_probe_error` 命中 `librcl_action.so` / `_rclpy_pybind11`
- `path_generation_attempted=false`
- `path_generated=false`

因此本 sprint 的问题不是“再读回一点 supporting 状态”，而是“能否把 runtime graph、AMCL inventory runtime 和 TF source gate 修到允许 planner-only path attempt 的门槛”。

## 范围内

- 只处理 O3/O1 no-motion localization/path readiness
- 只派 `robot-algorithm-engineer` 单线闭环
- 只允许 managed runtime wait graph probe、node graph inventory、AMCL rclpy inventory runtime、TF source probe fallback、planner-only path generation gate 相关实现和验证
- 只接受 strict no-motion 证据

## 范围外

- O5 production external evidence
- O6/O7 archive/readback/consumer/UI
- 手机/Web/API
- 真实 route execution
- delivery/operator acceptance
- HIL pass
- 发布 `/cmd_vel`
- `/api/base/manual`
- NavigateToPose
- WAVE ROVER UART

## 成功标准

计划阶段成功标准：

- 三份文档完整建立 epic 计划链：`pre_start.md`、`prd.md`、`tech-plan.md`
- `tech-plan.md` 包含 `## OKR 最低优先级核对`
- owner、文件范围、接口边界、验收命令和 no-motion 约束可直接给 Algorithm worker 执行

implementation 阶段目标成功标准：

- 至少把 `managed_runtime_wait_timeout`、`rclpy_node_names_failed` 或 `/tf_topic_missing` 向前推进一层，且证据能明确说明：
  - runtime graph timeout 的真实边界
  - node graph inventory 是否已可稳定执行
  - AMCL inventory runtime 是否仍被 `librcl_action.so` / `_rclpy_pybind11` 阻塞
  - TF source probe fallback 是否已执行并得到结论
  - 只有当上述 gate ready 时，`path_generation_attempted=true`
  - 若仍 blocked，必须给出比 `22-48` 更窄的 root cause

## 不加分边界

以下结果都不能算 OKR 新进展：

- 继续重复 O5 support-only packet/readback
- 只有 `managed_runtime_started=true`
- 只有 `path_generation_requested=true`
- 只有 partial artifact、wrapper 或总结性 readback，没有更窄 root cause 或新的 attempted/generated 事实
- 任何突破 no-motion 边界的“假成功”

## 验收口径

- 文档必须让后续 worker 能直接复制命令执行
- 必须显式保留所有 safety/control/HIL/delivery false 字段
- 必须写明：只有 runtime graph、AMCL inventory 与 TF source gate ready，才允许 planner-only `ComputePathToPose` attempt
- 最终 closeout 若没有 `path_generation_attempted=true`，也必须证明 blocker 已从 `22-48` 进一步缩窄，不能原样复述
