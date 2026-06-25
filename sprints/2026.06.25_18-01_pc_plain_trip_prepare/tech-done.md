# PC Plain Trip Prepare

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `行程操作` 新增 `准备行程（不发车）`，复用既有 no-motion Nav2 proof refresh；刷新结果以“行程准备已刷新/还没完成”显示，不暴露 Nav2 proof 术语。
- `pc-tools/workstation/test/App.test.ts`：补充普通行程流程断言，确认未勾安全确认时不能准备，勾选后点击只调用 `/api/robot-control/nav2/proof/refresh`，不会调用 execute 或 manual。
- `docs/product/pc_tools_workstation.md`：同步记录普通行程准备入口和不发车边界。

## 验证结果

- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm test -- App.test.ts -t "runs plain trip preflight and execution only after the safety checkbox is checked"`：通过，1 passed / 68 skipped。
- `cd pc-tools/workstation && npm test`：通过，160 tests。
- `cd pc-tools/workstation && npm run build`：通过。
- PC 7001 只读 summary smoke：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`，`keyboard_control_mode=bounded_repeating_manual_pulse`，`free_roam_autonomy=locked`，当前路线 proof 为 `path_generated=false`、`path_generation_succeeded=false`、`path_point_count=0`，`pose=null`；本轮 smoke 没有点击 `准备行程`，没有调用 nav2 proof refresh、execute、manual、keyboard、delivery 或 `/cmd_vel`。

## 剩余风险

- 本轮只把 no-motion 行程准备入口放到普通首屏；真实上位机仍显示路线 proof 未生成，需要现场勾选安全确认后点击 `准备行程（不发车）` 刷新，再检查/执行。
- 当前只读 smoke 仍显示 `pose=null`、`free_roam_autonomy=locked`，完整 Nav2 路线执行、真实自由跑动建图和 delivery success 仍未完成。
