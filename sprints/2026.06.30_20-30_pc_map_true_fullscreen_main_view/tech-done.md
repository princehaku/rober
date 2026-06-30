# PC 地图主视图与真全屏

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - PC 普通地图 panel 新增 `data-default-map-layout=dominant-first-screen-map`、`data-default-map-height-mode=near-viewport` 和 `data-browser-fullscreen-active`。
  - 默认地图缩放从 400% 提升到 500%，缩放上限提升到 600%，继续保证底图、路线、小车位姿和雷达点共用同一个 overlay frame。
  - `全屏地图` 与 `观测模式` 优先调用浏览器 Fullscreen API；浏览器拒绝或测试环境不支持时，继续使用页面内 fixed 大图兜底。
  - 退出原生全屏时同步收起 PC 地图状态，避免按钮仍显示“退出全屏”。
- `pc-tools/workstation/src/styles.css`
  - 增加地图主视图高度变量，默认大地图 panel 和 visual-first 网格使用近首屏高度。
  - 增加 `.plain-map-panel[data-fullscreen="true"]:fullscreen`，让浏览器原生全屏时铺满真实屏幕。
- `pc-tools/workstation/test/App.test.ts`
  - 固定默认 500% 缩放、600% 上限、主视图 DOM 合同和浏览器 Fullscreen API 合同。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步说明：普通用户默认用 PC 内置大地图；ROS2 工程配套用 RViz2；浏览器远程多人观察用 Foxglove。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default"`：通过，1 个用例通过。
- `npm test -- --run`：通过，2 个测试文件，391 个用例通过。
- `npm run lint`：通过，0 error；仍有 `RobotControlConsolePanel.vue` 既有 4 条 Vue warning，本轮未新增。
- `npm run build`：通过，产物为 `dist/assets/index-BCk7Gb0P.js`、`dist/assets/index-C7tHGYa9.css`；仍有 Vite chunk > 500 kB 既有提示。
- `git diff --check`：通过。
- 7001 已重启为新 bundle，`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 Node PID 14005，监听 `TCP *:7001`。
- live bundle 验证：`index-BCk7Gb0P.js` 包含 `dominant-first-screen-map`、`near-viewport`、`data-uses-browser-fullscreen-api`、`requestFullscreen`、`500%`、`ros2 launch ros2_trashbot_bringup rviz.launch.py`；JS 中包含缩放序列 `[1,1.5,2,3,4,5,6]`。`index-C7tHGYa9.css` 包含地图高度变量、`calc(100vh - 18px)`、`.plain-map-panel[data-fullscreen=true]:fullscreen` 和 `height:var(--plain-map-fullscreen-height)`。
- live 只读 summary 验证：`/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 返回 HTTP 200，connection 为 degraded；地图 `map_once_observed=true`，当前雷达 `radar_stopped`，地图 WYSIWYG 文案明确“雷达来源点存在但当前不贴到地图”，不把停止状态下的雷达来源点冒充成当前地图标记。
- 浏览器级 DOM 尺寸验证：在 1280x720 视口下，`plain-map-panel` 为 1254x1195，`.plain-map-layer` 为 1224x960、`min-height=960px`，`.plain-map-overlay-frame` 为 6110x4790；DOM 合同为 `data-default-map-layout=dominant-first-screen-map`、`data-default-map-height-mode=near-viewport`、默认缩放 `500%`。`全屏地图` 与 `观测模式` 的 `data-uses-browser-fullscreen-api=true`，普通 `收起/放大地图` 不误标该属性。

## 剩余风险

- 本轮只改 PC 地图显示、全屏行为、测试和文档；没有启动 ROS2、RViz2、Nav2、建图 runtime、manual/free-roam/keyboard/delivery 或 `/cmd_vel`。
- 浏览器 Fullscreen API 仍受浏览器权限和用户手势约束；被拒绝时页面内 fixed 大图兜底生效。
