# O6 Labeling API Tech Done

## sprint_type

sprint_type: epic

## 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 新增 O6 labeling 本地 mock API：`POST /api/o6/archive/labels`、`GET /api/o6/archive/labels`、`GET /api/o6/archive/labels/<task_id>`。
  - 新增 `FileBackedO6CloudArchiveStore.upsert_labels / list_labels / get_task_labels`。
  - 标注只允许附着在已有 `archive task`，`unknown_task` 与 `unauthorized_task` fail-closed。
  - 标注幂等键为 `task_id + item_id + label_type`，首次写入返回 `write_status=created` + `duplicate=false`，重复返回 `write_status=updated` + `duplicate=true`。
  - 修正 `upsert_labels` 状态码语义：现在以本批次是否命中任意已存在 key 为准返回 `201/created` 或 `200/updated`，不再用 `existing_key_count` 判断。
  - 成功响应统一固定 `trashbot.o6.archive_labeling.v1` 与边界字段：`schema_version=1`、`source=local_mock_labeling`、`proof_status=not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`pc_only=true`、`submit_enabled=false`、`rollback_enabled=false`、`dataset_export_available=false`、`real_annotation_api_connected=false`、`real_dataset_export_connected=false`、`connects_cloud_production=false`、`robot_control_executed=false`。
  - `GET /api/o6/archive/labels` 返回任务摘要，不回显完整 labels 明细；支持 `status=pending|labeled|all` 与 `limit`（上限 100）。
  - 输入校验覆盖坏 JSON、非对象、类型错误、长度越界、unsafe claim。
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 新增 labeling 端到端测试：create/list/detail、idempotent、unknown/unauthorized、非法 payload、limit/status 参数。
  - 补充 O6 标注幂等语义回归测试：同任务新增新 key 时仍返回 `201/created/duplicate=false`，以及混合提交包含旧 key+新 key 时返回 `200/updated/duplicate=true`。
- `docs/interfaces/o6_cloud_archive_api.md`
  - 同步更新 O6 labeling API 合同（请求/响应/fail-closed）
- `docs/product/pc_tools_workstation.md`
  - 增补 PC O6 labeling 本地 contract 与固定边界说明
- `cloud-relay/README.md`
  - 新增 O6 labeling mock API 的部署/边界说明与 fail-closed 条款

## 验证结果

执行时间：2026-06-09 02:31:01 CST。

命令 1：python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
结果：通过，无输出。

命令 2：PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
Ran 127 tests in 39.611s
OK

命令 3（关键字检查）：`rg -n "trashbot.o6.archive_labeling.v1|POST /api/o6/archive/labels|GET /api/o6/archive/labels|real_annotation_api_connected=false|dataset_export_available=false|local_mock_labeling|unknown_task|unauthorized_task|idempotent" ...`
结果：命中预期关键字，覆盖 labeling 响应、边界与失败码。

命令 4（diff 健康）：git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md docs/product/pc_tools_workstation.md cloud-relay/README.md sprints/2026.06.09_02-03_o6-labeling-api
结果：通过，无 whitespace/语法冲突。

## 失败定位与修复

- 定位：`test_o6_cloud_archive_labels_endpoints_create_list_and_detail` 预期 `task_status="pending"`，但实现按 label 完整度返回 `partial`。
- 修复：更新该断言为 `"partial"`（与当前状态计算逻辑一致），保留 `pending`/`partial` 在列表过滤时的映射语义。
- 定位：`upsert_labels` 的 HTTP 语义依据 `existing_key_count > 0`，当 task 已有其他 labels 时提交新 key 会误判为“更新”。
- 修复：改为依据批次内是否命中任意既有 `(item_id, label_type)` 决定状态：有旧 key 命中则 `200/updated/duplicate=true`，全新 key 则 `201/created/duplicate=false`。混合批次按“任意命中即更新”解释。

## 剩余风险

- 当前仍是本地 mock：未对接真实 O7 标注 API、annotation review API、训练导出或 production cloud。
- `pending` 与 `partial` 语义需在消费端保持一致，避免把 `partial` 误读为完成。
- 未引入并发冲突治理（版本历史、审计签名、离线 reconcile）与持久化迁移策略，需后续迭代。
