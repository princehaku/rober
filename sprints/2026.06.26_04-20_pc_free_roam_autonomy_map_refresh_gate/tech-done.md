# 2026.06.26 04:20 PC 自动扫图地图刷新 gate

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `freeRoamMapWysiwygPending`，统一表示扫图地图画面或地图状态正在刷新。
  - 自动扫图 start gate 增加 `!freeRoamMapWysiwygPending`，避免基于旧地图画面启动上车端自动扫图状态机。
  - 自动扫图准备按钮在刷新中显示 `等待地图刷新`，准备区 blocker 显示 `地图画面正在刷新` 或 `地图状态正在刷新`。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展自动扫图 ready 测试：本轮已有地图刷新成功后，再次触发延迟的扫图画面刷新；pending 期间自动扫图按钮禁用，点击不会调用 `/api/robot-control/free-roam/autonomy/start`；刷新返回后按钮恢复可用。
- `docs/product/pc_tools_workstation.md`
  - 记录自动扫图 start 必须等待地图刷新完成的普通首屏 WYSIWYG 口径。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- -t "starts free-roam autonomy"`
  - 结果：1 passed，190 skipped。
- 已通过：`cd pc-tools/workstation && npm run lint`
- 已通过：`cd pc-tools/workstation && npm run build`
- 已通过：`cd pc-tools/workstation && npm test`
  - 结果：2 files passed，191 tests passed。
- 已通过：`git diff --check`
- 已确认：`lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - 结果：`node` 正在监听 `TCP *:7001 (LISTEN)`。

## 剩余风险

- 本轮是 PC 前端 mock 验证，没有做真实自动扫图 HIL。
- 没有触发真实上位机自动扫图、manual、Nav2、delivery 或 `/cmd_vel`；真实场地仍需 HIL 验证地图刷新期间 start gate。
