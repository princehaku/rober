# O6 Worker Report

## 实际改动文件

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `sprints/2026.07.10_11-30_o6_o7_same_task_route_execution_material_packet/artifacts/o6_worker_report.md`

## 实现内容

- 新增 O6 readback schema：`trashbot.o6.same_task_route_execution_material_packet.v1`。
- 固定 proof / evidence boundary：`software_proof_same_task_route_execution_material_packet_only`。
- 支持从 `field_evidence_manifest`、`artifact_bundle`、`field_motion_evidence_packet.same_task_route_execution_material_packet` 读取 Algorithm packet，并写入同一 `task_id` 的 O6 archive。
- 支持 archive task detail、`field_evidence`、`artifact_bundle`、`field_evidence_consumer_ingest`、`artifact_bundle_consumer_ingest`、consumer detail 顶层 alias 和 `include=same_task_route_execution_material_packet` 回读。
- 只保留安全摘要字段：`task_id`、`status`、`same_task_id_consumed`、`route_execution_material_consumed`、`same_task_field_material_packet_status`、`source_sections`、`material_summaries`、`material_sample_refs`、`blocked_reasons`、`next_required_evidence` 和固定 false flags。
- 对 schema mismatch、proof scope / evidence boundary mismatch、task mismatch、unsafe text、dangerous true、raw/base64、绝对路径、credential-like URL、token/secret/connection string、traceback/response body 执行 section-local fail-closed，只降级 `same_task_route_execution_material_packet`，不污染其它 evidence section。

## 验证结果

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
# 通过，无输出

python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
# Ran 171 tests in 68.334s
# OK
```

## 失败定位

- 首轮完整 unittest 失败 1 个断言：negative fixture 改了 artifact bundle `task_id`，但未同步既有 `same_task_field_material_packet.task_id`，触发旧合同的 task mismatch fail-closed。
- 已修复：negative fixture 中同步既有 field material packet 的 `task_id`，复跑单测和完整套件通过。

## 剩余风险

- 本轮证据边界仍是 `software_proof_same_task_route_execution_material_packet_only`。
- 不证明真实 production cloud、production DB/queue、live Nav2 route execution、真实机器人运动、真实 delivery record、真实 operator confirmation、hardware safety/HIL 或真实 delivery success。
- O7 readiness 必须只信 O6 顶层 `same_task_route_execution_material_packet.status`，不得从 child material ready 推导 delivery success 或 safe-to-control。
