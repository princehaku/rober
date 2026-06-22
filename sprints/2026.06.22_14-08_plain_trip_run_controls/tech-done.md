# Plain Trip Run Controls

sprint_type: micro

## 实际改动

- PC 普通首屏 `移动/导航` 卡片新增“行程操作”面板。
- 面板提供 `检查行程`、`执行行程`、`读取行程结果`，默认必须先勾选“人在旁边、周围安全、停止手段就绪”。
- 普通入口复用既有固定代理：`/api/robot-control/nav2/goal/preflight` 和 `/api/robot-control/nav2/goal/execute`，不新增后端绕行。
- 执行目标仍沿用当前受限默认参数 `map, x=0.8, y=0, yaw=0`，不开放地图点击、任意目标或任意 endpoint。
- 普通首屏文案只使用“行程”，不泄露 `Nav2/proof/API`；执行结果只更新行程状态，不自动确认 delivery success。
- 更新 Vue 测试，覆盖默认禁用、勾选后预检/执行按钮可用、请求 body 带确认位、不会调用 base manual 或 `/cmd_vel`。

## 验证结果

- 通过：`npm test`，Vitest `2 passed (2)`，`114 passed (114)`。
- 通过：`npm run lint`，ESLint 无报错。
- 通过：`npm run build`，`tsc` 与 Vite production build 通过。
- 通过：`git diff --check`，无 whitespace error。

## 剩余风险

- 本轮只把受限行程执行入口搬到普通首屏；未触发真实 Nav2 行程。
- 完整 Nav2 路线执行仍需要现场安全确认后执行，并由上位机返回真实 `goal_succeeded`。
- wheel raw L/R 非零和 delivery success 仍需要真实执行证据。
