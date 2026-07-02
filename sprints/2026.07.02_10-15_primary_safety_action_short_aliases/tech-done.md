# Primary Safety Action Short Aliases

## sprint_type

micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增现场短 alias：
  - `field_acceptance_primary_safety_action_id`
  - `field_acceptance_primary_safety_action_label`
  - `field_acceptance_primary_safety_action_display_label`
  - `field_acceptance_primary_safety_action_start_endpoint`
  - `field_acceptance_primary_safety_action_stop_endpoint`
  - `field_acceptance_primary_safety_action_acceptance_endpoints`
  - `field_acceptance_primary_safety_action_ready_for_safety_confirm`
  - `field_acceptance_primary_safety_action_minimal_precheck_safety_only`
  - `field_acceptance_primary_safety_action_requires_safety_confirm`
  - `field_acceptance_primary_safety_action_sends_motion`
  - `current_motion_action_ready_for_safety_confirm`
- 这些字段与既有 `field_acceptance_primary_safety_confirm_ready_action_*` 和 `current_motion_action_*` 同源，只让现场脚本更容易读到“勾安全确认后当前能跑哪个动作”。
- 同步 TypeScript contract、`robotControlSummary.test.ts` 和 `docs/product/pc_tools_workstation.md`。
- 不改变按钮逻辑，不自动勾安全确认，不执行 Nav2/manual/keyboard/free-roam/建图/delivery/stop 或 `/cmd_vel`。

## 验证结果

- `npm test -- --run robotControlSummary.test.ts`：1 个测试文件、10 个用例通过。
- `npm test -- --run App.test.ts catalog.test.ts robotControlSummary.test.ts`：3 个测试文件、429 个用例通过。
- `npm run build`：通过，Vite 仅保留既有大 chunk warning。
- `npm run lint`：通过。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `83353`。
- live smoke `GET http://127.0.0.1:7001/api/robot-control/summary` 读回：
  - `field_acceptance_primary_safety_action_id=run_nav2_route`
  - `field_acceptance_primary_safety_action_display_label=重跑图上行程并复验轮速`
  - `field_acceptance_primary_safety_action_start_endpoint=/api/robot-control/nav2/goal/execute`
  - `field_acceptance_primary_safety_action_stop_endpoint=/api/robot-control/base/stop`
  - `field_acceptance_primary_safety_action_ready_for_safety_confirm=true`
  - `field_acceptance_primary_safety_action_minimal_precheck_safety_only=true`
  - `field_acceptance_primary_safety_action_requires_safety_confirm=true`
  - `field_acceptance_primary_safety_action_sends_motion=true`
  - `current_motion_action_ready_for_safety_confirm=true`
  - `current_motion_action_missing_evidence=["same_window_wheel_lr_nonzero","delivery_success"]`
  - `minimal_precheck_safety_only=true`
  - `safety_confirm_required_for_motion=true`

## 剩余风险

- 本轮没有执行任何 motion/control POST；完整 Nav2 行程同窗口 wheel L/R 非零、delivery success、PC 键盘连续手控和自由移动真实运动仍需现场安全确认后验收。
- 当前相机首帧仍未恢复，建图启动仍缺 `camera_first_frame`；低速自由移动不被该缺口阻塞。
