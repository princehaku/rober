# O3 AMCL Map TF Recovery Probe Side2Side Check

## 验收结论

本轮 `sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/` 验收通过，结论为 fail-closed，不提升 OKR 百分比。

这轮相对 `2026.07.11_05-55_o3_live_localization_sensor_smoke` 有真实增量：不再只知道 `/amcl_pose` 与 `map->odom` 未观测，而是把 blocker 下钻到当前真实板 no-motion root cause：

- `/map` topic type 缺失；
- `/amcl_pose` topic type 缺失；
- `/map_server`、`/amcl`、`/planner_server` lifecycle 均不可用；
- configured managed map basename `trashbot_map.yaml` 当前可读，summary 只保留 basename、size 与 sha256 前缀；
- `map->odom`、`map->base_link` 都失败在 `Invalid frame ID "map"`；
- `/api/nav2/proof/refresh` 仍为 `refresh_command_failed`。

## 对照检查

| 检查项 | 期望 | 结果 |
| --- | --- | --- |
| 最低 OKR 转向理由 | O5 无真实 external evidence 时避免继续 support-only | 通过，`tech-plan.md` 已说明转向 O3 现场 lane |
| no-motion 边界 | 不发送 `/cmd_vel`、`/api/base/manual`、NavigateToPose | 通过，模板和测试均排除运动入口 |
| root-cause evidence | 输出 AMCL/map/TF/lifecycle/map yaml 安全摘要 | 通过，live summary 已包含 `root_cause_summary` |
| 路径泄漏 | summary-facing 字段不回显完整板上路径 | 通过，使用 `configured_basename=trashbot_map.yaml` |
| refresh 安全门 | 运动/成功危险 true 仍 fail-closed | 通过，`safe_to_control=true` 单测仍 fail-closed |
| managed runtime | `starts_nav2=true` 不被误判为运动危险 | 通过，单测覆盖 no-motion lifecycle start |
| OKR 结论 | 无 same-run path/material success 时不加分 | 通过，`tech-done.md` 明确 OKR 不变 |

## 验证证据

子 agent 汇报的验证结果：

```text
python3 -m py_compile onboard/scripts/field_route_evidence_preflight.py
通过

python3 -m unittest onboard.tests.test_field_route_evidence_preflight
Ran 16 tests in 0.019s
OK

git diff --check -- onboard/scripts/field_route_evidence_preflight.py onboard/tests/test_field_route_evidence_preflight.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe
通过
```

真实板 artifact：

- `artifacts/live_amcl_map_tf_preflight.summary.json`
- `status=blocked_refresh_readback_failed`
- `safe_to_control=false`
- `delivery_success=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `hil_pass=false`

## 剩余风险

- 本轮只证明 Nav2/map/AMCL runtime 当前未 ready，没有修复到 `map` frame 发布状态。
- no-motion refresh 仍没有 JSON 成功 readback，因此尚未产生 same-run path。
- 没有新的 `map.yaml`、`route.csv`、keyframe、rosbag、replay JSONL、delivery/operator 或 production cloud evidence。
