# 2026-06-23 16:25 轮速 0/0 直达雷达前置

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 当普通首屏已读到轮速卡点且雷达 lifecycle 未运行时，`本轮进度` 的主按钮与轮速行按钮直接指向 `启动雷达`。
  - `已检查轮速卡点` 仍保留在轮速模块内，但不再挡在启动雷达前面；现场可以先启动传感器，再回到低速试动读非零 L/R。
  - 轮速记录里的试动按钮在该状态下显示 `先启动雷达再试动` 且禁用，避免文案要求先启动雷达时仍误发 first-jog。
  - 该改动只改变页面焦点和下一步文案，不自动启动雷达、不自动试动、不调用 first-jog/manual/keyboard pulse/stop、Nav2 execute、delivery complete 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 更新轮速 `L/R=0/0` 且雷达未运行场景的首屏断言：主按钮应显示 `去启动雷达`，点击后聚焦 `plain-radar-start`，轮速试动按钮禁用，且不调用任何运动或 Nav2/delivery 接口。
- `docs/product/pc_tools_workstation.md`
  - 同步记录该普通首屏易用性调整。

## 验证结果

- 通过：`npm test -- test/App.test.ts -t "current wheel L/R|first-jog wheel retry"`，结果 `1 passed`，`2 passed | 50 skipped`。
- 通过：`npm test`，结果 `2 passed`，`141 passed`。
- 通过：`npm run lint`。
- 通过：`npm run build`，完成 app/server TypeScript 与 Vite production build。
- 通过：`git diff --check`。

## 剩余风险

- 本轮未执行真实雷达启动、first-jog、Nav2、delivery complete 或键盘手控。
- 真实状态仍需现场安全确认后继续拿 `wheel raw L/R 非零`、完整 Nav2 路线执行、`delivery_success=true` 和 PC 键盘连续手控证据。
