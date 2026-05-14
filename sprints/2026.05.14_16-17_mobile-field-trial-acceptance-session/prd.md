# Sprint 2026.05.14_16-17 Mobile Field Trial Acceptance Session - PRD

sprint_type: epic

## 用户价值和产品北极星

手机端是普通用户和现场验收人员唯一应接触的操作入口。当前 `mobile/web` 已有 field-trial package、review、runbook execution、evidence record、evidence verdict、retest execution，并在上一轮完成 current PWA local Chromium-family browser proof。剩余缺口不是继续堆本地 O5 metadata，而是把这些材料组织成现场可以按步骤执行、记录、复核和复制的验收会话。

本轮北极星是：现场人员拿起手机就能进入一个“真实设备现场验收会话”，看到本次会话目标、必须观察的真实设备/production app/PWA prompt/offline/touch/visual/redaction 项、来自 evidence verdict 和 retest execution 的缺口、会话状态和下一步材料请求；同时所有控制动作继续 fail closed，所有 copy 都是 whitelist-only，并且明确 `accepted_processing_only_not_delivery_success` 与 `not_proven`。

## OKR 映射

- Objective 4：直接推进。对应 KR1/KR5/KR7：手机最小流程、普通用户验收标准、手机端美观可用与主流尺寸适配。本轮把现场验收链条产品化为可执行会话，而不是只留下文档和 artifact。
- Objective 5：不推进 completion。当前仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration；本轮只记录 stop rule，不把 acceptance session 写成 O5 external proof。
- Objective 1/2/3：不推进 completion。Robot 侧只围栏 metadata，不证明底盘、导航、任务闭环、真实投放或 HIL。

## KR 拆解或更新

1. KR-A：手机端新增 `mobile_real_device_field_trial_acceptance_session*` 会话包。
   - schema 建议为 `trashbot.mobile_real_device_field_trial_acceptance_session.v1`。
   - summary/copy 字段建议为 `mobile_real_device_field_trial_acceptance_session_summary` 和 `mobile_real_device_field_trial_acceptance_session_copy`。
   - 本地证据边界统一为 `software_proof_docker_mobile_real_device_field_trial_acceptance_session_gate`。
2. KR-B：会话必须串起上一轮材料链。
   - 输入优先来自 `mobile_real_device_field_trial_retest_execution*`。
   - 可引用 `mobile_real_device_field_trial_evidence_verdict*`、`mobile_current_pwa_field_trial_browser_proof*`、`mobile_real_device_field_trial_evidence_record*`。
   - 缺失输入时只能派生 blocked-by-design 会话，不得发明真实验收结果。
3. KR-C：会话 checklist 必须覆盖真实现场观察项。
   - real device observed。
   - production app observed。
   - PWA install prompt observed。
   - install/user choice observed。
   - offline reload observed。
   - touch target issue。
   - visual issue。
   - material redaction status。
   - operator/support note。
4. KR-D：安全和语义边界必须保持。
   - `safe_to_control=false`。
   - `ack_semantics=accepted_processing_only_not_delivery_success`。
   - `not_proven` 必须包括真实 iPhone/Android、production app、真实 PWA install prompt/user choice、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL、dropoff/cancel completion、delivery success。
   - copy package 必须 whitelist-only，不包含 token、Authorization、OSS AK/SK、DB/queue URL、credential-bearing URL、raw ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER 参数、本地路径、traceback、checksum、完整 artifacts、raw robot responses、raw intake JSON 或 robot/internal 技术字段。
5. KR-E：Robot metadata-only fence 覆盖新 family。
   - metadata-only payload 不触发 collect/dropoff/cancel。
   - 不触发 ACK POST、cursor advance/persistence、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。
   - mixed valid-command 场景只执行合法 `trashbot.remote.v1` envelope，acceptance session metadata 不改变 action、target、idempotency、ACK 或 cursor。

## 本轮核心抓手

把 “field trial browser proof / retest execution / evidence verdict” 组合成一个现场可执行 session，而不是再新增一层无法执行的材料摘要。这个 session 的成功标准是“现场人员能按手机页面走完采证流程并复制安全材料”，不是“机器人真的送达”或“真实手机验收已经通过”。

## 需要做什么

- Full-stack：在 `mobile/web` 首屏新增 acceptance session 面板，生成/消费 `mobile_real_device_field_trial_acceptance_session*`，更新 fixture/test 和 mobile/product docs。
- Robot：新增/更新 remote bridge/protocol metadata-only fence，保证 acceptance session family 对机器人侧没有控制副作用，并更新 ROS contract。
- Product：工程完成后补齐 `tech-done.md`、`side2side_check.md`、`final.md`，并在 final 中复核 O5 stop rule 与 O4 进度边界。

## 优先级和验收口径

P0：手机端会话包必须可从 retest execution / evidence verdict / browser proof 派生 blocked-by-design session，并展示会话状态、材料缺口、观察 checklist、safe copy、ACK-not-delivery 和 `not_proven`。

P0：Start Delivery、Confirm Dropoff、Cancel 继续 fail closed；acceptance session 不得新增控制 grant，不得调用 `/api/collect`、`/api/dropoff/confirm`、`/api/cancel`、ACK 或 cursor 路径。

P0：Robot metadata-only fence 证明新 family 不触发控制、副作用或成功语义；mixed valid-command 只执行合法 command envelope。

P1：`docs/product/mobile_user_flow.md`、`mobile/README.md`、`docs/interfaces/ros_contracts.md` 同步更新，避免 Product/Support 把 session package 误读为真实手机验收或 delivery success。

P2：验证保持围栏：复用现有 mobile unittest、py_compile、remote bridge targeted unittest、required `rg` 和 scoped `git diff --check`；不新增大批测试。

## 对应责任 Engineer

- `full-stack-software-engineer`：Task A，负责 `mobile/web` acceptance session、fixture/test、mobile/product 文档和手机端 evidence boundary。
- `robot-software-engineer`：Task B，负责 remote bridge/protocol metadata-only fence 和 ROS contract 文档。
- Product Owner：只负责本 planning、后续验收口径、sprint 留档和 OKR 边界复核，不写产品代码或测试代码。

## 风险、阻塞和需要补齐的证据链

- 本轮不会产生真实手机验收；真实 iPhone/Android、production app、真实 PWA install prompt/user choice 仍需外部现场材料。
- 本轮不会产生 Objective 5 external proof；真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration 仍缺。
- 本轮不会产生 HIL、Nav2/fixed-route、WAVE ROVER、dropoff/cancel completion 或 delivery success。
- 需要补齐的证据链：后续现场人员用真实手机执行 session，提供截图/观察结果/production app/PWA prompt/user choice/offline/touch/visual/redaction 材料后，才能进入真实设备验收判定。

## 需要创建或更新的 sprint 文档

- 已创建/本阶段创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 工程完成后：`tech-done.md` 记录 Task A/B 实际改动、验证结果、失败定位和剩余风险。
- 验收收口后：`side2side_check.md` 对照 PRD/tech-plan；`final.md` 更新 OKR 边界和下一步。
