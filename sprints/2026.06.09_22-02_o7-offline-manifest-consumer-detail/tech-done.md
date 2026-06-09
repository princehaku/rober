# O7 Offline Manifest Consumer Detail Tech Done

## sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`：`buildO7ConsumerTaskDetail()` 新增可选 `fieldEvidenceManifestJson` 输入。远端 O6 detail 已有合法 `trashbot.field_evidence_manifest.v1` 或 `trashbot.pc_tools_workstation.o7_field_evidence_consumer_ingest.v1` 时优先远端；远端缺 field evidence 时才读取本地 manifest 补齐 `field_evidence`。坏 JSON、缺文件、非 object、schema mismatch、unsafe copy、`safe_to_control=true`、`primary_actions_enabled=true`、`delivery_success=true` 等危险声明均 fail closed。
- `pc-tools/workstation/src/server/index.ts`、`pc-tools/workstation/src/client/workstationApi.ts`、`pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`：把 `fieldEvidenceManifestJson=<local-json>` 从 UI 输入一路传到 PC 后端，页面展示 local manifest query、field evidence contract/input、manifest gate 和 fail-closed reason。
- `pc-tools/workstation/src/shared/contracts.ts`：扩展 consumer detail `field_evidence.input_status`，覆盖本地 manifest `bad_json` / `read_error` 等 fail-closed 状态。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`：新增/调整本地 manifest fallback、远端优先、缺本地输入、unsafe local manifest、UI query 拼接覆盖。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步 O7 consumer-detail 本地 offline manifest bridge 行为和边界。

## 验证结果

- `cd pc-tools/workstation && npm run build`：通过。`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`，Vite 输出 `31 modules transformed`。
- `cd pc-tools/workstation && npm run test`：通过。`Test Files 2 passed (2)`，`Tests 51 passed (51)`。
- `cd pc-tools/workstation && npm run lint`：通过。`eslint .` 无报错。
- `rg -n "fieldEvidenceManifestJson|trashbot.field_evidence_manifest.v1|safe_to_control=false|primary_actions_enabled=false|delivery_success=false" pc-tools docs/product/pc_tools_workstation.md sprints/2026.06.09_22-02_o7-offline-manifest-consumer-detail`：通过，命中新 query、manifest schema 与 fail-closed false 字段。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 当前证明边界是 `software_proof_local_manifest_consumer_detail_only`：不连接真实 O6 生产云、不读取真实 OSS/DB、不证明真实路线回放、真实标注提交或真实机器人运动。
- 本地 manifest 只补齐 `field_evidence`；`trajectory/events/evidence/labeling/inference/tunnel` 仍依赖远端 O6 detail 的本机回环 mock/relay 响应质量。
- 本轮未触碰 `onboard/**`、`cloud-relay/**`、硬件/vendor 资料或其他 sprint 目录。

## 完成前反思

- 已确认没有把 `gate_pass=true` 外推成 `delivery_success=true`，新增路径仍固定 `safe_to_control=false`、`primary_actions_enabled=false`、`delivery_success=false`、`robot_control_executed=false`。
- 本地 manifest fallback 只在远端 field evidence 缺失时触发；远端已有合法 field evidence 时不会被本地 query 覆盖。
- 当前时间：2026-06-09 22:12:05 CST。
