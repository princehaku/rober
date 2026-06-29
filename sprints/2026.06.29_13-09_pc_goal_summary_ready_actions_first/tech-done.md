# PC Goal Summary Ready Actions First

## sprint_type

micro

## 实际改动

- 修正 `pc-tools/workstation/src/server/robotControlSummary.ts`：`goal_checklist_summary.summary_plain` 在存在 ready / needs_safety_confirm 项时，先列出“现场可先收口 N 项”，再提示“先补条件”。
- 更新 `pc-tools/workstation/test/catalog.test.ts`：覆盖 summary 构造时，键盘连续手控和自由移动可先收口，不被画面缺口遮住。
- 更新 `pc-tools/workstation/test/App.test.ts` 默认 fixture 与断言：普通首屏目标总览显示可先收口项，并继续显示画面补条件。
- 同步更新 `pc-tools/README.md` 和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- Pass: `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "proxies Robot API readback"`，1 passed。
- Pass: `npm --prefix pc-tools/workstation test -- App.test.ts -t "renders Robot Control V1"`，1 passed。
- Pass: `npm --prefix pc-tools/workstation test`，2 files passed，379 tests passed。
- Pass: `npm --prefix pc-tools/workstation run build`，TypeScript 与 Vite build 通过；Vite 仍提示既有 chunk size warning。
- Pass: PC API 已重启到 `0.0.0.0:7001`，监听 PID 81294。
- Pass: 只读 curl `http://127.0.0.1:7001/api/robot-control/summary` 返回 `robot_api_connection.status=readable`、`loaded_count=15`、`failed_count=0`，`goal_checklist_summary.summary_plain` 包含“现场可先收口 3 项：完整行程执行、键盘连续手控、自由自助移动”，同时 `blocked_action_items` 仍列出画面、雷达点贴图、传感器 ready 后建图。
- Pass: 只读 7071 诊断仍返回 `robot_api_port_7071_mismatch_use_8787` 作为首位 blocker，并保持 `safe_to_control=false`、`primary_actions_enabled=false`。

## 剩余风险

- 本轮只修正只读 summary 文案；不自动勾选安全确认、不执行 Nav2、不启用 keyboard/free-roam、不启动建图、delivery、stop 或 `/cmd_vel`。
- 现场仍显示相机 `source_first_frame_failed`、雷达 `radar_stopped`；这些缺口继续阻止画面/雷达贴图/建图目标完成，但不阻止安全确认后的 Nav2 重跑、键盘连续手控和自由移动入口。
