# PC Nav2 ROS 重跑按钮

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏行程主按钮接入 Nav2 latest/summary 的 `next_execution_base_command_mode`。
  - 当上一轮控制模式不是下一轮控制模式，例如旧记录为 `pwm`、下一轮为 `ros`，安全确认后的按钮显示“用 ROS 重跑图上路线”。
  - 文案只改变现场下一手动作提示；真实执行仍由后端 `confirm_navigation_execution`、固定 Nav2 execute 代理和安全确认 gate 校验。
- `pc-tools/workstation/test/App.test.ts`
  - 增加旧 `pwm` 记录、下一轮 `ros` 复验场景的普通首屏按钮断言。
- `docs/product/pc_tools_workstation.md`
  - 记录普通首屏按钮文案与只读证据、安全边界。

## 验证结果

- `npm test -- --run App.test.ts -t "refreshes Robot Control summary after plain Nav2 execution latest is loaded"`
  - 结果：通过，`1 passed | 163 skipped`。
- `npm test`
  - 结果：通过，`2 passed`，`287 passed`。
- `npm run build`
  - 结果：通过，生成 `dist/`；Vite 仍提示单个 chunk 超过 500 kB，这是既有打包体积 warning，不影响本轮按钮文案功能。
- PC API 重启验证
  - `npm run api:public` 已重新启动，`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `*:7001`。
  - `GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 返回 `console_status=loaded_fail_closed_summary`。
- live 只读状态复核
  - camera：`status=source_first_frame_failed`，`source_diagnosis_not_exclusive=true`，`source_usage_owner_count=0`，说明当前不是页面独占，而是 UVC 设备没有输出首帧。
  - Nav2：`goal_execution_base_command_mode=pwm`、`next_execution_base_command_mode=ros`、`goal_execution_base_feedback_latest_left_speed=0`、`goal_execution_base_feedback_latest_right_speed=0`，正是本轮按钮文案覆盖的场景。
  - LiDAR：`lifecycle_running=true`，但 `latest_scan_proof_fresh=false`；free-roam：`start_ready=true`，当前 runtime 为 `artifact_only=true`、`cmd_vel_publish_enabled=false` 的停止记录。

## 剩余风险

- 本轮未触发真实 Nav2、manual、keyboard、delivery、stop 或 `/cmd_vel`；真实小车是否在下一次 ROS 模式复验中读到同窗口 wheel raw L/R 非零，仍需现场在安全确认后执行。
- 当前 live 相机仍是 `source_first_frame_failed` / `uvc_no_frame_not_exclusive`，雷达 scan proof freshness 仍需现场刷新；本改动不解决相机首帧或雷达 freshness。
