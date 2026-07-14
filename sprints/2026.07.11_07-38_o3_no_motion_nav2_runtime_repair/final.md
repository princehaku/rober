# O3 No-Motion Nav2 Runtime Repair Final

## 复盘结论

本轮 `sprints/2026.07.11_07-38_o3_no_motion_nav2_runtime_repair/` 完成 epic sprint 收口。O5 仍是最低主 Objective，约 `~85%`，但当前缺真实 production external evidence，继续 O5 support-only/readiness/probe 不允许计主 OKR 增量。本轮因此继续现场 O3 lane，并从诊断进入 no-motion runtime repair。

本轮修掉两处真实影响启动链的漂移：

- `o11_nav2_lifecycle.sh start` 启动 `__run` 子进程时不再丢失 `base_enabled`、`lidar_enabled`、LiDAR 串口/波特率和 `static_laser_tf_enabled`。
- `/api/nav2/proof/refresh` 在 artifact 记录 `managed_runtime_started=true` 时，顶层 readback 现在回填 `starts_nav2=true`，避免 no-motion managed runtime 被误读成未启动。

同步到真实板后，`live_nav2_refresh_after_sync.raw.json` 已证明顶层 `starts_nav2=true` 与 `managed_runtime_started=true` 生效；但同轮仍 `path_generated=false`、`path_generation_succeeded=false`、`path_point_count=0`，root cause 留在 `/amcl_pose_once_not_observed`、`map_to_odom_not_observed` 和 `map_to_base_link_blocked_by_missing_map_to_odom`。

## 实际改动

Robot Software owner 修改：

- `onboard/scripts/o11_nav2_lifecycle.sh`
- `onboard/scripts/upper_robot_api.py`
- `onboard/tests/test_upper_robot_api.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_07-38_o3_no_motion_nav2_runtime_repair/tech-done.md`
- `sprints/2026.07.11_07-38_o3_no_motion_nav2_runtime_repair/artifacts/**`

主节点新增：

- `sprints/2026.07.11_07-38_o3_no_motion_nav2_runtime_repair/pre_start.md`
- `sprints/2026.07.11_07-38_o3_no_motion_nav2_runtime_repair/prd.md`
- `sprints/2026.07.11_07-38_o3_no_motion_nav2_runtime_repair/tech-plan.md`
- `sprints/2026.07.11_07-38_o3_no_motion_nav2_runtime_repair/side2side_check.md`
- `sprints/2026.07.11_07-38_o3_no_motion_nav2_runtime_repair/final.md`

Product 同步更新：

- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证证据

子 agent 验证：

```text
bash -n onboard/scripts/o11_nav2_lifecycle.sh
通过

python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/field_route_evidence_preflight.py
通过

python3 -m unittest onboard.tests.test_upper_robot_api onboard.tests.test_field_route_evidence_preflight
Ran 123 tests in 0.276s
OK (skipped=1)

python3 -m unittest discover -s onboard/src/ros2_trashbot_bringup/test
Ran 23 tests in 0.045s
OK

local dry-run preflight
status=dry_run_template_only_not_proven

scoped git diff --check
通过
```

真实板 after-sync refresh：

```text
status=blocked_with_root_cause
starts_ros2=true
starts_nav2=true
managed_runtime_opt_in=true
managed_runtime_started=true
path_generated=false
path_generation_succeeded=false
path_point_count=0
safe_to_control=false
robot_control_executed=false
delivery_success=false
hil_pass=false
root_causes=[
  /amcl_pose_once_not_observed,
  map_to_odom_not_observed,
  map_to_base_link_blocked_by_missing_map_to_odom,
  helper_process_timeout_after_partial_artifact
]
```

## OKR 结论

- O5：保持约 `~85%`。本轮没有真实 production external evidence。
- O1/O6/O7：保持约 `~93%`。本轮没有 route execution、delivery record、operator acceptance、production readback 或 current live HIL。
- 现场 O3 lane：新增 no-motion runtime repair evidence，但没有 same-run path/material success。
- KR：本轮不归档 KR，不调整任何 Objective 百分比。

## Proof Boundary

本轮 proof boundary：

- `software_proof_real_board_no_motion_nav2_runtime_repair_only`
- `managed_runtime_start_readback_fixed`
- `blocked_amcl_map_tf_not_ready`

本轮不证明：

- same-run path generation success；
- live route execution success；
- safe-to-control；
- HIL pass；
- delivery success；
- production cloud / DB / queue / OSS / CDN / phone/browser external proof。

## 剩余风险

- AMCL 仍未输出可用 `/amcl_pose`。
- `map->odom` 未建立，`map->base_link` 被级联阻塞。
- SSH preflight 层仍看到 `/map` / `/amcl_pose` topic metadata unavailable，说明 ROS graph 仍不稳定或 runtime 未在 probe 窗口内保持 ready。

## 下一轮建议

下一轮继续 O3 现场 lane，但不要重复本轮参数透传和 readback 修复。优先排查 AMCL/TF：

1. 确认 `map_server`、`amcl`、`planner_server` 在 after-sync runtime 中是否稳定 active；
2. 定位 `/amcl_pose_once_not_observed` 的直接原因；
3. 让 `map->odom` 出现后再验证 `map->base_link`；
4. 重跑 `/api/nav2/proof/refresh`，只有拿到 `path_generated=true` 或新的 route/material artifact 后，才允许推动 O6/O7 消费链或 OKR 增量。
