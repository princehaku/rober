# PC Latest Readback Map Gate

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- status: done

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：新增 `canLoadNavGoalExecutionLatest` 和
  `canLoadDeliveryLatest`，地图 proof/preview 刷新 pending 时，普通首屏 `读取行程结果（只读）` 与
  `刷新送达状态（只读）` 都显示 `等待地图刷新` 并禁用。
- `loadNavGoalExecutionLatest()` 与 `loadDeliveryLatest()` 入口同步 fail-closed，避免 latest readback 在旧地图画面上提前改写
  到达/送达 marker。
- 高级诊断里的 `读取最近 Nav2 结果（高级）` 和 `读取送达缺口（高级）` 复用同一 gate。
- 初始化/内部同步通过 `allowDuringMapRefresh` 显式保留，不影响页面首次恢复历史行程/送达 readback，也不影响行程执行后在地图画面刷新结束再自动读取 latest。
- `pc-tools/workstation/test/App.test.ts`：扩展送达确认 map pending 回归测试，覆盖地图刷新中点击行程 latest / delivery latest
  不会发对应 GET 请求。
- `docs/product/pc_tools_workstation.md`：同步 2026-06-26 06:25 行为说明。

## 验证结果

- `npm test -- -t "shows delivery confirmation pending on the map while final completion is in flight"`：通过，1 passed / 190 skipped。
- `npm test -- -t "trip|delivery|map refresh|latest"`：通过，46 passed / 145 skipped。
- `npm run lint`：通过。
- `npm run build`：通过。
- `npm test`：通过，191 passed。
- `git diff --check`：通过。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：确认 `node` 监听 `*:7001`。

## 剩余风险

- 本轮只做 PC 前端 gate 和 mock/DOM 回归验证，没有触发真实上位机 Nav2 latest、delivery latest、manual、keyboard、delivery complete、
  stop 或 `/cmd_vel`；真实现场仍需在 `0.0.0.0:7001` 工作台确认。
