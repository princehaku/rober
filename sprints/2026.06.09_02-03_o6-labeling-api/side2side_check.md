# O6 Labeling API Side2Side Check

## 验收对照

| 需求 / 边界 | 本轮结果 | 证据 |
| --- | --- | --- |
| `POST /api/o6/archive/labels` 可写入既有 task 标注 | 通过 | `test_o6_cloud_archive_labels_endpoints_create_list_and_detail` / `test_o6_cloud_archive_labels_endpoint_idempotent_upsert_and_task_scope`
| 幂等更新 `task_id + item_id + label_type` | 通过 | 同上：重复同键返回 `duplicate=true`、`write_status=updated`、HTTP 200 |
| 幂等语义边界（新 key / 混合提交） | 通过 | 新增 `test_o6_cloud_archive_labels_endpoint_idempotent_upsert_and_task_scope`（同任务新增新 key）与 `test_o6_cloud_archive_labels_endpoint_batch_with_mix_existing_and_new_keys`（混合提交含旧+新 key） |
| `GET /api/o6/archive/labels` 返回任务摘要且不原样回显 labels | 通过 | `test_o6_cloud_archive_labels_endpoints_create_list_and_detail` 断言 `task_summary` 结构与 `label_summary` |
| `GET /api/o6/archive/labels` `status` query | 通过 | `status=pending` 与 `status=labeled` 查询在测试中覆盖 |
| `GET /api/o6/archive/labels` `limit` 上限 | 通过 | 测试覆盖 `limit=99999` 且响应 `limit <= O6_CLOUD_LABELING_MAX_LIST_LIMIT` |
| `GET /api/o6/archive/labels/<task_id>` 返回明细 | 通过 | `test_o6_cloud_archive_labels_endpoints_create_list_and_detail` 与 `test_o6_cloud_archive_labels_endpoint_idempotent_upsert_and_task_scope` |
| `unknown_task` fail-closed | 通过 | `test_o6_cloud_archive_labels_endpoint_idempotent_upsert_and_task_scope` 与 `unauthorized_task` 用例 |
| unsafe content / 缺字段 / 非对象 JSON fail-closed | 通过 | `test_o6_cloud_archive_labels_endpoint_rejects_bad_json_labels_and_invalid_query` |
| 固定 response boundary | 通过 | 所有 `POST`/`GET` 成功响应断言固定字段（`schema`, `source`, `proof_status`, `safe_to_control`, `connects_cloud_production`, `not_proven`） |
| 文档同步更新 | 通过 | `docs/interfaces/o6_cloud_archive_api.md`、`docs/product/pc_tools_workstation.md`、`cloud-relay/README.md` |

## 用户旅程收益对照

- 运营/开发可以在 PC 侧先建立固定状态的标注清单与明细查询，不依赖真实云标注服务。
- 任务失败路径有明确码（`unknown_task`、`unauthorized_task`、`bad_request`）用于前端复现与告警归类。
- 固定边界字段让产品验收页面能区分“能提交”与“只是 mock proof”，避免误导上线语义。
