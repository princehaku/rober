# PC 键盘停止 Pending 所见即所得

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 键盘/屏幕方向键松开后，固定 stop 请求尚未返回时，普通首屏 `当前事实`、键盘实时状态、自由移动/扫图状态和地图 marker 统一显示“停止请求已发送，等待返回；返回前未证明已停止”。
  - 地图 marker 从 `停止发送中` 调整为 `停止请求中`，继续保留上次方向、停止原因、轮速 L/R 和地图位置未知提示。
  - 本改动只改变 PC 端呈现，不新增 manual、Nav2、free-roam、delivery 或 `/cmd_vel` 调用。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 `shows free-roam keyboard release while stop is still pending`，覆盖扫图状态、键盘实时状态、当前事实、地图 marker label/state/aria 和 stop proxy 只发一次。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 2026-06-28 22:40 起的停止 pending 呈现口径。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "shows free-roam keyboard release while stop is still pending"`
  - `Test Files 1 passed (1)`
  - `Tests 1 passed | 199 skipped (200)`
- 通过：`npm test`
  - `Test Files 2 passed (2)`
  - `Tests 348 passed (348)`
- 通过：`npm run lint`
  - `eslint .`
- 通过：`npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - Vite 仍提示单 chunk 超过 500 kB，这是既有体积提示，不影响本轮构建通过。
- 通过：`git diff --check`

## 剩余风险

- 本轮没有连接真实小车，也没有发送真实 stop/manual/Nav2/free-roam/delivery 命令；仅验证 PC 前端 pending 状态呈现和 mock API 行为。
- 工作区已有两个旧 artifact JSON 文件处于 modified，本轮不修改、不提交。
