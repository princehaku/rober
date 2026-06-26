# 2026-06-27 06:06 Nav2 wheel L/R strict gate

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`：Nav2 latest/execute 代理的 `nav2_goal_execution_proven` 推导收紧为必须有同窗口 `base_feedback_summary.wheel_feedback_lr_nonzero_proven=true`；IMU 姿态变化、非零 PWM 命令和 `uses_base_uart` 只作为诊断材料。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：Robot Control summary 使用同一 wheel L/R 门禁，避免普通首屏或高级诊断把 `goal_succeeded + IMU delta` 说成完整路线执行。
- `onboard/scripts/o11_nav2_goal_execution_proof.py`：当 Nav2 goal 成功且 bridge 已记录非零 PWM 命令，但 WAVE ROVER T=1001 wheel L/R 仍未非零时，写出 `proof_status=nav2_goal_succeeded_with_pwm_commands_but_wheel_lr_zero` 和 `not_proven=["wheel_feedback_lr_nonzero", ...]`。
- `pc-tools/workstation/test/catalog.test.ts`：更新 Nav2 证明夹具，锁定“完整路线必须 wheel L/R 非零；IMU-only 只可见不可 proven”。
- `docs/product/pc_tools_workstation.md`、`docs/vision/board_camera_publisher.md`：同步记录当前摄像头共享预览不是独占问题、DV20 首帧仍失败，以及 Nav2 不依赖雷达发底盘命令但完整路线必须 wheel L/R 非零。

## 验证结果

- `python3 -m unittest onboard.tests.test_o11_nav2_goal_execution_proof`：通过，5 tests。
- `npm test -- --run test/catalog.test.ts`：通过，113 tests。
- `npm test -- --run test/App.test.ts`：通过，150 tests。
- `npm run lint`：通过。
- `npm run build`：通过；保留既有 Vite chunk size warning。
- `git diff --check`：通过。

## 真实上车读回

- 真实上位机最近 Nav2 artifact 已显示 `status=goal_succeeded`，命令日志包含 50 条非零 `T=11 L/R=164` PWM 命令。
- 同一窗口 WAVE ROVER `T=1001` feedback 可读，但 `left_speed/right_speed` 仍为 `0/0`；roll/pitch 有变化，只能作为运动迹象，不能替代 wheel L/R 非零闭环。
- 摄像头 summary 当前为 `source_first_frame_failed`、`source_usage_status=not_in_use`、`shared_preview_exclusive_camera_claim=false`；当前看不到画面不是多浏览器独占抢占，仍需硬件/驱动层恢复 DV20 首帧。

## 剩余风险

- 本轮修复的是证明口径和可诊断性，不等于已经让底盘 wheel L/R 非零。下一步仍要现场检查电机使能、供电、WAVE ROVER 模式、轮子离地/地面阻力或 firmware 反馈字段。
- 雷达不再被当作底盘能否发命令的前置；但建图、避障和可视化路线仍需要继续恢复雷达点云。
