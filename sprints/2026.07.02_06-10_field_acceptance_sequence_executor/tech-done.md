# 2026-07-02 06:10 现场验收只读 sequence 执行器

sprint_type: micro

## 实际改动

- PC 首屏“只读复验全部”改为读取 `field_acceptance_packet.no_motion_readback_actions[].sequence_endpoints` 中 `readback_all` 的声明顺序执行。
- 新增只读 endpoint 白名单执行器，只允许 summary、map preview、Nav2 latest、base feedback samples、delivery latest、free-roam latest、radar proof、radar status、camera first-frame probe、camera MJPEG status；其他 endpoint 直接跳过。
- 拆开 sequence 场景里的原子读回，避免 free-roam latest、delivery latest、camera probe、radar proof 额外偷刷 summary，保证实际点击路径和验收包声明一致。
- 同步 App 测试和 PC 文档，明确 sequence 不只是 DOM/API 字段，也是按钮实际执行合同；仍不启动 Nav2/manual/keyboard/free-roam/建图/雷达 lifecycle，不提交送达，不发送 stop 或 `/cmd_vel`。

## 验证结果

- 已通过：`git diff --check`
- 已通过：`cd pc-tools/workstation && npm test -- App.test.ts`，结果 `Test Files 1 passed`，`Tests 236 passed`。
- 已通过：`cd pc-tools/workstation && npm test -- robotControlSummary.test.ts App.test.ts catalog.test.ts`，结果 `Test Files 3 passed`，`Tests 427 passed`。
- 已通过：`cd pc-tools/workstation && npm run lint`
- 已通过：`cd pc-tools/workstation && npm run build`；Vite 仍提示单个 chunk 超过 500 kB，这是既有体积提醒，不影响本轮合同。
- 待补充：git 提交推送。

## 剩余风险

- 本轮只调整 PC 只读复验执行路径，没有执行真实发车、真实键盘控制、真实建图或真实摄像头/雷达 HIL。
