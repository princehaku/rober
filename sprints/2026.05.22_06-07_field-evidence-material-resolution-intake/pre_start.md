# Field Evidence Material Resolution Intake Pre-Start

Run time: 2026-05-22 06:07 Asia/Shanghai

## Sprint Declaration

- `sprint_type: epic`
- Sprint folder: `sprints/2026.05.22_06-07_field-evidence-material-resolution-intake/`
- Mode: planning-only in this task; implementation must be dispatched later to parallel owner subagents.
- Product owner: `product-okr-owner`
- Planned implementation owners: `autonomy-engineer`, `robot-software-engineer`, `full-stack-software-engineer`, `rober-hardware-engineer`

## User Value And Product North Star

用户价值：现场 owner / support 终于能把已经升级出来的 missing-material blocker 和 owner 提供的 safe resolution packet 放到同一条证据链里复核，而不是继续给用户展示“缺材料”包装层。用户或支持人员只看到 sanitized resolution status：`accepted`、`missing`、`rejected` 或 `blocked`，并知道下一步该补什么材料。

产品北极星：普通手机用户只在真实材料经同一 safe `evidence_ref` 复核后看到可推进状态；在本地 Docker-only 软件证明阶段，Robot/mobile 只能只读显示 resolution intake，不启用 Start Delivery、Confirm Dropoff、Cancel 或任何 robot control。

## Evidence Background

- `OKR.md` 4.1 当前进度：Objective 5 最低，约 68%；Objective 1 约 81%；Objective 2/3/4 约 99%。
- 当前主机只有 Docker，没有真实硬件、真实手机、4G/SIM、OSS/CDN live traffic、public HTTPS/TLS、production DB/queue、真实 terminal delivery/dropoff/cancel result。
- 最新 sprint `2026.05.22_05-06_verified-terminal-result-material-review-decision` 已完成 terminal-result material review-decision，但 final 明确只是一层 `software_proof_docker_verified_terminal_result_material_review_decision_gate`，不是真实材料，不应继续 wrap 同一 missing-material blocker。
- Sprint `2026.05.22_02-03_field-evidence-material-blocker-escalation-pack` 已把 O5 external、O1 PR #5 hardware/HIL、O2/O3/O4 route/elevator/phone field-material 缺口转成 blocker escalation pack。
- 下一步可执行软件路径是 `field_evidence_material_resolution_intake`：消费 blocker escalation artifact/summary/Robot alias + owner-provided safe resolution packet，校验 same safe `evidence_ref`，分类 `accepted`、`missing`、`rejected`、`blocked`，输出 sanitized software-proof summary，供 Robot/mobile read-only 显示。
- Live GitHub PR evidence：PR #5 merged；review threads `PRRT_kwDOSWB9286CJ3tQ` and `PRRT_kwDOSWB9286CJ3tU` resolved；`PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false`，要求为 mandatory sensor assumptions 引用 vendor sources。PR #6 merged docs-only and has no review threads。

## Current Blocker Scan

- 最近 blocker root cause 不是 Docker build、registry、测试命名或本地执行失败；根因是真实外部/硬件/现场材料未提供。
- 本轮不再重复制造新的 missing-material wrapper；它只定义如何消费 owner-provided safe resolution packet。
- 若后续 owner 没有提供 safe resolution packet，本 sprint 实现必须 fail closed 为 `blocked_missing_owner_resolution_packet_not_proven`，并继续保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## Scope Boundary

本轮 planning-only 文件范围仅限：

- `sprints/2026.05.22_06-07_field-evidence-material-resolution-intake/pre_start.md`
- `sprints/2026.05.22_06-07_field-evidence-material-resolution-intake/prd.md`
- `sprints/2026.05.22_06-07_field-evidence-material-resolution-intake/tech-plan.md`

后续实现允许范围由 `tech-plan.md` 分配。当前任务不改产品代码、不改测试、不改 `OKR.md`、不改 `docs/product`、不改 `docs/interfaces`、不改旧 sprint。

## Entry Criteria For Implementation

- `tech-plan.md` 写清并行 owner 分工、文件范围、接口影响、验收命令和风险边界。
- 四个 implementation owner 的文件范围互不重叠；Hardware 只做只读 vendor/PR #5 boundary consultation，不改硬件配置。
- Product closeout 只在 worker 完成后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和必要 docs/process 记录。

## Pre-Start Decision

启动 fresh Epic sprint。原因：这是跨 PC gate、Robot diagnostics、mobile/web 只读显示、Hardware vendor/PR #5 boundary consultation 和 Product closeout 的多 owner 计划，预计后续实现需要 2-4 个并行子 agent，不符合 micro sprint。
