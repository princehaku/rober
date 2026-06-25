# PC 自动扫图按钮人工向导

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 自动扫图仍锁定时，`自动扫图准备` 主按钮从禁用的 `自动扫图（未开放）` 改为可点击的 `按步骤人工扫图`。
  - 点击该按钮只复用 `focusPlainFreeRoamNextTarget()`，把焦点带到当前扫地图下一步：安全确认、开始记录、启用键盘、松开/停止、刷新或保存。
  - 不新增自动运动入口；后端返回 `free_roam_autonomy=ready` 时仍不假装 PC 已有自动扫图控制 endpoint。
- `pc-tools/workstation/test/App.test.ts`
  - 默认首屏测试锁定：`按步骤人工扫图` 可点击、只聚焦安全确认、不新增任何 fetch 调用。
- `docs/product/pc_tools_workstation.md`
  - 记录按钮语义和安全边界。

## 验证结果

- `npm test -- --testNamePattern "renders Robot Control V1 by default"`：通过，1 passed / 168 skipped。
- `npm run lint`：通过。
- `npm test`：通过，2 files / 169 tests passed。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 成功。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：`node` 监听 `TCP *:7001`。

## 剩余风险

- 本轮没有触发真实 map start、manual、keyboard pulse、Nav2 execute、delivery complete、stop、radar start 或 `/cmd_vel`。
- 真正自动扫图仍需要上车端开放安全状态机控制入口和真车 HIL 证据；本轮只是让锁定状态下的人工扫图流程更可操作。
