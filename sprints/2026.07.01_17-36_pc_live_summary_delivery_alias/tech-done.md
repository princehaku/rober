# PC live-summary 送达闭环短 alias

sprint_type: micro

## 实际改动

- `live_closure_summary` 和 `/api/robot-control/live-summary` 新增 delivery 短 alias，直接暴露是否仍需 `delivery success`、下一步文案、固定 latest/complete 端点和“不发车”边界。
- 普通首屏当前卡点 DOM 增加对应 `data-delivery-*` 字段，现场脚本只读当前卡点即可确认送达闭环还差什么。
- 更新测试和产品文档，保持 delivery latest 为只读，delivery complete 明确不发送运动。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts -t "minimal precheck fields for same-window wheel rerun"`：通过，1 passed。
- `cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "workstation live-summary route exposes a flat read-only current card for field curl checks"`：通过，1 passed。
- `cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`：通过，1 passed。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍提示单包 chunk 超过 500 kB，这是既有体积提醒，不影响本轮功能。
- `cd pc-tools/workstation && npm test`：通过，3 files / 418 tests。
- `git diff --check`：通过。
- 运行态只读确认：PC API 已重启到 `0.0.0.0:7001`，`GET /api/robot-control/live-summary` 返回 `delivery_success=false`、`delivery_success_required=true`、`fixed_delivery_latest_endpoint=/api/robot-control/delivery/latest`、`fixed_delivery_complete_endpoint=/api/robot-control/delivery/complete`、`delivery_latest_readback_only=true`、`delivery_complete_sends_motion=false`，当前仍为 `status=needs_wheel_rerun`。

## 剩余风险

- 本轮只改善送达闭环可读性；真实 delivery success 仍需要轮速复验通过后，由现场逐项确认并提交。
- 完整 Nav2 路线仍卡在同窗口轮速 L/R 非零复验；相机画面仍受 USB 12M full-speed 首帧失败影响。
