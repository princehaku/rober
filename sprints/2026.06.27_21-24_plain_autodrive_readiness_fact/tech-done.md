# PC 当前自动驾驶准备状态事实条

## Sprint 类型

sprint_type: micro

## 实际改动

- 修改 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：
  - 普通首屏 `当前事实` 新增当前自动驾驶准备状态行。
  - 将“当前图上路线/规划服务/控制服务/小车地图坐标缺口”和“旧路线 action 成功但 wheel raw L/R 未闭环”分开展示。
  - 当前自动驾驶未准备好时，首屏提示先准备图上路线或重新定位，并明确相机/雷达不挡底盘试动或键盘手控。
- 修改 `pc-tools/workstation/test/App.test.ts`：
  - 增加 no-motion 行程准备失败场景下的首屏事实条断言。
  - 锁定普通首屏不暴露 `planner_server_not_active`、`root_causes`、`Nav2` 或 `/cmd_vel`。
- 更新 `docs/product/pc_tools_workstation.md`：
  - 同步记录普通首屏自动驾驶当前准备状态和旧执行证据分层展示的 UX 合同。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- App.test.ts --testNamePattern "planner blocker|current facts|automatic|自动驾驶|plain trip"`（10 tests）
- 通过：`cd pc-tools/workstation && npm test -- App.test.ts --testNamePattern "renders Robot Control V1|planner blocker|current facts|自动驾驶"`（4 tests）
- 通过：`cd pc-tools/workstation && npm test`（313 tests）
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`
  - 保留既有 Vite chunk size warning：`Some chunks are larger than 500 kB after minification`。
- 通过：`git diff --check`

## 剩余风险

- 本轮没有发送真实 Nav2 execute、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- live 仍需要现场安全确认后重跑图上路线，才能证明完整 Nav2 路线执行和同窗口 wheel raw L/R 非零。
