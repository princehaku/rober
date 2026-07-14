# O3 Nav2 Map AMCL TF Runtime Repair Final

## 复盘结论

本轮 `sprints/2026.07.11_10-39_o3_nav2_map_amcl_tf_runtime_repair/` 完成 epic sprint 收口。O5 仍是最低主 Objective，约 `~85%`，但当前缺真实 production external evidence，继续 O5 readiness/probe/support packet 不允许计主 OKR 增量，因此本轮继续现场 O3 lane。

结果是有效现场修复与诊断推进，但仍 fail-closed。Robot Software 已修掉真实板 direct helper 的运行时缺陷 `UnboundLocalError: lifecycle_active referenced before assignment`，并新增板端 direct helper artifact。修复后 helper 已不再停在“lifecycle unavailable”这一层，而是给出更强的同轮事实：`managed_runtime_started=true`、`map_server_active=true`、`amcl_active=true`、`initialpose_published=true`、`amcl_pose_observed=true`、`amcl_pose_frame_id=map`、`odom_frame_observed=true`、`base_link_to_laser_frame=true`。但 helper 最终仍证明 `map_frame_observed=false`、`map_to_odom=false`、`map_to_base_link=false`、`path_generated=false`，root cause 收敛为 `map_to_odom_not_observed`、`map_to_base_link_blocked_by_missing_map_to_odom`、`localization_not_ready_for_path_generation`。

因此本轮价值在于把根因从“可能是 lifecycle / refresh 黑盒失败”推进到“AMCL 已经更接近 ready，但 `map->odom` 仍缺失，且 preflight refresh 外层预算小于 helper 完成预算”，而不是 same-run path、route execution 或 delivery 成功。

## 实际改动

Robot Software owner 修改或新增：

- `onboard/scripts/o11_nav2_lifecycle.sh`
- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/scripts/field_route_evidence_preflight.py`
- `onboard/scripts/upper_robot_api.py`
- `onboard/tests/test_o11_nav2_lifecycle_script.py`
- `onboard/tests/test_map_lifecycle_proof_helper.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `onboard/tests/test_field_route_evidence_preflight.py`
- `onboard/tests/test_upper_robot_api.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_10-39_o3_nav2_map_amcl_tf_runtime_repair/tech-done.md`
- `sprints/2026.07.11_10-39_o3_nav2_map_amcl_tf_runtime_repair/artifacts/local_preflight.raw.json`
- `sprints/2026.07.11_10-39_o3_nav2_map_amcl_tf_runtime_repair/artifacts/live_nav2_map_amcl_tf.raw.json`
- `sprints/2026.07.11_10-39_o3_nav2_map_amcl_tf_runtime_repair/artifacts/live_nav2_direct_helper.raw.json`
- `sprints/2026.07.11_10-39_o3_nav2_map_amcl_tf_runtime_repair/artifacts/live_nav2_runtime_log_probe.md`

主节点新增：

- `sprints/2026.07.11_10-39_o3_nav2_map_amcl_tf_runtime_repair/side2side_check.md`
- `sprints/2026.07.11_10-39_o3_nav2_map_amcl_tf_runtime_repair/final.md`

Product 同步更新：

- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证证据

子 agent 验证：

```text
bash -n onboard/scripts/o11_nav2_lifecycle.sh
通过

python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/field_route_evidence_preflight.py onboard/scripts/upper_robot_api.py
通过

python3 -m unittest onboard.tests.test_o11_nav2_lifecycle_script onboard.tests.test_map_lifecycle_proof_helper onboard.tests.test_nav2_runtime_proof_helper onboard.tests.test_field_route_evidence_preflight onboard.tests.test_upper_robot_api
Ran 181 tests in 2.544s
OK (skipped=1)

python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
Ran 44 tests in 2.203s
OK

python3 -m unittest discover -s onboard/src/ros2_trashbot_bringup/test
Ran 23 tests in 0.045s
OK

local dry-run
status=dry_run_template_only_not_proven

live ssh preflight
blocked_reason=blocked_refresh_readback_failed

scoped git diff --check
通过
```

真实板 preflight raw JSON：

```text
blocked_reason=blocked_refresh_readback_failed
safe_to_control=false
robot_control_executed=false
delivery_success=false
hil_pass=false
nav2_refresh.returncode=28
nav2_refresh.curl_max_time_s=38
nav2_refresh.process_timeout_s=42
```

真实板 direct helper raw JSON：

```text
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
proof.root_causes=[map_to_odom_not_observed, map_to_base_link_blocked_by_missing_map_to_odom, localization_not_ready_for_path_generation]
```

runtime/log probe 摘要：

```text
/root/rober/onboard/runtime/nav2_lifecycle_latest.json => managed_runtime_started=true
autonomous_nav2_stack_only.log => map_server lifecycle node launched
autonomous_nav2_stack_only.log => static_laser_tf publishing transform
autonomous_nav2_stack_only.log => repeated Invalid frame ID "map"
```

## OKR 结论

- O5：保持约 `~85%`。本轮没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic 或真实 phone/browser evidence。
- O1/O6/O7：保持约 `~93%`。本轮没有 current live HIL、same-run path success、route/material 新增、delivery record、operator acceptance 或 production readback。
- 现场 O3 lane：新增 direct helper 现场证据并修掉 helper 真实 bug，但仍没有 same-run path/material success。
- KR：本轮不归档 KR，不调整任何 Objective 百分比。

## Proof Boundary

本轮 proof boundary：

- `software_proof_real_board_nav2_amcl_tf_runtime_repair_only`
- `blocked_refresh_readback_failed`
- `blocked_map_to_odom_tf_missing`

本轮不证明：

- `map_frame_observed=true`；
- `map_to_odom=true` 或 `map_to_base_link=true`；
- same-run path generation success；
- live route execution success；
- safe-to-control；
- HIL pass；
- delivery success；
- production cloud / DB / queue / OSS / CDN / phone/browser external proof。

## 剩余风险

- preflight artifact 仍拿不到 helper 最终 HTTP body，说明 `curl_max_time_s=38` 与 helper `elapsed_ms≈64285` 的预算不匹配仍未解决。
- `map_server_active=true`、`amcl_active=true` 和 `amcl_pose_observed=true` 目前主要来自 direct helper 窗口，不等于外层 preflight 已稳定回读。
- `map_to_odom=false` 是当前最前置 blocker；在它恢复前，`map_to_base_link` 与 path generation 仍会保持 false。
- 本轮没有任何运动执行，必须继续保持 `safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`、`hil_pass=false`。

## 下一轮建议

下一轮继续现场 O3 lane，并直接对准当前最前置根因：

1. Algorithm / Robot Software 先修 `map->odom` TF；
2. 在 `map->odom` 修复后复验 `map->base_link` 与 `path_generated`；
3. 只有 TF 根因修掉后，再决定是缩短 helper 路径，还是上调 preflight refresh budget；
4. 在拿到 `map_to_odom=true`、同轮 path 或新路线材料之前，O6/O7 不应继续消费这条链路。
