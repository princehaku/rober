# PC ROS2 地图配套与 bridge 模式口径澄清

sprint_type: micro

## 实际改动

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_protocol.py`：修正 `build_cmd_vel_command` 注释，明确 `/cmd_vel` 最终落成 `T=11/T=13/T=1` 由 `command_mode` 决定，当前现场默认是 launch 选择的 `T=11/PWM`。
- `onboard/scripts/upper_robot_api.py`：修正 PC 手控方向转换注释，避免把 ROS `/cmd_vel` 控制面误写成一定直发 vendor `T=13`。
- `docs/product/pc_tools_workstation.md`：把最前面的当前有效地图口径从旧 `400%` 更新为 `45%` 完整态势视角，并继续说明 ROS2 配套为 RViz2 / Foxglove 只读观察，不替代普通 PC 页面。
- `docs/interfaces/ros_runtime_contracts.md`、`docs/interfaces/ros_contracts.md`：同步当前 `/cmd_vel -> esp32_bridge -> vendor T=11/PWM` 默认链路，保留 `speed/T=1` 与 `ros/T=13` 为显式诊断 override。

## 验证结果

- `python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_protocol.py`：通过。
- `cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts test/catalog.test.ts -t "map_display_default_zoom_percent|speed_mps|keyboard_manual_command_mode|safe command boundary"`：通过，1 个测试命中，195 个跳过。
- `cd pc-tools/workstation && npm test -- --run test/App.test.ts test/robotControlSummary.test.ts test/catalog.test.ts`：通过，3 个 test files，433 个 tests passed。
- `cd pc-tools/workstation && npm run build`：通过；保留既有 Vite chunk size warning。
- `git diff --check`：通过。
- 现场 PC Node `http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 读回：`map_display_default_zoom_percent=45%`、`map_current_visible=true`、`path_current_visible=true`、`radar_map_points_visible=true`、`keyboard_ready=true`。
- 现场 `POST /api/robot-control/base/stop?baseUrl=http://192.168.1.11:8787` 经 PC 代理返回 `proxy_status=command_forwarded`、`remote_http_status=200`，确保本轮诊断后底盘 stop 收口。

## 剩余风险

- 摄像头仍读回 USB `12M`，此前直接 V4L2 `VIDIOC_STREAMON` 返回 `Input/output error`；当前判断仍是物理 USB/full-speed 链路问题，不是 PC 页面独占。
- PC/WASD 到 `/cmd_vel`、`esp32_bridge`、vendor `T=11,L/R=255` 的命令链路已观察到，但 `T=1001 L/R` 仍为 `0/0`，不能宣称 wheel raw 非零、真实物理移动或 HIL pass。
- Nav2 `/navigate_to_pose` action server 当前可达但会拒收目标；本轮只修正文档/注释口径，没有完成完整 Nav2 路线执行和 delivery success。
