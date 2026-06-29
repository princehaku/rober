# PC 行程执行包显示 managed runtime 当前状态

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `行程执行包` 的“自动驾驶”行新增当前服务缺口前缀。
  - live 形态中路线已准备、`nav2_goal_ready=true` 但 Nav2 lifecycle stopped 时，页面会显示“当前自动驾驶服务未运行，执行会托管启动；这不是额外预检，点击前仍只复核安全确认”。
  - 不改变 `nav2_goal_ready` 门禁，不把 managed runtime 改成额外预检，不自动启动 Nav2、不执行路线。
- `pc-tools/workstation/test/App.test.ts`
  - 补强 managed runtime 回归断言，锁定 stopped lifecycle 形态下的执行计划文案。
- `docs/product/pc_tools_workstation.md`
  - 同步记录行程执行包展示口径和安全边界。

## 现场只读复核

- 已按 `docs/vendor/VENDOR_INDEX.md` 复核本地硬件资料入口；本轮没有改 UART、波特率、底盘协议或硬件配置。
- SSH 只读 `root@192.168.1.11 -p 37878 hostname` 通过，主机为 `op-z3-b6.home`。
- SSH 只读 `ls -l /dev/video*` 和 `v4l2-ctl --list-devices`：
  - DV20 USB 摄像头为 `/dev/video1`，`/dev/video2` 是 metadata。
  - `fuser -v /dev/video0 /dev/video1 /dev/video2` 未显示占用者。
- SSH 只读 `GET /api/camera/health`：
  - `status=source_first_frame_failed`
  - `source_usage_status=not_in_use`
  - `source_diagnosis_status=uvc_no_frame_not_exclusive`
  - 结论：当前相机不是页面独占，根因仍是 UVC 无首帧。
- SSH 只读 `GET /api/nav2/status`：
  - `status=path_ready_with_service_blockers`
  - `lifecycle_running=false`
  - `lifecycle_state=stopped`
  - `planner_server_active=true`
  - `controller_server_active=false`
  - `path_generated=true`
  - `path_point_count=18`
  - 结论：当前自动驾驶的问题不是相机/雷达，而是 Nav2 lifecycle stopped / 控制服务未 active；PC execute 仍按 managed runtime 口径处理。
- SSH 只读 `GET /api/radar/status`：
  - `lifecycle_running=false`
  - `lifecycle_state=stopped`
  - `observed_lidar_port=/dev/ttyACM0`
  - 结论：雷达旧 proof 存在但 lifecycle 未运行，地图不应贴旧点。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "managed Nav2 runtime"`
  - `Test Files 1 passed (1)`，`Tests 2 passed | 215 skipped (217)`。
- 通过：`npm --prefix pc-tools/workstation test`
  - `Test Files 2 passed (2)`，`Tests 382 passed (382)`。
- 通过：`npm --prefix pc-tools/workstation run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成；Vite 仍提示既有 bundle 大小 warning。
- 通过：`git diff --check`
- 通过：7001 本地服务重启。
  - `node` 监听 `TCP *:7001`，日志输出 `pc-tools workstation API listening on http://0.0.0.0:7001`。
- 通过：只读 live `GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`
  - `nav2_goal_ready=true`
  - `nav2_stack_running=false`
  - `nav2_lifecycle_state=stopped`
  - `controller_server_active=false`
  - `path_generated=true`
  - `path_point_count=18`
  - `route_execution_status=goal_succeeded_wheel_feedback_not_proven`
  - `next_execution_base_command_mode=ros`
  - `camera_status=source_first_frame_failed`
  - `camera_source_usage_status=not_in_use`
  - `camera_source_diagnosis_status=uvc_no_frame_not_exclusive`
  - `radar_status=radar_stopped`
  - `radar_lifecycle_running=false`
  - `radar_overlay_point_count=0`
  - `free_roam_status=start_ready`
  - `free_move_start_ready=true`
  - `primary_ready_action_item_id=free_move`

## 剩余风险

- 本轮没有现场安全确认，因此没有启动 Nav2、自由移动、键盘连续手控、雷达、建图或底盘运动。
- 完整自动驾驶仍需现场勾选安全确认后执行图上行程，并在同一执行窗口验证轮速 L/R 非零。
