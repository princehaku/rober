# O3 Map Odom TF Path Recovery Pre-start

## sprint_type

`sprint_type: epic`

## 上轮未完成项

- 最新收口：`sprints/2026.07.11_10-39_o3_nav2_map_amcl_tf_runtime_repair/final.md`
- 已完成事实：real-board direct helper 已证明 `managed_runtime_started=true`、`map_server_active=true`、`amcl_active=true`、`initialpose_published=true`、`amcl_pose_observed=true`、`amcl_pose_frame_id=map`、`odom_frame_observed=true`、`base_link_to_laser_frame=true`。
- 仍未完成：`map_frame_observed=false`、`map_to_odom=false`、`map_to_base_link=false`、`path_generated=false`。
- 额外运行时问题：外层 preflight 仍是 `blocked_refresh_readback_failed`，因为 `curl_max_time_s=38` 小于 direct helper `elapsed_ms≈64285`。

## 本轮目标

本轮继续 O3 现场定位链路，但服务于 O1/O6/O7 后续同 run path/material 缺口：不做 O5 production readiness/readback，不扩展 wrapper，只修当前最前置 blocker。

目标：

1. 让 no-motion managed runtime 能稳定解释或恢复 `map->odom`。
2. 若 `map->odom` 恢复，则复验 `map->base_link` 与 same-run path generation。
3. 若 `map->odom` 未恢复，则 artifact 必须给出比 `map_to_odom_not_observed` 更具体的 AMCL broadcast 条件缺口，例如 scan、map、params、particle/filter、time 或 frame contract。
4. 让外层 preflight 能自然回读 helper 最终 body，避免只剩 `curl (28)`。

## Blocker 重复消费核对

最近两轮 root cause：

- `2026.07.11_09-39_o3_ros_daemon_safe_localization_recovery`：generic ROS daemon 已排除，root cause 转为 map server / AMCL / TF runtime not ready。
- `2026.07.11_10-39_o3_nav2_map_amcl_tf_runtime_repair`：runtime 已进入 direct helper，root cause 收敛为 `map_to_odom_not_observed` 与 helper/preflight 预算不匹配。

本轮不是重复消费 generic daemon、lifecycle unavailable 或 O5 production external evidence；本轮只消费新的具体 blocker：`blocked_map_to_odom_tf_missing`。

## Owner 与分工

- 主责 owner：`robot-software-engineer`
  - 负责实现、测试、live/preflight 验证、`tech-done.md` 更新。
- 并行只读咨询：`robot-algorithm-engineer`
  - 负责基于现有代码和 artifacts 复核 AMCL/Nav2 最小链路、参数和 TF 条件，不改文件。
- Product closeout：实现完成后由 `product-okr-owner` 或主节点按证据更新 `side2side_check.md`、`final.md`、`OKR.md` 与 `docs/process/okr_progress_log.md`。

## 验收口径

必须保留 no-motion safety boundary：

- `safe_to_control=false`
- `robot_control_executed=false`
- `delivery_success=false`
- `hil_pass=false`
- 禁止 `/cmd_vel`、`/api/base/manual`、NavigateToPose 或真实底盘运动。

最低验收：

- local unit/static 验证通过；
- local dry-run artifact 可生成；
- live SSH preflight 或 direct helper 至少一个自然返回并落盘；
- artifact 对 `map->odom` 给出恢复事实或更具体 blocker；
- sprint `tech-done.md` 写清实际改动、验证输出、剩余风险。
