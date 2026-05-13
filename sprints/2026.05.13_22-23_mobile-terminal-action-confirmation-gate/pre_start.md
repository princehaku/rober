# Sprint 2026.05.13_22-23 Mobile Terminal Action Confirmation Gate - Pre Start

## Sprint 类型

sprint_type: epic

本轮是跨 owner 的 Epic sprint：Task A 由 `full-stack-software-engineer` 推进 `mobile/web/` 终端动作二次确认；Task B 由 `robot-software-engineer` 补 remote bridge/protocol metadata-only fence；Task C 由 `product-okr-owner` 在 A/B 完成后收口 `OKR.md`、进度日志和本 sprint 留档。

## 上轮输入

最新 sprint `sprints/2026.05.13_21-22_mobile-recovery-decision-gate/final.md` 已完成 `software_proof_docker_mobile_recovery_decision_gate`。该证据证明 Docker/local mobile 恢复决策 panel 和 robot metadata-only fence 可用，但不证明真实 iPhone/Android device behavior、production app、真实 PWA install prompt、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL、真实取消完成、真实投放完成或真实 delivery。

上轮 final 建议：若没有真实外部 O5 材料，下一轮继续 Objective 4 的真实 iPhone/Android device behavior、production app、真实 PWA install prompt 或真实移动设备验收缺口。当前本机只有 Docker，没有真实硬件和外部 O5 材料，因此不继续堆 O5 本地 metadata depth。

## 用户价值和产品北极星

本轮把手机端 Confirm Dropoff / Cancel 从“点击即发 generic payload”推进到“用户先看懂终端动作、风险和 ACK 语义，再显式二次确认”。普通用户在投放确认或取消任务前，需要知道这只是请求已提交/处理中，不等于真实投放完成、真实取消完成或 delivery success。

这服务于北极星：让不会电脑和硬件的普通手机用户能使用低成本 ROS2 垃圾投递机器人，并在终端动作上获得足够明确、保守、可追溯的操作反馈。

## OKR 映射

- Objective 4 KR1：手机端最小流程继续补齐“查看状态 -> 处理异常 -> 终端动作确认”。
- Objective 4 KR5：用户不理解 ROS2、ACK、cursor 或 remote bridge，也能知道 Confirm Dropoff / Cancel 的含义和限制。
- Objective 4 KR7：手机端主路径更接近可直接使用，但证据仍限定为 Docker/local mobile software proof。
- Objective 5：当前最低但被真实外部材料卡住；本轮不提升 Objective 5。

## 本轮核心抓手

核心抓手是 `software_proof_docker_mobile_terminal_action_confirmation_gate`：在 `mobile/web/` 为 Confirm Dropoff / Cancel 增加终端动作二次确认 gate，并用 robot metadata-only fence 证明 `mobile_terminal_action_confirmation_gate` / summary 只作为手机/支持 metadata，不触发 collect、confirm_dropoff、cancel、ACK 或 cursor。

## Blocker 和切换原因

当前 `OKR.md` 4.1 最低完成度是 Objective 5，约 68%。但 `OKR.md` 第 6 节明确要求，没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 证据时，不继续堆本地 O5 metadata depth。

本轮切换到 Objective 4，因为 Docker-only 环境下仍可推进手机端终端动作理解和确认 gate。该切换不是宣称真实手机设备、真实公网、真实云或真实投放完成，而是补齐本地 mobile software proof 的用户安全语义。

## Owner 和阶段

- Task A：`full-stack-software-engineer`，实现 `mobile/web/` 终端动作二次确认 UI/状态、fixture、targeted mobile test 和文档。
- Task B：`robot-software-engineer`，实现 remote bridge/protocol metadata-only fence 和接口文档。
- Task C：`product-okr-owner`，在 A/B 完成后更新 `OKR.md`、`docs/process/okr_progress_log.md`、`tech-done.md`、`side2side_check.md`、`final.md`。

Task A 与 Task B 文件范围互不重叠，进入实现阶段时必须并行派发。Task C 等 A/B 返回后再执行。

## 验收口径

本轮只接受以下证据：

- targeted mobile unittest 通过。
- targeted robot remote bridge/protocol unittest 通过。
- Python `py_compile` 通过。
- `node --check mobile/web/app.js` 通过。
- scoped `git diff --check` 通过。
- 文档明确 `software_proof_docker_mobile_terminal_action_confirmation_gate` 不等于真实 dropoff completion、真实 cancel completion 或 delivery success。

不跑 broad regression，不跑真实硬件，不跑 HIL，不声称真实 iPhone/Android、production app、真实 PWA install prompt、真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或真实送达。

## 需要创建或更新的 sprint 文档

本阶段创建：

- `sprints/2026.05.13_22-23_mobile-terminal-action-confirmation-gate/pre_start.md`
- `sprints/2026.05.13_22-23_mobile-terminal-action-confirmation-gate/prd.md`
- `sprints/2026.05.13_22-23_mobile-terminal-action-confirmation-gate/tech-plan.md`

后续 A/B/C 完成后必须继续创建或更新：

- `sprints/2026.05.13_22-23_mobile-terminal-action-confirmation-gate/tech-done.md`
- `sprints/2026.05.13_22-23_mobile-terminal-action-confirmation-gate/side2side_check.md`
- `sprints/2026.05.13_22-23_mobile-terminal-action-confirmation-gate/final.md`

