# Preserve Route When Saving Wheel Evidence

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- date: 2026-06-22

## 实际改动

- 修正普通首屏 `保存轮速记录` 的 operator report request body。
- 当当前 summary 已有 `route_map=true; ref=...` 时，保存 wheel raw L/R 非零材料会保留 `real_route_map_proven=true` 和 `route_map_ref`。
- 没有明确 route ref 时仍保持 false，不凭 wheel 记录伪造完整路线材料。
- 更新 Vue/Vitest 回归，覆盖已有 `route_map_ref` 时保存 wheel 不覆盖该材料。
- 更新 `docs/product/pc_tools_workstation.md`，记录该行为对完整 Nav2 路线执行和 delivery success gate 的影响。

## 验证结果

- `npm test`：通过，2 个测试文件、117 个用例。
- `npm run lint`：通过。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过。

## 剩余风险

- 本轮不新增 Nav2 执行能力，只避免保存 wheel 时覆盖已有路线材料。
- delivery success 仍需要现场最终确认和上位机 delivery gate 通过。
