# PC 首屏显示 Nav2 行程复验事实

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏行程卡片新增 `行程复验事实` 行，直接展示 summary 中的路线执行预检、准备状态和 wheel raw L/R 复验下一步。
- `pc-tools/workstation/test/App.test.ts`：补充首屏 DOM 断言，锁定普通用户能看到“执行只需勾选行程前安全确认”。
- `docs/product/pc_tools_workstation.md`：同步记录该首屏字段的只读边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "Robot Control V1"`，结果 `1 passed | 214 skipped`。
- 通过：`npm --prefix pc-tools/workstation run build`，结果 `tsc` 与 `vite build` 成功；Vite 仍提示既有 chunk 超过 500 kB。
- 通过：`npm --prefix pc-tools/workstation test`，结果 `2 passed`、`375 passed`。
- 通过：重启 PC API 到 `0.0.0.0:7001` 后只读请求 `GET /api/robot-control/summary`，确认 `route_execution_precheck_plain`、`route_execution_readiness_plain`、`goal_execution_wheel_raw_lr_status_plain` 和 `goal_execution_wheel_raw_lr_next_action_plain` live 返回；普通首屏 DOM 由测试锁定 `plain-trip-route-execution-readback` 会显示行程复验事实。

## 剩余风险

- 当前改动只把已有 Nav2 readback 展示到普通首屏；真实完整路线复验仍需要现场勾选安全确认后由用户显式点击执行。
