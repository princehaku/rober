# PC 首屏建图启动事实展示

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation/src/server/robotControlSummary.ts` 的 `current_fact_plain` 中新增 `建图启动` 片段，与 `建图验收` 分开展示。
- 在 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 中让普通首屏当前事实和自由移动/建图卡片优先展示 `mapping_start_*` / `free_roam_mapping_start_*`，旧响应缺字段时按当前画面和雷达事实 fallback。
- 更新 `pc-tools/workstation/test/App.test.ts`，锁定首屏同时展示“建图启动”和“建图验收”，并确保未 ready 时仍说明自由移动不受影响。
- 更新 `docs/product/pc_tools_workstation.md` 和 `pc-tools/README.md`，记录首屏消费建图启动口径。

## 验证结果

- 已通过定向前端验证：`npm --prefix pc-tools/workstation test -- App.test.ts -t "free-roam|当前事实|mapping|建图"`，结果 `26 passed | 189 skipped`。
- 已通过定向 summary 验证：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "current_fact|free-roam"`，结果 `12 passed | 148 skipped`。
- 已通过全量 PC 测试：`npm --prefix pc-tools/workstation test`，结果 `375 passed`。
- 已通过 PC build：`npm --prefix pc-tools/workstation run build`，`tsc` 与 `vite build` 通过；仅保留既有 Vite chunk size 提示。
- 已重启本地 PC API 到 `0.0.0.0:7001`，新 PID 为 `40386`。
- 已通过 7001 只读 summary live 验证：`current_fact_plain` 同时包含 `建图启动` 和 `建图验收`；当前 `mapping_start_ready=false`，启动缺口为 `camera_first_frame,lidar_fresh`，自由移动仍为 `start_ready`。

## 剩余风险

- 本轮只改只读 summary/UI 展示，不调用 free-roam、建图、manual、keyboard、Nav2、delivery、stop 或 `/cmd_vel`。
- 真实车当前相机首帧和雷达 fresh 仍取决于现场硬件；页面会显示建图启动缺口，但不会代替硬件复验。
