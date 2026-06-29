# PC Goal Motion Next Action

## sprint_type

micro

## 实际改动

- 在 `pc-tools/workstation/src/shared/contracts.ts` 为 `goal_checklist_summary` 增加移动优先与建图摘要字段：
  `first_motion_item_id`、`first_motion_source_card_id`、`motion_next_action_plain`、`motion_summary_plain`、
  `mapping_next_action_plain`、`mapping_summary_plain`。
- 在 `pc-tools/workstation/src/server/robotControlSummary.ts` 中把“本轮目标第一缺口”和“可先移动入口”分开计算。
  当自由移动未 ready 但键盘连续手控 ready 时，summary 会提示可以先用键盘连续手控；相机/雷达缺口只归入建图摘要。
- 在 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 与 `src/styles.css` 中让普通首屏显示移动优先摘要、
  建图摘要和“先动车”按钮。按钮只做页面内 scroll/focus，不自动勾选安全确认、不发车。
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
  - `HOST=0.0.0.0 PORT=7001 npm --prefix pc-tools/workstation run api` 已启动，监听 PID `12547`。
  - `curl -fsS http://127.0.0.1:7001/api/health` 返回 `mode=pc_only_readonly_workstation`。
  - `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `first_incomplete_item_id=camera_wysiwyg`、
    `first_motion_item_id=free_move`，并显示“可先自由移动；相机和雷达只影响建图验收”。
  - live 验证只读 summary/health；未调用 manual、Nav2、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

## 剩余风险

- 真实小车运动、Nav2 execute 和建图启动仍需现场勾选安全确认后手动触发；本轮未调用任何运动 endpoint。
