# Field Evidence Rerun Acceptance Owner Response Review Decision PRD

Run time: 2026-05-23 06:07 Asia/Shanghai

## 用户价值和产品北极星

普通手机用户最终只关心垃圾是否真实送达、异常是否安全停住、支持人员能否看懂下一步要谁补证据。本轮产品价值是把上一轮 owner response intake 的 safe summary 转成 review decision metadata，让 PC / Robot / `mobile/web` 对同一 safe `evidence_ref` 的 owner response 给出一致复核判断。

本 sprint 不交付真实现场结果。它只减少下一轮 review handoff 的歧义：哪些 owner response 材料可进入复核，哪些缺真实 task record / Nav2/fixed-route runtime log / 电梯现场材料 / true phone/browser evidence，哪些因 unsafe copy、success/control claim、O5 external proof claim、O1 HIL claim 或 PR #5 resolution claim 必须 fail closed。

## OKR 映射

- Objective 5 约 68%，当前最低。本轮没有 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser 或 verified terminal result materials，因此不写成 O5 external proof。
- Objective 1 约 81%。PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / `hardware_material_pending`，Q/U resolved 不能关闭 X；本轮不证明真实 2D LiDAR / ToF、WAVE ROVER、UART 或 HIL。
- Objective 2 / Objective 3 / Objective 4 约 99%。本轮只推进 `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision`，不证明真实 route/elevator field pass、Nav2/fixed-route runtime pass、dropoff/cancel completion、delivery result、delivery success 或 true phone/browser proof。

## KR 拆解或更新

本 sprint 不更新 `OKR.md` 百分比，不新增 KR。后续实现按以下验收拆解：

1. PC-only review decision gate 能读取上一轮 owner response intake safe artifact / summary / Robot safe alias，并输出 ready / rework / mismatch / unsafe / missing-source 的 fail-closed review decision。
2. Robot diagnostics safe alias 能消费 PC safe summary，只暴露 redacted metadata，不暴露 raw artifact、ROS topic、serial/UART、WAVE ROVER、凭证、DB/queue URL、本地路径或完整日志。
3. `mobile/web` read-only panel 能展示 owner response review decision，并保持 Start Delivery、Confirm Dropoff、Cancel disabled。
4. Product closeout 只能在 A/B/C 三路验证完成后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`，且必须保留 no OKR percentage lift。

## 本轮核心抓手

能力名称：`field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision`。

证据边界：`software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_gate`。

产品必须保留以下状态：

- `source=software_proof`
- `software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- no OKR percentage lift

## 需要做什么

- 接收上一轮 `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake` 的安全输出。
- 将 owner response 分类为可复核的 review decision metadata，而不是现场事实证明。
- 对缺 source、缺 required material、same evidence_ref 不一致、unsafe copy、success/control claim、O5 external proof claim、O1 HIL claim、PR #5 resolution claim 执行 fail-closed。
- 在 PC / Robot / mobile 三端保持同一能力名、边界、proof state 和 disabled primary actions。
- 同步更新 `docs/interfaces/`、`docs/product/` 和 sprint closeout 文档；本 planning 阶段只创建 `pre_start.md`、`prd.md`、`tech-plan.md`。

## 优先级和验收口径

P0：

- 三端必须包含 `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision` 与 `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_gate`。
- 三端必须保留 `source=software_proof`、`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- 任何真实送达、真实 field pass、真实 phone/browser、O5 external proof、O1 HIL、WAVE ROVER/UART proof、LiDAR/ToF installed proof 或 PR #5 resolution claim 都必须 fail closed。

P1：

- Review decision required materials 应继承上一轮 owner response intake 的真实 task record、真实 Nav2/fixed-route runtime log、route completion signal、电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result、真实 route/elevator field pass、true phone/browser evidence 和 PR #5 pending hardware material。
- `mobile/web` 必须只读展示，不新增 fetch route、review route、handoff route、follow-up route、owner-response route、material upload route、ACK/cursor route 或 robot command endpoint。

## 对应责任 Engineer

- Autonomy Algorithm Engineer：PC-only owner response review decision gate、测试、`pc-tools/README.md`、`docs/interfaces/evidence_contracts.md`。
- Robot Platform Engineer：operator gateway diagnostics safe alias、测试、`docs/interfaces/ros_runtime_contracts.md`。
- User Touchpoint Full-Stack Engineer：`mobile/web` read-only panel、fixture、测试、`docs/product/mobile_user_flow.md`。
- Product Manager / OKR Owner：后续 closeout、OKR/progress log 和 sprint 文档收口。

## 风险、阻塞和需要补齐的证据链

- 仍缺 O5 真实 external proof：public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser、verified terminal result materials。
- 仍缺 O1 真实硬件材料：2D LiDAR / ToF SKU/source/receipt、安装、接线、电源、标定、WAVE ROVER/UART/HIL、operator HIL report、PR #5 `PRRT_kwDOSWB9286CJ3tX` reviewer resolution。
- 仍缺 O2/O3/O4 真实现场材料：同一 safe `evidence_ref` 的真实 task record、真实 Nav2/fixed-route runtime log、route completion signal、电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result、真实 route/elevator field pass、true phone/browser evidence。
- 本 sprint 的成功标准是 owner response review decision 软件证明通过，不是 OKR percentage lift。

## Sprint 文档

- `pre_start.md`：记录 sprint_type、背景证据、owner、风险和边界。
- `prd.md`：记录用户价值、OKR 映射、KR 拆解、验收口径和责任 owner。
- `tech-plan.md`：记录三路并行 implementation plan、接口影响、验收命令和 OKR 最低优先级核对。
- 后续：`tech-done.md`、`side2side_check.md`、`final.md` 必须由 closeout 任务补齐。
