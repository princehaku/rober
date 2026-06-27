# PC 重新定位 Pending 地图位置未证明口径

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `POST /api/robot-control/localize/reset` pending 时，普通地图不再继续显示上一轮 map-frame 小车 marker。
  - 地图改显示 `定位中` 占位，并在 aria 中声明“返回前不把旧位置当作当前定位”。
  - 雷达贴图也随之不再锚到旧小车坐标，避免旧机器人位置看起来像当前定位。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展定位 pending 用例：先证明旧 robot marker 可见，再触发 delayed reset，断言旧 marker 隐藏、地图显示 `定位中`，并确认不发车、不执行 Nav2、不送达确认。
- `docs/product/pc_tools_workstation.md`
  - 同步记录重新定位 pending 的地图位置未证明口径。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "shows localization reset pending in current map facts"`
  - `Test Files 1 passed (1)`
  - `Tests 1 passed | 201 skipped (202)`
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

- 本轮没有连接真实小车，也没有发送真实 localization reset、Nav2、manual、keyboard、delivery、free-roam、stop 或 `/cmd_vel`；仅验证 PC 前端 pending 状态呈现和 mock API 行为。
- 工作区已有两个旧 artifact JSON 文件处于 modified，本轮不修改、不提交。
