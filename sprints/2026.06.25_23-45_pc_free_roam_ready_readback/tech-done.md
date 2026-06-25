# 2026.06.25 23:45 PC 自动扫图 ready 读回

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：从 `/api/free-roam/autonomy/latest` runtime artifact 推导 `safe_command_boundary.free_roam_autonomy`。只有 runtime 已加载、`cmd_vel_publish_enabled=true`，且所有自动扫图 gates（含 PC 侧 `motion_hil_unlock`）都为 `ready` 时，才显示 `ready`；顶层 `safe_to_control`、`command_dispatch_enabled` 和 `robot_control_executed` 仍保持 false。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏“自动扫图准备”支持 `已就绪` 状态，文案说明上车端自动扫图已就绪但 PC 按钮仍只做流程定位，不直接触发自动发车。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`：补充自动扫图 runtime ready 场景，断言 PC 不调用 manual、`/cmd_vel` 或不存在的 `/api/free-roam/autonomy/start`。
- `docs/product/pc_free_roam_mapping_design.md`、`docs/product/pc_tools_workstation.md`：同步 ready 读回边界和 PC 不直接发车的安全口径。

## 验证结果

- 通过：`npm test -- -t "free-roam autonomy"`（2 test files，3 passed，173 skipped）
- 通过：`npm run lint`
- 通过：`npm run build`
- 通过：`npm test`（2 test files，176 passed）
- 通过：`git diff --check`

## 剩余风险

- 本轮只推进 PC/mock 与 summary readback；没有新增上车端 `/api/free-roam/autonomy/start` 固定代理，也没有做真实自动扫图 HIL。
- `free_roam_autonomy=ready` 只证明上车端 artifact 已报告双重解锁和 gate ready，不证明 PC 已经能一键启动自由探索。
