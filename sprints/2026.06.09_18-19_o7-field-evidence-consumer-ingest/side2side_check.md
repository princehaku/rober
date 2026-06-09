# Side2Side Check - O7 Field Evidence Consumer Ingest

## sprint_type: epic

## 用户旅程变化

这轮把用户从“只有 manifest gate”推进到“manifest 可以直接进入 O7 route replay / labeling 消费链”。

新的旅程是：

1. 用户准备 `trashbot.field_evidence_manifest.v1`
2. 用户在 O7 Previews 里加载 manifest、route replay fixture、labeling fixture
3. 工作台返回统一的 consumer ingest 摘要
4. 缺材料、schema 不匹配、预检未 ready、SSH 不可达时，界面只给 blocked reason 和 next required evidence，不冒充成功

## 触点收益

- `Field evidence consumer ingest` 成为 manifest 的主入口，而不是孤立 preview。
- local/mock fixture 和 future live SSH 共享同一输出结构，减少用户切换成本。
- `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false` 在 ingest 入口中持续显式，避免误把软件证明当作现场成功。

## 对照结果

- 入口完整：完成。manifest 现在有明确主入口进入 O7 消费链。
- fallback 完整：完成。local/mock 与 future live SSH 保持同一份 summary 结构。
- 状态完整：完成。缺失材料、SSH 不可达、preflight 未 ready、fixture 不完整均可 fail closed。
- 契约完整：完成。shared/server contract 已表达 route replay / labeling 的关键字段。
- 安全完整：完成。控制与成功声明保持关闭。
- 可测完整：完成。已覆盖完整与缺失两种 local fixture 路径。
- 可读完整：完成。导航文档已补齐入口、状态与边界说明。

## 仍需机器人侧配合的事项

1. live SSH 恢复后，需要再补一轮附加 smoke，确认远端 manifest/fixture 路径仍然映射到同一份 ingest 输出。
2. 如果上位机真实输出字段变化，需保持 route replay / labeling 结构和 fail-closed 语义不变。
