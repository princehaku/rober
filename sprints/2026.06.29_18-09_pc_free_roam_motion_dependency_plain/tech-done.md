# PC Free Roam Motion Dependency Plain Readback

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：`readback_summary.free_roam` 新增 `motion_sensor_dependency_status` 和 `motion_sensor_dependency_plain`，把“自由移动不依赖相机/雷达，建图验收才依赖传感器材料”变成稳定只读字段。
- `pc-tools/workstation/src/shared/contracts.ts`：补充新增 free-roam 字段类型。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏自由移动卡新增“移动门禁”行，直接显示自由移动只看现场安全确认和停止兜底。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`：覆盖 UI 展示和 summary 字段。
- `pc-tools/README.md`：同步记录只读字段和普通首屏口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts`
  - `Test Files 1 passed (1)`，`Tests 166 passed (166)`。
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts`
  - `Test Files 1 passed (1)`，`Tests 218 passed (218)`。
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 通过；保留既有 Vite chunk 大小提示。
- 通过：`git diff --check`
  - 无输出。
- 通过：重启 `HOST=0.0.0.0 PORT=7001 npm run api` 后用 live summary 确认新增字段。
  - `lsof` 显示 `node` 监听 `TCP *:7001 (LISTEN)`，日志显示 `pc-tools workstation API listening on http://0.0.0.0:7001`。
  - 只读 summary 返回 `free_roam_status=start_ready`、`motion_start_ready=true`、`motion_sensor_dependency_status=not_required_for_motion`、`motion_sensor_dependency_plain=自由移动启动只看现场安全确认和停止兜底；相机、雷达和地图记录只影响建图验收。`
  - 同次只读 summary 仍显示 `camera_preview_visible_status=not_visible_source_first_frame_failed`、`camera_source_diagnosis_status=uvc_no_frame_not_exclusive`、`nav2_status=goal_succeeded_wheel_feedback_not_proven`。

## 剩余风险

- 本轮只增强 PC 端只读解释，不替代真实现场安全确认；自由移动仍需要用户在现场勾安全确认并显式点击启动或启用键盘。
- 本轮不启动自由移动、不发送 manual、keyboard、Nav2、delivery、stop 或 `/cmd_vel`。
- 摄像头实时预览和 Nav2 轮速反馈闭环仍是后续风险；本轮没有执行需要现场安全确认的真实动车验证。
