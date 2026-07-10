# O6 Worker Report

## 改动文件

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`

## 实际实现内容

- 在 `remote_cloud_relay.py` 新增 O6 安全摘要 `trashbot.o6.route_delivery_closure_packet.v1`，输入 schema 为 `trashbot.route_delivery_closure_packet.v1`，proof_scope 固定为 `software_proof_route_delivery_closure_packet_only`。
- 新增 `placeholder/request/unsafe/summary` 摘要链，支持从 `field_evidence_manifest`、`artifact_bundle` 和 `field_motion_evidence_packet` 读取 `route_delivery_closure_packet`。
- 将 `route_delivery_closure_packet` 接入：
  - field evidence ingest
  - artifact bundle ingest
  - archive task detail
  - `field_evidence_consumer_ingest`
  - `artifact_bundle_consumer_ingest`
  - consumer detail 顶层 alias
  - `include=route_delivery_closure_packet`
- 全局安全扫描前会剥离该 additive 子包，保证危险 true / unsafe 文本 / schema 或 proof_scope 不匹配 / 缺关键 linked flags 时，只把当前 closure packet 降级成 `blocked_not_proven`，不会阻断其它 field evidence 安全摘要写入。
- O6 摘要严格只保留：
  - `task_id`
  - `status`
  - `proof_scope`
  - `source`
  - `source_schema`
  - 5 个 linked readiness flags
  - `blocked_reasons`
  - `next_required_evidence`
  - 固定 false safety fields
- 单测补充了 field evidence、artifact bundle、consumer alias、显式 include，以及 missing / bad proof_scope / unsafe text / dangerous true 的 fail-closed 覆盖。
- 接口文档补充了新摘要合同、挂载位置和 `include=route_delivery_closure_packet` 白名单说明。

## 验证命令

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

## 验证结果

```text
.................................................................
----------------------------------------------------------------------
Ran 164 tests in 61.973s

OK
```

## 失败定位

- 本轮指定单测未失败。

## 剩余风险

- 仍然只是 local/mock software proof，不证明真实 production cloud、真实 live Nav2 route execution、真实 delivery record、真实 operator confirmation 或真实 delivery success。
- 当前 closure packet 依赖上游 Algorithm 提供的 `route_delivery_closure_packet`；若上游后续字段名或 ready 语义变化，O6 会按 fail-closed 降级为 `blocked_not_proven`。
- O7/UI 侧仍需单独消费该新摘要，否则 PC 端还看不到该 closure packet。

## 是否需要协同

- 需要 `robot-algorithm-engineer` 保持 `trashbot.route_delivery_closure_packet.v1` 上游字段稳定。
- 需要 `full-stack-software-engineer` 把 O7 consumer/UI 接到 `route_delivery_closure_packet`。
- 当前不需要 Product / Hardware 额外介入。
