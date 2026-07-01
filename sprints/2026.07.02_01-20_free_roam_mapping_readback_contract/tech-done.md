# 自由移动与建图读回合同补齐

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 自由移动 `start_free_move` 验收端点从 `free-roam latest + summary` 扩展为 `free-roam latest + map preview + summary`。
  - 传感器 ready 后建图 `start_mapping_when_sensors_ready` 验收端点扩展为 `free-roam latest + map preview + summary`，同时文案明确读回状态机和地图 WYSIWYG。
  - summary 顶层新增 `fixed_free_roam_latest_endpoint=/api/robot-control/free-roam/autonomy/latest`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 自由移动验收卡 fallback 读回链路同步加入地图预览。
  - `plain-live-closure-summary` 和 `plain-free-move-mapping-frontload` DOM 改为消费 summary 的 fixed free-roam latest endpoint。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 补齐 `RobotControlLiveClosureSummary` 与 `RobotControlSummaryResponse` 的 fixed free-roam latest endpoint 类型。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`
  - 更新自由移动、建图、现场验收和 DOM 合同断言。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录自由移动/建图启动后读回链路。

## 验证结果

- `cd pc-tools/workstation && npm test -- robotControlSummary.test.ts`
  - 10 tests passed。
- `cd pc-tools/workstation && npm test -- App.test.ts`
  - 236 tests passed。

## 剩余风险

- 本轮没有触发真实 free-roam 或 map start，因为当前会话没有新的现场安全确认；改动只证明 PC/API/DOM 合同和单测。
- 当前现场 summary 仍显示建图启动缺相机首帧，需处理 USB/UVC 首帧问题后再做真实建图 HIL 验收。
