# Sprint 2026.05.19_14-15 Mobile PWA Fresh Browser Proof - PRD

## sprint_type: epic

Run time: 2026-05-19 14:45 Asia/Shanghai。

## 1. 用户价值和产品北极星

普通用户最终只应该打开手机入口并看到当前任务状态、阻塞原因和安全动作，不应该被旧 service-worker cache、旧 console log 或旧 app shell 误导。本轮 PRD 将 `mobile_pwa_fresh_browser_proof` 定义为 Objective 4 的本地 browser acceptance 护栏：用可清空日志、可复现截图、可机器读取 summary 的 fresh Chromium profile 证明当前 `mobile/web` shell 在本地 Docker-only 环境下可被干净渲染。

产品北极星不变：手机端是普通用户入口，控制动作必须 fail-closed，证据必须可解释。本轮不做真实手机通过声明，不做 Objective 5 external proof，不做 Objective 1 HIL，不改变 robot command gating，不声称 PR #4 field pass 或 PR #5 real materials。

## 2. 问题背景

上一轮 `2026.05.19_13-14_mobile-pwa-cache-recovery` 已修复 PWA service-worker/cache recovery，但 closeout 仍留下一个具体风险：in-app browser dev log API 保留恢复前旧 cached app.js console error，Chrome headless fresh profile attempt 卡住，下一步需要可清空日志的 fresh browser context 或真实设备浏览器复核。

如果不解决该问题，Objective 4 的本地 browser proof 会继续混入旧日志噪声，无法区分“当前 shell 真的有 runtime error”与“历史 cached shell 留下的 console error”。这会直接影响后续真实手机/browser 验收前的预检质量。

## 3. OKR 映射

| Objective | 当前证据 | 本轮策略 |
| --- | --- | --- |
| Objective 5 | `OKR.md` 4.1 约 68%，最低；但没有真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/cutover。 | O5 stop rule 继续成立；不推进 O5 completion。 |
| Objective 1 | `OKR.md` 4.1 约 81%；没有 WAVE ROVER/UART/HIL，也没有 PR #5 2D LiDAR / ToF real materials。 | 不推进 O1 completion；不重复包装 10-11 sprint 的 `hardware_real_material_escalation_request` blocker。 |
| Objective 4 | 约 99%，但上一轮仍缺 clean fresh browser proof、真实手机/browser、production app、真实 PWA prompt/user choice。 | 推进 `mobile_pwa_fresh_browser_proof`，作为真实手机/browser 验收前的本地软件护栏。 |
| Objective 2/3 | 约 99%，PR #4 仍缺真实 route/elevator field pass。 | 不推进 field pass；只要求 Robot 静态确认本轮不扩大控制面。 |

## 4. KR 拆解或更新

- Objective 4 KR7 增加本轮软件护栏：本地 `mobile/web` PWA browser proof 必须能在独立 fresh Chromium profile 中验证当前 shell、service-worker/cache recovery marker、console/runtime error 为 0、主操作 fail-closed 和截图/JSON summary。
- Objective 4 KR5 增加验收可解释性：fresh browser proof 失败时必须输出 failure reason，而不是只留下卡住的 headless 进程或不可复核截图。
- Objective 5 KR 不更新：本轮没有 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实 external proof。
- Objective 1 KR 不更新：本轮没有 WAVE ROVER/UART/HIL、真实串口日志、PR #5 2D LiDAR / ToF real materials。
- Objective 2/3 KR 不更新：本轮没有 PR #4 route/elevator field pass、真实 Nav2/fixed-route、dropoff/cancel completion 或 delivery success。

## 5. 本轮核心抓手

`mobile_pwa_fresh_browser_proof` 的产品定义：

1. 基于 `pc-tools/evidence/phone_browser_acceptance_gate.py` 升级或扩展现有 browser acceptance gate。
2. 每次运行使用独立 fresh Chromium profile，避免复用 in-app browser 历史日志或旧 cache。
3. 对 `mobile/web` 当前 shell 执行两类 viewport 证明，至少覆盖 390x844 和 768x900。
4. 验证 service-worker/cache recovery marker；动态控制面必须 no-store/bypass cache。
5. 采集 console/runtime error 并要求为 0；否则 gate failed。
6. 产出 JSON、screenshot、summary，summary 必须写明 `software_proof_docker_mobile_pwa_fresh_browser_proof_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## 6. 需要做什么

Full-Stack 必须：

- 在 `pc-tools/evidence/phone_browser_acceptance_gate.py` 中实现 fresh browser profile 运行路径，或在不破坏兼容性的前提下新增 `mobile_pwa_fresh_browser_proof` mode。
- 确保 gate 能启动本地 `mobile/web` static server、连接 fresh Chromium/CDP、打开当前 shell、等待 app marker、捕获 console/runtime error、截图并写 summary。
- 补充最小 fixture/static tests，覆盖 summary schema、console-zero、service-worker/cache recovery marker、Start/Confirm/Cancel fail-closed 和 dynamic control cache bypass。
- 更新 `docs/product/mobile_user_flow.md`，说明 fresh browser proof 的入口、产物和证据边界。

Robot 必须：

- 只读/静态审查 Full-Stack diff，确认 service-worker 与 browser gate 不新增 robot command path、ACK 发送、diagnostics fetch 副作用或 `/cmd_vel` 控制面。
- 明确 `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` 是否仍成立。

Product 必须：

- 在实现完成后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。
- 保持 OKR 文案保守：本轮可记录 Objective 4 local fresh browser proof software-proof，但不得提高 O5/O1/O2/O3 completion。

## 7. 优先级和验收口径

P0：

- Fresh profile browser proof 能稳定运行，输出 JSON/screenshot/summary。
- Console/runtime error 为 0；若不为 0，summary 必须列出错误文本的安全摘要和失败状态。
- Start Delivery、Confirm Dropoff、Cancel fail-closed；`primary_actions_enabled=false`、`safe_to_control=false`。
- Dynamic control paths no-store/bypass cache：`/api/*`、`/robots/*`、commands、ACK、diagnostics、non-GET 不被 service-worker 缓存、排队或重放。

P1：

- Summary 同时包含 viewport、service-worker/cache recovery marker、evidence boundary、not_proven 列表和 artifact paths。
- `docs/product/mobile_user_flow.md` 说明该 gate 与旧 browser acceptance gate 的关系。
- Robot review 和 Product closeout 留档完整。

## 8. 风险、阻塞和需要补齐的证据链

- Fresh Chromium 仍可能在本机卡住；实现时必须有超时、进程清理和 failure summary。
- 本轮仍缺真实手机、真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice、真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、WAVE ROVER/UART/HIL、PR #4 route/elevator field pass、PR #5 2D LiDAR / ToF real materials、dropoff/cancel completion 和 delivery success。
- 本轮所有产物必须保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## 9. 需要创建或更新的 sprint 文档

当前创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实现和收口后必须继续更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
