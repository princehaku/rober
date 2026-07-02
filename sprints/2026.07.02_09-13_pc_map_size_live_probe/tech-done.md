# PC Map Size Live Probe

## sprint_type

micro

## 实际改动

- 回答并固化“PC 地图太小 / ROS2 有什么配套”的现场口径：
  - 普通用户优先使用 PC 自带大地图和 `/map` 直达页。
  - ROS2 配套只作为工程观察：本地 RViz2，远程 Foxglove bridge + Foxglove Web。
  - RViz2/Foxglove 不替代 PC 简易界面，不作为路线执行、自由移动或建图前置。
- 更新 `docs/product/pc_tools_workstation.md`，记录 7001 live DOM 尺寸 smoke 和 `/map` HTTP 200 证据。
- 本轮不改 motion/control 逻辑，不发送任何底盘、Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

## 验证结果

- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：Node 正在监听 `*:7001`，PID `54114`。
- `curl -i http://127.0.0.1:7001/map`：HTTP 200，返回 Vite 构建后的 `index.html`。
- Chrome DOM smoke，viewport `1440x1000`：
  - 首页 `plain-map-panel`：约 `1418x2278`，`plain-map-wysiwyg-view`：约 `1388x1886`。
  - `/map` 直达页 `plain-map-panel`：约 `1440x1000`，`plain-map-wysiwyg-view`：约 `1432x906`。
  - 两处均为 `data-map-zoom-percent=2400%`，标题为 `PC 大地图 2400% · /map 满屏 · 普通看 /map；工程看 RViz2 / Foxglove`。

## 剩余风险

- 本轮是 live probe 和文档固化，没有改 Vue/CSS/后端行为，因此不需要重新验证 motion/control 链路。
- 如果现场仍看到小地图，优先确认访问的是 `http://<PC-IP>:7001/map`，并确认浏览器没有打开旧端口、旧 tab 或旧构建缓存。
- Nav2 wheel raw L/R 非零、delivery success、键盘连续手控、自由移动和建图真实运动仍需要现场安全确认后继续验收。
