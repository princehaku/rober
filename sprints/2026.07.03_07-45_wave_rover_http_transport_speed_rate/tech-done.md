# 2026-07-03 07:45 WAVE ROVER HTTP Transport And Speed Rate

## sprint_type

micro

## 实际改动

- `esp32_bridge` 增加 `command_transport=http`、`wave_rover_http_base_url` 和 `http_timeout_s`，可把 `/cmd_vel` 转成 WAVE ROVER 原厂 HTTP `/js?json=...` 命令，绕过当前上位机 UART TX 不被 ESP32 解析的问题。
- `wave_rover_protocol.build_startup_config_commands()` 在 `T=900 main/module` 后新增非运动 `{"T":138,"L":1,"R":1}`，避免现场 `T=139` 读到速度倍率 `0/0` 后把速度控制压死。
- PC summary/普通首屏增加 HTTP transport 写入事实，轮速提示从只看“串口 write”扩展到“HTTP 下发/transport 下发”。
- 同步更新 `docs/product/pc_tools_workstation.md` 和 `docs/hardware/wave_rover_json_bridge.md`：ROS2 配套地图工具仍按普通用户 PC 大地图、工程 RViz2/Foxglove 分层；HTTP 下发和 IMU 扰动不能冒充 wheel raw 非零、Nav2 HIL 或 delivery success。

## 验证结果

- 本机单元验证：
  - `python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py onboard/src/ros2_trashbot_hardware/test/test_hardware_diagnostics_proof.py onboard/tests/test_upper_robot_api.py` 通过，`Ran 140 tests ... OK (skipped=1)`。
  - `npm test -- --run test/robotControlSummary.test.ts` 通过，`11 passed`。
  - `npm test -- --run test/App.test.ts -t "map|地图|RViz2|Foxglove|direct map"` 通过，`70 passed`。
  - `npm test -- --run test/catalog.test.ts` 通过，`185 passed`。
  - `npm run build` 通过。
  - `python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_protocol.py onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/bridge_config.py onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge_node.py onboard/scripts/upper_robot_api.py` 通过。
- 上位机现场验证：
  - ESP32 HTTP `http://192.168.1.3/js?json=...` 可访问，`T=139` 可返回，`T=138 L/R=1` 后 `T=139` 返回 `L=1,R=1`。
  - 重新部署并重启 `esp32_bridge` 后，startup command debug 已记录 `{"T":138,"L":1,"R":1}`，且 `command_transport=http`、`http_write_returned=true`、`transport_write_returned=true`。
  - `esp32_bridge` 以 `command_transport=http` 启动后，PC 手控 `forward 0.12m/s 800ms` 产生多帧 `T=11 L/R=255`，command debug 记录 `command_transport=http`、`http_write_returned=true`、`transport_write_returned=true`。
  - direct HTTP `T=1 L/R=0.39` 和 bridge HTTP PWM pulse 后，T1001 IMU roll/pitch 有明显变化，说明 ESP32 命令链路和运动扰动存在。
- PC 服务验证：
  - 本机 Node 已重启并监听 `0.0.0.0:7001`。
  - `GET /map` 返回 HTTP 200，使用新构建的 `dist/assets/index-9Z6uNbIr.js`。
  - PC map 答复口径保持：普通用户用 PC 大地图和 `/map`，ROS2 工程观察用 RViz2 或 Foxglove bridge。

## 剩余风险

- `T=1001.L/R` 仍为 `0/0`，本轮不能宣称 wheel raw L/R 非零、编码器 HIL pass、Nav2 真实路线执行成功或 delivery success。
- 相机仍是 UVC STREAMON 失败，`YUYV@320x240@20` 和 `MJPG@480x320@30` 都没有帧，页面独占已排除但硬件/USB 问题未解决。
- `trashbot-upper-robot-api.service` stop 偶发卡住，需要 `systemctl kill -s SIGKILL` 后再 start；后续应单独修 graceful shutdown。
- 当前 HTTP transport 是现场有效旁路，若 ESP32 STA IP 变化，需要更新 `wave_rover_http_base_url` 或固定地址发现机制。
