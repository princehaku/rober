# No-motion 读回短 alias

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：`RobotControlSummaryResponse` 新增 `field_acceptance_primary_no_motion_readback_*` 短 alias，覆盖 id、label、endpoint、method、sequence、sequence labels 和 sends motion。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：短 alias 与既有 `field_acceptance_primary_no_motion_readback_action_*` 同源，避免现场脚本查短字段时读到 `null`。
- `pc-tools/workstation/test/robotControlSummary.test.ts`：补雷达贴图 primary 与 camera-only primary 两类回归断言，确认短 alias 与长字段一致。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`：同步说明短 alias 只用于 no-motion 读回，不启动 Nav2/manual/keyboard/free-roam/建图/雷达 lifecycle，不发送 stop 或 `/cmd_vel`；同时修正文档内雷达贴图读回序列为 `radar scan proof -> radar status -> map preview -> summary`。

## 验证结果

- `git diff --check`：通过。
- `cd pc-tools/workstation && npm test -- --run catalog.test.ts App.test.ts robotControlSummary.test.ts`：3 个测试文件通过，427 条测试通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，保留既有 Vite chunk size warning。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `32257`。
- 真实只读 summary smoke：`status=needs_wheel_rerun`，`live_wysiwyg_missing_surface_ids=[camera]`，`field_acceptance_primary_no_motion_readback_id=refresh_camera_first_frame`，`field_acceptance_primary_no_motion_readback_endpoint=/api/robot-control/camera/first-frame/probe`，`field_acceptance_primary_no_motion_readback_method=POST`，`field_acceptance_primary_no_motion_readback_sequence=[/api/robot-control/camera/first-frame/probe,/api/robot-control/camera/mjpeg/status,/api/robot-control/summary]`，`field_acceptance_primary_no_motion_readback_sends_motion=false`。

## 剩余风险

- 本轮只读 summary smoke，没有发 camera probe，也没有执行任何 motion/control POST。
- `motion` 目标仍缺安全确认后的 Nav2 同窗口 wheel L/R 非零、delivery success、PC 键盘连续手控和自由移动 latest 运行读数。
- `wysiwyg` / `mapping` 仍只剩相机首帧硬件缺口；当前诊断仍指向 USB 12M full-speed，需要现场换高速 USB 口/线或带供电 Hub 后再复测。
