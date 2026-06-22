# Plain Wheel Zero Retry Hint

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- date: 2026-06-22

## 实际改动

- 普通首屏 `试动一下` 返回 during-motion T1001 帧、但 wheel raw L/R 仍为 `0/0` 时，显示现场排查提示。
- `轮速记录` 面板同步进入 `待重试`，提示检查电机使能、供电、模式和现场空间后重试。
- `保存轮速记录` 仍只在 `wheel_feedback_lr_nonzero_proven=true` 时可用；L/R 为 `0/0` 不会保存 operator report。
- 更新 Vue/Vitest 回归，覆盖 forwarded first-jog、L/R=0/0、保存按钮禁用，以及不调用 operator report/manual。
- 更新 `docs/product/pc_tools_workstation.md`，记录该提示不把 `0/0` 当作完成证据。

## 验证结果

- `npm test`：通过，2 个测试文件、117 个用例。
- `npm run lint`：通过。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过。

## 剩余风险

- 本轮只提升轮速失败后的现场排查可读性，不执行真实重试。
- 真实 wheel raw L/R 非零仍需要现场在安全确认后重新 first-jog/manual 采集，并由上位机返回同帧非零 L/R。
