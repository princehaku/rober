# PC Goal Mapping Next Action

## sprint_type

micro

## 实际改动

- 在 `pc-tools/workstation/src/shared/contracts.ts` 为 `goal_checklist_summary` 增加建图入口字段：
  `mapping_item_id`、`mapping_source_card_id`。
- 在 `pc-tools/workstation/src/server/robotControlSummary.ts` 中返回建图清单项的 source card，保持 `mapping_summary_plain`
  继续说明相机首帧和雷达新鲜缺口。
- 在 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 与 `src/styles.css` 中为目标汇总新增“去建图”按钮。
  按钮只聚焦到自由移动/建图流程安全确认或下一步控件，不自动启动建图。
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
  - `HOST=0.0.0.0 PORT=7001 npm --prefix pc-tools/workstation run api` 已启动，监听 PID `31533`。
  - `curl -fsS http://127.0.0.1:7001/api/health` 返回 `mode=pc_only_readonly_workstation`。
  - `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `mapping_item_id=mapping_start`、`mapping_source_card_id=mapping_start`。
  - live 读数显示建图启动仍 `not_ready`，缺口为 `camera_first_frame` 和 `lidar_fresh`。
  - live 验证只读 summary/health；未调用 manual、Nav2、keyboard、free-roam、delivery、map start、radar start、stop 或 `/cmd_vel`。

## 剩余风险

- 真实建图仍依赖相机首帧和雷达新鲜；当前 live 缺口仍是摄像头无帧、雷达 stopped。
