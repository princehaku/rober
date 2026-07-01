# Summary camera reprobe alias micro sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：`GET /api/robot-control/summary` 顶层补齐相机硬件恢复 alias：`camera_blocks_mapping_start`、`camera_blocks_free_move`、`camera_reprobe_after_hardware_action_required`、`camera_reprobe_sequence` 和 `camera_recovery_starts_map_runtime`。
- `pc-tools/workstation/src/shared/contracts.ts`：同步新增这些 summary 顶层字段类型。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/catalog.test.ts`：断言 summary 顶层字段与 `live_closure_summary` 同源，并保持相机恢复不发车、不启动建图 runtime。
- `docs/product/pc_tools_workstation.md`：记录相机硬件恢复 alias 的当前合同。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`，`9 passed`。
- 已通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "live-summary"`，`1 passed | 180 skipped`。
- 已通过：`git diff --check`。
- 已通过：`cd pc-tools/workstation && npm test`，`421 passed`。
- 已通过：`cd pc-tools/workstation && npm run lint`。
- 已通过：`cd pc-tools/workstation && npm run build`。
- 已通过：重启 `0.0.0.0:7001`，当前监听 PID `8706`。
- 已通过：只读 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `camera_hardware_action_required=true`、`camera_hardware_action_label=换高速USB后复测`、`camera_usb_full_speed_detected=true`、`camera_blocks_mapping_start=true`、`camera_blocks_free_move=false`、`camera_reprobe_after_hardware_action_required=true`、`camera_reprobe_sequence=[/api/robot-control/camera/first-frame/probe,/api/robot-control/camera/mjpeg/status,/api/robot-control/summary]`、`camera_recovery_sends_motion=false`、`camera_recovery_starts_map_runtime=false`、`mapping_start_missing_reasons=[camera_first_frame]`、`free_move_start_ready=true`。

## 剩余风险

- 本轮只把已有 live 相机恢复事实透到 summary 顶层，不打开独占相机、不启动建图 runtime、不执行 Nav2/manual/keyboard/free-roam/delivery/stop，也不发布 `/cmd_vel`。
- 真实画面仍需要现场按硬件建议换高速 USB/线或带供电 Hub 后复测。
