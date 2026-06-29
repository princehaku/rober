# PC Goal Radar Next Action

## sprint_type

micro

## 实际改动

- 在 `pc-tools/workstation/src/shared/contracts.ts` 为 `goal_checklist_summary` 增加雷达贴图专用字段：
  `radar_item_id`、`radar_source_card_id`、`radar_next_action_plain`、`radar_summary_plain`。
- 在 `pc-tools/workstation/src/server/robotControlSummary.ts` 中把“雷达点是否贴到当前地图”从总目标缺口里单独拆出。
  当旧来源点存在但当前地图未贴点时，summary 会明确旧点只作诊断，不能当作当前 marker。
- 在 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 与 `src/styles.css` 中让普通首屏目标汇总显示雷达摘要，
  并新增“去看雷达点”按钮。按钮只做 scroll/focus，不自动启动雷达或刷新地图。
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
  - `HOST=0.0.0.0 PORT=7001 npm --prefix pc-tools/workstation run api` 已启动，监听 PID `27497`。
  - `curl -fsS http://127.0.0.1:7001/api/health` 返回 `mode=pc_only_readonly_workstation`。
  - `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `radar_item_id=radar_map_points_wysiwyg`、
    `radar_source_card_id=radar_map_points`，`radar_summary_plain` 显示“雷达点还没有贴到当前地图”。
  - live 读数显示 `map_radar_overlay_status=not_current`、当前贴图点 `0`、旧来源点 `81`；旧点只作诊断。
  - live 验证只读 summary/health；未调用 manual、Nav2、keyboard、free-roam、delivery、radar start、map refresh、stop 或 `/cmd_vel`。

## 剩余风险

- 真实雷达当前仍是 stopped；本轮只改善雷达贴图缺口在 PC 首屏的可见性，未启动雷达。
