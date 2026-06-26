# PC Nav2 IMU 运动信号所见即所得

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - Nav2 latest proxy 不再把纯 action success 直接推导为完整行程证明。
  - 当 `nav2_goal_execution_proven` 没有显式为 true 时，必须同时看到 action 成功、result succeeded、`robot_control_executed=true`、底盘命令/UART 未被明确否定，以及轮速 L/R 非零或 IMU 姿态变化信号，才生成 `nav2_goal_execution_proven=true`。
  - 输出 `base_feedback_imu_attitude_delta_observed`、IMU roll/pitch delta、`sends_base_motion_commands` 和 `uses_base_uart`，供 PC 普通界面直接解释。
- `pc-tools/workstation/src/server/robotControlSummary.ts` 与 `pc-tools/workstation/src/shared/contracts.ts`
  - Robot Control summary/readback 契约补齐 Nav2 IMU 姿态变化和底盘命令/UART 字段。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通用户首屏把 `wheel_feedback_lr_nonzero_proven=true` 或 `base_feedback_imu_attitude_delta_observed=true` 都视为底盘运动信号。
  - 若 Nav2 已发非零底盘命令但轮速仍 0/0，且 IMU 已变化，UI 显示“底盘已响应（车身姿态有变化）”，进入“准备送达材料”；若 IMU 也未证明，继续提示排查电机使能、供电、底盘模式和控制模式，并明确不是雷达阻塞。
  - `delivery_success=false` 仍不会被运动信号提升为送达成功。
- `pc-tools/workstation/test/App.test.ts` 与 `pc-tools/workstation/test/catalog.test.ts`
  - 增加/修正 Nav2 PWM164 + IMU 姿态变化、轮速 L/R 非零、纯 action success 不充分等契约覆盖。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录 PC 普通首屏完整行程的证据口径，明确小车运动不依赖雷达，雷达/摄像头只影响建图或画面验收。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "Nav2 success"`
  - 通过：1 个测试文件，5 个 Nav2 成功路径用例通过。
- `cd pc-tools/workstation && npm test`
  - 通过：2 个测试文件，255 个用例通过。
- `cd pc-tools/workstation && npm run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 成功。
  - 仍有 Vite 既有 chunk 大小提示：`dist/assets/index-*.js` 超过 500 kB；不影响本轮功能。

## 剩余风险

- 本轮是 PC/Node 证据解释层修正，未重新上车跑真实 Nav2；真实硬件证据沿用上一轮 PWM164 复验结果。
- 摄像头 `/dev/video1` 仍是可 open 但无帧，当前判断不是简单浏览器独占；需要继续查 USB/供电/UVC/摄像头硬件链路。
- `wheel_feedback_lr_nonzero_proven=false` 但 IMU 变化只能证明底盘有运动响应，不能替代最终 `delivery_success=true` 或现场送达确认。
