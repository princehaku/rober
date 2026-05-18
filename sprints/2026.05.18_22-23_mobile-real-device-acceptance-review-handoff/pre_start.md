# Sprint 2026.05.18_22-23 Mobile Real Device Acceptance Review Handoff - Pre Start

## 1. Sprint 声明

- sprint_type: epic
- 启动时间：2026-05-18 22:00 Asia/Shanghai
- 主题：`mobile_real_device_field_trial_acceptance_review_handoff`
- 目标 Objective：Objective 4 手机用户体验与低成本量产边界。
- 证据边界：`software_proof_docker_mobile_real_device_field_trial_acceptance_review_handoff_gate`，必须保持 `not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. 用户价值和产品北极星

北极星仍是普通手机用户可用的低成本 ROS2 自主垃圾投递机器人。上一轮 `mobile_real_device_field_trial_acceptance_review_decision*` 已经能把真机现场验收材料转成复核决策，但还缺一个可交给 owner / 现场执行者的 handoff packet：谁负责补材料、补什么、如何保持同一 safe `evidence_ref`、哪些内容不能被解释成真实手机通过。

本轮用户价值不是放开控制，而是把复核结果变成可执行的现场交接材料。普通用户仍不会看到 raw JSON、ROS topic、串口、路径、凭证或底层硬件细节；Start Delivery、Confirm Dropoff、Cancel 继续 fail-closed。

## 3. 近期 PR / 评审证据

- `OKR.md` 4.1 显示 Objective 5 约 68%，数字最低；但仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser external proof，O5 stop rule 继续成立。
- Objective 1 约 81%，仍缺真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report；PR #5 相关 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 真实材料也不可得。
- PR #4 已合并，电梯 assisted delivery 已进入主链；但 18-19 与 19-20 已连续消费同一真实 route/elevator field-material blocker，20-21 已明确停止第三次本地 wrapper。
- PR #5 review 指出 `production_hardware_boundary` 默认硬件集与 mandatory 2D LiDAR / ToF baseline 矛盾、OKR lowest narrative 曾与表格不一致、mandatory sensor assumptions 缺 `docs/vendor/` source；本轮不修改硬件事实，不把 O4 handoff 写成 PR #5 材料已补齐。
- 最新 sprint `sprints/2026.05.18_21-22_mobile-real-device-acceptance-review-decision/final.md` 完成 O4 `mobile_real_device_field_trial_acceptance_review_decision*` fail-closed review decision，仍不证明真实 iPhone/Android、production app、真实 PWA prompt/user choice、delivery success 或 O5 external proof。

## 4. 本轮核心抓手

把上一轮 review decision 结果包装成 `mobile_real_device_field_trial_acceptance_review_handoff*`，让现场 owner 能拿到明确的补证据清单、交接对象、复跑命令摘要、safe copy 和禁止升级边界。该 handoff packet 是下一次真实手机验收的执行入口，不是验收通过证明。

## 5. Owner 和并行执行意图

- Product Manager / OKR Owner：负责本 sprint 前置规划、收口文档、OKR / progress log 保守更新口径。
- User Touchpoint Full-Stack Engineer：主责 UI / fixture / test / product flow，新增手机端只读 handoff panel 和对应前端围栏。
- Robot Platform Engineer：主责 diagnostics metadata-only safe alias，把 handoff summary 安全透出给 diagnostics / mobile 消费，不新增运动控制。

本轮至少 2 个 Engineer 并行：Full-stack 和 Robot 文件范围互不重叠，Product 只做 closeout 与 OKR，不抢实现。

## 6. 前置阻塞和不做事项

- 不推进 Objective 5：当前主机只有 Docker，没有公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/cutover 真实材料。
- 不推进 Objective 1：没有真实 WAVE ROVER/UART/HIL、真实反馈日志或 PR #5 2D LiDAR / ToF 实物材料。
- 不继续 PR #4 route/elevator 本地 wrapper：同一真实现场材料 blocker 已连续消费，继续包装会违反同一 Blocker 重复消费红线。
- 不放开 Start Delivery、Confirm Dropoff、Cancel；不把 ACK、fixture、review decision 或 handoff 写成真实手机验收通过。

## 7. 需要创建或更新的 sprint 文档

本轮已创建并完成前置三文档：

- `sprints/2026.05.18_22-23_mobile-real-device-acceptance-review-handoff/pre_start.md`
- `sprints/2026.05.18_22-23_mobile-real-device-acceptance-review-handoff/prd.md`
- `sprints/2026.05.18_22-23_mobile-real-device-acceptance-review-handoff/tech-plan.md`

执行完成后必须由 Product closeout 更新，不得预生成：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
