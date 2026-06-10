# PC Robot Control Simple UI Regression Fix

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 保留标题 `Rober 小车控制台`。
  - 普通首屏固定为 5 张卡片：`小车连接`、`实时画面`、`雷达`、`地图`、`移动/导航`。
  - 首屏普通动作收口为：`连接/刷新`、`打开画面`、`关闭画面`、`刷新雷达`、`刷新地图`、`地图列表`、`检查路径`、`停止`。
  - 从首屏移除工程摘要：scan/tf、map/evidence、自动导航未开放、最近证据、非 stop 点动状态、proof/readback/raw/source/status key 等。
  - 保留默认关闭的 `高级诊断`，高级诊断内继续承载保存地图、开始建图（高级）、雷达启动/停止（高级）、现场点动设置和 fail-closed 合同字段。
- `pc-tools/workstation/src/styles.css`
  - 将首屏路径状态样式从 `路径未证明` 更新为普通用户更易懂的 `未检查`。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 Robot Control DOM 测试，固定首屏 5 卡片、普通动作白名单和工程/危险词禁词清单。
  - 保留高级诊断断言，确认高级项默认不展开、展开后仍存在。
- `docs/product/pc_tools_workstation.md`
  - 同步 PC Robot Control 普通首屏口径：首屏只放普通动作，高级控件默认收进 `高级诊断`。
- `pc-tools/README.md`
  - 同步 workstation Robot Control 简易首屏说明。
- `sprints/2026.06.11_02-55_pc_simple_ui_regression_fix/artifacts/ui-smoke.md`
  - 保存本地 Browser UI smoke 结果。

## 验证结果

- `cd pc-tools/workstation && npm run test`
  - 通过：`Test Files 2 passed (2)`，`Tests 78 passed (78)`。
- `cd pc-tools/workstation && npm run build`
  - 通过：TypeScript app/server build 与 Vite production build 完成。
- `cd pc-tools/workstation && npm run lint`
  - 通过：`eslint .` 无报错。
- 本地 UI smoke
  - 启动：`cd pc-tools/workstation && npm run dev -- --port 5173`
  - 通过：首屏 5 张卡片，普通动作全在，禁词命中为空，`高级诊断` 默认关闭；展开后可见高级控件。
  - 结果见 `artifacts/ui-smoke.md`。
- `git diff --check`
  - 通过：无 whitespace error。

## 剩余风险

- 本轮只修 PC 普通用户首屏体验，没有新增上车能力，也没有改后端代理、onboard、硬件配置或 `/dev/ttyS5`。
- Vite dev server smoke 只验证 UI 可见结构；因为 dev server 不提供 `/api/*`，页面顶部出现 API 500 提示，不影响本轮首屏结构验收。后端代理安全边界由既有测试和合同覆盖。
