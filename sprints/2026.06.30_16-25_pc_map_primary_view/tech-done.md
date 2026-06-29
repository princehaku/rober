# 2026.06.30 16:25 PC map primary view

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/styles.css`
  - 普通首屏 `visual-first` 桌面布局下，地图卡固定横跨整行，避免地图被相机或状态卡压成小块。
  - 地图大图高度提升为 `clamp(680px, 84vh, 1180px)`，全屏地图高度提升为 `calc(100vh - 160px)`。
- `pc-tools/workstation/test/App.test.ts`
  - 锁定地图卡在 `visual-first` 布局中存在整行布局合同。
  - 锁定新的大图和全屏高度 CSS 合同，防止后续回退成小地图。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`
  - 同步说明 ROS2 配套工具使用边界：RViz2 用于工程调试 `/map`、`/scan`、TF、Nav2 path 和 AMCL pose；普通用户现场操作继续以 PC 工作站大地图为主。
- `sprints/2026.06.30_16-05_pc_keyboard_main_action_contract/tech-done.md`
  - 修正键盘 sprint 文档中的变量名笔误，不改变功能。

## 验证结果

- `cd pc-tools/workstation && npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`
  - 通过：`Test Files 1 passed (1)`，`Tests 1 passed | 218 skipped (219)`。
- `cd pc-tools/workstation && npm test -- --run`
  - 通过：`Test Files 2 passed (2)`，`Tests 389 passed (389)`。
- `cd pc-tools/workstation && npm run build`
  - 通过：Vite build 成功；保留既有 `Some chunks are larger than 500 kB after minification` warning。
- `git diff --check`
  - 通过：无 whitespace error。
- 7001 live 只读 HTTP smoke
  - 已重启：`npm run api -- --host 0.0.0.0 --port 7001`，`lsof` 显示 `TCP *:7001 (LISTEN)`。
  - `GET http://127.0.0.1:7001/` 返回当前构建产物：`index-Bkps9FmU.js` 与 `index-CWSPUlqS.css`。
  - `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 HTTP 200，`schema=trashbot.pc_tools_workstation.robot_control_summary.v1`，`map_status=visible`，`map_wysiwyg=current_map_visible`，`card_count=7`。
  - 当前 CSS 产物包含 `visual-first .plain-map-panel` 整行布局和新的 `clamp(680px,84vh,1180px)` / `calc(100vh - 160px)` 地图高度合同。

## 剩余风险

- 本轮只改 PC Web 只读显示尺寸，不启动 RViz2、不启动 ROS2 runtime、不执行 Nav2、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 真实现场是否“足够大”仍需你在 PC 浏览器上确认；工程调试可另开 RViz2，但普通界面不嵌 RViz2。
