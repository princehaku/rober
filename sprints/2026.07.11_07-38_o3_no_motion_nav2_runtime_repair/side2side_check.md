# O3 No-Motion Nav2 Runtime Repair Side2Side Check

## 验收对照

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| 不继续消费 O5 support-only blocker | 通过 | 本 sprint 明确转向 O3 no-motion Nav2 runtime repair，O5 `okr_credit_allowed=false` 保持不变 |
| 修复 `o11_nav2_lifecycle.sh start -> __run` 参数漂移 | 通过 | `o11_nav2_lifecycle.sh` 透传 `base_enabled`、`lidar_enabled`、LiDAR 串口/波特率和 `static_laser_tf_enabled` |
| 修复 managed runtime readback 漂移 | 通过 | `upper_robot_api.py` 在 `managed_runtime_started=true` 时回填 `starts_nav2=true` |
| 本地验证 | 通过 | `bash -n`、`py_compile`、`Ran 123 tests ... OK (skipped=1)`、bringup `Ran 23 tests ... OK`、local dry-run 和 scoped `git diff --check` 均通过 |
| 真实板 no-motion 证据 | 部分通过 | `live_nav2_refresh_after_sync.raw.json` 输出 `starts_nav2=true`、`managed_runtime_started=true`，但 `path_generated=false` |
| 安全边界 | 通过 | artifact 保持 `safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`、`hil_pass=false` |

## 对照结论

本轮不是 route execution 或 delivery 成功，而是修掉 no-motion Nav2 runtime 启动链中的两处软件漂移。同步后真实板已经证明 `starts_nav2=true` readback 生效，但 AMCL/TF 仍 blocked，当前不可上调 OKR 或归档 KR。

## 下一步验收焦点

下一轮不应回到 O5 readiness，也不应重复同一参数修复。应直接攻 `/amcl_pose_once_not_observed`、`map_to_odom_not_observed` 和 `map_to_base_link_blocked_by_missing_map_to_odom`，直到同轮 refresh 产生 `path_generated=true` 或更深层 root cause。
