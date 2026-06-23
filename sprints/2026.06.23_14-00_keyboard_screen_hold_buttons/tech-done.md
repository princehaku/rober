# 2026-06-23 14:00 键盘面板屏幕方向键

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏键盘面板新增四个屏幕方向键：前进、左转、右转、后退。
  - 屏幕方向键只在 `启用键盘` 后可按，复用现有 `startKeyboardControl()`、bounded repeating manual pulse、manual gate 和 stop 收口逻辑。
  - `pointerup`、`pointerleave`、`pointercancel` 都会走 `stopKeyboardControl()`，避免屏幕按钮残留连续点动。
  - 没有新增后端 endpoint，没有直连 `/cmd_vel`，没有绕过 operator report preflight。
- `pc-tools/workstation/src/styles.css`
  - 给键盘面板方向键增加紧凑尺寸约束，保持普通用户简易风格。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 PC 键盘连续手控测试，覆盖未启用时屏幕方向键 disabled、启用后按住屏幕方向键走固定 manual proxy、松开后走 stop。
- `docs/product/pc_tools_workstation.md`
  - 同步记录屏幕方向键的门禁和安全边界。

## 验证结果

- `npm test -- test/App.test.ts -t "enables non-stop motion only after complete operator material"`：
  - 首次失败：新增普通键盘方向键复用了 `.motion-pad`，旧测试误选中 disabled 的普通方向键。
  - 修复：普通键盘方向键改用专用 `.keyboard-direction-pad`，并把相关测试选择器收紧到高级诊断点动 pad。
  - 重跑通过，`1 passed | 50 skipped`。
- `npm test -- test/App.test.ts -t "renders Robot Control V1|keeps non-stop motion disabled"`：
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
  - `/api/base/feedback-samples/latest`: 未读到 `lr_nonzero_observed/left_speed/right_speed`
  - `/api/nav2/goal/execution/latest`: `status=not_proven`
  - `/api/delivery/latest`: `delivery_success=false`

## 剩余风险

- 本轮只是提升 PC 连续手控入口可用性，没有在真实小车上执行手控。
- `wheel raw L/R 非零`、`完整 Nav2 路线执行`、`delivery success`、`PC 键盘连续手控` 仍需现场安全确认和真实运行证据。
