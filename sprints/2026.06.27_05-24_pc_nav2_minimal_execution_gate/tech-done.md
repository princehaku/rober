# Tech Done

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation/src/server/robotControlSummary.ts` 将 Nav2 goal preflight 收敛为最小发车确认：只把 `confirm_navigation_preflight_required` 和危险 true 字段作为本机阻断原因。
- Nav2 preflight 仍读取 localization/nav2 proof/status 作为只读摘要，但定位 runtime、`map_to_base_link`、路径生成、路径点数不再进入 `missing_requirements`。
- 在 `pc-tools/workstation/src/server/index.ts` 保持 `/api/robot-control/nav2/goal/execute` 执行前复用 PC 本机门禁，但门禁语义改为最小确认，直接 POST 执行接口不会再因为路线 proof 不完整而被 Node 代理拒绝。
- 在 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 同步普通首屏行程文案：安全确认是最小预检；图上路线和小车位置可见仍作为所见即所得引导，不再描述为后端隐藏定位/路线预检。
- 在 `pc-tools/workstation/test/catalog.test.ts` 增加回归：路径 proof 不完整但已确认时 preflight 通过，执行接口会转发固定 `/api/nav2/goal/execute`。
- 同步更新 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `npm test -- --run test/catalog.test.ts`：112 tests passed。
- `npm test -- --run test/App.test.ts`：150 tests passed。
- `npm run lint`：通过。
- `npm run build`：通过，包含 `tsc -p tsconfig.app.json`、`vite build`、`tsc -p tsconfig.server.json`。
- `git diff --check`：通过。

## 剩余风险

- 该轮修正的是 PC Node 代理的本机门禁，不等于真实 Nav2 现场到达已通过；真实结果仍取决于上位机 `/api/nav2/goal/execute`、Nav2 lifecycle、定位、地图和底盘运动反馈。
- 前端仍要求执行“图上路线”前路线和小车位置可见，这是地图所见即所得约束；若现场定位不可见，普通首屏仍会引导重新定位，而不是直接让用户盲发。
- 摄像头无首帧、LiDAR 无 scan/raw 消息、当前轮速 L/R 复验仍未在本轮解决。
