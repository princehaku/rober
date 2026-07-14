# Tech Done - O6 Archive Task Query Filters

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_12-13_o6_archive_task_query_filters/`
- Owner: `full-stack-software-engineer`
- Completed at: 2026-07-13 12:25:08 CST
- Proof boundary: `software_proof_o6_archive_task_query_filters_only`

## 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 为 `GET /api/o6/archive/tasks` 增加 fail-closed query validator，支持 `robot_id`、`task_id`、`date=YYYY-MM-DD`、`status`、`limit`。
  - 过滤语义为 AND；`limit` 在过滤后应用；`date` 按 UTC 日过滤，优先 `started_at_ms`，缺失时回落 `finished_at_ms`。
  - 响应新增 `archive_task_query_filters_ready_not_production_proof=true`、`archive_task_query_filters_proof_scope=software_proof_o6_archive_task_query_filters_only`、`applied_filters`、`filter_semantics=and`、`filtered_result_count`，请求带 `date` 时新增 `date_filter_source`。
  - unknown query key、重复 query、非法日期、过长 id、path-like、URL-like、credential/token、raw/base64-like query value 统一 `400 bad_request`，错误原因包含 `invalid_archive_task_query_filter`，不回显危险原文。
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 新增 archive task list filter 覆盖：robot/task/date/status/limit、AND 组合、limit 后置、安全不存在 ID 返回空列表、fixed false 字段。
  - 新增 invalid query fail-closed 覆盖：unknown key、重复 key、非法日期、过长 ID、路径、URL/token、base64-like、非法 status，并验证失败 GET 不写 store。
- `docs/interfaces/o6_cloud_archive_api.md`
  - 增加 Archive Task Query Filters 合同，写明 proof boundary、query 字段、AND 语义、`date_filter_source`、`invalid_archive_task_query_filter` 和固定 false claims。

## 验证结果

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 通过，无输出。
- `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`
  - 通过：`Ran 189 tests in 83.926s`，`OK`。
- `rg -n "archive task query filters|archive_task_query_filters_ready_not_production_proof|software_proof_o6_archive_task_query_filters_only|invalid_archive_task_query_filter|filter_semantics=and|safe_to_control=false|delivery_success=false|connects_cloud_production=false" docs/interfaces/o6_cloud_archive_api.md onboard/src/ros2_trashbot_behavior`
  - 通过，命中 docs/interface、relay implementation、unit tests 和既有 fixed false anchors。
- `git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md sprints/2026.07.13_12-13_o6_archive_task_query_filters`
  - 通过，无 whitespace error。

## 失败定位 / 修复

- 本轮没有出现验证失败。
- 设计偏差说明：archive task `status` 过滤采用 consumer 侧 `task_status_summary` 词汇 `completed_mock` / `failed_mock` / `in_progress_mock` / `unknown_not_proven`，同时兼容 archive row 的 `local_mock_archive_ready`。这样补齐 archive list 与 consumer query 的合同 gap，但不改变现有 task summary item shape。

## 剩余风险

- 本轮仅证明 local/mock file-backed archive task list 查询合同，不证明 production cloud、production DB/queue、真实查询索引/容量、真实手机/browser、真实机器人数据、route execution、delivery、operator acceptance、HIL、safe-to-control 或 O5 external evidence。
- 当前 store 的正常 POST 路径要求 `started_at_ms` 必填；`finished_at_ms` fallback 已在 helper 层覆盖，但真实历史脏 state 中缺失 `started_at_ms` 的兼容仍需等生产迁移材料再验。
- 当前 worktree 在本轮前已有大量 dirty changes；本轮只在允许文件范围内增量修改，没有回滚或清理范围外文件。
