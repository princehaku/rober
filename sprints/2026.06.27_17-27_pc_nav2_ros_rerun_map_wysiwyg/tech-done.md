# 2026.06.27 17:27 PC Nav2 ROS 复验地图 WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 在 Nav2 最近结果为 `goal_succeeded` 但同窗口 `wheel raw L/R=0/0`，且 `mode_rerun_status=pending_ros_rerun_after_pwm` 时，地图终点 marker 文案从泛化“到达未证明”升级为“到达未证明：旧 PWM 结果，等待 ROS 复验”。
  - 同步把地图 `行程执行` caption 从“路线返回成功，底盘反馈 0/0”升级为“路线返回成功，底盘反馈 0/0，旧 PWM 结果，等待 ROS 复验”。
  - 普通未证明场景仍保留原短文案，避免所有未完成 Nav2 结果都被误说成 ROS 复验。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 Nav2 wheel 0/0 用例，覆盖地图 caption、终点 marker、aria 都显示 ROS 复验原因。
- `docs/product/pc_tools_workstation.md`
  - 记录地图 WYSIWYG 同步显示 Nav2 模式复验原因的边界。

## 验证结果

- 已通过：`npm test -- --run test/App.test.ts -t "explains Nav2 success with nonzero base commands but zero wheel feedback|keeps Nav2 success with IMU motion signal out of complete route evidence"`
  - 结果：目标 2 个用例 passed，其他 App 用例 skipped。
- 第一次全量 `npm test -- --run` 发现 1 个旧断言仍要求地图 caption 只显示“底盘反馈 0/0”；已同步更新为“旧 PWM 结果，等待 ROS 复验”。
- 已通过：`npm test -- --run`
  - 结果：2 test files passed，300 tests passed。
- 已通过：`npm run build`
  - 结果：Vite 构建成功，当前产物为 `assets/index-Crvl_wdZ.js` 和 `assets/index-DkzBjvNI.css`。
- 已通过：`npm run lint`
  - 结果：ESLint 无报错。
- 已通过：`git diff --check`
  - 结果：无空白或 patch 格式问题。
- 已确认：`http://127.0.0.1:7001/`
  - 结果：当前页面引用 `assets/index-Crvl_wdZ.js`；Node 仍监听 `*:7001`，未改 Clash 或系统代理。

## 剩余风险

- 该轮只改 PC 地图展示和 mock 验证，不触发真实 Nav2 execute；真实 ROS 模式重跑、执行窗口 wheel raw L/R 非零和 delivery success 仍需现场安全确认后单独验证。
- 摄像头 UVC 无帧仍未解决，本轮不宣称画面 ready。
