# PC Camera Shared Preview Summary

sprint_type: micro

## 实际改动

- PC Robot Control summary 的 `readback_summary.camera` 合入 MJPEG relay 只读状态，新增 `shared_preview_client_count`、`shared_preview_upstream_active`、`shared_preview_content_type_loaded`、`shared_preview_shared_capture`、`shared_preview_exclusive_camera_claim`。
- `preview_status` 不再固定为 `idle_not_started`，而是根据 PC Node 当前共享 relay 推导为 `idle_not_started`、`starting_local_peer` 或 `streaming`。
- PC Node 会在 MJPEG 上游失败时记录最近失败原因、远端 HTTP 状态和时间，并在 `camera/mjpeg/status` 与 summary 的 camera readback 中同步展示。
- `RobotControlConsolePanel` 的普通“共享画面”文案在单独 status 端点未返回 loaded 时，回退使用 summary 中的共享预览状态，避免现场只看到“未读取到共享流状态”。
- 保持只读边界：summary 不创建 MJPEG client，不打开摄像头，不执行 camera probe、Nav2、manual、keyboard、delivery、stop 或 `/cmd_vel`。
- 更新 workstation shared contracts、App fixture、catalog/App 测试和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- App.test.ts`
  - `Test Files 1 passed (1)`
  - `Tests 138 passed (138)`
- 通过：`cd pc-tools/workstation && npm test -- catalog.test.ts`
  - `Test Files 1 passed (1)`
  - `Tests 106 passed (106)`
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - Vite 仍有既有 `Some chunks are larger than 500 kB` warning，本轮无新增构建失败。
- 通过：`git diff --check`
- 通过：PC Node 已重启到 `0.0.0.0:7001`。
- 真实上位机 live summary 初始状态：
  - `readback_summary.camera.video_source=/dev/video1`
  - `readback_summary.camera.preview_status=idle_not_started`
  - `shared_preview_client_count=0`
  - `shared_preview_upstream_active=false`
  - `shared_preview_content_type_loaded=false`
  - `shared_preview_shared_capture=true`
  - `shared_preview_exclusive_camera_claim=false`
- 真实上位机 MJPEG 短拉结果：
  - `GET /api/robot-control/camera/mjpeg?baseUrl=http://192.168.1.11:8787` 返回 JSON 错误体，不是 multipart。
  - 错误体：`camera_mjpeg_proxy_failed`
  - `remote_http_status=502`
  - 随后 `camera/mjpeg/status` 与 summary 都保留最近失败：`last_failure_reason=camera_mjpeg_proxy_failed`、`last_remote_http_status=502`。
  - `safe_to_control=false`、`robot_control_executed=false` 保持不变。

## 剩余风险

- 本轮证明的是 PC summary 能解释共享 MJPEG relay 状态和最近上游失败；真实画面像素是否可见仍要看浏览器 `<img>/<video>` load/frame 事件或首帧 probe。
- 当前 live smoke 证明 PC relay 可正确暴露失败原因；但真实上位机 `/api/camera/mjpeg` 当前返回 502，实时画面仍未出图，需要后续继续定位上车 camera service/MJPEG endpoint。
