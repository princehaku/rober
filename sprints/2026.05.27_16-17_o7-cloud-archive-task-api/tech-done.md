# O7 Cloud Archive Task API Micro Sprint

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation` 增加 PC-only read-only API：`GET /api/o7/cloud-archive/tasks?archiveJson=<local-json>`。
- 新增 `trashbot.o7.cloud_archive_tasks.v1` 契约和 builder，只读取用户显式指定的本地 `trashbot.o7.cloud_archive_fixture.v1` JSON。
- API 返回 task list、selected/latest task summary，以及 trajectory/event/label/voice/command safe summaries。
- 固定 false 字段保持关闭：`real_cloud_archive_connected=false`、`real_realtime_api_connected=false`、`real_annotation_api_connected=false`、`real_voice_api_connected=false`、`real_command_api_connected=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`pc_only=true`、`robot_control_executed=false`。
- `O7 Previews` tab 增加 `Cloud Archive Tasks` 只读区块。页面默认不读取本地路径，点击 `Load archive tasks` 后才调用 GET query。
- 补充 API builder、HTTP endpoint 和 UI 测试，覆盖不自动加载、点击后 query、任务摘要展示、fixed false fields、危险动作入口不出现。
- 同步更新 `docs/product/pc_tools_workstation.md`、`docs/interfaces/o7_realtime_operator_console.md`，并新增 `docs/interfaces/o7_cloud_archive_task_api.md`。

## 验证结果

已执行：

```bash
cd pc-tools/workstation && npm run build
> rober-pc-tools-workstation@0.1.0 build
> tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json
✓ 31 modules transformed.
✓ built in 2.02s

cd pc-tools/workstation && npm run test
> rober-pc-tools-workstation@0.1.0 test
> vitest run
Test Files  2 passed (2)
Tests  31 passed (31)

cd pc-tools/workstation && npm run lint
> rober-pc-tools-workstation@0.1.0 lint
> eslint .

git diff --check -- pc-tools/workstation docs/product/pc_tools_workstation.md docs/interfaces/o7_realtime_operator_console.md docs/interfaces/o7_cloud_archive_task_api.md sprints/2026.05.27_16-17_o7-cloud-archive-task-api
# no output, exit 0
```

首轮失败和修复：

- 首轮 `npm run build` 失败：`src/server/index.ts` 中原有 `const app = express()` 与新增导出的 `app` 重名，TypeScript 报 `Cannot redeclare block-scoped variable 'app'`。
- 修复：删除旧顶层 `const app`，保留 `createWorkstationApp()` 和导出的 `app`，并仅在直接运行 `index.ts` 时监听端口。
- 修复后重新执行 build/test/lint/diff-check，均通过。

## 剩余风险

- 本轮只证明 Node/Vue software proof，未连接 O6 真实云归档、production DB、realtime API、annotation API、voice API、command API、ROS2、硬件或真实机器人。
- Archive fixture schema 是 O7 统一数据源雏形，后续接真实 O6/O7 API 时仍需补鉴权、分页、任务详情、媒体引用、审计和错误语义。
- 本轮不更新 `OKR.md`，不声明真实 O7 完成度提升。

## O7 推动说明

这不是单纯 mock：API 和 UI 建立了 KR3/KR4/KR5/KR6 共享任务数据入口的 fail-closed 契约。历史路线回放可读取 trajectory/events，标注可读取 labels，ASR/TTS 可读取 voice，手控/寻路可读取 command envelope 摘要；所有真实连接和控制字段仍固定 false。
