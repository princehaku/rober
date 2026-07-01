# Current Hardware Action Alias

sprint_type: micro

## 实际改动

- 补齐 PC `GET /api/robot-control/summary` 顶层 `current_hardware_action_*` 短字段，让现场脚本直接读取当前外部设备处理动作、处理后复测序列、建图/自由移动阻塞关系和 no-motion 标记。
- 同步 TypeScript 合同、summary 单测和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `npm test -- --run robotControlSummary.test.ts App.test.ts catalog.test.ts`：第一次失败于无硬件动作测试预期仍写 `none`；修正为现有普通文案“无设备处理动作”后重跑通过，3 个测试文件、428 个测试通过。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 保留既有 large chunk 提醒。
- `git diff --check`：通过。
- 已重启 PC Node，`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` PID 52789 监听 `TCP *:7001`。
- 只读 smoke `GET http://127.0.0.1:7001/api/robot-control/summary`：`current_hardware_action_required=true`、
  `current_hardware_action_id=camera_usb_recovery`、`current_hardware_action_label=换高速USB后复测`，
  处理后读回序列为 camera first-frame probe、camera MJPEG status、summary；
  `current_hardware_action_blocks_mapping_start=true`、`current_hardware_action_blocks_free_move=false`、
  `current_hardware_action_sends_motion=false`。
- `/map` HTTP smoke：`200 text/html; charset=utf-8`。

## 剩余风险

- 相机仍报告 `uvc_full_speed_usb_not_exclusive` 和 USB `12M`，需要现场换高速 USB 口/线或带供电 USB Hub 后再复测。
- 本轮没有新的现场安全确认，因此没有执行 Nav2、键盘 manual、free-roam、delivery complete、stop 或 `/cmd_vel`。
