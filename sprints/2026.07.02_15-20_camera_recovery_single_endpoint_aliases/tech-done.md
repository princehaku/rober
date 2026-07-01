# 2026.07.02 15:20 Camera Recovery Single Endpoint Aliases

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：`RobotControlSummaryResponse` 新增相机 WYSIWYG 恢复单值 alias：`camera_wysiwyg_recovery_readback_endpoint`、`camera_wysiwyg_recovery_probe_endpoint`、`camera_wysiwyg_recovery_status_endpoint`、`camera_wysiwyg_recovery_summary_endpoint`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：上述字段复用既有相机恢复链路，分别指向 first-frame probe、MJPEG status 和 summary。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `plain-live-closure-summary` DOM 暴露对应 `data-camera-wysiwyg-recovery-*endpoint`，现场脚本无需拆数组也能拿到当前相机复验入口。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`：补 summary 与 DOM 回归断言。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`：同步说明这些 alias 只描述换高速 USB/共享预览后的只读复验链，不启动独占相机、建图 runtime 或任何运动控制。

## 验证结果

- `git diff --check`：通过。
- `cd pc-tools/workstation && npm test -- --run catalog.test.ts App.test.ts robotControlSummary.test.ts`：3 files / 427 tests passed。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，Vite 仍有既有 chunk size warning。
- PC Node 已重启到 `0.0.0.0:7001`，`lsof` 显示 `node` 监听 `*:7001`。
- 真实 summary smoke：`GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `camera_wysiwyg_recovery_readback_endpoint=/api/robot-control/camera/first-frame/probe`、`camera_wysiwyg_recovery_status_endpoint=/api/robot-control/camera/mjpeg/status`、`camera_wysiwyg_recovery_summary_endpoint=/api/robot-control/summary`，并确认 `camera_wysiwyg_recovery_blocks_mapping_start=true`、`camera_wysiwyg_recovery_blocks_free_move=false`、`camera_wysiwyg_recovery_sends_motion=false`、`camera_wysiwyg_recovery_starts_map_runtime=false`。

## 剩余风险

- 本轮只补相机恢复读回 alias，不执行 camera probe，不启动相机独占采集，不启动建图 runtime，也不发送运动命令。
- 当前真实状态仍是 `status=needs_wheel_rerun`；motion 还缺安全确认后的 Nav2 wheel L/R 非零、delivery success、PC 键盘连续手控和自由移动验收。
- WYSIWYG / mapping 仍缺相机首帧；雷达贴图当前已 `radar_overlay_wysiwyg_complete=true`。
