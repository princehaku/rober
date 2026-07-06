# PC camera V4L2 control reset recovery

sprint_type: micro

## 实际改动

- `onboard/scripts/camera_usb_recovery_smoke.py` 新增 V4L2 控制项默认值恢复，默认在相机 USB recovery 的 reauthorize/audio rebind 后执行。
- `onboard/scripts/upper_robot_api.py`、PC Node recovery proxy、共享合同和 catalog 测试同步支持 `skip_control_reset` 白名单与 `v4l2_control_reset_ok` / `v4l2_control_reset_applied_count` 读回。
- 更新 `pc-tools/README.md`、`docs/product/pc_tools_workstation.md` 和 `docs/vision/board_camera_publisher.md`。

## 验证结果

- `python3 -m unittest onboard.tests.test_camera_usb_recovery_smoke onboard.scripts.test_camera_usb_recovery_smoke`：通过，11 tests OK。
- `cd pc-tools/workstation && npm test -- test/catalog.test.ts --run`：通过，195 tests OK。
- `cd pc-tools/workstation && npm test -- test/robotControlSummary.test.ts --run`：通过，18 tests OK。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍提示单个 chunk 超过 500 kB，这是既有体积警告。
- 上车部署：`scp -P 7878` 更新 `camera_usb_recovery_smoke.py` 与 `upper_robot_api.py` 到 `root@192.168.1.11:/root/rober/onboard/scripts/`；远端 `python3 -m py_compile` 通过；`trashbot-upper-robot-api.service` 和 `trashbot-local-webrtc-camera.service` 均为 active。
- 真实 7001 recovery：`v4l2_control_reset_ok=true`、`v4l2_control_reset_applied_count=10`、`usb_video_speed=480M`、`streamon_success_observed=true`、`zero_byte_no_frame_observed=true`、`frame_observed=false`。
- 真实 7001 WASD 复验：低速 `forward` 返回 raw `164/164`，低速 `backward` 返回 `-164/-164`，两次 stop 均转发成功；live-summary 返回 `keyboard_continuous_forwarded_pulses=2`、`keyboard_stop_settled_after_pulse=true`、`command_raw_lr_nonzero_proven=true`。
- 真实 7001 live-summary：`map_current_visible=true`、`path_current_visible=true`、`radar_map_points_visible=true`、`route_target_current_visible=true`、`delivery_success=true`。

## 剩余风险

- 实时图传仍未恢复：控制项默认值恢复、USB reauthorize、audio rebind、UVC quirks reset、OpenCV/V4L2/ffmpeg 矩阵均未读到任何真实首帧。
- 当前证据继续指向 DV20 上游输入信号、USB 线/接口/供电、采集设备本体，或需要接入 known-good UVC 对照；PC 不生成占位图、不伪造相机 ready。
- Wheel raw `T=1001 L/R` 仍未非零，本轮 WASD 只证明 PC 到底盘 command raw L/R 非零与 stop 生效。
