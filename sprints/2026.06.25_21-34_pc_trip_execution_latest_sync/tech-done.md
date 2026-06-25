# PC 行程执行 latest 同步

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏点击 `执行图上路线` 且 execute proxy 返回 `execution_forwarded` 后，自动追加一次只读 `loadNavGoalExecutionLatest()`。
  - 执行结果或 latest 中的 `evidence_ref` 会继续预填送达 `route/map` 材料；如果本轮行程已完整成功，再读取一次 delivery latest 让送达卡片和行程证据口径对齐。
  - 该流程不自动确认送达、不提交 delivery complete、不发送 manual/keyboard pulse/stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 新增可见图上路线执行用例，验证执行后 latest/delivery latest 只读同步、送达 route ref 预填、送达提交仍禁用，并确认未发送手控、delivery complete 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 记录执行成功后的 latest 同步和送达材料预填边界。

## 验证结果

- 已通过：`npm test -- --testNamePattern "syncs latest readbacks"`，`1 passed / 167 skipped`。
- 通过：`npm run lint`。
- 通过：`npm test`，`168 passed`。
- 通过：`npm run build`。
- 通过：`git diff --check`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`，`node` 监听 `TCP *:7001`。

## 剩余风险

- 本轮没有触发真实 Nav2 execute、manual、keyboard pulse、delivery complete、stop 或 `/cmd_vel`。
- 完整 Nav2 路线执行仍需要现场 operator 显式点击执行，并由上位机真实 `goal_succeeded` 与反馈样本证明；本轮只改善 PC 执行后的只读闭环和送达材料衔接。
