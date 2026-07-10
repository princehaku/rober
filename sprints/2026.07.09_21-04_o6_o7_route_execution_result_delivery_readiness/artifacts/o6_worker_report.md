# O6 Worker Report

## 改动文件

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`

## 实际实现

- 新增 `trashbot.route_execution_result_delivery_readiness.v1` -> `trashbot.o6.route_execution_result_delivery_readiness.v1` 的 O6 sanitizer / placeholder / include / readback 链路。
- 将结果链 readiness 接入 `field_evidence_manifest` 与 `artifact_bundle` 两条 archive ingest 路径，并统一写入：
  - `task.field_evidence.route_execution_result_delivery_readiness`
  - `task.field_evidence_consumer_ingest.route_execution_result_delivery_readiness`
  - `task.artifact_bundle.route_execution_result_delivery_readiness`
  - archive detail / consumer detail 顶层 alias
  - `include=route_execution_result_delivery_readiness`
- fail-closed 规则保持保守：坏 schema、坏 proof_scope、危险 true、unsafe path/topic/url/token/raw/base64/text、缺必填字段时只降级当前 section 为 `blocked_not_proven`，不升级为真实 route execution / delivery success。
- 文档同步补充新合同的 schema、proof_scope、白名单字段、include 能力和 fail-closed 边界。

## 验证命令

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py && python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

## 验证结果

```text
Ran 162 tests in 58.732s

OK
```

## 失败定位

- 无。首轮验收命令通过。

## 剩余风险

- 这次只证明 `software_proof_route_execution_result_delivery_readiness_only` 的本地/mock readback，不证明真实 production cloud、真实 live Nav2 route execution、真实 delivery result、真实 operator confirmation 或真实 delivery success。
- O7 必须继续只消费 O6 摘要，不能自行扩展成更强语义。

## 协同需求

- 需要 Full-Stack 按同一 O6 摘要合同消费 `route_execution_result_delivery_readiness`。
- 不需要 Product / Hardware / Autonomy 额外协同即可完成本轮 O6 侧接线；Autonomy 侧只需保持 source schema 稳定。
