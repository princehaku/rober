# Full-Stack Owner Note

## sprint_type

sprint_type: epic

## 本轮任务

- Objective：O7 PC operator workflow + O3 runtime material hook。
- Owner：User Touchpoint Full-Stack Engineer。
- 目标：PC workstation 侧接入上位机只读 `POST /api/radar/scan-proof/refresh`，让 operator 能从浏览器触发 scan proof refresh，并看到 fresh/stale/blocker 与 not_proven 边界。

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 新增 `radar_scan_proof_refresh` command、远端 `/api/radar/scan-proof/refresh` path、本机 `/api/o7/direct-upper/radar/scan-proof/refresh` path 和 `scan_proof_refresh` local path。
- `pc-tools/workstation/src/server/o7DirectUpperApi.ts`
  - 新增 `proxyO7DirectUpperRadarScanProofRefresh()`。
  - 沿用 radar/report 的现场默认策略：缺少 `ROBER_UPPER_API_BASE_URL` 时使用 `http://192.168.1.11:8787`，并返回 `upper_api_base_url_source=field_default`。
  - command response 保持 `safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`、`robot_ack_connected=false`、`t1001_observed=false`。
  - refresh command 额外保留 `driver_start_stop`、`pc_wasd_control`、`nav2_consumption`、`slam_map`、`delivery_success` 等 not_proven token。
- `pc-tools/workstation/src/server/index.ts`
  - 新增 PC 同源 `POST /api/o7/direct-upper/radar/scan-proof/refresh`。
- `pc-tools/workstation/src/client/workstationApi.ts`
  - 新增 workstation client endpoint 和 operator command helper 分支。
- `pc-tools/workstation/src/components/O7LiveOperatorPanel.vue`
  - 新增 `Refresh scan proof` operator 按钮，仍要求 `operator confirmation` 与 `evidence_ref`。
  - Direct 卡展示 scan proof artifact/freshness/age/latest status/top blockers。
  - 返回文案明确 read-only proof refresh，不证明 HIL、PC WASD、Nav2、map 或 delivery success。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 fixture、首屏断言、按钮同源代理断言。
  - 新增后端回归：scan proof refresh 缺 env 时走 field default，不触发底盘控制或 fake success。
- `docs/interfaces/o7_direct_upper_pc_api.md`
  - 记录 PC/upper path、env/field default、fixture、timeout、not_proven 和 forbidden action。
- `docs/product/pc_tools_workstation.md`
  - 同步 PC operator workflow 与产品边界。

## 安全边界

- PC 侧不直连 ROS graph。
- PC 侧不访问 LiDAR 串口。
- PC 侧不触发 `/api/base/manual`、`/cmd_vel`、WAVE ROVER JSON 或底盘运动。
- refresh 成功只代表 upper read-only refresh route 被 PC 同源代理调用；不证明 fresh `/scan` 已验收、LiDAR 长稳、HIL、PC WASD、Nav2、map、定位或 delivery success。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run`
  - 结果：通过。
  - 关键输出：`Test Files  3 passed (3)`，`Tests  99 passed (99)`。
- `cd pc-tools/workstation && npm run build`
  - 结果：通过。
  - 关键输出：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成，`vite` 输出 `built in 2.04s`。
- `cd pc-tools/workstation && npm run lint`
  - 结果：通过。
  - 关键输出：`eslint .` 无报错输出。
- `git diff --check -- pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/server/o7DirectUpperApi.ts pc-tools/workstation/src/server/index.ts pc-tools/workstation/src/client/workstationApi.ts pc-tools/workstation/src/components/O7LiveOperatorPanel.vue pc-tools/workstation/test/App.test.ts docs/interfaces/o7_direct_upper_pc_api.md docs/product/pc_tools_workstation.md sprints/2026.06.04_21-22_runtime-material-runtime-hooks/owner_notes/full-stack-software-engineer.md`
  - 结果：通过，无 whitespace error 输出。

## PC direct-upper smoke

- `GET http://192.168.1.11:8787/health`
  - 结果：HTTP `200 OK`。
  - 关键 payload：`schema=trashbot.upper_robot_api.v1.health`，`status=ready`，`safe_to_control=false`，`robot_control_executed=false`。
- `POST http://192.168.1.11:8787/api/radar/scan-proof/refresh`
  - 结果：HTTP `405 Method Not Allowed`，`Allow: OPTIONS`。
  - blocker：`upper_scan_proof_refresh_post_route_not_deployed_or_not_enabled`。
  - 证据边界：这是 expected blocker；本轮没有伪造 scan proof refresh 成功，也不能把 PC proxy/software guard 写成 `robot_runtime_material`。

## 剩余风险

- 需要 Robot Software 并行任务确认 upper `POST /api/radar/scan-proof/refresh` 已部署并返回 fresh/stale/blocker payload。
- 没有现场 8787 refresh 成功材料前，本轮 PC 改动只属于 `software_guard`，不能推动 O3/O7 产品 KR 涨分。
