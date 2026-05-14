# Sprint 2026.05.14_11-12 Mobile Field Trial Runbook Execution Gate - Pre Start

## Sprint Type

sprint_type: epic

## 用户原始要求

Automation「开始下一轮迭代」要求：根据近期 PR/评审给出证据驱动建议，用 team 继续完成 OKR，重新在功能往前走，测试只做围栏，优先推进 OKR 完成度低部分。本机没有真实硬件，只有 Docker；最后需要提交并推送。

## 当前证据

- `OKR.md` 4.1 更新时间为 2026-05-14 10:14 Asia/Shanghai，最新 sprint 是 `2026.05.14_10-11_mobile-field-trial-evidence-review-gate`。
- 当前最低 Objective 是 Objective 5，约 68%。但 `OKR.md` 第 6 节明确：只有拿到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 材料时才继续 O5 completion。
- 当前主机是 Docker-only，没有真实手机、真实云、真实 4G/SIM、真实硬件、WAVE ROVER、HIL 或真实送达证据。
- 最新 `10-11` final 明确：若没有 O5 外部材料，应继续 Objective 4 的真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice 或主路径真实移动设备验收。
- 上一轮已完成“现场试跑证据复核”package，本轮不重复 review metadata depth，而是推进为手机端“现场试跑执行清单 / runbook execution package”。

## 本轮产品北极星

让下一次真实手机现场试跑能被普通执行人按清单执行、按证据项记录、按脱敏规则复制，而不是继续停留在“材料复核”层。所有产物必须保持 phone-safe、fail-closed 和 `not_proven` 边界。

## 本轮目标

Primary Objective：Objective 4 手机用户体验与低成本量产边界。

本轮计划引入一致命名：

- package family：`mobile_real_device_field_trial_runbook_execution*`
- evidence boundary：`software_proof_docker_mobile_real_device_field_trial_runbook_execution_gate`

目标是把上一轮 `mobile_real_device_field_trial_review*` 推进成现场执行清单和执行包，指导真实手机/production app/PWA install prompt/user choice/offline/touch/visual/material redaction 的下一次现场试跑执行。

## Stop Rule 与切换理由

Objective 5 当前最低，但本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 材料。继续做本地 O5 metadata depth 会重复消费同一外部材料 blocker。

因此本轮触发 O5 stop rule，转向 Objective 4 的现场试跑执行准备：让下一次真实手机试跑更可执行、更可采证、更不容易把 ACK 或 copy package 误写成 delivery success。

## Owner 与并行方式

- Task A：User Touchpoint Full-Stack Engineer，负责 `mobile/web` 首屏“现场试跑执行清单”panel、summary/copy package、mobile tests、`mobile/README.md` 与 `docs/product/mobile_user_flow.md`。
- Task B：Robot Platform Engineer，负责 remote bridge metadata-only family 围栏和接口文档，证明该 package 不触发 command/ACK/cursor/terminal ACK/production readiness/HIL/dropoff/cancel/delivery success。
- Task C：Product Manager / OKR Owner，负责实现后更新 sprint closeout、`OKR.md`、`docs/process/okr_progress_log.md`，并核对证据边界。

Task A 与 Task B 文件范围互不重叠，应并行启动。Task C 只在 A/B 返回后收口。

## 验收边界

本轮计划只能产生 Docker/local mobile software proof。不得宣称真实手机、真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice、真实云、真实 4G/SIM、OSS/CDN live traffic、production DB/queue、WAVE ROVER、HIL、真实 dropoff/cancel completion 或 delivery success。

## 需要创建或更新的 sprint 文档

- 本阶段创建 `pre_start.md`、`prd.md`、`tech-plan.md`。
- A/B 实现后必须更新 `tech-done.md`。
- Product closeout 必须更新 `side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。
