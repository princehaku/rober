# Field Evidence Rerun Acceptance Owner Response Intake PRD

Run time: 2026-05-23 05:06 Asia/Shanghai

## 用户价值和产品北极星

普通手机用户最终只关心一次送垃圾是否真实完成、失败时谁该处理、材料是否可信。本轮产品价值是把现场 owner 的 response intake 做成三端一致的安全入口：PC 端判断 owner 回填是否满足同一 safe `evidence_ref`，Robot diagnostics 只暴露安全摘要，`mobile/web` 只读展示下一步缺口。

这不是交付结果本身，而是为了让后续真实 route/elevator field pass、true phone/browser evidence、dropoff/cancel completion 和 delivery result 能被安全接收、拒绝或阻塞。

## OKR 映射

- Objective 5 约 68%，当前最低。本轮没有 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser 或 verified terminal result materials，因此不写成 O5 external proof。
- Objective 1 约 81%。PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / `hardware_material_pending`，Q/U resolved 不能关闭 X；本轮不证明真实 2D LiDAR/ToF/WAVE ROVER/UART/HIL。
- Objective 2 / Objective 3 / Objective 4 约 99%。本轮只推进 owner response intake，用于要求真实 task record、真实 Nav2/fixed-route runtime log、route completion signal、电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result、真实 route/elevator field pass 和 true phone/browser evidence。

## KR 拆解或更新

本 sprint 不更新 `OKR.md` 百分比，不新增 KR。后续实现按以下验收拆解：

1. PC-only owner response intake 能读取上一轮 follow-up escalation status，并对 owner 回填做 accepted / missing / rejected / blocked 的 fail-closed 分类。
2. Robot diagnostics safe alias 能消费 PC safe summary，只暴露 redacted metadata，不暴露 raw artifact、ROS topic、serial/UART、WAVE ROVER、凭证或本地路径。
3. `mobile/web` read-only panel 能展示 owner response intake 状态，并保持 Start Delivery、Confirm Dropoff、Cancel disabled。
4. Product closeout 只能在三路验证完成后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`，且必须保留 no OKR percentage lift。

## 本轮核心抓手

能力名称：`field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake`。

证据边界：`software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_gate`。

产品必须保留以下状态：

- `source=software_proof`
- `software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- no OKR percentage lift

## 需要做什么

- 接收上一轮 `field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status` 的安全输出。
- 要求 owner response 对同一 safe `evidence_ref` 回填真实现场材料清单。
- 对材料缺失、evidence_ref 不一致、unsafe copy、success/control claim、O5 external proof claim、O1 HIL claim、PR #5 resolution claim 执行 fail-closed。
- 在 PC / Robot / mobile 三端保持相同能力名、边界和 proof state。
- 后续 implementation 必须同步更新相关 `docs/interfaces/`、`docs/product/` 和 sprint closeout 文档。

## 优先级和验收口径

P0：

- 三端都必须包含 `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake` 与 `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_gate`。
- 三端都必须保留 `source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- 任何真实送达、真实 field pass、真实 phone/browser、O5 external proof、O1 HIL 或 PR #5 resolution claim 都必须 fail closed。

P1：

- Owner response 的 required materials 应明确列出真实 task record、真实 Nav2/fixed-route runtime log、route completion signal、电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result、真实 route/elevator field pass 和 true phone/browser evidence。
- mobile/web 必须只读展示，不新增 fetch route、review route、handoff route、follow-up route、material upload route、ACK/cursor route 或 robot command endpoint。

## 对应责任 Engineer

- Autonomy Algorithm Engineer：PC-only owner response intake gate、测试、`pc-tools/README.md`、`docs/interfaces/evidence_contracts.md`。
- Robot Platform Engineer：operator gateway diagnostics safe alias、测试、`docs/interfaces/ros_runtime_contracts.md`。
- User Touchpoint Full-Stack Engineer：`mobile/web` read-only panel、fixture、测试、`docs/product/mobile_user_flow.md`。
- Product Manager / OKR Owner：后续 closeout、OKR/progress log 和 sprint 文档收口。

## 风险、阻塞和需要补齐的证据链

- 仍缺 O5 真实 external proof：public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser、verified terminal result materials。
- 仍缺 O1 真实硬件材料：2D LiDAR/ToF SKU/source/receipt、安装、接线、电源、标定、WAVE ROVER/UART/HIL、operator HIL report、PR #5 `PRRT_kwDOSWB9286CJ3tX` reviewer resolution。
- 仍缺 O2/O3/O4 真实现场材料：同一 safe `evidence_ref` 的真实 task record、真实 Nav2/fixed-route runtime log、route completion signal、电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result、真实 route/elevator field pass、true phone/browser evidence。
- 本 sprint 的成功标准是 owner response intake 软件证明通过，不是 OKR 提升。

## Sprint 文档

- `pre_start.md`：记录 sprint_type、背景证据、owner、风险和边界。
- `prd.md`：记录用户价值、OKR 映射、KR 拆解、验收口径和责任 owner。
- `tech-plan.md`：记录三路并行 implementation plan、接口影响、验收命令和 OKR 最低优先级核对。
- 后续：`tech-done.md`、`side2side_check.md`、`final.md` 必须由 closeout 任务补齐。
