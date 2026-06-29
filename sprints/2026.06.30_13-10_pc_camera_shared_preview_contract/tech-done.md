# 2026.06.30 13:10 PC 画面共享预览合同

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `camera_preview` action card evidence 新增固定共享预览端点、状态端点、自动接入和单上游共享 relay 字段。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 后端 summary 为画面卡固定返回 `/api/robot-control/camera/mjpeg` 和 `/api/robot-control/camera/mjpeg/status` 合同。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 前端兼容旧 summary，自动派生同一份共享预览合同。
  - 普通首屏 action card DOM 暴露对应 `data-*` 字段，方便现场脚本验证画面 WYSIWYG 缺口。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`
  - 补后端 action card 和前端 DOM 断言。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录共享预览合同和安全边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- test/catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints and keeps commands locked"`
  - `Test Files 1 passed (1)`，`Tests 1 passed | 169 skipped (170)`。
- 通过：`cd pc-tools/workstation && npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`
  - `Test Files 1 passed (1)`，`Tests 1 passed | 218 skipped (219)`。
- 通过：`cd pc-tools/workstation && npm test -- --run`
  - `Test Files 2 passed (2)`，`Tests 389 passed (389)`。
- 通过：`cd pc-tools/workstation && npm run build`
  - Vite build 成功；仅保留既有 chunk size warning。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `0.0.0.0:7001` 后只读检查 `GET /api/robot-control/summary`。
  - `camera_preview.evidence.fixed_shared_preview_endpoint=/api/robot-control/camera/mjpeg`。
  - `camera_preview.evidence.fixed_shared_preview_status_endpoint=/api/robot-control/camera/mjpeg/status`。
  - `auto_joins_shared_preview=true`、`shared_preview_single_upstream=true`。
  - `robot_control_executed=false`。

## 剩余风险

- 本轮只补只读合同和 DOM evidence，不重启相机、不独占摄像头、不发送 Nav2/manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。
- live summary 仍可能显示“本页共享实时预览还没显示缓存帧”；这需要浏览器实际加载 MJPEG 成功或相机源继续输出帧才能闭合。
