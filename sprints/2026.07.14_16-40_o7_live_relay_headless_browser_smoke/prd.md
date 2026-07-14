# PRD - O7 Live Relay Headless Browser Smoke

## 背景和问题

O5 当前约 85%，是当前最低 Objective，但本机环境没有可见 O5 production/cloud、OSS/CDN、4G/SIM、tunnel 凭据入口，不能产出 success-class production evidence。最近 sprint `sprints/2026.07.14_15-38_o7_live_relay_browser_smoke_artifact/` 已完成 live loopback HTTP socket smoke，证明 workstation live server 可以通过真实 HTTP 读取 `/api/health`、`/api/o7/operator-console`、`/api/o7/cloud-operator-console-probe?baseUrl=<same-loopback>`。

上一轮剩余风险是 `browser_smoke_status=not_run_http_only_minimum`，也就是没有真实浏览器自动化。本轮不重复 HTTP-only smoke，产品目标是把证据推进到本机真实 `headless Chrome` 进程加载同一 live relay JSON contract，并保存可复验 artifact。

## 用户价值和产品北极星

现场 owner 或普通操作者不应该依赖测试 fixture、jsdom 或 curl 日志判断 PC/O7 operator console 是否可被真实浏览器运行时加载。TA 需要一个明确的 headless browser artifact：真实浏览器进程、真实 loopback server、明确 endpoint、明确 schema、明确 fixed false fields。

产品北极星仍是普通用户通过手机/PC 入口可验证地完成垃圾投递闭环。本轮只推进用户触点侧的本机浏览器复验性，不把它包装成 production cloud、真实手机、送达、HIL 或机器人控制完成。

## OKR 映射和方向判断

- Objective 5: O5 当前约 85%，最低。生产云、4G/SIM、production DB/queue、OSS/CDN success-class evidence 当前不可用。
- Objective 7 / O7: 当前约 93%。本轮消费 O7 PC workstation live relay + headless Chrome 证据，支持后续 O5/O7 现场复验。
- Direction: `调整`。不重复 O5 support-only wrapper，也不重复上一轮 HTTP-only smoke；转向真实 headless browser runtime。
- Scoring: 默认不提升 OKR 百分比，不归档 KR。除非出现 success-class production/cloud evidence 或 same-window live route/HIL/delivery/operator evidence，否则保持 support-only。

## 产品需求

### 必须实现

1. 启动本机 `pc-tools/workstation` live loopback server，记录 host、port、启动方式和退出清理结果。
2. 用真实 `headless Chrome` 进程加载至少三个 live endpoint：
   - `GET /api/health`
   - `GET /api/o7/operator-console`
   - `GET /api/o7/cloud-operator-console-probe?baseUrl=<same-live-loopback-server>`
3. 从浏览器加载结果中解析 JSON contract，并记录 endpoint status、schema、probe status 和安全 false fields。
4. 生成 sprint artifact：
   - `schema=trashbot.pc_tools_workstation.o7_live_relay_headless_browser_smoke.v1`
   - `proof_boundary=software_proof_o7_live_relay_headless_browser_smoke_only`
   - `artifact_status=headless_browser_smoke_ready_not_delivery_proof`
   - `endpoint_transport=live_loopback_http_socket`
   - `browser_runtime=headless_chrome`
   - `browser_smoke_status=live_headless_chrome_executed`
   - `server_started=true`
   - `http_smoke_executed=true`
   - `headless_browser_smoke_executed=true`
5. Artifact 必须保留 fixed false fields：
   - `delivery_success=false`
   - `safe_to_control=false`
   - `route_execution_success=false`
   - `hil_pass=false`
   - `robot_control_executed=false`
   - `connects_cloud_production=false`

### 可以实现

- 如果现有依赖已包含 Playwright、Chrome launcher 或等效工具，可以复用；否则可用本机 Chrome/Chromium headless 命令行加载 JSON endpoint，再由脚本读取输出或临时文件。
- 可以在 artifact 中保留上一轮 HTTP smoke 对照字段，但本轮验收必须有 headless browser executed 字段。

### 明确不做

- 不新增 UI panel。
- 不做静态 jsdom-only DOM artifact。
- 不重复 HTTP-only smoke；`browser_smoke_status=not_run_http_only_minimum` 是上一轮缺口，不是本轮可接受完成状态。
- 不连接公网云、production DB/queue、OSS/CDN、4G/SIM 或 tunnel。
- 不发送 `/cmd_vel`、`/api/base/manual`、NavigateToPose、WAVE ROVER UART 或任何机器人控制命令。

## 验收口径

本轮验收必须看到 headless Chrome live relay smoke artifact。最低可接受证据：

```text
schema=trashbot.pc_tools_workstation.o7_live_relay_headless_browser_smoke.v1
proof_boundary=software_proof_o7_live_relay_headless_browser_smoke_only
endpoint_transport=live_loopback_http_socket
browser_runtime=headless_chrome
browser_smoke_status=live_headless_chrome_executed
server_started=true
http_smoke_executed=true
headless_browser_smoke_executed=true
operator_console_schema=trashbot.o7.operator_console.v1
cloud_operator_console_probe_schema=trashbot.pc_tools_workstation.o7_cloud_operator_console_probe.v1
probe_status=loaded_fail_closed_contract
delivery_success=false
safe_to_control=false
route_execution_success=false
hil_pass=false
```

Rejected evidence:

- `browser_smoke_status=not_run_http_only_minimum`
- `endpoint_transport=vitest_fetch_stub_no_socket`
- jsdom-only artifact
- curl-only or HTTP-only artifact
- snapshot-only UI text
- server not started
- only unit tests without live browser process
- any artifact claiming delivery success, route execution success, HIL pass, safe-to-control, production cloud connected, or robot command side effect

## 对应责任 Engineer

- Primary: `full-stack-software-engineer`
- Default execution: single owner closeout, no parallel.
- No Hardware/Algorithm/Robot owner in this sprint, because no `/cmd_vel`、UART、HIL、Nav2、route execution、map、scan、TF、camera or physical robot path is in scope.

## 风险和剩余证据链

- This is still `software_proof`; it does not close O5 production/cloud success.
- Headless Chrome on loopback proves browser-runtime loading of JSON contracts, not real phone browser, public HTTPS/TLS, 4G/SIM, production DB/queue, OSS/CDN, tunnel, delivery, route execution, HIL or safe-to-control.
- If Chrome is unavailable, implementation should fail closed and record the blocker in `tech-done.md`; it should not downgrade completion to HTTP-only and claim success.
- Future countable evidence still needs one of: success-class O5 production/cloud evidence, same-window live route execution result, same-task delivery/operator acceptance, current live HIL pass, or safe-to-control evidence.

## 已完成 KR 历史记录位置

No KR moves to history in this planning step. Relevant support-only records remain in:

- `sprints/2026.07.14_15-38_o7_live_relay_browser_smoke_artifact/final.md`
- `OKR.md` current O5/O7 notes for the 2026-07-14 15:38 closeout

The remaining risk from those records is explicit: live HTTP socket smoke was accepted, but browser automation was not run.

## 需要创建或更新的 sprint 文档

- This planning step creates `pre_start.md`, `prd.md`, and `tech-plan.md`.
- Implementation must create `tech-done.md`.
- Product acceptance must create `side2side_check.md` and `final.md`.
