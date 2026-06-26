# PC 行程最小预检提示

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `行程操作` 新增 `行程前确认` 提示。
  - 未勾选安全确认时明确只需勾选现场安全确认，不再让普通用户以为还要额外预检。
  - 勾选后按路线状态提示下一步：准备图上路线、刷新地图画面，或执行图上路线且由后端复查定位和路线。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖统一安全确认前后的 `行程前确认` 文案。
  - 保持断言：勾选安全确认不会自动触发 manual、stop 或 Nav2 execute。
- `docs/product/pc_tools_workstation.md`
  - 同步记录普通首屏最小发车前置口径。

## 验证结果

- 通过：`npm test -- test/App.test.ts -t "reuses one plain safety confirmation"`
  - `1 passed | 121 skipped`
- 通过：`npm test -- test/App.test.ts`
  - `122 passed`
- 通过：`npm test`
  - `2 passed, 219 passed`
- 通过：`npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - Vite 仍提示 bundle chunk 超过 500 kB，这是既有体积提示，不影响本轮构建通过。
- 通过：`npm run lint`
  - `eslint .`
- 通过：`git diff --check`
- 通过：`npm run api`
  - `pc-tools workstation API listening on http://0.0.0.0:7001`
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - `node ... TCP *:7001 (LISTEN)`
- 通过：`curl --max-time 8 -sS http://127.0.0.1:7001/api/robot-control/summary`
  - smoke 返回 `safe_to_control=false`、`delivery_success=false`，本轮未伪造真实安全或送达完成状态。

## 剩余风险

- 本轮只改 PC 普通首屏提示与测试，不改变上车端 Nav2、底盘或真实硬件安全 gate。
- 真实小车 `safe_to_control` 仍取决于上车端现场 proof；本轮没有声明 HIL 完成。
