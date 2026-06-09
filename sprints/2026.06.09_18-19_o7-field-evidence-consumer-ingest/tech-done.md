# Tech Done - O7 Field Evidence Consumer Ingest

## sprint_type: epic

## 实际改动

- 在 `pc-tools/workstation/src/shared/contracts.ts` 新增 `trashbot.pc_tools_workstation.o7_field_evidence_consumer_ingest.v1` 契约，以及 `trashbot.field_evidence_manifest.v1` 摘要类型。
- 在 `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts` 新增 `buildO7FieldEvidenceConsumerIngest()`，把 manifest、route replay fixture、labeling fixture 拼成同一份 fail-closed 只读摘要。
- 在 `pc-tools/workstation/src/server/index.ts` 和 `pc-tools/workstation/src/server/catalog.ts` 暴露 `GET /api/o7/field-evidence-consumer-ingest`。
- 在 `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue` 增加 `Field evidence consumer ingest` 入口，支持 local/mock manifest 路径输入和统一摘要展示。
- 在 `pc-tools/workstation/test/catalog.test.ts` 增加成功路径和缺失路径两组 builder 测试。
- 在 `pc-tools/workstation/test/App.test.ts` 增加 ingest 面板 UI smoke，并补齐 labeling preview 调用断言。
- 更新 `pc-tools/README.md`、`pc-tools/evidence/README.md`、`docs/navigation/fixed_route_workflow.md`、`docs/navigation/field_route_evidence_manifest.md`，并新增 `docs/navigation/o7_field_evidence_consumer_ingest.md`。

## 验证结果

### 1. 单测

`cd pc-tools/workstation && npm test`

关键结果：

```text
Test Files  2 passed (2)
Tests       46 passed (46)
```

### 2. 构建

`cd pc-tools/workstation && npm run build`

关键结果：

```text
vite v7.3.3 building client environment for production...
✓ built in 1.33s
```

### 3. API smoke

`cd pc-tools/workstation && npm run api`

关键结果：

```text
pc-tools workstation API listening on http://127.0.0.1:8787
```

### 4. curl smoke

`/api/o7/route-replay-preview` 失败闭合时返回：

```json
{"preview_status":"blocked_not_proven","input_status":{"status":"missing","failure_reason":"fixture_json_missing"}}
```

`/api/o7/labeling-preview` 失败闭合时返回：

```json
{"preview_status":"blocked_not_proven","input_status":{"status":"missing","failure_reason":"fixture_json_missing"}}
```

`/api/o7/operator-console` 维持：

```json
{"operator_mode":"observe_only","safe_to_control":false,"delivery_success":false,"primary_actions_enabled":false}
```

`/api/o7/consumer-read/tasks` 在本地回环上游不可达时 fail closed：

```json
{"list_status":"fail_closed","fail_closed_reason":"consumer_list_fetch_failed"}
```

`/api/o7/field-evidence-consumer-ingest` 的成功本地 fixture smoke 返回：

```json
{"ingest_status":"fixture_consumer_ready_not_proven","consumer_entry":{"fallback_mode":"local_mock","blocked_reason":""}}
```

`/api/o7/field-evidence-consumer-ingest` 的缺失路径 smoke 返回：

```json
{"ingest_status":"blocked_not_proven","manifest_input_status":{"status":"missing"}}
```

### 5. 静态检查

`git diff --check`

结果：无输出，通过。

## 剩余风险

1. 真实 live SSH 仍未在本轮恢复；当前只证明 local/mock 路径和 fail-closed 分支。
2. `consumer-read/tasks` 仍依赖本地回环上游服务可达，当前 smoke 只能证明 fail-closed，不证明真实 O6 连通。
3. 后续如果 route replay / labeling 的真实 live SSH 输出结构变化，需要继续保持同一份 ingest contract，不要把 UI 逻辑分叉成两套。
