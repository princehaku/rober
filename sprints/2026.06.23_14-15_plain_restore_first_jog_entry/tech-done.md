# 2026-06-23 14:15 普通首屏恢复试动确认入口

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 当送达草稿覆盖 first-jog 基础安全确认且仍保留视觉材料时，`移动/导航` 普通按钮行直接显示 `恢复试动确认`。
  - `本轮进度 -> 去恢复确认` 优先聚焦顶部 `恢复试动确认`，减少现场从进度区跳到轮速面板后再找按钮的步骤。
  - 该按钮复用现有 `restorePlainFirstJogMaterial()`，只提交固定 operator report 代理；不调用 first-jog、manual、keyboard pulse、Nav2、delivery complete、stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 更新恢复确认聚焦测试，锁定新顶部按钮。
  - 更新恢复材料测试，直接点击普通首屏按钮并继续断言不会调用 first-jog/manual。
- `docs/product/pc_tools_workstation.md`
  - 同步记录普通首屏恢复入口和安全边界。

## 验证结果

- `npm test -- test/App.test.ts -t "restore-first-jog|restores first-jog material"`：
  - 首次失败：`去恢复确认` 文案已出现，但旧跳转优先级仍先聚焦 `plain-wheel-zero-check`。
  - 修复：`plainWheelGoalTarget()` 中 `firstJogMaterialRestoreBlocksMotion` 优先于轮速零值卡点。
  - 重跑通过，`2 passed | 49 skipped`。
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
  - `/api/operator/report`: latest 是 `delivery-draft-smoke-1782102952`，`operator_present=false`、`physical_clearance_confirmed=false`、`emergency_stop_ready=false`

## 剩余风险

- 本轮没有执行真实恢复、雷达启动、first-jog、Nav2 或 delivery complete。
- `wheel raw L/R 非零`、`完整 Nav2 路线执行`、`delivery success`、`PC 键盘连续手控` 仍需现场安全确认后继续拿真实证据。
