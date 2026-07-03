# 2026-07-03 15:15 Camera 480M Transport / Base A-B

sprint_type: micro

## 实际改动

- 修复 PC 相机诊断：`480M` 高速 USB 但存在 `uvc_transport_error_not_exclusive` 时，`camera_hardware_action_required=true`，label 为 `检查USB/供电后复测`；`camera_usb_full_speed_detected` 仍只代表 `12M/full-speed`。
- 修复普通首屏相机硬件复验卡：480M transport error 不再提示“换高速 USB 口”，改为检查 USB 线、接口、摄像头供电或 known-good UVC。
- 补充测试覆盖 summary、MJPEG status 和 Vue 普通首屏 fallback。
- 更新 `docs/product/pc_tools_workstation.md`、`docs/product/pc_free_roam_mapping_design.md`、`docs/hardware/wave_rover_json_bridge.md`。

## 验证结果

- 通过：`npm test -- --maxWorkers=1 robotControlSummary.test.ts catalog.test.ts App.test.ts`，437 tests passed。
- 通过：`npm run build`，仅保留既有 Vite chunk size warning。
- 通过：PC Node 已运行在 `0.0.0.0:7001`。
- 通过：真实 PC summary 在首帧 probe 失败后返回 `camera_usb_speed=480M`、`camera_usb_full_speed_detected=false`、`camera_hardware_action_required=true`、`camera_hardware_action_label=检查USB/供电后复测`。
- 通过：相机共享预览仍返回 `shared_capture=true`、`exclusive_camera_claim=false`，所以不是浏览器页面独占。
- 通过：WAVE ROVER vendor 复核已查阅 `docs/vendor/VENDOR_INDEX.md`、`json_cmd.h`、`movtion_module.h`。现场 `T=900 main=1` A/B 后 `T=11 L/R=164` 仍未得到同窗口 `T=1001 L/R` 非零，已恢复 `main=2,module=0`。

## 剩余风险

- 摄像头已是 `480M`，但 DV20 UVC 仍无首帧并有 kernel UVC/USB transport error；下一步是检查线、接口、供电或换 known-good UVC。
- 底盘仍未证明同窗口 wheel raw `T=1001 L/R` 非零；自动驾驶不能宣称真实移动完成或 delivery success。
- 本轮未改变 Clash，PC Node 仍使用 `7001`，小车 API 默认仍为 `http://192.168.1.11:8787`。
