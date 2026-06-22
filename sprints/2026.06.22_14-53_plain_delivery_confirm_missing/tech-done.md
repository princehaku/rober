# Plain Delivery Confirm Missing Summary

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- date: 2026-06-22

## 实际改动

- 普通首屏“最终确认”在送达材料已预填后显示剩余人工确认项。
- 缺项提示覆盖：人在旁边可接管、周围安全、停止手段就绪、已观察到到达/移动、已观察到停止、视频和行程材料已核对、确认已投放/送达。
- 全部勾选后显示“全部确认项已勾选，可以提交。”，但仍需要用户点击 `确认送达` 才会提交。
- 更新 Vue/Vitest 回归，覆盖缺项数量、关键缺项文案和全部勾选后的可提交提示。
- 更新 `docs/product/pc_tools_workstation.md`，记录该提示不自动勾选、不提交、不置 true。

## 验证结果

- `npm test`：通过，2 个测试文件、116 个用例。
- `npm run lint`：通过。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过。

## 只读现场状态

- 上位机 `/api/nav2/goal/execution/latest` 仍读到 `goal_succeeded` artifact：`o11-nav2-goal-execution-1782099547218`。
- 上位机 `/api/base/status` 和 `/api/base/feedback-samples/latest` 可读到 vendor `T=1001`，但 L/R 仍是 `0/0`，wheel raw L/R 非零未证明。
- 上位机 `/api/delivery/latest` 仍为 `delivery_success=false`，缺人工最终确认、observed motion/stop 和 delivery success claim。

## 剩余风险

- 本轮只降低最终确认漏勾概率，不执行真实送达确认。
- wheel raw L/R 非零、delivery success 和真实键盘连续手控仍需要现场安全确认后产生 HIL 证据。
