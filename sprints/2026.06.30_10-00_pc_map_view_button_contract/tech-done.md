# PC 地图大屏观察按钮合同

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 给普通首屏地图的 `放大地图`、`全屏地图`、`观测模式` 三个视图按钮补齐按钮级 DOM 合同。
  - 三个按钮统一暴露 `data-map-view-action`、`data-target-surface=primary-map`、`data-sends-motion-when-clicked=false`、`data-starts-ros2=false`、`data-starts-rviz2=false`、`data-starts-map-runtime=false`、`data-starts-nav2=false`。
  - `观测模式` 额外暴露 `data-enter-size=fullscreen`、`data-hides-ordinary-actions-when-active=true`、`data-keeps-wysiwyg-overlays=image-route-robot-radar` 和 RViz2 launch 命令，证明它是 PC 内置大屏观察模式，不是启动 ROS2/RViz2。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展默认 Robot Control 首屏测试，固定地图大屏按钮的 no-motion/no-ROS2/no-runtime 合同，以及观测模式进入/退出后的状态。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 记录普通首屏地图视图按钮与 RViz2 配套边界。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`：通过，1 个测试文件，1 个用例通过。
- `npm test -- --run`：通过，2 个测试文件，390 个用例通过。
- `npm run lint`：通过，0 error；保留既有 4 个 Vue 换行 warning。
- `npm run build`：通过，Vite 仍提示单 chunk 超过 500 kB 的既有体积 warning；新 bundle 为 `index-BMOcdPCB.js`。
- `git diff --check`：通过。
- 已重启 PC Node 到 `0.0.0.0:7001`；端口监听 PID 为 `75236`。
- `GET http://127.0.0.1:7001/`：通过，页面返回新 bundle `index-BMOcdPCB.js` / `index-BQDMiOEq.css`。
- `GET http://127.0.0.1:7001/assets/index-BMOcdPCB.js`：通过，bundle 包含 `toggle_large_map`、`toggle_fullscreen_map`、`toggle_observer_map`、`data-starts-rviz2`、`data-hides-ordinary-actions-when-active`。
- live 只读 summary `http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`：HTTP 200，耗时 5.367546s；schema 为 `trashbot.pc_tools_workstation.robot_control_summary.v1`；地图 WYSIWYG 为“地图画面、图上路线和小车位置已显示；雷达来源点存在但当前不贴到地图：已有雷达来源点 81 个，但雷达未运行，所以当前不贴到地图。”；`radar_overlay=not_current`、当前地图雷达点 `0`。

## 剩余风险

- 本轮只改 PC Web 地图视图按钮、DOM 合同、测试和文档；不启动 RViz2、不启动 ROS2 runtime、不执行 Nav2、不启动建图、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 真实 RViz2 显示仍取决于上车 ROS graph 是否发布 `/map`、`/scan`、TF、Nav2 path 和 AMCL pose；普通用户默认仍在 PC 工作站大地图里观察。
