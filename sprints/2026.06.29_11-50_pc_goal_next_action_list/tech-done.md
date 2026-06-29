# PC 目标待处理动作列表

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：为 `goal_checklist_summary` 增加 `next_action_items[]`，每项包含目标 id、标题、状态、下一步、来源卡片、安全确认和真实运动标记。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：从现有 `goal_checklist[]` 只读派生待处理动作列表，不新增上车写接口，不触发雷达、建图、Nav2 或底盘运动。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`、`pc-tools/workstation/src/styles.css`：普通首屏在“本轮目标检查”摘要内显示“待处理动作”列表，每项 `去处理` 只滚动并聚焦到现有控件。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`：补充 API contract 和 UI 交互断言，确认动作列表顺序、中文文案和只聚焦不 fetch。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录 `next_action_items[]` 合约和只读行为边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints"`，1 个文件通过，1 个测试通过。
- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "renders Robot Control V1 by default"`，1 个文件通过，1 个测试通过。
- 通过：`npm --prefix pc-tools/workstation test`，2 个文件通过，376 个测试通过。
- 通过：`npm --prefix pc-tools/workstation run build`；仍有既有 Vite chunk size warning，但 TypeScript 和 Vite build 均通过。
- 通过：PC API 已重启到 `0.0.0.0:7001`，监听 PID `42411`；只读读取 `GET /api/health` 成功。
- 通过：只读读取 `GET /api/robot-control/summary`，live `goal_checklist_summary.next_action_items` 返回 6 项：
  `camera_wysiwyg`、`radar_map_points_wysiwyg`、`nav2_route_execution`、`keyboard_continuous_control`、`free_move`、`mapping_start`。
  当前 live 状态仍显示摄像头 UVC 无帧、雷达未运行或扫描已停、Nav2 上次路线成功但轮速 L/R 窗口未非零。

## 剩余风险

- 这次只改善 PC 首屏引导和 summary 合约，不执行真实运动、不启动雷达、不执行 Nav2，因此不等价于 HIL 验收。
- 摄像头当前 live 读数仍显示 UVC 设备无帧；雷达仍需要现场启动并刷新当前地图；Nav2 仍需要现场安全确认后复验轮速 L/R 非零。
