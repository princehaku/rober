# PC 普通首屏底盘试动入口

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `移动/导航` 新增 `底盘试动` 按钮。
  - 该按钮复用现有 `sendManualMotion('forward')`，只在勾选同一个安全确认后可点。
  - 首屏新增 `plain-chassis-trial-summary`，直接展示本次底盘试动是否读到 wheel raw L/R 非零；若仍为 0/0，提示检查电机使能、供电、底盘模式和现场空间。
- `pc-tools/workstation/test/App.test.ts`
  - 回归测试改为从普通首屏点击 `底盘试动`，验证仍走固定 `/api/robot-control/base/manual` 代理、body 带 `confirm_hil_checklist=true`，且不触发 `/cmd_vel` 或 NavigateToPose。
  - 同步锁定键盘实时状态会显示最近 wheel raw L/R，避免连续手控时隐藏底盘反馈。
- `docs/product/pc_tools_workstation.md`
  - 记录 `底盘试动` 与 `试动一下` 的分工：前者验证底盘执行链，不依赖相机/雷达；后者仍服务 first-jog/现场材料闭环。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- --testNamePattern "enables non-stop motion only after complete operator material"`
- 已通过：`cd pc-tools/workstation && npm test`
- 已通过：`cd pc-tools/workstation && npm run lint`
- 已通过：`cd pc-tools/workstation && npm run build`
  - 保留既有 Vite chunk size warning。
- 已通过：`git diff --check`

## 剩余风险

- 本轮是 PC 普通入口修正，没有直接在真机上发新的运动命令。
- 真实上位机最新证据仍是 Nav2/bridge 已发非零底盘命令，但 WAVE ROVER `T=1001 L/R` 仍为 `0/0`；现场仍需用新入口复测电机使能、供电、底盘模式和控制链。
- 摄像头仍处于 DV20/UVC no-frame；这不再阻塞底盘低速试动，但会继续阻塞“可验收建图”的画面 ready 条件。
