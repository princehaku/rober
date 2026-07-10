# O6 Worker Report

## 本轮范围

- 在 `remote_cloud_relay.py` 中新增 `route_bag_payload_replay` 读回合同，支持 `trashbot.route_bag_payload_replay.v1` 和 `trashbot.o6.route_bag_payload_replay.v1`。
- 将 `route_bag_payload_replay` 接入 `field_evidence`、`artifact_bundle`、`field_evidence_consumer_ingest`、`artifact_bundle_consumer_ingest`、archive task detail 和 consumer detail / `include=route_bag_payload_replay`。
- 补齐 `o6_cloud_archive_api.md` 的 schema、proof_scope、alias 和 include 文档。
- 补充单测，覆盖正常读回、缺失、坏 schema、unsafe topic、危险 true 和 consumer include。

## 实际改动

- 新增 `route_bag_payload_replay` 的 blocked placeholder、request 提取、unsafe 判定和 summary。
- 新增 payload replay 专用的安全 topic / hash prefix / 精确纳秒时间戳解析。
- 让 O6 的 global gate 对 payload replay 走 additive fail-closed，不把坏 replay 直接升级成整包拒绝。
- 在现有 field-evidence / artifact-bundle 读面中加入新的 top-level alias。

## 验证结果

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`
- 结果：159 个测试全部通过。

## 剩余风险

- 这条链路仍然只是 software proof / local mock，不证明真实 DB3、真实 Nav2、真实底盘控制或 delivery success。
- O6 仍然只回显脱敏摘要；后续如果 Algorithm worker 的 payload replay 源字段命名有偏差，需要再对齐一次 contract。

## 本轮时间

- 2026-07-09
