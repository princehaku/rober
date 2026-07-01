# 2026.07.02 10:00 camera probe no-motion flags

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：`RobotControlCameraFirstFrameProbeProxyResponse` 新增相机首帧 probe 本体只读合同字段：`readback_only`、`camera_probe_readback_only`、`sends_motion_when_clicked`、`starts_camera_exclusive_capture`、`starts_*`、`submits_delivery`、`stops_motion`。
- `pc-tools/workstation/src/server/index.ts`：相机首帧 probe 成功、503 失败、本机拒绝和 fetch 失败路径统一返回上述字段，避免 primary no-motion 动作回包出现 `null`。
- `pc-tools/workstation/test/catalog.test.ts`：补 quick probe、backend smoke probe 和 proxy timeout 的 no-motion 字段断言。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`：同步相机首帧 probe 回包合同。

## 验证结果

- `git diff --check`：通过。
- `cd pc-tools/workstation && npm test -- --run catalog.test.ts App.test.ts robotControlSummary.test.ts`：3 files passed，427 tests passed。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍提示单 chunk 超 500 kB 的既有警告。
- 重启 PC Node：`0.0.0.0:7001` 已监听，PID `47145`。
- 实机只读/no-motion smoke：
  - `POST /api/robot-control/camera/first-frame/probe?baseUrl=http://192.168.1.11:8787` 返回 `proxy_status=probe_failed`、`status=first_frame_timeout`、`remote_http_status=503`、`readback_only=true`、`camera_probe_readback_only=true`、所有 `starts_*`/`sends_motion_when_clicked`/`submits_delivery`/`stops_motion=false`、`robot_control_executed=false`。
  - 回包仍显示 `source_diagnosis_status=uvc_full_speed_usb_not_exclusive`、`camera_usb_full_speed_detected=true`、`failure_reason=deadline_expired`。
  - `GET /api/robot-control/summary` 仍为 `status=needs_wheel_rerun`，WYSIWYG 缺口只剩 `camera`，primary no-motion action 为 `refresh_camera_first_frame`。

## 剩余风险

- 本轮只修 PC 代理回包合同，不修复真实摄像头首帧；当前相机仍需要换高速 USB/供电 Hub 或 known-good UVC 后复测。
- 完整目标仍未完成：motion 还缺同窗口 wheel raw L/R 非零、delivery success、键盘连续手控验收和自由移动运行读回；mapping 仍缺 `camera_first_frame`。
- 未发送任何运动/control POST，未启动 Nav2/manual/keyboard/free-roam/建图/雷达 lifecycle，未提交 delivery 或 stop。
