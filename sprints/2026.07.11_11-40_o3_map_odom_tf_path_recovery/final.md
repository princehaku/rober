# O3 Map Odom TF Path Recovery Final

## 复盘结论

本轮 `sprints/2026.07.11_11-40_o3_map_odom_tf_path_recovery/` 完成 epic sprint 收口。O5 仍是最低主 Objective，约 `~85%`，但当前缺真实 production external evidence，继续 O5 wrapper / probe / support-only 工作不会产生主 OKR 增量，因此本轮继续现场 O3 lane，服务 O1/O6/O7 后续同 run path/material 缺口。

结果是：Robot Software 已经修掉 `o10_amcl_nav2_runtime_proof.py` 中 `/initialpose` verbose info probe 的旧卡点，local 验证和真实板 direct helper 都证明这部分修复生效；但真实板最终仍 fail-closed，且当前 blocker 比上一轮更前置。最新 direct helper artifact `artifacts/live_nav2_direct_helper_partial_after_lazy_initialpose.raw.json` 输出 `status=blocked_with_root_cause`、`proof.elapsed_ms=136389`、`proof.managed_runtime_started=true`、`proof.map_server_active=true`、`proof.amcl_active=true`、`proof.initialpose_publish_method=ros2_topic_pub_once_cli_fallback`、`proof.initialpose_subscriber_count=1`，同时仍 `proof.initialpose_published=false`、`proof.amcl_pose_observed=false`、`proof.localization_tf_observed.map_to_odom=false`、`proof.localization_tf_observed.map_to_base_link=false`、`proof.path_generated=false`。最终 root causes 为 `/scan_once_not_observed`、`cli_initialpose_publish_failed`、`/amcl_pose_once_not_observed`、`map_to_odom_not_observed`、`map_to_base_link_blocked_by_missing_map_to_odom`、`localization_not_ready_for_path_generation`。

因此本轮价值不是 same-run path success，而是把现场定位链继续收敛成更窄的 no-motion blocker：旧的 `/initialpose` topic-info stall 已退出主路径，但 `/scan`、`/amcl_pose`、`map->odom` 和 dynamic TF freshness 仍没有形成可用于 path generation 的链路。

## 实际改动

本轮 Product closeout 新增或更新：

- `sprints/2026.07.11_11-40_o3_map_odom_tf_path_recovery/side2side_check.md`
- `sprints/2026.07.11_11-40_o3_map_odom_tf_path_recovery/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Robot Software owner 在本 sprint 已完成并由 `tech-done.md` 记录的改动包括：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_11-40_o3_map_odom_tf_path_recovery/tech-done.md`
- `sprints/2026.07.11_11-40_o3_map_odom_tf_path_recovery/artifacts/local_preflight.raw.json`
- `sprints/2026.07.11_11-40_o3_map_odom_tf_path_recovery/artifacts/live_nav2_direct_helper_partial_after_lazy_initialpose.raw.json`

## 验证证据

子 agent 已交付的验证结果如下：

```text
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/field_route_evidence_preflight.py onboard/scripts/upper_robot_api.py
通过

python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper onboard.tests.test_field_route_evidence_preflight onboard.tests.test_upper_robot_api
Ran 171 tests in 2.488s
OK (skipped=1)

python3 onboard/scripts/field_route_evidence_preflight.py --mode local --dry-run --output sprints/2026.07.11_11-40_o3_map_odom_tf_path_recovery/artifacts/local_preflight.raw.json
status=dry_run_template_only_not_proven

ssh -o ConnectTimeout=12 -o BatchMode=yes -o StrictHostKeyChecking=accept-new -p 37878 root@192.168.1.11 'hostname && date'
op-z3-b6.home
Sat Jul 11 11:47:24 AM CST 2026
```

真实板最终采用 direct helper artifact 作为验收依据，因为 outer preflight 本轮仍未自然落盘 final body。关键事实如下：

```text
status=blocked_with_root_cause
proof.elapsed_ms=136389
proof.managed_runtime_started=true
proof.map_server_active=true
proof.amcl_active=true
proof.initialpose_publish_method=ros2_topic_pub_once_cli_fallback
proof.initialpose_subscriber_count=1
proof.initialpose_published=false
proof.amcl_pose_observed=false
proof.localization_tf_observed.map_to_odom=false
proof.localization_tf_observed.map_to_base_link=false
proof.path_generated=false
proof.root_causes=[
  /scan_once_not_observed,
  cli_initialpose_publish_failed,
  /amcl_pose_once_not_observed,
  map_to_odom_not_observed,
  map_to_base_link_blocked_by_missing_map_to_odom,
  localization_not_ready_for_path_generation
]
```

## OKR 结论

- O5：保持约 `~85%`。本轮没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic 或真实 phone/browser evidence。
- O1：保持约 `~93%`。本轮新增的是 O3 supporting no-motion evidence，没有 `current same-run path generation success`、`Nav2 route execution success`、current live HIL、wheel direction、IMU/battery calibration 或 delivery success。
- O6/O7：保持约 `~93%`。本轮没有 current-run `route.csv`、keyframe、rosbag、replay JSONL、delivery/operator material、production readback 或 live route execution。
- KR：本轮不归档 KR，不调整任何 Objective 百分比。

## Proof Boundary

本轮 proof boundary：

- `software_proof_real_board_no_motion_localization_probe_only`
- `blocked_with_root_cause`
- `blocked_scan_amcl_pose_map_to_odom_chain`

本轮不证明：

- `initialpose_published=true`
- `amcl_pose_observed=true`
- `map_to_odom=true`
- `map_to_base_link=true`
- same-run path generation success
- live route execution success
- HIL pass
- safe-to-control
- delivery success
- production cloud / DB / queue / OSS / CDN / phone/browser external proof

## 剩余风险

- outer preflight 仍没有自然落下 helper final body，因此主链路上的 read-only ROS CLI 探测串行耗时仍是问题。
- direct helper 已证明 managed runtime、map server 和 AMCL 可起，但 `/scan_once`、`/amcl_pose_once` 和 `map->odom` 仍不稳定或未满足 freshness 条件。
- 目前不能把 static `odom->base_link` 误当作完整动态 odom 链；下一轮必须显式区分 dynamic `/tf` 与 `/tf_static` 的来源和新鲜度。
- 本轮依旧没有任何运动执行，必须继续保持 `safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`、`hil_pass=false`。

## 下一轮建议

1. 继续现场 O3 lane，先把 `/scan`、`/amcl_pose`、`/odom`、`/tf` 单条 probe 的耗时、最近时间戳和 freshness 分层落盘。
2. 明确记录 `/tf` 是否出现来自 `/amcl` 的 dynamic transforms，不要把只有 static `odom->base_link` 当作 localization 已闭环。
3. 只有在 `map_to_odom=true` 或至少拿到更具体的 dynamic TF / sensor freshness blocker 后，才值得继续追 `path_generated`。
4. 在拿到 current-run path/material 之前，O6/O7 继续保持消费链冻结，不再因为 wrapper/readback/support-only 工作涨分。
