# O3 AMCL TF Bringup Repair Side2Side Check

## 验收结论

本轮 `sprints/2026.07.11_08-39_o3_amcl_tf_bringup_repair/` 完成 epic sprint 验收。目标不是 O5 support-only 继续包装，而是在现场 O3 no-motion lane 中修 AMCL/TF blocker。

结论：本轮没有拿到 same-run `path_generated=true`，也没有 `amcl_pose_observed=true` 或 `map->odom=true`。但本轮确实修掉两条前置问题：

- `/initialpose` 发布链从 `ros2 topic pub --once` 的单次 CLI 盲发，推进为 helper 内部 `rclpy` burst publisher，并在 artifact 中新增 method、subscriber count、attempts、elapsed 和 error 字段。
- `/api/nav2/proof/refresh` 的 SSH readback 不再用长等待吞掉整轮 automation；现在会在硬上限内自然返回，或以 fail-closed summary 写入主 raw JSON。

## 证据对照

本地验证：

```text
py_compile: 通过
field_route_evidence_preflight + upper_robot_api tests: Ran 125 tests in 0.266s OK (skipped=1)
bringup static tests: Ran 23 tests in 0.042s OK
local dry-run: status=dry_run_template_only_not_proven
scoped git diff --check: 通过
```

真实板 live artifact：

```text
artifact=sprints/2026.07.11_08-39_o3_amcl_tf_bringup_repair/artifacts/live_amcl_tf_bringup_repair.raw.json
status=blocked_live_localization_chain_not_ready
safe_to_control=false
robot_control_executed=false
delivery_success=false
hil_pass=false
```

refresh/readback 已修复为自然返回：

```text
nav2_refresh.status=blocked_with_root_cause
nav2_refresh.timed_out=false
nav2_refresh.naturally_returned=true
nav2_refresh.returncode=0
nav2_refresh.curl_max_time_s=38
nav2_refresh.process_timeout_s=42
path_generated=false
path_generation_succeeded=false
path_point_count=0
dangerous_true_fields=[]
```

当前 localization blocker：

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
managed_map_yaml.basename=trashbot_map.yaml
managed_map_yaml.exists=true
```

## OKR 判断

- O5：保持约 `~85%`。本轮没有真实 production external evidence，不消费 O5 support-only。
- O1/O6/O7：保持约 `~93%`。本轮没有 current live HIL、same-run path success、route execution、delivery record、operator acceptance 或 production readback。
- 现场 O3 lane：新增 AMCL initialpose 诊断与 refresh/readback 硬超时修复，但没有 same-run path/material success。
- KR：不归档。

## 剩余风险

- 真实板当前窗口 `/scan`、`/amcl_pose`、`map->odom`、`map->base_link` 仍全链未 observed。
- refresh 自然返回只证明 readback 机制可控，不证明 localization 或 planner 已 ready。
- 本轮所有结论仍保持 no-motion 边界，不证明 safe-to-control、HIL、delivery success 或真实路线执行成功。

## 下一轮验收建议

下一轮继续现场 O3 lane，但不要重复本轮 initialpose publisher 或 refresh hard-timeout 修复。优先拆开验证：

1. 独立确认 no-motion start 后 `/scan` 为什么在当前窗口未 observed；
2. 独立确认 AMCL 是否出现 `/amcl_pose` publisher/type 和 lifecycle active；
3. 在 refresh 之外直接采 `map->odom` / `map->base_link`；
4. 只有 `initialpose_published=true`、`amcl_pose_observed=true` 或 `map_to_odom=true` 出现后，才继续 planner-only path generation。
