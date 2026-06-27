# PC Camera MJPEG Failure Reason WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - PC 共享 MJPEG relay 在远端 `/api/camera/mjpeg` 非 multipart 或 HTTP 非 200 时，解析远端 JSON。
  - 优先保留 `relay.last_failure_reason`、`failure_reason` 或 `error`，避免把上位机已经知道的 503/相机后端失败统一压成 `camera_mjpeg_proxy_failed`。
  - 默认 MJPEG 上游等待窗口从 8s 调整为 12s，略长于上位机 8787 relay 的 8s 窗口，避免 PC 抢先 abort 丢失远端失败 JSON。
  - 将远端 `Timeout on reading data from socket` 归一为 `camera_mjpeg_upstream_timeout`，避免普通 UI 暴露英文 socket 错误。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏把 `camera_mjpeg_http_status_*` 和 `camera_backend_unavailable` 翻译为“上游没有返回可用画面，不是浏览器独占”。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 PC MJPEG proxy 保留上位机 relay 内层失败原因。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖普通首屏不泄露 `camera_mjpeg_http_status_503`，仍显示人话失败归因。
- `docs/product/pc_tools_workstation.md`
  - 同步记录共享 MJPEG 失败原因透传和安全边界。

## 验证结果

- `npm test -- catalog.test.ts --testNamePattern "camera MJPEG status and summary remember"`：通过，1 passed / 121 skipped。
- `npm test -- App.test.ts --testNamePattern "live not-in-use camera first-frame failure"`：通过，1 passed / 163 skipped。
- `npm test -- catalog.test.ts --testNamePattern "camera MJPEG status and summary remember|times out hanging upstream|normalizes upstream socket"`：通过，3 passed / 120 skipped。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 仍有既有 chunk size warning。
- `npm test`：通过，2 test files / 287 tests passed。
- `git diff --check`：通过，无 whitespace error。
- 7001 live camera MJPEG/status smoke：`/api/robot-control/camera/mjpeg?baseUrl=http://192.168.1.11:8787` 返回 fail-closed HTTP 502；status 返回 `last_failure_reason=camera_mjpeg_upstream_timeout`、`last_remote_http_status=502`；summary 返回 `camera.status=source_first_frame_failed`、`source_readiness=first_frame_failed`、`source_failure_reason=capture_read_returned_false`、`source_usage_status=not_in_use`、`shared_preview_last_failure_reason=camera_mjpeg_upstream_timeout`。
- 运行态：7001 LaunchAgent 重启后继续监听 `0.0.0.0:7001`；未修改 Clash 或系统代理。

## 剩余风险

- 本轮只修正 PC 端对共享 MJPEG 失败的真实归因；它不能让没有输出帧的 `/dev/video1` 变成有画面。
- live 只读/采帧证据显示 8088 `/mjpeg` 返回 503，`v4l2-ctl` 对 `/dev/video1` 与 `/dev/video2` 采样均为 0 字节；真实恢复画面仍需要检查 DV20 输入源、USB 线/供电、采集卡模式或替换 known-good UVC。
- 该改动不触发相机探针、manual、Nav2、delivery、free-roam start、stop 或 `/cmd_vel`。
