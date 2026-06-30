# PC Direct Map View Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 地图卡新增 `?view=map` 直达地图大屏入口和“打开地图大屏”链接。
  - 页面用 `?view=map`、`?mode=map`、`?mode=map-only` 或 `#map` 打开时，自动进入页面内全屏只看地图状态。
  - DOM 暴露 `data-direct-map-view-requested`、`data-direct-map-view-url="?view=map"` 和 `data-direct-map-view-behavior=page_fixed_fullscreen_map_only`。
  - 直达模式只改变 PC Web 显示，不自动请求浏览器 Fullscreen API、不启动 ROS2/RViz2/Foxglove/Nav2/建图 runtime、不发送运动命令。
- `pc-tools/workstation/src/styles.css`
  - 为“打开地图大屏”链接补齐按钮尺寸，保持地图工具栏稳定。
- `pc-tools/workstation/test/App.test.ts`
  - 锁定默认首屏的地图大屏链接和只读合同。
  - 新增 `?view=map` URL 直达用例，验证页面内全屏只看地图、WYSIWYG overlay 保留、且不启动 ROS2/RViz2/Nav2/运动。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步说明普通用户地图大屏与 ROS2 工程配套的分层：普通用户用 PC `?view=map`，工程调试用 RViz2，浏览器远程观察用 Foxglove。

## 验证结果

- `npm test -- test/App.test.ts -t "opens direct map view from URL without starting ROS2 or motion"`：通过，1 个目标测试通过。
- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default"`：通过，1 个目标测试通过。
- `npm test -- --run`：通过，2 个测试文件、392 个测试全部通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-CcXj_cN7.js` 与 `dist/assets/index-1TFDR4Wy.css`。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`，监听进程为 `node` PID `39118`，页面入口引用 `index-CcXj_cN7.js` 与 `index-1TFDR4Wy.css`。
- live bundle 检查：JS 命中 `打开地图大屏=1`、`view=map=4`、`data-direct-map-view-requested=2`、`page_fixed_fullscreen_map_only=2`、`data-starts-rviz2=4`；CSS 命中 `plain-map-direct-view-link=1`。

## 剩余风险

- 本轮只补 PC Web 显示和只读 DOM 合同，不启动 RViz2/Foxglove/ROS2 runtime，也不发送运动命令。
- 未做真实上位机 HIL 验证；`?view=map` 实际可读性仍受现场地图图片分辨率、浏览器窗口和显示器 DPI 影响。
