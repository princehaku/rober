# Sprint 2026.05.14_17-18 Mobile PWA Install Prompt Event Capture - Pre Start

sprint_type: epic

## 启动结论

本轮启动 fresh Epic sprint：`sprints/2026.05.14_17-18_mobile-pwa-install-prompt-event-capture/`。

当前 `OKR.md` 4.1 显示 Objective 5 仍是最低完成度，约 68%；但同一节和上一轮 `sprints/2026.05.14_16-17_mobile-field-trial-acceptance-session/final.md` 都明确，Objective 5 只有拿到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 等外部材料时才应继续推进。当前本机只有 Docker，没有真实外部 O5 材料，因此本轮按 stop rule 不继续堆 O5 本地 metadata，转向 Objective 4 的下一项可推进功能：`mobile_pwa_install_prompt_event_capture*`。

核心抓手是让 `mobile/web` 静态 PWA 入口直接监听浏览器级 `beforeinstallprompt`、`appinstalled` 和 `userChoice`，生成 phone-safe、whitelist-only 的安装提示事件证据包。该证据包用于记录真实浏览器 install prompt 事件是否出现、用户选择是否发生、是否安装完成；它仍必须保持 `safe_to_control=false`、`accepted_processing_only_not_delivery_success`、`not_proven` 和 Start/Confirm/Cancel fail closed。

## 背景证据

- `OKR.md` 4.1 更新时间为 2026-05-14 16:17 Asia/Shanghai：Objective 5 约 68%，Objective 4 约 93%，Objective 1 约 75%，Objective 2/3 约 77%；其中 Objective 5 未因上一轮 local mobile software proof 上调。
- `OKR.md` 4.1 和 `final.md` 均写明：若没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration，就不要重复本地 O5 metadata depth；可转向 Objective 4 的真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice。
- 上一轮 `tech-done.md` 和 `final.md` 说明 `mobile_real_device_field_trial_acceptance_session*` 已完成现场验收会话材料链，但边界仍是 `software_proof_docker_mobile_real_device_field_trial_acceptance_session_gate`，不是真实 PWA prompt/user choice。
- 当前 `mobile/README.md` 和 `docs/product/mobile_user_flow.md` 已有 `mobile_pwa_install_prompt_evidence*` 与 `mobile_real_device_field_trial_acceptance_session*` 材料展示、复制和 not_proven 边界；它们仍要求真实 PWA install prompt/user choice 后续补齐。
- 代码证据：`rg -n "beforeinstallprompt|appinstalled|userChoice" mobile/web` 当前无命中，说明 `mobile/web` 还没有真实浏览器 PWA install prompt 事件监听。
- 当前 `docs/interfaces/ros_contracts.md` 已把 `mobile_pwa_install_prompt_evidence*` 和 `mobile_real_device_field_trial_acceptance_session*` 定义为 metadata-only，不得触发 command、ACK、cursor、HIL、dropoff/cancel completion 或 delivery success。

## 用户价值和产品北极星

产品北极星仍是：普通手机用户不接触 ROS2、SSH、串口或命令行，也能围绕手机首屏理解能不能发车、缺什么证据、失败后谁接手。

本轮用户价值是把“PWA install prompt 仍是人工记录/展示材料”推进到“手机浏览器实际事件捕获”：当真实 iPhone/Android 浏览器或本地 Chromium-family PWA 入口触发 `beforeinstallprompt`、`userChoice` 或 `appinstalled` 时，现场人员能在手机端看到事件状态、时间、display mode、用户选择和 redacted copy package。缺事件时也能明确记录 `not_proven`，避免把没有出现 prompt 的场景误写成已通过。

## OKR 映射

- Objective 4：主目标。推进 KR1/KR5/KR7，把手机端 PWA 安装提示从材料展示推进到浏览器事件捕获，为真实 iPhone/Android device behavior、production app 或真实 PWA prompt/user choice 打基础。
- Objective 5：本轮不推进 completion。当前缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration；继续本地 O5 metadata 不应提升 O5。
- Objective 1/2/3：不作为本轮目标。Robot 侧只补 metadata-only fence，证明新的 install prompt event capture family 不会触发机器人控制、HIL、Nav2/fixed-route、dropoff/cancel completion 或 delivery success。

## 本轮 Owner

- Task A `full-stack-software-engineer`：实现 `mobile_pwa_install_prompt_event_capture*` 浏览器事件监听、phone-safe whitelist-only evidence package、mobile tests 和 mobile/product 文档。
- Task B `robot-software-engineer`：更新 metadata-only fence 和接口文档，确认该 family 不会触发 command、ACK、cursor、terminal ACK、success/readiness/HIL 或 delivery success 语义。
- Task C `product-okr-owner`：工程完成后负责 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 process log 收口；本阶段不更新 OKR.md 或上一轮 closeout 文档。

## 风险和阻塞

- 没有真实 iPhone/Android、production app 或真实 PWA prompt/user choice 时，本轮只能证明本地 PWA 已具备事件监听和 phone-safe 包装能力，不能证明真实设备验收通过。
- 没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/migration；Objective 5 不应上调。
- 没有 WAVE ROVER、真实串口、Nav2/fixed-route、HIL、真实 dropoff/cancel completion 或真实 delivery；Robot fence 只证明 metadata 无副作用。
- `beforeinstallprompt` 事件受浏览器、安装状态、manifest、service worker 和用户行为影响；未触发时必须记录 blocked/not_proven，不能用 fallback 文案冒充事件证据。

## 本轮需要创建或更新的 sprint 文档

- 本阶段创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 工程完成后必须补：`tech-done.md`。
- Epic 验收收口后必须补：`side2side_check.md`、`final.md`，并由 Product closeout 更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。
