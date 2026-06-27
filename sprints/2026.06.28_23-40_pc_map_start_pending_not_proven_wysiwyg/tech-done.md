# PC 地图记录启动 Pending 未证明口径

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `POST /api/robot-control/map/start` pending 时，地图 lifecycle 摘要、自由移动/建图卡片、扫图状态和地图 marker aria 统一显示“返回前未证明记录已启动”。
  - 该状态继续明确“不发车/不要移动小车”，只有 map start 返回并刷新扫图画面后才进入后续自由移动或自动扫图动作。
  - 本改动只改变 PC 前端 WYSIWYG 呈现，不新增 map、manual、keyboard、Nav2、delivery、free-roam、stop 或 `/cmd_vel` 调用。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 ready sensors auto mapping start 用例，锁定 map/start pending 的 marker、hint 和扫图状态。
- `docs/product/pc_tools_workstation.md`
  - 同步记录地图记录启动 pending 的未证明口径。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "starts map recording before auto sweep when camera and radar are ready"`
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

- 本轮没有连接真实小车，也没有发送真实 map start、free-roam、manual、keyboard、Nav2、delivery、stop 或 `/cmd_vel`；仅验证 PC 前端 pending 状态呈现和 mock API 行为。
- 工作区已有两个旧 artifact JSON 文件处于 modified，本轮不修改、不提交。
