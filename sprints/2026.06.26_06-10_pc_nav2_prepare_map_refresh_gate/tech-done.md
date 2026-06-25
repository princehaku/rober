# PC Nav2 Prepare Map Refresh Gate

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- status: done

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：新增统一的 `canRefreshNav2Proof` 和
  `nav2ProofRefreshButtonLabel`。地图画面或地图 proof 刷新中时，普通首屏 `准备行程（不发车）` 和高级
  `检查路径（高级）` 都显示 `等待地图刷新` 并禁用；`refreshNav2Proof()` 入口同步早退，避免绕过 disabled
  后仍刷新 Nav2 no-motion proof。
- `pc-tools/workstation/test/App.test.ts`：扩展 `blocks visible-route execution while the map preview is refreshing`
  回归测试，覆盖 map preview pending 和 map proof pending 两种状态下，准备行程、高级检查路径、执行图上路线都不会触发
  Nav2 proof refresh、Nav2 execute、manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`：补充 2026-06-26 06:10 的 PC 工作台行为说明。

## 验证结果

- `npm test -- -t "blocks visible-route execution while the map preview is refreshing"`：通过，1 passed / 190 skipped。
- `npm run lint`：通过。
- `npm run build`：通过。
- `npm test`：通过，191 passed。
- `git diff --check`：通过。

## 剩余风险

- 本轮只做 PC 前端 gate 和 mock/DOM 回归验证，没有触发真实上位机 Nav2 proof、execute、manual、keyboard、delivery、stop 或
  `/cmd_vel`；真实机器人现场仍需 operator 在 `0.0.0.0:7001` 工作台确认。
