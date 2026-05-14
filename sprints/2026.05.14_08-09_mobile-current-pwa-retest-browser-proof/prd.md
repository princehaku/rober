# Sprint 2026.05.14_08-09 Mobile Current PWA Retest Browser Proof - PRD

## 用户价值和产品北极星

手机仍是普通用户唯一入口。上一轮已经把真实设备验收材料推进到 retest request package，但还缺“当前 PWA 首屏变更能在浏览器里稳定看见”的可复查证据。

本轮用户价值是：支持或验收人员可以打开本地 evidence 包，看到最新首屏包含三步主路径、恢复决策、终端动作二次确认、设备证据、handoff、PWA install prompt、浏览器验收包和真实设备复测请求，并确认所有控制动作仍 fail closed。

## OKR 映射

- Objective 4 KR5：把真实设备复测请求从静态 fixture/unit proof 推进到本地浏览器 evidence，可为后续真机复测提供截图和 JSON 对照。
- Objective 4 KR7：验证最新手机首屏的关键面板、触控尺寸、phone-safe 文案、ACK 语义和主路径 fail-closed 状态。
- Objective 5：本轮不推进。没有真实公网、4G/SIM、OSS/CDN、production DB/queue 或 worker/migration 外部证据。

## 验收口径

- 浏览器 gate 必须输出 390x844 和 768x900 两套截图与 JSON evidence，并包含 retest request panel 的可见性、boundary、safe copy 和 not-proven 断言。
- Robot compatibility fence 必须证明 retest browser proof / retest request metadata 是 metadata-only，不会驱动 collect、confirm_dropoff、cancel、ACK、cursor、terminal ACK、production readiness、HIL 或 delivery success。
- Product closeout 必须在 OKR 中保守表达：这是 `software_proof_docker_mobile_current_pwa_retest_browser_proof_gate`，不是真实手机设备、production app、真实 PWA install prompt/user choice 或 O5 外部 proof。

## 非目标

- 不做真实 iPhone/Android 验收。
- 不做 production app 或真实 PWA install prompt/user choice 验收。
- 不做真实云公网、4G/SIM、OSS/CDN、production DB/queue 验收。
- 不做 WAVE ROVER、串口、HIL、Nav2/fixed-route 或真实送达验证。
