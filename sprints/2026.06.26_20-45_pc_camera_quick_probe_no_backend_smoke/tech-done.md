# PC 相机首帧快速检查

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`：普通首屏 `POST /api/robot-control/camera/first-frame/probe` 不再默认向上车端发送 `include_backend_smoke=true`，改为固定快速首帧检查 `{include_backend_smoke:false, timeout_s:3, read_call_timeout_s:4}`，PC 侧 fetch 超时从 60 秒收敛为 12 秒。
- `pc-tools/workstation/test/catalog.test.ts`：新增回归测试，锁定普通首屏相机 probe 发给上车端的请求体，防止以后重新默认启动 backend smoke；同时断言失败响应仍保持 fail-closed，不提升控制许可。
- `docs/product/pc_tools_workstation.md`：同步记录现场口径：PC 共享 MJPEG relay 不独占相机；当前相机问题是 `/dev/video1` 可打开但读帧超时，普通首屏不应再制造 backend smoke 占用。

## 验证结果

- `cd pc-tools/workstation && npm test -- catalog.test.ts`：通过，105 tests。
- `cd pc-tools/workstation && npm test`：通过，2 files / 242 tests。
- `cd pc-tools/workstation && npm run build`：通过；仅 Vite chunk size warning。
- 已重启 PC Node：`HOST=0.0.0.0 PORT=7001 ./node_modules/.bin/tsx src/server/index.ts`，`lsof` 确认监听 `*:7001`。
- 真实 PC 7001 quick probe 复测：`POST /api/robot-control/camera/first-frame/probe` 约 5.3 秒返回，`proxy_status=probe_failed`、`remote_http_status=503`、`status=first_frame_timeout`、`failure_reason=capture_read_call_timeout`、`backend_smoke_status=not_requested`。
- 真实 PC 7001 MJPEG 状态复测：`client_count=0`、`upstream_active=false`、`shared_capture=true`、`exclusive_camera_claim=false`。
- 真实上车端复查：没有残留 `camera_first_frame_probe` 或 `ffmpeg /dev/video1` 进程；`/api/camera/health` 返回 `source_usage.status=not_in_use`、`owner_count=0`、`last_successful_frame=null`。

## 剩余风险

- 本轮修复的是 PC 普通首屏检查画面不再制造长时间 backend smoke 占用，并把失败快速反馈给用户；它没有修好摄像头硬件读帧超时。
- 当前相机仍未证明有真实画面：`/dev/video1` 可打开但 `capture.read()` 超时，后续需要继续查 USB 摄像头输入、供电、格式或驱动。
- 自动扫图/free-roam start 仍应在相机首帧未证明时保持拒绝；雷达不是基础移动硬门禁，但相机和建图画面所见即所得仍是建图前置条件。
