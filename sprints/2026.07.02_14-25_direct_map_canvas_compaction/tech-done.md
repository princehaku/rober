# tech-done

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/styles.css`
  - `/map` 直达页隐藏“收起地图 / 退出全屏 / 退出只看”三个普通视图切换按钮。
  - `plain-map-wysiwyg-layer-strip` 改为地图画布内绝对定位浮层，不再占用地图垂直布局高度。
  - `/map` 内部地图层改为按紧凑工具条显式扣减视口高度，避免 grid/flex 百分比把内部画布算小。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 PC 地图样式合同测试，覆盖直达页隐藏冗余按钮、图层浮层和显式画布高度。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 `/map` 直达页画布收敛、ROS2 配套仍只作 RViz2/Foxglove 观察。
- `pc-tools/README.md`
  - 同步记录 `/map` 大屏显示合同和 no-motion 边界。

## 验证结果

- `npm test -- test/App.test.ts`
  - 通过，`Test Files 1 passed (1)`，`Tests 237 passed (237)`。
- `npm test -- test/robotControlSummary.test.ts`
  - 通过，`Test Files 1 passed (1)`，`Tests 10 passed (10)`。
- `npm run build`
  - 通过，生成 `dist/assets/index-BWCYxP2w.css` 和 `dist/assets/index-DzFy6gFD.js`；Vite 仍提示 JS chunk 超过 500 kB，这是既有体积提醒，不影响本轮地图 CSS 生效。
- `git diff --check`
  - 通过。
- 7001 live 验收
  - 已按 `ROBER_WORKSTATION_HOST=0.0.0.0 ROBER_WORKSTATION_PORT=7001 ROBER_ROBOT_API_BASE_URL=http://192.168.1.11:8787 npm run api -- --host 0.0.0.0 --port 7001` 重启。
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `TCP *:7001 (LISTEN)`。
  - `curl http://127.0.0.1:7001/api/health` 返回 `trashbot.pc_tools_workstation.health.v1`。
- 浏览器 `/map` 尺寸验收
  - viewport: `1280x720`。
  - `plain-map-panel`: `1280x720`。
  - `plain-map-layer`: `1272x668`，从旧的 `1272x632` 提升到接近整屏画布。
  - `plain-map-size-toggle` / `plain-map-fullscreen-toggle` / `plain-map-observer-toggle`: `display:none`。
  - `plain-map-wysiwyg-layer-strip`: `position:absolute`。
  - `ROS2观察` 仍可见，`data-ros2-companion-tools=rviz2,foxglove`，`data-foxglove-websocket-url=ws://192.168.1.11:8765`。

## 剩余风险

- 本轮只修 PC `/map` 显示密度和 ROS2 配套说明入口，不启动 RViz2/Foxglove bridge，不验证真实 ROS graph、真实 Nav2、真实 costmap 或运动链路。
- 真实远程 Foxglove 观察还依赖上位机已安装 `ros-humble-foxglove-bridge` 并启动 `ros2 launch ros2_trashbot_bringup foxglove_bridge.launch.py`。
- 浏览器验收基于 1280x720；更大外接屏应按同一 CSS 继续扩大画布，但未逐个物理屏幕验证。
