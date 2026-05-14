# Sprint 2026.05.14_18-19 Mobile PWA Install Prompt Evidence Export - Pre Start

sprint_type: epic

## 启动时间

- 2026-05-14 18:00 Asia/Shanghai
- Sprint 目录：`sprints/2026.05.14_18-19_mobile-pwa-install-prompt-evidence-export/`
- 目标证据边界：`software_proof_docker_mobile_pwa_install_prompt_evidence_export_gate`

## 上轮输入证据

- 最新 sprint：`sprints/2026.05.14_17-18_mobile-pwa-install-prompt-event-capture/final.md`
- 上轮完成：`mobile_pwa_install_prompt_event_capture*`，手机端已经监听 `beforeinstallprompt`、`beforeinstallprompt.userChoice`、`appinstalled`，并生成 whitelist-only 事件证据包。
- 上轮 Robot 围栏：metadata-only family 不触发 collect/dropoff/cancel、ACK POST、cursor 持久化、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。
- 上轮剩余风险：没有真实 iPhone/Android device behavior、production app、真实 PWA prompt/userChoice 现场验收。

## OKR 当前切换原因

当前 `OKR.md` 4.1 显示 Objective 5 约 68%，是最低完成度；Objective 4 约 94%。但 Objective 5 当前缺的是真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration。本机只有 Docker，无真实外部材料，按 stop rule 不再堆 O5 local metadata。

本轮切到 Objective 4：继续推进真实手机验收前的材料化能力，把上轮捕获到的 PWA install prompt 事件状态导出成 phone-safe、whitelist-only、可复制/下载的现场验收材料包。该材料包只帮助现场验收人员复测和交接，不把软件包写成真实手机验收。

## 用户价值和产品北极星

北极星仍是让普通手机用户不接触 SSH、ROS2、串口或硬件调试，也能完成送垃圾任务并知道失败时如何处理。本轮用户价值不是开放机器人控制，而是让现场验收人员可以从手机页面拿到一份干净、可复制、可下载、可复测的 PWA 安装提示证据材料。

成功后的用户价值：

- 验收人员可以明确看到 install prompt capture、userChoice、appinstalled 的当前状态。
- 材料包只包含安全白名单字段，避免泄露 token、DB/queue URL、ROS topic、`/cmd_vel`、串口、WAVE ROVER、local path、traceback 或完整 artifact。
- 缺真实设备或真实 prompt 时，材料仍显示 `not_proven`，不会误导成真实验收通过。
- Start Delivery、Confirm Dropoff、Cancel 继续 fail closed，不因证据导出能力启用任何控制。

## 本轮核心抓手

围绕 `mobile_pwa_install_prompt_evidence_export*` 建立一条可交给 Full-Stack 与 Robot 并行实现的 Epic sprint：

- Task A `full-stack-software-engineer`：在 `mobile/web/` 导出 phone-safe PWA install prompt evidence export 包，支持复制/下载，保持主操作 fail closed。
- Task B `robot-software-engineer`：在 remote bridge / protocol 侧添加 metadata-only fence，证明 export family 不能触发 robot control、ACK、cursor、delivery result 或 readiness grant。
- Task C `product-okr-owner`：收口 sprint 文档、OKR 进度口径和证据边界，确认 docs 同步状态；如实现改动触发产品文档差异，要求工程任务补齐 `docs/product/mobile_user_flow.md`。

## 风险、阻塞和证据缺口

- Objective 5 的真实外部证据仍阻塞：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration。
- Objective 4 仍缺真实 iPhone/Android device behavior、production app、真实 PWA prompt/userChoice 现场验收。
- 本轮目标只产出 `software_proof_docker_mobile_pwa_install_prompt_evidence_export_gate`，不是真实手机验收、不是真实 PWA prompt 通过、不是 delivery success。
- 任何 export/copy/download 材料必须 whitelist-only；不得包含 credential、内部 robot payload、完整 artifact 或硬件细节。
- 本轮不涉及 WAVE ROVER、ESP32、Orange Pi、UART、波特率、引脚、电压、底盘协议或机械尺寸；若后续实现触及硬件边界，必须先读 `docs/vendor/VENDOR_INDEX.md`。

## 需要创建或更新的 sprint 文档

本启动阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实现完成后必须补齐 Epic 链路：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

