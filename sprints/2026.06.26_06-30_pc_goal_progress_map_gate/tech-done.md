# PC Goal Progress Map Gate

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- status: done

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：新增 `canRefreshPlainGoalProgress`，地图 proof/preview 刷新
  pending 时，普通首屏 `本轮进度 / 刷新进度（只读）` 显示 `等待地图刷新` 并禁用。
- `refreshPlainGoalProgress()` 入口同步 fail-closed，避免手动进度刷新在旧地图画面上聚合更新 summary、底盘反馈、Nav2 latest 和
  delivery latest。
- `pc-tools/workstation/test/App.test.ts`：扩展地图刷新 pending 回归测试，覆盖 preview pending 和 proof pending 两种状态下，
  点击 `刷新进度` 不会发 summary、base feedback、Nav2 latest 或 delivery latest 请求。
- `docs/product/pc_tools_workstation.md`：同步 2026-06-26 06:30 行为说明。

## 验证结果

- `npm test -- -t "blocks visible-route execution while the map preview is refreshing"`：通过，1 passed / 190 skipped。
- `npm test -- -t "goal progress|map refresh|latest|feedback"`：通过，24 passed / 167 skipped。
- `npm run lint`：通过。
- `npm run build`：通过。
- `npm test`：通过，191 passed。
- `git diff --check`：通过。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：确认 `node` 监听 `*:7001`。

## 剩余风险

- 本轮只做 PC 前端 gate 和 mock/DOM 回归验证，没有触发真实上位机 summary、base feedback、Nav2 latest、delivery latest、manual、
  keyboard、delivery complete、stop 或 `/cmd_vel`；真实现场仍需在 `0.0.0.0:7001` 工作台确认。
