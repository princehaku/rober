# Plain Refresh Map Radar WYSIWYG

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `refreshPlainConsole()`，普通首屏 `连接/刷新` 先刷新 summary，再只读刷新地图 preview，并顺带读取雷达 status。
  - 该入口只调用 PC 固定 GET/summary、GET/map preview、GET/radar status，不触发 manual、Nav2、free-roam、delivery、stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 新增回归：点击 `连接/刷新` 后 summary、map preview、radar status 都各增加一次，只读刷新后地图当前事实显示真实地图画面。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "plain connection refresh"`，`Tests 1 passed | 165 skipped (166)`。
- 已通过：`cd pc-tools/workstation && npm test`，`Tests 292 passed (292)`。
- 已通过：`cd pc-tools/workstation && npm run build`。
  - 保留既有 Vite chunk size warning：`Some chunks are larger than 500 kB after minification`。
- 已通过：`git diff --check`。
- 已重启本机 PC Node，当前 `node` 监听 `*:7001`。
- live 只读验证：
  - `GET /api/robot-control/map/preview?baseUrl=http://192.168.1.11:8787` 返回 `proxy_status=preview_forwarded`、`width=223`、`height=116`、`image_data_url` 存在、`free=421`。
  - `GET /api/robot-control/radar/status?baseUrl=http://192.168.1.11:8787` 返回 `proxy_status=status_loaded`、`remote_http_status=200`、`latest_scan_proof_fresh=false`。

## 剩余风险

- 本轮只修普通首屏刷新行为，不执行真实 Nav2、键盘手控或自由移动。
- 地图 preview 能否显示仍取决于上车 `/api/map/preview` 返回真实 `image_data_url`；若上车端失败，PC 会继续显示失败原因。
