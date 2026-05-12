# Sprint 2026.05.13_00-01 Phone Offline Resume Gate - PRD

## 状态

- 阶段：prd
- 创建时间：2026-05-13 00:01 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主线 Objective：O5 手机体验与量产边界
- Evidence boundary：目标为 `software_proof_docker_phone_offline_resume_gate`

## 1. 用户价值和产品北极星

用户价值：当手机本地 fallback 入口离线、恢复连接、等待 robot status 或等待 ACK 时，普通用户应能在首屏看到可执行解释：能不能继续、为什么不能点发车、下一步是等待恢复、刷新、打开 Diagnostics/Support Handoff，还是人工接管。

产品北极星：普通用户只用手机完成垃圾交付。本轮把“手机离线/恢复”从静态 offline shell 推进为 O5 readiness gate，让本地 fallback 在异常网络状态下也不暴露工程细节、不误导用户、不误触发机器人动作。

## 2. OKR 映射

- O5 / KR1：手机端最小流程新增离线/恢复状态解释，覆盖连接设备、查看状态、异常处理。
- O5 / KR4：远程诊断最小数据包继续通过 Diagnostics/Support Handoff 提供 phone-safe 摘要。
- O5 / KR5：普通用户不接触命令行、ROS2、串口或 raw JSON，也能理解失败时该怎么做。
- O5 / KR6：电梯/人工接管等异常态继续通过 phone-safe copy 解释，不暴露 raw ROS topic。
- O5 / KR7：fallback 手机首屏在离线/恢复场景下仍保持主路径可读、按钮状态明确、Diagnostics/Support Handoff 可进入。

O6 只作为 remote readiness、ACK、production recovery 等已有摘要的消费来源。本轮不提升 O6，也不声明真实云、4G、OSS/CDN 或生产灾备。

## 3. KR 拆解或更新

本轮不修改 `OKR.md`，但实现完成后 final 可按以下口径评估 O5：

- KR1 增量：`phone_offline_resume_readiness` 把 offline、status stale、pending ACK、resume required、manual takeover 等状态进入手机最小流程。
- KR4 增量：Diagnostics/Support Handoff 在 primary actions blocked 时仍可访问，并输出 redacted support summary。
- KR5 增量：用户文案明确“离线不能发控制命令”“恢复后等待最新状态/ACK”“ACK 不代表送达成功”。
- KR7 增量：fallback 首屏/API 在 Docker/local proof 下覆盖 offline/resume，不声明 production app 或真实手机浏览器验收。

## 4. 本轮核心抓手

新增一个 phone-facing readiness gate：`trashbot.phone_offline_resume_readiness.v1`。

建议字段：

- `schema`: `trashbot.phone_offline_resume_readiness.v1`
- `schema_version`: `1`
- `evidence_boundary`: `software_proof_docker_phone_offline_resume_gate`
- `connection_state`: `online|offline|recovering|status_stale|waiting_ack|manual_takeover_required|support_required`
- `can_resume`: 恢复后是否允许继续观察或进入下一步，不等于允许发控制命令
- `primary_actions_enabled`: Start/Confirm/Cancel 的聚合 gate 结果
- `support_entry_enabled`: Diagnostics/Support Handoff 是否可进入
- `next_action`: `wait_reconnect|refresh_status|wait_ack|open_diagnostics|contact_support|manual_takeover|continue_observing`
- `safe_phone_copy`: 面向普通用户的短文案
- `recovery_hint`: 恢复建议
- `ack_semantics`: ACK 只是 accepted/processing evidence
- `not_proven`: 不证明真实手机、production app、真实云/4G、OSS/CDN 实流量、Nav2/fixed-route、WAVE ROVER、HIL 或 delivery success

## 5. 需要做什么

主责 `full-stack-software-engineer` 需要完成：

