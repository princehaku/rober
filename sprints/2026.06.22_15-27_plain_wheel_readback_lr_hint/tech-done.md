# Plain Wheel Readback L/R Hint

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- date: 2026-06-22

## 实际改动

- Robot Control summary 的 `readback_summary.base` 新增最新只读 `wheel_feedback_latest_left_speed` 和 `wheel_feedback_latest_right_speed`。
- 普通首屏“轮速记录”新增只读提示：当 T1001 可读但 L/R 仍为 `0/0` 时，显示“当前只读轮速是 L/R=0/0；这还不是非零证据，需要现场试动窗口。”
- 该提示同时消费 summary 只读回显和高级只读底盘反馈采样结果，不调用 manual、first-jog、Nav2 或 `/cmd_vel`。
- 补测试确认 L/R=0/0 会在普通首屏显示，并且不会被当成 wheel raw L/R 非零证据。
- 更新 `docs/product/pc_tools_workstation.md`。

## 验证结果

- 通过：`npm test`，2 个 test files、118 个 tests 全部通过。
- 通过：`npm run lint`。
- 通过：`npm run build`，完成 `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只改善 PC 首屏对真实 `L/R=0/0` 状态的解释，不完成 wheel raw L/R 非零。
- 真实 wheel raw L/R 非零仍需要现场安全确认后运行试动窗口，并由上位机返回同帧 L/R 非零证据。
