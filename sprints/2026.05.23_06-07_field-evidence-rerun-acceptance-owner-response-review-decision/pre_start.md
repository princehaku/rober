# Field Evidence Rerun Acceptance Owner Response Review Decision Pre-Start

Run time: 2026-05-23 06:07 Asia/Shanghai

## Sprint Type

sprint_type: epic

## 用户价值和产品北极星

产品北极星仍是普通手机用户可验证地完成垃圾投递闭环：用户不需要理解 ROS2、串口、云队列或现场材料格式，也能知道一次送垃圾任务是否真实完成、失败时谁该补材料、哪些证据仍不可采信。

本 sprint 不把本地 Docker metadata 写成真实送达，而是把上一轮 `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake` 的 owner response safe summary 推进到可复核的 review decision metadata。用户价值是让现场 owner 的回复被一致分类：是否可进入下一步 review handoff，是否缺同一 safe `evidence_ref` 的真实现场材料，是否包含 unsafe/success/control 过界声明。

## 背景证据

- 当前 `OKR.md` 4.1：Objective 5 最低，约 68%。本机只有 Docker，没有真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser 或 verified terminal result materials，因此本轮不能写成 O5 external proof。
- Objective 1 约 81%。GitHub PR #5 review thread `PRRT_kwDOSWB9286CJ3tX` live `is_resolved=false`，原因是强制 2D LiDAR / ToF 等硬件假设缺少 `docs/vendor/` 来源材料；Q/U threads 已 resolved 但不能关闭 X。
- 最新 sprint `sprints/2026.05.23_05-06_field-evidence-rerun-acceptance-owner-response-intake/final.md` 已完成 `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake`，边界 `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_gate`，no OKR percentage lift。
- 最新 final 的 Next Step 是：如果真实 O5 external 或 O1 hardware/PR #5 材料仍不可用，继续现场 owner-response review path，不弱化 `software_proof` 边界。

## OKR 映射

- Objective 5：最低，约 68%。本 sprint 不针对真实 O5 external proof，不提升进度。
- Objective 1：约 81%。PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / `hardware_material_pending`，本 sprint 不证明 HIL、WAVE ROVER/UART、LiDAR/ToF installed proof 或 reviewer resolution。
- Objective 2 / Objective 3：保持约 99%。本 sprint 只把 owner response intake 转成 review decision metadata，不是真实 route/elevator field pass、Nav2/fixed-route runtime pass、dropoff/cancel completion、delivery result 或 delivery success。
- Objective 4：保持约 99%。`mobile/web` 只读 review decision panel 不是真实手机/browser 证据，不启用主操作。

## 本轮核心抓手

能力名称：`field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision`。

证据边界：`software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_gate`。

必须保留：

- `source=software_proof`
- `software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- no OKR percentage lift

## 需要做什么

本轮要消费上一轮 owner response intake safe summary，将现场 owner response 分类为可复核的 review decision metadata。review decision 只能说明下一步是否进入 review handoff、是否需要 owner rework、是否 evidence_ref mismatch、是否 unsafe rejected 或 source missing；不能读取真实现场日志正文、不能验证真实云/手机/硬件/路线/电梯、不能触发机器人动作。

## 对应责任 Engineer

- Autonomy Algorithm Engineer：新增 PC-only review decision gate、测试、`pc-tools/README.md`、`docs/interfaces/evidence_contracts.md`。
- Robot Platform Engineer：更新 operator diagnostics safe alias、诊断测试、`docs/interfaces/ros_runtime_contracts.md`。
- User Touchpoint Full-Stack Engineer：更新 `mobile/web` read-only panel、fixture、mobile test、`docs/product/mobile_user_flow.md`。
- Product Manager / OKR Owner：A/B/C 返回后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。

## 风险、阻塞和需要补齐的证据链

- O5 仍缺真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser、verified terminal result materials。
- O1 仍缺真实 2D LiDAR / ToF SKU/source/receipt、安装、接线、电源、标定、WAVE ROVER/UART/HIL、operator HIL report，以及 PR #5 `PRRT_kwDOSWB9286CJ3tX` reviewer resolution。
- O2/O3/O4 仍缺同一 safe `evidence_ref` 的真实 task record、真实 Nav2/fixed-route runtime log、route completion signal、电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result、真实 route/elevator field pass、true phone/browser evidence。
- 本 sprint 成功标准是 review decision 软件证明通过，不是 OKR percentage lift。

## 需要创建或更新的 Sprint 文档

- 本次创建：`sprints/2026.05.23_06-07_field-evidence-rerun-acceptance-owner-response-review-decision/pre_start.md`
- 本次创建：`sprints/2026.05.23_06-07_field-evidence-rerun-acceptance-owner-response-review-decision/prd.md`
- 本次创建：`sprints/2026.05.23_06-07_field-evidence-rerun-acceptance-owner-response-review-decision/tech-plan.md`
- 后续 closeout 必须创建或更新：`tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`
