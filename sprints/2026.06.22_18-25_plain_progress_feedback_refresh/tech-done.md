# 2026-06-22 18:25 Plain Progress Feedback Refresh

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `本轮进度 -> 刷新进度` 现在同时触发固定只读底盘反馈采样 `POST /api/robot-control/base/feedback-samples`，并把 pending 状态纳入按钮禁用条件；高级诊断原有“采集底盘反馈（高级）”仍保留自动刷新 summary 的行为。
- `pc-tools/workstation/test/App.test.ts`：更新刷新进度测试，锁住 summary、base feedback samples、Nav2 latest、delivery latest 四个只读调用，并确认不会触发 Nav2 execution、delivery complete、manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`：同步记录刷新进度会刷新 T1001 L/R，但不会把静态反馈计数外推成 wheel raw L/R 非零完成。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善 PC 普通首屏只读刷新体验；真实 wheel raw L/R 非零仍需要现场安全确认后的试动窗口读到同帧非零 `L/R`。
- 真实上位机本轮只读复查仍显示 T1001 帧存在但 `L/R=0/0`，delivery success 仍缺最终现场确认材料。
