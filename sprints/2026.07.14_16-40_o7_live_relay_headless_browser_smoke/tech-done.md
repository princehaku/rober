# Tech Done - O7 Live Relay Headless Browser Smoke

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_16-40_o7_live_relay_headless_browser_smoke/`
- Owner: `full-stack-software-engineer`
- Proof boundary: `software_proof_o7_live_relay_headless_browser_smoke_only`
- Status: `implemented_support_only_ready_for_product_acceptance`

## 用户旅程变化和触点收益

本轮把上一轮 `browser_smoke_status=not_run_http_only_minimum` 的缺口推进到真实本机 `headless Chrome` browser smoke。现场 owner 现在可以用一个 npm 命令启动 workstation loopback server，并让 Chrome headless 进程实际加载 `/api/health`、`/api/o7/operator-console`、`/api/o7/cloud-operator-console-probe?baseUrl=<same-loopback>`，再把浏览器看到的 JSON schema/status/false-field contract 写入 sprint artifact。

这改善的是 O7/O5 支撑证据的可复验性：它证明本机真实浏览器 runtime 能读 live relay JSON contract，不再只是 Node fetch 或 HTTP-only smoke。它不新增 UI panel，不启用用户动作，不连接 production cloud，也不产生任何机器人控制副作用。

## 实际改动

- `pc-tools/workstation/src/server/o7LiveRelayHeadlessBrowserSmoke.ts`
  - 新增 headless Chrome smoke helper。
  - 默认使用 `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`。
  - 启动 `127.0.0.1:17002` 或下一可用端口的 live loopback Express server。
  - 用 Chrome `--headless=new --dump-dom` 加载三条 endpoint，并从 Chrome DOM `<pre>` 或 raw JSON 中解析 object payload。
  - 校验 endpoint schema/status，扫描危险 true 字段，固定 artifact 顶层 false safety/mission fields。
  - Chrome 缺失或运行失败时 fail closed，不回退 HTTP-only。
- `pc-tools/workstation/test/o7LiveRelayHeadlessBrowserSmoke.test.ts`
  - 覆盖 Chrome JSON DOM wrapper 解析、非 object payload 拒绝、Chrome dump-dom 参数和 CLI 默认值。
- `pc-tools/workstation/package.json`
  - 新增 `smoke:o7-live-relay-headless-browser`。
- `docs/product/pc_tools_workstation.md`
  - 记录 headless Chrome live relay smoke 命令、artifact schema/proof boundary、fail-closed 边界和不证明事项。
- `sprints/2026.07.14_16-40_o7_live_relay_headless_browser_smoke/artifacts/o7_live_relay_headless_browser_smoke.json`
  - 新增本轮 smoke artifact。
- `sprints/2026.07.14_16-40_o7_live_relay_headless_browser_smoke/tech-done.md`
  - 记录实现、验证、失败修复和剩余风险。

## Artifact 结果

Artifact path:

`sprints/2026.07.14_16-40_o7_live_relay_headless_browser_smoke/artifacts/o7_live_relay_headless_browser_smoke.json`

关键锚点：

- `schema=trashbot.pc_tools_workstation.o7_live_relay_headless_browser_smoke.v1`
- `proof_boundary=software_proof_o7_live_relay_headless_browser_smoke_only`
- `artifact_status=headless_browser_smoke_ready_not_delivery_proof`
- `endpoint_transport=live_loopback_http_socket`
- `browser_runtime=headless_chrome`
- `browser_smoke_status=live_headless_chrome_executed`
- `server_started=true`
- `http_smoke_executed=true`
- `headless_browser_smoke_executed=true`
- `delivery_success=false`
- `safe_to_control=false`
- `route_execution_success=false`
- `hil_pass=false`
- `robot_control_executed=false`
- `connects_cloud_production=false`

Chrome-loaded endpoint observations:

- `/api/health`: `schema=trashbot.pc_tools_workstation.health.v1`
- `/api/o7/operator-console`: `schema=trashbot.o7.operator_console.v1`
- `/api/o7/cloud-operator-console-probe?baseUrl=http%3A%2F%2F127.0.0.1%3A17002`: `schema=trashbot.pc_tools_workstation.o7_cloud_operator_console_probe.v1`，`probe_status=loaded_fail_closed_contract`

## 接口影响

- 新增 CLI-only smoke script，不新增产品运行时 API。
- 复用既有 endpoint：
  - `GET /api/health`
  - `GET /api/o7/operator-console`
  - `GET /api/o7/cloud-operator-console-probe?baseUrl=<local-loopback-url>`
- 不修改 O6/O7 adapter 运行时 contract，不修改 UI，不修改 ROS2/hardware/Nav2/robot control 路径。

## 验证结果

1. `cd pc-tools/workstation && npm run smoke:o7-live-relay-headless-browser -- --artifact ../../sprints/2026.07.14_16-40_o7_live_relay_headless_browser_smoke/artifacts/o7_live_relay_headless_browser_smoke.json`
   - Exit 0.
   - Key output: `o7_live_relay_headless_browser_smoke_ready ... endpoint_transport=live_loopback_http_socket browser_runtime=headless_chrome browser_smoke_status=live_headless_chrome_executed server_started=true http_smoke_executed=true headless_browser_smoke_executed=true`
2. `python3 -m json.tool sprints/2026.07.14_16-40_o7_live_relay_headless_browser_smoke/artifacts/o7_live_relay_headless_browser_smoke.json`
   - Exit 0.
   - JSON artifact parsed and formatted successfully.
3. `cd pc-tools/workstation && npm run test`
   - Exit 0 after repair.
   - Key output: `Test Files 4 passed (4)`, `Tests 529 passed (529)`.
4. `cd pc-tools/workstation && npm run build`
   - First run failed on `test/o7LiveRelayHeadlessBrowserSmoke.test.ts` using `Array.prototype.at()` under current app tsconfig.
   - Repaired by replacing `.at(-1)` with `args[args.length - 1]`.
   - Final run exit 0.
   - Vite kept the existing large chunk warning.
5. `cd pc-tools/workstation && npm run lint`
   - Exit 0.
6. `rg -n "trashbot.pc_tools_workstation.o7_live_relay_headless_browser_smoke.v1|software_proof_o7_live_relay_headless_browser_smoke_only|headless Chrome|browser_smoke_status=live_headless_chrome_executed|headless_browser_smoke_executed=true|endpoint_transport=live_loopback_http_socket|server_started=true|http_smoke_executed=true|delivery_success=false|safe_to_control=false|route_execution_success=false|hil_pass=false" pc-tools/workstation docs/product/pc_tools_workstation.md sprints/2026.07.14_16-40_o7_live_relay_headless_browser_smoke`
   - Exit 0.
   - Required anchors found in code/docs/current sprint artifact/docs.
7. `git diff --check -- pc-tools/workstation docs/product/pc_tools_workstation.md sprints/2026.07.14_16-40_o7_live_relay_headless_browser_smoke`
   - Exit 0.
   - No whitespace errors.

## 失败定位与修复

- Build first failure:
  - Root cause:新增测试使用 `args.at(-1)`，当前 build path 的 TypeScript lib 设置未暴露该 API。
  - Fix:改为 `args[args.length - 1]`。
  - Re-validation:`npm run build`、`npm run test`、`npm run lint` 均通过。

## 剩余风险和边界

- 本轮只证明本机 headless Chrome 能加载 live loopback workstation JSON contract，证明边界为 `software_proof_o7_live_relay_headless_browser_smoke_only`。
- 不证明 production cloud、public HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN、真实手机/browser production proof、delivery、operator acceptance、route execution、HIL、safe-to-control 或 robot control。
- Chrome path 当前依赖本机 `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`，脚本支持 `--chrome <path>` 或 `CHROME_PATH` 覆盖；其他机器缺 Chrome 时会 fail closed。
- 当前 worktree 已有多项早前 workstation 改动和 untracked 文件，本轮未清理、未回滚、未触碰硬件/Nav2/robot control 文件。
