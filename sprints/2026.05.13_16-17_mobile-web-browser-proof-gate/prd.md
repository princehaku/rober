# Sprint 2026.05.13_16-17 Mobile Web Browser Proof Gate - PRD

## 1. 用户价值和产品北极星

用户价值：手机/PWA 验收不应停留在 fixture 和字符串单测。用户、售后或工程支持需要一份由真实本地 Chromium-family browser 生成的证据包，包含当前 `mobile/web/` 首屏截图、结构化 JSON、summary 和阻塞说明，用来判断手机入口是否真实可打开、可阅读、可复制交接、主操作是否 fail closed。

产品北极星：`rober` 面向普通手机用户完成垃圾交付。当前还没有真实手机设备、production app、PWA install prompt 和真实云/4G 条件，因此本轮的产品目标是把真实浏览器验收能力补到当前手机入口，保证“未满足真实条件时不误导用户、不误开主操作、不把 ACK 当交付成功”。

## 2. OKR 映射

- Objective 4 KR1：手机端最小流程需要真实浏览器打开并验证首屏入口，而不只是静态文件存在。
- Objective 4 KR4：远程诊断最小数据包需要可复制、可交接的 browser evidence summary。
- Objective 4 KR5：普通用户无需命令行、ROS2 或硬件知识，也能看懂当前阻塞原因和下一步。
- Objective 4 KR7：手机端 UI 美观且能直接使用；本轮验证真实浏览器中的 viewport、touch target、PWA shell、browser acceptance bundle 和 fail-closed 状态。

本轮不直接推进 Objective 5。O5 的下一步需要真实 OSS/CDN、4G/SIM、云账号或 production DB/queue 外部证据，当前条件不可用且最近两轮已形成 blocked-by-design proof。

## 3. KR 拆解或更新

- KR-A：`pc-tools/evidence/phone_browser_acceptance_gate.py` 能服务当前 `mobile/web/` 静态 PWA，并通过真实本地 Chromium-family browser 验证首屏可用性。
- KR-B：browser proof 输出到 `sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/evidence/`，至少包含 screenshot、JSON 和 human-readable summary。
- KR-C：browser proof 明确证据边界为本地 Chromium-family browser proof / Docker-local browser software proof，不声明真实 iPhone/Android、production app、真实 PWA install prompt 或真实送达。
- KR-D：如果新增 evidence boundary 或 acceptance summary 字段，robot compatibility fence 证明这些字段只是 metadata，不触发 backend action、ACK、cursor 推进或持久化。
- KR-E：相关产品文档同步到 `mobile/README.md` 与 `docs/product/mobile_user_flow.md`，保持 browser proof 与当前 `mobile/web/` 入口一致。

## 4. 本轮核心抓手

核心抓手是把 2026-05-12 的 browser gate 能力迁移到当前 `mobile/web/` PWA，而不是继续增加 UI 字段或只补 fixture 单测。验收必须由真实本地 Chromium-family browser 产出 evidence 文件，且 evidence 文件必须落在本 sprint 目录，方便 Product closeout 和 OKR 更新引用。

## 5. 需要做什么

1. Full-stack 修改或迁移 `pc-tools/evidence/phone_browser_acceptance_gate.py`，让脚本启动/服务当前 `mobile/web/` 静态入口，并生成 browser evidence。
2. Full-stack 同步 `mobile/README.md` 和 `docs/product/mobile_user_flow.md`，说明当前 browser proof 的运行方式、证据边界和非声明项。
3. Full-stack 仅在必要时调整少量 fenced unittest，避免扩大测试面。
4. Robot 只做 compatibility fence：新增字段时更新 `docs/interfaces/ros_contracts.md` 和 remote bridge/protocol tests；如果没有新增后端字段，则只读确认并在 `tech-done.md` 说明无需 runtime 改动。
5. Product 等 A/B 返回后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 6. 优先级和验收口径

P0：
- browser gate 必须指向当前 `mobile/web/`，不能继续验证过时入口。
- evidence 必须写入本 sprint `evidence/` 目录。
- Start Delivery、Confirm Dropoff、Cancel 在缺真实条件时仍 fail closed。
- ACK 仍只能描述为 accepted/processing evidence。

P1：
- 文档同步说明如何运行 browser proof、输出什么、不能证明什么。
- 如新增 metadata 字段，robot tests 证明不会触发 backend action/ACK/cursor。

不做：
- 不声明真实 iPhone/Android 手机设备验收。
- 不声明 production app 或真实 PWA install prompt。
- 不接入真实云/4G、OSS/CDN live traffic、production DB/queue。
- 不改 Nav2/fixed-route、WAVE ROVER、HIL 或真实送达链路。

## 7. 对应责任 Engineer

- Task A：`full-stack-software-engineer`
- Task B：`robot-software-engineer`
- Task C：`product-okr-owner`

## 8. 风险、阻塞和证据链

- 风险：本机可能没有可用 Chromium-family browser 或 headless 依赖；若失败，Task A 必须定位缺失依赖并报告 blocked evidence，不能把字符串单测冒充 browser proof。
- 风险：evidence summary 字段如果进入 status/diagnostics metadata，可能被 remote bridge 误归类为 command/status/ACK envelope；Task B 必须用 compatibility fence 消除该风险。
- 风险：浏览器 proof 容易被误写成真实手机设备或 production app 验收；所有文档和 closeout 必须写清证据边界。
- 阻塞：真实云/4G/OSS/CDN/DB/queue、真实手机设备、production app、真实 PWA install prompt、真实硬件/HIL 仍不可用。
- 证据链：`phone_browser_acceptance_gate.py` run output -> sprint `evidence/` screenshot/json/summary -> Task A unittest/py_compile/diff check -> Task B robot compatibility tests -> Product closeout/OKR progress log。

## 9. 需要创建或更新的 sprint 文档

本启动任务创建：
- `sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/pre_start.md`
- `sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/prd.md`
- `sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/tech-plan.md`

Task C 收口时更新：
- `sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/tech-done.md`
- `sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/side2side_check.md`
- `sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
