# 2026.06.28 11:05 PC Nav2 恢复后自动无运动检查

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通行程入口点击“恢复自动驾驶服务（不发车）”成功后，自动串联一次 Nav2 no-motion proof refresh 与地图预览刷新。
  - 恢复状态文案增加“已自动重新检查图上路线（不发车）”，让 operator 不需要在恢复服务和准备路线之间继续猜下一步。
  - 该链路只走固定 `/api/robot-control/nav2/start`、`/api/robot-control/nav2/proof/refresh` 和地图预览读取；不调用 goal execute、`/cmd_vel`、底盘 manual 或 free-roam。
- `pc-tools/workstation/test/App.test.ts`
  - 更新普通行程恢复服务回归，断言恢复成功后会自动请求 Nav2 no-motion proof refresh，同时仍不会请求行程执行、底盘 manual 或 `/cmd_vel`。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录 PC 普通行程入口的新恢复后检查口径。

## 验证结果

- 已只读 SSH 到上位机 `root@192.168.1.11 -p 37878`：
  - 当前看到 `free_roam_autonomy_node`、camera smoke、upper_robot_api、esp32_bridge。
  - 未看到 Nav2 planner/controller 相关 ROS 节点或 service；`ros2 node list` 与 nav/planner/controller service grep 均为空。
  - 结论：自动驾驶当前不能动的主要根因是 Nav2 服务栈未运行，不是相机独占，也不是雷达 ready 直接阻塞自由移动。
- `npm test -- test/App.test.ts --testNamePattern "no-motion Nav2 restore action" --maxWorkers=1 --no-fileParallelism`：1 passed，186 skipped。
- `npm test -- --maxWorkers=1 --no-fileParallelism`：2 files passed，331 tests passed。
- `npm run lint`：passed。
- `npm run build`：passed（Vite chunk-size warning 保持既有状态，不影响构建通过）。
- `git diff --check`：passed。
- 7001 已按 `HOST=0.0.0.0 PORT=7001 npm run api:public` 重启，`lsof` 显示 node 监听 `*:7001`。
- live summary `http://127.0.0.1:7001/api/robot-control/summary`：
  - `robot_api_connection.status=readable`，`blocked_count=0`，`failed_count=0`。
  - 相机 `status=source_first_frame_failed`，`source_diagnosis_status=uvc_no_frame_not_exclusive`，明确不是页面独占，而是 UVC 设备没有输出视频帧。
  - 自由移动 `free_roam_motion_start_ready=true`，建图验收仍缺 `camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview`。
  - Nav2 `planner_server_active=false`、`controller_server_active=false`、`path_generated=false`，`nav2_goal_ready=false`；当前自动驾驶不能动的恢复顺序仍是先恢复服务、再生成图上路线和复验 wheel raw L/R。

## 剩余风险

- 本轮没有在真实车上点击 `/api/nav2/start`，因为这是 Nav2 现场控制类动作；需要现场 operator 明确安全确认后再触发。
- 真实 NavigateToPose、wheel raw L/R 非零、delivery success 仍未证明；本轮只改恢复服务后的 no-motion 检查闭环。
- 相机仍是 `source_first_frame_failed/uvc_no_frame_not_exclusive`，需要继续查 USB/输入/供电或换 known-good UVC。
