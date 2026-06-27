# Camera MJPEG Status Health Timeout

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：导出 `ROBOT_CONTROL_CAMERA_HEALTH_TIMEOUT_MS`，让 summary 与其他只读 camera health 消费方共享同一读取预算。
- `pc-tools/workstation/src/server/index.ts`：`GET /api/robot-control/camera/mjpeg/status` 读取 `/api/camera/health` 时改用 8 秒 camera health 预算，避免真实上位机 health 慢于 2.5 秒时丢掉 `source_diagnosis_*`。
- `pc-tools/workstation/test/catalog.test.ts`：新增慢 health 回归测试，模拟 `/api/camera/health` 2.7 秒返回 `source_first_frame_failed/uvc_no_frame_not_exclusive`，验证 status 仍返回诊断且不访问 `/api/camera/mjpeg`。
- `docs/product/pc_tools_workstation.md`：同步记录共享 MJPEG 状态的只读 health 窗口口径。

## 验证结果

- `npm test -- --run test/catalog.test.ts -t "MJPEG status"`：通过，4 个用例通过。
- `npm test -- --run test/catalog.test.ts -t "slower camera health"`：通过，1 个用例通过，耗时约 2.74 秒，证明旧 2.5 秒窗口覆盖不到的诊断现在能返回。
- `npm test -- --run`：通过，2 个测试文件、299 个用例全部通过。
- `npm run build`：通过，产物为 `dist/assets/index-Br5SB-PE.js` 和 `dist/assets/index-DkzBjvNI.css`；Vite 仍提示主 chunk 超过 500 kB，这是既有体积告警。
- `npm run lint`：通过。
- `git diff --check`：通过。
- PC Node 已用 `HOST=0.0.0.0 PORT=7001 npm run api` 重启；`lsof` 显示 Node 监听 `*:7001`。
- live `GET http://127.0.0.1:7001/api/robot-control/camera/mjpeg/status`：返回 `proxy_status=status_loaded`、`client_count=0`、`upstream_active=false`、`last_failure_reason=camera_source_first_frame_failed`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、`source_diagnosis_not_exclusive=true`，并显示“不是页面独占：USB Composite Device: DV20 USB ... UVC 设备没有输出视频帧”。该 live 读数证明 status 端点只读 health 后能稳定带出源诊断，且没有打开 MJPEG 上游流。

## 剩余风险

- 本轮只修 PC Node 的只读状态一致性，不修复真实 DV20/UVC 无首帧。live 摄像头若仍不出帧，状态会稳定提示“不是独占 / UVC 无帧”，但不会凭空生成可见画面。
