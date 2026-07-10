# O6/O7 Route Bag Full Semantic Decode Matrix Tech Done

## Sprint 类型

sprint_type: epic

收口时间：2026-07-09 22:45 CST。

## 实际改动

### Algorithm

- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_manifest.py`
- `docs/navigation/field_route_evidence_manifest.md`
- `sprints/2026.07.09_22-05_o6_o7_route_bag_full_semantic_decode_matrix/artifacts/algorithm_worker_report.md`

实现 `trashbot.route_bag_full_semantic_decode_matrix.v1`，将 route bag DB3 的 `topics` / `messages.data` 只读聚合成 per topic/type decode coverage matrix，并同时写入 manifest 顶层和 `field_motion_evidence_packet.route_bag_full_semantic_decode_matrix`。矩阵区分 `decoded`、`unsupported`、`failed`，输出 topic/type counts、message sample counts、coverage ratio、safe sample hash prefix、blocked reasons 和 next evidence。

### O6

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `sprints/2026.07.09_22-05_o6_o7_route_bag_full_semantic_decode_matrix/artifacts/o6_worker_report.md`

实现 `trashbot.o6.route_bag_full_semantic_decode_matrix.v1`，接入 field evidence、artifact bundle、archive task detail、consumer detail 和 `include=route_bag_full_semantic_decode_matrix`。O6 只回读 counts、coverage ratio、safe topic/type matrix、blocked reasons、next evidence 和 false safety fields；bad schema/proof_scope、dangerous true、unsafe topic/text/path/url/token/raw/base64、缺计数或负数计数均 fail-closed。

### O7

- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `docs/product/pc_tools_workstation.md`
- `pc-tools/README.md`
- `sprints/2026.07.09_22-05_o6_o7_route_bag_full_semantic_decode_matrix/artifacts/o7_worker_report.md`

O7 consumer detail 默认 include 新 matrix，从 direct、field evidence、field motion packet、artifact bundle、artifact bundle consumer ingest 和 artifact bundle readiness 等候选源读取。PC UI 在 O7 preview 中显示 matrix status、coverage、decoded/unsupported/failed counts、sample topic/type、blocked reasons 和 next evidence，并保持只读。

## 验证结果

- Algorithm：`python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py && python3 -m unittest onboard.tests.test_field_route_evidence_manifest`，结果 `Ran 48 tests in 0.251s OK`。
- O6：`python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py && python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`，结果 `Ran 163 tests in 61.181s OK`。
- O7：`cd pc-tools/workstation && npm run test && npm run build && npm run lint`，结果 `Test Files 3 passed (3)`、`Tests 482 passed (482)`、build `built in 1.74s`、lint exit code 0。

## 偏差与返工

- O6 首轮 matrix 二次 sanitize 把 nested `counts` 读丢，随后兼容输入 schema 顶层 counts 和 O6 nested counts；HTTP 响应的 generic `safe_value()` 误删 topic/matrix 字段，已通过安全例外修复。
- O7 首轮 fixture 使用 `/camera/image_raw` 命中既有 topic safety guard，且 readiness candidate 可能携带已适配的 `sample_topic_type_matrix`；已改用安全 sample topic 并同时兼容 `topic_type_matrix` / `sample_topic_type_matrix`。

## 剩余风险

- 证据边界为 `software_proof_route_bag_full_semantic_decode_matrix_only`。
- 当前 decoder 仍只覆盖 `LaserScan`、`Image`、`TFMessage`，unknown safe type 会进入 unsupported；这不是 raw ROS message payload 全量语义回放完成。
- 不证明真实 production cloud、真实 DB/queue、真实 OSS/CDN、真实 4G/TLS、真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation、真实 delivery success 或真实 annotation API/export。
- 本轮不归档 KR。
