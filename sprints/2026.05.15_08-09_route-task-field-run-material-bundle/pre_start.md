# Sprint 2026.05.15_08-09 Route Task Field Run Material Bundle - Pre Start

sprint_type: epic

## 1. 上轮未完成项

上一轮 `2026.05.15_07-08_route-task-field-run-evidence-kit` 已完成 `software_proof_docker_route_task_field_run_evidence_kit_gate`，把 route status、task record、completion signal、console summary 和未来现场回填材料组织成同一 `evidence_ref` 的 evidence kit。

未完成项仍是实证材料：真实 Nav2/fixed-route 运行、真实路线采集、同一 `evidence_ref` 的上车实机复账、真实 dropoff/cancel completion、真实 delivery success、WAVE ROVER/HIL，以及 Objective 5 的公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 外部证据。

## 2. 本轮目标

本轮不重复堆 Objective 5 本地 metadata。当前 `OKR.md` 4.1 显示 Objective 5 约 66% 最低，但 `OKR.md` 第 6 节明确写明，只有拿到真实外部材料时才应继续提升 O5；本机只有 Docker，无法生成真实 O5 外部证据。

因此本轮选择 Objective 2 / Objective 3 的下一步可行动作：把上一轮 evidence kit 转成可交给现场同学执行的 material bundle，实际生成同一 `evidence_ref` 的目录结构、模板文件、run/rerun commands、缺口清单和 operator handoff 摘要，并让 Robot diagnostics 与 `mobile/web` 只读消费该 bundle summary。

## 3. Owner 与边界

- Autonomy Algorithm Engineer：实现 PC 侧 `route_task_field_run_material_bundle` CLI、fixture/test、PC/navigation 文档。
- Robot Platform Engineer：让 diagnostics metadata-only 消费 material bundle summary，并更新接口文档。
- User Touchpoint Full-Stack Engineer：让 `mobile/web` 展示只读 material bundle panel，不改变 Start/Confirm/Cancel gating。
- Product Manager / OKR Owner：收口 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 4. 证据边界

本轮只能形成 `software_proof_docker_route_task_field_run_material_bundle_gate`。它证明 Docker/local 环境能生成、消费和展示现场材料包，不证明真实固定路线运行、真实底盘运动、真实投放、真实取消、真实手机验收、HIL 或 Objective 5 外部证据。

## 5. 重复 blocker 核对

最近多轮 O5 blocker 均是缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration。按同一 blocker 重复消费红线，本轮不继续消费该 blocker，改走 O2/O3 material bundle。
