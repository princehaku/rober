# Pre Start - O6 Archive Task Query Filters

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_12-13_o6_archive_task_query_filters/`
- Start time: 2026-07-13 12:13 CST
- Product owner: `product-okr-owner`
- Implementation owner: `full-stack-software-engineer`
- Primary Objective: Objective 6
- Secondary Objective: Objective 5 remains lowest but blocked on real external production evidence.
- Proof boundary target: `software_proof_o6_archive_task_query_filters_only`

## 上轮未完成项和阻塞

- `sprints/2026.07.13_11-13_o6_o7_label_query_filters/` 已完成 `/api/o6/archive/labels` 的 `robot_id` / `task_id` / `date` local/mock filter hardening。
- O5 仍是最低进度 Objective，约 `85%`，但需要真实公网 HTTPS/TLS、4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic 或真实手机/browser 材料；当前环境没有新的真实外部材料。
- 最近 O1/O3 已连续消费 stop path readiness、mock-only stop HIL capture gate、bounded route command plan 等 operator approval/current live HIL 前置 blocker；本轮不继续包装同一 blocker。

## 本轮切换理由

本轮不继续推进 O5 external evidence wrapper，因为上一轮 O5 readiness packet 已明确 `okr_credit_allowed=false` / `support_only_reason=no_real_production_external_evidence`，当前也没有新增真实生产或外部材料可消费。

本轮转向 Objective 6 的可推进软件合同 gap：`GET /api/o6/consumer/tasks` 已有 `robot_id` / `task_id` / `date` / `status` / `limit` 查询语义，但 lower-level `GET /api/o6/archive/tasks` 仍只返回全量 local/mock task list。补齐 archive task list filters 能让 task archive 自身支持按机器人、任务、日期和状态安全查询，避免 operator/O7 只能依赖 consumer 聚合面。

## 本轮目标

实现 `GET /api/o6/archive/tasks` 的 fail-closed task query filters：

- 支持 `robot_id`、`task_id`、`date=YYYY-MM-DD`、`status`、`limit`。
- filters 使用 AND 语义，`limit` 在过滤后应用。
- 响应 metadata 暴露 `archive_task_query_filters_ready_not_production_proof=true`、`applied_filters`、`filter_semantics=and`、`filtered_result_count`、`date_filter_source`。
- 非法 query、重复 query、path/URL/token/raw/base64-like 值必须 fail-closed，不泄露其它 task。
- 保持所有 production/control false fields，不声明 production cloud、route execution、delivery、HIL 或 safe-to-control。

## Owner 和范围

- `full-stack-software-engineer`
  - `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - `docs/interfaces/o6_cloud_archive_api.md`
  - `sprints/2026.07.13_12-13_o6_archive_task_query_filters/tech-done.md`

## 验收口径

- Unit tests must prove multi-task filtering, AND semantics, post-filter limit, invalid query fail-closed, and no mutation on failed GET.
- Docs must clearly state local/mock boundary and rejected claims.
- Product closeout must keep O5/O6/O7 percentages flat unless stronger evidence appears.

## 风险

- 当前 worktree 已有大量既有 dirty changes；本轮 owner 只能在上述范围内改动，并且不得回滚或清理其它文件。
- 该 sprint 是 O6 local/mock archive query hardening，不是 production query capacity proof。
