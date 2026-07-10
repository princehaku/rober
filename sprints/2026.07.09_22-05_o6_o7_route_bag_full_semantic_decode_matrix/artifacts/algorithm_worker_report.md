# Algorithm Worker Report

运行时间：2026-07-09 22:19:10 CST

## 自主能力目标和本轮抓手

- 目标：把 route bag DB3 从有限语义摘要推进到 per topic/type 的 `route_bag_full_semantic_decode_matrix`。
- 抓手：只读 SQLite DB3 `topics` / `messages.data`，复用现有 CDR `decode_semantic_message`、topic/source safety、DB3 schema 检查和短 hash 摘要。
- 证据边界：`software_proof_route_bag_full_semantic_decode_matrix_only`，只证明离线 DB3 payload 语义覆盖矩阵可生成，不证明真实 live Nav2 route execution、真实 robot motion、delivery success 或 production cloud。

## 改动文件和接口影响

- `onboard/scripts/field_route_evidence_manifest.py`
  - 新增 `trashbot.route_bag_full_semantic_decode_matrix.v1` / `software_proof_route_bag_full_semantic_decode_matrix_only` additive。
  - 新增 topic type sanitizer，拒绝路径、凭证、raw/base64、token 和不安全 type 文本。
  - 新增 per topic/type matrix 聚合：`decoded`、`unsupported`、`failed`，以及 message sample counts、coverage ratio、decoder name 和短 sample hash prefix。
  - 同步写入 manifest 顶层与 `field_motion_evidence_packet.route_bag_full_semantic_decode_matrix`。
- `onboard/tests/test_field_route_evidence_manifest.py`
  - 新增 mixed ready、missing DB3、unsupported-only blocked、unsafe topic/type/source/metadata fail-closed 测试。
- `docs/navigation/field_route_evidence_manifest.md`
  - 同步说明新 additive、字段清单、安全边界和 false safety。
- `sprints/2026.07.09_22-05_o6_o7_route_bag_full_semantic_decode_matrix/artifacts/algorithm_worker_report.md`
  - 写入本报告。

接口输出新增字段：

- `topic_type_count`
- `decoded_topic_type_count`
- `unsupported_topic_type_count`
- `failed_topic_type_count`
- `decoded_message_sample_count`
- `decode_failed_message_sample_count`
- `unsupported_message_sample_count`
- `coverage_ratio`
- `topic_type_matrix[]`

所有安全字段保持：

- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`
- `live_nav2_run_proven=false`
- `route_execution_success=false`
- `connects_cloud_production=false`

## 实现内容

- DB3 继续使用 Python 标准库 `sqlite3` 只读打开，不引入 ROS2 runtime。
- `topic_type_matrix[]` item 只输出安全 topic/type、计数、`status`、`blocked_reason`、`decoder_name` 和 12 位 `sample_sha256_prefixes`。
- supported decoder 命中并全部样本成功时计入 decoded；未知安全 ROS type 计入 unsupported；支持类型解码异常计入 failed。
- `status=ready_not_route_execution_proof` 只在 DB3 可读、至少 1 个 decoded topic/type、无 unsafe topic/type、无 dangerous true、无 unsafe source/metadata 时输出；否则为 `blocked_not_proven`。
- unsupported/failed 在 ready 场景中仍保留到 `blocked_reasons` 和 `next_required_evidence`，用于后续 O6/O7 展示真实缺口。

## 测试、dry-run 或上车验证结果

验收命令：

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py && python3 -m unittest onboard.tests.test_field_route_evidence_manifest
```

结果片段：

```text
................................................
----------------------------------------------------------------------
Ran 48 tests in 0.251s

OK
```

补充检查：

```bash
git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.09_22-05_o6_o7_route_bag_full_semantic_decode_matrix/artifacts/algorithm_worker_report.md
```

结果：通过，无 whitespace error 输出。

## 数据、样本或调试输出变化

- mixed ready fixture 输出 3 个 topic/type：
  - `/scan` + `sensor_msgs/msg/LaserScan` -> `decoded`
  - `/diagnostics` + `custom_msgs/msg/Diagnostics` -> `unsupported`
  - `/camera/image_raw` + `sensor_msgs/msg/Image` -> `failed`
- mixed ready fixture 顶层计数：
  - `topic_type_count=3`
  - `decoded_topic_type_count=1`
  - `unsupported_topic_type_count=1`
  - `failed_topic_type_count=1`
  - `coverage_ratio=0.333`
- unsafe fixture 验证 `/cmd_vel`、绝对路径、credential URL、secret/raw/base64 文本不进入 evidence JSON。

## 失败定位

无。本轮验收命令与 `git diff --check` 均通过。

## 剩余风险和下一步能力建设建议

- 剩余风险：当前 decoder 仍只覆盖 `LaserScan`、`Image`、`TFMessage` 三类安全语义，未知类型只进入 unsupported，不代表 raw ROS message payload 已全量语义回放。
- 剩余风险：本轮仍是离线 DB3 software proof，不证明真实 production cloud、真实 live Nav2、真实 robot motion、真实 delivery record、真实 operator confirmation 或真实 delivery success。
- 下一步建议：由 O6/O7 owner 接入该 additive 到 archive/readback/UI，并在后续 sprint 补更多安全 decoder 或消费真实现场 route bag 长期样本。
