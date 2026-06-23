# 2026-06-23 14:45 轮速零值卡点后先补雷达

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 当轮速卡点已检查且雷达未运行时，轮速目标下一步改为先启动雷达，再重试读非零 L/R。
  - `已检查轮速卡点` 点击后优先聚焦 `启动雷达` / `刷新雷达`；雷达已运行时才聚焦试动按钮。
  - 试动按钮文案在该状态下显示 `先启动雷达再试动`，轮速面板 hint 同步提示先启动雷达。
  - 该改动只影响文案和焦点，不自动启动雷达、不自动试动、不调用 first-jog/manual/keyboard pulse/stop、Nav2、delivery complete 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 更新当前 L/R=0/0 与 first-jog 后 L/R=0/0 两条测试，显式覆盖雷达未运行时的焦点和文案。
- `docs/product/pc_tools_workstation.md`
  - 同步记录轮速零值卡点后的雷达优先顺序。

## 验证结果

- `npm test -- test/App.test.ts -t "current wheel L/R|wheel retry"`：
  - 通过，`2 passed | 49 skipped`。
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
  - `/api/base/status`: `T=1001` 可读，最新 `L=0/R=0`，反馈电压约 `12.42V`
  - `/api/base/feedback-samples/latest`: 未读到非零 L/R
  - `/api/nav2/goal/execution/latest`: `status=not_proven`
  - `/api/delivery/latest`: `delivery_success=false`
  - `/api/operator/report`: latest 是 `delivery-draft-smoke-1782102952`，基础安全三项为 false

## 剩余风险

- 本轮没有执行真实雷达启动、first-jog、Nav2 或 delivery complete。
- `wheel raw L/R 非零`、`完整 Nav2 路线执行`、`delivery success`、`PC 键盘连续手控` 仍需现场安全确认后继续拿真实证据。
