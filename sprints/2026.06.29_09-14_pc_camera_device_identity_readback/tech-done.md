# PC Camera Device Identity Readback

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `cameraSelectedCandidateSummary()` 现在会从 camera health 顶层字段、`media_diagnostics.source_diagnosis` 和 `media_diagnostics.source_usage` 回填 `selected_path`、`selected_name`、`selected_is_uvc_or_usb`。
  - `readback_summary.camera.selected_path` 不再只依赖 `current_selection/source_summary`，也会使用 `health.selected_path`、`source_diagnosis.selected_path`、`source_usage.device` 或 `video_source`。
- `pc-tools/workstation/src/server/index.ts`、`pc-tools/workstation/src/shared/contracts.ts`
  - `/api/robot-control/camera/mjpeg/status` 的只读 source diagnosis 也同步输出 `selected_path`、`selected_name`、`selected_is_uvc_or_usb`、`source_usage_status` 和 `source_usage_owner_count`。
  - Robot Control summary 的 MJPEG overlay 会消费这些结构化字段；当 summary 直接读 camera health/devices 被 502 fail-closed 时，仍能从本机 status overlay 输出设备身份。
- `pc-tools/workstation/test/catalog.test.ts`
  - 补充 devices readback 为空但 health/source_diagnosis 带设备身份的用例，锁定 `/dev/video1`、设备名、UVC 标识和不是独占的无帧诊断。
  - 扩展 MJPEG status/summary 无帧测试，确认 summary 也暴露结构化设备身份。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录该变化只消费只读 camera health/devices/status，不打开第二条相机上游、不重启 camera service、不触发任何运动命令。

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "camera device identity|MJPEG status derives non-exclusive|source first-frame failure|infers UVC sibling"`。
- 已通过：`npm --prefix pc-tools/workstation test`，结果 `376 passed`。
- 已通过：`npm --prefix pc-tools/workstation run build`，Vite 仍只有既有 chunk size warning。
- 已重启本机 PC API 到 `0.0.0.0:7001`，当前监听进程为 `node` PID `70463`。
- 已只读验证真实上车 `http://192.168.1.11:8787`：
  - `GET /api/robot-control/summary` 的 `readback_summary.camera` 返回 `selected_path=/dev/video1`、`selected_name=USB Composite Device: DV20 USB`、`selected_is_uvc_or_usb=true`、`source_usage_status=not_in_use`、`source_usage_owner_count=0`。
  - `GET /api/robot-control/camera/mjpeg/status` 返回同一设备身份，且保留 bus 后缀供高级诊断。
  - camera WYSIWYG 仍正确显示“不是页面独占，但 UVC 设备没有输出视频帧”。

## 剩余风险

- 本轮只证明 PC summary 能结构化暴露当前相机设备身份；真实摄像头仍未出首帧，live 根因仍是 UVC 设备没有输出视频帧，不是页面独占。
- 没有执行 camera restart、Nav2 goal、keyboard manual、free-roam start/stop、radar start/stop 或 `/cmd_vel`。
