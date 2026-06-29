# PC 目标收口分组

sprint_type: micro

## 实际改动

- `goal_checklist_summary` 新增 `ready_action_items[]` 和 `blocked_action_items[]`，按未完成项的真实状态把“现场可收口”和“先补条件”分开。
- 普通首屏新增“收口分组”只读条，点击只聚焦到已有控件，不自动勾选、不执行行程、不启用键盘、不启动雷达/自由移动/建图。
- 同步更新 PC workstation 文档和对应单测，避免后续 UI 回退到一串混杂的未完成列表。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints"`，1 passed。
- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "renders Robot Control V1 by default"`，1 passed。
- 通过：`npm --prefix pc-tools/workstation test`，2 files / 376 tests passed。
- 通过：`npm --prefix pc-tools/workstation run build`。
- 通过：PC API 已重启到 `0.0.0.0:7001`，PID `76339`。
- 通过：只读 `GET /api/robot-control/summary` 返回 `ready_action_items=["nav2_route_execution","keyboard_continuous_control","free_move"]`，
  `blocked_action_items=["camera_wysiwyg","radar_map_points_wysiwyg","mapping_start"]`。

## 剩余风险

- 当前改动只提升 PC 端目标分组和现场操作入口清晰度，不直接触发真实运动；Nav2、键盘连续手控、自由移动仍需要现场安全确认后再做硬件复验。
- live 只读状态显示摄像头不是页面独占，但 UVC 设备没有输出视频帧；雷达未运行且当前地图雷达点为 0；建图启动仍缺 `camera_first_frame` 和 `lidar_fresh`。
