# PC Camera MJPEG Retry

sprint_type: micro

## 实际改动

- 普通首屏 MJPEG 共享预览在浏览器图片加载失败后，会等待 5 秒并自动追加 `retry=N` 重新请求同一个只读 `/api/robot-control/camera/mjpeg` 端点。
- `load`、base URL 切换、手动关闭画面和组件卸载都会清掉 retry timer，避免用户关掉画面后后台继续重连。
- 补充 App 测试，验证 MJPEG error 后 5 秒 URL 变为 `retry=1`，且没有发送 manual、free-roam 或 Nav2 execute。
- 同步更新 `docs/product/pc_tools_workstation.md`。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts`，`1 passed / 153 passed`。
- 通过：`npm run lint`。
- 通过：`npm run build`，Vite 仍提示主 chunk 超过 500 kB 的既有体积警告。
- 通过：重启 `0.0.0.0:7001` 后 Node 监听 `*:7001`，`/api/health` 返回 `pc_only_readonly_workstation`。
- 通过：live `GET /api/robot-control/camera/mjpeg/status?baseUrl=...` 返回 `shared_capture=true`、`exclusive_camera_claim=false`、`robot_control_executed=false`。
- 通过：live `GET /api/robot-control/camera/mjpeg?baseUrl=...&retry=1` 返回 HTTP 502，body 为 `camera_mjpeg_upstream_timeout`、`robot_control_executed=false`；随后 status 记录 `last_failure_reason=camera_mjpeg_upstream_timeout`。

## 剩余风险

- 本轮让页面在摄像头恢复后能自动重试共享预览，但不修复当前 DV20 `/dev/video1` 首帧读取失败的硬件/驱动根因。
