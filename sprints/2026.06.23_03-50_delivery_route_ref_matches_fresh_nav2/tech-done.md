# Tech Done

- sprint_type: micro
- 目标：修复 PC 端送达确认材料可能沿用旧草稿 route/map ref 的缺口，确保最终确认绑定当前未过期 Nav2 行程结果。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增当前新鲜 Nav2 `evidence_ref` 与送达 `route_map_ref` 一致性检查。
  - 普通首屏 `确认送达`、高级诊断最终提交和提交 handler 都增加一致性 gate。
  - 旧草稿 ref 与本轮行程不一致时，普通首屏提示 `下一步：更新行程材料。` 和 `确认送达（先更新行程材料）`。
  - `准备送达材料` 会在 ref 不一致时更新 route/map ref，但仍不提交 operator report、不调用 delivery complete、不发送运动命令。
- `pc-tools/workstation/test/App.test.ts`
  - 新增旧 delivery 草稿 ref 与新鲜 Nav2 ref 不一致的回归测试，覆盖禁用最终确认、禁止提交、更新材料后才放行。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 PC 端送达材料必须匹配当前新鲜行程 ref 的产品行为和安全边界。

## 验证结果

- `cd pc-tools/workstation && npm test`：通过，2 个 test files、131 个 tests passed。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，`tsc` + `vite build` + server `tsc` 完成。
- `git diff --check`：通过。

## 剩余风险

- 本轮为 PC 前端/fixture 回归验证；不包含真实小车送达 HIL、真实 Nav2 执行或真实 delivery complete 提交。
