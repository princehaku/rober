# 2026.06.26 07:00 PC free-roam auto stop queue

- sprint_type: micro
- status: done
- owner: User Touchpoint Full-Stack Engineer

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `freeRoamAutonomyStopQueuedAfterStart`，自动扫图 start 请求 pending 时允许红色 `停止自动扫图` 排队。
  - 新增 `canStopFreeRoamAutonomy` 和 `plainFreeRoamAutoStopButtonLabel`，stop 请求 pending 才禁用，start pending 时保持可点。
  - start 请求返回后如已有排队 stop，立即调用固定 `/api/robot-control/free-roam/autonomy/stop`，并跳过 start 后监看刷新链路。
  - 地图扫图 marker、扫图状态和下一步文案同步显示 `自动扫图停止已排队`。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 start pending 下点击 stop 的测试，覆盖按钮可点、排队文案、start 返回后自动发送 stop，且不调用 manual、Nav2 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录自动扫图 stop 排队行为和安全边界。

## 验证结果

- `npm test -- -t "queues free-roam autonomy stop while the start request is still pending"`：通过，1 passed / 191 skipped。
- `npm run lint`：通过。
- `npm run build`：通过。
- `npm test`：通过，2 files / 192 tests passed。
- `git diff --check`：通过。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN || true`：确认 PC Node 仍监听 `*:7001`。

## 剩余风险

- 本轮只验证 PC 前端 mock 行为，不触发真实小车运动，不覆盖真车 HIL、Nav2 实车执行或 WAVE ROVER 串口反馈。
- 未修改 Clash、系统代理或端口策略；本轮仅确认现有 Node 服务仍在 `0.0.0.0:7001` 等效监听。
