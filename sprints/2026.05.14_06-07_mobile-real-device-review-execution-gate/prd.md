# Sprint 2026.05.14_06-07 Mobile Real Device Review Execution Gate - PRD

## 用户价值和产品北极星

本轮面向普通手机用户、真实设备评审者和支持同学。上一轮 `review handoff package` 已经能把材料交给人工评审；本轮要让评审者在手机/PWA 首屏记录执行结果：哪些 checklist 已检查，哪些 evidence item ready，评审结论是什么，操作员或 reviewer note 写了什么，为什么 blocked，下一份证据要什么，以及 redaction/source boundary 是否仍然可信。

北极星仍是普通用户用手机完成低成本垃圾投递机器人任务，并且在失败或缺证据时知道下一步。review execution 不是验收通过的包装，而是让真实设备人工验收从“可交接”推进到“有执行记录、可复盘、可继续补证据”。

## OKR 映射

- Objective 4 KR5：用户验收标准从 review handoff 推进到人工评审执行记录，能说明当前是否 blocked、为什么 blocked、下一步证据请求是什么。
- Objective 4 KR7：手机端 UI 的真实设备/PWA/production app 验收链路增加 review execution checklist、review result/status、evidence items readiness、operator/reviewer notes、blocked reason、next evidence request、redaction/source boundary 和 `not_proven`。
- Objective 5：本轮不推进云中转/OSS/CDN 产品化，因为当前没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他 Objective 5 外部材料。
- Objective 1/2/3：本轮不推进硬件、导航或真实送达，因为没有 WAVE ROVER/HIL、Nav2/fixed-route、任务复盘或真实 delivery 材料。

## KR 拆解或更新

- KR-A：`mobile/web` 首屏新增或派生 `mobile_real_device_review_execution`、`mobile_real_device_review_execution_summary`、`mobile_real_device_review_execution_package`。
- KR-B：review execution panel 展示 execution checklist、review result/status、evidence items readiness、operator notes、reviewer notes、blocked reason、next evidence request、redaction status、source boundary、ACK-not-delivery 和 `not_proven`。
- KR-C：copy package 必须过滤敏感字段，不包含 token、Authorization、OSS AK/SK、root password、DB/queue URL、raw ROS topic、`/cmd_vel`、serial、baudrate、WAVE ROVER、本地路径、traceback、checksum、complete artifact 或 raw robot response。
- KR-D：缺真实设备行为、production app、真实 PWA install prompt/user choice 或 O5 外部材料时，Start Delivery、Confirm Dropoff、Cancel 必须继续 fail closed。
- KR-E：Robot remote bridge/protocol tests 证明 `mobile_real_device_review_execution*` 是 metadata-only，不触发 collect、dropoff、cancel、ACK、cursor、terminal ACK、production readiness、HIL、dropoff/cancel success 或 delivery success。
- KR-F：Product closeout 只在 A/B 证据成立后谨慎更新 Objective 4；Objective 5 没有外部材料则保持约 68%。

## 本轮核心抓手

核心抓手是从 `mobile_real_device_review_handoff*` 派生人工评审执行包。review execution 必须把“材料已交接”变成“执行状态可见、blocker 可复盘、下一步证据请求明确”，但不新增控制放行语义。

必须保留的产品边界：

- `review_executed`、`ready_for_review`、`accepted_for_review` 或 execution-ready 只表示人工评审执行记录存在，不等于真实设备验收通过。
- ACK、HTTP accepted、receipt、intake package、decision package、review handoff package、review execution package 仍只是 accepted/processing/support metadata，不是 delivery success。
- 缺真实设备材料、production app 或真实 PWA install prompt/user choice 时，Start / Confirm / Cancel 继续 fail closed。
- Objective 5 外部证据缺失时，不把本轮 Objective 4 software proof 计入 Objective 5 completion。

## 需要做什么

1. Full-stack 在 `mobile/web`、fixture、mobile unit test、`mobile/README.md` 和 `docs/product/mobile_user_flow.md` 中增加 review execution checklist/status/package。
2. Robot 在 remote bridge/protocol tests 和 `docs/interfaces/ros_contracts.md` 中增加 `mobile_real_device_review_execution*` metadata-only response fence。
3. Product 在 A/B 之后核对证据，更新 `OKR.md`、`docs/process/okr_progress_log.md` 和 sprint closeout，严格区分 software proof、真实设备证据、Objective 5 外部证据、HIL 和 delivery success。

## 优先级和验收口径

- P0：review execution package 可复制，字段 phone-safe，敏感字段被过滤。
- P0：UI 可展示 checklist 执行状态、review result/status、evidence items readiness、operator/reviewer notes、blocked reason、next evidence request、redaction/source boundary、ACK-not-delivery 和 `not_proven`。
- P0：缺真实手机、production app、真实 PWA install prompt/user choice 时，Start / Confirm / Cancel 继续 fail closed。
- P0：Robot fence 证明 review execution metadata 不进入 command、ACK、cursor、terminal ACK、production readiness、HIL、dropoff/cancel success 或 delivery success。
- P1：Product closeout 明确 `software_proof_docker_mobile_real_device_review_execution_gate` 不是真实手机设备、真实 PWA prompt、Objective 5 外部材料、HIL 或 delivery success。

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
- 本轮成功后也只能证明 Docker/local mobile software proof + Robot metadata-only fence；不能提升 Objective 5，也不能把 review execution 写成真实验收完成。

## 需要创建或更新的 sprint 文档

本阶段已创建或计划创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

执行后必须更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
