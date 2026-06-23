# 2026.06.23 23:05 Keyboard Stop Settle Gate

sprint_type: micro

## 实际改动

- PC 普通首屏把 `PC 键盘连续手控` 验收从“同一次按住 2/2 pulse 成功”收紧为“2/2 pulse 成功并且松开后 stop 已发送”。
- 按住期间达到 2/2 时，`本轮进度`、高级 `目标收口进度` 和键盘 live status 仍保持待验证，并提示 `松开按键完成停止收口`。
- 松开后固定 `POST /api/robot-control/base/stop` 已发送，才显示 `键盘手控已验证`。
- 更新 `docs/product/pc_tools_workstation.md` 记录最新键盘验收口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- -t "enables non-stop motion only after complete operator material"`，1 个目标测试通过。
- 通过：`cd pc-tools/workstation && npm test`，2 个 test files、145 个测试通过。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只收紧 PC 前端键盘验收状态；真实上位机当前仍未满足 wheel raw L/R 非零、雷达运行、完整 Nav2 本轮路线、delivery success 和真实键盘连续手控。
