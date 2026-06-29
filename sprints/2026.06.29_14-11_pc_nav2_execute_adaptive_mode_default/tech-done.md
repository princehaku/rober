# PC Nav2 执行默认模式跟随 latest 策略

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation/src/server/index.ts` 中补齐 Nav2 execute 代理的默认模式策略：请求体没有显式 `base_command_mode` / `nav2_base_command_mode` 时，只有在 `confirm_navigation_execution=true` 且本机最小 preflight 通过后，才只读 `/api/nav2/goal/execution/latest` 并按 `next_execution_base_command_mode` 选择本次转发模式。
- 同步补齐 server 侧 `navGoalLatestNextMode()`：上次 `pwm` 成功但轮速 L/R 未证明时切 `ros`，上次 `ros` 成功但轮速 L/R 未证明时切 `speed`；latest 不可读或无有效建议时仍回落 `ros`。
- 在 `pc-tools/workstation/test/catalog.test.ts` 中新增回归用例，锁定“省略模式 + 最近 ROS action 成功但 L/R=0/0”时转发 `base_command_mode: speed`。
- 更新 `pc-tools/README.md` 与 `docs/product/pc_tools_workstation.md`，记录该执行代理合同。

## 验证结果

- 已按硬件纪律阅读 `docs/vendor/VENDOR_INDEX.md`。本轮只使用其记录的 WAVE ROVER 既有控制面事实：`ros` 对应 vendor `T=13`，`speed` 对应 `T=1`，`pwm` 对应 `T=11`；未修改 UART、波特率、引脚、电压或底盘协议。
- 已通过定向 PC 测试：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Nav2 goal execution|omitted Nav2 goal execution mode|default"`，结果 `9 passed | 156 skipped`。
- 已通过全量 PC 测试：`npm --prefix pc-tools/workstation test`，结果 `380 passed`。
- 已通过 PC build：`npm --prefix pc-tools/workstation run build`，`tsc` 与 `vite build` 通过；仅保留既有 Vite chunk size 提示。
- 已重启本地 PC API 到 `0.0.0.0:7001`，新 PID 为 `45329`。
- 已通过 7001 只读 latest 验证：`GET /api/robot-control/nav2/goal/execution/latest` 返回 `base_command_mode=pwm`、`next_execution_base_command_mode=ros`、`goal_execution_base_feedback_lr_nonzero_proven=false`，当前现场仍指向“勾选行程前安全确认后用 ROS 模式重跑图上路线，并在同窗口确认轮速 L/R 非零”。

## 剩余风险

- 本轮不调用 `/api/robot-control/nav2/goal/execute`、不执行 Nav2、不启用键盘、不启动自由移动、不发送 manual、delivery、stop 或额外 `/cmd_vel`。
- 当前 live 仍显示相机首帧未出、雷达新鲜点未就绪、上次完整路线执行窗口轮速 L/R=0/0；真实自动驾驶闭环仍需要现场安全确认后重跑，并读取同窗口非零 L/R 证据。
