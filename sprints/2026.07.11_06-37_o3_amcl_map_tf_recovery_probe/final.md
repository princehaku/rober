# O3 AMCL Map TF Recovery Probe Final

## 复盘结论

本轮 `sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/` 完成 epic sprint 收口。O5 仍是当前最低主 Objective，约 `~85%`，但最近 O5 external evidence lane 已 fail-closed，继续做 readiness / wrapper / support packet 会重复消费 `no_real_production_external_evidence` blocker。本轮因此继续现场 O3 验证 lane。

结果是 fail-closed，但产生了新的真实板 root-cause evidence：当前问题不再是 `/scan`，也不再是 managed map yaml basename 缺失；当前核心 blocker 是 Nav2/map/AMCL runtime 没有把 `/map` topic、`/amcl_pose` topic、`map` frame 和相关 lifecycle 节点拉起来。

## 实际改动

Algorithm owner 修改：

- `onboard/scripts/field_route_evidence_preflight.py`
- `onboard/tests/test_field_route_evidence_preflight.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/tech-done.md`
- `sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/artifacts/local_preflight.raw.json`
- `sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/artifacts/local_preflight.pretty.json`
- `sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/artifacts/local_preflight.summary.json`
- `sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/artifacts/live_amcl_map_tf_preflight.raw.json`
- `sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/artifacts/live_amcl_map_tf_preflight.pretty.json`
- `sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/artifacts/live_amcl_map_tf_preflight.summary.json`

主节点新增：

- `sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/pre_start.md`
- `sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/prd.md`
- `sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/tech-plan.md`
- `sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/side2side_check.md`
- `sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/final.md`

Product 同步更新：

- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证证据

子 agent 验证：

```text
python3 -m py_compile onboard/scripts/field_route_evidence_preflight.py
通过

python3 -m unittest onboard.tests.test_field_route_evidence_preflight
Ran 16 tests in 0.019s
OK

python3 onboard/scripts/field_route_evidence_preflight.py --mode local --dry-run --output sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/artifacts/local_preflight.raw.json
通过，status=dry_run_template_only_not_proven

python3 onboard/scripts/field_route_evidence_preflight.py --mode ssh --ssh-target root@192.168.1.11 --ssh-port 37878 --timeout-s 8 --output sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/artifacts/live_amcl_map_tf_preflight.raw.json
通过执行并 fail-closed，status=blocked_refresh_readback_failed

git diff --check -- onboard/scripts/field_route_evidence_preflight.py onboard/tests/test_field_route_evidence_preflight.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe
通过
```

真实板 root-cause summary：

```text
/map topic_type=null
/amcl_pose topic_type=null
/map_server lifecycle unavailable
/amcl lifecycle unavailable
/planner_server lifecycle unavailable
managed_map_yaml.configured_basename=trashbot_map.yaml
managed_map_yaml.exists=true
map->odom blocked: Invalid frame ID "map"
map->base_link blocked: Invalid frame ID "map"
nav2_refresh.status=refresh_command_failed
safe_to_control=false
delivery_success=false
route_execution_success=false
hil_pass=false
```

## OKR 结论

- O5：保持约 `~85%`。本轮没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic 或真实 phone/browser evidence。
- O1：保持约 `~93%`。本轮没有 current live HIL、wheel direction、IMU/battery calibration、same-run path generation success 或 route execution success。
- O6/O7：保持约 `~93%`。本轮没有新的 same-run path、route execution、delivery record、operator acceptance 或 production readback 可消费。
- O3 现场验证 lane：新增真实板 root-cause evidence，但没有 same-run path/material success。

本轮不调整 OKR 百分比，不归档 KR。

## Proof Boundary

本轮 proof boundary：

- `software_proof_real_board_amcl_map_tf_root_cause_only`
- `blocked_nav2_map_runtime_not_ready`
- `software_proof_no_motion_refresh_readback_failed`

本轮不证明：

- same-run path generation success；
- live route execution success；
- delivery success；
- safe-to-control；
- HIL pass；
- `map.yaml` / `route.csv` / keyframe / rosbag / replay JSONL 已产出；
- production cloud / DB / queue / OSS / CDN / phone/browser external proof。

## 剩余风险

- 当前真实板 Nav2/map/AMCL runtime 未 ready，`map` frame 没建立。
- `trashbot_map.yaml` basename 可读只能证明 managed map 文件前置不再是当前 blocker，不等于 map server 已加载并发布 `/map`。
- `/api/nav2/proof/refresh` 仍失败，没有同轮 path result。

## 下一轮建议

下一轮继续 O3 现场 lane，但应从“诊断”进入“no-motion runtime repair”：

1. 先定位为什么 `/map_server`、`/amcl`、`/planner_server` 是 `Node not found`。
2. 用 `trashbot_map.yaml` 的 safe basename 对齐 map server 启动入口，确保 `/map` topic type 和 publisher 出现。
3. 确认 `/amcl_pose` 与 `map->odom` / `map->base_link` 后，再重跑 `/api/nav2/proof/refresh`。
4. 只有产出 same-run path 或新路线材料后，才允许推进 O6/O7 消费链或调整 OKR。
