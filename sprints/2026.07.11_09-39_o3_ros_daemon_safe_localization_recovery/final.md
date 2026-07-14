# O3 ROS Daemon-safe Localization Recovery Final

## 复盘结论

本轮 `sprints/2026.07.11_09-39_o3_ros_daemon_safe_localization_recovery/` 完成 epic sprint 收口。O5 仍是最低主 Objective，约 `~85%`，但当前缺真实 production external evidence，继续 O5 readiness/probe/support packet 不允许计主 OKR 增量，因此本轮继续现场 O3 lane。

结果是有效现场诊断推进，但仍 fail-closed。Algorithm 已把 live localization probe 改成 daemon-safe：能识别 `!rclpy.ok()` / XMLRPC fault，对 ROS graph/lifecycle/TF 只读查询执行 stop/start retry，并把 daemon/root-cause fields 写入 artifact。真实板 `live_daemon_safe_localization.raw.json` 证明本轮 blocker 已不再是 generic ROS daemon fault，而是 localization/runtime 本身：`/scan observed=true`，但 `/map` 未建立、`/amcl_pose` 无 publisher、`map->odom` / `map->base_link` 缺失，refresh 仍 `curl (28)` 超时。

因此本轮价值在于把根因从“可能是 daemon 坏了”推进到“map server / AMCL / TF / refresh runtime 仍未 ready”，而不是 same-run path、route execution 或 delivery 成功。

## 实际改动

Algorithm owner 修改：

- `onboard/scripts/field_route_evidence_preflight.py`
- `onboard/tests/test_field_route_evidence_preflight.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_09-39_o3_ros_daemon_safe_localization_recovery/tech-done.md`
- `sprints/2026.07.11_09-39_o3_ros_daemon_safe_localization_recovery/artifacts/local_preflight.raw.json`
- `sprints/2026.07.11_09-39_o3_ros_daemon_safe_localization_recovery/artifacts/live_daemon_safe_localization.raw.json`

主节点新增：

- `sprints/2026.07.11_09-39_o3_ros_daemon_safe_localization_recovery/pre_start.md`
- `sprints/2026.07.11_09-39_o3_ros_daemon_safe_localization_recovery/prd.md`
- `sprints/2026.07.11_09-39_o3_ros_daemon_safe_localization_recovery/tech-plan.md`
- `sprints/2026.07.11_09-39_o3_ros_daemon_safe_localization_recovery/side2side_check.md`
- `sprints/2026.07.11_09-39_o3_ros_daemon_safe_localization_recovery/final.md`

Product 同步更新：

- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证证据

子 agent 验证：

```text
python3 -m py_compile onboard/scripts/field_route_evidence_preflight.py onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/upper_robot_api.py
通过

python3 -m unittest onboard.tests.test_field_route_evidence_preflight onboard.tests.test_upper_robot_api
Ran 126 tests in 0.268s
OK (skipped=1)

python3 -m unittest discover -s onboard/src/ros2_trashbot_bringup/test
Ran 23 tests in 0.041s
OK

local dry-run
status=dry_run_template_only_not_proven

live ssh preflight
status=blocked_refresh_readback_failed

scoped git diff --check
通过
```

真实板 live raw JSON：

```text
status=blocked_refresh_readback_failed
safe_to_control=false
robot_control_executed=false
delivery_success=false
hil_pass=false
```

daemon / localization 摘要：

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

runtime 细节：

```text
/map topic_type=null
/amcl_pose topic_type=geometry_msgs/msg/PoseWithCovarianceStamped
/amcl_pose publisher_count=0
/map_server lifecycle unavailable
/amcl lifecycle unavailable
/planner_server lifecycle unavailable
managed_map_yaml.basename=trashbot_map.yaml
managed_map_yaml.exists=true
nav2_refresh.status=refresh_command_failed
nav2_refresh.returncode=28
```

## OKR 结论

- O5：保持约 `~85%`。本轮没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic 或真实 phone/browser evidence。
- O1/O6/O7：保持约 `~93%`。本轮没有 current live HIL、same-run path success、route/material 新增、delivery record、operator acceptance 或 production readback。
- 现场 O3 lane：新增 daemon-safe localization probe 和更细的 root-cause evidence，但没有 same-run path/material success。
- KR：本轮不归档 KR，不调整任何 Objective 百分比。

## Proof Boundary

本轮 proof boundary：

- `software_proof_real_board_daemon_safe_localization_probe_only`
- `blocked_refresh_readback_failed`
- `blocked_localization_runtime_not_ready`

本轮不证明：

- `amcl_pose_observed=true`；
- `map_to_odom=true` 或 `map_to_base_link=true`；
- same-run path generation success；
- live route execution success；
- safe-to-control；
- HIL pass；
- delivery success；
- production cloud / DB / queue / OSS / CDN / phone/browser external proof。

## 剩余风险

- `managed_map_yaml.exists=true` 只证明地图文件存在，不证明 `/map_server` 已启动。
- `/amcl_pose` 有 topic type 但 `publisher_count=0`，说明 AMCL 或其运行链还没有真正进入可发布状态。
- refresh 仍 `curl (28)` 超时，表明 no-motion readback 仍被 runtime/localization blocker 卡住。

## 下一轮建议

下一轮继续 O3 现场 lane，并直接围绕 `live_daemon_safe_localization.raw.json` 拆解：

1. 先修 `/map_server`、`/amcl`、`/planner_server` lifecycle unavailable；
2. 再解释 `/map topic_type=null` 与 `trashbot_map.yaml` 可读并存的原因；
3. 把 `/amcl_pose publisher_count=0` 修到可发布，再复采 `map->odom` / `map->base_link`；
4. 只有出现 `amcl_pose_observed=true`、`map_to_odom=true` 或同轮 path/material 后，才继续 planner-only path 或 O6/O7 消费链。
