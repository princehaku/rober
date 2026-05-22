# Mobile Current Panel Browser Proof Refresh PRD

Run time: 2026-05-22 17:18 Asia/Shanghai

## Product Goal

刷新当前 `mobile/web` 手机入口的本地 fresh Chromium-family proof，确认最近多轮 current panels 仍能在当前 shell 中可见、无 console error、无明显遮挡溢出，并且在 blocked/not_proven fixture state 下不启用 Start Delivery、Confirm Dropoff 或 Cancel。

Capability: `mobile_current_panel_browser_proof_refresh`

Evidence boundary: `software_proof_docker_mobile_current_panel_browser_proof_refresh_gate`

## 用户价值和产品北极星

用户价值：当机器人处在材料缺失、ACK pending、terminal result pending、cloud readiness blocked 或 reviewer ACK 等状态时，普通手机用户能看懂“现在不能发车 / 不能确认投放 / 不能取消完成”的原因，并知道该等待还是联系支持。

产品北极星：手机端是普通用户唯一入口；它必须清楚、保守、fail-closed，并且不要求用户理解 ROS2、raw JSON、串口、云队列或硬件材料细节。

## OKR 映射

- Objective 4: 本轮直接服务 Objective 4，刷新当前手机入口的 browser proof 和当前 panels 可见性证据。
- Objective 5: 不直接推进。Objective 5 仍约 68% 且最低，但缺真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser 或 verified terminal result；本地 browser proof 不算 O5 external proof。
- Objective 1: 不推进。Objective 1 仍约 81%，缺真实 WAVE ROVER/UART/HIL 和 PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution。
- Objective 2 / Objective 3: 不推进真实现场闭环；本轮不证明 route/elevator field pass、Nav2/fixed-route runtime、dropoff/cancel completion、terminal result 或 delivery success。

## KR 拆解或更新

- Objective 4 KR7: 后续执行需要证明当前手机端 UI 在本地 fresh browser profile 下可打开、关键状态可见、主操作保持 disabled。
- Objective 4 KR4: 支持/诊断最小数据包的手机可见性需要通过 current panels refresh 复核，但只限 phone-safe summary。
- Objective 5 KR1 / KR6: 本轮只消费云/ACK/terminal-result状态的 phone-safe blocked copy，不证明 HTTPS、4G、OSS/CDN、DB/queue 或 production degradation。
- 本轮不更新 `OKR.md` 进度，不提高任何 Objective 百分比。

## 本轮核心抓手

刷新 current panel browser proof，而不是增加新业务能力：

- 使用 isolated/fresh Chromium-family profile 避免旧 cache 或旧 service-worker 污染结果。
- 覆盖当前 `mobile/web` 首屏、恢复/支持/ACK/material panels 和最新 reviewer ACK panel。
- 严格要求 console-zero；一旦发现 runtime error，由 `full-stack-software-engineer` 只修 scoped current-panel 问题并复跑。
- 证明 blocked state 下 `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- 输出材料必须写明 `not true phone/browser`，不得写成真实手机、真实浏览器外部验收、O5 external proof 或 delivery success。

## 需要做什么

1. 后续 `full-stack-software-engineer` 执行 `pc-tools/evidence/phone_browser_acceptance_gate.py` 的 fresh profile browser proof refresh，并把 output-dir 指向本 sprint evidence 目录。
2. 如果 gate 暴露 current panels 缺失、DOM id 漂移、console error、service-worker cache 误用、布局遮挡或主操作误启用，只在允许文件范围内修复。
3. 后续 `robot-software-engineer` 做只读接口事实核对：current panels 使用的 diagnostics summary 仍是 safe alias / phone-safe metadata，不包含 raw ROS topics、`/cmd_vel`、串口、凭证、traceback 或完整 artifact。
4. 后续 Product closeout 用 `tech-done.md`、`side2side_check.md`、`final.md` 记录证据边界；本轮预设 no OKR percentage lift。

## 优先级和验收口径

Priority: P0 for O4 software-proof refresh after repeated O5 external-material blocker.

Acceptance criteria for execution:

- Browser proof summary exists under sprint evidence directory and reports `ok=true` for both phone and tablet-ish viewports, if browser runtime is available.
- Required proof text includes `mobile_current_panel_browser_proof_refresh` and `software_proof_docker_mobile_current_panel_browser_proof_refresh_gate`.
- Current panels status passes; latest material-resolution / reviewer ACK / terminal result / support / cloud readiness panels remain visible through phone-safe fields.
- `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` remain visible or machine-checkable.
- Console-zero passes; no runtime exception is accepted as a successful proof.
- Closeout states: not true phone/browser, not O5 external proof, not HIL, not route/elevator field pass, not delivery success.

## 对应责任 Engineer

- Primary owner: `full-stack-software-engineer`
- Read-only support: `robot-software-engineer`
- Product closeout: `product-okr-owner`

## Non Goals

- 不改 `OKR.md`。
- 不新增本地 O5 wrapper。
- 不声明真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/cutover。
- 不声明真实 iPhone/Android、production app、真实 PWA prompt/userChoice 或 true phone/browser proof。
- 不声明 PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved。
- 不声明真实 WAVE ROVER/UART/HIL、route/elevator field pass、dropoff/cancel completion、verified terminal result 或 delivery success。

## 风险、阻塞和需要补齐的证据链

- 如果本地 browser runtime 不可用，后续执行只能收口为 blocked validation gap，不能替代为 unit test pass。
- 如果 fresh profile 暴露 stale shell 或 service-worker 问题，必须先修复并复跑，不得把失败作为可接受证明。
- 真实 OKR 提升仍依赖外部材料：O5 需要真实云/4G/OSS/CDN/DB/queue/phone proof；O1 需要真实硬件/HIL 和 PR resolution；O4 需要真实设备或 production app evidence。

## 需要创建或更新的 sprint 文档

- 本任务创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 后续执行创建/更新：`tech-done.md`、`side2side_check.md`、`final.md`。
