# Sprint 2026.05.14_11-12 Mobile Field Trial Runbook Execution Gate - PRD

## 用户价值和产品北极星

用户价值：现场试跑人员需要一份手机端可执行清单，明确下一次真实手机/production app/PWA install prompt/user choice/offline/touch/visual/material redaction 应该怎么跑、记录什么、哪些材料必须脱敏、哪些结果仍然是 `not_proven`。这能减少现场材料返工，也避免把 ACK、HTTP accepted、review package 或 copy package 误认为 delivery success。

产品北极星：手机端持续靠近真实用户可执行的现场验收链路，但所有 Docker/local 产物必须保持 `safe_to_control=false`、`accepted_processing_only_not_delivery_success`、`not_proven` 和 whitelist-only copy。

## OKR 映射

- Objective 4：推进手机用户体验与低成本量产边界，把“现场试跑证据复核”升级为“现场试跑执行清单 / runbook execution package”。
- Objective 5：当前最低约 68%，但缺真实外部材料。本轮不推进 O5 completion，不声明真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration。
- Objective 1/2/3：本轮不改硬件、Nav2/fixed-route、task orchestrator 或 HIL，不提升真实硬件/导航/送达完成度。

## KR 拆解或更新

- O4 KR1：手机端主入口继续保持普通用户可理解的现场流程，不要求 SSH、ROS2、串口或硬件知识。
- O4 KR5：现场执行清单必须用 phone-safe 文案解释“能记录什么”和“不能控制什么”。
- O4 KR7：补齐真实手机现场试跑前的执行包，覆盖 real device、production app、PWA install prompt、user choice、offline、touch、visual、material redaction。
- O5 KR：仅保留缺口说明；没有真实外部材料时不新增 O5 进度 claim。

## 本轮核心抓手

统一采用 package family：`mobile_real_device_field_trial_runbook_execution*`。

最小产物应包括：

- `mobile_real_device_field_trial_runbook_execution`
- `mobile_real_device_field_trial_runbook_execution_summary`
- `mobile_real_device_field_trial_runbook_execution_copy`

证据边界为 `software_proof_docker_mobile_real_device_field_trial_runbook_execution_gate`。该边界只证明 Docker/local `mobile/web` 能生成 phone-safe 现场执行清单和 copy package，并由 Robot metadata-only fence 证明不会触发控制语义。

## 需要做什么

### Task A Full-stack

在 `mobile/web` 首屏新增“现场试跑执行清单”panel。该 panel 必须：

- 生成或消费 `mobile_real_device_field_trial_runbook_execution*` package。
- 覆盖真实设备类型、production app 观察、PWA install prompt、user choice、offline reload、touch target、visual issue、material redaction、operator/support notes。
- 展示 `safe_to_control=false`、`ack_semantics=accepted_processing_only_not_delivery_success`、`not_proven`、`software_proof_docker_mobile_real_device_field_trial_runbook_execution_gate`。
- copy package 只能 whitelist-only，不包含 token、Authorization、OSS AK/SK、DB/queue URL、credential-bearing URL、raw ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER 参数、本地路径、traceback、checksum、完整 artifacts、raw robot response 或 robot/internal technical fields。
- Start Delivery、Confirm Dropoff、Cancel 继续由既有 command safety、readiness、operation log、action feedback 等 gate 控制；本 package 不授予控制权限。

### Task B Robot

在 remote bridge/protocol 测试中新增 metadata-only family 围栏。必须证明：

- `mobile_real_device_field_trial_runbook_execution*` 不是 `trashbot.remote.v1` command envelope。
- 单独出现该 metadata family 不触发 backend action、ACK POST、cursor advance/persistence、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。
- mixed payload 中若同时包含有效 `trashbot.remote.v1` command envelope，只执行该 valid-command envelope，runbook execution metadata 不改变 command 语义。
- `docs/interfaces/ros_contracts.md` 明确该 family 是 phone/support metadata，不是 robot command、ACK、cursor、terminal result 或 production readiness grant。

### Task C Product Closeout

A/B 完成后更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

收口时必须确认 Objective 5 是否仍缺真实外部材料；若仍缺，只允许谨慎评估 Objective 4，不上调 Objective 5。

## 优先级和验收口径

P0：Task A 与 Task B 并行完成，且两者都用 targeted/fenced validation 证明新 package 可生成、可复制、phone-safe、metadata-only、fail-closed。

P1：Task C 完成 sprint closeout、OKR 进度和 progress log，文案必须清楚说明本轮只是 `software_proof_docker_mobile_real_device_field_trial_runbook_execution_gate`。

验收通过必须同时满足：

- `mobile/web` 有首屏“现场试跑执行清单”panel。
- copy package 含 `safe_to_control=false`、`accepted_processing_only_not_delivery_success`、`not_proven` 和 whitelist-only copy。
- Robot tests 证明 metadata-only family 不触发控制/ACK/cursor/terminal/prod/HIL/dropoff/cancel/delivery success。
- 文档同步到 `mobile/README.md`、`docs/product/mobile_user_flow.md`、`docs/interfaces/ros_contracts.md`。
- Sprint closeout 和 OKR 只写软件证据边界，不写真实手机、真实云、HIL 或 delivery success。

## 责任 Engineer

- User Touchpoint Full-Stack Engineer：Task A。
- Robot Platform Engineer：Task B。
- Product Manager / OKR Owner：Task C。

## 风险、阻塞和证据链

- O5 stop rule：没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration，不能继续堆 O5 本地 metadata。
- Docker-only：当前主机不能证明真实 iPhone/Android、production app、真实 PWA install prompt/user choice、真实云、真实 4G/SIM、WAVE ROVER、HIL 或真实 delivery。
- 产品风险：执行清单如果措辞过强，容易被误读为“现场试跑已通过”。所有 UI、copy、docs 和 closeout 必须保留 `not_proven` 与 ACK 非 delivery success。
- 工程风险：Robot metadata-only fence 必须覆盖 mixed valid-command，避免 metadata family 被误解析为 command envelope。
