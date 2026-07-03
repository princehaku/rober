# Bridge HTTP WAVE ROVER Runtime Fix

## sprint_type: micro

## 实际改动

- `onboard/src/ros2_trashbot_bringup/launch/bringup.launch.py`
  - 显式新增并传递 `command_transport`、`wave_rover_http_base_url`、`http_timeout_s`、`main_type`、`module_type`。
  - 现场默认固定为 `command_transport=http`、`wave_rover_http_base_url=http://192.168.1.3`、`main_type=1`、`module_type=0`，避免后续 launch 回到 serial 或 UGV02 口径。
- `onboard/src/ros2_trashbot_bringup/launch/autonomous.launch.py`
  - 同步上述 bridge 参数，确保 Nav2/autonomous runtime 也沿用当前可跑的 WAVE ROVER HTTP 控制链路。
- `onboard/scripts/o11_nav2_goal_execution_proof.py`
  - helper 自启动托管 Nav2 runtime 时，`esp32_bridge` 命令固定携带 HTTP、WAVE ROVER `1/0`、`pwm=164`。
  - managed runtime metadata 额外记录 `base_command_transport`、`base_wave_rover_http_base_url`、`base_main_type`、`base_module_type`。
- `onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`
  - 锁住 bringup/autonomous 的 HTTP + WAVE ROVER 主类型参数合同。
- `onboard/scripts/test_o11_nav2_goal_execution_proof.py`
  - 锁住 O11 helper 拼出的 bridge 命令必须包含 `command_transport=http`、`wave_rover_http_base_url=http://192.168.1.3`、`main_type=1`、`module_type=0`。

## 现场同步与运行验证

- 已同步到上位机 `/root/rober/onboard`：
  - `bringup.launch.py` sha256 `bad3a5404a7c12794708071b323e2db2e332187d4a76a7edacbec6a883306d11`
  - `autonomous.launch.py` sha256 `ca0d344ed33500c98b8ac5575397162870da4608bdf047c17e84eb3def05734a`
  - `o11_nav2_goal_execution_proof.py` sha256 `773573e08e56223a5d04306b6f2e544507244696b6b5d44038962552d5cc8238`
- 已先向 ESP32 HTTP 发送 stop：
  - `T=11 L=0,R=0`
  - `T=1 L=0,R=0`
  - `T=13 X=0,Z=0`
- 已重启现场脱管 `esp32_bridge`，当前进程参数为：
  - `command_mode:=pwm`
  - `pwm_min_abs:=164`
  - `pwm_max_abs:=164`
  - `main_type:=1`
  - `module_type:=0`
  - `command_transport:=http`
  - `wave_rover_http_base_url:=http://192.168.1.3`
- ROS 参数读回：
  - `/esp32_bridge main_type=1`
  - `/esp32_bridge module_type=0`
  - `/esp32_bridge command_transport=http`
  - `/esp32_bridge wave_rover_http_base_url=http://192.168.1.3`
  - `/esp32_bridge pwm_min_abs=164`
  - `/esp32_bridge pwm_max_abs=164`
- bridge startup command debug 已写出：
  - `{"T":900,"main":1,"module":0}`
  - `{"T":138,"L":1,"R":1}`
  - `{"T":143,"cmd":0}`
  - `{"T":142,"cmd":100}`
  - `{"T":131,"cmd":1}`

## PC 功能复测

- WASD/手控短脉冲：
  - PC `POST /api/robot-control/base/manual` 前进和后退均返回 `proxy_status=command_forwarded`。
  - 两次均返回 `command_result_ok=true`、`stop_result_ok=true`、`command_raw_lr_nonzero_proven=true`、`motion_signal_observed=true`、`motion_signal_source=imu_attitude_delta`。
  - `wheel_feedback_lr_nonzero_proven=false`、`wheel_feedback_latest_raw_left=0`、`wheel_feedback_latest_raw_right=0` 仍未解决。
- 地图：
  - `live-summary` 读回 `map_current_visible=true`、`path_current_visible=true`、`route_target_current_visible=true`。
  - 雷达只读刷新后 `map/preview` 读回 `radar_overlay_status=loaded`、`radar_overlay_current_point_count=162`、`radar_overlay_wysiwyg_complete=true`。
  - 最终 `live-summary` 读回 `radar_map_points_current_visible=true`。
- 相机：
  - `camera_current_visible=false`
  - `camera_source_diagnosis_status=uvc_no_frame_not_exclusive`
  - 上位机 camera health 显示 DV20 `/dev/video1` 为 480M UVC，`source_usage_owner_count=0`，当前没有页面独占。
  - 内核当前无新的 UVC transport error，历史只有旧 `Failed to resubmit video URB (-1)`；V4L2 input 状态为 `ok`，但仍没有首帧。

## 测试结果

- `python3 -m unittest onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py onboard/scripts/test_o11_nav2_goal_execution_proof.py`
  - 26 tests OK。
- `python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py onboard/src/ros2_trashbot_hardware/test/test_hardware_diagnostics_proof.py`
  - 40 tests OK。
- `git diff --check`
  - OK。

## 剩余风险

- `esp32_bridge` 现在已按正确参数重启，但仍是手工脱管进程；后续若需要开机自启，应补 systemd unit 或统一由 bringup/autonomous 管理。
- PC 大地图和 WASD 当前可用；wheel raw `T=1001 L/R` 仍为 `0/0`，不能声明 wheel raw 非零闭环。
- 实时图传仍没有首帧。当前证据排除了页面独占、USB 低速、当前 UVC 传输错误和格式枚举失败，剩余更像 DV20 上游输入信号、摄像头/采集卡、视频线、接口或供电问题；需要换 known-good UVC 或检查 DV20 输入源后复测。
