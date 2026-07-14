# O3 Map Server TF Source Recovery Pre-Start

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.11_22-48_o3_map_server_tf_source_recovery/`
- Product owner: `product-okr-owner`
- Planned implementation owner: `robot-algorithm-engineer`
- Date: `2026-07-11`
- Related prior sprint:
  - `sprints/2026.07.11_21-47_o3_amcl_lifecycle_path_generation_repair/`

## 上轮未完成项

上一轮 `21-47` 已把 `/amcl` lifecycle 推进到最终 live artifact 的 `active [3]`，这是当前 no-motion chain 的新增 supporting delta；但以下门槛仍未通过：

- `map_server_active=false`
- `managed_runtime_started=false`
- `amcl_pose_observed=false`
- `tf_source_probe_not_executed`
- `map_to_odom_dynamic.observed=false`
- `path_generation_requested=true`
- `path_generation_attempted=false`
- `path_generated=false`

因此本轮不再重复证明 `/amcl active [3]` 本身，而是继续拆开两个更靠前的 blocker：

1. `map_server_active=false`
2. `tf_source_probe_not_executed`

## Blocker 重复消费判断

本轮不按“同一根因第三轮重复消费”处理，理由如下：

1. `20-46` 的主要 blocker 是 `/amcl inactive [2]`、stale `/amcl_pose`、dynamic `map->odom` missing 和 localization/path gate not ready。
2. `21-47` 已把 `/amcl` lifecycle 推进到 `active [3]`，并把主 blocker 收口到 `map_server_lifecycle_not_active_during_preflight`、`tf_source_probe_not_executed` 和 `localization_not_ready_for_path_generation`。
3. 本轮目标是继续把 `map_server_active=false` 与 TF source inventory 拆解成更窄 root cause，避免原样复述上轮 closeout。

若本轮结束后仍不能把 `map_server_active=false` 或 `tf_source_probe_not_executed` 进一步前移成可修复的单点 root cause，`final.md` 必须明确说明是否已接近重复消费红线，并给出下一轮是否需要升级 CEO 决策。

## 用户价值和产品北极星

普通手机用户真正关心的是“机器人能否沿固定路线稳定完成送垃圾任务”。本轮仍不直接证明送达闭环；本轮的价值是把真实板 no-motion localization chain 从“planner-only path 仍不能 attempt”推进到“localization/TF gate ready 后可尝试 `ComputePathToPose`”，为后续 route execution、delivery/operator acceptance 和 HIL 铺路。

## 本轮 Owner 和协作边界

- 单线 owner：`robot-algorithm-engineer`
- Product 只负责计划、边界、验收口径和后续 closeout，不直接做实现。
- 本轮不拆给 O5/O6/O7/UI/cloud owner，避免 support-only 或读回类工作再次侵占最低有效抓手。

## 本轮核心抓手

1. 先确认 `map_server_active=false` 是 lifecycle、map source、preflight 时序还是 managed runtime clean-up 问题。
2. 单独恢复 TF source probe，让 `tf_source_probe_not_executed` 变成可读 inventory，而不是继续留空。
3. 在 `/amcl active [3]` 既有事实不回退的前提下，恢复 fresh `/amcl_pose` 与 dynamic `map->odom` 前置证据。
4. 只有 localization/TF gate ready 后，才允许 planner-only `ComputePathToPose` attempt。

## 验收口径

本轮计划阶段必须明确：

- O5 虽是最低 Objective，但当前继续 O5 support-only 不计 OKR 增量
- 单线 owner 为 `robot-algorithm-engineer`
- 文件范围、接口边界、验收命令和 no-motion 风险边界完整
- `ComputePathToPose` attempt 的前置条件是 localization/TF gate ready

后续 implementation 阶段至少要争取以下之一：

- `map_server_active=true`
- `tf_source_probe_not_executed` 被替换为具体的 TF source inventory / blocked reason
- `amcl_pose_observed=true`
- `map_to_odom_dynamic.observed=true`
- 若前置门槛 ready，则 `path_generation_attempted=true`

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

- map_server / AMCL / TF source / readiness / probe
- planner-only `ComputePathToPose` attempt
- 且前提是 localization/TF gate 已 ready
