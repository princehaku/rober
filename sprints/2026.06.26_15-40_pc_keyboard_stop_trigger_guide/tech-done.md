# PC 键盘连续手控停止触发说明

## sprint_type

micro

## 实际改动

- 普通首屏键盘指南补充 `松开、窗口失焦或切页面都会停`，和现有 keyup/window blur/page hidden stop 触发保持一致。
- 更新 PC 工作站测试，锁定键盘连续手控普通指南文案。
- 同步 `docs/product/pc_tools_workstation.md`，明确该改动只解释现有 stop 收口，不改变 pulse 周期、不自动启用键盘、不额外发送控制命令，不修改 Clash/系统代理，PC 入口保持 `0.0.0.0:7001`。

## 验证结果

- 通过：`npm test -- -t "enables non-stop motion only after complete operator material and still uses the fixed workstation proxy|queues release stop when the stop button is clicked during an in-flight keyboard pulse"`，结果 `Test Files 1 passed | 1 skipped (2)`，`Tests 2 passed | 200 skipped (202)`。
- 通过：`npm run lint`。
- 通过：`npm run build`。Vite 仍提示单个 chunk 超过 500 kB，这是既有体积提醒，不影响本轮功能。
- 通过：`npm test`，结果 `Test Files 2 passed (2)`，`Tests 202 passed (202)`。
- 通过：完整测试改写的两个历史 smoke artifact `checked_at` 已恢复到历史固定值，未纳入本轮提交。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN` 确认 `node` 监听 `*:7001`。

## 剩余风险

- 本轮只做 PC 前端提示和 mock/单测验证，未做真实小车 HIL 或真实键盘手控实车验证。
