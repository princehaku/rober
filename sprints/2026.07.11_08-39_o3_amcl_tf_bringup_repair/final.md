# O3 AMCL TF Bringup Repair Final

## 复盘结论

本轮 `sprints/2026.07.11_08-39_o3_amcl_tf_bringup_repair/` 完成 epic sprint 收口。O5 仍是最低主 Objective，约 `~85%`，但当前缺真实 production external evidence，继续 O5 readiness/probe/support packet 不允许计主 OKR 增量。本轮因此继续现场 O3 lane。

结果是 fail-closed，但比上一轮更可执行：AMCL `/initialpose` 发布链已从单次 CLI 盲发升级为进程内 `rclpy` burst publisher，并把 publish method、subscriber count、attempts、elapsed 和 error 写入 proof；同时 `/api/nav2/proof/refresh` SSH readback 已从长时间挂起修成硬超时/自然返回/fail-closed raw JSON。本轮真实板 `live_amcl_tf_bringup_repair.raw.json` 已自然返回，不再需要人工中断。

当前 blocker 回到定位链本身：`/scan`、`/amcl_pose`、`map->odom`、`map->base_link` 当前窗口仍未 observed，`path_generated=false`。

## 实际改动

Algorithm owner 修改：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/scripts/field_route_evidence_preflight.py`
- `onboard/tests/test_field_route_evidence_preflight.py`
- `onboard/tests/test_upper_robot_api.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_08-39_o3_amcl_tf_bringup_repair/tech-done.md`
- `sprints/2026.07.11_08-39_o3_amcl_tf_bringup_repair/artifacts/local_preflight.raw.json`
- `sprints/2026.07.11_08-39_o3_amcl_tf_bringup_repair/artifacts/live_amcl_tf_bringup_repair.raw.json`
- `sprints/2026.07.11_08-39_o3_amcl_tf_bringup_repair/artifacts/live_amcl_tf_bringup_repair.interrupted.md`

主节点新增：

- `sprints/2026.07.11_08-39_o3_amcl_tf_bringup_repair/pre_start.md`
- `sprints/2026.07.11_08-39_o3_amcl_tf_bringup_repair/prd.md`
- `sprints/2026.07.11_08-39_o3_amcl_tf_bringup_repair/tech-plan.md`
- `sprints/2026.07.11_08-39_o3_amcl_tf_bringup_repair/side2side_check.md`
- `sprints/2026.07.11_08-39_o3_amcl_tf_bringup_repair/final.md`

Product 同步更新：

- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证证据

子 agent 验证：

```text
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/field_route_evidence_preflight.py onboard/scripts/upper_robot_api.py
通过

python3 -m unittest onboard.tests.test_field_route_evidence_preflight onboard.tests.test_upper_robot_api
Ran 125 tests in 0.266s
OK (skipped=1)

python3 -m unittest discover -s onboard/src/ros2_trashbot_bringup/test
Ran 23 tests in 0.042s
OK

local dry-run
status=dry_run_template_only_not_proven

scoped git diff --check
通过
```

真实板 live raw JSON：

```text
status=blocked_live_localization_chain_not_ready
safe_to_control=false
robot_control_executed=false
delivery_success=false
hil_pass=false
route_execution_success=false
primary_actions_enabled=false
```

refresh/readback 摘要：

```text
status=blocked_with_root_cause
timed_out=false
naturally_returned=true
returncode=0
curl_max_time_s=38
process_timeout_s=42
path_generated=false
path_generation_succeeded=false
path_point_count=0
dangerous_true_fields=[]
```

当前 root cause：

```text
blocked_scan_not_observed
blocked_amcl_pose_not_observed
blocked_map_to_odom_not_observed
blocked_map_to_base_link_not_observed
/map topic_type=null
/amcl_pose topic_type=null
/map_server lifecycle unavailable
/amcl lifecycle unavailable
/planner_server lifecycle unavailable
managed_map_yaml.exists=true
```

## OKR 结论

- O5：保持约 `~85%`。本轮没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic 或真实 phone/browser evidence。
- O1/O6/O7：保持约 `~93%`。本轮没有 current live HIL、same-run path success、route execution、delivery record、operator acceptance 或 production readback。
- 现场 O3 lane：新增 AMCL initialpose 可观测化和 refresh/readback 硬超时修复，但没有 same-run path/material success。
- KR：本轮不归档 KR，不调整任何 Objective 百分比。

## Proof Boundary

本轮 proof boundary：

- `software_proof_real_board_amcl_initialpose_publish_diagnostics_only`
- `software_proof_real_board_nav2_refresh_readback_hard_timeout_only`
- `blocked_live_localization_chain_not_ready`

本轮不证明：

- same-run path generation success；
- live route execution success；
- safe-to-control；
- HIL pass；
- delivery success；
- current live localization readiness；
- production cloud / DB / queue / OSS / CDN / phone/browser external proof。

## 剩余风险

- 当前窗口 `/scan`、`/amcl_pose`、`map->odom`、`map->base_link` 仍全链未 observed。
- `trashbot_map.yaml` 可读只证明 map 文件仍存在，不证明 map server 或 AMCL 已 ready。
- refresh/readback 可控不等于 planner 或 localization 成功。

## 下一轮建议

下一轮继续 O3 现场 lane，并直接围绕 `live_amcl_tf_bringup_repair.raw.json` 拆解：

1. 先确认 no-motion start 后 `/scan` 为什么当前窗口未 observed；
2. 再确认 `/map_server`、`/amcl`、`/planner_server` 为什么 lifecycle unavailable；
3. 独立采 `/amcl_pose` type/publisher 和 `map->odom`；
4. 只有出现 `initialpose_published=true`、`amcl_pose_observed=true` 或 `map_to_odom=true` 后，才继续 planner-only `path_generated`。
