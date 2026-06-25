# 2026.06.26 06:55 PC wheel readback map gate

- sprint_type: micro
- status: done
- owner: User Touchpoint Full-Stack Engineer

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `canRunBaseFeedbackSamples`，把普通 `刷新当前轮速（只读）` 和高级 `采集底盘反馈（高级）` 接入地图 WYSIWYG pending gate。
  - 地图 preview/proof 刷新期间，轮速只读按钮显示 `等待地图刷新` 并禁用。
  - `runBaseFeedbackSamples()` 默认在地图刷新期间早退；first-jog 后的内部反馈采样显式 `allowDuringMapRefresh`，避免动作证据丢失。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展地图刷新互斥用例，覆盖轮速只读按钮在 preview/proof pending 下禁用、显示等待地图刷新，点击不新增 `/api/robot-control/base/feedback-samples`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录轮速只读刷新地图 WYSIWYG gate 行为边界。

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
