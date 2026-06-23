# 2026.06.23 23:20 Keyboard Stop Success Gate

sprint_type: micro

## 实际改动

- PC 键盘连续手控的 stop 收口从“调用 `sendStop()` resolve”收紧为 stop proxy 必须 `command_forwarded` 且远端 HTTP 为 2xx。
- release stop 返回 rejected、4xx/5xx 或 fallback failure 时，普通首屏显示 `键盘停止请求未成功，未记为已验证`，`PC 键盘连续手控` 继续保持未完成。
- 新增回归测试覆盖“两次 keyboard manual pulse 成功，但 release stop 被拒绝时不能标记键盘已验证”。
- 更新 `docs/product/pc_tools_workstation.md` 记录 stop 成功判定口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- -t "keyboard control"`，2 个目标测试通过。
- 通过：`cd pc-tools/workstation && npm test`，2 个 test files、146 个测试通过。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只收紧 PC 前端键盘 stop 成功判定；真实上位机当前仍未满足 wheel raw L/R 非零、雷达运行、完整 Nav2 本轮路线、delivery success 和真实键盘连续手控。
