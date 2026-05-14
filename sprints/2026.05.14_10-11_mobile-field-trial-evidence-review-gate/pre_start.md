# Sprint 2026.05.14_10-11 Mobile Field Trial Evidence Review Gate - Pre Start

## Sprint 类型

- sprint_type: epic
- 目录：`sprints/2026.05.14_10-11_mobile-field-trial-evidence-review-gate/`
- 本轮目标：新增真实设备现场试跑证据复核链路，形成 `mobile_real_device_field_trial_review*` phone-safe package。
- 本轮边界：`software_proof_docker_mobile_real_device_field_trial_review_gate`

## 上轮输入

上轮 `2026.05.14_09-10_mobile-real-device-field-trial-package` 已完成 `software_proof_docker_mobile_real_device_field_trial_package_gate`。其核心结果是：`mobile/web` 能生成真实设备现场试跑包，采集 phone-safe runtime metadata 和人工 observation fields，并保持 `safe_to_control=false`、`ack_semantics=accepted_processing_only_not_delivery_success`、`not_proven`。

Robot 侧已补 `mobile_real_device_field_trial_package*` metadata-only / mixed valid-command 围栏，证明该 package 不触发 collect、confirm_dropoff、cancel、ACK POST、cursor advance/persistence、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。

## OKR 当前事实

- `OKR.md` 4.1 显示 Objective 5：云中转 + OSS/CDN 数据通路产品化约 68%，是当前最低 Objective。
- Objective 5 当前缺少真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 等外部材料。
- 本机当前只有 macOS + Docker/local browser proof 能力，不能提供真实公网、4G/SIM、OSS/CDN live traffic、production DB/queue/worker 或真实手机设备证据。
- 按 stop rule，本轮不继续堆 Objective 5 本地 metadata；转向 Objective 4 的真实设备现场试跑材料复核链路。

## 本轮用户价值和产品北极星

用户价值：现场试跑材料不能只被“收集”，还必须能被复核。现场人员或支持同学需要一份 phone-safe review package，明确哪些材料已经可进入验收，哪些仍是 `not_proven`，哪些材料因脱敏、缺失或口径不合规不能作为真实设备/production app/PWA install prompt 证据。

产品北极星：手机端从“能发起/能复制材料”推进到“能复核现场材料是否足够支撑下一步验收”，但不把 ACK、HTTP accepted、package copy、review pass 或 metadata-only response 包装成 delivery success。

## 本轮核心抓手

新增 `mobile_real_device_field_trial_review*` evidence review gate，消费上一轮 `mobile_real_device_field_trial_package*` 或等价人工输入，输出：

- 真实设备材料复核状态：real device observed、iPhone/Android behavior、production app observed、PWA install prompt observed、user choice observed。
- 体验材料复核状态：offline reload、touch target issue、visual issue、viewport/display-mode/service worker hints。
- 材料安全状态：redaction status、phone-safe copy whitelist、禁止泄露 URL/token/credential/raw path/robot control metadata。
- 证据边界：`software_proof_docker_mobile_real_device_field_trial_review_gate`。
- 控制边界：继续 `safe_to_control=false`，ACK 语义继续 `accepted_processing_only_not_delivery_success`。
- 缺口边界：完整保留 `not_proven`，尤其是真实手机设备、production app、真实 PWA install prompt/user choice、O5 外部材料、Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff/cancel completion 和真实 delivery。

## Owner 和分工

- User Touchpoint Full-Stack Engineer：实现 `mobile/web` review gate UI、review package 生成/复制、测试和 `docs/product/mobile_user_flow.md` 同步。
- Robot Platform Engineer：补 `mobile_real_device_field_trial_review*` metadata-only / mixed valid-command 围栏，确保 review package 不触发机器人控制语义。
- Product Manager / OKR Owner：收口 sprint 文档、OKR 证据边界和产品文档一致性；本轮计划阶段不修改 `OKR.md` 或 closeout 文件。

## 预期验收证据

- 手机端可生成/复制 `mobile_real_device_field_trial_review*` package。
- Review package 能列出真实设备、production app、PWA install prompt、user choice、offline、touch、visual、material redaction 的复核状态。
- 所有输出保持 `safe_to_control=false`、`accepted_processing_only_not_delivery_success`、`not_proven`。
- Robot metadata-only fence 证明 review package 不触发控制、ACK、cursor、terminal ACK、production readiness、HIL 或 delivery success。
- 文档明确本轮是 Docker/local mobile software proof，不是真实设备验收、Objective 5 外部 proof、HIL 或 delivery success。

## 风险和阻塞

- 真实 iPhone/Android、production app、真实 PWA install prompt/user choice 仍需要外部现场材料，本轮只能复核材料 shape 和 phone-safe 状态。
- Objective 5 的真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue/worker 仍无法在本机 Docker 环境产生。
- 如果现场材料缺少截图/录屏/URL 来源/人工 observation，review gate 必须输出 `not_proven` 或 missing，不得输出 pass。
- Review pass 只能代表材料可进入下一步人工验收，不代表 delivery success 或机器人任务闭环。

## 本轮不做

- 不修改 Objective 5 外部 proof gate。
- 不声明真实手机设备、production app、真实 PWA install prompt/user choice 已通过。
- 不启用远程控制；继续 `safe_to_control=false`。
- 不把 ACK、HTTP accepted、package copy、review package 或 metadata-only response 写成 delivery success。
- 不修改 `OKR.md`、`tech-done.md`、`side2side_check.md` 或 `final.md`。
