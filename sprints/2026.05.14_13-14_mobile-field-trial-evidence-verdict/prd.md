# Sprint 2026.05.14_13-14 Mobile Field Trial Evidence Verdict - PRD

sprint_type: epic

## 用户价值

现场人员已经可以填写、复制和归档现场证据记录，但 Product/Support 仍需要人工判断哪些字段缺失、是否可进入真实设备复核、下一轮应补什么材料。本轮把这个判断做成手机端可见的 verdict package，降低试跑材料返工。

## 产品北极星

普通手机用户和现场支持人员能围绕同一份 phone-safe 证据包协作，同时系统不把 Docker/local、人工记录或 ACK 元数据误写成真实交付、真实设备验收或云生产就绪。

## OKR 对齐

- Objective 5 仍是最低约 68%，但当前主机没有真实外部云/4G/OSS/DB/queue 材料，不能推进 O5 completion。
- Objective 1 真实硬件/HIL 也被本机无硬件锁死。
- 本轮转向 Objective 4：继续补真实手机/production app/PWA prompt/user choice 验收链路中的可执行材料复核步骤。

## 需求

1. 手机端新增“现场证据 verdict”首屏 panel。
2. Panel 从 `mobile_real_device_field_trial_evidence_record*` 或本地归档派生 verdict。
3. Verdict 至少表达：
   - `verdict_status`
   - `ready_for_manual_review`
   - `missing_evidence`
   - `retest_request`
   - `material_redaction_status`
   - `safe_to_control=false`
   - `ack_semantics=accepted_processing_only_not_delivery_success`
   - `evidence_boundary=software_proof_docker_mobile_real_device_field_trial_evidence_verdict_gate`
   - `not_proven`
4. 复制包只包含 whitelist-only phone-safe 字段，不包含 token、Authorization、OSS AK/SK、DB/queue URL、ROS topic、`/cmd_vel`、serial、WAVE ROVER、本地路径、traceback、checksum、raw robot response 或完整附件。
5. Robot 侧测试证明 verdict metadata-only family 不会触发控制语义或推进 cursor。

## 非目标

- 不连接真实手机、真实 production app、真实 PWA install prompt 或真实云。
- 不提升 O5；不证明公网、TLS、4G、OSS/CDN、production DB/queue。
- 不改变 `/api/collect`、`/api/dropoff/confirm`、`/api/cancel` 控制语义。
- 不新增大测试套件；只更新围栏测试。

## 验收口径

- Full-stack static smoke 能看到 verdict panel、schema、boundary、whitelist copy、fail-closed 文案。
- Robot compatibility fence 能证明 verdict family 是 metadata-only。
- 文档同步说明 verdict 不是真实设备验收、production app readiness、PWA prompt success、O5 external proof、HIL 或 delivery success。
