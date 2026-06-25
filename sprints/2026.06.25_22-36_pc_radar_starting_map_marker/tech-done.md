# PC radar starting map marker

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 增加 radar lifecycle pending action，只用于显示当前 `start/stop` 请求飞行中的普通状态。
- 普通首屏点击 `启动雷达` 后，在请求未返回前立即显示 `雷达启动中`；地图 marker、扫描范围占位、雷达点口径和坐标口径同步进入启动中语义。
- 在 `pc-tools/workstation/test/App.test.ts` 增加延迟 radar start POST 的单测，覆盖请求飞行中地图 marker 与不误触 manual/Nav2/delivery 的边界。
- 更新 `docs/product/pc_tools_workstation.md`，记录启动中 marker 不等于真实雷达已运行。

## 验证结果

- 通过：`npm test -- --testNamePattern "shows a map radar-starting marker while the plain radar start request is in flight"`，1 passed / 170 skipped。
- 通过：`npm run lint`。
- 通过：`npm test`，171 passed。
- 通过：`npm run build`。
- 通过：`git diff --check`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，确认 `node` 监听 `TCP *:7001`。
- 测试副作用：`npm test` 刷新两个历史 smoke artifact 的 `checked_at`；已只还原这两个时间戳，未纳入本轮改动。

## 剩余风险

- 本轮只验证 PC 前端请求飞行中的状态和 mock API，不代表真实雷达已经运行；真实运行仍以 refresh 后的 summary/proof 为准。
- 没有触发真实底盘运动，也没有做上车 HIL。
