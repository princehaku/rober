# Sprint 2026.05.14_16-17 Mobile Field Trial Acceptance Session - Pre Start

sprint_type: epic

## 启动结论

本轮启动 fresh Epic sprint：`sprints/2026.05.14_16-17_mobile-field-trial-acceptance-session/`。

当前 `OKR.md` 4.1 显示 Objective 5 仍是最低完成度，约 68%；但最新 sprint `2026.05.14_15-16_mobile-current-pwa-field-trial-browser-proof/final.md` 和 `OKR.md` 都明确，Objective 5 只有拿到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 等外部材料时才应继续推进。当前用户明确本机没有真实硬件，只有 Docker，因此本轮按 stop rule 转向 Objective 4 下一项可推进功能：`mobile_real_device_field_trial_acceptance_session*`。

核心抓手是把上一轮 field-trial browser proof、retest execution 和 evidence verdict 转成手机端可执行的现场验收会话包，让 Product/Support/现场验收人员在手机首屏能看到会话入口、验收步骤、材料缺口、观察项、复制包和边界声明。它是验收会话准备和执行辅助，不是真实手机验收结果。

## 背景证据

- `OKR.md` 4.1 更新时间为 2026-05-14 15:16 Asia/Shanghai，Objective 5 约 68%，Objective 4 约 92%，Objective 1 约 75%，Objective 2/3 约 77%。
- 最新 sprint `2026.05.14_15-16_mobile-current-pwa-field-trial-browser-proof/final.md` 已完成 `software_proof_docker_mobile_current_pwa_field_trial_browser_proof_gate`，390x844 与 768x900 local Chromium-family proof 均通过，但仍不是真实 iPhone/Android、production app、真实 PWA install prompt/user choice 或 O5 external proof。
- 当前 `docs/product/mobile_user_flow.md` 已记录 field-trial package、review、runbook execution、evidence record、evidence verdict、retest execution 和 current PWA browser proof 的 phone-safe 边界。
- 当前 `docs/interfaces/ros_contracts.md` 已将 `mobile_current_pwa_field_trial_browser_proof*` 定义为 Robot metadata-only fence，不能触发 control、ACK、cursor、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。
- 用户明确本机只有 Docker；本轮不得把 local software proof、browser proof、ACK、HTTP accepted 或 evidence package 写成真实手机验收、O5 external proof、HIL 或 delivery success。

## 用户价值和产品北极星

产品北极星仍是：普通手机用户不接触 ROS2、SSH、串口或命令行，也能围绕手机首屏理解能不能发车、缺什么证据、失败后谁接手。

本轮用户价值是把“现场复测执行”和“现场证据 verdict”从材料链条推进到一个手机端可执行的现场验收会话：现场人员能按手机首屏逐项检查真实设备、production app、PWA install prompt、user choice、offline、touch、visual、material redaction，并复制 whitelist-only 会话包给 Product/Support。会话包仍保持 `safe_to_control=false`、`accepted_processing_only_not_delivery_success`、`not_proven` 和 Robot metadata-only fence。

## OKR 映射

- Objective 4：主目标。推进 KR1/KR5/KR7，让手机端真实设备现场验收从“证据记录/复测清单”进入“可执行会话”阶段，并保留 phone-safe、fail-closed、主流尺寸和可复制验收材料边界。
- Objective 5：本轮不推进 completion。当前缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration；继续本地 O5 metadata 不应提升 O5。
- Objective 1/2/3：不作为本轮目标。Robot 侧只补 metadata-only fence，证明新的 acceptance session family 不会触发机器人控制、HIL、Nav2/fixed-route、dropoff/cancel completion 或 delivery success。

## 本轮 Owner

- Task A `full-stack-software-engineer`：实现 `mobile_real_device_field_trial_acceptance_session*` 手机端会话面板、whitelist-only copy package、产品触点文档和最小 mobile 围栏验证。
- Task B `robot-software-engineer`：实现/更新 Robot metadata-only fence，覆盖 `mobile_real_device_field_trial_acceptance_session*` family，并同步 ROS contract 文档。

## 风险和阻塞

- 没有真实 iPhone/Android、production app、真实 PWA install prompt/user choice；本轮只能产出 Docker/local mobile software proof。
- 没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/migration；Objective 5 不应上调。
- 没有 WAVE ROVER、真实串口、Nav2/fixed-route、HIL、真实 dropoff/cancel completion 或真实 delivery；Robot fence 只证明 metadata 无副作用。
- acceptance session 是现场验收会话辅助，不是验收通过判定；copy 和 UI 文案必须避免 happy path 被误读为成功闭环。

## 本轮需要创建或更新的 sprint 文档

- 本阶段创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 工程完成后必须补：`tech-done.md`。
- Epic 验收收口后必须补：`side2side_check.md`、`final.md`。
