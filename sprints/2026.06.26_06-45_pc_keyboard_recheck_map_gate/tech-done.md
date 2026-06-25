# 2026.06.26 06:45 PC keyboard recheck map gate

- sprint_type: micro
- status: done
- owner: User Touchpoint Full-Stack Engineer

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏键盘区 `复查手控条件` 新增 `canRefreshPlainKeyboardGate`，复用地图 WYSIWYG pending 状态。
  - 地图 preview/proof 刷新期间按钮显示 `等待地图刷新` 并禁用。
  - `refreshPlainKeyboardGate()` 入口同步早退，避免地图刷新期间继续聚合 summary、底盘反馈、Nav2 latest 和 delivery latest。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展地图刷新互斥用例，覆盖键盘复查按钮在 preview/proof pending 下禁用、文案等待地图刷新、点击不新增只读请求。
- `docs/product/pc_tools_workstation.md`
  - 同步记录键盘复查地图 WYSIWYG gate 行为边界。

## 验证结果

- `npm test -- -t "blocks visible-route execution while the map preview is refreshing"`：通过，1 passed / 190 skipped。
- `npm run lint`：通过。
- `npm run build`：通过。
- `npm test`：通过，2 files / 191 tests passed。
- `git diff --check`：通过。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN || true`：确认 PC Node 仍监听 `*:7001`。

## 剩余风险

- 本轮只验证 PC 前端 mock 行为，不触发真实小车运动，不覆盖真车 HIL、Nav2 实车执行或 WAVE ROVER 串口反馈。
- 未修改 Clash、系统代理或端口策略；本轮仅确认现有 Node 服务仍在 `0.0.0.0:7001` 等效监听。
