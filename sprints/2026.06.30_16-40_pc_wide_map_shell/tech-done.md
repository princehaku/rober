# 2026.06.30 16:40 PC wide map shell

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/styles.css`
  - 将桌面 `.shell` 宽度从 `min(1120px, calc(100% - 32px))` 放宽到 `min(1560px, calc(100% - 32px))`。
  - 保留移动端既有窄屏规则，避免小屏按钮和说明挤压。
- `pc-tools/workstation/test/App.test.ts`
  - 在普通首屏测试中锁定新的桌面外壳宽度合同，防止地图又被旧 1120px 容器压小。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`
  - 同步说明本轮只扩大 PC Web 只读页面容器，不改变 ROS2、Nav2、manual、keyboard、free-roam 或 `/cmd_vel` 安全边界。

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
  - `GET http://127.0.0.1:7001/` 返回当前构建产物：`index-CkvyH_nC.js` 与 `index-BZI7zFw0.css`。
  - `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 HTTP 200，`schema=trashbot.pc_tools_workstation.robot_control_summary.v1`，`map_status=visible`，`map_wysiwyg=current_map_visible`，`card_count=7`。
  - 当前 CSS 产物可匹配 `width:min(1560px,calc(100% - 32px))`、`plain-map-panel{grid-column:1 / -1}` 和 `height:clamp(680px,84vh,1180px)`。

## 剩余风险

- 本轮只解决大屏 PC 横向空间被容器限制的问题，没有触发真实地图刷新、RViz2、Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 真实现场是否满足“地图足够大”仍需要在目标 PC 浏览器上验收。
