# O7 fixture preview UI

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation/src/client/workstationApi.ts` 集中封装五个 O7 PC-only fixture preview API，并保留空路径由后端返回 `not_provided` 的 fail-closed 行为。
- 在 `pc-tools/workstation/src/components/WorkstationTabs.vue` 和 `pc-tools/workstation/src/App.vue` 新增独立 `O7 Previews` tab，与 `O7 Console` 分开。
- 新增 `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`，提供五个本地 fixture JSON 路径输入和五个只读 `Load ... preview` 按钮；页面展示 schema、preview status、input status/failure reason、核心 false 字段、安全摘要、blocked reasons 和 not_proven。
- 更新 `pc-tools/workstation/test/App.test.ts`，覆盖 O7 Previews 不自动读取本地路径、通过 client query 调用五个 preview API、展示 fail-closed false 字段，并确认无 send/run/submit/control/play/export 等动作文案。
- 更新 `docs/product/pc_tools_workstation.md` 和 `docs/interfaces/o7_realtime_operator_console.md`，同步 O7 Previews UI 边界、接口入口和 not_proven 说明。

## 验证结果

- `cd pc-tools/workstation && npm run build`：通过。最终重跑关键输出：`✓ 31 modules transformed.`、`✓ built in 1.97s`。
- `cd pc-tools/workstation && npm run test`：通过。关键输出：`Test Files  2 passed (2)`、`Tests  28 passed (28)`。
- `cd pc-tools/workstation && npm run lint`：通过，最终无输出 warning/error。
- `git diff --check -- pc-tools docs/product/pc_tools_workstation.md docs/interfaces/o7_realtime_operator_console.md sprints/2026.05.27_15-16_o7-fixture-preview-ui`：通过，无 whitespace error。

第一轮 build 曾因测试里 `findAll("input")` 返回值可能为 undefined 触发 TypeScript 严格检查失败，已补输入数量断言和非空断言后重新验证通过。第一轮 lint 曾提示 Vue `input` 不应自闭合，已手动改为普通 void element 写法后重新验证通过。

## 剩余风险

- 当前实现只接入 PC 本地 fixture preview API，不证明真实 realtime API、ROS2 `/tf`、云归档、annotation API、voice API、safe command API、robot ACK、HIL/硬件安全或 delivery success。
- 本轮不修改 `OKR.md`，不提升 O7 百分比。
