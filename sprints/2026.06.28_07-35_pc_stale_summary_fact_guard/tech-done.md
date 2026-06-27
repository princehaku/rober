# Tech Done

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增普通首屏连接事实行：当本次刷新失败但仍有旧 summary 时，`当前事实` 首行提示“下面可能是上一次读数”。
  - 当 Node 返回 fail-closed timeout summary 且没有任何 loaded endpoint 时，`当前事实` 首行提示“当前事实不能当作实时读数”。
  - 该提示只改变 PC 展示，不清空旧诊断材料，不发送 manual/Nav2/free-roam/delivery 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖远端 timeout summary 的普通事实提示。
  - 覆盖已有上一拍 summary 后刷新失败时的 stale facts 提示，并断言不触发运动/送达/导航 endpoint。
- `docs/product/pc_free_roam_mapping_design.md`
  - 补充 2026-06-28 07:35 的 stale summary/current facts 所见即所得规则。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- --testNamePattern "plain timeout|stale facts|Robot Control V1" --maxWorkers=1 --no-fileParallelism`
  - 结果：1 个 test file 通过，3 passed，322 skipped。
- 已通过：`cd pc-tools/workstation && npm test -- --maxWorkers=1 --no-fileParallelism`
  - 结果：2 个 test files，325 passed。
- 已通过：`cd pc-tools/workstation && npm run lint`
- 已通过：`cd pc-tools/workstation && npm run build`
  - 备注：Vite 输出既有 `Some chunks are larger than 500 kB` 警告；构建命令退出码为 0。
- 已通过：`git diff --check`

## 剩余风险

- 本轮只修 PC 首屏事实可信度展示，不恢复现场 7001 无响应问题。
- 如果上位机服务持续卡住，真实相机/雷达/Nav2 状态仍需要重启或修复服务后才能重新验证。
- 旧 summary 会继续留作诊断背景；用户必须以首行 stale 提示为准，不把旧材料当作实时画面或实时地图。
