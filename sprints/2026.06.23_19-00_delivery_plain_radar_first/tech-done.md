# 2026-06-23 19:00 Micro Sprint: 送达普通入口先指向雷达

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `送达确认` 在本轮行程未完成且雷达未运行时，下一步改为 `先启动雷达，再完成本轮行程`。
  - 红色 `确认送达（不发车）` 的禁用文案在同一状态下改为 `确认送达（先启动雷达）`。
  - `本轮进度 -> 去送达` 在该状态下只聚焦雷达启动入口，不自动启动雷达、不执行 Nav2、不提交 delivery complete、不发送 manual 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展雷达未运行时的普通首屏回归测试，覆盖送达下一步、确认按钮禁用文案和 `去送达` 聚焦行为。
- `docs/product/pc_tools_workstation.md`
  - 同步记录送达普通入口的雷达前置提示。

## 验证结果

- `cd pc-tools/workstation && npm test -- -t "blocks plain trip actions on the first screen until radar is running"`：通过，`1 passed | 141 skipped`。
- `cd pc-tools/workstation && npm test`：通过，`2 passed`、`142 passed`。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，Vite 产物生成成功。
- `git diff --check`：通过。

## 剩余风险

- 当前改动只提升 PC 普通首屏引导，不证明真实 `wheel raw L/R 非零`、完整 Nav2 路线执行、`delivery success` 或 PC 键盘连续手控。
- 真实上位机动作仍需要现场 operator 明确确认；本轮没有自动启动雷达、没有执行行程、没有提交送达、没有发送底盘手控。
