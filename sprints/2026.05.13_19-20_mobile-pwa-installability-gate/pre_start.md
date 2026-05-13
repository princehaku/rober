# Sprint 2026.05.13_19-20 Mobile PWA Installability Gate - Pre Start

## Sprint 类型

- `sprint_type: epic`
- 启动时间：2026-05-13 19:20 Asia/Shanghai
- 主目标：Objective 4 建立手机用户体验与低成本量产边界
- 关联目标：Objective 5 云中转 + OSS/CDN 数据通路产品化
- 证据边界目标：`software_proof_docker_cloud_hosted_mobile_pwa_installability_gate`

## 用户原始要求

用户要求根据近期 PR/评审给出基于证据的下一步 OKR，team 执行，功能往前走，测试只围栏，优先推进完成度低的 OKR；本机只有 Docker、没有真实硬件；最后整体 sprint 需要提交并推送。

## 开工证据

- `OKR.md` 4.1 更新时间为 2026-05-13 19:00，最新 sprint 为 `2026.05.13_18-19_cloud-hosted-mobile-web-gate`。
- 当前完成度：Objective 5 约 68%，Objective 4 约 70%，Objective 1 约 75%，Objective 2/3 约 77%。
- `2026.05.13_17-18_o5_external-evidence-intake-gate` 已完成 `software_proof_docker_external_evidence_intake_gate`，但没有真实外部材料，因此 Objective 5 当轮不上调。
- `2026.05.13_18-19_cloud-hosted-mobile-web-gate` 已完成 `software_proof_docker_cloud_hosted_mobile_web_gate`，证明 `cloud-relay` Docker/local runtime 可 same-origin 托管 `mobile/web/` PWA，并提供 fail-closed `/api/status`、`/api/diagnostics` adapter。
- 最新 O5 缺口仍是：真实公网 HTTPS/TLS、真实 4G/SIM、真实手机设备/browser、production app、真实 PWA install prompt、OSS/CDN live traffic、production DB/queue。
- 最新 O4 缺口仍是：真实 iPhone/Android device behavior、production app、真实 PWA install prompt、TTS/喇叭实放、真实送达与量产实物验收。

## 本轮选择

本轮不继续做本地 O5 metadata depth，转向 Objective 4 的 cloud-hosted PWA installability/browser acceptance gate。

选择理由：

- Objective 5 虽是最低完成度，但 `OKR.md` 第 6 节明确写明：若继续 O5，下一轮必须接入至少一种真实外部材料；如外部材料不可用，应回到 Objective 4 的真实手机设备/browser、production app 或 PWA install prompt 缺口。
- 当前没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic 或 production DB/queue 材料可接入，继续 O5 本地 metadata gate 会重复 17-18 和 18-19 的局部深度。
- Objective 4 仍缺 PWA install prompt/browser acceptance；在 Docker/local + Chromium-family browser 围栏内，可以把同一份 cloud-hosted PWA 的 manifest、service worker、offline shell、asset routing、phone-safe browser evidence bundle 推到更接近用户入口的验收形态。
- 本机没有真实硬件，不能重复消费 Objective 1 HIL blocker，也不能把 Docker/browser proof 说成真实设备、真实 PWA install prompt 或真实送达。

## 本轮核心抓手

把 18-19 的 same-origin hosted PWA 从“能被 cloud-relay 托管”推进到“具备可机器验收的 cloud-hosted PWA installability/browser acceptance bundle”：

- 浏览器能从 cloud-hosted URL 获取 manifest、service worker、offline shell 和图标。
- gate 能验证 manifest installability metadata、service worker 静态缓存边界和 `/api/*` no-store 控制面边界。
- 手机首屏仍 fail-closed，ACK 文案仍是 accepted/processing evidence，不是 delivery success。
- robot metadata compatibility fence 证明 installability/browser metadata 不触发 command、ACK 或 cursor。

## Owner 和并行方式

- Task A：`full-stack-software-engineer`，负责 cloud-hosted PWA installability/browser acceptance gate。
- Task B：`robot-software-engineer`，负责 metadata-only compatibility fence。
- Task C：`product-okr-owner`，负责后续 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md` 收口；本阶段不执行。

Task A 与 Task B 文件范围互不重叠，应并行启动。Task C 在 A/B 返回后收口。

## Blocker 扫描

最近两轮没有重复消费 O1 HIL blocker。本轮不碰 WAVE ROVER、ESP32、Orange Pi、UART、launch 硬件参数、Nav2/fixed-route 或真实送达。

O5 的当前 blocker 是“没有真实外部材料”。该 blocker 已在 17-18 明确记录，18-19 转为 same-origin hosted PWA software proof，本轮按 `OKR.md` 第 6 节切到 O4 可推进缺口，避免第三轮重复消费。

## 预期非目标

- 不证明真实 iPhone/Android device behavior。
- 不证明真实 PWA install prompt。
- 不证明 production app。
- 不证明真实 HTTPS/TLS、公网入口、4G/SIM、OSS/CDN live traffic 或 production DB/queue。
- 不证明 Nav2/fixed-route、WAVE ROVER、HIL、真实投放、真实取消完成或真实送达。

