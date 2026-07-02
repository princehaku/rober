# Current Motion Action Readback Facts

## sprint_type

micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增 `current_motion_action_*` 当前读回细项：
  - 图上行程是否已显示、Nav2 是否到点、同窗口 wheel L/R 是否非零、送达确认是否完成。
  - 当前 wheel L/R、样本数、非零样本数、当前缺口、最小预检说明和送达下一步。
- PC 普通首屏 `plain-trip-current-motion-action` 和行程执行按钮 DOM 同步暴露这些字段。
- 可见文案新增“当前读回：图上行程 / 到点 / 同窗口轮速 / 送达确认”四段，让现场重跑完整路线后能直接看 motion 目标还缺哪一段。
- 该变化只抬升只读验收事实，不新增自动发车、不自动提交送达、不发送 stop 或 `/cmd_vel`。

## 验证结果

- `npm test -- --run App.test.ts catalog.test.ts robotControlSummary.test.ts`：3 个测试文件、428 个用例通过。
- `npm run build`：通过；Vite 仍保留既有大 chunk warning。
- `npm run lint`：通过。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `85135`。
- live summary smoke：
  - `current_motion_action_id=run_nav2_route`
  - `current_motion_action_route_ready_on_map=true`
  - `current_motion_action_nav2_goal_succeeded=true`
  - `current_motion_action_same_window_wheel_lr_nonzero=false`
  - `current_motion_action_delivery_success=false`
  - `current_motion_action_latest_raw_left/right=0/0`
  - `current_motion_action_feedback_nonzero_sample_count=0`
- Chrome DOM smoke：`plain-trip-current-motion-action` 与 `plain-trip-execute` 均暴露 route/Nav2/wheel/delivery 当前读回字段；执行按钮在未勾安全确认时保持 disabled。

## 剩余风险

- 本轮没有现场安全确认，未执行 Nav2 路线、键盘连续手控或自由移动 motion POST；真实 wheel L/R 非零和 delivery success 仍需现场安全确认后验收。
- 当前 live summary 仍显示 motion 未完成，缺 `same_window_wheel_lr_nonzero` 和 `delivery_success`。
