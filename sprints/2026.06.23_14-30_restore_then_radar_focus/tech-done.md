# 2026-06-23 14:30 恢复确认后先补雷达

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `恢复试动确认` 成功后新增焦点分流：雷达未运行时先聚焦 `启动雷达` / `刷新雷达`，雷达已运行时才聚焦 `试动一下`。
  - 该分流只改变页面焦点，不自动启动雷达、不自动试动、不调用 first-jog/manual/keyboard pulse/stop、Nav2、delivery complete 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 更新恢复确认测试，显式构造雷达未运行状态，并断言恢复成功后焦点落到 `plain-radar-start`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录恢复确认后的雷达优先聚焦规则和安全边界。

## 验证结果

- `npm test -- test/App.test.ts -t "restores first-jog material"`：
  - 通过，`1 passed | 50 skipped`。
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
  - `/api/base/feedback-samples/latest`: 未读到非零 L/R
  - `/api/nav2/goal/execution/latest`: `status=not_proven`
  - `/api/delivery/latest`: `delivery_success=false`
  - `/api/operator/report`: latest 是 `delivery-draft-smoke-1782102952`，基础安全三项为 false

## 剩余风险

- 本轮没有执行真实恢复确认、雷达启动、first-jog、Nav2 或 delivery complete。
- `wheel raw L/R 非零`、`完整 Nav2 路线执行`、`delivery success`、`PC 键盘连续手控` 仍需现场安全确认后继续拿真实证据。
