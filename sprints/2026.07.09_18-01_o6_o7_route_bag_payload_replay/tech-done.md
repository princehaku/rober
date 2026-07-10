# O6/O7 Route Bag Payload Replay Tech Done

## sprint_type: epic

收口时间：2026-07-09 18:01 CST。

## 实际改动

- Algorithm 侧在 [`/Users/m1/apps/rober/onboard/scripts/field_route_evidence_manifest.py`](/Users/m1/apps/rober/onboard/scripts/field_route_evidence_manifest.py) 新增 `route_bag_payload_replay` 生成器，挂到 manifest 顶层和 `field_motion_evidence_packet.route_bag_payload_replay`。
- Algorithm 侧新增 `trashbot.route_bag_payload_replay.v1` 与 `software_proof_route_bag_payload_replay_only`，只读解析 DB3 `messages.data` BLOB，输出安全 payload 摘要和 replay readiness，不回显 raw/base64/content/绝对路径/完整 hash。
- Algorithm 侧将 `payload_sha256_prefix_samples` 收敛为 O6/O7 可消费的短 hex `string[]`，修复了最初结构化 dict 样本与后续合同不一致的问题。
- Algorithm 侧补齐缺 DB3、DB3 不可读、SQLite schema 不符、空 topic/message、payload 为空、unsafe topic、dangerous true、path/root/token/raw/base64/credential URL 等 fail-closed 分支，并更新测试与接口说明。
- O6 侧在 [`/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`](/Users/m1/apps/rober/onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py) 新增 `trashbot.o6.route_bag_payload_replay.v1` 读回合同，接入 field-evidence、artifact-bundle、archive task detail、consumer detail 和 `include=route_bag_payload_replay`。
- O7 侧在 [`/Users/m1/apps/rober/pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`](/Users/m1/apps/rober/pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts)、[`/Users/m1/apps/rober/pc-tools/workstation/src/shared/contracts.ts`](/Users/m1/apps/rober/pc-tools/workstation/src/shared/contracts.ts)、[`/Users/m1/apps/rober/pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`](/Users/m1/apps/rober/pc-tools/workstation/src/components/O7FixturePreviewPanel.vue) 和测试里接入 payload replay 只读展示，覆盖 source/status、topic/message/timestamp、payload size/hash prefix、blocked reasons、next evidence 和 false safety fields。
- 本轮同步更新了 [`/Users/m1/apps/rober/docs/navigation/field_route_evidence_manifest.md`](/Users/m1/apps/rober/docs/navigation/field_route_evidence_manifest.md)、[`/Users/m1/apps/rober/docs/interfaces/o6_cloud_archive_api.md`](/Users/m1/apps/rober/docs/interfaces/o6_cloud_archive_api.md) 和 [`/Users/m1/apps/rober/docs/product/pc_tools_workstation.md`](/Users/m1/apps/rober/docs/product/pc_tools_workstation.md)，保证 `docs/` 与实现同步。

## 验证结果

- Algorithm：`python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py && python3 -m unittest onboard.tests.test_field_route_evidence_manifest`
- O6：`python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py && python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`
- O7：`cd pc-tools/workstation && npm run test && npm run build && npm run lint`
- 收口验证：`test -f ...algorithm_worker_report.md`、`test -f ...o6_worker_report.md`、`test -f ...o7_worker_report.md`、`test -f ...tech-done.md`、`test -f ...side2side_check.md`、`test -f ...final.md`
- 收口验证：`rg -n "route_bag_payload_replay|software_proof_route_bag_payload_replay_only|O6|O7|safe_to_control=false|delivery_success=false|payload_sample_count=8|921652|479 passed|159|32|~62%" ...`
- 收口验证：`git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.09_18-01_o6_o7_route_bag_payload_replay`
- 结果摘要：Algorithm worker report 记录 `32 tests passed`，payload replay smoke 输出 `status=ready_not_route_execution_proof`、`proof_scope=software_proof_route_bag_payload_replay_only`、`payload_sample_count=8`、`payload_size_min_bytes=72`、`payload_size_max_bytes=921652`、`payload_size_avg_bytes=1371.093`、`payload_sha256_prefix_samples` 为短 hex `string[]`、`contains_abs_path=false`、`safe_to_control=false`、`delivery_success=false`。
- 结果摘要：O6 worker report 记录 `159 tests passed`，并保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
- 结果摘要：O7 worker report 记录 `npm run test` `479 passed`、`npm run build` 通过且仅有既有 Vite chunk warning、`npm run lint` 通过。

## 剩余风险

- 本轮只证明 DB3 payload-derived replay evidence 可被安全消费，不证明 raw ROS message payload 语义解码、真实 live Nav2 route execution、真实 robot motion、delivery record/operator confirmation 或 delivery success。
- 不证明真实 production cloud、production DB/queue、TLS/4G、OSS/CDN live traffic、真实 annotation API/export 或完整路线长期验收。
- O6/O7 仍只回显脱敏摘要，后续若再扩展 payload replay 字段名或嵌套位置，必须继续保持 fail-closed contract。

## 复核结论

- 本轮确实针对 `OKR.md` 4.1 节里完成度最低的 O6/O7。
- 方向判断保持不变：只把准现场 DB3 route bag 从 metadata 摘要推进到 payload-derived replay evidence，不把 payload 可读性写成真实路线执行或送达成功。
- 本轮不归档任何 KR。
