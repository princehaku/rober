# PC Direct Map Shell Bigscreen Contract Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/App.vue`
  - 识别 `?view=map`、`?mode=map-only` 或 `#map` 后，把 App 页面壳标记为直达地图模式。
  - 直达地图模式隐藏顶部栏和默认关闭的高级工具，避免第二屏地图大屏还带普通控制台外壳。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 直达地图模式继续进入 full + 只看地图状态，并默认切到最高 `800%` 缩放。
  - 地图卡和“打开地图大屏”链接暴露 `data-direct-map-view-default-zoom-percent=800%`。
- `pc-tools/workstation/src/styles.css`
  - `.shell[data-direct-map-view-requested=true]` 使用 `100vw`、`100vh` 和零 padding，让地图大屏真正铺满浏览器。
- `pc-tools/workstation/test/App.test.ts`
  - 锁定普通首页仍为 `600%` 大地图。
  - 锁定 `?view=map` 是 App shell map-only、顶栏/高级工具隐藏、地图 `800%`，并且不启动 ROS2/RViz2/建图/Nav2/manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录直达地图大屏合同和 ROS2 配套分层。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default"`：通过。
- `npm test -- test/App.test.ts -t "opens direct map view from URL without starting ROS2 or motion"`：通过。
- `npm test -- --run`：通过，2 个测试文件、396 个测试全部通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-D6XwmOj2.js` 与 `dist/assets/index-DCA8Xtd4.css`。
- `git diff --check`：通过。
- 7001 重启：旧 `node` PID `10319` 已停止，新监听进程为 `node` PID `22810`，地址 `TCP *:7001`。
- live bundle 只读检查：`http://127.0.0.1:7001/?view=map` 已引用 `index-D6XwmOj2.js` 和 `index-DCA8Xtd4.css`；构建产物命中 `page_shell_map_only`、`page_fixed_fullscreen_map_only`、`data-direct-map-view-default-zoom-percent`、`800%`、`data-starts-ros2`、`data-sends-motion-when-clicked`、`width:100vw`、`min-height:100vh` 和 `padding:0`。
- live summary 只读检查：Robot API connection 当前为 `degraded`，地图雷达 overlay 当前点数为 `0`，Nav2 action card 仍为 `ready_needs_wheel_rerun`；本轮未执行任何运动命令。

## 剩余风险

- 本轮只改 PC Web 显示和 DOM 合同，不启动 RViz2、Foxglove、ROS2 runtime，也不执行任何运动命令。
- 直达地图模式默认 `800%` 可能需要滚动查看完整地图；普通首页仍保留 `适配` 和 `600%` 默认视图。
- 当前 live 地图雷达点数仍为 0，说明“地图大屏更大”已改善，但雷达开始后的地图点所见即所得仍需要下一轮继续围绕实时雷达刷新/贴图闭环推进。
