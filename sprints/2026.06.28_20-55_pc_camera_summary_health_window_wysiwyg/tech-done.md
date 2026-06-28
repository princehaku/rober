# 2026-06-28 20:55 PC camera summary health window WYSIWYG

sprint_type: micro

## 实际改动

- 修改 `pc-tools/workstation/src/server/index.ts`：`GET /api/robot-control/summary` 构造 camera MJPEG overlay 时，读取 `/api/camera/health` 的窗口从 600ms 改为复用 `ROBOT_CONTROL_CAMERA_HEALTH_TIMEOUT_MS`，与 `/api/robot-control/camera/mjpeg/status` 对齐。
- 修改 `pc-tools/workstation/src/server/robotControlSummary.ts`：当 health 同时给出 `source_first_frame_failed`、`source_usage.status=not_in_use/owner_count=0`，即使旧 `source_diagnosis.not_exclusive=false`，summary 也归一为 `uvc_no_frame_not_exclusive`。
- 修改 `pc-tools/workstation/test/catalog.test.ts`：扩展慢 health / 非独占无帧测试，覆盖 summary route 和 MJPEG status 口径一致。
- 更新 `docs/product/pc_tools_workstation.md`：记录 summary camera health 窗口对齐和只读边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- --run test/catalog.test.ts -t "HTTP first-screen budget|camera health times out|camera MJPEG status"`，结果 `8 tests passed`。
- 通过：`npm --prefix pc-tools/workstation test -- --run test/catalog.test.ts -t "slower camera health|camera no-frame diagnosis|relay no-frame diagnosis|bad JSON"`，结果 `4 tests passed`。
- 通过：`npm --prefix pc-tools/workstation test -- --run test/catalog.test.ts`，结果 `153 tests passed`。
- 通过：`npm --prefix pc-tools/workstation run build`，TypeScript 与 Vite build 成功；仍有既有 chunk size warning。
- 通过：重启 PC Node 到 `0.0.0.0:7001` 后，只读请求 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `camera.status=source_first_frame_failed`、`source_readiness=first_frame_failed`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、`source_diagnosis_not_exclusive=true`、`shared_preview_last_failure_reason=camera_source_first_frame_failed`，并显示 `nav2_goal_ready=true`、`keyboard_control_start_ready=true`、`free_roam_autonomy_start_ready=true`。
- 通过：只读请求 `GET /api/robot-control/camera/mjpeg/status?baseUrl=http://192.168.1.11:8787` 返回 `proxy_status=status_loaded`、`client_count=0`、`upstream_active=false`、`shared_capture=true`、`exclusive_camera_claim=false`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、`source_diagnosis_not_exclusive=true`、`robot_control_executed=false`。

## 剩余风险

- 本轮只修 PC summary 只读诊断窗口；真实 UVC 首帧仍未恢复。
- 8 秒窗口可能让 summary 在相机 health 慢时稍晚返回，但比普通首屏显示互相矛盾的相机事实更符合所见即所得。
