# PC Free Roam Autonomy Gates

- sprint_type: micro
- time: 2026-06-25 20:58 Asia/Shanghai
- owner: full-stack-software-engineer
- safe_to_control: false
- real_motion_triggered: false

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：在 `safe_command_boundary` 合同中新增 `free_roam_autonomy_gates`，用 `ready/blocked/not_proven` 表达自动扫图逐项门禁。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：默认 fail-closed summary 增加上车端自动停止、雷达避障、地图刷新、停止按钮兜底、真车验证五项门禁；自动扫图仍固定 `locked`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏“自动扫图准备”显示逐项门禁和下一步提示，按钮仍禁用，不绑定自动移动。
- `pc-tools/workstation/test/App.test.ts`：补充 Robot Control V1 默认渲染断言，覆盖门禁行和普通用户文案。
- `docs/product/pc_free_roam_mapping_design.md`、`docs/product/pc_tools_workstation.md`：同步自动扫图门禁的产品边界。

## 验证结果

- 通过：`npm test -- --testNamePattern "renders Robot Control V1 by default"`，`1 passed | 166 skipped`。
- 通过：`npm run lint`。
- 通过：`npm test`，`167 passed`。
- 通过：`npm run build`。
- 通过：`git diff --check`。
- 已复原旧 DOM smoke artifact 的 `checked_at` 测试副作用，未把历史证据时间戳带入本次提交。

## 剩余风险

- 本轮只做 PC fail-closed 可视化和合同扩展，没有实现上车端自动探索状态机。
- `free_roam_autonomy_gates` 当前由 PC summary 默认 locked 边界提供，真实自动扫图开放仍需要上车端 watchdog、雷达避障、现场低速验证记录和新的安全合同。
