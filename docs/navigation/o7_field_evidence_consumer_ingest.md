# O7 Field Evidence Consumer Ingest

`pc-tools/workstation` 的 `GET /api/o7/field-evidence-consumer-ingest` 和 O7 Previews 面板里的 `Field evidence consumer ingest` 区块，把 `trashbot.field_evidence_manifest.v1` 接到 `route replay` / `labeling` 两条只读消费链上。它只做软件证明摘要，不做真实回放、真实标注提交或控制面下发。

## 输入

主入口接受三条本地/Mock 文件路径：

- `manifestJson`
- `routeReplayFixtureJson`
- `labelingFixtureJson`

manifest 必须是 `trashbot.field_evidence_manifest.v1`。如果 manifest 缺失、schema 不匹配、包含 unsafe copy、或显式带出 `delivery_success=true` / `safe_to_control=true` / `primary_actions_enabled=true` 这类控制或成功声明，入口都要 fail closed。

## 输出

输出统一为 `trashbot.pc_tools_workstation.o7_field_evidence_consumer_ingest.v1`，并继续保留：

- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `consumer_entry.blocked_reason`
- `blocked_reasons`
- `not_proven`
- `next_required_evidence`

route replay 和 labeling 的 preview 结果必须和 local/mock 与未来 live SSH 共用同一份结构，区别只在输入来源，不在 UI 语义。

## 状态

- `fixture_consumer_ready_not_proven`: 三条输入都读到且 preview ready
- `blocked_not_proven`: 任一层缺失、坏 JSON、schema 不匹配、unsafe copy、控制/成功声明、fixture 不完整或其它 fail closed 条件

## 边界

这个入口不证明：

- 真正的现场路线回放
- 真正的标注提交、回滚或导出
- 真正的机器人控制
- 真正的 SSH 可达或上车成功

它只把缺口整理成可读的、可追踪的 blocked reason 和 next required evidence，供 PC 工作台做本地验证和 future SSH smoke。
