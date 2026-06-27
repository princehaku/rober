# PC 行程执行 Pending 未证明口径

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - Nav2 图上路线执行请求 pending 时，普通首屏和地图统一显示“行程请求已发送，等待结果返回；返回前未证明已执行或已到达”。
  - 该状态覆盖地图终点 marker aria、路线 caption/aria、行程状态、行程进度和当前事实，避免把 PC 请求未返回窗口误读为已经执行或到达。
  - 本改动不改变执行门禁、不新增 Nav2 cancel、不新增 manual/keyboard/delivery/free-roam/stop 或 `/cmd_vel` 调用。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 visible-route execute pending 用例，锁定 marker、路线、行程卡和当前事实的未证明口径。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 2026-06-28 23:00 起的 execute pending WYSIWYG 口径。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "marks the visible route goal as request-pending while the plain trip request is pending"`
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

- 本轮没有连接真实小车，也没有发送真实 Nav2 execute、manual、keyboard、delivery、free-roam、stop 或 `/cmd_vel`；仅验证 PC 前端 pending 状态呈现和 mock API 行为。
- 工作区已有两个旧 artifact JSON 文件处于 modified，本轮不修改、不提交。
