# PC Nav2 Preflight Usability

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `检查行程` 改为不发车预检动作：勾选现场安全确认后，即使雷达未运行或待刷新，也允许调用固定 `nav2/goal/preflight` 查看路线 gate。
  - `执行行程` 继续被雷达未运行/待刷新状态挡住，仍必须走后端固定 execute gate。
- `pc-tools/workstation/test/App.test.ts`
  - 新增雷达停止时可执行行程预检但不能执行行程的回归测试。
  - 更新旧断言，明确当前阻塞对象是行程执行，不是只读/预检。
- `docs/product/pc_tools_workstation.md`
  - 同步普通首屏 Nav2 行程预检最新口径和安全边界。

## 验证结果

- `npm test`
  - 通过：2 个 test files，158 个 tests 全部通过。
- `npm run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
- 只读 7001 smoke：
  - `GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787`
  - 返回 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`navigate_goal_enabled=false`、`robot_control_executed=false`。
  - 当前真实读回仍显示 `lidar_state=stopped`、`path_generated=false`、`path_generation_succeeded=false`。

## 剩余风险

- 本轮只改善 PC 普通首屏的 Nav2 预检可用性，没有执行真实 NavigateToPose。
- 完整 Nav2 路线执行、wheel raw L/R 非零和 delivery success 仍需要现场显式确认后再跑真实运动链路。
- 7001 smoke 只读验证不等于 HIL 或真实路线完成证明。
