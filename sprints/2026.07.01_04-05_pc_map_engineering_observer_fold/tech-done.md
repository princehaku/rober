# PC 地图工程观察折叠

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通地图 proof 文案精简为大地图、缩放、WYSIWYG overlay 和不发车边界，不再把 RViz2/Foxglove 命令直接铺在普通首屏。
  - 新增默认折叠的“工程观察”入口，展开后显示 RViz2 launch、Foxglove bridge launch 和 `ws://192.168.1.11:8765`。
  - `live_closure_summary` 地图配套 DOM 同步暴露 Foxglove WebSocket 地址，仍固定不启动 ROS2/RViz2/Foxglove/Nav2/建图 runtime。
- `pc-tools/workstation/src/server/robotControlSummary.ts`、`pc-tools/workstation/src/shared/contracts.ts`
  - 新增只读字段 `map_display_foxglove_websocket_url=ws://192.168.1.11:8765`。
- `pc-tools/workstation/src/styles.css`
  - 给“工程观察”折叠区增加轻量样式，默认不抢普通地图主视图。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`
  - 覆盖普通 proof 不再显示工程命令、工程观察默认收起、展开后显示 ROS2 配套命令和 Foxglove 地址。
- `docs/product/pc_tools_workstation.md`
  - 同步产品边界：普通用户继续用 PC 大地图，ROS2 配套默认折叠为工程观察。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts test/App.test.ts -t "map|ROS2|Foxglove|plain-map-display-proof|plain-map-ros2-tool-note|plain-live-map-companion-summary"`。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`cd pc-tools/workstation && npm test -- --run`，3 files / 413 tests passed。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`git diff --check`。
- 通过：7001 只读 smoke，`GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `source_base_url=http://192.168.1.11:8787`，`live_closure_summary.map_display_foxglove_websocket_url=ws://192.168.1.11:8765`。

## 剩余风险

- 本轮只改 PC 只读显示和合同字段，没有启动 RViz2/Foxglove，也没有验证上车端是否已安装 `foxglove_bridge`。
- 没有触发任何 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel` 运动接口。
