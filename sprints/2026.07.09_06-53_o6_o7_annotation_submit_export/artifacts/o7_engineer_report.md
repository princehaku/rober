# O7 Engineer Report - PC annotation submit/export

更新时间：2026-07-09 07:25:04 CST

## 范围

- sprint：`sprints/2026.07.09_06-53_o6_o7_annotation_submit_export/`
- owner：`full-stack-software-engineer`
- 证据边界：`software_proof_local_mock_annotation_only`
- 本报告只覆盖 O7 PC adapter/UI，不修改 O6 Python backend、`docs/interfaces/o6_cloud_archive_api.md`、`tech-done.md`、`side2side_check.md`、`final.md`。

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 新增 `trashbot.pc_tools_workstation.o7_annotation_submit_result.v1` 与 `trashbot.pc_tools_workstation.o7_annotation_dataset_export_result.v1`。
  - 结果类型固定 `proof_status=not_proven`、`submit_enabled=false`、`dataset_export_available=false`、`real_annotation_api_connected=false`、`real_dataset_export_connected=false`、`cloud_write_executed=false`、`connects_cloud_production=false`、`safe_to_control=false`、`robot_control_executed=false`。
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
  - 新增 `buildO7ConsumerAnnotationSubmit()`，PC 端调用 O6 `POST /api/o6/archive/labels`。
  - 新增 `buildO7ConsumerAnnotationExport()`，PC 端调用 O6 `GET /api/o6/archive/labels/<task_id>/export?format=jsonl`。
  - adapter 只允许本机 HTTP 回环 base URL，并拒绝 credentials、query/hash、非 HTTP、非回环、空 task id、schema mismatch、危险 true 字段、未知 submit body 字段和 token/password/secret/credential/bearer 文本。
- `pc-tools/workstation/src/server/index.ts`
  - 新增 PC 后端路由：
    - `POST /api/o7/consumer-read/tasks/<task_id>/annotations/submit`
    - `GET /api/o7/consumer-read/tasks/<task_id>/annotations/export`
  - 新 builder 直接从 `o7ConsumerReadAdapter.ts` 引入，未再修改 `server/catalog.ts`。
- `pc-tools/workstation/src/client/workstationApi.ts`
  - 新增 `postO7ConsumerAnnotationSubmit()` 与 `getO7ConsumerAnnotationExport()`。
  - 浏览器只调用 PC 后端 route，不直连 O6。
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
  - consumer-detail labeling primary path 增加 local/mock 提交标注和导出数据集操作。
  - 展示 submit receipt/export manifest/sample rows、blocker 和 false 字段；缺 detail 或 labeling MVP blocker 时按钮禁用。
  - 可见文案保持 local/mock、not_proven，不暗示真实控制、真实生产云或真实 annotation API。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 adapter submit/export 成功路径、危险输入 fail-closed、PC route JSON contract。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖 UI 缺 detail 禁用、submit/export 成功展示、浏览器请求只打 PC route、blocked 状态不触发 submit/export。
- `pc-tools/README.md`
- `docs/product/pc_tools_workstation.md`
- `docs/interfaces/o7_realtime_operator_console.md`
  - 同步记录 PC route、O6 local/mock route、result schema、fail-closed 条件和真实能力未证明边界。

## 验证结果

- `cd pc-tools/workstation && npm run test -- catalog.test.ts`
  - 结果：通过
  - 关键输出：`Test Files  1 passed (1)`；`Tests  204 passed (204)`；`Duration  43.10s`
- `cd pc-tools/workstation && npm run test -- App.test.ts`
  - 结果：通过
  - 关键输出：`Test Files  1 passed (1)`；`Tests  247 passed (247)`；`Duration  30.55s`
- `cd pc-tools/workstation && npm run build`
  - 结果：通过
  - 关键输出：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`；`✓ built in 1.77s`
  - 备注：Vite 仍提示现有 chunk 大于 500 kB，这是既有 bundle size warning，不阻塞本轮。
- `cd pc-tools/workstation && npm run lint`
  - 结果：通过
  - 关键输出：`eslint .`

## 失败定位与修复

- 第一轮 `App.test.ts` 失败：新增英文按钮文案 `Submit local/mock annotation` / `Export local/mock dataset` 触发既有只读安全断言。
  - 修复：按钮改为中文“提交 local/mock 标注”“导出 local/mock 数据集”，测试同步按中文文案查找。
- 第一轮复跑 `catalog.test.ts` 失败：恢复越界 `server/catalog.ts` 改动后，`index.ts` 仍从 `catalog.ts` 引入新 builder，导致 HTTP route 未正确返回 JSON contract。
  - 修复：保持 `server/catalog.ts` 无本轮 diff，在 `index.ts` 和 `catalog.test.ts` 中直接从 `o7ConsumerReadAdapter.ts` 引入新 builder。

## 剩余风险

- O7 只验证了 PC adapter 对 O6 local/mock API 的软件证据；不证明真实 annotation API、真实训练集导出、生产云写入、真实 rollback 或 O7 完成度提升。
- 当前 O7 export adapter 已按 sprint tech-plan 使用 `GET /api/o6/archive/labels/<task_id>/export?format=jsonl`；如果 O6 worker 最终改动路径或字段，需要 O7 adapter 跟随更新。
- 未做真实云端、4G、硬件 HIL、真实 ROS2/机器人联调；本轮所有安全字段继续固定 false。
