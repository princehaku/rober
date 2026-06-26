# PC 当前轮速读回所见即所得

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `底盘读回` 不再把历史 `wheel_feedback_lr_nonzero_proven=true` 直接展示成当前轮速非零。
  - 当历史材料存在但最新 `T=1001 L/R=0/0` 时，明确提示“当前轮速是 L/R=0/0，本轮仍需底盘试动读非零”。
- `pc-tools/workstation/test/App.test.ts`
  - 新增历史非零材料 + 当前 `L/R=0/0` 的回归用例，确认不会调用 manual 代理，也不会把 blocker 误判为已完成。
- `docs/product/pc_tools_workstation.md`
  - 同步记录普通首屏读回口径：历史材料只能解释曾经通路有效，不能替代本轮 wheel raw L/R 非零、完整 Nav2 路线执行或 delivery success。

## 验证结果

- `npm test -- --testNamePattern "historical wheel material|historical base nonzero|current wheel L/R"`：通过，3 passed。
- `npm test`：通过，2 test files / 256 tests passed。
- `npm run lint`：通过。
- `npm run build`：通过；保留既有 Vite chunk size warning。
- `git diff --check`：通过。

## 剩余风险

- 该 sprint 修正 PC 首屏读回和验收口径，不直接改变 WAVE ROVER、电机使能、底盘模式、Nav2 控制器或摄像头 UVC 首帧问题。
- 当前现场底盘静态读回仍可能是 `L/R=0/0`；需要通过首屏 `底盘试动` 或 Nav2 执行期间同帧 `T=1001 L/R` 非零继续复验。
