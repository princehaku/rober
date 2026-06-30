# PC 地图大屏主入口 Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 将地图卡标题行的“打开地图大屏”提升为第一个主入口，普通用户无需记住 `?view=map`。
  - 入口新增 `data-user-facing-primary-map-action=true`、`data-ordinary-user-map-entry=true`、`data-opens-new-window=true`、`data-ros2-companion-required=false`。
  - `plain-map-display-proof` 同步暴露主入口 test id、按钮文案和开新窗口语义，证明 PC 地图大屏才是普通用户解决地图太小的首选路径。
- `pc-tools/workstation/src/styles.css`
  - 为 `.plain-map-direct-view-link-primary` 增加轻量强调样式，并在窄屏下和其他地图工具同样伸展。
- `pc-tools/workstation/test/App.test.ts`
  - 锁定地图大屏入口在工具行第一位、普通用户入口字段、开新窗口字段、ROS2 配套非必需字段和 CSS class。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步说明普通用户优先使用 PC 地图大屏；RViz2 只作本地工程调试，Foxglove 只作 bridge 部署后的浏览器远程观察。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default"`：通过，1 个目标用例通过。
- `npm test -- test/App.test.ts -t "opens direct map view from URL without starting ROS2 or motion"`：通过，1 个目标用例通过。
- `npm test -- --run`：通过，2 个测试文件、397 个测试全部通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-Br1hU7sp.js` 和 `dist/assets/index-ChxCHc-R.css`；保留既有 Vite chunk size warning。
- `git diff --check`：通过。
- 7001 live：已停止旧 `node` PID `23878`，新监听进程为 `node` PID `45157`，地址 `TCP *:7001`。
- live bundle：`http://127.0.0.1:7001/` 引用 `index-Br1hU7sp.js` 和 `index-ChxCHc-R.css`；资源内命中 `data-user-facing-primary-map-action`、`data-ordinary-user-map-entry`、`plain-map-direct-view-link-primary`、`data-ros2-companion-required` 和 `data-primary-map-action-testid`。

## 剩余风险

- 本轮只改 PC Web 地图入口、样式、测试和文档；不启动 RViz2、Foxglove、ROS2 runtime、Nav2、建图 runtime，不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 真实浏览器全屏仍受用户手势和浏览器权限限制；`?view=map` 页面内大屏兜底仍保留。
