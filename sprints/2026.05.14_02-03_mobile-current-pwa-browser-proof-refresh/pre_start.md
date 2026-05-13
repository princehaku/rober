# Sprint 2026.05.14_02-03 Mobile Current PWA Browser Proof Refresh - Pre Start

## sprint_type

sprint_type: epic

## 背景

Automation `skill-progression-map` 在 2026-05-14 继续下一轮迭代。当前 `OKR.md` 4.1 显示 Objective 5 约 68%，是数字最低 Objective；但 `OKR.md` 第 6 节明确，继续提升 Objective 5 需要至少一种真实外部材料：真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration。本机只有 Docker，没有真实硬件，也没有这些外部 O5 材料。

最近 sprint 已连续把 Objective 4 的 `mobile/web/` 从 browser acceptance bundle、local browser proof、cloud-hosted PWA、primary journey、recovery decision、terminal action confirmation、device evidence capture、handoff session 推进到 PWA install prompt evidence。最新收口 `sprints/2026.05.14_01-02_mobile-pwa-install-prompt-evidence-gate/final.md` 的下一步明确：若仍没有 O5 外部材料，应继续 Objective 4，把 phone-safe evidence package 带到真实 iPhone/Android、production app 或真实 PWA install prompt/user choice 验收。

当前 Docker-only 主机无法证明真实 iPhone/Android 或 production app，但可以推进一个可执行缺口：现有 `pc-tools/evidence/phone_browser_acceptance_gate.py` 的真实本地 Chromium-family browser proof 诞生于 `2026.05.13_16-17_mobile-web-browser-proof-gate`，早于后续多个首屏面板。需要刷新 gate，让它覆盖当前 `mobile/web/` 第一屏关键面板，并重新产出截图/JSON evidence。

## 本轮目标

目标 Objective：Objective 4 手机用户体验与低成本量产边界。

本轮抓手：`software_proof_docker_mobile_current_pwa_browser_proof_refresh_gate`。它只证明当前 dependency-free `mobile/web/` PWA 在本地 Chromium-family 浏览器中能渲染最新首屏证据链、主操作继续 fail closed、phone-safe copy 不泄漏敏感字段，并产出 390x844 与 768x900 的截图/JSON 证据。

## 最近证据

- `OKR.md` 4.1：Objective 5 约 68%，但下一步需要真实公网/4G/OSS-CDN/DB-queue/worker 等外部证据。
- `sprints/2026.05.14_01-02_mobile-pwa-install-prompt-evidence-gate/final.md`：PWA install prompt evidence 已是 phone-safe software proof，但仍缺真实手机/browser、production app 和真实 PWA prompt/user choice。
- `docs/process/okr_progress_log.md`：`2026.05.13_16-17_mobile-web-browser-proof-gate` 曾产出 local Chromium proof，但该 proof 早于 primary journey、recovery、terminal action、device evidence、handoff、install prompt evidence 等后续面板。
- `mobile/README.md` 与 `docs/product/mobile_user_flow.md`：当前 mobile/web 已包含多个首屏 proof/support panels，需要浏览器 gate 与当前 UI 同步。

## Owner

- Task A：`full-stack-software-engineer`，更新 current PWA browser proof gate、mobile tests、mobile 文档，并运行 fenced browser proof。
- Task B：`robot-software-engineer`，核对或补充 robot metadata-only compatibility fence，确保 browser proof refresh metadata 不进入 command/ACK/cursor/delivery 语义。
- Task C：`product-okr-owner`，等待 A/B 后执行 closeout，更新 OKR、progress log、sprint 收口文档。

## 证据边界

本轮不能声明真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice、真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff/cancel completion 或真实 delivery。

ACK、HTTP accepted、receipt、browser proof、evidence package、handoff session 和 install prompt evidence 仍只是 accepted/processing/support metadata，不是 delivery success。
