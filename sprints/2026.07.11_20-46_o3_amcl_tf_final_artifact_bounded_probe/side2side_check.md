# O3 AMCL TF Final Artifact Bounded Probe Side-to-Side Check

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.11_20-46_o3_amcl_tf_final_artifact_bounded_probe/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Closeout date: 2026-07-11
- Check result: accepted as O3/O1 supporting no-motion bounded final artifact progress; not accepted as path generation, route execution, HIL, delivery, or production cloud success

## 用户价值和产品北极星

产品北极星仍是普通用户把垃圾交给小车后，小车能沿固定路线完成送达，并留下可复盘的 current-run delivery evidence chain。本轮用户价值不是让车运动，也不是证明送达，而是把真实板 no-motion 链路从上一轮 partial/source repair 推进到 AMCL lifecycle、`/amcl_pose` freshness、TF edge 和 planner-only path gate 的 final artifact root cause，给下一轮现场执行命令提供更窄的入口。

## Side-to-Side 对照结论

| 对照项 | 19-46 source/CLI repair | 20-46 bounded final artifact | Product 判定 |
| --- | --- | --- | --- |
| Artifact status | `status=interrupted_before_final_artifact` | `status=blocked_with_root_cause` | 本轮有新增 final artifact 证据 |
| Evidence type | `evidence_type=partial_runtime_material` | `evidence_type=blocked_with_root_cause` | 从 partial 推进到可收口 root cause |
| Source/CLI blocker | `board_source_preflight_ready`，`ros2_cli_ok=true`，`rclpy_import_ok=true` | 继续保持 `board_source_preflight_ready`，`ros2_cli_ok=true`，`rclpy_import_ok=true` | 旧 source/CLI blocker 没有被重复消费 |
| Runtime | interrupted before final | `managed_runtime_started=true` | runtime 已启动，但仍不是 path 或 route success |
| AMCL | `/amcl_pose_once_not_observed` | `/amcl` lifecycle `inactive [2]`，`/amcl_pose.topic_type=geometry_msgs/msg/PoseWithCovarianceStamped`，sample observed 但 stale，`age_ms=85437` | blocker 收窄到 lifecycle/freshness |
| TF | `map_to_odom_not_observed` | `tf_readiness_summary.map_to_odom_dynamic.observed=false`，`map_to_base_link.observed=false` 且 blocked by `map_to_odom` | blocker 收窄到 dynamic `map->odom` source |
| Path gate | requested but not attempted/generated | `path_generation_requested=true`，`path_generation_attempted=false`，`path_generated=false`，`planner_server_ready_for_path_generation=true` | planner ready，但 localization/TF gate 未 ready |
| Safety | all false | `safe_to_control=false`，`publishes_cmd_vel=false`，`calls_base_manual=false`，`robot_control_executed=false`，`route_execution_success=false`，`delivery_success=false`，`hil_pass=false`，`uses_base_uart=false` | no-motion invariant 保持 |

## OKR 映射和方向判断

- O5：继续保持约 `85%`。O5 仍是当前最低 Objective，但缺真实 production/external evidence；继续 O5 support-only/readback/checklist 不产生主 OKR 增量。
- O1：继续保持约 `93%`。本轮只推进 current same-run path generation 的前置诊断，不证明 `path_generated=true`、Nav2 route execution、HIL pass 或 safe-to-control。
- O6/O7：继续保持约 `93%`。本轮没有新的 route execution、delivery record、operator confirmation 或 production readback material 可消费。
- 方向判断：`继续` O3/O1 no-motion localization/path readiness；`暂停` O5 support-only 包装；`不调整` 百分比；`不归档` KR。

## KR 拆解和历史归档判断

本轮不归档任何 KR，原因如下：

- 没有 current same-run `path_generated=true` 或 path point count 大于 0；
- 没有 Nav2 route execution success；
- 没有 delivery record 或 operator acceptance；
- 没有 current live HIL pass；
- 没有 production cloud external evidence；
- O6/O7 没有新的 current-run material consumption。

当前推进区继续保留 O1 path generation / route execution / HIL 缺口、O5 production external evidence 缺口、O6/O7 current live route/delivery/operator/production material 缺口。

## 本轮核心抓手和验收口径

本轮核心抓手已达成：Algorithm owner 让 artifact 继续证明 `board_source_preflight_ready`，同时新增 `amcl_readiness_summary`、`tf_readiness_summary` 和 `path_generation_gate`，把最小下一步收窄到 `/amcl` lifecycle inactive、`/scan` dual-QoS timeout、`/map_once_not_observed`、`cli_initialpose_publish_failed`、dynamic `map->odom` 和远端 SSH 自然返回 cleanup。

验收结论：

- 接受：O3/O1 supporting no-motion bounded final artifact progress。
- 不接受：path generation success、route execution、HIL、delivery、production cloud 或 O5 external production evidence。
- 不调整：O5 约 `85%`，O1/O6/O7 约 `93%`。
- 不归档：没有 KR 达到完成或历史归档条件。

## 对应责任 Engineer

下一轮主责仍建议 `robot-algorithm-engineer`，因为最小 blocker 在 Nav2 lifecycle、AMCL、scan/map input、TF source 与 helper remote cleanup 内。若进入 WAVE ROVER motion/HIL 或 hardware feedback，再切 `rober-hardware-engineer`；若出现 production cloud/external evidence，再切 `robot-software-engineer` 或 O6/O7 owner。

## 风险、阻塞和需要补齐的证据链

剩余风险：

- `/amcl` lifecycle 仍为 inactive，`amcl_lifecycle_not_active` 阻塞 `/amcl_pose` fresh sample；
- `/scan_reliable_and_best_effort_timeout` 与 `/map_once_not_observed` 仍未解除；
- `cli_initialpose_publish_failed` 仍阻塞 AMCL 收敛；
- `map_to_odom_dynamic_source_missing` 继续阻塞 `map_to_base_link`；
- live SSH helper 仍需人工中断后再 pull final artifact，远端自然返回 cleanup 需要继续收敛。

下一步证据链：

1. `/amcl` lifecycle active；
2. `/scan` 与 `/map` 同窗可读；
3. `/amcl_pose` fresh sample；
4. dynamic `map->odom` observed；
5. planner-only `ComputePathToPose` attempted/generated；
6. 后续 live route execution、delivery/operator acceptance 或 production external evidence。

## 需要创建或更新的 Sprint 文档

本轮 Product closeout 已创建/更新：

- `side2side_check.md`
- `final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
