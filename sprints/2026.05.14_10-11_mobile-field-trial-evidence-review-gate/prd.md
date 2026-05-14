# Sprint 2026.05.14_10-11 Mobile Field Trial Evidence Review Gate - PRD

## 用户价值和产品北极星

真实设备现场试跑需要的不只是“提交材料”，而是“复核材料能不能支撑验收”。上一轮已经有 `mobile_real_device_field_trial_package*`，本轮要让手机端继续生成一份 `mobile_real_device_field_trial_review*` phone-safe package，帮助现场、支持和 Product 明确材料状态。

产品北极星：普通用户和现场同学可以在手机入口看到真实设备现场材料的复核结论，知道哪些材料已记录、哪些仍缺失、哪些因脱敏或口径不满足只能标记为 `not_proven`。系统必须继续避免把 ACK、HTTP accepted、copy package、review package 或 backend metadata 当成 delivery success。

## OKR 映射

- Objective 4：建立手机用户体验与低成本量产边界。本轮补真实设备现场试跑后的 evidence review gate，推进手机主路径验收材料链路。
- Objective 5：云中转 + OSS/CDN 数据通路产品化仍约 68%，当前最低，但缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue/worker 等外部材料。本轮按 stop rule 不继续堆本地 O5 metadata。
- Objective 1/2/3：本轮不推进硬件、真实 Nav2/fixed-route、WAVE ROVER、HIL 或真实 delivery。

## KR 拆解

1. KR4 手机端真实设备材料复核：新增 review gate，消费 field trial package，列出真实设备、production app、PWA install prompt、user choice、offline、touch、visual 和 material redaction 状态。
2. KR7 手机端 UI 可用性：review panel 必须 phone-first、文案中文优先、状态可扫读、按钮可点击区域不低于既有标准，并保持主操作 fail-closed。
3. KR9 证据边界和支持交接：生成 `mobile_real_device_field_trial_review*` phone-safe package，明确 `software_proof_docker_mobile_real_device_field_trial_review_gate`、`safe_to_control=false`、`accepted_processing_only_not_delivery_success`、`not_proven`。

## 本轮核心抓手

### Review package

新增 package family：

- `mobile_real_device_field_trial_review`
- `mobile_real_device_field_trial_review_summary`
- `mobile_real_device_field_trial_review_copy`

建议 schema：

- `schema=trashbot.mobile_real_device_field_trial_review.v1`
- `evidence_boundary=software_proof_docker_mobile_real_device_field_trial_review_gate`
- `safe_to_control=false`
- `ack_semantics=accepted_processing_only_not_delivery_success`
- `not_proven=[...]`

### Review status

Review package 至少覆盖：

- real device evidence：真实设备是否有材料、设备类型、OS/browser、iPhone/Android behavior 是否仍缺。
- production app evidence：production app observed、入口来源、是否只是 local PWA。
- PWA install evidence：install prompt observed、user choice observed、display-mode 状态。
- offline evidence：offline reload observed、service worker hint、offline shell hint。
- touch/visual evidence：touch target issue、visual issue、viewport/DPR/orientation 摘要。
- material safety：redaction status、phone-safe whitelist、禁止包含 token、Authorization、credential-bearing URL、raw local path、串口、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。

## 需要做什么

### Full-stack

- 在 `mobile/web` 新增 evidence review panel，消费上一轮 field trial package 或页面内现有 observation fields。
- 生成 `mobile_real_device_field_trial_review*` package 和 copy text。
- 更新 mobile tests，覆盖 review package schema、boundary、copy、not_proven、ACK 语义和 fail-closed 状态。
- 同步 `mobile/README.md` 和 `docs/product/mobile_user_flow.md`。

### Robot

- 扩展 remote bridge protocol / worker tests，把 `mobile_real_device_field_trial_review*` 纳入 metadata-only family。
- 增加 mixed valid-command 围栏：同一 payload 中有 review metadata 和有效 `trashbot.remote.v1` command 时，只允许 command envelope 触发既有控制链路。
- 文档同步 `docs/interfaces/ros_contracts.md`，说明 review package 不触发 control、ACK、cursor、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。

### Product

- 本轮计划阶段创建 `pre_start.md`、`prd.md`、`tech-plan.md`。
- 实现完成后再由 Product 更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`；本轮计划任务不修改这些文件。
- Product 收口时必须确认 `docs/` 已随代码同步，且证据边界没有写成真实设备或 O5 外部 proof。

## 优先级和验收口径

- P0：Review package 必须生成并可复制，包含 `mobile_real_device_field_trial_review*`、`software_proof_docker_mobile_real_device_field_trial_review_gate`、`safe_to_control=false`、`accepted_processing_only_not_delivery_success`、`not_proven`。
- P0：Robot metadata-only fence 必须证明 review package 不触发控制语义。
- P1：Review status 必须覆盖真实设备、production app、PWA install prompt、user choice、offline、touch、visual、material redaction。
- P1：文档必须同步说明本轮不是真实手机设备验收，不是 Objective 5 外部 proof，不是 HIL，不是 delivery success。
- P2：UI 状态命名和 copy 保持 phone-safe，避免出现“已送达”“真实通过”等成功暗示。

## 风险、阻塞和证据链

- 本轮无法补真实 iPhone/Android、production app、真实 PWA install prompt/user choice、4G/SIM、公网 HTTPS/TLS、OSS/CDN live traffic、production DB/queue/worker。
- Review gate 只能复核材料状态；没有真实材料时必须输出 missing 或 `not_proven`。
- 现场截图、录屏、真实浏览器或 production app 入口、安装提示和用户选择仍需后续现场提供。
- ACK、HTTP accepted、copy package、review package 和 metadata-only backend response 仍必须是 accepted/processing/support metadata，不得作为 delivery success。
