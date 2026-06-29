# PC 本轮进度可先动摘要

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏“本轮进度”新增 `可先动` 只读摘要，按 summary 展示自由移动、键盘手控、图上行程是否已到“勾安全确认即可”的状态。
- `pc-tools/workstation/test/App.test.ts`：补充 DOM 断言，锁定相机/雷达缺口存在时，首屏仍明确显示“自由移动可启动、键盘可启用、图上行程可重跑；画面和雷达只影响建图验收”。
- `docs/product/pc_tools_workstation.md`：同步普通首屏 `可先动` 摘要和无控制边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "plain"`，结果 `46 passed | 171 skipped`。
- 通过：`npm --prefix pc-tools/workstation test`，结果 `2 passed` test files，`382 passed` tests。
- 通过：`npm --prefix pc-tools/workstation run build`，TypeScript 与 Vite build 成功；Vite 仍提示单个 chunk 超过 500 kB，这是既有体积提示，不影响本轮首屏摘要。
- 通过：`git diff --check`。
- 通过：本机 PC API 已重启到 `0.0.0.0:7001`，日志输出 `pc-tools workstation API listening on http://0.0.0.0:7001`。
- 通过：只读检查 live `/api/robot-control/summary`，`free_move_start_ready="true"`、`keyboard.start_ready="true"`、`safe_command_boundary.nav2_goal_ready=true`；同时 `camera.status="source_first_frame_failed"`、`radar.status="radar_stopped"`、`mapping_blocked_reasons="camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview"`，符合“可先动，传感器缺口只卡建图验收”的展示口径。

## 剩余风险

- 本轮只改普通首屏只读提示，不自动勾选安全确认、不启动自由移动、不启用键盘、不执行 Nav2、不发送 `/cmd_vel`。
- 真实车仍需现场确认后才能验证：Nav2 ROS 模式重跑 wheel L/R 非零；相机首帧和雷达新鲜仍是建图验收缺口。
