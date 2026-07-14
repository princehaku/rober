# Tech Done - O7 Live Relay Browser Smoke Artifact

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_15-38_o7_live_relay_browser_smoke_artifact/`
- Implementation owner: `full-stack-software-engineer`
- Completed at: 2026-07-14 15:51:54 CST
- Proof boundary: `software_proof_o7_live_relay_browser_smoke_artifact_only`

## 用户旅程变化和触点收益

现场 owner 现在可以在 PC workstation 包内运行一个可复验 live relay smoke 命令，而不是只看 Vitest/jsdom 或静态 DOM artifact。该命令会启动本机 loopback Express server，并用真实 HTTP socket 读取 `/api/health`、`/api/o7/operator-console`、`/api/o7/cloud-operator-console-probe?baseUrl=<same-live-loopback-server>`，然后保存 sprint artifact。

本轮没有新增 UI panel，也没有把 HTTP smoke 包装成真实浏览器、生产云、送达、路线执行、HIL 或 safe-to-control 证据。

## 实际改动

- `pc-tools/workstation/src/server/o7LiveRelayBrowserSmokeArtifact.ts`
  - 新增 live loopback HTTP smoke artifact helper。
  - 默认监听 `127.0.0.1:17001`，端口占用时顺延并记录 `listen_attempts`。
  - 断言 health/operator console/cloud probe schema、`probe_status=loaded_fail_closed_contract` 和危险 true 字段。
- `pc-tools/workstation/package.json`
  - 新增 `npm run smoke:o7-live-relay-browser`。
- `docs/product/pc_tools_workstation.md`
  - 补充 live relay browser smoke 命令、artifact schema、proof boundary 和 fixed false 字段。
- `sprints/2026.07.14_15-38_o7_live_relay_browser_smoke_artifact/artifacts/o7_live_relay_browser_smoke_artifact.json`
  - 生成 artifact：`schema=trashbot.pc_tools_workstation.o7_live_relay_browser_smoke_artifact.v1`。
- `sprints/2026.07.14_15-38_o7_live_relay_browser_smoke_artifact/tech-done.md`
  - 记录本轮实现、验证、失败/重试和风险。

## 接口影响

- 新增命令入口，不新增 runtime API endpoint。
- 复用现有 endpoints：
  - `GET /api/health`
  - `GET /api/o7/operator-console`
  - `GET /api/o7/cloud-operator-console-probe?baseUrl=<local-loopback-url>`
- Artifact 关键字段：
  - `endpoint_transport=live_loopback_http_socket`
  - `server_started=true`
  - `http_smoke_executed=true`
  - `browser_smoke_status=not_run_http_only_minimum`
  - `operator_console_schema=trashbot.o7.operator_console.v1`
  - `cloud_operator_console_probe_schema=trashbot.pc_tools_workstation.o7_cloud_operator_console_probe.v1`
  - `probe_status=loaded_fail_closed_contract`

## 固定边界

- `delivery_success=false`
- `safe_to_control=false`
- `route_execution_success=false`
- `hil_pass=false`
- `robot_control_executed=false`
- `connects_cloud_production=false`

## 验证结果

### Live HTTP smoke

```bash
cd pc-tools/workstation && npm run smoke:o7-live-relay-browser -- --artifact ../../sprints/2026.07.14_15-38_o7_live_relay_browser_smoke_artifact/artifacts/o7_live_relay_browser_smoke_artifact.json
```

Result:

```text
o7_live_relay_browser_smoke_artifact_ready artifact=/Users/m1/apps/rober/sprints/2026.07.14_15-38_o7_live_relay_browser_smoke_artifact/artifacts/o7_live_relay_browser_smoke_artifact.json endpoint_transport=live_loopback_http_socket server_started=true http_smoke_executed=true browser_smoke_status=not_run_http_only_minimum
```

Artifact observed:

```text
server_base_url=http://127.0.0.1:17001
health_schema=trashbot.pc_tools_workstation.health.v1
operator_console_schema=trashbot.o7.operator_console.v1
cloud_operator_console_probe_schema=trashbot.pc_tools_workstation.o7_cloud_operator_console_probe.v1
probe_status=loaded_fail_closed_contract
```

### JSON validation

```bash
python3 -m json.tool sprints/2026.07.14_15-38_o7_live_relay_browser_smoke_artifact/artifacts/o7_live_relay_browser_smoke_artifact.json
```

Result: exit 0.

### Package gates

```bash
cd pc-tools/workstation && npm run test
```

Result:

```text
Test Files  3 passed (3)
Tests  525 passed (525)
Duration  50.25s
```

```bash
cd pc-tools/workstation && npm run build
```

Result:

```text
tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json
✓ 34 modules transformed.
✓ built in 2.06s
```

Note: Vite emitted the existing large chunk warning for `dist/assets/index-*.js`; build still exited 0.

```bash
cd pc-tools/workstation && npm run lint
```

Result: exit 0.

### Anchor and diff checks

```bash
rg -n "trashbot.pc_tools_workstation.o7_live_relay_browser_smoke_artifact.v1|software_proof_o7_live_relay_browser_smoke_artifact_only|live relay|browser smoke|endpoint_transport=live_loopback_http_socket|server_started=true|http_smoke_executed=true|delivery_success=false|safe_to_control=false|route_execution_success=false|hil_pass=false" pc-tools/workstation docs/product/pc_tools_workstation.md sprints/2026.07.14_15-38_o7_live_relay_browser_smoke_artifact
```

Result: exit 0; required anchors found in artifact, docs, and sprint files.

```bash
git diff --check -- pc-tools/workstation docs/product/pc_tools_workstation.md sprints/2026.07.14_15-38_o7_live_relay_browser_smoke_artifact
```

Result: exit 0.

## 失败定位和重试

No validation failure occurred. No repair rerun was required.

## 剩余风险

- Browser automation was not run: artifact explicitly records `browser_smoke_status=not_run_http_only_minimum` and `browser_runtime=not_configured_in_workstation_package`.
- This is live loopback HTTP software proof only; it does not prove production cloud, public HTTPS/TLS, 4G/SIM, DB/queue, OSS/CDN, true phone/browser production path, route execution, delivery/operator acceptance, HIL, safe-to-control, or robot control side effects.
- O5 remains blocked on success-class production/cloud evidence or explicit same-window live route/HIL/delivery/operator evidence; this sprint should not increase OKR percentage.
