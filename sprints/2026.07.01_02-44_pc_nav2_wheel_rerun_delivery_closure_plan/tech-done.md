# PC Nav2 轮速复验到送达闭环计划

sprint_type: micro

## 实际改动

- `live_closure_summary` 新增轮速复验闭环字段：重跑 checklist、验收口径、验收只读 endpoint、送达成功下一步和固定送达 latest/complete endpoint。
- 普通首屏新增 `plain-wheel-rerun-closure-plan`，在 `needs_wheel_rerun` 时直接说明：勾安全确认、执行图上路线、读取 latest/轮速/summary、确认同窗口 wheel L/R 非零、再确认本轮 delivery success。
- 当前卡点 DOM 和“去重跑/去勾安全确认”按钮同步暴露这些字段；按钮仍只聚焦，不自动执行 Nav2 或任何运动。
- 同步更新 `docs/product/pc_tools_workstation.md`。

## 验证结果

- 通过：`npm test -- test/robotControlSummary.test.ts --run`，1 个文件、6 条测试通过。
- 通过：`npm test -- test/App.test.ts -t "wheel rerun|live closure" --run`，命中 1 条 live closure / wheel rerun DOM 测试通过。
- 通过：`npm run build`，TypeScript app/server 与 Vite build 通过；仅保留既有 chunk size warning。
- 通过：`npm test -- --run`，3 个文件、413 条测试通过。
- 通过：`npm run lint`，0 error，4 个既有 Vue 多行 HTML warning。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `0.0.0.0:7001` 后只读 `GET /api/robot-control/summary`，返回 `status=needs_wheel_rerun`、`needs_same_window_wheel_rerun=true`、`wheel_rerun_checklist_plain` 含同窗口 wheel L/R 与 delivery success、`wheel_rerun_acceptance_endpoints=/api/robot-control/nav2/goal/execution/latest,/api/robot-control/base/feedback-samples,/api/robot-control/summary,/api/robot-control/delivery/latest`、`fixed_wheel_rerun_delivery_complete_endpoint=/api/robot-control/delivery/complete`、`wheel_rerun_delivery_complete_sends_motion=false`。

## 剩余风险

- 本轮不发送 Nav2、manual、keyboard、free-roam、delivery complete、stop 或 `/cmd_vel`；真实轮速非零和 delivery success 仍需要现场安全确认后操作验证。
- 当前 live 状态仍显示 `needs_wheel_rerun`，相机首帧仍未恢复，建图启动仍缺 `camera_first_frame`。
