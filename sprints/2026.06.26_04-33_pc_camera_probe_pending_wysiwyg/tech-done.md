# PC 当前画面记录 pending 所见即所得

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：当前画面 probe pending 且浏览器还没有真实可绘制视频帧时，实时画面卡片显示 `检查中`，画面状态说明正在等待上位机返回样张；`用当前画面记录` 按钮 pending 时显示 `正在检查画面`。
- `pc-tools/workstation/test/App.test.ts`：扩展当前画面记录单测，用延迟 camera first-frame probe 验证 pending 状态可见、按钮禁用、probe 返回前不提交 operator report，也不发送 first-jog/manual/Nav2/delivery/`/cmd_vel`。
- `docs/product/pc_tools_workstation.md`：同步 `用当前画面记录` pending 状态和安全边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- -t "records the current camera frame from the plain first screen without sending motion"`，1 passed / 190 skipped。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`cd pc-tools/workstation && npm test`，2 test files passed，191 tests passed。
- 通过：`git diff --check`。
- 确认：`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示项目 node 监听 `*:7001`。

## 剩余风险

- 本轮只覆盖 PC mock/单测路径，不触发真实相机或真实小车运动；真实 USB camera 首帧慢返回仍需要现场 HIL 观察确认。
