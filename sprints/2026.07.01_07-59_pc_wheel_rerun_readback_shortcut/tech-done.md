# 轮速复验读回按钮

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 在 `plain-wheel-rerun-closure-plan` 轮速复验提示内新增 `plain-wheel-rerun-readback-refresh` “读回复验”按钮。
  - 按钮复用完整行程读回链路，只刷新 `nav2/goal/execution/latest`、`base/feedback-samples`、`summary` 和 `delivery/latest`。
  - DOM 显式声明只读边界：不执行 Nav2、不进入手控/键盘/自由移动、不启动建图、不提交 delivery complete、不 stop、不发布 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖轮速复验提示和新增按钮的只读属性、固定验收端点、点击后的读回请求，以及无 motion/control POST 的边界。
- `docs/product/pc_tools_workstation.md`
  - 同步普通 PC 工作站轮速复验读回按钮合同，并保留 ROS2 配套工具只作工程观察的口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "wheel rerun"`，1 file passed，1 test passed，230 skipped。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，仅保留既有 Vite chunk size warning。
- 通过：`cd pc-tools/workstation && npm test`，3 files passed，417 tests passed。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `0.0.0.0:7001`，PID `83524`。
- 通过：只读 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `robot_api_connection_status=readable`、`objective_status=in_progress`、`objective_done=1/4`、`nav2_goal_succeeded=true`、`wheel_lr_nonzero=false`、`delivery_success=false`。
- 通过：构建产物 `pc-tools/workstation/dist/assets/index-B5KoLqXp.js` 包含 `plain-wheel-rerun-readback-refresh` / “读回复验”。

## 剩余风险

- 本轮只改 PC UI 读回入口和测试，不执行 Nav2、manual、keyboard、free-roam、map start、delivery、stop 或 `/cmd_vel`。
- 真实完整行程仍需要现场勾选安全确认后由用户触发重跑，再用该按钮复验同窗口 wheel L/R 非零和 delivery success。
- 相机首帧问题仍取决于现场 USB full-speed 拓扑修复，建图启动仍缺 `camera_first_frame`。
