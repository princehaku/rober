# Sprint 2026.05.14_03-04 Mobile Real Device Evidence Intake Gate - PRD

## 产品目标

定义并交付 `software_proof_docker_mobile_real_device_evidence_intake_gate`：让手机/PWA 首屏支持导入或生成 phone-safe 的真实设备验收材料包 schema，用于后续真实 iPhone/Android、production app、真实 PWA install prompt/user choice 验收收口。

本轮只证明 Docker/local 软件入口、脱敏规则、首屏交互和 Robot metadata-only 围栏，不证明真实手机设备已经验收通过。

## 用户价值和产品北极星

北极星：手机是普通用户唯一入口，真实设备验收材料也应从手机/PWA 入口被安全收集、解释和交接，而不是散落在截图、聊天和未脱敏日志里。

用户价值：

- 验收人员可以按同一个 schema 提交 iPhone/Android device behavior、browser、viewport、display-mode、PWA install prompt/user choice 和 production app readiness。
- 支持人员拿到的是 redaction 后的 phone-safe package，可快速判断材料是否足够，或者哪些仍为 `not_proven`。
- 工程人员能把材料接入 tests 和 diagnostics，但不会让材料误触发机器人控制、ACK、cursor、HIL 或 delivery success。

## OKR 映射

- Objective 4 KR5：把真实手机验收标准转为可复制、可归档、可判定的材料包。
- Objective 4 KR7：服务 iPhone/Android 主流尺寸、PWA install prompt、production app readiness 的验收闭环。
- Objective 5：本轮不推进。没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration，所以 O5 保持 blocked-by-evidence，不做本地 metadata depth。

## KR 拆解或更新

1. **KR-A：Schema 与 evidence boundary**
   - Schema：`trashbot.mobile_real_device_evidence_intake.v1`。
   - Summary/package 兼容命名：`mobile_real_device_evidence_intake`、`mobile_real_device_evidence_intake_summary`、`mobile_real_device_evidence_package`，并允许同名字段嵌套在 `phone_readiness` 或 `/api/diagnostics`。
   - Evidence boundary：`software_proof_docker_mobile_real_device_evidence_intake_gate`。

2. **KR-B：材料白名单**
   - Device：platform（iPhone/Android/unknown）、model summary、OS major/minor summary。
   - Browser：browser family/version summary、viewport CSS width/height、devicePixelRatio、orientation、touch target summary。
   - PWA：display-mode、manifest/service-worker/offline shell summary、PWA install prompt status、PWA install prompt user choice。
   - App：production app readiness、entry URL safe summary、release/build safe summary。
   - Evidence：screenshot summary、URL summary、client timestamp、observer note、redaction status、`not_proven`。

3. **KR-C：Phone-safe redaction**
   - 必须过滤 token、Authorization、OSS AK/SK、root password、DB/queue URL、ROS topic、`/cmd_vel`、serial、WAVE ROVER 参数、本地路径、traceback、checksum、完整 artifact、raw robot response。
   - 复制包只保留摘要、布尔值、枚举值和短 reference。

4. **KR-D：动作与证据边界**
   - Intake package 是 support/acceptance metadata only。
   - 不能触发 Start Delivery、Confirm Dropoff、Cancel、ACK POST、cursor advance、cursor persistence、delivery success、dropoff success、cancel completed、production readiness 或 HIL。

## 本轮核心抓手

从“已有 handoff / install prompt / local browser proof”前进一步：建立真实设备材料进入系统的安全 intake gate。核心不是证明真实手机通过，而是保证真实材料进入时有统一 schema、脱敏规则、判定字段和 Robot 忽略规则。

## 需要做什么

### Full-stack

- 在 `mobile/web` 首屏增加真实设备证据导入/生成面板。
- 支持从现有 phone-safe 字段和本地浏览器 metadata 生成 blocked-by-design package。
- 支持导入一段 JSON 或由用户填写关键观察项，输出 redacted package。
- 展示 `not_proven`、redaction status、PWA install prompt/user choice、production app readiness 和 evidence boundary。
- 更新 targeted unittest、fixture、`docs/product/mobile_user_flow.md`、`mobile/README.md`。

### Robot

- 在 remote bridge / operator gateway tests 中声明并验证 intake fields 是 metadata-only。
- 兼容字段出现在 status/diagnostics/phone_readiness 中，但不触发 command、ACK、cursor、persistence 或 delivery success。
- 更新 `docs/interfaces/ros_contracts.md`。

### Product

- Engineer 返回后更新 `tech-done.md`、`side2side_check.md`、`final.md`。
- 如果 evidence boundary 达成但仍没有真实设备材料，Objective 4 只能谨慎上调软件入口能力，不得写成真实设备验收通过。
- Objective 5 只有拿到真实外部材料才调整。

## 优先级和验收口径

P0：

- `software_proof_docker_mobile_real_device_evidence_intake_gate` 出现在 UI、fixture/test、docs、Robot fence 中。
- Copy package 白名单和黑名单均有测试或文档约束。
- Start Delivery、Confirm Dropoff、Cancel 在材料缺失、blocked、not_proven 未关闭时保持 fail closed。
- Robot tests 证明 intake metadata 不触发控制语义。

P1：

- UI 能同时覆盖真实 iPhone/Android、production app、真实 PWA install prompt/user choice 的观察项。
- Package 能引用前序 handoff session、device evidence capture、PWA install prompt evidence 和 current PWA browser proof，但不能把这些引用表述为真实验收已通过。

P2：

- 后续可接入真实设备截图文件或外部 URL 存证，但本轮只允许 safe summary，不要求上传完整 artifact。

## 对应责任 Engineer

- Full-stack：User Touchpoint Full-Stack Engineer，主责手机/PWA 首屏、fixture、mobile tests、产品文档。
- Robot：Robot Platform Engineer，主责 metadata-only fence、remote bridge/operator gateway tests、接口文档。
- Product：Product Manager / OKR Owner，主责 sprint 留档、OKR 口径和最终阶段验收。

## 风险、阻塞和需要补齐的证据链

- 缺真实手机设备材料：本轮不会证明真实 iPhone/Android behavior。
- 缺 production app：`production_app_ready` 只能是 false 或 not_proven，不能靠 Docker/local PWA 推断。
- 缺真实 PWA install prompt/user choice：只能记录 observed/imported 状态，不能把 installability 或 local browser proof 写成真实 prompt。
- 缺 O5 外部材料：不能推进 Objective 5 completion。
- Redaction 漏洞：如果 package 暴露凭证、内部路径或 robot raw response，本轮不能收口。

## 需要创建或更新的 sprint 文档

- 已创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 实现后更新：`tech-done.md`。
- 验收收口：`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。
