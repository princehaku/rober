# Tech Done - O7 Mission Evidence Bundle Export

sprint_type: epic

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：新增 `trashbot.pc_tools_workstation.o7_mission_evidence_bundle_export_result.v1` receipt contract，固定 `software_proof_o7_o6_mission_evidence_bundle_export_only` proof scope 和 false fields。
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`：新增 selected-task mission evidence bundle export builder，固定读取 O6 consumer detail，并对非回环 URL、credentials/query/hash、task mismatch、schema mismatch、dangerous true fields、unsafe refs/content fail closed。
- `pc-tools/workstation/src/server/index.ts` 与 `pc-tools/workstation/src/client/workstationApi.ts`：挂载并调用 `GET /api/o7/consumer-read/tasks/:taskId/mission-evidence/export?baseUrl=<local-loopback-url>&format=json`。
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`：在 O7 consumer read primary path 增加 selected-task bundle export action、禁用条件、receipt 摘要、section summaries、false fields 和 not_proven 展示。
- `pc-tools/workstation/test/catalog.test.ts` 与 `pc-tools/workstation/test/App.test.ts`：覆盖 adapter success/fail-closed matrix、HTTP endpoint smoke、UI action request 和 receipt summary。
- `docs/interfaces/o7_realtime_operator_console.md` 与 `docs/product/pc_tools_workstation.md`：同步接口、用户旅程、fail-closed 条件和 proof boundary。

## 用户旅程变化和触点收益

O7 primary path 现在从“只能查看 selected task detail”前进一步到“可导出 selected-task local/mock mission evidence bundle receipt”。Operator 必须先选中 task 并加载 detail，页面才允许点击 export；没有 selected task/detail、detail fail-closed 或 task mismatch 时不会假装成功。

receipt 聚合 mission events、field evidence、same-task replay packet/readiness、delivery result/readiness、route/closure/material sections 的安全摘要，便于产品/算法/机器人侧在同一 `task_id` 上核对证据链是否已经被 O6/O7 主路径消费。

## 接口影响

- 新增 O7 PC adapter endpoint：`GET /api/o7/consumer-read/tasks/:taskId/mission-evidence/export?baseUrl=<local-loopback-url>&format=json`。
- 返回 schema：`trashbot.pc_tools_workstation.o7_mission_evidence_bundle_export_result.v1`。
- 成功状态：`local_mock_mission_evidence_bundle_ready`。
- proof scope：`software_proof_o7_o6_mission_evidence_bundle_export_only`。
- 固定 false fields：`safe_to_control=false`、`delivery_success=false`、`route_execution_success=false`、`hil_pass=false`、`connects_cloud_production=false`、`robot_control_executed=false`、`real_cloud_db_connected=false`、`real_oss_connected=false`。
- export 只返回 receipt 摘要和 basename refs，不导出 raw artifact body、真实路径、完整 URL、token、credential、real dataset 或 production cloud 内容。

## 验证结果

- `cd pc-tools/workstation && npm run test`：通过，`Test Files 3 passed (3)`，`Tests 504 passed (504)`，`Duration 49.58s`。
- `cd pc-tools/workstation && npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成；Vite 仅提示既有 bundle size warning。
- `cd pc-tools/workstation && npm run lint`：通过，`eslint .` 无输出错误。
- `rg -n "mission evidence bundle|mission-evidence/export|o7_mission_evidence_bundle_export|software_proof_o7_o6_mission_evidence_bundle_export_only|safe_to_control=false|delivery_success=false|route_execution_success=false|hil_pass=false|不归档" pc-tools/workstation/src docs/interfaces docs/product sprints/2026.07.13_18-17_o7_mission_evidence_bundle_export/tech-done.md`：通过，命中新 endpoint、schema/proof scope、UI copy、docs 和本 tech-done 边界字段；仓库既有大量 `safe_to_control=false` / `delivery_success=false` 命中，命令退出码为 0。
- `git diff --check -- pc-tools/workstation/src pc-tools/workstation/test docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md sprints/2026.07.13_18-17_o7_mission_evidence_bundle_export`：通过，无 whitespace/error 输出。

## 失败定位

- 第一轮 `npm run test` 失败于新增 `catalog.test.ts` fixture 引用了不存在的 `sampleCurrentFieldEvidenceMaterial` helper。已改为测试内联 current field evidence fixture 后复验通过。
- 第一轮 `npm run build` 失败于 `test/App.test.ts` mission evidence bundle fixture 中 `safe_to_control`、`delivery_success`、`primary_actions_enabled` 与 `PROOF_FLAGS` spread 重复。已删除重复字段，由共享 `PROOF_FLAGS` 提供相同 literal false 值后复验通过。

## 剩余风险和证明边界

- 这是 local/mock software proof only，不证明 production cloud、route execution、delivery success、HIL、safe-to-control、real dataset export 或 O5 external evidence。
- 本轮没有触碰真实 `/cmd_vel`、`/api/base/manual`、NavigateToPose、WAVE ROVER UART、硬件/vendor 文件、ROS2 launch、O5 CDN/TLS probe 或历史 sprint 文件。
- receipt 不归档，不写云端、不读取真实外部数据集、不执行路线或送达动作；下一步若要升级为真实 export，需要 O6/O7 提供生产数据源、鉴权、安全审计和现场验收证据。
