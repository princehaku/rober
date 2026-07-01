# 自由移动读回 alias

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：`RobotControlSummaryResponse` 新增顶层只读别名 `free_move_readback_endpoints` 和 `free_move_required_success_markers`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：两个别名复用 `start_free_move` runbook 的 `acceptance_endpoints` 和 `missing_evidence`，fallback 保持 `/api/robot-control/free-roam/autonomy/latest`、`/api/robot-control/map/preview`、`/api/robot-control/summary`。
- `pc-tools/workstation/test/robotControlSummary.test.ts`：补回归断言，防止现场 `curl | jq` 再读到空字段。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`：同步说明自由移动读回 alias 只解释验收链路，不自动启动 free-roam 或任何运动接口。

## 验证结果

- `git diff --check`：通过。
- `cd pc-tools/workstation && npm test -- --run catalog.test.ts App.test.ts robotControlSummary.test.ts`：3 个测试文件通过，427 条测试通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，保留既有 Vite chunk size warning。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `21984`。
- 真实只读 summary smoke：`status=needs_wheel_rerun`，`map_display_primary_url=/map`，`map_display_default_zoom_percent=1600%`，`map_display_max_zoom_percent=4800%`，`map_display_ros2_companion_tools=[rviz2,foxglove]`，`map_display_starts_ros2=false`，`map_display_starts_nav2=false`，`map_display_starts_map_runtime=false`，`free_move_readback_endpoints=[/api/robot-control/free-roam/autonomy/latest,/api/robot-control/map/preview,/api/robot-control/summary]`，`free_move_required_success_markers=[free_roam_latest_motion_ready]`。
- `/map` 直达页 HTTP 200。

## 剩余风险

- 本轮没有执行任何 motion/control POST，没有安全确认后的 Nav2、键盘或 free-roam 真实运动验收；`motion` 仍缺同窗口 wheel L/R 非零、delivery success、键盘连续手控和自由移动 latest 运行读数。
- `wysiwyg` 和 `mapping` 仍受相机首帧硬件问题影响；当前 ROS2 配套口径是 RViz2/Foxglove 只作观察，普通用户默认仍用 PC `/map` 大屏。
