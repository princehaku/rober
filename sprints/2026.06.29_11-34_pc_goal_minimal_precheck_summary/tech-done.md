# PC Goal Minimal Precheck Summary

## sprint_type

micro

## 实际改动

- 在 `pc-tools/workstation/src/shared/contracts.ts` 为 `goal_checklist_summary` 增加最小预检字段：
  `safety_precheck_source_card_id`、`safety_precheck_next_action_plain`、`safety_precheck_summary_plain`。
- 在 `pc-tools/workstation/src/server/robotControlSummary.ts` 中为目标汇总生成统一最小预检摘要：
  发车前只需要现场安全确认，相机和雷达不作为移动或行程发车前额外预检。
- 在 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 与 `src/styles.css` 中显示该摘要，
  并新增“去勾确认”按钮。按钮只做 scroll/focus，不自动勾选、不触发任何控制。
- 同步更新 `pc-tools/README.md` 与 `docs/product/pc_tools_workstation.md`。

## 验证结果

- 通过：
  `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints"`
  - 结果：1 个文件通过，1 个测试通过，160 个跳过。
- 通过：
  `npm --prefix pc-tools/workstation test -- App.test.ts -t "renders Robot Control V1 by default"`
  - 结果：1 个文件通过，1 个测试通过，214 个跳过。
- 通过：
  `npm --prefix pc-tools/workstation test`
  - 结果：2 个文件通过，376 个测试通过。
- 通过：
  `npm --prefix pc-tools/workstation run build`
  - 结果：TypeScript、Vite client build、server TypeScript 通过；仅保留既有 Vite chunk size warning。
- 通过 PC API 只读 live 验证：
  - `HOST=0.0.0.0 PORT=7001 npm --prefix pc-tools/workstation run api` 已启动，监听 PID `35199`。
  - `curl -fsS http://127.0.0.1:7001/api/health` 返回 `mode=pc_only_readonly_workstation`。
  - `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `safety_precheck_source_card_id=free_move`，
    `safety_precheck_summary_plain` 显示“发车前预检已精简：只需要现场安全确认”。
  - live 验证只读 summary/health；未调用 manual、Nav2、keyboard、free-roam、delivery、map start、radar start、stop 或 `/cmd_vel`。

## 剩余风险

- 真实运动入口仍必须由现场人员勾选安全确认并显式点击；本轮只改善最小预检的可见性。
