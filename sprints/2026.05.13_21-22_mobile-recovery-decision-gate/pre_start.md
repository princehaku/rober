# Sprint 2026.05.13_21-22 Mobile Recovery Decision Gate - Pre Start

## Sprint 类型

- `sprint_type: epic`
- 启动时间：2026-05-13 21:00 Asia/Shanghai
- 主目标：Objective 4 手机用户体验与低成本量产边界
- 证据边界：`software_proof_docker_mobile_recovery_decision_gate`

## 上轮证据

- `sprints/2026.05.13_20-21_mobile-primary-journey-gate/final.md` 已完成 `software_proof_docker_mobile_primary_journey_gate`：`mobile/web/` 首屏具备目标垃圾站、已放入垃圾确认、发车安全 gate 三步主路径。
- 同一 final 明确 ACK、HTTP accepted、action receipt 仍只是 accepted/processing evidence，不是 delivery success、dropoff success、cancel completed 或 true task completion。
- `OKR.md` 4.1 当前最低完成度是 Objective 5 约 68%，但第 6 节要求没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 材料时，不继续堆本地 O5 metadata depth。

## 本轮选择

在 Docker-only 约束下，本轮不重复消费 Objective 5 外部材料 blocker，转向当前最低可推进 Objective 4。具体抓手是手机端恢复决策：当 Start/Confirm/Cancel 被阻塞、pending ACK、offline、manual takeover 或本地提交失败时，普通用户应在首屏看到明确的下一步，而不是只看到一组 proof 面板。

## Owner

- `full-stack-software-engineer`：实现 `mobile/web/` 恢复决策首屏 panel、fixture、围栏测试和产品流程文档。
- `robot-software-engineer`：补齐 robot remote bridge metadata-only compatibility fence，证明恢复决策 summary 不触发 command、ACK 或 cursor。
- `product-okr-owner`：A/B 返回后更新 sprint closeout、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 风险边界

- 本机没有真实硬件，不做 WAVE ROVER、串口、HIL、Nav2/fixed-route 或真实送达声明。
- 本机没有真实公网/4G/OSS/CDN/production DB queue 证据，不提升 Objective 5。
- 本轮只形成 Docker/local software proof；不是真实 iPhone/Android device behavior、production app、真实 PWA install prompt、真实 cancel completion 或真实 dropoff completion。
