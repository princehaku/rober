# Preserve Progress For Plain Reports

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- date: 2026-06-22

## 实际改动

- 新增/扩展 `inheritedProgressClaimsFromSummary()`，统一继承已有 `wheel_feedback_ref`、`scan_delta_ref` 和 `route_map_ref`。
- `移动前检查`、`记录画面`、`恢复试动确认`、`保存轮速记录` 写 operator report 时都会保留已有明确 `true; ref=...` 的进度材料。
- delivery 草稿和最终确认继续使用同一继承逻辑；delivery 自身仍以当前行程 ref 覆盖 route/map。
- 没有明确 ref 时仍保持 false，不伪造 wheel、LiDAR 或 route/map 证明。
- 更新 Vue/Vitest 回归，覆盖 `恢复试动确认` 不覆盖已有 wheel/LiDAR/route 材料。
- 更新 `docs/product/pc_tools_workstation.md`，记录 latest-only operator report slot 的保留策略。

## 验证结果

- `npm test`：通过，2 个测试文件、117 个用例。
- `npm run lint`：通过。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过。

## 剩余风险

- 本轮不新增真实 wheel、LiDAR 或 Nav2 采集能力，只避免普通 PC 动作擦除已有材料。
- 完整目标仍需要现场真实 wheel raw L/R 非零、delivery success 和键盘连续手控验证。
