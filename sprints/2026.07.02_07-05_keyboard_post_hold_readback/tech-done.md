# 2026-07-02 07:05 键盘松开后轮速读回

sprint_type: micro

## 实际改动

- PC 键盘连续手控在 release stop 转发成功后，自动执行只读 `base/feedback-samples -> summary` 复验链路。
- 该 post-hold 读回只刷新同一次按住窗口后的 wheel L/R 证据，不再发送 manual 脉冲，不启动 Nav2/free-roam/建图/雷达 lifecycle，不提交送达，不发送额外 stop 或 `/cmd_vel`。
- App 测试覆盖非零 L/R 和 0/0 两种键盘回包：keyup 后必须看到 stop、feedback samples、summary 顺序，并确认没有 Nav2 execute、delivery complete 或 `/cmd_vel`。
- 同步 PC 工具文档，明确键盘连续控制的松开后自动读回口径。

## 验证结果

- 已通过：`git diff --check`
- 已通过：`cd pc-tools/workstation && npm test -- App.test.ts`，结果 `Test Files 1 passed`，`Tests 236 passed`。
- 已通过：`cd pc-tools/workstation && npm test -- robotControlSummary.test.ts App.test.ts catalog.test.ts`，结果 `Test Files 3 passed`，`Tests 427 passed`。
- 已通过：`cd pc-tools/workstation && npm run lint`
- 已通过：`cd pc-tools/workstation && npm run build`；Vite 仍提示单个 chunk 超过 500 kB，这是既有体积提醒，不影响本轮合同。
- 待补充：提交和推送。

## 剩余风险

- 本轮没有现场安全确认，也没有真实按键发车；只增强真实键盘手控停止后的自动读回闭环。
