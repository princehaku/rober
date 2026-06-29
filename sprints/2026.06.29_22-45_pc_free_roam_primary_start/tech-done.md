# PC 自由移动首屏主按钮启动状态机

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 将普通首屏 `plain-free-roam-start` 从只调用 `startMapRuntime()` 改为 `startPlainFreeRoamPrimary()`。
  - 传感器未满足建图验收时，主按钮直接调用固定 free-roam autonomy start 代理，让车可在安全确认后先低速自由移动。
  - 传感器 ready 且处于自动扫图模式时，主按钮先启动地图记录，再启动 free-roam autonomy start，使同一次低速移动可用于建图。
  - 新增 `plain-map-runtime-start` 测试入口，保留地图卡“重新建图”的纯地图记录职责，避免地图 lifecycle 测试误触发状态机。
  - 将自由移动状态机 pending/start/stop 的“下一步”判断前置，避免无地图记录时状态机已启动但下一步仍提示“开始自由移动”。
- `pc-tools/workstation/test/App.test.ts`
  - 更新首屏主按钮测试：ready 建图场景断言主按钮先 `map/start` 后 `free-roam/autonomy/start`，请求体 `confirm_mapping_active=true`。
  - 更新 degraded 场景测试：相机或雷达未 ready 时，主按钮直接 `free-roam/autonomy/start`，不调用 `map/start`、`base/manual`、Nav2 或 `/cmd_vel`。
  - 地图记录、键盘扫图、地图失败和保存失败类测试改为使用 `plain-map-runtime-start`，继续覆盖纯地图记录合同。
- `docs/product/pc_tools_workstation.md`
  - 记录普通首屏主按钮新语义和本轮安全边界。
- `docs/process/okr_progress_log.md`
  - 追加本轮 Objective 3/5 进展摘要。

## 验证结果

- `npm test -- --run`：通过，2 个 test files，386 tests OK。
- `npm run build`：通过，`tsc -p tsconfig.app.json`、`vite build`、`tsc -p tsconfig.server.json` OK。
- 本轮没有通过浏览器或 API 点击真实 free-roam start/manual/keyboard/Nav2/delivery/stop，也没有发送 `/cmd_vel`。

## 剩余风险

- 本轮验证边界是 PC 前端和代理合同测试，没有做真实小车 HIL 发车验证。
- 上车端最新只读状态在本轮开始前仍显示 `decision_state=stopping`、`cmd_vel_publish_enabled=false`；需要现场安全确认后再由 operator 触发真实 start 验证。
