# 2026.06.30 12:45 PC 全屏地图视图

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏地图卡新增 `全屏地图` / `退出全屏` 切换。
  - 地图默认仍是放大视图；全屏状态只改变只读地图、路线、小车位置和雷达 overlay 的显示尺寸。
- `pc-tools/workstation/src/styles.css`
  - 新增全屏地图固定视口样式，让地图浮到当前浏览器视口内作为主工作区。
  - 保持移动端响应式高度，避免全屏后按钮和 caption 挤出可操作区域。
- `pc-tools/workstation/test/App.test.ts`
  - 补默认大地图、全屏切换、退出全屏、CSS 合同断言。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步说明 ROS2 配套选择：工程调试用 RViz2，普通用户现场操作用 PC 工作站全屏地图。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`
  - `Test Files 1 passed (1)`，`Tests 1 passed | 218 skipped (219)`。
- 通过：`cd pc-tools/workstation && npm test -- --run`
  - `Test Files 2 passed (2)`，`Tests 389 passed (389)`。
- 通过：`cd pc-tools/workstation && npm run build`
  - Vite build 成功；仅保留既有 chunk size warning。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `0.0.0.0:7001` 后做只读 HTTP spot check。
  - `GET http://127.0.0.1:7001/` 返回 200。
  - `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 200，响应中未出现 `robot_control_executed=true`。

## 剩余风险

- 本轮只改 PC Web 显示，不启动 RViz2、不刷新地图、不启动雷达、不执行 Nav2、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- RViz2 仍是工程调试工具，普通用户界面只嵌入当前 PC 自绘地图；后续若要把 Foxglove/rosbridge 接进 Web，需要另起 sprint 做 ROS bridge 安全边界。
