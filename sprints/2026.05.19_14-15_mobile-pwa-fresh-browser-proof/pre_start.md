# Sprint 2026.05.19_14-15 Mobile PWA Fresh Browser Proof - Pre Start

## sprint_type: epic

Run time: 2026-05-19 14:45 Asia/Shanghai。

## 1. 用户价值和产品北极星

产品北极星仍是让普通手机用户可以用手机完成低成本 ROS2 垃圾投递任务，并在失败时看懂机器人状态、证据边界和下一步动作。本轮不新增真实手机、真实公网、真实电梯或真实机器人运动证据，而是把上一轮遗留的本地 Browser QA 噪声收敛成可重复、可清空上下文的 fresh browser proof。

用户价值是让后续 Objective 4 手机触点验收能在独立 Chromium profile 中看到当前 `mobile/web` shell、service-worker/cache recovery marker、动态控制面 no-store/bypass cache 和 console/runtime error 为 0，而不是继续被 in-app browser 旧日志或旧 cached app.js 误导。

## 2. 背景证据

- `OKR.md` 4.1 显示 Objective 5 当前约 68%，是最低完成度；但本机 Docker-only，没有真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/cutover，因此 O5 stop rule 继续成立，本轮不推进 O5 completion。
- `OKR.md` 4.1 显示 Objective 1 当前约 81%；但本机没有 WAVE ROVER/UART/HIL，也没有 PR #5 真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry materials。10-11 sprint 已做 `hardware_real_material_escalation_request`，本轮不得重复包装同一 blocker。
- PR #5 unresolved review threads 仍指出默认硬件清单、传感器基线和 vendor 来源缺口；该缺口继续作为 Objective 1 / PR #5 real-material blocker 保留，本轮不声称解决真实硬件材料。
- PR #4 要求 elevator-assisted delivery 必须进入主线；最近几轮已做 action feedback、task terminal、field material intake 等软件证明，但仍缺真实 route/elevator field pass。
- 最新 sprint `2026.05.19_13-14_mobile-pwa-cache-recovery` 的 concrete risk 是：in-app browser dev log API 保留旧 cached app.js console error，Chrome headless fresh profile attempt 卡住，下一步需要可清空日志的 fresh browser context 或真实设备浏览器复核。

## 3. 本轮核心抓手

本轮选择 Objective 4 的 Docker-only 可执行功能方向：升级 `pc-tools/evidence/phone_browser_acceptance_gate.py` 为 `mobile_pwa_fresh_browser_proof` gate。

核心能力要求：

1. 在独立 fresh Chromium profile 中启动并验证当前 `mobile/web` shell。
2. 验证 service-worker/cache recovery marker 可见，旧 `rober-mobile-shell-*` cache 不污染当前证明。
3. 验证 console/runtime error 为 0，并把异常写入 JSON summary。
4. 验证 Start Delivery、Confirm Dropoff、Cancel 继续 fail-closed。
5. 验证动态控制面 no-store/bypass cache，覆盖 `/api/*`、`/robots/*`、commands、ACK、diagnostics 和 non-GET。
6. 产出 JSON、screenshot 和 summary artifact，便于 Product closeout 与后续真实设备复核。

## 4. OKR 映射和 KR 拆解

| Objective | 本轮判断 | KR 拆解或更新 |
| --- | --- | --- |
| Objective 5 | 约 68%，最低但被真实外部材料阻塞。 | 不更新 KR，不提高完成度；继续要求真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 external proof。 |
| Objective 1 | 约 81%，但被 WAVE ROVER/UART/HIL 与 PR #5 real materials 阻塞。 | 不更新 KR，不提高完成度；PR #5 默认硬件清单、传感器基线、vendor 来源缺口继续保留。 |
| Objective 4 | 约 99%，仍缺真实手机/browser、production app、真实 PWA prompt/user choice。 | 新增软件护栏：本地 `mobile/web` browser proof 必须使用 fresh Chromium profile、console-zero、截图和 JSON summary；只记录 `software_proof_docker_mobile_pwa_fresh_browser_proof_gate`。 |
| Objective 2/3 | 约 99%，仍缺 PR #4 route/elevator field pass。 | 不更新 KR，不提高完成度；Robot 只读验收只确认本轮不扩大 robot command path、ACK、diagnostics fetch 或 `/cmd_vel` 控制面。 |

## 5. 责任 Engineer 和分工

- `full-stack-software-engineer`：实现 fresh browser proof gate、必要 fixture/static tests、`docs/product` 更新；主责产出 JSON/screenshot/summary。
- `robot-software-engineer`：只读/静态验收，确认 gate 和 service-worker 不扩大 robot command path、ACK、diagnostics fetch 或 `/cmd_vel` 控制面。
- `product-okr-owner`：收口更新 sprint docs、`OKR.md`、`docs/process/okr_progress_log.md`，并保持证据边界不被写成真实手机或真实送达。

## 6. 优先级和验收口径

P0 验收：

- `mobile_pwa_fresh_browser_proof` 在 fresh Chromium profile 中运行，输出 JSON、screenshot、summary。
- summary 明确 `evidence_boundary=software_proof_docker_mobile_pwa_fresh_browser_proof_gate`。
- console/runtime error 计数为 0；如果 Chromium 启动失败，必须 fail closed 并记录失败原因。
- Start Delivery、Confirm Dropoff、Cancel 保持 disabled；`primary_actions_enabled=false`、`safe_to_control=false`。
- 动态控制面保持 no-store/bypass cache，不缓存或重放 `/api/*`、`/robots/*`、commands、ACK、diagnostics 和 non-GET。

P1 验收：

- fixture/static tests 覆盖 fresh profile 参数、summary schema、console-zero、service-worker/cache marker、动态控制面 cache bypass。
- `docs/product/mobile_user_flow.md` 补充 fresh browser proof gate 的使用方式和边界。
- Product closeout 更新 `OKR.md` 和 `docs/process/okr_progress_log.md`，不提高 O5/O1/O2/O3 完成度。

## 7. 风险、阻塞和证据链

- Chrome/Chromium 在本机 headless fresh profile 仍可能卡住；若发生，Full-Stack 必须定位进程、端口、profile 和 CDP 连接失败点，不得把第一轮卡住直接作为完成。
- 即使 fresh browser proof 通过，也只证明 Docker/local 当前 PWA software proof，不证明真实 iPhone/Android、production app、真实 PWA prompt/user choice、O5 external proof、O1 HIL、PR #4 route/elevator field pass、PR #5 real materials 或 delivery success。
- 本轮证据边界必须保持：`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## 8. 需要创建或更新的 sprint 文档

本轮先创建：

- `sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof/pre_start.md`
- `sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof/prd.md`
- `sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof/tech-plan.md`

后续实现与收口必须继续补齐：

- `sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof/tech-done.md`
- `sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof/side2side_check.md`
- `sprints/2026.05.19_14-15_mobile-pwa-fresh-browser-proof/final.md`
