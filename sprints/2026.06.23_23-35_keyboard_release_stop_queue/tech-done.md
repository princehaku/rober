# 2026.06.23 23:35 Keyboard Release Stop Queue

sprint_type: micro

## 实际改动

- PC 键盘连续手控在 keyup/松开时，如果上一条 keyboard manual pulse 仍在请求中，会先记录 release reason，并在该 pulse 返回后补发一次固定 stop。
- 新增 `keyboardStopAfterPulseReason` 队列状态，避免 release stop 被 `manualCommandPending` 直接跳过。
- 新增回归测试覆盖“keydown 后 manual 请求 pending、keyup 先发生、manual resolve 后自动补发 stop”。
- 更新 `docs/product/pc_tools_workstation.md` 记录 release stop 排队口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- -t "keyboard control"`，2 个目标测试通过。
- 通过：`cd pc-tools/workstation && npm test -- -t "in-flight keyboard pulse"`，1 个目标测试通过。
- 通过：`cd pc-tools/workstation && npm test`，2 个 test files、147 个测试通过。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只修正 PC 前端键盘 release stop 排队；真实上位机当前仍未满足 wheel raw L/R 非零、雷达运行、完整 Nav2 本轮路线、delivery success 和真实键盘连续手控。
