# 安全确认队列本地焦点切换

sprint_type: micro

## 实际改动

- 普通首屏 `plain-current-safety-confirm-queue` 保留后端原始焦点字段，同时新增浏览器本地有效焦点字段。
- 当队列 primary action 是 `run_nav2_route` 且用户已勾现场安全确认时，队列按钮从 `去勾行程安全确认` 即时切换为 `去执行图上行程`，焦点目标从 `trip_safety_confirm` 切到 `trip_execute_button`。
- 队列按钮继续保持 focus-only：点击只跳转到对应动作卡，不直接执行 Nav2、manual、keyboard、free-roam、建图、delivery、stop 或 `/cmd_vel`。
- 同步更新 PC 工具文档和 DOM 测试。

## 验证结果

- 通过：`npm test -- test/App.test.ts`，237 个测试通过。
- 通过：`npm run build`；仅保留 Vite 大 chunk 提醒。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只修正 PC 本地交互状态，不发送真实运动命令，也不包含 HIL 发车验证。
