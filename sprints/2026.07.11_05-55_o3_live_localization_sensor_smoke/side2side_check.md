# O3 Live Localization Sensor Smoke Side2Side Check

## 验收对象

本轮验收对象是 `sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/`。目标不是证明真实 route execution、delivery success 或 safe-to-control，而是验证真实上位机当前同窗 live localization smoke 是否足以支撑 no-motion `/api/nav2/proof/refresh` readback，并把 blocker 从“泛化 localization 未就绪”收敛到更具体的 `/amcl_pose`、`map->odom`、`map->base_link` 与 refresh timeout。

## 对照结论

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| O5 最低优先级核对 | 通过 | `tech-plan.md` 明确 O5 约 `~85%` 仍最低，但最近 O5 external evidence sprint 已 fail-closed，本轮合理转 O3 live localization smoke |
| Epic 留档完整性 | 通过 | 已有 `pre_start.md`、`prd.md`、`tech-plan.md`、`tech-done.md`、本文件和 `final.md` |
| 子 agent 执行 | 通过 | Robot Software worker 完成 live localization smoke / refresh readback 扩展、验证和 artifact 落档 |
| `/scan` 同窗观测 | 通过 | `artifacts/live_localization_preflight.summary.json` 记录 `/scan observed=true`、`returncode=0` |
| `/amcl_pose` 同窗观测 | fail-closed | summary 记录 `/amcl_pose observed=false`、`blocked_amcl_pose_not_observed` |
| `map->odom` TF | fail-closed | summary 记录 `blocked_map_to_odom_not_observed` |
| `map->base_link` TF | fail-closed | summary 记录 `blocked_map_to_base_link_not_observed` |
| no-motion refresh readback | fail-closed | summary 记录 `status=blocked_refresh_readback_failed`、`nav2_proof_refresh.status=refresh_command_failed` |
| 安全边界 | 通过 | summary 和 `tech-done.md` 固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`route_execution_success=false`、`hil_pass=false` |
| 本地 fallback | 通过 | `artifacts/local_preflight.summary.json` 输出 `status=dry_run_template_only_not_proven`，用于模板回归，不计现场成功 |

## 用户侧判断

这轮没有把 `/scan observed=true` 误写成“定位链 ready”。新的现场事实更具体了：LiDAR topic 当前窗口可观测，但 `/amcl_pose` 仍未发布，`map->odom` 与 `map->base_link` 仍未建立，且 no-motion `/api/nav2/proof/refresh` 在当前轮 readback 超时。也就是说，本轮把主 blocker 从上一轮的“/scan、/amcl_pose、TF 全部不清楚”推进为“/scan 已到位，但定位链和 refresh 回读仍未通”。

## 不通过项

- 当前轮没有 same-run `path_generated=true` 或 `path_generation_succeeded=true`。
- 当前轮没有新的 `map.yaml`、`route.csv`、keyframe、rosbag 或 replay JSONL。
- 当前轮没有 route execution success、delivery success、operator acceptance 或 production cloud evidence。
- 因此本轮必须明确 `无 OKR 百分比上调`、`不归档 KR`。

## 下一步验收口径

下一轮应继续现场 O3 lane，但目标必须收紧到：

- 先查清 `/amcl_pose` 为什么未发布；
- 查清 `map` frame、`map->odom`、`map->base_link` 的发布链；
- 在上述项恢复后再次重跑 no-motion `/api/nav2/proof/refresh`；
- 只有同一轮 refresh 不再 `blocked_refresh_readback_failed`，并进一步产出 same-run path 或路线材料时，才允许继续推动 O6/O7 消费链。
