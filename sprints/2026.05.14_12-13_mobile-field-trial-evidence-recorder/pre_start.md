# Sprint 2026.05.14_12-13 Mobile Field Trial Evidence Recorder - Pre Start

## Sprint Type

sprint_type: epic

## 用户原始要求

CEO 要求创建下一轮 fresh Epic sprint 计划文档，不修改产品代码，不更新 `OKR.md`。当前 live evidence 显示 `OKR.md` 4.1 中 Objective 5 约 68% 最低，但最新 sprint `sprints/2026.05.14_11-12_mobile-field-trial-runbook-execution-gate/final.md` 明确没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration 等外部 O5 材料；按 stop rule 不继续堆本地 O5 metadata。本轮转向 Objective 4 的下一步可执行功能：把上一轮“现场试跑执行清单”推进成 `mobile_real_device_field_trial_evidence_record*` 现场证据记录入口。

## 当前证据

- `OKR.md` 4.1 更新时间为 2026-05-14 11:17 Asia/Shanghai，最新 sprint 是 `2026.05.14_11-12_mobile-field-trial-runbook-execution-gate`。
- 当前最低 Objective 是 Objective 5 云中转 + OSS/CDN 数据通路产品化，约 68%。
- Objective 5 未拿到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他真实外部材料。
- 最新 final 明确：若下一轮仍没有 O5 外部材料，应继续沿 Objective 4 收集真实移动设备、production app、PWA prompt、user choice 相关证据。
- 上一轮已完成 `mobile_real_device_field_trial_runbook_execution*` 执行清单和 Robot metadata-only fence。本轮不重复 checklist metadata，而是推进为可记录、展示、复制和归档人工观察的现场证据记录入口。

## 本轮产品北极星

让真实手机现场试跑不再只靠执行人截图和自由文本散落记录，而是能在手机/PWA 表面按结构化字段记录 production app、PWA prompt、user choice、offline、touch、visual、material redaction 等人工观察，并持续保持 `safe_to_control=false`、ACK 非 delivery success、`not_proven` 和 metadata-only 控制边界。

## 本轮目标

Primary Objective：Objective 4 手机用户体验与低成本量产边界。

本轮计划引入一致命名：

- package family：`mobile_real_device_field_trial_evidence_record*`
- 建议 schema：`trashbot.mobile_real_device_field_trial_evidence_record.v1`
- evidence boundary：`software_proof_docker_mobile_real_device_field_trial_evidence_record_gate`

目标是把上一轮 `mobile_real_device_field_trial_runbook_execution*` 从“要跑什么”推进成“现场真实观察如何记录、展示、复制、归档”。该入口只记录人工观察和 phone-safe runtime metadata，不授予控制权限，不证明真实送达。

## Stop Rule 与切换理由

Objective 5 当前最低，但没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 等外部材料。继续 O5 本地 metadata 只会重复消费同一外部材料 blocker。

因此本轮触发 O5 stop rule，转向 Objective 4 的现场证据记录缺口：真实手机或 production app 现场试跑一旦发生，需要一个结构化入口记录人工观察、脱敏结果和剩余 `not_proven`，并避免把 ACK、HTTP accepted、copy package 或 evidence record 误写成 delivery success。

## Owner 与并行方式

- Task A：User Touchpoint Full-Stack Engineer，负责 `mobile/web` 现场证据记录入口、record/summary/copy/archive package、mobile 围栏测试、`mobile/README.md` 与 `docs/product/mobile_user_flow.md`。
- Task B：Robot Platform Engineer，负责 remote bridge/protocol metadata-only fence 与接口文档，证明 `mobile_real_device_field_trial_evidence_record*` 不触发 command、ACK、cursor、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。

Task A 与 Task B 文件范围互不重叠，应并行启动。Product Owner 在 A/B 完成后再做 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 与 progress log 收口，本阶段不更新这些文件。

## 验收边界

本轮计划只能产生 Docker/local mobile software proof 与 Robot metadata-only fence。不得宣称真实手机设备通过、production app 通过、真实 PWA install prompt/user choice 通过、真实公网 HTTPS/TLS、真实 4G/SIM、OSS/CDN live traffic、production DB/queue、WAVE ROVER、HIL、真实 dropoff/cancel completion 或 delivery success。

## 需要创建或更新的 sprint 文档

- 本阶段创建 `pre_start.md`、`prd.md`、`tech-plan.md`。
- A/B 实现后必须更新 `tech-done.md`。
- Product closeout 必须更新 `side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。
