# PC Summary 历史底盘 Debug 读回不再误阻塞

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：把 `/api/base/status` 中的历史 `bridge_command_debug.robot_control_executed=true` 从当前 GET summary 的危险动作扫描里排除；根级 `robot_control_executed=true` 仍然保持危险字段，继续 fail-closed。
- `pc-tools/workstation/test/robotControlSummary.test.ts`：新增回归测试，证明普通 PC 页面打开时不会因为历史底盘命令 debug 读回被误判为当前会发车，同时继续证明根级危险字段仍被拦截。
- `docs/product/pc_tools_workstation.md` 与 `docs/process/okr_progress_log.md`：同步记录 PC summary 的只读语义边界，说明该修正不执行 Nav2、手控、键盘、delivery、stop 或 `/cmd_vel`。

## 验证结果

- `npm test -- test/robotControlSummary.test.ts --run`：15 tests OK。
- `npm test -- test/App.test.ts -t "current facts|keyboard|map display|direct map|camera|Nav2|dangerous" --run`：99 tests OK / 140 skipped。
- `npm run build`：通过，仅保留 Vite chunk size warning。

## 剩余风险

- 本轮只修正 PC summary 对历史读回的归因，不执行真实底盘运动命令；wheel raw L/R 非零、完整 Nav2 路线执行和 delivery success 仍需继续实机闭环。
- 摄像头当前仍是 UVC 枚举正常但首帧 buffer 为 0 的硬件/链路问题，不由本轮代码修复覆盖。
