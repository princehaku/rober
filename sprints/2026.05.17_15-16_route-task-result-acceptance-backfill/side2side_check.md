# Sprint 2026.05.17_15-16 Route Task Result Acceptance Backfill - Side2Side Check

sprint_type: epic

## 1. 对照验收

| PRD / Tech Plan 口径 | 本轮结果 | 验收判断 |
| --- | --- | --- |
| PC gate 从 `route_task_field_retest_result_acceptance_packet` summary 与 `--material-dir` 生成 backfill artifact / summary。 | Task A 新增 `route_task_field_retest_result_acceptance_backfill`，支持 acceptance packet artifact / summary / wrapper 和 material-dir。 | 通过 |
| 八类材料必须显式检查：Nav2/fixed-route runtime log、route completion signal、task record、door state、target floor confirmation、human assistance note、dropoff/cancel completion、delivery result。 | Task A 输出覆盖 `nav2_or_fixed_route_runtime_log`、`route_completion_signal`、`task_record`、`door_state`、`target_floor_confirmation`、`human_assistance_note`、`dropoff_or_cancel_completion`、`delivery_result`。 | 通过 |
| 输出和消费者必须保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。 | PC / Robot / mobile 三侧均保持该边界，`software_proof_docker_route_task_field_retest_result_acceptance_backfill_gate` 固定为本轮证据边界。 | 通过 |
| Robot diagnostics 只读消费 file/env/top-level/nested summary，不改变 task_orchestrator/action/Start/Dropoff/Cancel 控制语义。 | Task B 新增 diagnostics metadata-only consumer，支持 file/env/top-level/nested summary，未改变控制语义。 | 通过 |
| mobile/web 只读展示 backfill summary，copy/export whitelist-only，主操作 gating 不变。 | Task C 新增“路线任务结果回填” panel，缺 safe_copy blocked，Start/Confirm Dropoff/Cancel gating 不变。 | 通过 |
| Product closeout 更新 sprint 收口文档、OKR 和进度日志，Objective 5 不因本地 software proof 上调。 | Task D 已更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`；Objective 5 保持约 68%。 | 通过 |

## 2. 用户价值检查

本轮把上一轮 acceptance packet 从“验收清单”推进为“回填入口”。现场同学后续可以按同一 `evidence_ref` 放入八类材料，PC gate 判断材料完整性和 same-evidence-ref alignment；Robot diagnostics 与 mobile/web 只读显示缺口、owner handoff 和 rerun commands。普通用户主操作仍 fail closed，不会因为 backfill summary 出现而误开启 Start / Confirm Dropoff / Cancel。

## 3. OKR 对照

Objective 2：PR #4 route/elevator 现场材料链从 acceptance packet 推进到 result acceptance backfill，可支持后续真实 door state、target floor confirmation、human assistance note、dropoff/cancel completion 和 delivery result 回填，因此从约 95% 保守更新到约 96%。

Objective 3：Nav2/fixed-route runtime log、route completion signal、task record 进入 material-dir backfill 和 PC / Robot / mobile 只读核对链路，因此从约 95% 保守更新到约 96%。

Objective 5：仍缺真实 external proof，保持约 68%。本轮 `software_proof_docker_route_task_field_retest_result_acceptance_backfill_gate` 不能写成 production cloud、OSS/CDN、4G、DB/queue 或真实手机/browser 证明。

## 4. 剩余风险和证据缺口

本轮仍是 Docker/local software proof。尚未补齐真实 route/elevator field pass、真实 Nav2/fixed-route、真实 route completion signal、真实 task record、真实 dropoff/cancel completion、delivery success、真实手机/browser、production app、WAVE ROVER、真实串口/UART、HIL、Objective 5 external proof 或 PR #5 真实 2D LiDAR / ToF hardware materials。
