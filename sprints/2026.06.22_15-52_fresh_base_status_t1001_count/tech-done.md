# Fresh Base Status T1001 Count

sprint_type: micro

## 实际改动

- Robot Control summary 对 `/api/base/status` 内 fresh `feedback_readback.t1001_feedback_frame_count` 增加优先级派生。
- 当 base status 同时带有 stale `feedback_samples_latest` 时，PC 摘要优先显示 fresh T=1001 frame count。
- 补 catalog 测试覆盖真实形态：fresh base/status 为 12 帧、stale samples latest 为 3 帧时，PC summary 显示 12 帧和 L/R=0/0。
- 更新 `docs/product/pc_tools_workstation.md`。

## 验证结果

- 通过：`npm test`，2 个 test files、120 个 tests 全部通过。
- 通过：`npm run lint`，ESLint 无报错。
- 通过：`npm run build`，完成 `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只读摘要，不执行真实 first-jog/manual。
- 当前真实 wheel raw L/R 仍是 `0/0`，非零证明尚未完成。
