# O6/O7 Route Bag Full Semantic Decode Matrix PRD

## 背景

O6/O7 已经能消费 route bag metadata、payload hash、有限语义摘要、pose progress 和 route execution readiness。但当前 OKR 仍明确缺 `raw ROS message payload 全量语义解析/回放`。本轮要把“payload 是否可被语义解码”从少数 summary 推进为 per topic/type 的覆盖矩阵，让后续 production cloud、PC 回放和标注平台能知道哪些 topic 已可读、哪些还缺 decoder 或真实证据。

## 用户价值

运营和开发者在 PC 端查看历史任务时，必须能判断一份 route bag 是否已经足够支撑回放和诊断，而不是只看到“有 payload hash”。覆盖矩阵能把问题拆成具体 topic/type：已解码、未支持、解码失败、被安全策略阻断，以及下一步需要补什么 decoder 或现场材料。

## P0 需求

- 新增 additive schema：`trashbot.route_bag_full_semantic_decode_matrix.v1`，O6 回读 schema 为 `trashbot.o6.route_bag_full_semantic_decode_matrix.v1`。
- 证据边界固定为 `software_proof_route_bag_full_semantic_decode_matrix_only`。
- Algorithm 对 DB3 `topics` 与 `messages.data` 只读扫描，按 safe topic/type 输出：
  - `topic_type_count`
  - `decoded_topic_type_count`
  - `unsupported_topic_type_count`
  - `failed_topic_type_count`
  - `decoded_message_sample_count`
  - `decode_failed_message_sample_count`
  - `unsupported_message_sample_count`
  - `coverage_ratio`
  - `topic_type_matrix[]` 的安全短摘要
- O6/O7 只接收 summary-only 字段，不回显 raw payload、base64、完整 hash、绝对路径、token、credential URL 或控制 topic。
- unsupported 或 failed 不应触发危险成功声明；它们必须进入 `blocked_reasons` 和 `next_required_evidence`。

## P1 需求

- O7 artifact bundle readiness 汇总 matrix 的 decoded/unsupported/failed counts。
- UI 在高级预览区显示 matrix 摘要和 sample topic/type，不解锁任何控制动作。
- 文档同步更新 `docs/navigation/field_route_evidence_manifest.md`、`docs/interfaces/o6_cloud_archive_api.md`、`docs/product/pc_tools_workstation.md` 和 `pc-tools/README.md`。

## 非目标

- 不做 ROS2 runtime 反序列化依赖。
- 不输出完整 ROS message payload 或媒体内容。
- 不补真实 live Nav2 route execution、真实 delivery record 或真实 operator confirmation。
- 不宣称 route execution success、delivery success、production cloud ready 或 robot control ready。

## 验收

- Algorithm unit test 覆盖 ready、missing DB3、unsupported topic type、decode failed、unsafe topic/text。
- O6 unit test 覆盖 field evidence、artifact bundle、consumer detail、`include=route_bag_full_semantic_decode_matrix` 和 unsafe fail-closed。
- O7 tests/build/lint 通过，覆盖 adapter、artifact bundle readiness 和 UI DOM 文案/数据。
