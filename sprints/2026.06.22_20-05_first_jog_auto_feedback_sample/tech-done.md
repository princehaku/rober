# 2026-06-22 20:05 First Jog Auto Feedback Sample

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：`试动一下 / 开始试动读轮速` 返回后自动追加一次固定只读 `base/feedback-samples` 采样，再刷新 summary，让普通首屏马上看到当前 T1001 L/R。
- `pc-tools/workstation/test/App.test.ts`：补充 first-jog 后自动调用 `/api/robot-control/base/feedback-samples` 的断言，同时继续确认不会调用旧 `/api/base/manual` 直通。
- `docs/product/pc_tools_workstation.md`：同步记录该采样依据 `docs/vendor/VENDOR_INDEX.md` 中 WAVE ROVER `T=130` 反馈请求和 `T=1001` L/R 反馈来源；它不发送方向、速度、manual、Nav2 或 `/cmd_vel`。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只让 first-jog 后的只读 L/R 刷新更及时；真实 wheel raw L/R 非零仍需要现场运动窗口内观察到同一 T1001 帧 L/R 均非零。
- 当前真实上位机 `/api/base/status` 只读证据显示 T1001 可读，但 L/R 仍为 0/0，不能作为 wheel raw L/R 非零完成证据。
