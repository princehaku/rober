# 相机共享 MJPEG 快速失败

## sprint_type

micro

## 实际改动

- `onboard/scripts/local_webrtc_camera_smoke.py`
  - 将共享 MJPEG 自动预览的首帧预算从约 `9s` 收紧到约 `5s`。
  - 单次格式尝试从 `1.2s` 收紧到 `0.75s`，第一段关键格式总预算 `3.8s`，index/V4L2 打开兜底预算 `1.2s`。
  - 设计边界保持不变：不发送黑帧、不发送 placeholder，只有真实首帧才输出 multipart MJPEG。
- `onboard/tests/test_local_webrtc_camera_smoke.py`
  - 更新共享 MJPEG 预算单测，要求总失败窗口不超过 `5s`，同时仍覆盖多个格式。
- `docs/product/pc_tools_workstation.md`
  - 同步普通 PC 图传口径：MJPEG 是短路实时预览入口，无帧时快速返回结构化失败，完整诊断仍走 first-frame probe / USB recovery。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步建图边界：快失败避免首页一直卡在打开画面，但建图相机首帧仍必须由真实帧证明。

## 验证结果

- 通过：`python3 -m unittest onboard.tests.test_local_webrtc_camera_smoke onboard.scripts.test_local_webrtc_camera_smoke_health`，47 tests passed。
- 通过：上位机部署后 `trashbot-local-webrtc-camera.service` active，监听 `0.0.0.0:8088`。
- 通过：PC 7001 live `GET /api/robot-control/camera/mjpeg?baseUrl=http://192.168.1.11:8787` 在 `time_total=5.983123s` 返回 `http_code=502`、`content_type=application/json`，不再出现 10s 无首字节等待。
- 通过：MJPEG 失败 body 返回 `error=first_frame_total_timeout`、`safe_to_control=false`、`robot_control_executed=false`。
- 通过：PC 7001 live `GET /api/robot-control/camera/mjpeg/status` 返回 `status=source_first_frame_failed`、`last_failure_reason=first_frame_total_timeout`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、`source_diagnosis_not_exclusive=true`、`camera_usb_speed=480M`、`shared_preview_everyone_can_join=true`、`camera_blocks_free_move=false`。

## 剩余风险

- 本轮没有让 DV20 UVC 产出真实图像帧；当前真实问题仍是 `480M` high-speed 但 UVC STREAMON 0 字节无帧。
- 普通 PC 页面现在能更快显示真实失败状态，但“实时图传可见”仍未完成；下一步需要检查摄像头输入、线/口/供电或换 known-good UVC 复测。
- 低速自由移动、PC WASD 和图上路线不依赖相机首帧；建图验收仍依赖真实相机首帧。
