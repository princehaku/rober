# Camera Recovery Top-Level Sequence

sprint_type: micro

## 实际改动

- 补齐 PC `GET /api/robot-control/summary` 顶层相机 WYSIWYG 恢复、硬件处理后复测和建图解锁相机恢复序列字段。
  当前相机卡在 USB 12M/full-speed 时，顶层也能直接读到“首帧 probe -> MJPEG status -> summary”的复测顺序、labels 和 no-motion 标记。
- 同步 TypeScript 合同、summary 单测和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `npm test -- --run robotControlSummary.test.ts App.test.ts catalog.test.ts`：通过，3 个测试文件、428 个测试通过。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 保留既有 large chunk 提醒。
- `git diff --check`：通过。
- 已重启 PC Node，`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` PID 18532 监听 `TCP *:7001`。
- 只读 smoke `GET http://127.0.0.1:7001/api/robot-control/summary`：顶层返回
  `camera_wysiwyg_recovery_sequence`、`camera_reprobe_sequence_labels`、`mapping_unblock_camera_recovery_sequence_labels`，
  且 `camera_reprobe_sequence_sends_motion=false`、`mapping_unblock_camera_recovery_sends_motion=false`。
- `/map` HTTP smoke：`200 text/html; charset=utf-8`。

## 剩余风险

- 本轮没有新的现场安全确认，因此没有执行 Nav2、键盘 manual、free-roam、delivery complete、stop 或 `/cmd_vel`。
- 摄像头首帧仍需现场按硬件提示处理 USB 12M/full-speed 或 UVC 问题后复测；本轮只把复测链路变成顶层可读合同。
