# PC 地图大屏 WYSIWYG 刷新

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 进入“全屏地图”时自动刷新 `/api/robot-control/map/preview`，并同步读取 `/api/robot-control/radar/status`。
  - 进入“只看地图”时自动刷新同一轮地图和雷达状态，保证大屏不是放大的旧图。
  - `?view=map` 直达地图大屏首次加载时，初始地图刷新带上 radar status，同步更新地图、路线、机器人和雷达 overlay。
  - 全屏、只看地图、直达大屏入口新增 DOM 契约字段：`data-refreshes-map-preview-on-enter=true`、`data-refreshes-radar-status-on-enter=true`。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展普通用户首屏大地图测试，确认全屏/只看地图入口会额外触发 map preview 和 radar status 只读刷新。
  - 扩展 `?view=map` 直达大屏测试，确认打开第二屏不会启动 ROS2、Nav2、建图、手控或 `/cmd_vel`，但会刷新当前地图和雷达状态。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default|opens direct map view"`：通过，2 passed。
- `npm test -- --run`：通过，2 test files、393 tests passed。
- `npm run lint`：通过，0 errors；保留既有 4 个 Vue multiline warning。
- `npm run build`：通过，产物 `dist/assets/index-Bf8k5VmY.js`。
- `git diff --check`：通过，无 whitespace 问题。
- 7001 重启：`npm run api` 后 `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 Node PID `14242` 监听 `*:7001`。
- 7001 只读 smoke：`curl 'http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787'` 返回 `trashbot.pc_tools_workstation.robot_control_summary.v1`；小车 API 读回仍有 `fetch_timeout_2400ms`，所以仅证明 PC Node 正常。

## 剩余风险

- 当前验证为 PC 端 DOM 和 mock API 行为，未证明真实上车端 radar/status 与 map/preview 在现场总能及时返回。
- 大屏自动刷新只读画面，不启动 RViz2/Foxglove；专业调试工具仍需要 operator 在现场单独打开。
