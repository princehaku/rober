# Tech Done

sprint_type: micro

## 实际改动

- 将 PC Robot Control summary 的 `/api/camera/devices` 只读端点预算从 `SLOW_READBACK_TIMEOUT_MS` 提升到 `HEAVY_READBACK_TIMEOUT_MS`，与 `/api/camera/health` 对齐。
- 新增回归测试：模拟 `/api/camera/devices` 5.2 秒后返回合法 JSON，summary 必须读成 `loaded`，连接状态保持 `readable`，不能出现 `camera_devices:fetch_timeout_4000ms`。
- 更新 `pc-tools/README.md`，记录 camera devices 是只读设备枚举，不创建 preview/offer/capture；慢一拍时不能把已知非独占无首帧诊断降级成整车连接异常。

## 验证结果

- `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "slow camera devices|slow base readback"`：通过，2 个相关用例通过。
- `npm --prefix pc-tools/workstation test`：通过，2 个 test files、373 个用例通过。
- `npm --prefix pc-tools/workstation run build`：通过，`tsc` app/server 与 Vite build 均完成；仅保留既有 chunk size warning。
- 7001 已重启到新代码，`lsof` 显示监听 `TCP *:7001`；live `GET /api/robot-control/summary` 返回 `robot_api_connection.status=readable`、15 个端点 loaded、0 failed，`camera_devices.request_status=loaded`。
- 本轮真实只读复核：
  - 直连 `http://192.168.1.11:8787/api/camera/devices` 在约 0.36s 返回 HTTP 200 合法 JSON。
  - 直连 `http://192.168.1.11:8787/api/camera/health` 在约 0.51s 返回 HTTP 200 合法 JSON，仍显示 `/dev/video1` `source_first_frame_failed`、`source_diagnosis.status=uvc_no_frame_not_exclusive`。

## 剩余风险

- 该改动只改善 PC summary 对只读 camera devices 慢枚举的容忍度，不修复 UVC 实际无首帧问题。
- 本轮没有发真实运动命令，也没有调用 camera offer/MJPEG preview start；摄像头真实画面仍需现场检查 USB、摄像头输入/供电或换 known-good UVC。
