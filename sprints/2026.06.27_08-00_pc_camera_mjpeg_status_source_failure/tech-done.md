# PC 共享画面状态补源无首帧事实

sprint_type: micro

## 设计结论

- 目标是“谁进页面都能看到实时预览或真实失败原因”。当 PC Node 刚重启且 MJPEG relay 还没有失败记录时，单独 status 端点不能显示成“没有失败”。
- status 端点可以短读上车 `/api/camera/health`，但不能创建 MJPEG client、不能打开运动控制、不能把 health 失败外推成画面可见。
- 当前 live 事实是 `/dev/video1` 已选中、`source_usage_owner_count=0`、`source_failure_reason=capture_read_returned_false`；这说明不是浏览器独占，而是相机源无首帧。

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - `GET /api/robot-control/camera/mjpeg/status` 在 relay 没有 last failure 时短读 `/api/camera/health`。
  - health 若证明 `source_first_frame_failed`、`first_frame_failed`、`capture_read_returned_false`、`capture_read_call_timeout` 或 `first_frame_timeout`，status 返回 `last_failure_reason=camera_source_first_frame_failed`。
  - 该 status 仍不创建 MJPEG client，不访问 `/api/camera/mjpeg`，不改变 `robot_control_executed=false`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏把 `camera_source_first_frame_failed` 翻译为“相机源没有输出首帧；设备可被共享读取，但当前没有真实画面”。
- `pc-tools/workstation/test/catalog.test.ts`
  - 更新 status readonly 测试：允许短读 health，但禁止打开 MJPEG stream。
  - 新增 source first-frame failure status 测试。
- `pc-tools/workstation/test/App.test.ts`
  - 新增普通首屏翻译回归，避免泄露 `camera_source_first_frame_failed` token。
- `docs/product/pc_tools_workstation.md`
  - 记录 shared MJPEG status 的源无首帧 overlay 边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "camera MJPEG status"`
  - `Test Files 1 passed (1)`
  - `Tests 3 passed | 115 skipped (118)`
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "camera source first-frame failure|shared camera MJPEG"`
  - `Test Files 1 passed (1)`
  - `Tests 4 passed | 150 skipped (154)`
- 通过：`cd pc-tools/workstation && npm run lint`
  - `eslint .`
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - Vite 保留既有 chunk size warning，本轮无新增构建失败。
- 通过：`cd pc-tools/workstation && npm test`
  - `Test Files 2 passed (2)`
  - `Tests 272 passed (272)`
- 通过：重启 PC Node 到 `0.0.0.0:7001`
  - `lsof` 显示 `node` PID `40041` 监听 `TCP *:7001`。
  - `curl http://127.0.0.1:7001/api/health` 返回 `mode=pc_only_readonly_workstation`、`pc_only=true`、`safe_to_control=false`。
  - `curl /api/robot-control/camera/mjpeg/status?baseUrl=http://192.168.1.11:8787` 返回 `status_loaded`、`client_count=0`、`upstream_active=false`、`exclusive_camera_claim=false`、`last_failure_reason=camera_source_first_frame_failed`、`last_remote_http_status=200`、`robot_control_executed=false`。

## 剩余风险

- 本轮只修 PC status 和普通首屏解释，不修复真实 UVC 无首帧。
- 当前真实相机仍需现场检查 DV20/UVC 输出、USB 线/供电、采集卡输入模式或替换 known-good UVC。
