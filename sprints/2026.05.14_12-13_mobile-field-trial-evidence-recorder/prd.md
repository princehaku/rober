# Sprint 2026.05.14_12-13 Mobile Field Trial Evidence Recorder - PRD

## 用户价值和产品北极星

用户价值：真实手机现场试跑人员需要一个结构化证据记录入口，把 production app/PWA prompt/user choice/offline/touch/visual/material redaction 等人工观察记录下来，能展示、复制和归档，同时不会泄露凭证、不会夹带 raw robot response、不会把 ACK 或记录包误解为 delivery success。这能降低现场材料返工，帮助后续 Product closeout 判断哪些仍是 `not_proven`。

产品北极星：手机端逐步靠近普通用户真实验收链路，但所有 Docker/local 和人工记录产物必须保持 `safe_to_control=false`、`ack_semantics=accepted_processing_only_not_delivery_success`、`not_proven`、whitelist-only copy 和 Robot metadata-only 边界。

## OKR 映射

- Objective 4：推进手机用户体验与低成本量产边界，把“现场试跑执行清单”升级为可记录真实手机/production app/PWA prompt/user choice/offline/touch/visual/material redaction 观察的 evidence recorder。
- Objective 5：当前最低约 68%，但缺真实外部材料。本轮不推进 O5 completion，不声明真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration。
- Objective 1/2/3：本轮不改硬件、Nav2/fixed-route、task_orchestrator 或 HIL，不提升真实硬件/导航/送达完成度。

## KR 拆解或更新

- O4 KR1：手机最小流程继续面向普通用户，不要求 SSH、ROS2、串口或硬件知识；现场观察记录必须能在手机/PWA 表面理解。
- O4 KR5：用户验收标准从“知道失败时该怎么做”继续推进到“知道哪些现场证据已记录、哪些仍未证明”。
- O4 KR7：补齐真实手机现场试跑的记录入口，覆盖真实设备、production app、PWA install prompt、user choice、offline、touch、visual、material redaction。
- O5 KR：仅保留缺口说明；没有真实公网/4G/OSS/CDN/DB/queue/worker 材料时不新增 O5 进度 claim。

## 本轮核心抓手

统一采用 package family：`mobile_real_device_field_trial_evidence_record*`。

最小产物应包括：

- `mobile_real_device_field_trial_evidence_record`
- `mobile_real_device_field_trial_evidence_record_summary`
- `mobile_real_device_field_trial_evidence_record_copy`
- `mobile_real_device_field_trial_evidence_record_archive`

证据边界为 `software_proof_docker_mobile_real_device_field_trial_evidence_record_gate`。该边界只证明 Docker/local `mobile/web` 能记录、展示、复制/归档 phone-safe 现场观察，并由 Robot metadata-only fence 证明不会触发控制语义。

## 需要做什么

### Task A Full-stack

在 `mobile/web` 首屏新增或推进“现场证据记录”入口。该入口必须：

- 生成或消费 `mobile_real_device_field_trial_evidence_record*` package。
- 允许结构化记录真实设备类型、OS/browser、production app observed、PWA install prompt observed、user choice、offline reload observed、touch target issue、visual issue、material redaction status、operator note、support note。
- 展示 record summary、copy package 和 archive package，便于现场材料被复制到后续 sprint closeout。
- 固定 `safe_to_control=false`、`ack_semantics=accepted_processing_only_not_delivery_success`、完整 `not_proven` 和 `software_proof_docker_mobile_real_device_field_trial_evidence_record_gate`。
- copy/archive 只能 whitelist-only，不包含 token、Authorization、OSS AK/SK、DB/queue URL、credential-bearing URL、raw ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER 参数、本地路径、traceback、checksum、完整 artifacts、raw robot response、raw intake JSON 或 robot/internal technical fields。
- Start Delivery、Confirm Dropoff、Cancel 继续由既有 command safety、cloud/device/browser readiness、handoff session、operation log、action feedback 等 gate 控制；本 record 不授予控制权限。

### Task B Robot

在 remote bridge/protocol 测试和接口文档中新增 metadata-only family 围栏。必须证明：

- `mobile_real_device_field_trial_evidence_record*` 不是 `trashbot.remote.v1` command envelope。
- 单独出现该 metadata family 不触发 backend action、ACK POST、cursor advance/persistence、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。
- mixed payload 中若同时包含有效 `trashbot.remote.v1` command envelope，只执行该 valid-command envelope，evidence record metadata 不改变 command 语义。
- `docs/interfaces/ros_contracts.md` 明确该 family 是 phone/support metadata，不是 robot command、ACK、cursor、terminal result、production readiness grant、HIL 或真实送达证据。

## 优先级和验收口径

P0：Task A 与 Task B 并行完成，且两者都用 targeted/fenced validation 证明新 record 可生成、可展示、可复制/归档、phone-safe、metadata-only、fail-closed。

P1：实现后 Product Owner 完成 sprint closeout、OKR 进度和 progress log，文案必须清楚说明本轮只是 `software_proof_docker_mobile_real_device_field_trial_evidence_record_gate`。

验收通过必须同时满足：

- `mobile/web` 有首屏现场证据记录入口。
- record/copy/archive package 含 `safe_to_control=false`、`accepted_processing_only_not_delivery_success`、`not_proven` 和 whitelist-only copy。
- Robot tests 证明 metadata-only family 不触发控制、ACK、cursor、terminal、production readiness、HIL、dropoff/cancel completion 或 delivery success。
- 文档同步到 `mobile/README.md`、`docs/product/mobile_user_flow.md`、`docs/interfaces/ros_contracts.md`。
- Sprint closeout 和 OKR 只写软件证据边界，不写真实手机通过、真实云通过、HIL 或 delivery success。

## 责任 Engineer

- User Touchpoint Full-Stack Engineer：Task A，runtime role id `full-stack-software-engineer`。
- Robot Platform Engineer：Task B，runtime role id `robot-software-engineer`。
- Product Manager / OKR Owner：实现后只做阶段验收、sprint closeout、OKR 与 evidence boundary 核对。

## 风险、阻塞和证据链

- O5 stop rule：没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration，不能继续堆 O5 本地 metadata。
- Docker-only：当前主机不能证明真实 iPhone/Android、production app、真实 PWA install prompt/user choice、真实云、真实 4G/SIM、WAVE ROVER、HIL 或真实 delivery。
- 产品风险：证据记录入口如果措辞过强，容易被误读为“现场试跑已通过”。所有 UI、copy、docs 和 closeout 必须保留 `not_proven`、`safe_to_control=false` 与 ACK 非 delivery success。
- 工程风险：Robot metadata-only fence 必须覆盖 metadata-only 和 mixed valid-command，避免 record family 被误解析为 command envelope。
- 材料风险：人工观察可能包含截图路径、URL、token 或内部错误信息；copy/archive 必须采用 whitelist-only 字段，不保存原始敏感材料。

## 需要创建或更新的 sprint 文档

- 已创建本 sprint 的 `pre_start.md`、`prd.md`、`tech-plan.md`。
- 实现完成后更新 `tech-done.md`。
- 阶段验收后更新 `side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。
