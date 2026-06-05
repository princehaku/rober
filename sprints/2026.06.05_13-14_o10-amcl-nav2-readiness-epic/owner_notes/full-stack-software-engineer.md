# Full-stack Software Engineer Note

## sprint_type

epic owner note

## 本轮任务

把 O10/O7 的 PC proof 从 curl/API smoke 推进到浏览器按钮级 workflow：operator 在
`pc-tools/workstation` 页面勾选 confirmation 后，通过真实按钮触发 scan proof refresh、
scan proof latest、map proof latest 和 localize reset，并在 UI 内看到 canonical path、hz、
TF、fallback、artifact status、failure/blocker、fail-closed/safety 字段。

## 用户旅程变化

- `雷达 / 建图 / 定位` 区新增 `Read scan latest` 和 `Read map proof latest` 两个只读按钮。
- `Refresh scan proof`、`Read scan latest`、`Read map proof latest` 返回后，统一在
  lock message 展示 `upper_request.path`、HTTP、adapter、evidence_ref、ACK/T=1001 缺口、
  `safe_to_control=false`、not_proven/fail-closed，以及 upper 业务摘要。
- scan proof readback 展示 fresh、hz、TF、fallback、continuous blockers、artifact status/path。
- map proof readback 展示 canonical/resolved/configured/compatibility paths、artifact status/path、
  upper blockers、`safe_to_control=false`、`robot_control_executed=false`。

## 实际改动

- `pc-tools/workstation/src/client/workstationApi.ts`
  - 新增 `radar_scan_proof_latest` 和 `map_proof_latest` client command。
  - 新增通用 GET readback query helper，避免把 latest readback 错路由到 map/list。
- `pc-tools/workstation/src/components/O7LiveOperatorPanel.vue`
  - 新增 `Read scan latest`、`Read map proof latest` 按钮。
  - 扩展 command result 文案，展示 scan proof hz/TF/fallback 和 map proof canonical path。
- `pc-tools/workstation/scripts/o7-direct-upper-browser-workflow.mjs`
  - 新增 Playwright workflow collector，输出按钮级 JSON 和截图证据。
- `pc-tools/workstation/package.json`
  - 新增 `npm run o7:direct-upper-workflow`。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展首屏、按钮路径、readback 文案和 same-origin guard 测试。
- `docs/interfaces/o7_direct_upper_pc_api.md`
  - 补充按钮级 readback 入口和 workflow 证据边界。
- `docs/interfaces/o7_live_operator_panel.md`
  - 补充 UI 行为与验收要求。
- `docs/product/pc_tools_workstation.md`
  - 补充 direct-upper browser workflow 脚本与产品边界。

## 接口影响

- 未新增后端 API route；复用已有：
  - `GET /api/o7/direct-upper/radar/scan-proof/latest`
  - `GET /api/o7/direct-upper/map/proof/latest`
  - `POST /api/o7/direct-upper/radar/scan-proof/refresh`
  - `POST /api/o7/direct-upper/localize/reset`
- 前端新增两个按钮级入口，但仍只访问 PC 同源 `/api/o7/direct-upper/*`。
- 未改 ROS2、硬件、真实控车逻辑、OKR 或上一轮 sprint。

## 验证结果

### Unit / build

```bash
cd pc-tools/workstation && TMPDIR=/tmp npm test
```

结果：`Test Files 3 passed (3)`，`Tests 103 passed (103)`。

```bash
cd pc-tools/workstation && TMPDIR=/tmp npm run build
```

结果：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 通过，
Vite 输出 `✓ built in 1.72s`。

### 8788 API / curl

```bash
cd pc-tools/workstation && TMPDIR=/tmp PORT=8788 ROBER_UPPER_API_BASE_URL=http://192.168.1.11:8787 npm run api
```

结果：8788 API 启动成功。

```bash
curl -sS http://127.0.0.1:8788/api/o7/direct-upper/status
```

关键结果：`status=ready`，`upper_api_base_url_source=env`，`health_request.http_status=200`，
`status_request.http_status=200`，scan proof `hz=278.795`、`tf=true`、
`runtime_summary_fallback_used=true`，map canonical path
`/root/rober/onboard/runtime/map_lifecycle_latest.json`，`safe_to_control=false`。

```bash
curl -sS http://127.0.0.1:8788/api/o7/direct-upper/radar/scan-proof/latest
```

关键结果：HTTP 200 JSON，`upper_request.path=/api/radar/scan-proof/latest`，
`proof_status=scan_once_hz_raw_packet_tf_observed`，`hz=278.795`，`tf_observed=true`，
`runtime_summary_fallback_used=true`，`continuous_scan_status=not_proven`，
`safe_to_control=false`。

```bash
curl -sS http://127.0.0.1:8788/api/o7/direct-upper/map/proof/latest
```

关键结果：HTTP 200 JSON，`upper_request.path=/api/map/proof/latest`，
`fail_closed=true`，`proof_status=not_proven`，canonical/resolved/configured path 均为
`/root/rober/onboard/runtime/map_lifecycle_latest.json`，compat path 为
`/root/rober/runtime/map_lifecycle_latest.json`，`safe_to_control=false`。

### Browser workflow evidence

```bash
cd pc-tools/workstation && TMPDIR=/tmp npm run o7:direct-upper-workflow
```

结果：`status=ok`，页面 `http://127.0.0.1:8788/` 非空，无 framework overlay，
`console_messages=[]`。覆盖按钮：

- `Refresh scan proof` -> `/api/radar/scan-proof/refresh`，HTTP 200，`fresh=true`，
  `hz=277.908`，`tf=observed`，`fallback=true`，`continuous=not_proven`，
  `safe_to_control=false`。
- `Read scan latest` -> `/api/radar/scan-proof/latest`，HTTP 200，artifact loaded，
  `hz=277.908`，`tf=observed`，`fallback=true`，`safe_to_control=false`。
- `Read map proof latest` -> `/api/map/proof/latest`，HTTP 200，canonical/resolved/configured
  path 均为 `/root/rober/onboard/runtime/map_lifecycle_latest.json`，
  `upper_not_proven=upper_api_map_proof_not_proven`，`safe_to_control=false`。
- `Localize reset` -> `/api/localize/reset`，HTTP 200，但仍显示 ACK/T=1001 缺口和
  `safe_to_control=false`。

证据文件：

- JSON: `pc-tools/workstation/.workstation-runtime/o7-direct-upper-browser-workflow.json`
- Screenshot: `pc-tools/workstation/.workstation-runtime/o7-direct-upper-browser-workflow.png`

### Browser availability

Browser plugin not available；按前端验证 skill 降级使用项目 devDependency Playwright/Chromium。

## 剩余风险

- evidence_type：`browser_workflow_button_level`。
- 不得外推为：PC WASD 控车、HIL、AMCL ready、Nav2 consumption、地图可导航、真实 delivery success。
- scan proof 仍显示 `continuous_scan_status=not_proven`，不能声明 continuous radar ready。
- map proof latest 当前 upper 业务状态仍是 `not_proven`，只能证明 canonical path readback，不证明 AMCL/Nav2。
- localize reset HTTP 200 只证明 API 请求成功，不证明 `/amcl_pose`、TF 或定位恢复。
- `safe_to_control=false`、`robot_control_executed=false`、`robot_ack_connected=false`、`t1001_observed=false` 全程保持。

## 新 KR

无。当前只补 O10/O7 浏览器按钮级证据，不提出新 KR，不更新 OKR 完成度。
