# WAVE ROVER Main Type Live Alignment

## sprint_type: micro

## 实际改动

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/bridge_config.py`
  - 修正 `main_type/module_type` 参数注释：按 `docs/vendor/VENDOR_INDEX.md` 指向的本地 vendor 资料，WAVE ROVER 是 `main_type=1,module_type=0`；`main_type=2` 只作为 UGV02/UGV Rover 覆盖，不再写成现场推荐口径。
- `docs/hardware/wave_rover_json_bridge.md`
  - 把 2026-07-03 `main_type=2` A/B 结论改成历史证据，不再作为当前目标状态。
  - 明确 `json_cmd.h` 定义 `1-WAVE ROVER, 2-UGV02, 3-UGV01`，`ugv_config.h` 默认 `mainType=1`，现场重启/deploy 应固化 `main_type=1,module_type=0`。
- `docs/product/pc_tools_workstation.md`
  - 同步 PC 当前硬件口径：WAVE ROVER 主类型已纠正为 `1/0`，不改变 `0.0.0.0:7001`，不触碰 clash，不把 `T=1001 L/R=0/0` 伪装成 wheel raw 非零。

## 验证结果

- 已读 vendor 资料入口：
  - `docs/vendor/VENDOR_INDEX.md`
  - `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
  - `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_config.h`
  - `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- 上位机当前进程复核：
  - `/esp32_bridge main_type=2,module_type=0,command_mode=pwm,command_transport=http,wave_rover_http_base_url=http://192.168.1.3`，这是历史手工参数覆盖，和本项目 WAVE ROVER 推荐口径不一致。
- 已对 ESP32 HTTP 控制面执行非运动修正：
  - `T=900 main=1,module=0`
  - `T=138 L=1,R=1`
  - `T=139` 读回 `L=1,R=1`
- PC 7001 WASD/手控短脉冲复测：
  - `POST /api/robot-control/base/manual`，`direction=forward,speed_mps=0.06,duration_ms=450,command_mode=ros`
  - `POST /api/robot-control/base/manual`，`direction=back,speed_mps=0.06,duration_ms=450,command_mode=ros`
  - 两次均返回 `proxy_status=command_forwarded`、`command_result_ok=true`、`stop_result_ok=true`、`command_raw_lr_nonzero_proven=true`、`motion_signal_observed=true`、`motion_signal_source=imu_attitude_delta`。
  - 同窗口仍为 `wheel_feedback_lr_nonzero_proven=false`、`wheel_feedback_latest_raw_left=0`、`wheel_feedback_latest_raw_right=0`。
- PC 7001 live-summary 复核：
  - `map_display_primary_url=/map`
  - `map_display_default_zoom_percent=800%`
  - `map_current_visible=true`
  - `path_current_visible=true`
  - `route_target_current_visible=true`
  - `radar_map_points_current_visible=true`
  - `keyboard_continuous_motion_verified=true`
- PC 7001 camera status 复核：
  - `status=source_first_frame_failed`
  - `source_diagnosis_status=uvc_no_frame_not_exclusive`
  - `source_usage_owner_count=0`
  - `exclusive_camera_claim=false`
  - `camera_hardware_action_required=true`
  - `camera_input_signal_check_required=true`
  - `selected_device=/dev/video1`
  - `last_failure_reason=first_frame_total_timeout`
- 测试：
  - `python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py onboard/src/ros2_trashbot_hardware/test/test_hardware_diagnostics_proof.py`：40 tests OK。
  - `python3 -m pytest ...` 未运行成功，本地 Python 环境没有 `pytest` 模块；已用同文件 `unittest` 路径覆盖硬件协议测试。

## 剩余风险

- 现场常驻 `/esp32_bridge` 进程仍带历史手工参数 `main_type:=2,module_type:=0`。本轮已通过 ESP32 HTTP 非运动写回 `main=1,module=0`，但进程重启后仍可能被旧命令行覆盖；下一次 deploy/restart 必须移除该覆盖或显式改为 `1/0`。
- PC 地图大屏已读到地图、机器人位姿、Nav2 路线、雷达点和目标点；实时图传仍未达成首帧，当前证据指向 DV20/UVC 上游输入信号、摄像头/采集卡、线材、接口或供电，而不是浏览器独占。
- WASD/手控链路已经能通过 PC 7001 到上位机再到 ESP32 HTTP 写出非零命令，并观察到 IMU 动作信号；WAVE ROVER `T=1001 L/R` 仍为 `0/0`，不能声明 wheel raw L/R 非零完成。
