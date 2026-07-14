# O3 AMCL Lifecycle Path Generation Repair Pre-Start

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.11_21-47_o3_amcl_lifecycle_path_generation_repair/`
- Product owner: `product-okr-owner`
- Planned implementation owner: `robot-algorithm-engineer`
- Date: `2026-07-11`
- Related prior sprints:
  - `sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair/`
  - `sprints/2026.07.11_20-46_o3_amcl_tf_final_artifact_bounded_probe/`

## 上轮未完成项

上一轮 `20-46` 已把旧 `board_source_preflight_ros2_cli_unavailable` 推进到 `board_source_preflight_ready`，并确认 `ros2_cli_ok=true`、`rclpy_import_ok=true`，因此本轮不再回头消费旧 source/CLI blocker。

上轮遗留且必须继续处理的未完成项：

- `/amcl` lifecycle `inactive [2]`，`amcl_readiness_summary.ready=false`
- `/amcl_pose` 虽有 topic type 和 sample，但 sample stale，`age_ms=85437`
- `/scan` BEST_EFFORT / RELIABLE 双 QoS timeout
- `/map_once_not_observed`
- `cli_initialpose_publish_failed`
- `map_to_odom_dynamic_source_missing`
- `map_to_base_link_blocked_by_missing_map_to_odom`
- `path_generation_requested=true` 但 `path_generation_attempted=false`
- 远端 helper 仍需人工中断，natural-return cleanup 未完成

## Blocker 重复消费判断

本轮不属于同一 blocker 的第三次重复消费，理由如下：

1. `19-46` 的核心修复对象是旧 source/CLI blocker，结果已稳定推进到 `board_source_preflight_ready`。
2. `20-46` 的核心 blocker 已切换为 AMCL lifecycle、signal freshness、dynamic TF 和 planner gate。
3. 本轮继续处理的是新的 localization/path gate blocker，不是继续包装 `ros2_cli_ok=false` 或泛化 source/CLI 失败。

因此本轮不需要升级 CEO 决策；但若本轮结束后仍无法把 blocker 进一步缩窄到 `/amcl` lifecycle clean active、fresh `/scan`/`/map`/`/amcl_pose` 或 dynamic `map->odom` 的具体 repair 点，则 `final.md` 必须明确说明是否已接近第三轮重复消费，并给出下一轮是否需要改 owner 或升级决策的判断。

## 用户价值和北极星

普通手机用户的核心价值仍是“把垃圾交给机器人后，机器人能沿固定路线安全送到垃圾桶/垃圾站并返回”。本轮不直接证明送达闭环；本轮要做的是把 no-motion 定位和 planner-only path generation 前置门槛推进到可尝试 `ComputePathToPose`，为后续 route execution、delivery/operator acceptance 和 HIL 留出真实入口。

## 本轮 Owner 和协作边界

- 单线 owner：`robot-algorithm-engineer`
- Product 只负责计划、边界、验收口径和后续 closeout，不直接做实现。
- 本轮不并行拆给其他 engineer，避免在共享 helper/artifact 合同上制造耦合返工。

## 验收口径

本轮验收只认以下层级的推进，不认 O5 support-only 包装，也不认 O6/O7 读回类增量：

必需：

- 计划文档明确写出 O5 虽最低但本轮不直接做 O5 的具体理由
- 写清 `robot-algorithm-engineer` 单线闭环 owner
- 写清文件范围、接口边界、验收命令和 no-motion 强约束
- 明确只有 localization/TF gate ready 后才允许进入 planner-only path generation attempt

后续 implementation 阶段应至少争取以下之一：

- `/amcl` lifecycle clean active
- `/scan`、`/map`、`/amcl_pose` freshness 恢复到可用于 localization gate
- dynamic `map->odom` 出现
- `path_generation_attempted=true`，且仍保持 no-motion safety false 字段

本轮不加分边界：

- 不因为 `path_generation_requested=true` 就算 mission 进展
- 不因为 planner ready 或 topic type 可见就算 path success
- 不因为 support-only packet/readback 再次包装就算 O5/O6/O7 推进

## No-Motion 安全边界

本轮及后续 implementation 必须继续 fail-closed：

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`

严格禁止：

- 发布 `/cmd_vel`
- 调用 `/api/base/manual`
- 发送 NavigateToPose
- 打开 WAVE ROVER UART

允许范围仅限：

- lifecycle / map / AMCL / TF / readiness / probe
- planner-only `ComputePathToPose` attempt
- 但前提是 localization/TF gate 已 ready
