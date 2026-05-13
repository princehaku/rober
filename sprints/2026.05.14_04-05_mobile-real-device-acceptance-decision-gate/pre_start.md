# Sprint 2026.05.14_04-05 Mobile Real Device Acceptance Decision Gate - Pre Start

## Sprint 类型

- sprint_type: epic
- 启动时间：2026-05-14 04:05 Asia/Shanghai
- 主目标：Objective 4 mobile real-device acceptance decision gate。
- 证据边界：`software_proof_docker_mobile_real_device_acceptance_decision_gate`。

## 用户价值和产品北极星

北极星仍是让普通手机用户不接触 SSH、ROS2、串口、云端内部配置或 raw JSON，也能完成一次送垃圾任务并知道失败时该怎么做。本轮不做真实设备通过声明，而是把上一轮已导入的真实 iPhone/Android、PWA、production app 或 observer 材料，转成 phone-safe acceptance decision、blocker list 和 next required evidence。

用户价值是减少“材料已经收到了，但产品和工程不知道能不能验收”的灰区：用户、支持人员和工程同学看到的必须是可判定状态，而不是散落截图、ACK 文案或本地浏览器 metadata 被误读成真实设备通过。

## 当前证据

- `OKR.md` 4.1 显示 Objective 5 约 68% 为最低，但第 6 节明确：没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/migration 证据时，不继续堆 O5 metadata。
- 当前主机只有 Docker/local，没有真实硬件、真实公网入口、真实 4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 材料。
- 上一 sprint `sprints/2026.05.14_03-04_mobile-real-device-evidence-intake-gate/final.md` 已完成 `software_proof_docker_mobile_real_device_evidence_intake_gate`：Full-stack 提供真实设备材料 intake/redaction/package，Robot 提供 `mobile_real_device_evidence_intake` metadata-only compatibility fence。
- Objective 4 目前约 80%，仍缺真实手机设备、真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice 和主路径真实移动设备验收。

## 本轮切换原因

Objective 5 仍是最低数字，但本机无法提供 O5 下一步真实外部材料；继续做本地 O5 metadata 会重复消费同一外部证据 blocker。按 `OKR.md` 第 6 节和上一 sprint final 建议，本轮切换到 Objective 4，把 intake gate 收到的材料变成验收决策门。

本轮不会宣称真实设备、production app 或 PWA prompt 已通过；只建立判定结构：`accepted_for_review`、`blocked_missing_evidence`、`rejected_unsafe_or_unredacted` 等 phone-safe 状态，并保留 `not_proven`。

## 本轮核心抓手

1. Full-stack：在 `mobile/web` 首屏新增或接入 `mobile_real_device_acceptance_decision`，把 intake package 转成 phone-safe decision、blocker list 和 next required evidence。
2. Robot：补充 metadata-only compatibility fence，证明 acceptance decision metadata 不会污染 command、ACK、cursor、terminal result、delivery success 或 production readiness。
3. Product：同步 `docs/product/mobile_user_flow.md`、`OKR.md`、`docs/process/okr_progress_log.md` 和本 sprint closeout，确保 Objective 4/5 进度和证据边界不混淆。

## Owner 和范围

- Product Manager / OKR Owner：本轮方向、PRD、验收口径、后续 closeout 和 OKR 边界。
- User Touchpoint Full-Stack Engineer：手机/PWA 决策面、fixture、targeted tests、mobile README 和 product docs。
- Robot Platform Engineer：remote bridge/protocol metadata-only fence 和 interface docs。
- Hardware Infra Engineer：本轮不进入实现；无 WAVE ROVER、ESP32、Orange Pi、UART、波特率、引脚、电压或机械事实改动。
- Autonomy Algorithm Engineer：本轮不进入实现；无 Nav2/fixed-route、地图、路线或 keyframe 改动。

## 风险和阻塞

- 真实设备材料如果仍缺失，本轮只能输出 `blocked_missing_evidence` 或 `not_proven`，不能提升到真实设备通过。
- 如果导入材料包含 token、Authorization、OSS AK/SK、DB/queue URL、raw robot response、ROS topic、`/cmd_vel`、serial、WAVE ROVER、local path、traceback、checksum 或完整 artifact，必须判为不安全或需要重交。
- ACK、HTTP accepted、receipt、intake package、acceptance decision package、handoff session 和 browser proof 仍只是 accepted/processing/support metadata，不是 delivery success。

## 需要创建或更新的 sprint 文档

- 本阶段创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 实现完成后必须更新：`tech-done.md`、`side2side_check.md`、`final.md`。
