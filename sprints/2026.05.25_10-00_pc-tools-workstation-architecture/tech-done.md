# PC Tools Workstation Architecture Micro Sprint

## sprint_type

micro

## 实际改动

- 前端模块化：
  - `pc-tools/workstation/src/App.vue` 收敛为全局状态、刷新流程、错误处理和页面组合。
  - 新增 `pc-tools/workstation/src/components/ProofFlagStrip.vue`、`WorkstationTabs.vue`、`RouteDebugPanel.vue`、`EvidenceToolsPanel.vue`、`TrainingLabelingPanel.vue`、`ProofBoundaryPanel.vue`。
  - 新增 `pc-tools/workstation/src/client/workstationApi.ts`，集中维护 `/api/*` fetch、route debug query 参数拼接和全量 snapshot 加载。
- 后端分层：
  - 新增 `pc-tools/workstation/src/server/paths.ts` 集中维护仓库路径和安全展示路径。
  - 新增 `pc-tools/workstation/src/server/evidenceAssets.ts` 管理 Evidence JSON fixture 索引。
  - 新增 `pc-tools/workstation/src/server/proofBoundary.ts` 管理 health、Training/Labeling 占位和 Proof Boundary 契约。
  - `pc-tools/workstation/src/server/catalog.ts` 保留 Route Debug summary 聚合，并 re-export 其他响应构建器以保持原导入路径兼容。
- 测试更新：
  - `pc-tools/workstation/test/App.test.ts` 新增 route 表单 query 契约测试，确认组件输入通过统一 API client 进入 `/api/route/debug-summary?...`。
  - 原有 route JSON loader、fixture index、proof flags、UI 不暴露 `/cmd_vel`/串口、无 Python gate 语义覆盖继续保留。
- 文档同步：
  - `docs/product/pc_tools_workstation.md` 更新为当前 Node/Vue 工作站架构、前端分层、后端分层和 fail-closed 产品边界。

## 验证结果

```powershell
cd pc-tools/workstation && npm run build
```

结果：通过。

日志片段：

```text
> rober-pc-tools-workstation@0.1.0 build
> tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json
✓ 25 modules transformed.
✓ built in 412ms
```

```powershell
cd pc-tools/workstation && npm run test
```

结果：通过。

日志片段：

```text
Test Files  2 passed (2)
Tests  9 passed (9)
Duration  2.45s
```

```powershell
cd pc-tools/workstation && npm run lint
```

结果：通过。

日志片段：

```text
> rober-pc-tools-workstation@0.1.0 lint
> eslint .
```

```powershell
Get-ChildItem -Path pc-tools -Recurse -File -Include *.py | Where-Object { $_.FullName -notmatch '\\workstation\\node_modules\\' }
```

结果：通过，输出为空。

## 剩余风险

- 本轮验证范围是 PC 工作站 Node/Vue 软件链路；不包含真实 ROS2 runtime、真实硬件、真实串口、真实手机、真实云链路或 HIL。
- Route Debug 仍是本地 JSON safe summary，不证明真实 Nav2/fixed-route runtime pass 或 delivery success。
- 构建产物由 `npm run build` 刷新，后续若仓库策略不提交 `dist/`，需要在提交前按项目规范决定是否保留。
