# PC 地图大屏显示证明

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏地图卡新增 `plain-map-display-proof` 可见验收条，直接说明当前是 PC 默认大地图主视图，或 `?view=map` 只看地图大屏。
  - 验收条同步当前缩放、地图尺寸状态、WYSIWYG overlay 范围和 ROS2 配套分工：RViz2 用于工程调试，Foxglove 需要 bridge handoff 后做浏览器远程观察。
  - 继续保持普通用户文案，不在默认首屏暴露 `Nav2` / `路线` 这类禁词；DOM 合同仍保留机器可读 `data-starts-nav2=false`。
  - 验收条固定只读，不启动 ROS2/RViz2/Foxglove/行程执行/建图 runtime，不发送任何运动命令。
- `pc-tools/workstation/test/App.test.ts`
  - 默认首屏锁定 `plain-map-display-proof` 的 DOM 字段、普通文案、`600%` 默认缩放和 ROS2 配套只读边界。
  - `?view=map` 直达模式锁定 `800%`、fullscreen/observer 状态和不启动 ROS2/RViz2/Foxglove/行程执行/运动命令。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步地图大屏显示 proof 合同，明确普通用户仍使用 PC 简易页，RViz2/Foxglove 只作配套观察。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`：通过。
- `npm test -- test/App.test.ts -t "opens direct map view from URL without starting ROS2 or motion"`：通过。
- `npm test -- --run`：通过，2 个测试文件、397 个测试全部通过。
- `npm run lint`：通过，0 errors；仍有既有 4 个 Vue 换行 warning。
- `npm run build`：通过，生成 `dist/assets/index-BMtmeXsd.js` 与 `dist/assets/index-DCA8Xtd4.css`。
- `git diff --check`：通过。
- Live 7001 验证：重启后 `node` PID `71769` 监听 `TCP *:7001`；首页引用新构建资源 `index-BMtmeXsd.js` / `index-DCA8Xtd4.css`。
- Live bundle 验证：`index-BMtmeXsd.js` 命中 `plain-map-display-proof`、`pc_plain_big_map`、`Foxglove bridge`、`handoff_required`、`图上行程、小车位置和雷达标记` 和 `不启动 ROS2/RViz2/Foxglove/行程执行`。
- Live summary 验证：`GET /api/robot-control/summary` 返回地图已观察、可通行格 425、图上路线 18 点、pose 已观察；雷达当前贴图点 0，旧来源点 81 只作诊断，不冒充当前地图标记。

## 剩余风险

- 本轮只补 PC Web 显示 proof、测试和文档；没有启动 RViz2、Foxglove、ROS2 runtime、Nav2、建图 runtime，也没有发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- Foxglove 仍是 handoff 口径，仓库当前没有现成 Foxglove bridge launch；真实远程观察需要后续部署 bridge 并现场验证。
- 工作区仍保留两个历史 artifact 脏文件，本轮未修改、未纳入提交。
