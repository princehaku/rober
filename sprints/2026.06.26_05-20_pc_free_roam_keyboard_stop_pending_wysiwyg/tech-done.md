# PC 扫图键盘停止 pending WYSIWYG

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 扫地式建图 `下一步` 在键盘/屏幕方向键松开且 stop 请求 pending 时显示 `下一步：等待停止完成`。
  - `扫图状态` 在 `released:*` 状态显示 `已松开，正在发送停止；完成前不要继续移动`。
  - 地图 marker 在 stop pending 时显示 `停止发送中：<方向>`，并保留上次方向、停止原因、轮速 L/R 和非零口径。
- `pc-tools/workstation/test/App.test.ts`
  - 新增延迟 stop 的扫图键盘用例，验证 stop pending 中间态不会回落成“键盘已启用/可继续按键”，并确认不调用 Nav2、delivery 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录键盘 stop pending 的首屏与地图 WYSIWYG 行为。

## 验证结果

- 通过：`cd pc-tools/workstation && npx vitest run test/App.test.ts -t "shows free-roam keyboard release while stop is still pending"`
  - 1 个 test file passed，1 个测试通过，92 个跳过。
- 通过：`cd pc-tools/workstation && npm run lint`
  - `eslint .` 完成。
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- 通过：`cd pc-tools/workstation && npm test`
  - 2 个 test files passed，187 个测试通过。
- 通过：`git diff --check`
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - `node ... TCP *:7001 (LISTEN)`

## 剩余风险

- 该轮只覆盖 PC mock 的 stop pending 中间态，没有触发真实底盘运动或真实 stop。
- 真实现场仍需观察 stop pending 时间较长时，operator 是否能清楚理解“完成前不要继续移动”。
