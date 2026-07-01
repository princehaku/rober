# PC 地图默认 150% 大图

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏地图和 `/map` 直达大屏默认缩放从 `100%` 改为 `150%`。
  - `适配` 仍回到 `100%` 全图，`细节放大` 仍到 `2400%`。
  - 可见说明改为“默认 150% 现场大图”，并明确“适配回到 100% 全图”。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `live_closure_summary.map_display_default_zoom_percent` 改为 `150%`。
  - `map_display_companion_plain` 同步说明 PC `/map` 是普通用户地图主工具，RViz2/Foxglove 只作工程观察。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 同步 `map_display_default_zoom_percent` 类型合同为 `150%`。
- `pc-tools/workstation/src/styles.css`
  - 地图 overlay frame 注释同步为默认 `150%`、适配 `100%`。
- `pc-tools/workstation/test/App.test.ts`
  - 更新普通首屏和 `/map` 直达大屏默认缩放、按钮状态、放大/适配断言。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 更新 live summary 地图默认缩放和 companion 文案断言。
- `docs/product/pc_tools_workstation.md`
  - 记录当前有效地图显示合同：默认 `150%` 现场大图，`适配` 回 `100%` 全图，ROS2 配套仍默认折叠。

## 验证结果

- 已通过：`npm test -- --run test/App.test.ts -t "plain map"`，1 file passed，3 tests passed / 228 skipped。
- 已执行但筛选词未命中：`npm test -- --run test/robotControlSummary.test.ts -t "map display"`，1 file skipped，9 tests skipped；后续用全量测试覆盖。
- 已通过：`npm test`，3 files passed，421 tests passed。
- 已通过：`npm run lint`。
- 已通过：`npm run build`，Vite 仍提示单 chunk 超过 500 kB 的既有 warning，构建成功。
- 已通过：`git diff --check`。
- 已重启 PC Node：`http://0.0.0.0:7001`，PID `6307`。
- 已通过只读 live GET：
  - `GET /api/robot-control/live-summary?baseUrl=http://192.168.1.11:8787` 返回 `map_display_default_zoom_percent="150%"`、`map_display_primary_url="/map"`、`map_display_ros2_companion_tools=["rviz2","foxglove"]`，且 `map_display_sends_motion_when_clicked=false`、`map_display_starts_ros2=false`、`map_display_starts_nav2=false`、`map_display_starts_map_runtime=false`。
  - `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 的 `live_closure_summary` 返回同样的地图显示合同。

## 剩余风险

- 本轮只改 PC 显示和只读合同，没有启动 ROS2/RViz2/Foxglove，也没有执行 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 150% 默认会让小地图更大，但窄屏可能需要横向滚动；`适配` 已保留为 100% 全图退路。
