# 2026-06-28 20:45 PC managed Nav2 runtime execute WYSIWYG

sprint_type: micro

## 实际改动

- 修改 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：当 summary 已证明 `nav2_goal_ready=true` 且图上路线点数已读到时，普通首屏不再因为当前 Nav2 lifecycle stopped 或 controller inactive 把主按钮锁成“先启动自动驾驶服务”。
- 同一 live 形态下，`当前事实` / `自动驾驶诊断` 改为说明“路线已准备，点击执行图上路线会自动启动 runtime”，并继续提示本轮成败要看执行返回和 wheel raw L/R 非零。
- 修改 `pc-tools/workstation/test/App.test.ts`：新增 managed runtime 前端回归，覆盖 ready route + lifecycle stopped + controller inactive 时按钮可显示 `执行图上路线`，且未点击时不调用 `/api/nav2/start`、`/api/nav2/goal/execute`、manual 或 `/cmd_vel`。
- 更新 `docs/product/pc_tools_workstation.md`：记录 managed runtime 例外和控制边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- --run test/App.test.ts -t "managed Nav2 runtime|no-motion Nav2 start action|summary route on the initial map preview"`，结果 `3 tests passed`。
- 通过：`npm --prefix pc-tools/workstation test -- --run test/App.test.ts`，结果 `211 tests passed`。
- 通过：`npm --prefix pc-tools/workstation test -- --run`，结果 `364 tests passed`。
- 通过：`npm --prefix pc-tools/workstation run build`，TypeScript 与 Vite build 成功；仍有既有 chunk size warning。
- 通过：重启 PC Node 到 `0.0.0.0:7001` 后，只读请求 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `nav2_goal_ready=true`、`nav2_goal_blockers=[]`、`nav2_status=path_ready_with_service_blockers`、`nav2_stack_lifecycle_state=stopped`、`controller_server_active=false`、`path_generated=true`、`path_point_count=18`，且 `robot_control_executed=false`。这证明 live 仍是 managed runtime execute 形态，但本轮未发送 execute。
- 通过：`GET /` 返回 HTTP 200，7001 继续监听 `*:7001`。

## 剩余风险

- 本轮没有发送真实 Nav2 execute、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`；完整路线执行、wheel raw L/R 非零和 delivery success 仍需要现场安全确认后实车复验。
- 当前 live summary 仍显示上一轮路线成功但 wheel raw L/R=0/0；本轮只修 PC 首屏不再错误要求单独启动 lifecycle，不证明底盘已经动起来。
