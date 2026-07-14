# O3 Live Localization Sensor Smoke Final

## 复盘结论

本轮 `sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/` 完成 epic sprint 收口。O5 仍是最低 Objective，约 `~85%`，但最近 O5 external evidence lane 已 fail-closed，继续做 O5 support-only / wrapper / readback 不会产生新的 `external_artifact_delta`。本轮因此按计划切到现场 O3 live localization smoke lane。

结果仍然是 fail-closed，但比上一轮更进一步：真实上位机当前窗口已经确认 `/scan observed=true`，说明 LiDAR topic 本轮不是主 blocker；新的 blocker 收敛为 `/amcl_pose` 未观测、`map->odom` 未观测、`map->base_link` 未观测，以及 no-motion `/api/nav2/proof/refresh` readback 超时。当前还没有 same-run path generation success，也没有新的路线材料成功。

## 实际改动

Robot Software 执行阶段修改：

- `onboard/scripts/field_route_evidence_preflight.py`
- `onboard/tests/test_field_route_evidence_preflight.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `tech-done.md`
- `artifacts/robot_software_worker_report.md`
- `artifacts/live_localization_preflight.raw.json`
- `artifacts/live_localization_preflight.pretty.json`
- `artifacts/live_localization_preflight.summary.json`
- `artifacts/local_preflight.raw.json`
- `artifacts/local_preflight.pretty.json`
- `artifacts/local_preflight.summary.json`

Product closeout 阶段新增：

- `side2side_check.md`
- `final.md`

Product 同步更新：

- `OKR.md`
- `docs/process/okr_progress_log.md`

本轮没有修改 `pc-tools/**`、其他 sprint 目录，也没有改 O1/O5/O6/O7 实现或任何运动默认入口。

## 验证证据

live localization summary：

```text
status=blocked_refresh_readback_failed
/scan observed=true
/amcl_pose observed=false
blocked_amcl_pose_not_observed
blocked_map_to_odom_not_observed
blocked_map_to_base_link_not_observed
nav2_proof_refresh.status=refresh_command_failed
```

安全边界：

```text
safe_to_control=false
delivery_success=false
primary_actions_enabled=false
robot_control_executed=false
route_execution_success=false
hil_pass=false
```

Robot Software 验证：

```text
python3 -m py_compile ... 通过
Ran 25 tests in 0.022s
OK
git diff --check ... 通过
```

local fallback：

```text
status=dry_run_template_only_not_proven
safe_to_control=false
delivery_success=false
```

## OKR 结论

- O5：保持约 `~85%`。本轮没有新的真实 production external evidence，且当前收口明确 `无 OKR 百分比上调`。
- O1：保持约 `~93%`。本轮没有 current live HIL、wheel direction、IMU/battery calibration、same-run path generation success 或 route execution success。
- O6/O7：保持约 `~93%`。本轮没有新的 `map.yaml`、`route.csv`、keyframe、rosbag、replay JSONL、delivery record、operator acceptance 或 production readback 可消费。
- KR：本轮 `不归档 KR`。因为收口结论仍是 live localization/readback blocker 收敛，而不是已完成能力闭环。

## Proof Boundary

本轮 proof boundary：

- `software_proof_real_board_live_localization_smoke_only`
- `blocked_live_localization_chain_not_ready`
- `software_proof_real_board_no_motion_refresh_readback_only`

本轮不证明：

- same-run path generation success；
- live route execution success；
- delivery success；
- safe-to-control；
- HIL pass；
- `map.yaml` / `route.csv` / keyframe / rosbag / replay JSONL 已产出；
- production cloud / DB / queue / OSS / CDN / phone/browser external proof。

## 剩余风险

- `/scan` 已经 observed，但 `/amcl_pose` 和 map 相关 TF 仍未 ready，说明定位链卡点已经下沉到 AMCL / map frame / TF 发布链。
- `/api/nav2/proof/refresh` 当前只证明 readback timeout，尚不能说明 refresh endpoint 的内部 blocker 已演化或恢复。
- 当前仍没有 same-run path、路线材料、delivery/operator/prod-cloud evidence，因此不能推动任何主 OKR 百分比或 KR 归档。

## 下一轮建议

下一轮继续现场 O3 验证 lane，但不要再重复 O5 support-only 或旧 latest readback。优先顺序应为：

1. 定位 `/amcl_pose` 未发布的直接根因；
2. 定位 `map` frame、`map->odom`、`map->base_link` 发布链；
3. 修复后重跑 no-motion `/api/nav2/proof/refresh`；
4. 只有当 refresh 不再 `blocked_refresh_readback_failed`，并进一步产出 same-run path 或新的路线材料时，才允许继续推动 O6/O7 消费链。
