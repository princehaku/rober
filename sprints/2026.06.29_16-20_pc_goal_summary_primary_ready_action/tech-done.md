# PC 目标 summary 主 ready 动作

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：`RobotControlGoalChecklistSummary` 新增 `primary_ready_action_item_id`、`primary_ready_action_source_card_id`、`primary_ready_action_next_action_plain`、`primary_ready_action_summary_plain`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：从排序后的 `ready_action_items` 派生主 ready 动作，优先级为自由移动、键盘连续手控、完整图上行程、建图启动；fail-closed 和未读到目标时返回空 id 和恢复/刷新提示。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`：同步合同和回归断言，锁定脚本可直接读到“先做自由移动”。
- `docs/product/pc_tools_workstation.md`：同步字段合同和只读边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints"`。
- 通过：`npm --prefix pc-tools/workstation test`，结果 `2 passed` test files，`382 passed` tests。
- 通过：`npm --prefix pc-tools/workstation run build`，TypeScript 与 Vite build 成功；Vite 仍提示单个 chunk 超过 500 kB，这是既有体积提示，不影响本轮 summary 合同。
- 通过：`git diff --check`。
- 通过：本机 PC API 已重启到 `0.0.0.0:7001`，日志输出 `pc-tools workstation API listening on http://0.0.0.0:7001`。
- 通过：只读检查 live `/api/robot-control/summary`，`goal_checklist_summary.primary_ready_action_item_id="free_move"`、`primary_ready_action_source_card_id="free_move"`，且 `ready_action_ids=["free_move","keyboard_continuous_control","nav2_route_execution"]`；`next_action_item_ids` 保持兼容顺序，仍先列画面和雷达缺口。

## 剩余风险

- 本轮只增加只读 summary 字段，不改变已有 `next_action_items` 顺序，不启动自由移动、键盘、Nav2、delivery、stop 或 `/cmd_vel`。
- 真实目标仍需现场安全确认后验证自由移动/键盘/Nav2；相机首帧和雷达新鲜仍是建图验收缺口。
