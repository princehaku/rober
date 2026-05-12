# Sprint 2026.05.13_07-08 Mobile Operation Log Gate - PRD

## 背景

Objective 4 当前约 58%，低于 Objective 5 约 59%，是 live `OKR.md` 里最低且可在 Docker-only 环境继续推进的目标。最近两个 O4 sprint 已建立 `mobile/web/` PWA 静态入口和 Start 前 destination + loaded confirmation gate，但手机用户在"查看状态 -> 处理异常 -> 交接支持"上的闭环仍薄。

本轮产品目标是用 Docker/local software proof 建立手机端 operation log gate：把 phone-safe 操作、状态、异常、ACK 语义和支持交接摘要显示在手机端，同时保证这些 metadata 不进入机器人动作语义。

## 用户价值和产品北极星

用户价值：用户遇到等待、失败、离线、人工接管或 ACK 未完成时，可以在手机上看到最近事件、阻塞原因、恢复建议和支持交接摘要，不需要理解 ROS2、云队列、串口或硬件细节。

产品北极星：普通手机用户只通过手机理解任务状态和下一步动作；系统内部的 command/status/ack、diagnostics 和 robot compatibility fence 必须服务于这个手机体验，而不是让用户暴露在内部协议面前。

## 目标用户

- 普通家庭或物业操作员：只使用手机，不会 SSH、ROS2、串口、日志检索。
- 售后或远程支持：需要一份脱敏、可复制、可定位当前问题的支持摘要。
- 工程团队：需要确认 operation-log metadata 不会被 robot bridge 当作动作、ACK 或 cursor 进展。

## OKR 映射

- Objective 4 KR1：补齐手机最小流程中的"查看状态 -> 处理异常"段。
- Objective 4 KR4：把最近任务状态、失败原因、关键日志引用和支持摘要以 phone-safe 方式组织。
- Objective 4 KR5：普通用户不接触命令行或硬件调试，也能处理异常或请求支持。
- Objective 4 KR7：手机端中文优先、主路径清晰、按钮 fail-closed、支持入口可见。
- Objective 5 guardrail：未来可复用云中转状态，但本轮不声明真实云、4G 或 OSS/CDN live traffic。
- Objective 2 guardrail：operation log 只解释任务状态，不代表真实送达或导航成功。

## KR 拆解或更新

### KR-A：手机端操作/状态事件日志

- `mobile/web/` 显示 phone-safe operation log 面板。
- 面板按时间或优先级展示最近状态、用户操作、blocked 原因、pending ACK、manual takeover、offline/recovering 等事件。
- 事件来源只消费既有 phone-safe `/api/status`、`/api/diagnostics` 或 fixture 字段；前端不发明机器人状态。

### KR-B：异常恢复提示

- 每条阻塞或异常事件提供中文 `safe_phone_copy` 或 `recovery_hint`。
- Start/Confirm/Cancel 仍遵守 `command_safety` 和 legacy permission 双 gate，事件日志不能让被 block 的动作变绿。
- ACK 文案必须保持 accepted/processing evidence only。

### KR-C：支持交接摘要入口

- 手机端提供 Support Handoff 或操作日志摘要入口。
- 摘要可复用现有 `phone_support_bundle`、`phone_readiness`、`phone_task_flow_readiness`、`phone_offline_resume_readiness`、`voice_prompt_readiness` 等 phone-safe summary。
- 摘要不得暴露 token、Authorization header、OSS AK/SK、root password、DB/queue URL、raw ROS topic、`/cmd_vel`、串口、波特率、WAVE ROVER 参数、路径、traceback、checksum 或完整 artifact。

### KR-D：Robot compatibility fence

- operation-log metadata-only response 不触发 backend action。
- 不 POST ACK。
- 不推进 cursor，不持久化 cursor。
- protocol normalization 剥离 command envelope 外的 operation-log metadata。

### KR-E：文档同步与 evidence boundary

- `mobile/README.md`、`docs/product/mobile_user_flow.md` 写清 `software_proof_docker_mobile_operation_log_gate`。
- `docs/interfaces/ros_contracts.md`、`docs/product/remote_4g_mvp.md` 写清 metadata-only fence 与不触发 robot action 的边界。
- Product 收口时更新 `OKR.md` 与 `docs/process/okr_progress_log.md`，但本 planning 阶段不改这些文件。

## 本轮核心抓手

以"状态可解释 + 异常可恢复 + 支持可交接"推进 Objective 4，而不是继续堆云端后端深度。当前环境没有真实手机和真实云，所以本轮必须把证据限定为 Docker/local 软件证明。

## 需要做什么

1. full-stack-software-engineer 在 `mobile/web/` 增加 operation log UI、fixture、smoke tests 和手机产品文档。
2. robot-software-engineer 增加 remote bridge / protocol metadata-only compatibility fence，并同步接口/远程 MVP 文档。
3. Product owner 在 worker 返回后做 side-by-side 验收，确认 OKR 口径、证据边界和剩余风险，再更新 `OKR.md` 与进度日志。

## 优先级和验收口径

P0：

- operation log 面板在 fixture smoke 中可见。
- 异常/blocked/pending ACK/offline/manual takeover 至少有一条可读恢复提示。
- Support Handoff 或日志摘要入口可见且不触发控制动作。
- Start/Confirm/Cancel 不因 operation log metadata 而绕过 command safety。
- Robot compatibility fence 通过。

P1：

- mobile README 和产品文档补齐路线图状态。
- interface docs 明确 operation-log metadata-only response 的 robot fence。
- Product closeout 明确不声明真实手机、production app、真实云/4G、OSS/CDN live traffic、HIL 或真实送达。

## 对应责任 Engineer

- full-stack-software-engineer：手机端 operation log UI、fixture、static smoke、mobile/product docs。
- robot-software-engineer：remote bridge/protocol compatibility fence、interface docs、remote MVP docs。
- Product Manager / OKR Owner：后续验收、`OKR.md`、`docs/process/okr_progress_log.md`、sprint closeout。

## 非目标

- 不做真实手机设备或真实浏览器验收。
- 不做 production app、账号系统、推送通知或 native 壳。
- 不做真实云、4G/SIM、OSS/CDN live traffic、production DB/queue。
- 不做 ROS2 runtime、Nav2/fixed-route、WAVE ROVER、串口、HIL 或真实送达。
- 不把 operation log 当成 action/ACK/cursor/delivery success 证据。

## 风险、阻塞和需要补齐的证据链

- 真实手机/浏览器与 PWA install prompt 仍需后续有设备时补证。
- 真实云/4G 与 OSS/CDN live traffic 仍需后续 Objective 5 sprint 补证。
- 真实机器人状态和送达结果仍依赖 O1/O2/O3 的硬件、路线和 HIL 证据。
- 本轮需要补齐的证据链是 local fixture smoke + robot compatibility fence + scoped docs diff check，且必须标注 `software_proof_docker_mobile_operation_log_gate`。
