# PC 可收口动作按自由移动优先

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation/src/server/robotControlSummary.ts` 中为 `goal_checklist_summary.ready_action_items[]` 增加只读展示排序：自由自助移动、键盘连续手控、完整行程执行、建图启动。
- 同步调整 `summary_plain` 里的“现场可先收口”列表，保证列表顺序和“先做：自由自助移动”一致。
- 更新 `pc-tools/workstation/test/catalog.test.ts` 与 `pc-tools/workstation/test/App.test.ts` 的目标总览断言。
- 更新 `pc-tools/README.md` 与 `docs/product/pc_tools_workstation.md`，记录本轮只读排序合同。

## 验证结果

- 已通过全量 PC 测试：`npm --prefix pc-tools/workstation test`，结果 `379 passed`。
- 已通过 PC build：`npm --prefix pc-tools/workstation run build`，`tsc` 与 `vite build` 通过；仅保留既有 Vite chunk size 提示。
- 已重启本地 PC API 到 `0.0.0.0:7001`，新 PID 为 `37371`。
- 已通过 7001 只读 summary live 验证：`summary_plain` 显示“现场可先收口 3 项：自由自助移动、键盘连续手控、完整行程执行”，`ready_action_items[]` 顺序为 `free_move -> keyboard_continuous_control -> nav2_route_execution`。

## 剩余风险

- 本轮只改 PC 只读 summary 和普通首屏展示顺序，不调用 Nav2 execute、不启用键盘、不启动自由移动、不启动建图、不发送 manual、delivery、stop 或 `/cmd_vel`。
- 相机首帧、雷达新鲜点、完整 Nav2 同窗口轮速 L/R 非零仍需要现场真实硬件验证。
