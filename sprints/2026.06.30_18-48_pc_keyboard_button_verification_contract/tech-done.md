# PC keyboard 按钮级复验合同

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏键盘连续手控面板、启用键、四个屏幕方向键和屏幕停止键补齐按钮级复验字段。
  - 新增固定 `manual`、`stop`、`base/feedback-samples`、`summary` endpoint，以及 `manual_command_mode=ros`。
  - 明确按住后必须做 wheel raw L/R 非零读回、summary 刷新、同一次按住窗口验收和 stop settled 收口。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展默认首屏和键盘连续按住流程测试，覆盖新增 `data-*` 合同。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录 PC 键盘连续手控的按钮级现场验收口径。

## 验证结果

- `npm test -- -t "keyboard"`：通过，21 passed / 381 skipped。
- `npm test -- App.test.ts`：通过，225 passed。
- `npm test -- --run`：通过，3 files / 402 tests passed。
- `npm run lint`：通过，0 errors；保留既有 4 个 Vue multiline warning。
- `npm run build`：通过；保留 Vite chunk size warning。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`，`lsof` 显示 node PID `13113` 监听 `TCP *:7001`。
- 只读 `GET http://127.0.0.1:7001/api/health`：通过，API routes 包含 `/api/robot-control/base/feedback-samples`、`/api/robot-control/summary`。
- 只读 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：通过，返回 `live_status=needs_wheel_rerun`、`keyboard_ready=true`、`minimal_precheck=true`、`keyboard_status=start_ready`。
- 只读 bundle 检查：通过，产物中包含 `postHoldFeedbackReadbackRequired`、`fixedFeedbackSamplesEndpoint`、`base/feedback-samples` 等新增键盘合同字段。

## 剩余风险

- 本轮未发 live motion POST，未真实按住键盘让车移动；真实 wheel raw L/R 非零和 stop settled 仍需要现场安全确认后复验。
- 本轮只补 PC DOM 合同和测试，不改变上位机 manual/stop 代理、底盘控制或 ROS2/Nav2 runtime。
