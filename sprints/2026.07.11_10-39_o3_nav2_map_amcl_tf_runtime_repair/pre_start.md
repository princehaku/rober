# O3 Nav2 Map AMCL TF Runtime Repair Pre Start

## sprint_type

sprint_type: epic

## 上轮未完成项和 blocker

- `sprints/2026.07.11_09-39_o3_ros_daemon_safe_localization_recovery/` 已把现场 no-motion 预检从 generic ROS daemon 怀疑，推进到更具体的 runtime 缺口：
  - `/scan observed=true`
  - `/map topic_type=null`
  - `/amcl_pose topic_type=geometry_msgs/msg/PoseWithCovarianceStamped` 但 `publisher_count=0`
  - `/map_server`、`/amcl`、`/planner_server` lifecycle unavailable
  - `map->odom=false`
  - `map->base_link=false`
  - `/api/nav2/proof/refresh` 仍 `curl (28)` 超时
- O5 仍是 `OKR.md` 4.1 当前最低主 Objective，约 `~85%`，但最近两轮 O5 收口已经确认：
  - `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/final.md`
  - `sprints/2026.07.11_03-40_o5_external_evidence_or_field_execution_pivot/final.md`
- 这两轮都被同一根因 `no_real_production_external_evidence` 卡住，且 `okr_credit_allowed=false`；继续做 readiness、probe、support packet 或 review surface 会重复消费同一 blocker。

## 本轮目标

在严格 no-motion 安全边界内，把真实板 Nav2 localization runtime 从“只知道 blocked”推进到“map / AMCL / TF 明确拉起或给出更深层根因”：

1. 拉起或修复 `/map_server`、`/amcl`、`/planner_server` 的 lifecycle；
2. 让 `/map` topic 真正建立，而不是只有 map yaml 可读；
3. 让 `/amcl_pose` 从 `topic exists but publisher_count=0` 推进到有真实 publisher；
4. 建立 `map->odom`，并在此基础上争取 `map->base_link`；
5. 复跑 no-motion `/api/nav2/proof/refresh`，确认 refresh 不再停在旧的超时 / root-cause 状态。

## Owner

- 主责 owner：`robot-software-engineer`
- 主节点职责：只做任务拆解、派单、验收、后续 `side2side_check.md` / `final.md` 汇总和自动化记忆更新。

## 风险边界

- 本轮允许启动受管 Nav2 runtime，但不允许任何真实底盘运动。
- 明确禁止：
  - `/cmd_vel`
  - `/api/base/manual`
  - `NavigateToPose` goal
  - 真实底盘运动或 delivery 执行
- 即使 `starts_nav2=true`、`/map` 建立或 `path_generated=true`，也只代表 no-motion runtime / proof 进展，不代表 `safe_to_control`、`hil_pass` 或 `delivery_success`。
- 所有现场 artifact 仍必须固定 `safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`、`hil_pass=false`。
