# O3 No-Motion Planner Path Proof Side2Side Check

## 验收对象

本轮验收对象是 `sprints/2026.07.11_04-36_o3_no_motion_planner_path_proof/`。目标不是证明真实路线执行或送达成功，而是验证真实上位机在 no-motion 条件下能否重新产出 planner/path proof；失败时必须把 blocker 分层到可执行下一步。

## 对照结论

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| O5 最低优先级核对 | 通过 | `tech-plan.md` 明确 O5 约 `~85%` 最低，但上一轮已因无真实 production external evidence 和无新 field material fail-closed，本轮不继续 O5 support-only |
| Epic 留档完整性 | 通过 | 已有 `pre_start.md`、`prd.md`、`tech-plan.md`、`tech-done.md`、本文件和 `final.md` |
| 子 agent 执行 | 通过 | Product worker 创建计划文档；Algorithm worker 执行真实 SSH/HTTP no-motion proof 与 local fallback |
| 真实上位机 SSH | 通过 | `artifacts/ssh_probe.txt` 输出 `board_live_ssh_ok`、`op-z3-b6.home`、`Sat Jul 11 04:44:19 AM CST 2026` |
| 历史 latest readback | 通过但不可计作本轮成功 | Algorithm 记录 `GET /api/nav2/proof/latest` 可读到旧 `path_generated=true`、`path_point_count=31` |
| 当前 no-motion refresh | fail-closed | `nav2_proof_refresh.summary.json` 输出 `status=blocked_with_root_cause`、`path_generated=false`、`path_point_count=0` |
| 安全边界 | 通过 | refresh summary 和 `tech-done.md` 固定 `safe_to_control=false`、`delivery_success=false`、`hil_pass=false`、`robot_control_executed=false` |
| 本地 fallback | 通过 | `local_preflight.pretty.json` 输出 `status=dry_run_template_only_not_proven`，提供下一轮采集模板 |

## 用户侧判断

这轮没有把旧 latest artifact 冒充当前成功。新的现场事实是：SSH 和 HTTP API 可达，但当前轮 `POST /api/nav2/proof/refresh` 没有复现 path generation，根因收敛到 `/scan`、`/amcl_pose`、`map_to_odom` 与 planner readiness 同窗缺失。

## 不通过项

- 当前轮没有新的 same-run `path_generated=true`。
- 当前轮没有新的 `map.yaml`、`route.csv`、keyframe、rosbag 或 replay JSONL。
- 因此 O3 现场 lane 只能记录 fail-closed 现场 blocker，不得推动 O5/O6/O7 主 OKR 百分比。

## 下一步验收口径

下一轮必须先在真实上位机做 no-motion ROS graph 同窗 smoke：

- `/scan` once 或 hz；
- `/amcl_pose` once；
- `/tf` 中 `map->odom` 与 `map->base_link`；
- 再重跑 `/api/nav2/proof/refresh`。

只有同一轮 refresh 得到 `path_generated=true` 或产出新的路线材料，才允许继续推动 O6/O7 消费链。
