# PC Mapping Action Motion Flag

## sprint_type

micro

## 实际改动

- 修正 `pc-tools/workstation/src/server/robotControlSummary.ts`：`mapping_start.sends_motion_when_clicked` 只在 `free_roam_mapping_start_ready=true` 时为 true；建图未就绪时不再暗示点击会进入运动流程。
- 更新 `pc-tools/workstation/test/catalog.test.ts`：覆盖建图未就绪时 `can_start_after_safety_confirm=false`、`sends_motion_when_clicked=false`，以及建图 ready 时保持可启动。
- 更新 `pc-tools/workstation/test/App.test.ts` 默认 fixture，避免普通首屏测试数据继续把未就绪建图标记为会发运动。
- 同步更新 `pc-tools/README.md` 和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- Pass: `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "proxies Robot API readback"`，1 passed。
- Pass: `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "marks free-roam autonomy ready"`，1 passed。
- Pass: `npm --prefix pc-tools/workstation test -- App.test.ts -t "plain"`，46 passed。
- Pass: `npm --prefix pc-tools/workstation test`，2 files passed，379 tests passed。
- Pass: `npm --prefix pc-tools/workstation run build`，TypeScript 与 Vite build 通过；Vite 仍提示既有 chunk size warning。
- Pass: PC API 已重启到 `0.0.0.0:7001`，监听 PID 75148。
- Pass: 只读 curl `http://127.0.0.1:7001/api/robot-control/summary` 返回 `robot_api_connection.status=readable`、`loaded_count=15`、`failed_count=0`，live `mapping_start.status=not_ready`、`can_start_after_safety_confirm=false`、`sends_motion_when_clicked=false`、`free_move.sends_motion_when_clicked=true`、`keyboard_control.sends_motion_when_clicked=false`。
- Pass: 只读 7071 诊断仍返回 `robot_api_port_7071_mismatch_use_8787` 作为首位 blocker，并保持 `safe_to_control=false`、`primary_actions_enabled=false`。

## 剩余风险

- 本轮只修正只读 summary 结构化语义；不启动建图、不执行 Nav2、不调用 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 现场仍显示建图启动缺口为 `camera_first_frame`、`lidar_fresh`；需要相机首帧和雷达新鲜后才能进入建图启动。
