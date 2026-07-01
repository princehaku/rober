# Summary Sensor Ready Alias

## Sprint 类型

sprint_type: micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增相机/雷达 ready 短 alias：`camera_ready`、`camera_first_frame_ready`、`camera_needs_usb_fix`、`camera_usb_high_speed`、`radar_ready`、`radar_fresh` 和 `radar_map_ready`。
- `camera_ready` / `camera_first_frame_ready` 镜像当前画面首帧可见；`camera_needs_usb_fix` 镜像硬件恢复建议；`camera_usb_high_speed` 在 USB full-speed、unknown 或 not_loaded 时保持 fail-closed false。
- `radar_ready` / `radar_fresh` 镜像建图可用的新鲜雷达读回；`radar_map_ready` 镜像当前地图雷达点是否已贴图，避免把旧来源点误报成当前所见。
- 更新 summary 合同、服务端返回、定向测试、catalog live-summary 合同测试和 PC 工作站产品文档。

## 验证结果

- 通过：`git diff --check`
- 通过：`npm test -- --run test/robotControlSummary.test.ts`，结果 `1 passed / 9 passed`。
- 通过：`npm test -- --run test/catalog.test.ts -t "live-summary"`，结果 `1 passed / 1 passed / 180 skipped`。
- 通过：`npm test`，结果 `3 passed / 421 passed`。
- 通过：`npm run lint`。
- 通过：`npm run build`；仅保留 Vite 既有 chunk size warning。
- 通过：重启 `0.0.0.0:7001` 后，用只读 `GET /api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 确认相机/雷达 ready 短 alias 不再为 `null`：`camera_ready=false`、`camera_first_frame_ready=false`、`camera_needs_usb_fix=true`、`camera_usb_high_speed=false`、`radar_ready=false`、`radar_fresh=false`、`radar_map_ready=false`。

## 剩余风险

- 本轮只增加只读 alias，不打开相机，不启动雷达 lifecycle，不刷新地图，不执行 Nav2、manual、keyboard、free-roam、建图、delivery、stop 或 `/cmd_vel`。
- 当前现场仍是 `camera_ready=false`、`radar_ready=false`、`radar_map_ready=false`；真实 WYSIWYG 和建图条件还需要现场硬件/刷新链路继续收口。
