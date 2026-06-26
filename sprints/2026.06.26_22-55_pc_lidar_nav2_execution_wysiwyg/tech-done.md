# PC 雷达与 Nav2 执行状态所见即所得

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 在 `readback_summary.lidar` 合同中新增 `scan_preview_point_count`、`scan_preview_source_point_count`、`scan_preview_frame_id`，让普通 summary 不再只能从高级 proof 里找雷达点数。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `lidarSummaryFromReadbacks` 接入 `RobotApiProofSummary`，把雷达预览点数和 frame id 下沉到普通 lidar 摘要。
  - `nav2SummaryFromReadbacks` 新增 Nav2 执行证明兼容逻辑：旧字段 `nav2_goal_execution_proven` 优先；缺旧字段时，用 `robot_control_executed=true`、`sends_motion_commands=true`、`goal_succeeded/succeeded` 和正数反馈样本推导为已执行。
- `pc-tools/workstation/test/App.test.ts`
  - 补齐默认 fixture 的 lidar 新字段。
- `pc-tools/workstation/test/catalog.test.ts`
  - 增加雷达普通 summary 字段断言。
  - 增加 live-shape Nav2 latest 测试，覆盖没有旧 `nav2_goal_execution_proven` key 的执行证明推导。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 PC 7001 live 读回、Nav2 执行证明解释边界和底盘非零轮速剩余风险。

## 验证结果

- `cd pc-tools/workstation && npm test -- catalog.test.ts`
  - 通过：`Test Files 1 passed`，`Tests 107 passed`。
- `cd pc-tools/workstation && npm run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 成功；Vite 仅保留既有 chunk size warning。
- `git diff --check`
  - 通过，无空白错误。
- 现场 PC Node
  - 已重启为 `HOST=0.0.0.0 PORT=7001 ./node_modules/.bin/tsx src/server/index.ts`，监听 `TCP *:7001`，PID `23903`。
- live 7001 summary 读回
  - `readback_summary.lidar.scan_preview_point_count="72"`。
  - `readback_summary.lidar.scan_preview_source_point_count="72"`。
  - `readback_summary.lidar.scan_preview_frame_id="laser_frame"`。
  - `readback_summary.nav2.goal_execution_status="goal_succeeded"`。
  - `readback_summary.nav2.goal_execution_proven="true"`。
  - `readback_summary.nav2.goal_execution_robot_control_executed="true"`。
  - `readback_summary.nav2.goal_execution_feedback_sample_count="8"`。
  - `safe_command_boundary.nav2_goal_ready=true`，`keyboard_control_start_ready=true`。

## 剩余风险

- 这轮没有发送任何真实运动命令，也没有点击 free-roam start、manual、keyboard、Nav2 execute 或 `/cmd_vel`；因此没有新增物理轮速 `T=1001 L/R` 非零证据。
- live free-roam 仍为 `decision_state=stopping`、`artifact_only=true`、`cmd_vel_publish_enabled=false`，说明当前自动扫图没有处在运动发布状态；这不是雷达硬阻塞，而是尚未通过 start 进入运动发布。
- 现场摄像头仍是 `/dev/video1` 可打开但无首帧输出，当前 PC 共享预览不是独占根因；仍需检查摄像头输入、USB/供电或更换 known-good UVC。
- 硬件协议判断继续引用 `docs/vendor/VENDOR_INDEX.md` 中的 WAVE ROVER UART JSON 事实：底盘反馈以 vendor `T=1001 L/R` 为准，后续真车运动验收必须观察非零 L/R。
