# PC 地图太小与 ROS2 配套说明

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：地图卡可见说明直接写明普通用户先点 `/map` 大屏，ROS2 配套是本地 RViz2 和远程 Foxglove，入口在“工程观察”，只观察地图/雷达/TF/路径/定位，不发车。
- `pc-tools/workstation/test/App.test.ts`：补充 DOM 文案断言，确保这条说明可见且不暴露长工程命令。
- `docs/product/pc_tools_workstation.md`：同步 PC 地图与 ROS2 配套的用户口径。

## 验证结果

- `npm --prefix pc-tools/workstation test -- --run test/App.test.ts`：通过，233 个用例通过。
- `npm --prefix pc-tools/workstation test -- --run test/robotControlSummary.test.ts test/catalog.test.ts`：通过，190 个用例通过。
- `git diff --check`：通过。
- `npm --prefix pc-tools/workstation run lint`：通过。
- `npm --prefix pc-tools/workstation run build`：通过；仅保留既有 Vite chunk size 警告。
- `npm --prefix pc-tools/workstation test -- --run`：通过，423 个用例通过。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `43203`；`GET /` 返回 200，`GET /map` 返回 200。
- `GET /api/robot-control/summary` 只读 smoke：`map_display_primary_url=/map`、`map_display_default_zoom_percent=1000%`、`map_display_ros2_companion_tools=[rviz2,foxglove]`、`map_display_primary_action_label=进入地图大屏`、`map_display_sends_motion_when_clicked=false`、`map_display_starts_ros2=false`、`map_display_starts_rviz2=false`。

## 剩余风险

- 本轮只改 PC 可见说明和只读合同测试，没有启动 RViz2/Foxglove，也没有真实打开浏览器验收 `/map` 视觉尺寸；后续如现场仍觉得地图小，下一步应做截图级 UI 验收并继续调大 `/map` 直达页布局。
