# Sprint 2026.05.13_16-17 Mobile Web Browser Proof Gate - Pre Start

## Sprint 声明

- sprint_type: epic
- Objective: Objective 4 手机用户体验与低成本量产边界。
- 本轮主题：把真实 Chromium-family browser proof 迁移到当前 `mobile/web/` 静态 PWA 入口，形成可复用 screenshot/json/summary evidence。
- 当前边界：本轮最多声明真实本地 Chromium-family browser proof / Docker-local browser software proof；不能声明真实 iPhone/Android 手机设备、production app、真实 PWA install prompt、真实云/4G、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

## 开工依据

- `OKR.md` 4.1 当前最低完成度为 Objective 5 约 67%，Objective 4 约 68% 为次低。
- `OKR.md` 第 6 节明确：如继续 Objective 5，下一轮必须引入真实 OSS/CDN、4G/SIM、云账号或 production DB/queue 外部证据；如外部云/4G/DB/queue 条件仍不可用，应回到 Objective 4 的真实手机设备/browser、production app 或 PWA install prompt 验收缺口。
- `sprints/2026.05.13_15-16_mobile-browser-acceptance-bundle-gate/final.md` 给出同样下一步：外部环境仍不可用时，回到 Objective 4 的真实手机设备/browser、production app 或 PWA install prompt 验收。
- `sprints/2026.05.13_14-15_oss-cdn-live-probe-gate/final.md` 与 `sprints/2026.05.13_12-13_cloud-db-queue-external-probe-gate/final.md` 已分别把 OSS/CDN、DB/queue 外部 probe 做成 blocked-by-design 软件证明。
- 当前主机口径仍是 Docker-only，没有真实硬件，也没有已知真实云/OSS/CDN/DB/queue/4G 凭证可用。
- 2026-05-12 曾有 `phone_browser_acceptance_gate.py` 真实 Chrome browser gate，但当前 repo 已重构到 `onboard/`、`mobile/web/`，且 mobile PWA 已新增 browser acceptance bundle；本轮应迁移到当前静态入口，不继续只写字符串单测。

## 用户价值和产品北极星

用户价值：测试者或售后同学可以打开当前手机 PWA 静态入口，用真实本地 Chromium-family browser 生成截图、JSON、summary 证据，判断手机首屏、浏览器验收包、fail-closed 操作和复制交接是否在真实浏览器里成立，而不是只相信 fixture 字符串单测。

产品北极星：普通用户只用手机完成垃圾交付；在真实手机/production app 条件未满足前，手机入口必须用真实浏览器证明可见、可复制、可解释、fail closed，且不能把 ACK 或本地 proof 误说成真实送达。

## 上轮未完成项和阻塞

- 未完成项：Objective 4 仍缺真实手机设备/browser、production app、真实 PWA install prompt。
- 未完成项：Objective 5 仍缺真实 OSS/CDN live traffic、真实云、真实 4G/SIM、production DB/queue。
- 阻塞：O5 下一步必须依赖外部云/OSS/CDN/DB/queue/4G 条件；最近两轮已经分别消费 DB/queue external probe 与 OSS/CDN live probe blocked-by-design，继续做本地 metadata 深度会重复消费同一类外部证据缺口。
- 本轮切换理由：在外部条件不可用时，改做 Objective 4 的真实 browser 验收缺口，避免第三轮继续围绕 O5 外部条件做 blocked-by-design 软件证明。

## Owner 和分工

- Task A `full-stack-software-engineer`：迁移并修复 browser acceptance gate，使其服务并验证当前 `mobile/web/` PWA，产出 evidence。
- Task B `robot-software-engineer`：做 metadata-only compatibility fence，确认新的 evidence boundary 或 summary 字段不触发 backend action/ACK/cursor。
- Task C `product-okr-owner`：等待 Task A/B 后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。

## 启动验收

- `pre_start.md`、`prd.md`、`tech-plan.md` 已创建后，进入 Task A/B 并行实现阶段。
- 本启动任务不修改产品代码、测试代码、`OKR.md` 或 closeout 文件。
