# O6 Worker Report - route_bag_full_semantic_decode_matrix

更新时间：2026-07-09 22:30:37 CST

## 实际改动文件

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `sprints/2026.07.09_22-05_o6_o7_route_bag_full_semantic_decode_matrix/artifacts/o6_worker_report.md`

## 实际实现内容

- 新增 O6 additive 合同：
  - 输入 schema：`trashbot.route_bag_full_semantic_decode_matrix.v1`
  - O6 输出 schema：`trashbot.o6.route_bag_full_semantic_decode_matrix.v1`
  - proof_scope：`software_proof_route_bag_full_semantic_decode_matrix_only`
- 接入 O6 archive/readback 主链路：
  - `field_evidence_manifest`
  - `artifact_bundle`
  - archive task detail
  - `field_evidence_consumer_ingest`
  - `artifact_bundle_consumer_ingest`
  - consumer detail 顶层 alias
  - `include=route_bag_full_semantic_decode_matrix`
- 只输出 summary-only 字段：
  - `counts`
  - `coverage_ratio`
  - safe `topic_type_matrix`
  - `blocked_reasons`
  - `next_required_evidence`
  - false safety fields
- 保持全字段 false safety：
  - `safe_to_control=false`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
  - `robot_control_executed=false`
  - `live_nav2_run_proven=false`
  - `route_execution_success=false`
  - `connects_cloud_production=false`
- fail-closed 覆盖：
  - bad schema
  - bad proof_scope
  - dangerous true
  - unsafe topic/text/path/url/token/raw/base64
  - 缺必填计数
  - 负数计数
  - 非法 coverage ratio
- 为 `safe_value` 增加 matrix summary 字段例外，确保 HTTP 响应不误删已由专用 sanitizer 裁剪过的 `topic/topic_type_*` 字段。
- 更新 `docs/interfaces/o6_cloud_archive_api.md`，记录新 schema、include 白名单、字段边界和 fail-closed 规则。

## 验证命令与结果

命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py && python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

最终结果：

```text
Ran 163 tests in 61.181s

OK
```

补充检查：

```bash
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md
```

结果：通过，无 whitespace error 输出。

## 失败定位与修复

- 第一轮失败：matrix 写入后被降级为 `blocked_not_proven`。定位为 O6 schema 二次 sanitize 时只读取顶层计数字段，未兼容 O6 输出中的 nested `counts`。已修复为同时兼容输入 schema 顶层 counts 与 O6 schema nested `counts`。
- 第二轮失败：HTTP 响应缺少 `topic_type_count` / `topic_type_matrix` / `topic`。定位为全局 `safe_value` 按 key 名脱敏，误删了已经由专用 sanitizer 裁剪过的 matrix summary 字段。已把 `topic`、`topic_type_count`、`decoded_topic_type_count`、`unsupported_topic_type_count`、`failed_topic_type_count`、`topic_type_matrix` 加入安全例外。

## 剩余风险

- 本轮只证明 O6 local/mock software readback，不证明真实 production cloud、真实 DB/queue、真实 OSS/CDN、真实 4G/TLS。
- 本轮不证明真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation 或真实 delivery success。
- O7 和 Algorithm 文件未按本 owner 范围修改；需要对应 owner 继续完成 matrix 生成与 UI 消费。

## 协同需求

- `robot-algorithm-engineer`：确认 Algorithm 输出字段与 O6 接收字段一致，尤其是 `topic_type_matrix[]` 的 topic/type/status/counts。
- `full-stack-software-engineer`：消费 O6 `include=route_bag_full_semantic_decode_matrix`，在 O7 只读展示 counts、coverage、matrix、blocked reasons 和 false safety fields。
- 暂不需要 Product 或 Hardware 介入；本轮不涉及硬件参数或真实串口/WAVE ROVER 集成。
