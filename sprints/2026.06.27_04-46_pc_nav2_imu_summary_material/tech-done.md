# PC Nav2 IMU summary material

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 修正 `nav2GoalExecutionProvenText()`：`hil_pass=false` 不再一刀切压掉同一 artifact 内的真实运动材料。
  - 当最近 Nav2 artifact 同时满足 `goal_succeeded/result_status=succeeded`、`robot_control_executed=true`、`sends_base_motion_commands=true`、`uses_base_uart` 未否定、反馈样本存在，并且 `base_feedback_summary.imu_attitude_delta_observed=true` 或轮速 L/R 非零时，PC summary 会把 `goal_execution_proven` 推导为 `true`。
  - 保留 `goal_execution_hil_pass=false`、`goal_execution_base_feedback_lr_nonzero_proven=false` 和 latest L/R=`0/0`，避免把 IMU 姿态变化误写成 wheel raw L/R HIL。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增 summary 层回归测试：Nav2 action 成功 + 已发底盘运动命令 + UART 链路 + IMU 姿态变化时，首屏 summary 应显示路线执行材料成立，同时继续显示 wheel HIL false 和 L/R=`0/0`。
- `docs/product/pc_tools_workstation.md`
  - 同步 PC 产品边界：IMU-only 可作为“路线已执行并有车身响应”的现场材料，但不能替代 wheel raw L/R 非零、delivery success 或控制权限。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --maxWorkers=1 --no-fileParallelism --testNamePattern "Robot Control summary (does not treat Nav2 action success|keeps Nav2 IMU motion material)|Nav2 latest execution proxy derives proven execution|treats Nav2 success with base command and IMU motion signal"`。
  - 结果：2 个测试文件通过，4 个目标用例通过。
- 通过：`cd pc-tools/workstation && npm test`。
  - 结果：2 个测试文件通过，261 个用例通过。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。
  - Vite 仍提示单个 chunk 大于 500 kB，这是既有前端体积提示，不影响本轮功能。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `0.0.0.0:7001` 后，`GET /api/health` 返回
  `mode=pc_only_readonly_workstation`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- 通过：live 只读 summary `GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：
  - Nav2：`status=goal_succeeded`、`goal_execution_proven=true`、`goal_execution_hil_pass=false`、`result_status=succeeded`、`robot_control_executed=true`、`base_command_nonzero_observed=true`、`base_command_nonzero_count=49`、`base_feedback_lr_nonzero_proven=false`、`base_feedback_imu_attitude_delta_observed=true`、`base_feedback_imu_pitch_delta=24.210531`、latest L/R=`0/0`。
  - 摄像头：`status=source_first_frame_failed`、`source_readiness=first_frame_failed`、`source_failure_reason=capture_read_returned_false`、`source_usage_status=not_in_use`、`shared_preview_exclusive_camera_claim=false`、`shared_preview_client_count=0`。
  - 自由移动 gate：`free_roam_autonomy_start_ready=true`、`free_roam_autonomy_label=自由移动（勾确认后可启动）`。

## 剩余风险

- 摄像头仍未证明首帧可见；上一轮 live evidence 是 `/dev/video1` 没有进程独占但 `capture_read_returned_false` / backend no frame，需要继续查 USB、摄像头输入、格式或供电。
- Nav2 本轮只修 PC summary 的现场材料解释，没有新增真实发车；wheel raw L/R 同窗口非零仍未证明，`hil_pass=false` 仍保留给复验。
- 自由移动不依赖雷达 freshness 的 start-ready 口径已存在，本轮没有重新触发真实自由移动或自动扫图。

## OKR 最低优先级核对

- 本轮是 micro sprint，不强制完整 OKR 最低优先级章节；实际推进的是 O3 可验证导航与固定路线的 WYSIWYG 解释，避免把已发生的 Nav2 车身响应继续误报为完全未执行。
