# 2026.06.28 16:25 PC keyboard current fact runtime

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `当前事实` 的键盘行现在优先显示键盘连续控制运行态。
  - 启用后显示“已启用”，按住方向键时显示方向、连续低速脉冲、轮速 L/R 和“松开即停”，验证完成后显示连续 2/2 与停止已发送。
  - 该变更只消费 PC 本地键盘状态和固定 manual proxy 回包，不新增控制接口。
- `pc-tools/workstation/test/App.test.ts`
  - 在 PC 键盘连续手控回归测试中覆盖当前事实条的启用、按住、松开和验证完成状态。
- `docs/product/pc_tools_workstation.md`
  - 同步记录键盘当前事实运行态的产品口径和安全边界。

## 验证结果

- `npm test -- --run test/App.test.ts -t "enables non-stop motion only after complete operator material"`：通过，1 个测试文件通过，1 个测试通过，191 个跳过。
- `npm test`：通过，2 个测试文件通过，339 个测试通过。
- `npm run lint`：通过。
- `npm run build`：通过；仍有既有 Vite chunk size warning。
- `git diff --check`：通过。

## 剩余风险

- 本轮只修正 PC 顶部事实条和键盘控制状态的一致性，不证明真实底盘已移动。
- 真实 PC 键盘连续控制仍需现场安全确认后实车验证 wheel raw L/R 非零和 stop 收口。
