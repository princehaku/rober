# PC 首屏消费主 ready 动作

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏“本轮进度”的 `可先动` 摘要优先显示 `goal_checklist_summary.primary_ready_action_summary_plain`；目标总览的“行程/键盘/自由移动”跳转优先使用 `primary_ready_action_source_card_id`。
- `pc-tools/workstation/test/App.test.ts`：补充 DOM 断言，锁定普通首屏直接显示后端主 ready 动作。
- `docs/product/pc_tools_workstation.md`：同步页面消费 `primary_ready_action_*` 的只读边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "plain"`，结果 `46 passed | 171 skipped`。
- 通过：`npm --prefix pc-tools/workstation test`，结果 `2 passed` test files，`382 passed` tests。
- 通过：`npm --prefix pc-tools/workstation run build`，TypeScript 与 Vite build 成功；Vite 仍提示单个 chunk 超过 500 kB，这是既有体积提示，不影响本轮首屏展示。
- 通过：`git diff --check`。
- 通过：本机 PC API 已重启到 `0.0.0.0:7001`，日志输出 `pc-tools workstation API listening on http://0.0.0.0:7001`。
- 通过：只读检查 live `/api/robot-control/summary`，`primary_ready_action_item_id="free_move"`、`primary_ready_action_source_card_id="free_move"`、`primary_ready_action_summary_plain` 显示“可先做：自由自助移动”；同时 `free_move_start_ready="true"`、`keyboard.start_ready="true"`、`nav2_goal_ready=true`。

## 剩余风险

- 本轮只改变普通首屏展示和焦点跳转，不自动勾选安全确认、不启动自由移动、不启用键盘、不执行 Nav2、不发送 `/cmd_vel`。
- 真实车仍需要现场安全确认后验证：自由移动、键盘连续控制和 Nav2 ROS 模式重跑；相机首帧和雷达新鲜仍卡建图验收。
