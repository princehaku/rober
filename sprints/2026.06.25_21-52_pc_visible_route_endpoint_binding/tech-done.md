# PC 图上路线终点执行绑定

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `latestNavPathOverlay()` 输出当前可见路线终点的 map-frame 坐标，作为普通用户执行入口的唯一 `goal_x/goal_y` 来源。
  - `runPlainTripExecution()` 在安全确认和路线可见 gate 通过后，把图上终点传给 Nav2 execute proxy；高级 Nav2 表单仍使用手动输入的目标坐标。
  - 终点朝向仍沿用显式 `goal_yaw` 输入，因为当前路线 preview 只有平面点，不额外推断隐藏朝向。
- `pc-tools/workstation/test/App.test.ts`
  - 更新“执行图上路线后同步 latest/delivery”的回归用例：图上终点设为 `0.6,0.2`，高级目标输入故意设为 `0.2,-0.2`，断言普通按钮 POST 的 `goal_x/goal_y` 等于图上终点。
- `docs/product/pc_tools_workstation.md`
  - 记录普通首屏 `执行图上路线` 请求体与地图可见路线终点绑定，以及不新增自动控制的安全边界。

## 验证结果

- `npm test -- --testNamePattern "syncs latest readbacks"`：通过，1 passed / 168 skipped。
- `npm test -- --testNamePattern "visible-route trip execution|syncs latest readbacks|draws no-motion route"`：通过，2 passed / 167 skipped。
- `npm run lint`：通过。
- `npm test`：通过，2 files / 169 tests passed。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 成功。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：`node` 监听 `TCP *:7001`。

## 剩余风险

- 本轮尚未触发真实 Nav2 execute、manual、keyboard pulse、delivery complete、stop、map start、radar start 或 `/cmd_vel`。
- 完整 Nav2 路线执行仍需要现场 operator 显式勾选安全确认并点击执行；上位机 execute proxy 仍会做后端复查。
