# Sprint 2026.05.14_03-04 Mobile Real Device Evidence Intake Gate - Pre Start

## Sprint Type

sprint_type: epic

本轮是跨 Full-stack 与 Robot 的 epic sprint。目标不是再刷新本机 Chromium browser proof，而是为真实 iPhone/Android、production app、真实 PWA install prompt/user choice 的验收材料建立 phone-safe 导入、生成、归档和判定入口。

## 用户价值和产品北极星

北极星：普通手机用户不需要懂 SSH、ROS2、串口、日志路径或云端内部配置，也能把真实手机上的验收材料交给产品和工程团队判断下一步是否能放行动作。

用户价值：

- 验收人员能在手机/PWA 首屏生成或导入真实设备材料包，而不是靠聊天截图散落交接。
- 支持人员能看到 iPhone/Android、浏览器、viewport、display-mode、PWA install prompt/user choice、production app readiness、截图/URL 摘要和 `not_proven`，且材料已脱敏。
- 工程侧能把真实设备材料识别为支持/验收 metadata，不会误触发 Start Delivery、Confirm Dropoff、Cancel、ACK、cursor 或 delivery success。
- Product 能在后续 closeout 中明确区分 `software_proof_docker_mobile_real_device_evidence_intake_gate` 与真实手机设备验收通过。

## 背景证据

- `OKR.md` 4.1 更新时间为 2026-05-14 02:14。Objective 5 约 68%，是最低 Objective；Objective 4 约 79%。
- `OKR.md` 第 6 节明确：只有拿到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 之一，才应继续推进 Objective 5 completion。
- 本轮仍没有外部 O5 材料，且当前主机口径是“本机没有真实硬件，只有docker”。
- 最新 sprint `sprints/2026.05.14_02-03_mobile-current-pwa-browser-proof-refresh/final.md` 建议：若仍没有 O5 外部材料，不要继续本地 O5 metadata depth，优先把 current PWA proof 带到真实 iPhone/Android 或 production app/PWA prompt 验收。
- 近期 `00-01`、`01-02`、`02-03` 已有 handoff session、PWA install prompt evidence、current PWA local Chromium browser proof；当前缺口是“真实设备验收材料如何被安全导入/归档/判定”。

## OKR 映射

- 主目标：Objective 4 KR5、KR7。手机端用户验收标准和真实手机/PWA 设备验收材料进入可复现、可脱敏、可判定的产品路径。
- 关联目标：Objective 5。只保留真实公网/4G/OSS/CDN/production DB/queue 等 O5 外部材料缺口，不用本轮 Docker/local 软件入口上调 O5。
- 非目标：Objective 1/2/3。本轮不改 WAVE ROVER、UART、Nav2/fixed-route、task_orchestrator、真实 dropoff/cancel 或真实 delivery。

## KR 拆解

1. 定义真实设备验收材料包 schema：`trashbot.mobile_real_device_evidence_intake.v1` 和 summary/package 兼容命名。
2. 定义证据边界：`software_proof_docker_mobile_real_device_evidence_intake_gate`。
3. 明确材料字段白名单：iPhone/Android、browser、viewport、display-mode、PWA install prompt/user choice、production app readiness、截图/URL 摘要、redaction、`not_proven`。
4. 明确材料黑名单：token、Authorization、OSS AK/SK、root password、DB/queue URL、ROS topic、`/cmd_vel`、serial、WAVE ROVER 参数、本地路径、traceback、checksum、完整 artifact、raw robot response。
5. 明确动作边界：材料 intake package 是验收/支持 metadata，不是 command、ACK、cursor、production readiness、HIL 或 delivery success。

## 本轮核心抓手

建立“真实设备材料入口”的产品和工程合同：Full-stack 负责手机/PWA 首屏导入或生成 phone-safe package；Robot 负责 metadata-only compatibility fence，确保该材料不会进入机器人控制语义。

## 团队分工

- Product Manager / OKR Owner：维护本 sprint 的 `pre_start.md`、`prd.md`、`tech-plan.md`，定义用户价值、OKR 映射、验收口径和证据边界。
- User Touchpoint Full-Stack Engineer（Full-stack）：实现 `mobile/web` 首屏真实设备材料 intake 面板、复制/导入 package、fixture 和 targeted mobile tests，同步 `docs/product/mobile_user_flow.md` 与 `mobile/README.md`。
- Robot Platform Engineer（Robot）：补齐 operator gateway / remote bridge metadata-only fence 与 targeted tests，同步 `docs/interfaces/ros_contracts.md`。

## 风险、阻塞和证据链

- 本轮只有 Docker/local 软件入口，不证明真实手机设备、真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 或真实 delivery。
- 如果后续拿不到真实设备材料，本轮只能把 intake gate 建好，不能把 Objective 4 直接判成真实设备验收通过。
- 如果导入/复制内容未严格脱敏，会破坏 phone-safe contract；这是本轮最高产品风险。
- 如果 Robot fence 不充分，metadata 可能被误解成控制或 ACK，需要 targeted tests 明确拒绝。

## 需要创建或更新的 sprint 文档

- 当前创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- Engineer 完成后必须更新：`tech-done.md`。
- Product closeout 必须更新：`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。
