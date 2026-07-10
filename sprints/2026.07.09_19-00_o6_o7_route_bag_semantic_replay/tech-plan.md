# O6/O7 Route Bag Semantic Replay Tech Plan

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 active Objective：O6（约 62%）和 O7（约 62%）并列最低。
- 本 sprint 是否针对该 Objective：是。
- 选择理由：本轮直接推进 O6/O7 的 route bag consumer/readback 能力，接续上一轮剩余缺口“raw ROS message payload 语义解码/回放”。
- final.md 收口时需复核：是否仍然只证明 software proof；是否有足够证据保守更新 O6/O7 进度；是否需要归档 KR。

## 合同设计

新增 Algorithm 输入合同：

- `route_bag_semantic_replay.schema=trashbot.route_bag_semantic_replay.v1`
- `route_bag_semantic_replay.proof_scope=software_proof_route_bag_semantic_replay_only`
- `status=ready_not_route_execution_proof | blocked_not_proven`
- 继承 route bag 安全字段：`source_label`、`task_id`、`task_id_source`、`db3_present`、`db3_read_ok`、`topic_count`、`message_count`、`timestamp_first_ns`、`timestamp_last_ns`、`sample_topic_names`
- 新增语义字段：
  - `semantic_sample_count`
  - `semantic_decode_ok_count`
  - `semantic_decode_failed_count`
  - `semantic_topic_types`
  - `laser_scan_summary`
  - `image_summary`
  - `tf_summary`
  - `blocked_reasons`
  - `next_required_evidence`

O6 回读合同：

- `schema=trashbot.o6.route_bag_semantic_replay.v1`
- `source_schema=trashbot.route_bag_semantic_replay.v1`
- `proof_scope=software_proof_route_bag_semantic_replay_only`
- 只保留白名单字段和 false safety flags。

O7 合同：

- shared contract 增加 `O7ConsumerRouteBagSemanticReplaySummary`。
- consumer adapter 从 O6 top-level、`field_evidence`、`field_motion_evidence_packet`、`artifact_bundle`、`artifact_bundle_consumer_ingest`、`artifact_bundle_readiness` 读取该 section。
- UI 只读展示 decode status、topic types、LaserScan/Image/TF 摘要、blocked reasons、next evidence。

## 文件范围

Algorithm owner 可改：

- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_manifest.py`
- `docs/navigation/field_route_evidence_manifest.md`
- `sprints/2026.07.09_19-00_o6_o7_route_bag_semantic_replay/artifacts/algorithm_worker_report.md`

Robot software owner 可改：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `sprints/2026.07.09_19-00_o6_o7_route_bag_semantic_replay/artifacts/o6_worker_report.md`

Full-stack owner 可改：

- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `docs/product/pc_tools_workstation.md`
- `pc-tools/README.md`
- `sprints/2026.07.09_19-00_o6_o7_route_bag_semantic_replay/artifacts/o7_worker_report.md`

Product owner 收口可改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.07.09_19-00_o6_o7_route_bag_semantic_replay/tech-done.md`
- `sprints/2026.07.09_19-00_o6_o7_route_bag_semantic_replay/side2side_check.md`
- `sprints/2026.07.09_19-00_o6_o7_route_bag_semantic_replay/final.md`

范围外文件不得改动；遇到必须改范围外文件时先在 worker report 写明原因，不直接扩大范围。

## 实现任务

### Algorithm

1. 在 `field_route_evidence_manifest.py` 中新增 `ROUTE_BAG_SEMANTIC_REPLAY_SCHEMA` / proof scope 常量。
2. 读取 DB3 `topics` 的 `type` 列和 `messages.data`，只对白名单 topic type 做有限 CDR 摘要解析。
3. 语义解析必须 fail closed：未知类型、短 payload、字段越界、unsafe text/topic、危险 true 均记录 blocked reason，不回显原始内容。
4. 将结果写入 manifest 顶层和 `field_motion_evidence_packet.route_bag_semantic_replay`。
5. 补单元测试：ready summary、bad schema/missing type、unsafe topic/text、decode failure、nested packet。

### O6

1. 增加 O6 语义 replay schema/proof scope 常量和 summary sanitizer。
2. 在 field-evidence、artifact-bundle、archive detail、consumer detail、`include=route_bag_semantic_replay` 中回读。
3. 坏 schema/proof_scope、危险 true、unsafe text/topic、缺必填字段时降级为 `blocked_not_proven`。
4. 补后端单元测试覆盖正常 ingest/readback、include 单独读取、危险字段 fail-closed。

### O7

1. 增加 shared contract 与 adapter sanitizer。
2. adapter 从 O6 detail 多个合法位置归一化 `route_bag_semantic_replay`。
3. artifact bundle readiness 合并 semantic replay blocked reasons 和 next evidence。
4. UI 展示 LaserScan/Image/TF 语义摘要，但不解锁 Play/Submit/Control。
5. 补前端测试和 UI snapshot/DOM 断言。

## 验收命令

Algorithm owner 必须运行：

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py && python3 -m unittest onboard.tests.test_field_route_evidence_manifest
```

O6 owner 必须运行：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py && python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

O7 owner 必须运行：

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
```

Product 收口验收：

```bash
test -f sprints/2026.07.09_19-00_o6_o7_route_bag_semantic_replay/artifacts/algorithm_worker_report.md
test -f sprints/2026.07.09_19-00_o6_o7_route_bag_semantic_replay/artifacts/o6_worker_report.md
test -f sprints/2026.07.09_19-00_o6_o7_route_bag_semantic_replay/artifacts/o7_worker_report.md
rg -n "route_bag_semantic_replay|software_proof_route_bag_semantic_replay_only|safe_to_control=false|delivery_success=false" sprints/2026.07.09_19-00_o6_o7_route_bag_semantic_replay OKR.md docs/process/okr_progress_log.md docs/navigation/field_route_evidence_manifest.md docs/interfaces/o6_cloud_archive_api.md docs/product/pc_tools_workstation.md
git diff --check -- OKR.md docs/process/okr_progress_log.md docs/navigation/field_route_evidence_manifest.md docs/interfaces/o6_cloud_archive_api.md docs/product/pc_tools_workstation.md pc-tools/README.md onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/catalog.test.ts pc-tools/workstation/test/App.test.ts sprints/2026.07.09_19-00_o6_o7_route_bag_semantic_replay
```

## 风险和边界

- 本轮只做 software proof，不证明真实 production cloud、真实 live Nav2 run、真实 robot motion、真实 delivery success、真实 OSS/CDN 或真实 annotation API/export。
- CDR 解析为最小白名单能力，不能扩展到控制 topic 或任意 message introspection。
- 如果某一端验证失败，必须由对应子 agent 定位修复后复验，不能以第一轮失败收口。
