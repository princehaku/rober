# Sprint 2026.05.20_10-11 Mobile Real Device Acceptance Handoff Review Decision - Pre Start

## 1. Sprint 类型

sprint_type: epic

本轮主题：`mobile_real_device_field_trial_acceptance_execution_handoff_review_decision`。

本轮继续 Objective 4 现场真实手机验收材料链：上一轮 `2026.05.20_09-10_mobile-real-device-acceptance-handoff-intake` 已完成 `mobile_real_device_field_trial_acceptance_execution_handoff_intake`，Robot diagnostics 与 mobile/web 可以只读展示现场验收交接回执、缺失材料、下一责任人和 rerun guidance。下一步可执行 rung 是 review decision：把 handoff intake 的回执状态复核成 `accepted`、`missing`、`rejected`、`blocked` 四类结论，并给出 next owner 与 rerun guidance。

本轮不是实机手机验收，不新增控制能力，不打开 Start Delivery、Confirm Dropoff、Cancel，不更新 OKR 或 docs/process closeout。所有结论必须保持 `software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. 用户价值和产品北极星

产品北极星仍是：普通手机用户不需要 SSH、ROS2、串口、云凭证、GitHub review 细节或硬件调试，也能看懂一次送垃圾任务是否可继续、证据缺在哪里、下一步谁负责补齐。

本轮用户价值是把“现场验收交接回执已收到”推进为“材料是否可进入下一步复跑或仍需补证据”的可判定状态。手机端和 Robot diagnostics 后续应能只读展示 review decision：哪些材料被接受、哪些材料缺失、哪些材料被拒绝、是否被真实环境 blocker 卡住、下一责任 Engineer 是谁、要按什么 rerun guidance 重新提交。这样避免把 handoff intake 或 ACK 误读成真实手机/browser 通过、真实 route/elevator field pass、HIL、dropoff/cancel completion、O5 external proof 或 delivery success。

## 3. 开工证据

- 当前 `OKR.md` 4.1 更新时间为 2026-05-20 09:48 Asia/Shanghai，最新 sprint 是 `2026.05.20_09-10_mobile-real-device-acceptance-handoff-intake`。
- Objective 5 当前约 68%，是数字最低 Objective；但真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、真实手机/browser 仍缺。当前 Docker-only host 无法提供这些外部材料，不能再堆本地 O5 metadata depth。
- Objective 1 当前约 81%；PR #5 live review thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved，Q/U 已 resolved；X 等真实 2D LiDAR / ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry，不得重复 PR #5 wrapper，也不得把 reply comment 写成 reviewer resolved。
- 最近 final `2026.05.20_09-10_mobile-real-device-acceptance-handoff-intake/final.md` 明确：`mobile_real_device_field_trial_acceptance_execution_handoff_intake` 已完成 handoff intake，但仍不是真实手机/browser、PWA prompt/userChoice、production app、O5 external proof、O1 hardware proof、HIL、route/elevator field pass、dropoff/cancel completion 或 delivery success。
- `docs/product/mobile_user_flow.md` 约束 mobile/web：手机端状态必须中文优先、phone-safe、read-only，Start Delivery / Confirm Dropoff / Cancel 只受 command safety gates 控制；真实材料链 panel 不得暴露 raw JSON、ROS topic、`/cmd_vel`、serial/UART、凭证、local path、checksum、complete artifact 或 success/control copy。

## 4. Rerank 决策

本轮不选择 Objective 5 completion：Objective 5 虽然最低，但当前有效提升需要至少一种真实外部材料，例如真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser。当前主机只有 Docker，继续 O5 local metadata 会重复消费同一外部 blocker。

本轮不选择 Objective 1 completion：PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending；真实 2D LiDAR / ToF source、receipt、采购、安装、接线、电源、标定、HIL-entry 和 WAVE ROVER/UART/HIL packet 仍缺。没有真实材料或 reviewer resolve 前，不得关闭 thread 或提升 O1。

本轮选择 Objective 4 的 review decision rung：上一轮 handoff intake 已让现场 owner 回执进入 Robot/mobile safe summary。下一步最可执行且不弱化边界的功能抓手，是把回执材料判定为 accepted / missing / rejected / blocked，并明确 next owner 与 rerun guidance。该工作推进真实手机验收材料链，但仍只作为 `software_proof_docker_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_gate`，不声称真实手机通过。

## 5. 本轮核心抓手

把 `mobile_real_device_field_trial_acceptance_execution_handoff_intake` 后的状态推进到 `mobile_real_device_field_trial_acceptance_execution_handoff_review_decision`：

- Robot Platform Engineer：后续实现 Robot diagnostics safe summary 和 fail-closed review decision 判定。
- User Touchpoint Full-Stack Engineer：后续实现 mobile/web 只读“现场验收交接复核决策”panel、fixture、copy/export whitelist 和 gating 不变测试。
- Product Owner：当前仅创建 planning 文档；实现完成后再做 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 progress log 保守 closeout。

## 6. Owner 和并行规则

本轮后续实现阶段必须并行启动 2 个工程 worker，文件范围互不重叠；Product Owner 在工程返回后负责 closeout 文档和 OKR 边界核对。

- Robot Platform Engineer：负责 ROS2 behavior diagnostics summary、review decision normalization、safe alias、fail-closed schema handling 和接口文档。
- User Touchpoint Full-Stack Engineer：负责手机端只读 panel、fixture、前端测试和 `docs/product/mobile_user_flow.md`。
- Product Owner：负责阶段验收、OKR 边界和 sprint 收口；不写产品代码和测试代码。

## 7. 风险、阻塞和证据链缺口

- Objective 5 真实外部证据仍缺：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration/cutover。
- Objective 1 / PR #5 真实硬件证据仍缺：WAVE ROVER/UART/HIL、真实 feedback / odom / imu / battery 样本、真实 2D LiDAR / ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry；`PRRT_kwDOSWB9286CJ3tX` 仍不能写成 resolved。
- Objective 4 真实手机验收仍缺：真实 iPhone/Android device behavior、production app、真实 PWA prompt/userChoice、true phone/browser acceptance。
- Objective 2 / Objective 3 真实现场证据仍缺：真实 route/elevator field pass、Nav2/fixed-route runtime log、route completion signal、现场 task record、dropoff/cancel completion、delivery result。
- 本轮所有新增状态必须保留 `software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

## 8. 需要创建或更新的 sprint 文档

本规划阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实现完成后必须继续更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

closeout 阶段才允许更新 `OKR.md` 和 `docs/process/okr_progress_log.md`；若仍无真实外部/硬件/手机材料，OKR 百分比保守不提高。
