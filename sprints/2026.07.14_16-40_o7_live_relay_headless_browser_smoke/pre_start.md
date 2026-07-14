# Pre Start - O7 Live Relay Headless Browser Smoke

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_16-40_o7_live_relay_headless_browser_smoke/`
- Start time: 2026-07-14 16:40 CST
- Product owner: `product-okr-owner`
- Implementation owner: `full-stack-software-engineer`
- Owner model: default single owner closeout, no parallel agents.
- Product status: `planned`
- Proof boundary: `software_proof_o7_live_relay_headless_browser_smoke_only`

## 用户价值和产品北极星

北极星仍是让普通手机/PC 用户可以可验证地发起、观察和复验垃圾投递任务。上一轮 `sprints/2026.07.14_15-38_o7_live_relay_browser_smoke_artifact/` 已证明 live loopback HTTP socket 可以读取 O7 operator console contract，但 `browser_smoke_status=not_run_http_only_minimum`，真实浏览器自动化没有运行。

本轮用户价值不是再生成一个 HTTP-only smoke，而是给现场 owner 一个更贴近真实用户触点的复验材料：启动 workstation live loopback server，用本机真实 `headless Chrome` 进程加载 `/api/health`、`/api/o7/operator-console`、`/api/o7/cloud-operator-console-probe?baseUrl=<same-loopback>`，解析 schema 和固定 false fields，并写入 artifact。它证明本机真实浏览器进程能加载 live relay JSON contract，但不证明 production cloud、真实手机、4G/SIM、delivery、HIL 或 safe-to-control。

## OKR 映射和方向判断

- 当前最低 Objective 是 Objective 5，O5 当前约 85%。O1 约 94%，O6/O7 约 93%。
- O5 仍缺 success-class production evidence：本机环境没有可见 O5 production/cloud、OSS/CDN、4G/SIM、tunnel 凭据入口。
- 本轮方向判断：`调整`。继续针对 O5 browser evidence 缺口，但通过 O7 supporting `headless Chrome` live relay smoke 前进，避免重复上一轮 HTTP-only smoke。
- 计分判断：默认不提升 OKR 百分比，不归档 KR。只有 success-class O5 production/cloud evidence，或同窗口 live route execution + terminal result + operator/dropoff + HIL/safe-to-control evidence 出现时，才重新评估。

## KR 拆解、更新或历史归档

- 当前 KR 不归档：O5 production/cloud success evidence 仍缺；O7 headless browser smoke 仍是本机 support-only 证据。
- 本轮 KR 拆解只新增一个 supporting evidence 抓手：把上一轮 `not_run_http_only_minimum` 缺口推进到真实 `headless Chrome` 进程加载 live relay JSON contract。
- 已完成 KR 历史记录不移动。上一轮 live HTTP socket smoke 的证据来源保留在 `sprints/2026.07.14_15-38_o7_live_relay_browser_smoke_artifact/final.md`；剩余风险正是本轮要处理的 browser automation gap。

## 本轮核心抓手

核心抓手是 `headless Chrome` + `live relay` 的可复验 artifact，而不是新增 UI panel、status/readback wrapper、CLI export 或 HTTP-only smoke。

最低可接受实现：

1. 启动 `pc-tools/workstation` 本机 live loopback server。
2. 用本机真实 Chrome headless 进程访问：
   - `/api/health`
   - `/api/o7/operator-console`
   - `/api/o7/cloud-operator-console-probe?baseUrl=<same-loopback>`
3. 解析每个页面/response 的 JSON contract、schema、status 和固定 false fields。
4. 写入 sprint artifact，证明 `browser_smoke_status=live_headless_chrome_executed`，并固定 `delivery_success=false`、`safe_to_control=false`、`route_execution_success=false`、`hil_pass=false`。

## 需要做什么

- 由 `full-stack-software-engineer` 单线闭环实现、验证、修复和 `tech-done.md` 留档。
- 复用现有 workstation server 和 endpoints；不引入公网云、生产凭据、4G/SIM、OSS/CDN 或机器人控制链路。
- Artifact 建议路径：`sprints/2026.07.14_16-40_o7_live_relay_headless_browser_smoke/artifacts/o7_live_relay_headless_browser_smoke.json`。
- 实现后同步更新当前 sprint `tech-done.md`；如果改变 workstation 使用方式，再同步更新 `docs/product/pc_tools_workstation.md`。

## 优先级和验收口径

- Priority: P0 for the next non-repeating O5/O7 supporting browser evidence gap.
- Acceptance: 必须使用真实 `headless Chrome` 进程访问 live loopback server，不接受仅 `curl`、unit test、jsdom、fixture 或 snapshot。
- Acceptance: artifact 必须包含 `proof_boundary=software_proof_o7_live_relay_headless_browser_smoke_only`。
- Acceptance: artifact 必须包含 `browser_smoke_status=live_headless_chrome_executed`，并记录被加载的三个 endpoint。
- Acceptance: artifact 必须固定 `delivery_success=false`、`safe_to_control=false`、`route_execution_success=false`、`hil_pass=false`。
- Rejection: `browser_smoke_status=not_run_http_only_minimum` 只能作为上一轮缺口说明，不能作为本轮完成证据。

## 对应责任 Engineer

- Primary: `full-stack-software-engineer`
- Consultation only: none by default.
- No Hardware/Algorithm/Robot owner in this sprint, because no `/cmd_vel`、`/api/base/manual`、NavigateToPose、WAVE ROVER UART、Nav2、route execution、HIL、map、scan、TF 或 camera path is in scope.

## 风险、阻塞和需要补齐的证据链

- O5 production/cloud success evidence 仍不可见；本轮只能是 `software_proof_o7_live_relay_headless_browser_smoke_only`。
- 本机 headless Chrome 能证明真实浏览器进程加载 live relay JSON contract，但不证明真实手机、public HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN 或 tunnel。
- 本轮不允许把 live browser smoke 宣称为 delivery、route execution、HIL、safe-to-control 或 robot control proof。
- 剩余计分证据链仍是 success-class O5 production/cloud evidence，或 same-window live route execution + terminal result + operator/dropoff + HIL/safe-to-control。

Fixed false fields:

- `delivery_success=false`
- `safe_to_control=false`
- `route_execution_success=false`
- `hil_pass=false`
- `robot_control_executed=false`
- `connects_cloud_production=false`

## 需要创建或更新的 sprint 文档

- Planning now: `pre_start.md`, `prd.md`, `tech-plan.md`.
- Implementation later: `tech-done.md`.
- Acceptance later: `side2side_check.md`, `final.md`.
