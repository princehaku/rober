# PC 本轮进度主动作对齐 Nav2 重跑

sprint_type: micro

## 实际改动

- `goal_checklist` 的 `nav2_route_execution.title` 在轮速复验场景下改为 `重跑图上行程并复验轮速`，与现场验收包 display label 保持一致。
- `goal_checklist_summary` 的 ready 主动作排序改为：当 Nav2 已可重跑时优先 `nav2_route_execution`，其次键盘连续手控、自由自助移动；当 Nav2 不 ready 时仍保留自由移动/键盘等可先动入口排序。
- PC 首屏“本轮进度”的主 ready 按钮因此指向图上行程卡点，避免与现场验收主动作互相打架；自由移动仍保留在“可先动”列表中。
- 同步更新 `docs/product/pc_tools_workstation.md` 和 summary 单测期望。

## 验证结果

- `npm test -- --run robotControlSummary.test.ts`：通过，10 tests passed。
- `npm test -- --run robotControlSummary.test.ts App.test.ts catalog.test.ts`：通过，3 files / 428 tests passed。
- `npm run lint`：通过。
- `git diff --check`：通过。
- `npm run build`：通过，Vite 仅保留既有 bundle size warning。
- 7001 已重启并监听 `*:7001`。
- `curl http://127.0.0.1:7001/api/robot-control/summary` 只读 smoke：`goal_checklist_summary.primary_ready_action_item_id=nav2_route_execution`，ready titles 为 `重跑图上行程并复验轮速、键盘连续手控、自由自助移动`。
- Chrome headless DOM smoke：`plain-goal-progress-primary-ready-action` 显示 `去图上行程`，`plain-goal-progress-move-now` 的主动作显示 `重跑图上行程并复验轮速`，现场验收并行动作摘要也保持同一主动作。

## 剩余风险

- 本轮仍未获得新的现场安全确认，未发送 Nav2/manual/keyboard/free-roam/建图/stop 或 `/cmd_vel`；wheel L/R 非零、delivery success、键盘连续运动、自由移动运行和建图启动仍需现场执行后复验。
- 相机仍提示 USB 12M full-speed，建图启动还缺 `camera_first_frame`；本轮只修正 PC 首屏主动作对齐，不处理物理相机链路。
