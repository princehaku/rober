# PC 行程 Latest Pending 未证明口径

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `GET /api/robot-control/nav2/goal/execution/latest` pending 时，行程 latest 按钮显示“读取行程结果中”。
  - 行程卡主摘要、行程状态、行程进度、当前事实和地图 caption 统一显示“返回前不把旧结果当作当前结论 / 旧结果暂不作为当前结论”。
  - 本改动只收紧只读 latest pending 的所见即所得状态，不新增 Nav2 execute、manual、keyboard、delivery、free-roam、stop 或 `/cmd_vel` 调用。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 delayed latest 用例，锁定 pending 期间按钮、卡片、地图 marker、当前事实状态，并确认不发车、不送达确认。
- `docs/product/pc_tools_workstation.md`
  - 同步记录行程 latest pending 的未证明口径。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "keeps trip latest pending unproven across trip card and map"`
  - `Test Files 1 passed (1)`
  - `Tests 1 passed | 201 skipped (202)`
- 通过：`npm test -- --run test/App.test.ts -t "latest Nav2 goal result|keeps trip latest pending unproven across trip card and map"`
  - `Test Files 1 passed (1)`
  - `Tests 2 passed | 200 skipped (202)`
- 通过：`npm test`
  - `Test Files 2 passed (2)`
  - `Tests 350 passed (350)`
- 通过：`npm run lint`
  - `eslint .`
- 通过：`npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - Vite 仍提示单 chunk 超过 500 kB，这是既有体积提示，不影响本轮构建通过。
- 通过：`git diff --check`

## 剩余风险

- 本轮没有连接真实小车，也没有发送真实 Nav2 execute、manual、keyboard、delivery、free-roam、stop 或 `/cmd_vel`；仅验证 PC 前端 latest pending 状态呈现和 mock API 行为。
- 工作区已有两个旧 artifact JSON 文件处于 modified，本轮不修改、不提交。
