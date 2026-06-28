# 2026.06.29 10:50 PC free-roam next action summary

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：为 `safe_command_boundary` 增加 `free_roam_autonomy_next_action`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：按自由移动状态与建图验收缺口生成顶层下一步，不要求外部页面展开 gates 才能解释当前状态。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`：补充 start-ready、mapping-ready 和默认 fixture 的新字段断言。
- `docs/product/pc_tools_workstation.md`：同步记录新字段语义和只读安全边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- --run test/catalog.test.ts -t "keeps free-roam start ready|marks free-roam autonomy ready"`，结果 `1 passed`、`2 passed | 152 skipped`。
- 通过：`npm --prefix pc-tools/workstation test`，结果 `2 passed`、`366 passed`。
- 通过：`npm --prefix pc-tools/workstation run build`，结果 `tsc` 和 `vite build` 成功；Vite 仅保留既有大 chunk warning。
- 通过：`git diff --check -- pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/server/robotControlSummary.ts pc-tools/workstation/test/App.test.ts pc-tools/workstation/test/catalog.test.ts docs/product/pc_tools_workstation.md sprints/2026.06.29_10-50_pc_free_roam_next_action_summary/tech-done.md`，无 whitespace 问题。
- 通过：重启 PC Node 到 `0.0.0.0:7001` 后只读请求 `GET /api/robot-control/summary`；返回 `free_roam_autonomy=start_ready`、`free_roam_motion_start_ready=true`、`free_roam_mapping_ready=false`、`free_roam_mapping_missing_reasons=camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview`、`free_roam_autonomy_next_action=勾选现场安全确认后可先自由移动；建图验收还差：画面首帧、雷达新鲜、地图记录、地图画面`、`robot_control_executed=false`。

## 剩余风险

- 本轮只补 PC summary 的自由移动/建图下一步口径，不执行自由移动、不启动地图记录、不证明真实建图。
- 未获得本轮现场安全确认，因此不执行 Nav2 goal、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
