# First-Jog Latest Slot Hint Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `firstJogMaterialRestoreSummary`。
  - 高级诊断 `现场点动设置 / 控制边界` 中新增 `first-jog material restore` 行。
  - 当上位机 latest operator report 被送达草稿覆盖、但仍保留视觉材料时，明确展示：
    - operator report 是 latest-only slot；
    - 当前 `site_state`；
    - first-jog 缺失的基础安全字段；
    - 下一步 action 是 restore first-jog confirmation。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 `恢复试动确认` 测试，断言高级诊断展示 latest-only 覆盖原因和恢复 action。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 latest-only operator report 对 first-jog readiness 的影响和 PC 提示。

## 当前真实状态

- 上位机只观察到 `operator_report_latest.json`，没有 operator report 历史列表或分用途 slot。
- 当前 latest report 是 `delivery-draft-smoke-1782102952`，`site_state=delivery_material_draft_not_operator_confirmed`。
- 当前 first-jog 缺 `operator_present`、`physical_clearance_confirmed`、`emergency_stop_ready`，但 `visual_material_ready=true`。

## 验证结果

- `npm test`
  - 通过：`Test Files 2 passed (2)`，`Tests 111 passed (111)`。
- `npm run lint`
  - 通过：`eslint .` 无报错。
- `npm run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。

## 剩余风险

- 本轮仍未执行真实 first-jog/manual 运动。
- wheel raw L/R 非零仍需现场恢复材料后再采 during-motion `T=1001 L/R`。
- delivery success 仍不能宣称完成。
