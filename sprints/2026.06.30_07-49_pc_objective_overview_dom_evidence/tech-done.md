# PC 目标总览 DOM 证据 micro sprint

- sprint_type: micro
- 时间：2026-06-30 07:49 CST
- owner：User Touchpoint Full-Stack Engineer（主会话直接执行；本轮按用户要求不调用 subagent）

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 扩展普通首屏 `目标总览` 的四个目标组：行程/键盘/自由移动、画面/地图/雷达点、发车前确认、自由移动到建图。
  - 每行新增结构化 DOM 证据：`data-objective-id`、`data-state`、`data-completed`、`data-actionable`、`data-missing-count`、`data-item-ids`、`data-source-card-id`、`data-next-action`、`data-sends-motion-when-clicked=false`。
  - 这些字段只派生自现有 `goal_checklist` 和 `goal_checklist_summary`，不新增控制动作。
- `pc-tools/workstation/test/App.test.ts`
  - 补默认首屏目标总览 DOM 合同断言。
- `pc-tools/README.md`
  - 同步普通首屏目标总览结构化验收合同。
- `docs/product/pc_tools_workstation.md`
  - 同步 PC 工作站产品边界。

## 验证结果

- 已通过：`npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`
- 已通过：`npm test -- --run`（389 passed）
- 已通过：`npm run build`（产物 `index-Df6-n1hi.js` / `index-Cmol8DJx.css`）
- 已通过：`git diff --check`

## 剩余风险

- 本轮只补 PC 首屏 DOM 合同和测试，未执行真实小车 HIL。
- 完整目标完成仍需要真实上车验证：Nav2 完整路线、键盘连续手控、画面/地图/雷达 WYSIWYG、自由移动和建图启动。
