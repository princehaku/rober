# PC Nav2 位姿提示不再硬挡路线执行

sprint_type: micro

## 实际改动

- 将 `pc-tools/workstation/src/server/robotControlSummary.ts` 的 `nav2_goal_ready` 口径改为只把路线生成和路线点数作为硬条件；小车 map 位姿未显示时只写入 `nav2_goal_next_action` 建议，不再加入 `nav2_goal_blockers`。
- 更新 `pc-tools/workstation/test/catalog.test.ts`，覆盖“路线已生成但小车 map 位姿缺失时仍 ready”的回归场景，并同步既有 planner/controller 未运行场景的 next action。
- 更新 `pc-tools/README.md` 和 `docs/product/pc_tools_workstation.md`，说明自动驾驶路线 ready 不再被 pose 显示状态误挡；真实执行仍需要现场安全确认和固定 Nav2 execute 代理。

## 验证结果

- `npm test -- --run test/catalog.test.ts -t "Nav2 route"`：通过，2 passed / 147 skipped。
- `git diff --check`：通过。
- `npm run lint`：通过。
- `npm run build`：通过；保留既有 Vite chunk size warning。
- `npm test -- --run test/catalog.test.ts`：通过，149 passed。
- `npm test`：首轮失败于既有偶发用例 `does not close wheel raw L/R from static nonzero base feedback samples`；随后单跑该用例通过，最终全量复跑通过，2 files / 354 tests passed。

## 剩余风险

- 本轮只修正 PC summary/文案/test，不发送真实 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 真实小车是否能完成路线执行仍需要现场安全确认后的真实 Nav2 execute/HIL 证据。
