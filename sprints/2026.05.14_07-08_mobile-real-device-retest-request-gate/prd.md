# Sprint 2026.05.14_07-08 Mobile Real Device Retest Request Gate - PRD

## 用户价值和产品北极星

本轮面向真实设备复测验收人员、支持同学和 Product closeout。上一轮 `mobile_real_device_review_execution*` 已经能记录人工评审执行状态，但仍停在“评审执行记录”；本轮要把 blocked reason、next evidence request、evidence readiness、operator/reviewer notes、`not_proven` 和 source/redaction boundary，整理成下一次真实设备复测可以直接照单执行的 retest request package。

北极星仍是普通用户用手机完成低成本垃圾投递机器人任务。本轮不是扩大本地 metadata，而是把真实设备验收缺口转成清晰复测请求：谁负责、下一步补什么、哪些材料仍 missing、为什么 blocked 或 rejected、哪些证据只能作为软件证明。复测请求包不能被误读为真实验收通过、HIL、Objective 5 外部 proof 或 delivery success。

## OKR 映射

- Objective 4 KR5：用户验收标准从 review execution 推进到 retest request，能说明下一轮真实设备复测缺哪些材料、由谁补齐、当前 readiness/status 是什么。
- Objective 4 KR7：手机端 UI 的真实设备/PWA/production app 验收链路增加 retest checklist、missing evidence list、owner/next action、blocked reason、rejection reason、redaction/source boundary、ACK-not-delivery 和 `not_proven`。
- Objective 5：本轮不推进云中转/OSS/CDN 产品化，因为当前没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他 Objective 5 外部材料。
- Objective 1/2/3：本轮不推进硬件、导航或真实送达，因为没有 WAVE ROVER/HIL、Nav2/fixed-route、任务复盘或真实 delivery 材料。

## KR 拆解或更新

- KR-A：`mobile/web` 首屏新增或派生 `mobile_real_device_retest_request`、`mobile_real_device_retest_request_summary`、`mobile_real_device_retest_request_package`。
- KR-B：retest request 从 `mobile_real_device_review_execution`、`mobile_real_device_review_execution_summary`、`mobile_real_device_review_execution_package` 派生，保留 source evidence boundary。
- KR-C：retest request panel 展示 retest checklist、missing evidence list、每项材料 readiness/status、owner/next action、blocked reason、rejection reason、redaction/source boundary、ACK-not-delivery 和 `not_proven`。
- KR-D：copy package 必须 whitelist/phone-safe，只输出复测所需摘要和下一步请求；敏感字段必须被过滤或转为 blocked/rejected summary。
- KR-E：缺真实设备行为、production app、真实 PWA install prompt/user choice 或 Objective 5 外部材料时，Start Delivery、Confirm Dropoff、Cancel 必须继续 fail closed。
- KR-F：Robot remote bridge/protocol tests 证明 `mobile_real_device_retest_request*` 是 metadata-only；即使与 valid command 混合，也只执行 command envelope，不让 retest request metadata 进入 command/status/ACK/cursor/terminal ACK/production readiness/HIL/delivery success。
- KR-G：Product closeout 只在 A/B 证据成立后谨慎更新 Objective 4；Objective 5 没有真实外部材料则保持约 68%。

## 本轮核心抓手

核心抓手是把 `review execution` 的“执行记录”变成 `retest request` 的“下一轮实测材料请求”。这不是再堆一层状态名，而是要解决真实复测人员的具体问题：

- 下一轮复测入口是什么。
- 缺哪些真实材料：真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice、production HTTPS URL summary、真实公网/4G/O5 外部材料等。
- 每项材料当前 readiness/status 是 ready、missing、blocked、rejected 还是 not_proven。
- owner 和 next action 是谁负责、下一步提交什么。
- redaction/source boundary 是否可信，哪些材料不能复制。
- ACK 或 HTTP accepted 只能表示 accepted/processing，不能表示 delivery success。

## 需要做什么

1. Full-stack 在 `mobile/web`、fixture、mobile unit test、`mobile/README.md` 和 `docs/product/mobile_user_flow.md` 中增加 retest request checklist/status/package。
2. Robot 在 remote bridge/protocol tests 和 `docs/interfaces/ros_contracts.md` 中增加 `mobile_real_device_retest_request*` metadata-only response fence。
3. Product 在 A/B 之后核对证据，更新 `OKR.md`、`docs/process/okr_progress_log.md` 和 sprint closeout，严格区分 software proof、真实设备材料、Objective 5 外部证据、HIL 和 delivery success。

## 优先级和验收口径

- P0：retest request package 可复制，字段 phone-safe，敏感字段被过滤。
- P0：UI 可展示 retest checklist、missing evidence list、readiness/status、owner/next action、blocked reason、rejection reason、redaction/source boundary、ACK-not-delivery 和 `not_proven`。
- P0：缺真实手机、production app、真实 PWA install prompt/user choice 或 O5 外部材料时，Start / Confirm / Cancel 继续 fail closed。
- P0：Robot fence 证明 retest request metadata 不进入 command、status、ACK、cursor、terminal ACK、production readiness、HIL、dropoff/cancel success 或 delivery success。
- P1：Product closeout 明确 `software_proof_docker_mobile_real_device_retest_request_gate` 不是真实手机设备、真实 PWA prompt、Objective 5 外部材料、HIL 或 delivery success。

## 对应责任 Engineer

- `full-stack-software-engineer`：Task A，手机首屏、fixture、unit test、mobile README、product mobile flow doc。
- `robot-software-engineer`：Task B，Robot metadata-only fence 与 ROS contract doc。
- `product-okr-owner`：Task C，验收、OKR、progress log 和 sprint closeout。
- `hardware-engineer`：本轮无实现任务；如触及硬件事实只能只读补证，不改硬件配置。
- `autonomy-engineer`：本轮无实现任务；如触及 Nav2/fixed-route 事实只能只读补证。

## 风险、阻塞和需要补齐的证据链

- 真实手机设备、真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice 仍缺。
- 真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 仍缺。
- Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff/cancel completion 和真实 delivery 仍缺。
- 本轮成功后也只能证明 Docker/local mobile software proof + Robot metadata-only fence；不能提升 Objective 5，也不能把 retest request 写成真实验收完成。

## 需要创建或更新的 sprint 文档

本阶段已创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`
- `tech-done.md` 待工程回填骨架

执行后必须更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
