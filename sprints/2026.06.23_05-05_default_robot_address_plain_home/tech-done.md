# 2026-06-23 05:05 default robot address plain home

sprint_type: micro

## 实际改动

- 普通首屏移除 `小车地址` 输入框和默认 URL 展示，改为固定显示 `默认小车`、默认地址状态和 `连接/刷新`。
- 地址输入和恢复默认地址按钮下沉到默认关闭的 `高级诊断 -> 连接详情`，用于高级联调；普通用户不需要手输 `http://192.168.1.11:8787`。
- 更新 PC 工作站测试，确认 `.simple-user-console` 中没有 `robotApiBaseUrl` 输入框、默认 URL 不出现在普通首屏、恢复默认不触发额外 fetch。
- 更新 `docs/product/pc_tools_workstation.md` 的普通首屏契约。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test`，`Test Files 2 passed (2)`，`Tests 134 passed (134)`。
- 已通过：`cd pc-tools/workstation && npm run lint`。
- 已通过：`cd pc-tools/workstation && npm run build`，Vite client build 和 server TypeScript build 均完成。
- 已通过：`git diff --check`。
- 测试期间两个历史 DOM smoke JSON 只改动 `checked_at`，已还原为原始时间戳，未纳入本轮 diff。

## 剩余风险

- 本轮只改善 PC 普通首屏易用性，不包含真实上位机运动、Nav2 路线执行、送达确认或键盘连续手控 HIL 验证。
