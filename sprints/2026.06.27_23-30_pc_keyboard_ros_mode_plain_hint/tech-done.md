# PC Keyboard ROS Mode Plain Hint

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏当前事实里的键盘行新增 `走 ROS/T=13 低速入口`。
  - 键盘手控说明新增 `通过 ROS/T=13 低速入口持续移动`，仍保留按住才动、低速脉冲、速度/时长上限和松开/失焦/切页即停。
- `pc-tools/workstation/test/App.test.ts`
  - 更新普通首屏当前事实和键盘说明断言，锁住 ROS/T=13 可见口径。
- `docs/product/pc_tools_workstation.md`
  - 记录本轮只把已有 PC proxy `command_mode=ros` 口径显示给普通用户，不改变控制路径。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "continuous keyboard control"`，`Tests 1 passed | 164 skipped (165)`。
- 已通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "renders Robot Control V1"`，`Tests 1 passed | 164 skipped (165)`。
- 已通过：`cd pc-tools/workstation && npm test`，`Tests 291 passed (291)`。
- 已通过：`cd pc-tools/workstation && npm run build`。
  - 保留既有 Vite chunk size warning：`Some chunks are larger than 500 kB after minification`。
- 已通过：`git diff --check`。
- 已完成只读 live 验证：
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `*:7001`。
  - `GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 只读返回：相机 `source_first_frame_failed` 且 `uvc_no_frame_not_exclusive`，Nav2 为 `goal_succeeded_wheel_feedback_not_proven`，上次模式 `pwm`、下次模式 `ros`，底盘当前 L/R=`0/0` 且 `wheel_feedback_lr_nonzero_proven=false`，键盘合同 `bounded_repeating_manual_pulse` 且 `keyboard_control_start_ready=true`。

## 剩余风险

- 本轮只改 PC 普通首屏 WYSIWYG 文案，不执行真实 keyboard/manual/Nav2/free-roam 运动。
- 是否真正读到 wheel raw L/R 非零，仍需要现场勾选安全确认后按住方向键做低速复验。
