# 2026-07-02 05:25 现场验收只读复验链路

sprint_type: micro

## 实际改动

- `field_acceptance_packet.no_motion_readback_actions[]` 从单 endpoint 升级为完整只读 sequence：每项暴露 `sequence_endpoints`、`sequence_labels` 和 summary/radar/camera/map/status refresh flags。
- Summary 顶层新增 `field_acceptance_no_motion_readback_action_sequences`、`field_acceptance_no_motion_readback_action_sequence_labels`，以及 primary no-motion action 的 sequence 与 refresh flags。
- 普通 PC 首屏现场验收卡和“只读复验”按钮同步暴露 sequence/flags；雷达贴图复验固定说明 `radar proof -> summary -> radar status -> map preview`。
- 同步更新测试和文档，明确该链路只读，不启动 Nav2/manual/keyboard/free-roam/建图/雷达 lifecycle，不提交送达，不发送 stop 或 `/cmd_vel`。

## 验证结果

- 通过：`git diff --check`
- 通过：`cd pc-tools/workstation && npm test -- robotControlSummary.test.ts App.test.ts catalog.test.ts`，结果 `Test Files 3 passed`，`Tests 426 passed`。
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`；Vite 仍提示单个 chunk 超过 500 kB，这是既有打包体积提醒，不影响本轮合同。
- 通过：重启 PC Node 工作站到 `0.0.0.0:7001` 后，`GET /api/robot-control/summary` 返回 primary no-motion action `refresh_radar_map_overlay`，sequence 为 `/api/robot-control/radar/scan-proof/refresh -> /api/robot-control/summary -> /api/robot-control/radar/status -> /api/robot-control/map/preview`，并返回 `refreshes_radar_scan_proof=true`、`refreshes_summary=true`、`refreshes_radar_status=true`、`refreshes_map_preview=true`、`refreshes_camera_first_frame_probe=false`。

## 剩余风险

- 本轮只增强 no-motion 读回合同和 DOM/API 可验收性，没有执行真实雷达刷新，也没有触发任何运动或建图动作。
