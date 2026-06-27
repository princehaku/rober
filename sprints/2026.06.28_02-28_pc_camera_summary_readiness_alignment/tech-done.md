# 2026-06-28 02:28 PC 相机 summary readiness 对齐

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 当 PC summary 最终相机 `status` 已经由 health 或共享 MJPEG relay 判定为 `source_first_frame_failed` 时，返回的 `source_readiness` 同步归一为 `first_frame_failed`。
  - 该改动只修正只读 summary 口径，不打开相机上游、不发送 manual、stop、Nav2、free-roam、delivery 或 `/cmd_vel`。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增 catalog 测试覆盖 live 形态：camera health 慢到超时，但 relay 已证明 `camera_source_first_frame_failed`，summary 不得返回 `status=source_first_frame_failed` 且 `source_readiness=not_loaded` 的矛盾组合。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录 PC summary 相机 status/readiness 对齐的 WYSIWYG 口径。

## 验证结果

- `npm test -- -t "Robot Control summary keeps camera status and readiness aligned when relay proves first-frame failure"`：通过，1 passed / 331 skipped。
- `npm test -- --maxWorkers=1 --no-fileParallelism`：通过，2 files passed / 332 tests passed。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 仍有既有 chunk size warning。
- `git diff --check`：通过。
- 重启 PC Node 到 `0.0.0.0:7001`：通过，`node` 监听 `*:7001`。
- 只读检查 `/api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：通过，schema 为 `trashbot.pc_tools_workstation.robot_control_summary.v1`；`camera_status=source_first_frame_failed` 且 `camera_source_readiness=first_frame_failed`；相机诊断仍为 `uvc_no_frame_not_exclusive`；`keyboard_control_start_ready=true`、`free_roam_motion_start_ready=true`、`free_roam_mapping_ready=false`；`nav2_goal_ready=false`；雷达 lifecycle 仍未运行且 runtime scan stale。

## 剩余风险

- 本轮只修复 PC summary 的相机状态一致性，不修复真实 UVC 无帧问题；建图验收仍需要真实 camera first frame。
- 当前 live 雷达 lifecycle 仍可能 stopped/stale；雷达 marker WYSIWYG 已能表达不当前，但要建图仍需雷达新鲜扫描。
