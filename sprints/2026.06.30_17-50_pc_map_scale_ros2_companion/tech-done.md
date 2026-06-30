# PC Map Scale ROS2 Companion Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏地图默认缩放从 `800%` 提升到 `1200%`，`?view=map` 直达地图大屏从 `1200%` 提升到 `1600%`。
  - 保留现有“打开地图大屏”“全屏地图”“只看地图”入口，并继续声明这些入口只改显示，不启动 ROS2/RViz2/Foxglove/Nav2/建图 runtime，不发车。
- `pc-tools/workstation/src/styles.css`
  - 大地图目标高度贴近整屏，fullscreen 高度改为 `100vh`。
- `pc-tools/workstation/test/App.test.ts`
  - 同步普通地图、直达地图、缩放按钮、display proof 和 ROS2 配套提示的 DOM 合同断言。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 记录 ROS2 配套分层：RViz2 用于本地工程调试，Foxglove 用于部署 bridge 后浏览器远程观察；普通用户优先使用 PC 简易工作站大地图。

## 验证结果

- `npm test -- App.test.ts`：通过，1 个测试文件、225 个测试通过。
- `npm test -- --run`：通过，3 个测试文件、402 个测试通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-Bj83bAYD.js` 与 `dist/assets/index-BCQK7HRw.css`。
- `git diff --check`：通过。
- 7001 重启：已停止旧 `node` PID `78116`，新监听进程为 `node` PID `87620`，地址 `TCP *:7001`。
- live 只读 smoke：
  - `GET http://127.0.0.1:7001/` 返回新构建页面，HTML 引用 `/assets/index-Bj83bAYD.js` 与 `/assets/index-BCQK7HRw.css`。
  - `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `ok=true`、`live_status=needs_wheel_rerun`；本 smoke 未发送任何运动请求。
  - `GET http://127.0.0.1:7001/assets/index-Bj83bAYD.js` 中确认包含 `1200%`、`1600%`、`RViz2`、`Foxglove`。

## 剩余风险

- 本轮只改变 PC 地图显示大小和 ROS2 配套说明，不启动 RViz2/Foxglove，不配置 bridge，不执行真实 Nav2/建图/自由移动。
