# Summary Nested Wheel L/R

sprint_type: micro

## 实际改动

- Robot Control summary 从 `/api/base/feedback-samples/latest` 的 nested `wheel_feedback_summary.latest_pair` 派生既有 wheel latest L/R 摘要字段。
- 派生字段包括 `wheel_feedback_latest_left_speed`、`wheel_feedback_latest_right_speed`、nonzero frame count 和 source，供 PC 普通首屏直接解释当前只读 L/R。
- 补 catalog 测试覆盖真实上位机形态：latest artifact 内 `left_speed=0/right_speed=0` 时，PC summary 显示 L/R=0/0 且仍判定为未证明非零。
- 更新 `docs/product/pc_tools_workstation.md`。

## 验证结果

- 通过：`npm test`，2 个 test files、119 个 tests 全部通过。
- 通过：`npm run lint`，ESLint 无报错。
- 通过：`npm run build`，完成 `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只读 latest artifact，不执行真实 first-jog 或 Nav2。
- 当前真实上位机只读证据仍显示 wheel raw L/R 为 `0/0`，wheel raw L/R 非零尚未完成。
