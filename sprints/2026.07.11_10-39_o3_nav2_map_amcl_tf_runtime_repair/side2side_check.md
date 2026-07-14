# O3 Nav2 Map AMCL TF Runtime Repair Side2Side Check

## 验收结论

本轮 `sprints/2026.07.11_10-39_o3_nav2_map_amcl_tf_runtime_repair/` 完成 epic sprint 验收。目标不是继续包装 O5 support-only 进度，而是在现场 O3 no-motion lane 中把 Nav2 runtime、AMCL 和 TF blocker 从“lifecycle unavailable + refresh 超时”推进到更具体的软件根因。

结论：本轮没有拿到 `map_frame_observed=true`、`map_to_odom=true`、`map_to_base_link=true`，也没有 same-run `path_generated=true`。但本轮确实新增了两类有效现场事实：

- 真实 helper 缺陷已被确认并修复：板端 direct helper 原先稳定触发 `UnboundLocalError: lifecycle_active referenced before assignment`，本轮已修掉并同步到板端。
- 修复后 direct helper 能在 no-motion 条件下完成整轮 proof，证明更强的现场事实已经存在：`managed_runtime_started=true`、`map_server_active=true`、`amcl_active=true`、`initialpose_published=true`、`initialpose_publish_method=rclpy_inprocess_burst`、`initialpose_subscriber_count=1`、`amcl_pose_observed=true`、`amcl_pose_frame_id=map`、`odom_frame_observed=true`、`base_link_to_laser_frame=true`，但最终仍收敛到 `map_to_odom_not_observed`、`map_to_base_link_blocked_by_missing_map_to_odom`、`localization_not_ready_for_path_generation`。

## 证据对照

本地验证：

```text
bash -n o11_nav2_lifecycle.sh: 通过
py_compile: 通过
targeted unittest: Ran 181 tests in 2.544s OK (skipped=1)
helper recheck unittest: Ran 44 tests in 2.203s OK
bringup static tests: Ran 23 tests in 0.045s OK
local dry-run: status=dry_run_template_only_not_proven
scoped git diff --check: 通过
```

真实板 preflight artifact：

```text
artifact=sprints/2026.07.11_10-39_o3_nav2_map_amcl_tf_runtime_repair/artifacts/live_nav2_map_amcl_tf.raw.json
blocked_reason=blocked_refresh_readback_failed
safe_to_control=false
robot_control_executed=false
delivery_success=false
hil_pass=false
```

direct helper artifact：

```text
artifact=sprints/2026.07.11_10-39_o3_nav2_map_amcl_tf_runtime_repair/artifacts/live_nav2_direct_helper.raw.json
proof.elapsed_ms=64285
managed_runtime_started=true
map_server_active=true
amcl_active=true
initialpose_published=true
initialpose_publish_method=rclpy_inprocess_burst
initialpose_subscriber_count=1
amcl_pose_observed=true
amcl_pose_frame_id=map
odom_frame_observed=true
base_link_to_laser_frame=true
map_frame_observed=false
map_to_odom=false
map_to_base_link=false
path_generated=false
path_point_count=0
```

direct helper 最终 root cause：

```text
map_to_odom_not_observed
map_to_base_link_blocked_by_missing_map_to_odom
localization_not_ready_for_path_generation
```

preflight / runtime 预算对照：

```text
nav2_refresh.returncode=28
nav2_refresh.curl_max_time_s=38
nav2_refresh.process_timeout_s=42
direct_helper.elapsed_ms=64285
```

这说明当前 `/api/nav2/proof/refresh` 仍拿不到 helper 最终 body，不是因为 generic launch crash，而是外层等待预算小于 helper 完成预算。

## OKR 判断

- O5：保持约 `~85%`。本轮没有真实 production external evidence，不消费 O5 support-only。
- O1/O6/O7：保持约 `~93%`。本轮没有 current live HIL、same-run path success、route/material 新增、delivery record、operator acceptance 或 production readback。
- 现场 O3 lane：本轮把 live root cause 从 `lifecycle unavailable` 继续推进到“AMCL 已可发布 pose，但 `map->odom` 仍缺失，且 refresh 外层预算仍不足”。
- KR：不归档。

## 剩余风险

- direct helper 里的 `map_server_active=true`、`amcl_active=true` 和 `amcl_pose_observed=true` 还没有通过 preflight HTTP body 同步回读到主 artifact，外层仍是 `blocked_refresh_readback_failed`。
- `map_frame_observed=false`、`map_to_odom=false`、`map_to_base_link=false`，说明定位链关键 TF 仍未真正建立。
- `path_generated=false`、`path_point_count=0` 继续固定，不能把 direct helper 的更强 AMCL 证据误写成 same-run path success。
- 本轮所有结论仍保持 no-motion 边界，不证明 safe-to-control、HIL、delivery success、真实路线执行成功或 production cloud 证据。

## 下一轮验收建议

下一轮继续现场 O3 lane，并直接围绕 direct helper 已暴露出的真实 blocker 修：

1. 先修 `map->odom` TF；
2. 再确认 `map->base_link` 是否随 `map->odom` 恢复而出现；
3. 在 TF 根因修掉之后，再决定是缩短 helper 路径，还是上调 preflight refresh budget；
4. 只有出现 `map_to_odom=true`、`map_to_base_link=true`、same-run path 或新路线材料后，才允许继续推动 O6/O7 消费链。
