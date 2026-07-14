# O3 ROS Daemon-safe Localization Recovery Pre-start

## sprint_type

sprint_type: epic

## 上轮未完成项

- `sprints/2026.07.11_08-39_o3_amcl_tf_bringup_repair/` 已把 AMCL `/initialpose` 发布链升级为进程内 `rclpy` burst publisher，并把 `/api/nav2/proof/refresh` SSH readback 修成硬超时和自然返回。
- 真实板 artifact `live_amcl_tf_bringup_repair.raw.json` 仍输出 `status=blocked_live_localization_chain_not_ready`、`path_generated=false`。
- 当前窗口 `/scan`、`/amcl_pose`、`map->odom`、`map->base_link` 仍未 observed。

## 本轮 blocker 判断

- O5 仍是 `OKR.md` 4.1 当前最低主 Objective，约 `~85%`。
- O5 缺真实 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic 和真实 phone/browser evidence；继续 O5 readiness/probe/support packet 会重复消费 `no_real_production_external_evidence`，且 `okr_credit_allowed=false`。
- 本轮继续现场 O3 lane，因为真实板已经可达，且 live raw JSON 暴露了更具体的新根因：多条板端 ROS2 CLI 查询返回 `RuntimeError: !rclpy.ok()`，这更像 ROS daemon/CLI graph 查询层损坏，而不是单纯 topic 不存在。

## 本轮目标

在 no-motion 安全边界内，把 live localization probe 改成 daemon-safe：

- 检测板端 `ros2 daemon` / CLI graph 查询是否处于坏状态；
- 必要时 stop/start daemon 或使用 bypass/retry 方式重新采 topic、lifecycle 和 TF；
- 复跑 `/scan`、`/amcl_pose`、`map->odom`、`map->base_link` 与 `/api/nav2/proof/refresh`；
- 若 daemon 修复后仍 blocked，必须把 blocker 重新分类为传感器、map server、AMCL、TF 或 launch/runtime 层。

## Owner

- 主责：`robot-algorithm-engineer`
- 主节点职责：派单、验收、更新 `side2side_check.md` / `final.md` / 自动化记忆。

## 安全边界

- 禁止 `/cmd_vel`。
- 禁止 `/api/base/manual`。
- 禁止 Nav2 `NavigateToPose` goal。
- `path_generation_opt_in=true` 只允许 ComputePathToPose planner-only readback。
- 所有 artifact 必须固定 `safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`、`hil_pass=false`，除非真实 HIL 另行验收。
