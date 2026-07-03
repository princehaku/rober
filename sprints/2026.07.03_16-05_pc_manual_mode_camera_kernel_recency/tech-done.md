# 2026-07-03 16:05 PC Manual Mode / Camera Kernel Recency

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`：PC 手控代理新增显式 `command_mode` 透传，允许 `ros|speed|pwm`；未传时仍默认 `ros`，普通页面 WASD 行为不变。
- `onboard/scripts/local_webrtc_camera_smoke.py`：UVC dmesg 诊断增加最近枚举时间围栏，同一个 USB 地址重用后，早于最近 `Found UVC/authorized to connect` 的旧错误归为 stale，不再当作当前传输错误。
- 补充测试：PC catalog 覆盖显式 `command_mode=speed` 不被改写；相机 smoke 覆盖同地址旧错误在重新枚举后归为 stale。
- 同步更新 `docs/product/pc_tools_workstation.md`、`docs/product/pc_free_roam_mapping_design.md`、`docs/hardware/wave_rover_json_bridge.md`。

## 验证结果

- 通过：`python -m py_compile onboard/scripts/local_webrtc_camera_smoke.py && python -m unittest onboard.tests.test_local_webrtc_camera_smoke`，42 tests passed。
- 通过：`npm test -- --run test/catalog.test.ts -t "Robot Control manual proxy"`，2 tests passed。
- 通过：`npm test`，3 files / 439 tests passed。
- 通过：`npm run build`，仅保留既有 Vite chunk size warning。
- 通过：`npm run lint`。
- 通过：上位机已同步 `local_webrtc_camera_smoke.py` 并重启 `trashbot-local-webrtc-camera.service`，服务 active。
- 通过：PC Node 已重启并监听 `*:7001`。
- 通过：真实 PC 7001 请求 `command_mode=speed` 后，上位机 command debug 记录 `vendor_command={"T":1,"L":0.04,"R":0.04}`，并自动写出 `T=1/T=11/T=13` stop。
- 通过：真实相机 health 返回 `uvc_kernel_diagnostics_status=uvc_kernel_seen_without_current_transport_errors`、`transport_error_count=0`、`stale_transport_error_count=50`、`camera_usb_speed=480M`。
- 通过：无抢占首帧 probe 显示 OpenCV 可打开 `/dev/video1`，但 v4l2 mmap、ffmpeg、MJPG/YUYV/current 九个后端均 `no_frame_timeout` 且输出 0 字节。

## 剩余风险

- 实时图传仍无首帧；当前收窄为 UVC 枚举正常但没有视频 buffer 到达主机，下一步需换 known-good UVC、查线/供电/设备固件或内核兼容。
- `T=1/T=11/T=13` 都已证明可写出，但 `T=1001 L/R` 仍为 `0/0`；不能宣称 wheel raw 非零、完整 Nav2 行程或 delivery success。
- 两个 2026-06-11 artifact JSON 是本轮前已有工作区脏文件，本轮未 stage、未修改、未提交。
