# Field Evidence Material Resolution Review Decision Pre-Start

Run time: 2026-05-22 07:08 Asia/Shanghai

## Sprint Declaration

- `sprint_type: epic`
- Sprint folder: `sprints/2026.05.22_07-08_field-evidence-material-resolution-review-decision/`
- Mode: planning-only in this task; implementation must be dispatched later to parallel owner subagents.
- Product owner: `product-okr-owner`
- Planned implementation owners: `autonomy-engineer`, `robot-software-engineer`, `full-stack-software-engineer`, `robot-hardware-engineer`

## User Value And Product North Star

用户价值：现场 owner / support 已经有 `field_evidence_material_resolution_intake` 的 sanitized summary，但还缺一个明确的 review-decision gate 来判断这些材料是否可进入 owner review、是否仍需补证据、是否因 unsafe resolution 被拒绝，或是否因为缺 intake 而阻塞。用户和支持人员应该看到清晰、保守、可行动的 review decision，而不是把 `accepted` 误读成真实送达或真实材料闭环。

产品北极星：普通手机用户只看到安全、脱敏、只读的材料复核状态；在本地 Docker-only 软件证明阶段，Robot/mobile 必须保持 `source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`，不得启用 Start Delivery、Confirm Dropoff、Cancel 或任何 robot control。

## Evidence Background

- `OKR.md` 4.1 更新时间为 2026-05-22 06:21 Asia/Shanghai。Objective 5 当前最低，约 68%；Objective 1 约 81%；Objective 2/3/4 约 99%。
- 最新 sprint `sprints/2026.05.22_06-07_field-evidence-material-resolution-intake/final.md` 明确：`field_evidence_material_resolution_intake` 已完成，但只是 `software_proof`。其中 `accepted` 不是 delivery success、field pass、HIL、真实 phone/browser、O5 external proof、PR #5 resolution 或 verified terminal result。
- GitHub PR #5 live review thread 状态：`PRRT_kwDOSWB9286CJ3tQ` resolved，`PRRT_kwDOSWB9286CJ3tU` resolved，`PRRT_kwDOSWB9286CJ3tX` unresolved。comment `3269642220` 是 software-proof reply publication，不是 reviewer resolution。
- 当前主机只有 Docker，没有真实硬件、真实外部云/4G/OSS/CDN/DB/queue、真实手机/browser 或 verified terminal result。本轮不得把需要真实材料才能完成的验收写成必成项。

## Current Blocker Scan

- 最近两轮不是卡在 Docker build、registry、测试命名或本地执行失败；根因仍是真实外部/硬件/现场材料未提供。
- 上轮已经消费了 resolution intake，本轮不再新增 generic missing-material wrapper，而是把 intake summary 推进到 `field_evidence_material_resolution_review_decision`。
- 如果 implementation 阶段缺少 resolution intake summary，本 sprint 必须 fail closed 为 `blocked_missing_resolution_intake_not_proven`，并继续保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## Review Decision Scope

本轮 capability 是 `field_evidence_material_resolution_review_decision`，只允许输出以下安全决策：

- `accepted_for_owner_review_not_proven`
- `needs_more_evidence_not_proven`
- `rejected_unsafe_resolution_not_proven`
- `blocked_missing_resolution_intake_not_proven`

所有 surface 必须使用 evidence boundary `software_proof_docker_field_evidence_material_resolution_review_decision_gate`。`accepted_for_owner_review_not_proven` 只表示可以交给 owner review，不表示真实送达、真实 field pass、HIL、真实手机/browser、O5 external proof、PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved、verified terminal delivery/dropoff/cancel result 或 OKR 完成度提升。

## Planning File Scope

本轮 planning-only 文件范围仅限：

- `sprints/2026.05.22_07-08_field-evidence-material-resolution-review-decision/pre_start.md`
- `sprints/2026.05.22_07-08_field-evidence-material-resolution-review-decision/prd.md`
- `sprints/2026.05.22_07-08_field-evidence-material-resolution-review-decision/tech-plan.md`

当前任务禁止修改产品代码、测试代码、硬件配置、`OKR.md`、`docs/process` 或其他 sprint 文件。后续 implementation 的代码和文档范围由 `tech-plan.md` 分配给并行 worker。

## Entry Criteria For Implementation

- `tech-plan.md` 必须写清四个并行 implementation / consultation worker：Autonomy PC gate、Robot diagnostics alias、Full-Stack mobile/web read-only panel、Hardware vendor/PR #5 boundary consultation。
- 每个 owner 必须有明确文件范围、接口边界、围栏验收命令和输出要求。
- Product closeout 只在 workers 完成后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和必要 progress log；不得在真实证据缺失时提升 Objective percentages。

## Pre-Start Decision

启动 fresh Epic sprint。原因：这是跨 PC gate、Robot diagnostics、mobile/web read-only panel、Hardware boundary consultation 和 Product closeout 的多 owner review-decision 能力，预计后续实现需要 2-4 个并行子 agent，不符合 micro sprint。
