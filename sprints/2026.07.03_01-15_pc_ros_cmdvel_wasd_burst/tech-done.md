# PC ROS WASD Burst And Big Map Companion

## sprint_type

micro

## 目标

本轮响应 CEO 现场反馈：PC 地图太小、ROS2 是否有配套工具、PC 键盘连续手控要能真正走 ROS 控制链，且普通用户界面继续保持简易风格。

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - 新增上车端进程内 `rclpy` `/cmd_vel` burst publisher，优先复用同一个 ROS2 publisher，不再每个按键 pulse 冷启动两次 `ros2 topic pub`。
  - ROS 手控现在先等待 `/cmd_vel` 至少一个订阅者，再按 20Hz 在 pulse 窗口内连续发布，停车也按短 hold 发布零速。
  - 保留 CLI burst fallback：当 ROS Python 环境不可用或进程内发布失败时，使用带 `--wait-matching-subscriptions` 的 `ros2 topic pub` burst。
- `pc-tools/workstation/src/**`
  - PC 普通手控、键盘 WASD 和 Node 代理默认控制模式从 `pwm` 改为 `ros`。
  - 普通用户文案保持简易口径：首屏写“ROS 桥接低速脉冲”，不把 `/cmd_vel` 直接漏到普通界面。
  - 7001 服务继续绑定 `0.0.0.0:7001`，默认小车地址继续固定 `http://192.168.1.11:8787`。
- `docs/product/pc_tools_workstation.md`
  - 补充 PC 键盘低速点动默认 `command_mode=ros` 的产品边界。
  - 明确 ROS2 配套分层：普通用户用 PC 大地图和 `/map`，工程调试用 RViz2，远程浏览器观察用 Foxglove bridge。
- `onboard/tests/test_upper_robot_api.py`、`pc-tools/workstation/test/*.test.ts`
  - 更新 ROS burst publisher、PC 代理默认模式和普通首屏文案的回归测试。

## 采用的硬件/vendor 资料来源

- `docs/vendor/VENDOR_INDEX.md`
  - WAVE ROVER 上下位通信为 UART 换行 JSON，vendor Raspberry Pi 默认 `/dev/ttyAMA0` `115200`，Orange Pi 现场串口需以目标机实际设备为准。
  - 关键指令：`T=1` speed、`T=11` PWM、`T=13` ROS X/Z、`T=130/131/142/143` feedback/flow。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER/WAVE_ROVER_V0.9/json_cmd.h`
  - `CMD_ROS_CTRL=13`，示例 `{"T":13,"X":0.1,"Z":0.3}`，注释为 `(m/s,rad/s)(Not for the products without encoders)`。
  - `CMD_PWM_INPUT=11`，示例 `{"T":11,"L":164,"R":164}`。

## 验证结果

- 单元测试：
  - `python3 -m py_compile onboard/scripts/upper_robot_api.py`
  - `python3 -m unittest onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests`
  - 结果：`Ran 97 tests ... OK (skipped=1)`。
- PC 测试：
  - `npm test -- --run test/catalog.test.ts test/App.test.ts test/robotControlSummary.test.ts`
  - 结果：`Test Files 3 passed`，`Tests 431 passed`。
- PC 构建：
  - `npm run build`
  - 结果：通过；Vite 仅提示 bundle chunk 超过 500kB。
- Docker/Humble 构建：
  - `bash onboard/scripts/docker_humble_build.sh`
  - 结果：通过，`Summary: 6 packages finished [46.6s]`。
- 上车部署：
  - 已把 `onboard/scripts/upper_robot_api.py` 部署到 `root@192.168.1.11:8787` 并重启上车 API。
  - 上车 API 当前监听 `0.0.0.0:8787`。
- PC 服务：
  - 已重启本机 workstation，当前监听 `0.0.0.0:7001`。
  - `GET /api/health` 读回 `default_robot_api_base_url=http://192.168.1.11:8787`。
- 实机/现场 smoke：
  - `GET /api/robot-control/summary`：`keyboard_mode=ros`，地图、路线、雷达点可见，`camera_visible=false`。
  - `GET /api/robot-control/map/preview`：`width=261`、`height=113`、`path_preview_point_count=18`、`radar_overlay_status=loaded`、`robot_pose_status=map_pose_observed`、目标点 `x=0.8,y=0.05` 可见。
  - 直连上车 `POST /api/base/manual command_mode=ros feedback_mode=realtime`：`publish_backend=rclpy_inprocess_burst`，0.26s 指令发布 6 帧，停车发布 4 帧，`subscription_count=1`。
  - PC 7001 代理 `POST /api/robot-control/base/manual`：`proxy_status=command_forwarded`，`remote_http_status=200`，`manual_command_executed=true`，`auto_stop_executed=true`，耗时约 `0.48s`。

## 剩余风险

- WAVE ROVER T1001 轮速仍为 `L/R=0/0`，`wheel_feedback_lr_nonzero_proven=false`。本轮已证明 PC 和 ROS2 `/cmd_vel` 发布链路打通，但还不能证明底盘实际轮速非零；后续需要继续查 ESP32 bridge、底盘 enable/编码器/固件模式或现场电机状态。
- 相机仍为 `source_first_frame_failed`，诊断为 `uvc_full_speed_usb_not_exclusive`，不是页面独占问题。当前 USB 速率/物理链路仍需换高速 USB 口/线或 known-good UVC 后复测。
- 完整 Nav2 路线执行和 delivery success 仍不能因本轮手控链路修复而标记完成；还需要同一执行窗口 wheel raw L/R 非零和送达确认材料。
