# Sprint 2026.05.14_05-06 Mobile Real Device Review Handoff Gate - PRD

## 用户价值和产品北极星

本轮面向的用户不是只会看技术日志的工程同学，而是普通手机用户、人工评审同学和支持同学。上一轮 acceptance decision 已能判定材料是否可进入人工评审；本轮要把这个 decision 变成可交接的 review handoff session/package，让评审者知道谁负责、看什么、缺什么、哪些字段已脱敏、哪些能力仍是 `not_proven`。

北极星仍是普通用户用手机完成低成本垃圾投递机器人任务，并在失败或缺证据时知道下一步。review handoff 不是把流程做复杂，而是让真实设备验收从“有 decision”推进到“有人能接手评审并补证据”。

## OKR 映射

- Objective 4 KR5：用户验收标准继续从 decision gate 推进到人工评审交接，普通用户和评审者能知道真实设备验收还缺哪些材料。
- Objective 4 KR7：手机端 UI 的真实设备/PWA/production app 验收链路增加 reviewer checklist、review owner/status、redaction status 和 phone-safe copy package。
- Objective 5：本轮不推进云中转/OSS/CDN 产品化，因为没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他 O5 外部材料。
- Objective 1/2/3：本轮不推进硬件、导航或真实送达，因为没有 WAVE ROVER/HIL、Nav2/fixed-route 或真实 delivery 材料。

## KR 拆解或更新

- KR-A：`mobile/web` 首屏新增或派生 `mobile_real_device_review_handoff`、`mobile_real_device_review_handoff_summary`、`mobile_real_device_review_handoff_package`。
- KR-B：review handoff panel 展示 reviewer checklist、decision status、review owner/status、evidence blocker、next required evidence、redaction status、source boundary、ACK-not-delivery 和 `not_proven`。
- KR-C：copy package 必须过滤敏感字段，不包含 token、Authorization、OSS AK/SK、root password、DB/queue URL、raw ROS topic、`/cmd_vel`、serial、baudrate、WAVE ROVER、本地路径、traceback、checksum、complete artifact 或 raw robot response。
- KR-D：Robot remote bridge/protocol tests 证明 `mobile_real_device_review_handoff*` 是 metadata-only，不触发 collect、dropoff、cancel、ACK、cursor、terminal ACK、production readiness、HIL 或 delivery success。
- KR-E：Product closeout 只在 A/B 证据成立后谨慎更新 Objective 4；Objective 5 没有外部材料则保持约 68%。

## 本轮核心抓手

核心抓手是从 `mobile_real_device_acceptance_decision*` 派生人工评审交接。review handoff 必须把“材料可否评审”变成“评审者下一步怎么做”，但不新增控制放行语义。

必须保留的产品边界：

- `accepted_for_review` 或 review-ready 只表示材料可以交给人工评审，不等于真实设备验收通过。
- ACK、HTTP accepted、receipt、intake package、decision package、review handoff package 仍只是 accepted/processing/support metadata，不是 delivery success。
- 缺真实设备材料时 Start / Confirm / Cancel 继续 fail closed。

## 需要做什么

1. Full-stack 在 `mobile/web` 和 fixture/test/doc 中增加 review handoff session/package。
2. Robot 在 remote bridge/protocol tests 和 interface doc 中增加 metadata-only response fence。
3. Product 在 A/B 之后核对证据，更新 `OKR.md`、`docs/process/okr_progress_log.md` 和 sprint closeout，严格区分 software proof 与真实设备/O5/HIL/delivery 证据。

## 优先级和验收口径

- P0：review handoff package 可复制，字段 phone-safe，敏感字段被过滤。
- P0：缺真实手机、production app、真实 PWA install prompt/user choice 时，Start / Confirm / Cancel 继续 fail closed。
- P0：Robot fence 证明 review handoff metadata 不进入 command、ACK、cursor、terminal ACK、production readiness、HIL、dropoff/cancel success 或 delivery success。
- P1：UI 明确展示 reviewer checklist、review owner/status、decision status、evidence blocker、next required evidence、redaction status、source boundary、ACK-not-delivery 和 `not_proven`。
- P1：Product closeout 明确 `software_proof_docker_mobile_real_device_review_handoff_gate` 不是真实手机设备、真实 PWA prompt、O5 外部材料、HIL 或 delivery success。

## 对应责任 Engineer

- `full-stack-software-engineer`：Task A，手机首屏与 package。
- `robot-software-engineer`：Task B，Robot metadata-only fence。
- `product-okr-owner`：Task C，验收、OKR 和 closeout。
- `hardware-engineer`：本轮无实现任务；如触及硬件事实只能只读补证，不改硬件配置。
- `autonomy-engineer`：本轮无实现任务；如触及 Nav2/fixed-route 事实只能只读补证。

## 风险、阻塞和需要补齐的证据链

- 真实手机设备、真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice 仍缺。
- 真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 仍缺。
- Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff/cancel completion 和真实 delivery 仍缺。
- 本轮成功后也只能证明 Docker/local mobile software proof + robot metadata-only fence；不能提升 Objective 5，也不能把 review handoff 写成真实验收完成。

## 需要创建或更新的 sprint 文档

本阶段已创建或计划创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

执行后必须更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
