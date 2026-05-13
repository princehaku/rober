# Sprint 2026.05.14_00-01 Mobile Device Handoff Session Gate - Pre Start

## Sprint 声明

- sprint_type: epic
- 启动时间：2026-05-14 00:01 Asia/Shanghai
- 目标 Objective：Objective 4 手机用户体验与低成本量产边界
- 统一证据边界：`software_proof_docker_mobile_device_handoff_session_gate`
- 本轮功能名：`mobile-device-handoff-session`
- 上一轮 sprint：`sprints/2026.05.13_23-24_mobile-device-evidence-capture-gate/`
- 计划状态：A/B 实现前计划；不得修改 `OKR.md`、`tech-done.md`、`side2side_check.md` 或 `final.md`

## 背景证据

`OKR.md` 4.1 显示当前完成度最低的是 Objective 5，约 68%。但 `OKR.md` 第 6 节明确要求：只有拿到至少一种真实外部材料时才继续推进 Objective 5 completion，包括真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 证据。若外部材料仍不可用，不应继续堆本地 O5 metadata depth，应转向 Objective 4 的真实 iPhone/Android device behavior、production app、真实 PWA install prompt、主路径真实移动设备验收，或继续补齐手机端设备证据包的真实设备采集证明。

`sprints/2026.05.13_17-18_o5_external-evidence-intake-gate/final.md` 已完成 Objective 5 的 `software_proof_docker_external_evidence_intake_gate`，但没有真实外部材料，因此 O5 没有上调；下一步若继续 O5 必须接入真实外部材料，否则应转向 O4 的真实手机设备/browser、production app 或 PWA install prompt 缺口。

`sprints/2026.05.13_23-24_mobile-device-evidence-capture-gate/final.md` 已完成 `software_proof_docker_mobile_device_evidence_capture_gate`，把手机设备证据采集做成 phone-safe 软件护栏。剩余风险仍是真实 iPhone/Android device behavior、production app、真实 PWA install prompt、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 和真实 delivery。

因此本轮不继续重复消费 Objective 5 外部材料 blocker，转向 Objective 4，把最新 `mobile_device_evidence_capture` 推进为面向普通用户/测试人员的“真实手机设备验收 handoff session”。

## 用户价值和产品北极星

产品北极星仍是让普通手机用户可以不用 SSH、ROS2、串口或硬件知识完成送垃圾任务，并在失败时知道如何交给支持人员继续定位。本轮的用户价值不是放行动作，而是把真实手机验收前最容易漏掉的现场信息整理成一个 phone-safe 会话包：入口 URL、步骤清单、设备/browser/PWA 观察项、证据包复制要求、ACK 语义和 not-proven 边界。

普通测试人员拿到会话包后，应能按步骤在真实手机上执行验收、复制安全证据，并清楚知道“ACK accepted”不等于送达成功，“证据包已复制”不等于真实 iPhone/Android、production app 或 PWA install prompt 已通过。

## 本轮目标

建立 `mobile_device_handoff_session`：在 `mobile/web/` 现有证据采集能力基础上，提供一个 phone-safe 的真实设备验收 handoff session，至少覆盖：

- 当前入口 URL 与 session metadata。
- 测试人员步骤清单。
- 期望设备、浏览器、PWA/display-mode/install prompt、offline shell、touch target、viewport 观察项。
- 证据包复制和提交给支持人员的要求。
- ACK/HTTP accepted/receipt 只是 accepted/processing 或 reproduction metadata，不是 delivery success。
- `not_proven` 边界：真实 iPhone/Android、production app、真实 PWA install prompt、真实云/4G、Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff/cancel/delivery。

## Owner 与并行要求

本 sprint 是 Epic，后续必须并行启动 A/B 两个 owner，C 等待 A/B 返回后收口：

- Task A Full-stack：负责 `mobile/web/` handoff session UI、fixture、targeted mobile unittest 和 `docs/product/mobile_user_flow.md` 更新。
- Task B Robot compatibility fence：负责 remote bridge/protocol metadata-only 围栏和 `docs/interfaces/ros_contracts.md` 更新，证明 handoff session 不触发 robot action、ACK、cursor 或 delivery result。
- Task C Product closeout：等待 A/B 返回后再更新 `OKR.md`、`docs/process/okr_progress_log.md` 与本 sprint `tech-done.md`、`side2side_check.md`、`final.md`。

## 范围边界

本轮只创建计划，不执行 A/B/C 实现，不修改 `OKR.md` 或 closeout 文档。

后续实现不得改硬件配置、launch 参数、WAVE ROVER、UART、底盘协议、Nav2/fixed-route、production cloud 配置或真实凭证。`mobile_device_handoff_session` 只能作为 phone/support metadata；不得因为 session 存在而放行 Start Delivery、Confirm Dropoff 或 Cancel。

## 阻塞与风险

- Objective 5 仍缺真实外部材料：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。
- Objective 4 仍缺真实设备验收材料：真实 iPhone/Android device behavior、production app、真实 PWA install prompt。
- Handoff session 只降低真实设备验收的执行成本；它本身不是验收通过证据。
- ACK、HTTP accepted、receipt、terminal confirmation、evidence package 和 handoff session 都不能写成 delivery success。