- 在 operator gateway status builder 中增加 `phone_offline_resume_readiness`，并嵌入 `/api/status.phone_readiness.phone_offline_resume_readiness`。
- 在 `/api/diagnostics` 中暴露同口径 phone-safe summary，确保 support 能复现离线/恢复阻塞原因。
- 更新 fallback HTML 首屏，显示 offline/resume safe copy、recovery hint、ACK 语义和 not-proven boundary。
- 确保 service worker/offline shell 不缓存或伪造 `/api/*`、command routes、ACK routes、diagnostics 或非 GET 控制请求。
- 将 command safety 与 offline/resume gate 合并：Start/Confirm/Cancel 被阻断时，Diagnostics/Support Handoff 仍可打开。
- 同步更新 `docs/product/mobile_user_flow.md` 与接口文档中相关 phone status contract。

`robot-software-engineer` 只在接口语义受影响时补兼容性围栏：

- remote bridge metadata-only offline/resume summary 不得触发 robot action。
- summary 不得污染 `trashbot.remote.v1` command/status/ACK envelope。
- pending ACK、stale status、manual takeover 不得推进 cursor 或误判 delivery success。

## 6. 优先级和验收口径

P0：

- `/api/status`、`/api/status.phone_readiness`、`/api/diagnostics` 三处同口径输出 `phone_offline_resume_readiness`。
- Offline shell 明确不能发控制命令，Start/Confirm/Cancel disabled。
- Recovering/status stale/pending ACK 场景下，primary actions disabled，Diagnostics/Support Handoff accessible。
- ACK 文案明确 accepted/processing only，不等于送达成功。
- Phone-safe redaction 覆盖 token、Authorization、OSS AK/SK、root password、DB/queue URL、ROS topic、`/cmd_vel`、serial、baudrate、local path、checksum、complete artifact。
- 所有结论保持 `software_proof_docker_phone_offline_resume_gate` 边界。

P1：

- 本地 browser acceptance fixture 覆盖 mobile viewport 上 offline/resume 文案无重叠、按钮 hit area 和 disabled 状态。
- Diagnostics support bundle 能引用 offline/resume blocking reason。

不做：

- 不做 production app、账号系统、推送通知、真实手机设备验收。
- 不做真实云/4G、HTTPS/TLS、公网入口、OSS/CDN 实流量。
- 不做 Nav2/fixed-route、WAVE ROVER、串口、HIL 或真实送达验证。
- 不新增硬件，不修改 vendor/hardware 配置。

## 7. 对应责任 Engineer

- 主责：`full-stack-software-engineer`
- 协作围栏：`robot-software-engineer`
- 不参与本轮实现：`hardware-engineer`、`autonomy-engineer`

## 8. 风险、阻塞和证据链

- 离线 shell 不能伪造机器人状态；它只能说明无法确认当前状态并提示恢复。
- Resume gate 必须消费真实 status freshness 和 ACK pending 语义，不能靠页面状态猜 ready。
- Support copy 必须是 phone-safe summary，不能把 diagnostics 原文或内部路径给普通用户。
- 当前证据只能是 local/Docker software proof；真实手机、真实云、真实硬件和 HIL 必须列入 not-proven。

## 9. 需要创建或更新的 sprint 文档

本轮已创建或需要创建：

- `sprints/2026.05.13_00-01_phone-offline-resume-gate/pre_start.md`
- `sprints/2026.05.13_00-01_phone-offline-resume-gate/prd.md`
- `sprints/2026.05.13_00-01_phone-offline-resume-gate/tech-plan.md`

实现后必须继续更新：

- `sprints/2026.05.13_00-01_phone-offline-resume-gate/tech-done.md`
- `sprints/2026.05.13_00-01_phone-offline-resume-gate/side2side_check.md`
- `sprints/2026.05.13_00-01_phone-offline-resume-gate/final.md`

实现后还必须同步更新 `docs/product/mobile_user_flow.md`。如新增或调整 schema 字段，需同步更新 `docs/interfaces/ros_contracts.md` 或现有对应接口文档。
