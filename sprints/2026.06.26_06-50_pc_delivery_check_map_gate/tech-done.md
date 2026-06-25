# 2026.06.26 06:50 PC delivery check map gate

- sprint_type: micro
- status: done
- owner: User Touchpoint Full-Stack Engineer

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `canCheckDeliveryGap`，把送达缺口复查接入地图 WYSIWYG pending gate。
  - 普通首屏 `复查送达条件（不确认）` 在地图 preview/proof 刷新期间显示 `等待地图刷新` 并禁用。
  - `checkDeliveryGap()` 入口同步早退，高级 `复算送达缺口（高级）` 也复用同一 gate。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展送达地图刷新用例，覆盖地图刷新期间送达复查按钮禁用、显示等待地图刷新，点击不发 `/api/robot-control/delivery/check`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录送达缺口复查的地图 WYSIWYG gate 行为边界。

## 验证结果

- `npm test -- -t "shows delivery confirmation pending on the map while final completion is in flight"`：通过，1 passed / 190 skipped。
- `npm run lint`：通过。
- `npm run build`：通过。
- `npm test`：通过，2 files / 191 tests passed。
- `git diff --check`：通过。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN || true`：确认 PC Node 仍监听 `*:7001`。

## 剩余风险

- 本轮只验证 PC 前端 mock 行为，不触发真实小车运动，不覆盖真车 HIL、Nav2 实车执行或 WAVE ROVER 串口反馈。
- 未修改 Clash、系统代理或端口策略；本轮仅确认现有 Node 服务仍在 `0.0.0.0:7001` 等效监听。
