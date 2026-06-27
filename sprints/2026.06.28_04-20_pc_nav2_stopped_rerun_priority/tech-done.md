# 2026.06.28 04:20 PC Nav2 Stopped Rerun Priority

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：当 live 同时读到旧 PWM 路线成功记录、执行窗口轮速 L/R=0/0、以及当前 `nav2_stack_not_running` 时，普通首屏行程卡优先进入“需恢复”，提示先启动自动驾驶服务（不发车）。
- 同一 live 形状下，“自动驾驶为什么不动”的诊断把 `Nav2 stack stopped` 翻译为“自动驾驶服务未运行，重跑前先启动”，不再只提示规划/控制服务恢复或直接 ROS 重跑。
- `pc-tools/workstation/test/App.test.ts`：新增 stopped stack + old PWM zero-wheel 场景，验证按钮禁用、状态优先级、当前事实文案，以及不调用 goal execute、base manual 或 `/cmd_vel`。
- `docs/product/pc_free_roam_mapping_design.md`：同步记录该 live 形状的普通首屏口径和 no-motion 边界。

## 验证结果

- `npm test -- --run test/App.test.ts -t "stopped Nav2 stack ahead of ROS rerun|Nav2 start action when the stack is stopped"` 通过，2 passed / 188 skipped。
- `npm test` 通过，2 个 test file / 337 个测试通过。
- `npm run lint` 通过。
- `npm run build` 通过；Vite 仍有既有 chunk size warning，未影响构建产物。
- `git diff --check` 通过。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `24966`。
- live 只读 summary（未发运动/未启动服务）确认：
  - `nav2_stack_running=false`、`nav2_stack_lifecycle_state=stopped`、planner/controller 均为 `false`、`path_point_count=0`。
  - 最近旧路线为 `goal_succeeded`，上次 `base_command_mode=pwm`、下次 `next_execution_base_command_mode=ros`，执行窗口 wheel raw L/R=`0/0`，`goal_execution_base_feedback_lr_nonzero_proven=false`。
  - `safe_command_boundary.nav2_goal_label=自动驾驶服务未启动`，blockers 以 `nav2_stack_not_running` 开头，next action 为“先启动自动驾驶服务（不发车）→ 生成图上路线并读到小车地图位置 → 勾确认后用 ROS 重跑并复验 wheel raw L/R”。
  - 相机仍为 `source_first_frame_failed/uvc_no_frame_not_exclusive`，不是页面独占；雷达 lifecycle stopped，地图雷达 overlay `not_current`；`free_roam_motion_start_ready=true` 但 `free_roam_mapping_ready=false`。

## 剩余风险

- 本轮不点击 live “启动自动驾驶服务（不发车）”，因为没有新的现场安全确认；真实 Nav2 stack 启动、路线重新生成、ROS 模式重跑和 wheel raw L/R 非零仍待现场确认后验证。
