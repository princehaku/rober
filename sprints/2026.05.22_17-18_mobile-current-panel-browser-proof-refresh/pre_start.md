# Mobile Current Panel Browser Proof Refresh Pre Start

Run time: 2026-05-22 17:18 Asia/Shanghai

## Sprint Type

- `sprint_type: epic`
- Sprint folder: `sprints/2026.05.22_17-18_mobile-current-panel-browser-proof-refresh/`
- Capability: `mobile_current_panel_browser_proof_refresh`
- Target proof boundary: `software_proof_docker_mobile_current_panel_browser_proof_refresh_gate`
- Planning status: Product planning only. No product code, tests, `OKR.md`, or non-sprint docs are changed in this planning task.

## 用户价值和产品北极星

普通用户只应该从手机入口看到当前任务状态、阻塞原因、恢复建议和支持入口，不应该因为本地 stale shell、旧 service-worker cache、console runtime error 或只读 panel 缺失而误以为可以发车。

产品北极星不变：让不会 SSH、ROS2、串口或硬件调试的用户，通过手机理解机器人是否安全可控、下一步该等候还是联系支持。本轮是对当前 `mobile/web` 首屏和最新 panel 的本地 fresh Chromium 证据刷新，不是现场验收。

## 背景证据

- `OKR.md` 4.1 显示 Objective 5 约 68%，仍是完成度最低 Objective；但它缺真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser 或 verified terminal result 外部材料。
- Objective 1 约 81%，仍缺真实 WAVE ROVER/UART/HIL、2D LiDAR/ToF material、operator HIL report 和 PR #5 thread `PRRT_kwDOSWB9286CJ3tX` reviewer resolution。
- Objective 2、Objective 3、Objective 4 约 99%，但仍缺真实 route/elevator field pass、真实 Nav2/fixed-route runtime、真实手机/browser、dropoff/cancel completion、verified terminal result 和 delivery success。
- 最新 sprint `sprints/2026.05.22_16-17_field-evidence-material-resolution-reviewer-ack-intake/final.md` 明确：不要在无真实外部材料时继续堆本地 Objective 5 wrapper。
- 近期 `mobile/web` 已多轮加入 material-resolution、owner response、reviewer ACK、support handoff、terminal result、cloud readiness 和 field evidence panels；需要重新证明当前手机入口在 fresh Chromium profile 中仍能打开、console-zero、current panels 可见，并保持 fail-closed。

## Rerank Decision

Objective 5 是数字最低项，但当前主机无法产出真实外部云、4G、OSS/CDN、production DB/queue 或 true phone/browser proof。继续推进本地 O5 wrapper 只会重复消费同一外部材料 blocker。

本 sprint 因此切到 Objective 4 的可执行缺口：刷新当前 `mobile/web` panel 的 local Chromium-family browser proof，确认当前首屏与最新安全/材料/ACK panels 在 isolated profile 下可见且不会启用主操作。

本轮不提高 OKR 百分比，不声明真实手机/browser，不声明 Objective 5 external proof，不声明 delivery success。

## 本轮核心抓手

用一个聚焦 browser proof refresh 把当前 `mobile/web` 状态重新变成可复验材料：

- fresh Chromium profile 加载当前 `mobile/web` shell。
- 证明最新 current panels 可见，尤其是 material-resolution / reviewer ACK / terminal result / support handoff / cloud readiness 相关只读状态。
- 严格保持 `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- 保留 `not true phone/browser` 证据边界，不把本地浏览器通过写成真实手机或真实外部浏览器验收。

## 优先级和验收口径

Priority: P0 planning for next Engineer execution, because如果当前入口在 fresh profile 中不能证明 console-zero 和 fail-closed，就无法继续把用户手机入口作为可信支持界面。

Acceptance:

- `pre_start.md`、`prd.md`、`tech-plan.md` 创建完成。
- 三份文档同时包含 capability、evidence boundary、Objective 5 / Objective 1 blocker、PR #5 unresolved thread、fail-closed booleans 和 `not true phone/browser` 边界。
- `tech-plan.md` 包含 `## OKR 最低优先级核对`，并给出不直接推进 Objective 5 的具体理由。
- 本规划不改产品代码、测试、`OKR.md` 或其他 `docs/`。

## 对应责任 Engineer

- `full-stack-software-engineer`: 后续执行 browser proof refresh，必要时只修 `mobile/web` 或 browser gate 暴露出的当前 panel / console-zero / fail-closed 问题。
- `robot-software-engineer`: 后续只读核对 Robot diagnostics safe summary 是否仍只暴露 phone-safe metadata，不扩大控制面。
- `product-okr-owner`: 本轮创建规划文档；执行后负责 closeout、OKR 边界和 no-lift 复核。

## 风险、阻塞和证据链缺口

- O5 仍阻塞：缺真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser 和 verified terminal result。
- O1 仍阻塞：缺真实 WAVE ROVER/UART/HIL、2D LiDAR/ToF material、operator HIL report；PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍按 unresolved / hardware_material_pending 处理。
- O4 仍阻塞：本轮即使后续 browser proof 通过，也仍不是真实 iPhone/Android device behavior、production app、真实 PWA prompt/userChoice 或 true phone/browser acceptance。
- 代码质量风险：若后续 Engineer 改 `mobile/web`，新增技术注释必须使用中文且保持有意义注释比例；本轮规划不新增产品代码。

## 需要创建或更新的 sprint 文档

- 本规划任务创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 后续 Engineer 执行后必须更新：`tech-done.md`。
- 后续 Product closeout 必须更新：`side2side_check.md`、`final.md`；只有真实证据支持时才更新 `OKR.md`，本轮预期 no OKR percentage lift。
