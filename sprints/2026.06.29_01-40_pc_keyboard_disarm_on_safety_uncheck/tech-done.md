# PC 键盘安全确认取消即撤销控制

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏统一安全确认取消后，若 PC 键盘已启用或正在按住方向，立即释放键盘控制权。
  - 未按住方向时只撤销 armed 状态，不发送 manual/stop。
  - 正在按住方向时复用既有 `stopKeyboardControl()` / 固定 stop 代理收口，并把停止原因翻译为“安全确认取消”。
- `pc-tools/workstation/test/App.test.ts`
  - 增加安全确认取消的两个回归：armed 未按住不发运动；按住中取消会发一次 stop、禁用方向键且不触发 Nav2/`/cmd_vel`。
  - 启用 Vue Test Utils 自动卸载，清理每个用例挂载出的全局键盘监听和 timer，避免跨用例污染。
- `pc-tools/README.md`、`docs/product/pc_free_roam_mapping_design.md`
  - 同步记录“取消安全确认即撤销 PC 键盘控制权”的普通用户口径。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "safety confirmation"`：通过，1 个文件，4 个相关用例通过。
- `cd pc-tools/workstation && npm test -- --run test/App.test.ts`：通过，207 个用例通过。
- `cd pc-tools/workstation && npm test -- --run`：通过，2 个文件，356 个用例通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍提示单 chunk 大于 500 kB，这是既有体积提示，不影响构建。
- `git diff --check`：通过。

## 剩余风险

- 本轮未连接真实上车机，也未发送真实 manual/Nav2/free-roam/delivery/stop 或 `/cmd_vel`；验证范围是 PC 前端 mock 回归、静态检查和生产构建。
- 取消安全确认时如果真实车已经在执行上车端自主状态机，仍需要使用自由移动/Nav2 专用停止入口收口；本轮只处理 PC 键盘连续手控的本地 armed/hold 状态。
