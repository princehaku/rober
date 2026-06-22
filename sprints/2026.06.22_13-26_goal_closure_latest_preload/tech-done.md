# Goal Closure Latest Preload

sprint_type: micro

## 实际改动

- PC 页面初载读取 Robot Control summary 后，自动预载 `GET /api/robot-control/nav2/goal/execution/latest` 和 `GET /api/robot-control/delivery/latest`。
- 目标是让 `目标收口进度` 面板进入页面后就能显示最近 Nav2 goal 和 delivery gate 状态，不需要现场人员先手点两个高级按钮。
- 该预载只走固定 GET 代理，不调用 Nav2 execute、delivery complete、base manual、`/cmd_vel` 或任何运动/确认接口。
- 补充 Vue 测试，锁住初载会请求两个 latest GET，同时不会请求 Nav2 execute 或 delivery complete。
- 更新 `docs/product/pc_tools_workstation.md` 记录预载边界。

## 验证结果

- 通过：`npm test`，Vitest `2 passed (2)`，`112 passed (112)`。
- 通过：`npm run lint`，ESLint 无报错。
- 通过：`npm run build`，`tsc` 与 Vite production build 通过。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只改善目标状态可见性，不执行真实 first-jog、键盘手控、Nav2 目标或送达确认。
- 真实完成仍依赖现场产生 wheel raw L/R 非零、确认 delivery success，并由上位机 gate 接受。
