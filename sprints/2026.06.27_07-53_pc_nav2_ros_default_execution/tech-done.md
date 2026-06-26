# PC Nav2 ROS 默认执行模式

sprint_type: micro

## 设计结论

- “自动驾驶没法动”的下一轮复验不能继续靠旧 PWM 诊断路径碰运气；普通 PC 路线执行应默认走 ROS 控制入口。
- 雷达 freshness 不作为底盘能否发命令的前置；雷达只影响避障、建图和验收材料。
- 本轮只改请求合同和所见即所得记录，不执行真实路线，不声明 wheel raw L/R 已非零。

采用的本地资料来源：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - `POST /api/robot-control/nav2/goal/execute` 在浏览器未传 `base_command_mode` 时默认使用 `ros`。
  - fallback `goal_request` 和转发到上车 `/api/nav2/goal/execute` 的 body 都固定带 `base_command_mode=ros`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏“执行图上路线”调用 `runNavGoalExecution` 时显式携带 `base_command_mode: "ros"`。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增后端合同测试：浏览器省略模式时，PC Node 仍转发 `base_command_mode=ros`。
- `pc-tools/workstation/test/App.test.ts`
  - 收紧普通首屏路线执行请求体断言，确认按钮请求携带 `base_command_mode=ros`。
- `docs/product/pc_tools_workstation.md`
  - 记录“下次将用 ros 复验”已经进入真实请求合同，不只是 summary 文案。
- `docs/interfaces/ros_runtime_contracts.md`
  - 更新 Nav2 执行模式合同：普通路线执行默认 ROS，`speed`/`pwm` 仅保留为白名单诊断 override。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "Nav2 goal execution"`
  - `Test Files 1 passed (1)`
  - `Tests 2 passed | 115 skipped (117)`
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "visible-route trip execution|plain trip|route execution"`
  - `Test Files 1 passed (1)`
  - `Tests 9 passed | 144 skipped (153)`
- 通过：`cd pc-tools/workstation && npm run lint`
  - `eslint .`
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - Vite 保留既有 chunk size warning，本轮无新增构建失败。
- 通过：`cd pc-tools/workstation && npm test`
  - `Test Files 2 passed (2)`
  - `Tests 270 passed (270)`
- 通过：重启 PC Node 到 `0.0.0.0:7001`
  - `lsof` 显示 `node` PID `22474` 监听 `TCP *:7001`。
  - `curl http://127.0.0.1:7001/api/health` 返回 `mode=pc_only_readonly_workstation`、`pc_only=true`、`safe_to_control=false`。
  - 安全拒绝态 POST `/api/robot-control/nav2/goal/execute` 未带 `confirm_navigation_execution`，返回 `execution_rejected`、`robot_control_executed=false`、`blocked_reasons=[confirm_navigation_execution_required]`，且 `goal_request.base_command_mode=ros`。

## 剩余风险

- 本轮不执行真实 Nav2 发车，不证明底盘 wheel raw L/R 非零。
- 真实小车若下一轮 ROS 模式仍不动，仍需现场继续查电机使能、供电、底盘模式、控制模式、WAVE ROVER `T=13` 固件支持和 `T=1001` 反馈链路。
