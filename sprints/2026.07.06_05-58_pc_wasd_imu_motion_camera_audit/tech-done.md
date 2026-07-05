# 2026.07.06 05:58｜pc_wasd_imu_motion_camera_audit｜PC WASD 运动信号与相机复验

## sprint_type

micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - 将 WAVE ROVER `T=1001` IMU roll/pitch 运动信号阈值从 `1.0°` 调整为 `0.35°`。
  - 该阈值只用于 PC WASD/低速短脉冲判断 `motion_signal_observed=imu_attitude_delta`，不替代 wheel raw L/R 非零。
  - 硬件字段依据 `docs/vendor/VENDOR_INDEX.md`、WAVE ROVER `json_cmd.h` 和 `IMU_ctrl.h`。
- `onboard/tests/test_upper_robot_api.py`
  - 新增 0.5 度级短脉冲 IMU 姿态变化测试，确认它能点亮运动信号但不点亮 wheel raw L/R。
- `pc-tools/README.md`
- `docs/product/pc_tools_workstation.md`
- `docs/product/pc_free_roam_mapping_design.md`
- `onboard/README.md`
  - 同步当前口径：PC WASD 当前可通过 command raw + IMU 运动信号 + stop 证明可动；图传仍卡 DV20 无视频帧。

## 验证结果

- 本地单测：`python3 -m unittest onboard.tests.test_upper_robot_api`
  - `Ran 104 tests in 0.247s`
  - `OK (skipped=1)`
- 上车部署：
  - 已通过 `scp -P 7878 onboard/scripts/upper_robot_api.py root@192.168.1.11:/root/rober/onboard/scripts/upper_robot_api.py` 部署。
  - 已重启 `trashbot-upper-robot-api.service`，8787 恢复监听，进程为 `/root/rober/onboard/scripts/upper_robot_api.py --host 0.0.0.0 --port 8787 ...`。
- PC WASD/手控复验：
  - `POST /api/robot-control/base/manual`，`direction=forward`、`speed_mps=0.12`、`duration_ms=800`、`command_mode=ros`。
  - 返回 `proxy_status=command_forwarded`、`remote_http_status=200`、`command_result_ok=true`、`stop_result_ok=true`。
  - 返回 `command_raw_lr_nonzero_proven=true`、`command_raw_latest_left/right=164/164`。
  - 返回 `feedback_during_motion_t1001_frame_count=80`、`motion_signal_observed=true`、`motion_signal_source=imu_attitude_delta`。
  - 随后 `POST /api/robot-control/base/stop` 返回 `proxy_status=command_forwarded`。
  - `GET /api/robot-control/live-summary` 返回 `status=ready_for_motion`、`keyboard_motion_verified=true`、`keyboard_stop_settled_after_pulse=true`、`keyboard_continuous_motion_verified=true`。
- 相机复验：
  - DV20 `/dev/video1` 枚举正常，USB `480M`，无页面独占。
  - PC first-frame probe 返回 `probe_total_timeout / uvc_no_frame_not_exclusive`。
  - USB recovery 返回 `streamon_success_zero_byte_no_frame / high_speed_zero_byte_no_frame`。
  - 停止 8088 服务后，独占 `v4l2-ctl` 对 `MJPG@640x480`、`MJPG@1280x720`、`MJPG@1920x1080`、`YUYV@320x240`、`YUYV@640x480` 均 `select timeout` 且输出 0 字节。
  - `ffmpeg` 对 `MJPG@1280x720`、`MJPG@1920x1080` 等待首帧超时，没有生成可用图片。
  - 已恢复 `trashbot-local-webrtc-camera.service`，8088 继续监听。

## 剩余风险

- PC 实时地图和 WASD 当前可用；实时图传仍未达成，因为 DV20 UVC 设备枚举正常但不输出视频帧。
- 当前证据排除了 PC 页面独占、多人预览独占、8088 服务独占、常用分辨率选择和 USB 低速问题；剩余动作是检查 DV20 输入信号、线/接口/供电，或换 known-good UVC 后复测。
- WAVE ROVER `T=1001` wheel raw L/R 仍为 `0/0`，本轮只证明命令链路和 IMU/车体运动信号，不宣称 wheel raw 闭环完成。
