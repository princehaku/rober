# PC 共享画面 MJPEG 超时所见即所得

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - 共享 MJPEG relay 上游连接默认 8 秒超时，超时后返回 `camera_mjpeg_upstream_timeout`。
  - `/api/robot-control/camera/mjpeg/status` 和 robot-control summary 会记住最近一次超时失败。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏把 `camera_mjpeg_upstream_timeout` 翻译为“共享预览等不到上游画面；不是浏览器独占”。
- `pc-tools/workstation/test/catalog.test.ts`
  - 增加 hanging upstream 回归测试，确认 MJPEG 请求会快速失败，并且 status/summary 保留失败原因。
- `pc-tools/workstation/test/App.test.ts`
  - 增加 UI 回归测试，确认普通首屏不暴露内部 token，也不触发任何运动代理。
- `docs/product/pc_tools_workstation.md`
  - 同步记录共享画面超时的所见即所得口径。

## 验证结果

- 已通过：
  - `npm test -- --run test/catalog.test.ts --testNamePattern "MJPEG"`
  - `npm test -- --run test/App.test.ts --testNamePattern "shared camera|MJPEG upstream timeout|not-in-use camera"`
- `npm test -- --run test/App.test.ts`
  - 通过：`Tests 152 passed (152)`。
- `npm test -- --run test/catalog.test.ts`
  - 通过：`Tests 114 passed (114)`。
- `npm run lint`
  - 通过：`eslint .` 无报错。
- `npm run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
  - Vite 仍提示产物 chunk 大于 500 kB，这是既有体积提示。
- PC Node 已重启到 `0.0.0.0:7001`，`node` 监听 `*:7001`。
- live 只读验证：
  - `GET /api/robot-control/camera/mjpeg?baseUrl=http://192.168.1.11:8787` 在约 8 秒返回 HTTP 502。
  - 响应体：`error=camera_mjpeg_upstream_timeout`、`robot_control_executed=false`。
  - `GET /api/robot-control/camera/mjpeg/status` 显示 `last_failure_reason=camera_mjpeg_upstream_timeout`、`upstream_active=false`、`client_count=0`。
  - summary 同步显示 `shared_preview_last_failure_reason=camera_mjpeg_upstream_timeout`，相机源仍为 `source_first_frame_failed`、`source_usage_status=not_in_use`。

## 剩余风险

- 本轮不修复真实 `/dev/video1` 无首帧根因，只让新页面看到明确失败态。
- 本轮不执行真实底盘运动、Nav2 路线或 free-roam start。
