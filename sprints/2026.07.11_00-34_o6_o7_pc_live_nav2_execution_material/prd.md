# O6/O7 PC Live Nav2 Execution Material PRD

## 用户价值

普通用户需要看到机器人路线执行到底卡在哪里：是 Nav2 没接上、底盘命令没发出、UART 没触达，还是轮速反馈/送达确认缺失。本轮把已有真实 PC live Nav2 执行材料结构化，让 O6/O7 能展示“Nav2/bridge 已发非零底盘命令并观察到 IMU 运动迹象，但 wheel L/R 和 delivery 仍未完成”。

## OKR 映射

- O6：数据存档与模型/打标平台需要能存档 route execution material，而不是只看离线 route bag 或 wrapper。
- O7：PC 运营调试平台需要能消费真实 PC live execution material，给 operator 清楚的下一步。
- O5：保持最低但本轮不推进，原因是真实 production external evidence 缺失。
- O1：不继续同一 current HIL blocker 的 historical material 包装。

## 范围

本轮只做安全 material intake、archive/readback 和 UI 消费，不执行新的 Nav2、manual、keyboard、delivery、stop、`/cmd_vel` 或真实硬件命令。

## 必须字段

- `schema`
- `proof_scope`
- `status`
- `task_id`
- `source_sprint`
- `goal_accepted`
- `cancel_accepted`
- `uses_base_uart`
- `base_command_nonzero_observed`
- `base_command_nonzero_count`
- `base_feedback_sample_count`
- `base_feedback_lr_nonzero_proven`
- `base_feedback_imu_attitude_delta_observed`
- `route_execution_success=false`
- `delivery_success=false`
- `safe_to_control=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`
- `hil_pass=false`
- `blocked_reasons`
- `next_required_evidence`

## 非目标

- 不证明真实 delivery success。
- 不证明 current live rerun。
- 不归档 O5 production KR。
- 不把 `robot_control_executed=true` 从源材料抬到 O6/O7 顶层控制字段。
- 不开放任何新控制入口。

## 成功标准

三段链路均通过各自测试，O7 文案/结构能区分：

- 已有真实 PC live Nav2 material：goal accepted、UART used、base command nonzero、IMU attitude delta observed。
- 仍缺：same-window WAVE ROVER wheel L/R nonzero、delivery result/operator confirmation、current production cloud。
