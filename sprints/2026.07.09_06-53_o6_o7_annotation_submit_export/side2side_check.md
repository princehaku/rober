# O6/O7 Annotation Submit Export Side-by-Side Check

## Sprint 类型和证据边界

- sprint_type: epic
- product_owner: product-okr-owner
- evidence_boundary: software_proof_local_mock_annotation_only
- safe_to_control: false
- delivery_success: false
- primary_actions_enabled: false
- robot_control_executed: false

## PRD 验收逐项对照

| PRD 验收口径 | 证据 | 结论 |
| --- | --- | --- |
| O6 unittest 覆盖合法 submit、幂等 update、task-level export、无 labels blocked、危险字段 true fail-closed、unsafe refs fail-closed | O6 report：`python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay` 输出 `Ran 149 tests ... OK`；实现摘要列明危险 true 字段、unsafe refs、非法 format/query、missing task、robot mismatch、empty labels、oversized labels 和 no-label export fail-closed。 | 通过 |
| O6 local/mock archive 接收并持久化 annotation submit | O6 report：`POST /api/o6/archive/labels` 返回 `local_mock_annotation_submit_written=true` 与 `submit_receipt.status=local_mock_annotation_written`，并写入 file-backed archive store。 | 通过，边界为 local/mock |
| O6 提供 task-level annotation dataset export，支持安全 JSON/JSONL 摘要 | O6 report：新增 `GET /api/o6/archive/labels/<task_id>/export?format=jsonl`，返回安全 `export_manifest` 和限量 `sample_rows[]`。 | 通过，非真实生产 dataset export |
| O6 consumer detail 或 labels detail 可稳定暴露 submit/export 结果 | O6 report：labels detail 与 O6 consumer `labeling` section 增加 submit/export 摘要。 | 通过 |
| PC catalog tests 覆盖 O7 adapter submit/export 成功路径和 fail-closed 路径 | O7 report：`catalog.test.ts` 输出 `Tests  204 passed (204)`，覆盖 adapter submit/export 成功路径、危险输入 fail-closed、PC route JSON contract。 | 通过 |
| PC App tests 覆盖 UI 触发 submit/export、receipt/export result 展示、缺 detail/blocked 时禁用或显示 blocker | O7 report：`App.test.ts` 输出 `Tests  247 passed (247)`，覆盖缺 detail 禁用、submit/export 成功展示、浏览器只请求 PC route、blocked 状态不触发 submit/export。 | 通过 |
| PC 后端只允许本机回环 relay base URL，不从浏览器直连 O6 | O7 report：adapter 只允许 `localhost`/`127.0.0.1`/`[::1]`，浏览器只调用 PC 后端 route。 | 通过 |
| UI 文案不暗示生产云、真实 API、可控制或送达成功 | O7 report：文案保持 local/mock、not_proven；安全字段固定 false。 | 通过 |
| Build、lint、git diff check 通过 | O7 report：build、lint 通过；Product closeout `git diff --check` 退出码 0、无输出。 | 通过 |
| `tech-done.md` 写清实际改动、验证结果、失败定位和剩余风险 | 本文件同目录 `tech-done.md` 已创建。 | 通过 |
| implementation 更新相关 `docs/` 文档 | O6 report 更新 `docs/interfaces/o6_cloud_archive_api.md`；O7 report 更新 `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`、`docs/interfaces/o7_realtime_operator_console.md`。 | 通过 |

## 危险字段核对

本轮所有真实能力字段继续保持 fail-closed：

- safe_to_control: false
- delivery_success: false
- primary_actions_enabled: false
- robot_control_executed: false
- connects_cloud_production: false
- real_annotation_api_connected: false
- real_dataset_export_connected: false
- cloud_write_executed: false
- submit_enabled: false
- dataset_export_available: false

## 用户价值和产品北极星对照

- 用户价值：运营/开发者可以围绕同一 `task_id` 在 PC 工作站触发 local/mock 标注提交，并查看 O6 返回的 receipt/export result，形成最小数据训练闭环。
- 产品北极星：仍服务于“可验证地可靠送垃圾”的长期目标；本轮只补复盘/打标/训练数据链路，不证明真实送达或控制能力。

## OKR 映射和方向判断

- O6 KR4：从只读/草稿推进到 local/mock annotation submit + task-level export 软件证据。
- O6 KR6：consumer detail 具备 submit/export 摘要回读，增强 PC/手机消费 API 的数据闭环。
- O7 KR4：PC 标注界面从 `submit_blocked_fail_closed` 展示推进到 local/mock submit/export 操作闭环。
- 方向判断：继续 O6/O7，但下一步必须消费真实 route artifacts、真实媒体可访问性或生产 backing，不能继续只堆 local/mock surface。

## 收口判断

本 sprint PRD 验收口径成立，closeout 轻量命令已确认文档存在、关键字段可检索和 `git diff --check` 通过。验收边界必须写为 `software_proof_local_mock_annotation_only`。

本轮不证明真实 annotation API、真实 dataset export、production cloud、真实媒体、真实机器人控制或 delivery success。
