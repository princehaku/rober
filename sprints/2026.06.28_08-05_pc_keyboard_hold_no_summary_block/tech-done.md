# Tech Done

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 键盘连续手控按住同一方向且 manual pulse 成功时，不再在每个 pulse 后等待 `refreshConsole()`。
  - 按住期间继续用 manual 回包里的 `remote_motion_key_values` 更新 wheel raw L/R 和连续脉冲状态。
  - 失败、松开后 stop、停止失败等路径仍会刷新或进入 fail-closed，不改变安全确认、限速、限时、固定代理和 stop 兜底。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 summary 在按住期间卡住时，键盘仍能在 260ms 后发送第二次 manual pulse 的测试。
- `docs/product/pc_free_roam_mapping_design.md`
  - 补充 2026-06-28 08:05 的键盘连续手控节奏规则。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- --testNamePattern "keyboard|键盘|continuous|summary refresh stalls" --maxWorkers=1 --no-fileParallelism`
  - 结果：1 个 test file 通过，17 passed，310 skipped。
- 已通过：`cd pc-tools/workstation && npm test -- --maxWorkers=1 --no-fileParallelism`
  - 结果：2 个 test files，327 passed。
- 已通过：`cd pc-tools/workstation && npm run lint`
- 已通过：`cd pc-tools/workstation && npm run build`
  - 备注：Vite 输出既有 `Some chunks are larger than 500 kB` 警告；构建命令退出码为 0。
- 已通过：`git diff --check`

## 剩余风险

- 本轮只修 PC 键盘按住期间的前端调度，不做真实小车运动验证。
- 如果 manual proxy 本身慢或上位机拒绝 manual pulse，键盘仍会进入失败/未验证状态，不能宣称连续手控已完成。
- 真实 wheel raw L/R 非零和停止闭环仍需要操作员明确安全确认后的现场验证。
