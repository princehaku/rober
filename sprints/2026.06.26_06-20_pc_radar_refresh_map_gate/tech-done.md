# PC Radar Refresh Map Gate

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- status: done

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：新增 `canRefreshRadarProof` 和
  `radarProofRefreshButtonLabel`。地图 proof/preview 任一刷新 pending 时，普通首屏 `刷新雷达` 显示 `等待地图刷新`
  并禁用。
- `refreshRadarProof()` 入口同步 fail-closed，防止绕过按钮后在旧地图底图或旧坐标状态上刷新雷达 scan proof。
- `pc-tools/workstation/test/App.test.ts`：扩展雷达启动自动刷新测试，覆盖地图刷新 pending 时 `刷新雷达` 禁用且不会发送
  `/api/robot-control/radar/scan-proof/refresh`。
- `docs/product/pc_tools_workstation.md`：同步 2026-06-26 06:20 行为说明。

## 验证结果

- `npm test -- -t "auto-refreshes radar proof after plain radar start reports ok"`：通过，1 passed / 190 skipped。
- `npm test -- -t "radar|map refresh|map proof"`：通过，17 passed / 174 skipped。
- `npm run lint`：通过。
- `npm run build`：通过。
- `npm test`：通过，191 passed。
- `git diff --check`：通过。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：确认 `node` 监听 `*:7001`。

## 剩余风险

- 本轮只做 PC 前端 gate 和 mock/DOM 回归验证，没有触发真实上位机 radar proof、Nav2、manual、keyboard、delivery、stop 或
  `/cmd_vel`；真实现场仍需在 `0.0.0.0:7001` 工作台确认。
