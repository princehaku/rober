# Sprint 2026.05.19_17-18 Mobile Real Device Acceptance Callback Intake - Pre Start

## 1. Sprint 类型

sprint_type: epic

本轮 fresh Epic sprint 目标是启动 `mobile_real_device_field_trial_acceptance_execution_callback_intake*`，消费上一轮 `mobile_real_device_field_trial_acceptance_execution_pack*`，为现场 owner 后续提交真实手机执行回调材料提供 fail-closed 入口。

证据边界固定为 `software_proof_docker_mobile_real_device_field_trial_acceptance_execution_callback_intake_gate`。本轮必须保持 `source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`，不得写成真实手机验收通过、真实 route/elevator field pass、HIL、真实投放、真实取消完成或 Objective 5 external proof。

## 2. Live OKR Rerank

当前 `OKR.md` 4.1 最新 sprint 是 `2026.05.19_16-17_task-terminal-field-material-review-decision`：

- Objective 5 约 68%，数字最低，但仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover 或真实 external phone/browser proof。
- Objective 1 约 81%，次低，但仍缺 WAVE ROVER/UART/HIL、`feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery`、operator HIL report，以及 PR #5 真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry material。
- Objective 2 / Objective 3 / Objective 4 约 99%，但最新 16-17 final 仍明确缺真实 dropoff/cancel completion、Nav2/fixed-route、route/elevator field pass、真实手机/browser、O5 external 和 O1/HIL。

本轮不推进 Objective 5 completion。原因是当前主机只有 Docker，没有真实外部云、公网入口、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/cutover 材料；继续添加本地 O5 metadata 会重复消费已 blocked 的 O5 external blocker。

本轮不推进 Objective 1 completion。原因是当前主机没有真实 WAVE ROVER、UART、HIL 或 PR #5 2D LiDAR / ToF mandatory sensor material；不能把本地 callback intake 写成硬件协议可信底盘或 PR #5 sensor material 进展。

本轮不关闭 PR #5 unresolved thread `PRRT_kwDOSWB9286CJ3tX`。该 thread 的 blocker 是缺 vendor/source-backed mandatory sensor material，当前仍没有真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 证据；callback intake 只服务 O4 真实手机执行回调材料，不能替代 PR #5 hardware materials。

本轮选择 Objective 4 callback intake。原因是 2026.05.18_23-24 final 明确下一步最好拿真实 iPhone/Android/production app/PWA prompt/user choice 材料；在 Docker-only 主机上，当前可交付的下一层不是宣称真机验收通过，而是提供 fail-closed callback intake 入口，允许现场 owner 后续按同一 safe `evidence_ref` 提交真实手机执行回调材料。

## 3. Repeated Blocker Stop-rule 判断

- O5 external blocker 已多轮保持：缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover。第三次继续做本地 O5 wrapper 会违规，因此本轮切换 away from O5。
- O1/HIL blocker 已多轮保持：缺真实 WAVE ROVER/UART/HIL packet、底盘 feedback、operator HIL report。当前无硬件，不能再次消费同一 blocker。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` blocker 已确认仍是真实 mandatory sensor material；本轮不得把 callback intake 包装成 PR #5 关闭证据。
- O2/O3 route/elevator blockers 已被多轮 software-proof wrapper 消费；最新 16-17 final 仍缺真实 dropoff/cancel completion、Nav2/fixed-route、route/elevator field pass，因此本轮不再新增 O2/O3 blocker wrapper。
- O4 mobile real-device execution pack 的下一步是接受真实执行回调材料；本轮是新的 callback-intake rung，不重复消费上一轮 execution pack blocker，也不宣称真实手机验收通过。

## 4. 用户价值和产品北极星

产品北极星仍是让普通手机用户不接触命令行、ROS2、串口、云凭证或硬件调试，也能完成送垃圾任务并理解失败时下一步。当前真实手机验收仍缺现场材料，所以本轮用户价值是把现场执行回调变成结构化入口：现场 owner 能按同一 safe `evidence_ref` 提交 accepted/missing/rejected callback evidence，系统能告诉 owner 还缺什么、由谁接手、如何 rerun。

这不是 production app，也不是真实 iPhone/Android 验收通过；它是把上一轮 execution pack 的执行结果回流路径补齐。

## 5. 本轮核心抓手

- 新增 `mobile_real_device_field_trial_acceptance_execution_callback_intake*` contract。
- 消费上一轮 `mobile_real_device_field_trial_acceptance_execution_pack*`。
- 输出 accepted / missing / rejected callback evidence。
- 保持 same safe `evidence_ref` 要求。
- 输出 owner handoff、`next_required_evidence` 和 rerun guidance。
- 在 mobile/web、Robot diagnostics 和产品文档中保持只读、fail-closed、phone-safe。

## 6. Owner 和 Sprint 留档

本轮需要创建并维护：

- `pre_start.md`：本文件，记录 rerank、stop-rule、证据边界和 sprint_type。
- `prd.md`：定义用户价值、OKR/KR、验收口径和不证明事项。
- `tech-plan.md`：定义 owner/file split、接口影响、验收命令和 `OKR 最低优先级核对`。

后续实现阶段应并行启动：

- Full-stack owner：手机 UI / fixture / `docs/product/mobile_user_flow.md`。
- Robot owner：operator gateway diagnostics safe alias / diagnostics docs。
- Product owner：closeout docs、`OKR.md`、`docs/process/okr_progress_log.md`。

## 7. 风险和阻塞

- 没有真实手机、production app、PWA prompt/user choice 材料时，本轮只能证明 callback intake 软件入口。
- 没有真实外部云材料时，不得推进 Objective 5 completion。
- 没有 WAVE ROVER/UART/HIL 和 PR #5 mandatory sensor material 时，不得推进 Objective 1 或关闭 `PRRT_kwDOSWB9286CJ3tX`。
- 没有真实 route/elevator field materials、Nav2/fixed-route runtime log、dropoff/cancel completion 或 delivery result 时，不得推进 Objective 2 / Objective 3 completion。
