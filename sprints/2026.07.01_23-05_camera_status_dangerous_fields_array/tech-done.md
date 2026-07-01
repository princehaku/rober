# Camera MJPEG Status 危险字段数组合同

## Sprint 类型

sprint_type: micro

## 实际改动

- `GET /api/robot-control/camera/mjpeg/status` 响应体显式返回 `hard_dangerous_true_fields=[]`，和已有 `robot_control_executed=false`、`camera_status_readback_only=true` 组成稳定只读合同。
- `RobotControlCameraMjpegStatusResponse` 共享契约补齐 `hard_dangerous_true_fields: string[]`，避免 TypeScript 调用方把该字段当成可选或缺失。
- `catalog.test.ts` 的 full-speed USB 相机状态用例新增断言，锁定该端点不会因为无危险字段而返回 `null`。
- `docs/product/pc_tools_workstation.md` 同步记录 2026-07-01 23:05 CST 起的相机状态危险字段数组合同。

## 验证结果

- `npm test -- --run test/catalog.test.ts -t "camera"`：通过，1 个 test file，31 passed，150 skipped。
- `npm test`：通过，3 个 test files，421 passed。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 仍有既有 chunk size warning。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`，PID `32317`。
- 真实只读 `GET /api/robot-control/camera/mjpeg/status?baseUrl=http://192.168.1.11:8787` 读回：
  - `status=idle_not_started`
  - `source_diagnosis_status=uvc_full_speed_usb_not_exclusive`
  - `camera_hardware_action_required=true`
  - `camera_blocks_free_move=false`
  - `camera_status_readback_only=true`
  - `robot_control_executed=false`
  - `hard_dangerous_true_fields=[]`

## 剩余风险

- 本轮只修相机共享预览状态 JSON 合同，不恢复真实相机首帧。
- 当前真实相机仍需换高速 USB 口/线或带供电 Hub 后复测。
- 本轮不执行 Nav2、manual、keyboard、free-roam、建图、delivery、stop，也不发布 `/cmd_vel`。
