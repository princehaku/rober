# PC Live Closure Next Step Label Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `plain-live-closure-go` 当前卡点按钮从固定“去处理当前卡点”改为按状态显示具体下一步。
  - 画面缺口显示“去看实时画面”，轮速复验未勾安全确认显示“去勾行程安全确认”，勾确认后显示“去重跑图上行程”。
  - 新增 `data-focus-target-kind`，让现场脚本直接确认实际落点是 `camera_preview`、`trip_safety_confirm` 或 `trip_execute_button`。
- `pc-tools/workstation/test/App.test.ts`
  - 锁定默认画面缺口场景的按钮文案和 `data-focus-target-kind=camera_preview`。
  - 锁定 `needs_wheel_rerun` 场景未勾确认时聚焦安全确认框，勾确认后文案和 kind 切到行程执行按钮。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步说明当前卡点按钮只是聚焦真实下一手控件，不自动勾确认、不执行 Nav2、不发送底盘命令。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default|keeps live closure wheel rerun as a focus-only Nav2 action"`
  - 通过：`Test Files 1 passed (1)`，`Tests 2 passed | 222 skipped (224)`。
- `npm test -- --run`
  - 通过：`Test Files 2 passed (2)`，`Tests 398 passed (398)`。
- `npm run lint`
  - 通过：0 error，保留既有 `RobotControlConsolePanel.vue` 4 个 Vue multiline warning。
- `npm run build`
  - 通过：生成 `dist/assets/index-pJJV0ri8.js` 与 `dist/assets/index-BBcFFzNr.css`。
- `git diff --check`
  - 通过，无 whitespace 错误。
- 7001 重启与只读 smoke
  - 已重启 Node 到 `0.0.0.0:7001`，新 PID `72915`。
  - `GET http://127.0.0.1:7001/` 返回新 bundle `index-pJJV0ri8.js`。
  - bundle 只读 grep 命中 `plain-live-closure-go`、`data-focus-target-kind`、`trip_safety_confirm`、`trip_execute_button`、`去勾行程安全确认`、`去重跑图上行程` 和 `去看实时画面`。
  - `GET /api/robot-control/summary?base_url=http%3A%2F%2F192.168.1.11%3A8787` 为只读请求，未发送运动；返回 `live_status=needs_wheel_rerun`、`target=nav2_route`、`needs_wheel_rerun=true`。

## 剩余风险

- 本轮只改当前卡点按钮的普通用户下一步文案和落点合同，不执行真实 Nav2 重跑、不证明真实 wheel raw L/R 非零。
- 现场当前卡点仍为 `needs_wheel_rerun`，需要用户明确安全确认后在行程卡重跑图上行程，才能完成同窗口轮速 L/R 复验。
