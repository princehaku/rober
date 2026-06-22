# 2026-06-23 01:55 轮速证据来源提示

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：新增 wheel raw L/R 收口证据来源摘要，区分本轮 first-jog during-motion、只读采样非零和历史 operator report 材料。
- 当历史 wheel 材料存在但当前只读 T1001 为 L/R=`0/0` 时，高级 `目标收口进度` 显示 `已有历史非零材料；当前只读 L/R=0/0，本轮复验需低速重试`。
- 普通首屏 `当前读数` 同步显示 `轮速有历史材料，当前 L/R=0/0`，避免现场把历史材料和当前静态读回混成“当前仍非零”。
- 该改动只调整只读口径和文案，不刷新接口、不调用 first-jog、manual、stop、Nav2、delivery complete 或 `/cmd_vel`，不写 operator report。
- `pc-tools/workstation/test/App.test.ts`：新增历史 wheel 材料 + 当前 L/R=`0/0` 的回归测试，锁定来源化提示。
- `docs/product/pc_tools_workstation.md`：同步记录 wheel raw L/R 证据来源区分。

## 验证结果

- `npm test`：通过，`2 passed (2)`，`127 passed (127)`。
- `npm run lint`：通过，无 ESLint 报错。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮不产生新的 wheel raw L/R 非零证据，只避免 PC UI 把历史材料和当前静态 L/R=`0/0` 混淆。
- 当前上位机只读 `GET /api/base/status` 新鲜 T1001 仍为 L/R=`0/0`。
- 真实本轮复验仍需要现场显式执行低速 first-jog 或受控 manual，并拿到 during-motion T1001 同帧非零 L/R。
