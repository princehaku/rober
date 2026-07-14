# Final - O6 Archive Task Query Filters

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_12-13_o6_archive_task_query_filters/`
- Closed at: 2026-07-13 12:29 CST
- Owner: `full-stack-software-engineer`
- Product status: accepted
- Proof boundary: `software_proof_o6_archive_task_query_filters_only`

## 实际改动

- `GET /api/o6/archive/tasks` 新增 fail-closed query filters：`robot_id`、`task_id`、`date=YYYY-MM-DD`、`status`、`limit`。
- 过滤语义为 AND；`limit` 在过滤后应用；`date` 按 UTC 日匹配，优先 `started_at_ms`，缺失时回落 `finished_at_ms`。
- 响应 metadata 新增 `archive_task_query_filters_ready_not_production_proof=true`、`archive_task_query_filters_proof_scope=software_proof_o6_archive_task_query_filters_only`、`applied_filters`、`filter_semantics=and`、`filtered_result_count` 和可选 `date_filter_source`。
- O6 interface docs 与 unit tests 已同步；`tech-done.md` 已记录实际改动、验证结果和剩余风险。

## 验证结果

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`：通过。
- `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`：通过，`Ran 189 tests in 83.926s OK`。
- `rg -n "archive task query filters|archive_task_query_filters_ready_not_production_proof|software_proof_o6_archive_task_query_filters_only|invalid_archive_task_query_filter|filter_semantics=and|safe_to_control=false|delivery_success=false|connects_cloud_production=false" docs/interfaces/o6_cloud_archive_api.md onboard/src/ros2_trashbot_behavior`：通过。
- `git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md sprints/2026.07.13_12-13_o6_archive_task_query_filters`：通过。

## OKR 收口

- O5 仍是最低进度 Objective，约 `85%`；本轮没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence，因此不继续消费 O5 support-only blocker。
- 本轮推进 Objective 6 的 lower-level archive task list query contract gap，接受为 local/mock software proof；O6 继续约 `93%`，主百分比不调整，KR `不归档`。
- O1 继续约 `94%`，O7 继续约 `93%`；本轮不触碰 HIL、route execution、delivery 或 PC UI/action/export/control 能力。

## 剩余风险

- 本轮不证明 production cloud、production DB/queue、production query capacity、真实机器人数据、真实手机/browser、route execution、delivery、operator acceptance、HIL、safe-to-control 或 O5 external evidence。
- 下一轮只有拿到真实 production/cloud evidence 或 explicit-operator-approved current live HIL/current route evidence，才应提升主 OKR；否则继续寻找不重复的软件 contract gap。
