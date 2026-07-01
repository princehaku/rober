# PC 地图工程观察与键盘短 alias

sprint_type: micro

## 实际改动

- `live_closure_summary` 和 `/api/robot-control/live-summary` 新增键盘连续手控短 alias，直接暴露键盘 ready、安全确认、启用不发车、按住才动、脉冲周期、停止触发、验收口径和固定端点。
- PC 大地图工程观察合同补齐 RViz2/Foxglove 角色说明、Foxglove bridge 安装命令、普通用户主工具和工程工具不发车字段；普通用户入口仍优先 `/map` 大地图。
- 普通首屏 DOM、地图工程观察折叠区、测试夹具和产品文档同步更新；新增字段只读，不启动 ROS2/RViz2/Foxglove，不发送任何运动命令。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts -t "minimal precheck fields for same-window wheel rerun"`，1 file passed，1 test passed。
- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "workstation live-summary route exposes a flat read-only current card for field curl checks"`，1 file passed，1 test passed。
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`，1 file passed，1 test passed。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，Vite 构建成功；保留既有 chunk size warning。
- 通过：`cd pc-tools/workstation && npm test`，3 files passed，418 tests passed。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `0.0.0.0:7001`；`HEAD http://127.0.0.1:7001/map` 返回 `200`，`GET /api/robot-control/live-summary` 返回 `keyboard_ready=true`、`keyboard_enable_sends_motion=false`、`keyboard_hold_to_move_required=true`、`keyboard_pulse_interval_ms=260`、`keyboard_pulse_duration_ms=240`、`map_display_engineering_tools_action_label=工程观察`、`map_display_ordinary_user_tool=pc_big_map`、`map_display_foxglove_bridge_install_command="sudo apt install ros-humble-foxglove-bridge"`、`map_display_engineering_tools_sends_motion=false`。

## 剩余风险

- 本轮只改善 PC 地图/工程观察说明和键盘连续控制可读性；真实 `keyboard_continuous_motion_verified` 仍需要现场安全确认后按住方向键/WASD，并在同一次按住窗口读到 wheel L/R 非零和松开 stop 落稳。
- RViz2/Foxglove 仍是手动工程观察入口；本轮不安装、不启动，也不验证真实 Foxglove bridge 连接。
