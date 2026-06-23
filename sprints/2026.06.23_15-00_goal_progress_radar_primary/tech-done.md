# 2026-06-23 15:00 本轮进度主按钮指向雷达

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 当轮速卡点已检查且雷达未运行时，`本轮进度` 主按钮从 `去轮速记录卡点` 改为 `去启动雷达`。
  - 同状态下轮速行按钮改为 `去雷达`，总下一步改为 `先启动雷达，再重试读非零 L/R`。
  - 入口仍只聚焦 `启动雷达` / `刷新雷达`，不自动启动雷达、不自动刷新、不自动试动、不调用 first-jog/manual/keyboard pulse/stop、Nav2、delivery complete 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 L/R=0/0 和 first-jog 后 L/R=0/0 测试，锁定主按钮、轮速行按钮和总下一步文案。
- `docs/product/pc_tools_workstation.md`
  - 同步记录本轮进度主入口的雷达优先规则。

## 验证结果

- `npm test -- test/App.test.ts -t "current wheel L/R|wheel retry"`：
  - 首次失败：first-jog 零值测试使用已有历史材料 fixture，主进度已转到行程卡点；该场景只应要求轮速面板指向雷达。
  - 修正测试断言后通过，`2 passed | 49 skipped`。
- `npm test`：
  - 通过，`2 files / 138 tests`。
- `npm run lint`：
  - 通过。
- `npm run build`：
  - 通过，Vite 产物生成完成。
- `git diff --check`：
  - 通过。
- 真实上位机只读状态：
  - `/api/radar/status`: `lifecycle_running=false`, `lifecycle_status=lifecycle_not_running`
  - `/api/base/status`: `T=1001` 可读，最新 `L=0/R=0`，反馈电压约 `12.43V`
  - `/api/nav2/goal/execution/latest`: `status=not_proven`
  - `/api/delivery/latest`: `delivery_success=false`
  - `/api/operator/report`: latest 是 `delivery-draft-smoke-1782102952`，基础安全三项为 false

## 剩余风险

- 本轮没有执行真实雷达启动、first-jog、Nav2 或 delivery complete。
- `wheel raw L/R 非零`、`完整 Nav2 路线执行`、`delivery success`、`PC 键盘连续手控` 仍需现场安全确认后继续拿真实证据。
