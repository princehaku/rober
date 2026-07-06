# PC camera userptr/no-query recovery

sprint_type: micro

## 实际改动

- `onboard/scripts/camera_usb_recovery_smoke.py` 的 STREAMON 矩阵扩展为 `mmap`、`userptr` 和 `mmap + --stream-no-query`。
- PC recovery proxy 和类型合同新增 `userptr_zero_byte_no_frame_observed`、`no_query_zero_byte_no_frame_observed`、`userptr_attempt_count`、`no_query_attempt_count`。
- 更新 PC README、产品文档和视觉图传文档，记录 userptr/no-query 仍无帧的真实结论。

## 验证结果

- `python3 -m unittest onboard.tests.test_camera_usb_recovery_smoke onboard.scripts.test_camera_usb_recovery_smoke onboard.tests.test_camera_first_frame_probe`：通过，24 tests OK。
- `cd pc-tools/workstation && npm test -- test/catalog.test.ts --run`：通过，195 tests OK。
- `cd pc-tools/workstation && npm test -- test/robotControlSummary.test.ts --run`：通过，18 tests OK。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍提示单个 chunk 超过 500 kB，这是既有体积警告。
- 上车部署：`scp -P 7878 onboard/scripts/camera_usb_recovery_smoke.py root@192.168.1.11:/root/rober/onboard/scripts/`；远端 `python3 -m py_compile` 通过；`trashbot-upper-robot-api.service` 与 `trashbot-local-webrtc-camera.service` 均为 active。
- 真实 7001 recovery：`userptr_attempt_count=2`、`userptr_zero_byte_no_frame_observed=true`、`no_query_attempt_count=2`、`no_query_zero_byte_no_frame_observed=true`、`streamon_success_observed=true`、`frame_observed=false`。
- 真实 7001 live-summary：`map_current_visible=true`、`path_current_visible=true`、`radar_map_points_visible=true`、`route_target_current_visible=true`、`delivery_success=true`、`keyboard_continuous_forwarded_pulses=2`、`keyboard_stop_settled_after_pulse=true`、`command_raw_lr_nonzero_proven=true`。

## 剩余风险

- 实时图传仍未恢复：DV20 `/dev/video1` 在 USB `480M` 下能 STREAMON，但 mmap、userptr、no-query、OpenCV、ffmpeg 都没有真实首帧。
- 当前剩余方向是 DV20 上游输入信号、USB 线/接口/供电、采集设备本体，或 known-good UVC 对照；PC 不生成占位图、不伪造相机 ready。
- Wheel raw `T=1001 L/R` 仍未非零，本轮 WASD 继续只证明 PC 到底盘 command raw L/R 非零与 stop 生效。
