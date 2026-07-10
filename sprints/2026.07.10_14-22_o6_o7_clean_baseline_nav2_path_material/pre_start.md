# O6/O7 Clean Baseline Nav2 Path Material Pre-start

## sprint_type

epic

## 背景

本轮自动化已读 `AGENTS.md`、`OKR.md`、最近 sprint 收口和自动化记忆。当前活跃 Objective 进度为：O5 约 85%、O1 约 86%、O6/O7 约 89%。

最低 O5 的下一步必须消费真实 production cloud、production DB/queue、4G/TLS 或 live endpoint evidence；当前环境变量检查没有 `TRASHBOT_CLOUD_BASE_URL`、`TRASHBOT_CLOUD_PRODUCTION_BASE_URL`、`TRASHBOT_CLOUD_PROBE_URL`、`TRASHBOT_O5_PRODUCTION_BASE_URL`、`DATABASE_URL`、`QUEUE_URL`、`OSS_ENDPOINT` 或 `CDN_BASE_URL`，因此本轮不能安全地产出 O5 主进度。O1 下一步必须是真实同一 run 的 WAVE ROVER `feedback_T1001.log`、motion command、operator report 和 HIL acceptance；当前工作区没有新的真实 nonzero L/R 证据，继续做 software gate 包装会重复消费同一 blocker。

为避免连续消费 O5/O1 的外部 blocker，本轮切到仍可推进的 O6/O7：把 `sprints/2026.06.11_11-15_clean_baseline_nav2_path_refresh/` 中的 clean-baseline Nav2 no-motion path proof 变成同一 `task_id` 可归档、可回读、可展示的安全材料。该材料包含首次失败 root-cause、一次重试成功、31 点 path、cleanup readback 和明确 no-motion 边界，比上一轮 current field evidence 更聚焦路线执行前置材料，但仍不能声明真实 route execution 或 delivery success。

## 本轮目标

- Algorithm 侧新增 `trashbot.clean_baseline_nav2_path_material.v1` 安全摘要，消费 clean-baseline Nav2 path refresh summary/latest/status artifacts。
- O6 archive/readback 支持该 additive section，能在 field evidence、artifact bundle、archive detail、consumer detail 和 `include=clean_baseline_nav2_path_material` 中回读。
- O7 consumer/detail 只读展示 clean-baseline Nav2 path material，包括 first failure、retry success、path point count、cleanup state、blocked reasons 和 next required evidence。
- 全链路固定 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`route_execution_success=false`、`hil_pass=false`、`connects_cloud_production=false`。

## owner

- Algorithm owner：`robot-algorithm-engineer`
- O6 backend owner：`robot-software-engineer`
- O7 consumer/UI owner：`full-stack-software-engineer`
- Product closeout owner：主节点验收后更新 sprint 收口、`OKR.md` 和 `docs/process/okr_progress_log.md`

## 风险边界

- 本轮不连接 production cloud、production DB/queue、TLS/4G、OSS/CDN。
- 本轮不执行新的上车命令，不发布 `/cmd_vel`，不调用 `NavigateToPose`、`FollowPath` 或 `/api/base/manual`。
- 本轮只证明 clean-baseline no-motion path proof 被 O6/O7 安全消费；不证明真实机器人运动、真实 route execution、delivery record、operator confirmation、delivery success、WAVE ROVER HIL 或 safe-to-control。
