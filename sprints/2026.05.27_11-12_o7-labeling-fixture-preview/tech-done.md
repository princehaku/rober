# O7 Labeling Fixture Preview Tech Done

## sprint_type

micro

## 实际改动

- 新增 `pc-tools/workstation/src/server/o7LabelingPreview.ts`，实现 `GET /api/o7/labeling-preview?fixtureJson=<local-json>` 背后的只读 adapter：仅读取用户显式指定的本地 JSON fixture，支持 `trashbot.o7.labeling_fixture.v1`，输出 `trashbot.o7.labeling_preview.v1` 安全摘要。
- 扩展 `pc-tools/workstation/src/shared/contracts.ts`，新增 labeling preview 共享契约，并把新 API 写入 `API_ROUTES` 与 not-proven 边界。
- 更新 `pc-tools/workstation/src/server/catalog.ts` 和 `pc-tools/workstation/src/server/index.ts`，挂载 labeling preview builder 与 Express 路由。
- 更新 `pc-tools/workstation/test/catalog.test.ts`，覆盖安全 fixture 摘要，以及缺文件、坏 JSON、unsupported schema、unsafe copy、success claim、control claim、submit claim、rollback claim、dataset export claim 的 fail-closed 行为。
- 更新 `docs/product/pc_tools_workstation.md` 和 `docs/interfaces/o7_realtime_operator_console.md`，同步 O7-KR4 PC-only fixture preview 的 API、schema、输出摘要、禁止动作和剩余边界。

## 用户旅程变化和触点收益

- PC operator 后续可以用本地 labeling fixture 预览待标注队列、最多 3 个样本、label schema、draft label 槽位和 dataset export 缺口。
- 该入口只提供摘要和缺口说明，不提供 submit、rollback、export、恢复、控制或云端成功文案，避免把本地 fixture 误读成真实 O6 annotation API。

## 接口影响

- 新增只读 API：`GET /api/o7/labeling-preview?fixtureJson=<local-json>`。
- 输入 schema：`trashbot.o7.labeling_fixture.v1`。
- 输出 schema：`trashbot.o7.labeling_preview.v1`。
- 固定关闭：`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`pc_only=true`、`real_annotation_api_connected=false`、`submit_enabled=false`、`rollback_enabled=false`、`dataset_export_available=false`、`robot_control_executed=false`。
- 禁止连接云端、ROS2 或硬件；禁止写标注文件；禁止把 fixture 内 submit/rollback/export availability claim 当作可用能力。

## 验证结果

- `cd pc-tools/workstation && npm run build`
  - 通过。关键输出：`✓ 29 modules transformed.`、`✓ built in 1.95s`。
- `cd pc-tools/workstation && npm run test`
  - 首次失败：`O7 labeling preview summarizes...` 中测试期望 item evidence refs 只包含 3 个，但实现按 evidence ref 独立限量输出 4 个安全引用。
  - 修正测试期望后通过。关键输出：`Test Files  2 passed (2)`、`Tests  21 passed (21)`。
- `cd pc-tools/workstation && npm run lint`
  - 通过，ESLint 无输出错误。

## 剩余风险

- 本轮只证明 PC-only 本地 fixture preview adapter 可用，不证明 O6 annotation API、真实 review queue、真实媒体可访问、真实 label schema API、真实 draft autosave、真实 submit/rollback、真实 dataset export 或真实 delivery success。
- 本轮未改 UI，PC 页面还没有直接展示该新 API 的专用 panel；后续需要在 O7-KR4 UI 面板接入前继续保持 submit/rollback/export 按钮禁用。
- 未修改 `OKR.md`，未提升 O7 百分比。
