# 2026-06-23 20:00 Micro Sprint: 当前 0/0 时历史 wheel 材料不点亮收口

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 历史 operator report 中已有 wheel 非零材料，但当前只读 T1001 明确为 L/R=`0/0` 时，`目标收口进度` 的 `wheel raw L/R 非零` 保持 `ready=false`。
  - 仍保留历史材料提示 `已有历史非零材料；当前只读 L/R=0/0，本轮复验需低速重试`，但不再让总进度跳过轮速复验。
  - 不自动试动、不提交 operator report、不执行 Nav2、不提交 delivery complete、不发送 manual、keyboard pulse 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 更新历史 wheel 材料 + 当前 L/R=`0/0` 的回归测试，确认该项保持未完成，总进度先处理轮速记录。
- `docs/product/pc_tools_workstation.md`
  - 同步记录当前 0/0 时历史 wheel 材料不点亮收口。

## 验证结果

- `cd pc-tools/workstation && npm test -- -t "shows historical wheel material separately from current zero readback"`：通过，`1 passed | 143 skipped`。
- `cd pc-tools/workstation && npm test`：通过，`2 passed`、`144 passed`。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，Vite 产物生成成功。
- `git diff --check`：通过。

## 剩余风险

- 当前改动只收紧 PC 收口状态，不证明真实 `wheel raw L/R 非零`、完整 Nav2 路线执行、`delivery success` 或 PC 键盘连续手控。
- 真实上位机当前只读状态仍显示 T1001 可读但 L/R=`0/0`，真实复验仍需现场 operator 明确确认并执行低速试动。
