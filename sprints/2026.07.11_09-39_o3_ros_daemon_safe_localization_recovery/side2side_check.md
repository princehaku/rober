# O3 ROS Daemon-safe Localization Recovery Side2Side Check

## 验收结论

本轮 `sprints/2026.07.11_09-39_o3_ros_daemon_safe_localization_recovery/` 完成 epic sprint 验收。目标不是继续包装 O5 support-only 进度，而是在现场 O3 no-motion lane 中把 ROS daemon/CLI fault 与真实 localization blocker 拆开。

结论：本轮没有拿到 `amcl_pose_observed=true`、`map_to_odom=true`、`map_to_base_link=true`，也没有 same-run `path_generated=true`。但本轮确实新增了有效现场诊断事实：

- live localization probe 已具备 daemon-safe readback 能力，能识别 `!rclpy.ok()` / XMLRPC fault，并只对 ROS graph/lifecycle/TF 只读查询执行 stop/start retry。
- 真实板本轮证明当前 blocker 不是 ROS daemon fault：`daemon_fault_detected=false`、`daemon_recovered=false`、`retry_attempts=0`。
- root cause 已从 generic ROS CLI fault 下钻到 `map_server_not_active`、`amcl_not_active`、`tf_missing`，同时保留 `/scan observed=true` 这一条现场正向事实。

## 证据对照

本地验证：

```text
py_compile: 通过
field_route_evidence_preflight + upper_robot_api tests: Ran 126 tests in 0.268s OK (skipped=1)
bringup static tests: Ran 23 tests in 0.041s OK
local dry-run: status=dry_run_template_only_not_proven
scoped git diff --check: 通过
```

真实板 live artifact：

```text
artifact=sprints/2026.07.11_09-39_o3_ros_daemon_safe_localization_recovery/artifacts/live_daemon_safe_localization.raw.json
status=blocked_refresh_readback_failed
safe_to_control=false
robot_control_executed=false
delivery_success=false
hil_pass=false
```

daemon / root-cause 关键事实：

```text
daemon_fault_detected=false
daemon_recovered=false
retry_attempts=0
/scan observed=true
/amcl_pose observed=false
map->odom observed=false
map->base_link observed=false
root_cause_layers=[map_server_not_active, amcl_not_active, tf_missing]
```

live readback 细节：

```text
/amcl_pose topic_type=geometry_msgs/msg/PoseWithCovarianceStamped
/amcl_pose publisher_count=0
/map topic_type=null
/map_server lifecycle unavailable
/amcl lifecycle unavailable
/planner_server lifecycle unavailable
managed_map_yaml.basename=trashbot_map.yaml
managed_map_yaml.exists=true
nav2_refresh.status=refresh_command_failed
nav2_refresh.returncode=28
nav2_refresh.failure_summary=curl: (28) Operation timed out after 38000 milliseconds with 0 bytes received
```

## OKR 判断

- O5：保持约 `~85%`。本轮没有真实 production external evidence，不消费 O5 support-only。
- O1/O6/O7：保持约 `~93%`。本轮没有 current live HIL、same-run path success、route/material 新增、delivery record、operator acceptance 或 production readback。
- 现场 O3 lane：新增 daemon-safe localization probe 与更细的 live root-cause 分层，但还没有 same-run path/material success。
- KR：不归档。

## 剩余风险

- `/scan` 已 observed，但 `/map` 未建立、`/amcl_pose` 无 publisher、`map->odom` / `map->base_link` 仍缺失，说明定位链主 blocker 已转为 map server / AMCL / TF runtime。
- `/api/nav2/proof/refresh` 仍 `curl (28)` 超时，refresh readback 还没有穿透当前 runtime/localization blocker。
- 本轮所有结论仍保持 no-motion 边界，不证明 safe-to-control、HIL、delivery success、真实路线执行成功或生产云证据。

## 下一轮验收建议

下一轮继续现场 O3 lane，但不要再重复 generic daemon fault 方向。优先拆开验证：

1. 直接确认 `/map_server`、`/amcl`、`/planner_server` 为什么 lifecycle unavailable；
2. 解释 `/map topic_type=null` 与 `managed_map_yaml.exists=true` 之间的 runtime 缺口；
3. 把 `/amcl_pose publisher_count=0` 修到可观测，再重采 `map->odom` / `map->base_link`；
4. 只有出现 `amcl_pose_observed=true`、`map_to_odom=true` 或同轮 path/material 后，才允许继续推动 O6/O7 消费链。
