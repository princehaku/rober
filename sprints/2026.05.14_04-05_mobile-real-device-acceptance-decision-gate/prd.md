# Sprint 2026.05.14_04-05 Mobile Real Device Acceptance Decision Gate - PRD

## 用户价值和产品北极星

本轮要解决的问题不是“再收一次材料”，而是“收上来的真实手机/PWA/production app 材料能否进入产品验收”。普通用户和支持同学需要看到清楚结论：当前材料是否足够进入评审、还缺哪些证据、哪些字段因为安全或语义问题被拒绝、下一步要补什么。

北极星保持不变：手机是普通用户唯一入口，用户不理解 ROS2、串口、raw JSON 或云端内部设施也能完成任务并在失败时获得可执行解释。本轮把材料判定做成 phone-safe 决策，而不是把本地 Docker/PWA proof 或 ACK 误写成真实设备通过。

## 产品问题

上一 sprint 已经把真实设备材料 intake、redaction 和 phone-safe package 做成软件入口，但缺少下一步产品判定层：

- intake package 能说明“收到什么”，但不能说明“是否足以验收”。
- 真实 iPhone/Android、PWA install prompt、production app readiness、截图/URL/browser/viewport 材料需要统一 decision schema。
- 决策 metadata 必须继续被 Robot 侧忽略，不能影响 command envelope、ACK、cursor、delivery result 或 production readiness。

## OKR 映射

- Objective 4 KR5：用户验收标准从“能收集材料”推进到“能判定材料是否足以进入真实手机验收”。
- Objective 4 KR7：围绕 iPhone/Android 主流尺寸、真实设备行为、PWA prompt/user choice、production app readiness 和首屏可交互证据建立 decision gate。
- Objective 5：本轮不推进 O5 completion。没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/migration 材料，不能把 O4 决策 metadata 算作 O5 进度。

## KR 拆解或更新

本轮拟形成的 Objective 4 子 KR：

1. `mobile_real_device_acceptance_decision` 能表达材料判定状态：`accepted_for_review`、`blocked_missing_evidence`、`rejected_unsafe_or_unredacted`、`not_proven`。
2. 决策输出必须包含 blocker list、next required evidence、safe phone copy、ACK 语义、evidence boundary 和 redaction status。
3. 决策 package 必须只包含 phone-safe metadata，不包含 token、Authorization、OSS AK/SK、DB/queue URL、raw ROS topic、`/cmd_vel`、serial、WAVE ROVER、本地路径、traceback、checksum、完整 artifact 或 raw robot response。
4. Robot metadata-only fence 必须证明 acceptance decision 不触发 collect、confirm_dropoff、cancel、ACK POST、cursor advance/persistence、terminal ACK、production readiness、HIL、dropoff/cancel success 或 delivery success。

## 本轮核心抓手

把上一轮 intake 的“材料导入”升级为“材料判定”。手机首屏要能展示当前 decision、blocker、下一份需要补齐的证据、是否仍为 `not_proven`，并让支持人员复制 redacted decision package。

## 功能范围

### In Scope

- `mobile/web` 消费或派生 `mobile_real_device_acceptance_decision`、`mobile_real_device_acceptance_decision_summary`、`mobile_real_device_acceptance_decision_package`。
- 支持从顶层、`phone_readiness`、`/api/diagnostics`、本地导入 intake package 派生决策。
- 显示 phone-safe 决策状态、blocker list、next required evidence、redaction status、safe-to-control=false 时的主操作禁用原因。
- 保留 `not_proven`，明确真实设备、production app、PWA prompt/user choice、real HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff/cancel/delivery 未证明。
- Robot 侧只增加 metadata-only fence，不改实际控制路径。
- 同步 `docs/product/mobile_user_flow.md` 和 `docs/interfaces/ros_contracts.md`。

### Out of Scope

- 不宣称真实 iPhone/Android、production app 或 PWA install prompt 已通过。
- 不新增云端生产 DB/queue、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic 或 production worker/migration。
- 不改硬件、串口、WAVE ROVER、Orange Pi、launch、Nav2/fixed-route、delivery action。
- 不新增真实设备自动化执行要求；真实设备材料由外部人工或后续验收流程提供。

## 优先级和验收口径

- P0：决策 schema 和 UI 必须 fail closed。缺材料、材料不安全、redaction 未通过、仍缺真实设备/PWA/production app 时，Start/Confirm/Cancel 不得被该 metadata 打开。
- P0：Robot fence 必须证明 metadata-only response 不污染 command、ACK、cursor、success 或 production readiness。
- P1：决策 package 可复制，且只包含 phone-safe metadata。
- P1：文档必须同步解释 `software_proof_docker_mobile_real_device_acceptance_decision_gate` 的证据边界。
- P2：产品 closeout 后再由 Product 更新 `OKR.md`；未拿到真实设备通过材料时，Objective 4 最多只能谨慎说明软件决策门完成，Objective 5 不调整。

## 对应责任 Engineer

- User Touchpoint Full-Stack Engineer：手机/PWA decision gate、fixture、unit tests、mobile README、`docs/product/mobile_user_flow.md`。
- Robot Platform Engineer：remote bridge/protocol metadata-only fence、`docs/interfaces/ros_contracts.md`。
- Product Manager / OKR Owner：本 sprint 收口、OKR 边界、progress log、验收判定。

## 风险、阻塞和证据链

- 阻塞：本机无真实手机设备、真实 production app、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或真实硬件。
- 证据链要求：每个 positive-looking decision 都必须同时带 `not_proven` 和 next required evidence，除非材料明确包含真实设备/PWA/production app 的外部证据。
- 安全风险：任何未脱敏材料不得进入 copied package 或 robot metadata。
- 语义风险：ACK、accepted、receipt、handoff、decision package 不能被写成 delivery success。

## 需要创建或更新的 sprint 文档

- 已创建规划文档：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 实现阶段必须追加：`tech-done.md`。
- 验收和收口阶段必须追加：`side2side_check.md`、`final.md`。
