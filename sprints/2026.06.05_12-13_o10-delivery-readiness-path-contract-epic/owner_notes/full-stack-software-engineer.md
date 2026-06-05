# Full-stack Software Engineer Owner Note

## sprint_type

sprint_type: epic

## 本轮范围

- 角色：full-stack-software-engineer
- 任务：检查并补齐 PC workstation 对 O10 map/scan proof latest/path/fail-closed 边界的消费能力。
- 时间：2026-06-05 12:20:38 CST

## 实际改动

- `pc-tools/workstation/src/server/o7DirectUpperApi.ts`：新增只读 `map_proof_latest` command envelope，代理 upper `/api/map/proof/latest`，并在 direct status 摘要中展示 map proof latest status、artifact path、canonical/resolved/configured/compatibility paths、failure reason、blockers 和 `safe_to_control=false`。
- `pc-tools/workstation/src/server/index.ts`：新增 PC 同源 `GET /api/o7/direct-upper/map/proof/latest`。
- `pc-tools/workstation/src/shared/contracts.ts`：补齐 map proof latest command、request path、schema、local API path 和 status summary 字段。
- `pc-tools/workstation/src/components/O7LiveOperatorPanel.vue`：Direct 卡片展示 map proof latest artifact/path/fail-closed/safety false，并把本机 map proof latest path 暴露给 operator/curl。
- `docs/interfaces/o7_direct_upper_pc_api.md`：同步接口契约和前端展示边界。

## 验证结果

```bash
cd pc-tools/workstation && TMPDIR=/tmp npm test -- --run test/App.test.ts
```

结果：

```text
Test Files  1 passed (1)
Tests  30 passed (30)
Duration  18.81s
```

```bash
cd pc-tools/workstation && TMPDIR=/tmp npm run build
```

结果：

```text
tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json
✓ 14 modules transformed.
dist/index.html                  0.41 kB │ gzip:  0.28 kB
dist/assets/index-EBE9rJR4.css  13.79 kB │ gzip:  3.46 kB
dist/assets/index-BrngR4ks.js   95.40 kB │ gzip: 34.71 kB
✓ built in 1.77s
```

```bash
cd pc-tools/workstation && TMPDIR=/tmp PORT=8788 ROBER_UPPER_API_BASE_URL=http://192.168.1.11:8787 npm run api
```

结果：

```text
pc-tools workstation API listening on http://127.0.0.1:8788
```

同轮 curl 后已用 Ctrl-C 停止 8788：

```bash
curl -fsS http://127.0.0.1:8788/api/o7/direct-upper/status
```

关键结果：

```text
status=ready
health_request.ok=true, status_request.ok=true
upper_api_base_url_source=env
map_proof_artifact_status=loaded
map_proof_artifact_path=/root/rober/onboard/runtime/map_lifecycle_latest.json
map_proof_canonical_path=/root/rober/onboard/runtime/map_lifecycle_latest.json
map_proof_resolved_path=/root/rober/onboard/runtime/map_lifecycle_latest.json
map_proof_configured_path=/root/rober/onboard/runtime/map_lifecycle_latest.json
map_proof_compatibility_paths=[/root/rober/runtime/map_lifecycle_latest.json]
map_proof_safe_to_control=false
safe_to_control=false
robot_control_executed=false
```

```bash
curl -fsS http://127.0.0.1:8788/api/o7/direct-upper/radar/scan-proof/latest
```

关键结果：

```text
upper_request.path=/api/radar/scan-proof/latest
upper_request.ok=true
upper_request.http_status=200
latest_proof_status=scan_once_hz_raw_packet_tf_observed
continuous_scan_status=not_proven
blocked_reasons include continuous_scan_status_not_proven and scan_continuity_not_observed
safe_to_control=false
robot_control_executed=false
```

```bash
curl -fsS http://127.0.0.1:8788/api/o7/direct-upper/map/proof/latest
```

关键结果：

```text
upper_request.path=/api/map/proof/latest
upper_request.ok=true
upper_request.http_status=200
artifact_status=loaded
artifact_path=/root/rober/onboard/runtime/map_lifecycle_latest.json
map_proof_canonical_path=/root/rober/onboard/runtime/map_lifecycle_latest.json
map_proof_resolved_path=/root/rober/onboard/runtime/map_lifecycle_latest.json
map_proof_configured_path=/root/rober/onboard/runtime/map_lifecycle_latest.json
map_proof_compatibility_paths=[/root/rober/runtime/map_lifecycle_latest.json]
fail_closed=true
safe_to_control=false
robot_control_executed=false
not_proven includes upper_api_map_proof_not_proven, amcl_not_proven, nav2_consumption, pc_wasd_control, delivery_success
```

## 失败定位

- 第一轮 App 测试失败：旧 direct status mock 缺少新增 `map_proof_compatibility_paths` / `map_proof_blockers` 字段，前端直接访问 `.length` 导致 render error。
- 修复：前端计算属性对缺字段使用空数组默认值，保持旧 API/mock 也 fail-closed 可渲染。
- 第二轮回归失败：曾把 scan proof 既有 `upper_api_scan_not_proven` token 改名，破坏既有测试口径。
- 修复：恢复 scan proof token，只给 map proof latest 使用独立 `upper_api_map_proof_not_proven`。

## 当前边界与风险

- 本轮 PC 侧只做 software guard 和 API readback 展示，不做浏览器点击验收。
- 即使 map proof latest HTTP 200，PC 仍固定 `safe_to_control=false`、`robot_control_executed=false`，且不证明 AMCL/Nav2、PC WASD、HIL 或 delivery success。
- `GET /api/o7/direct-upper/map/proof/latest` 当前能消费 canonical path contract，但 upper payload 的 proof state 仍为 `not_proven`，所以 PC envelope 正确保持 `fail_closed=true`。
- 完成时间：2026-06-05 12:41:07 CST。
