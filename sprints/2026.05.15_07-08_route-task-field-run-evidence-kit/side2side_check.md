# Sprint 2026.05.15_07-08 Route Task Field Run Evidence Kit - Side2Side Check

sprint_type: epic

## 1. PRD 对照

| PRD 要求 | 结果 | 证据 |
| --- | --- | --- |
| PC 侧生成 evidence kit JSON | 通过 | Task A 新增 `trashbot.route_task_field_run_evidence_kit.v1` CLI 与 6 个目标测试；boundary 为 `software_proof_docker_route_task_field_run_evidence_kit_gate`。 |
| 输出材料目录、采集模板、命令、same `evidence_ref`、缺失材料、handoff 与 not_proven | 通过 | Engineering summary 覆盖 material directory manifest、capture templates、commands to run/rerun、same evidence_ref、missing materials、operator handoff、robot diagnostics summary、mobile readonly summary、`not_proven`。 |
| Robot diagnostics 只做 metadata-only consumption | 通过 | Task B 支持 explicit ref 与环境变量来源，校验 schema/boundary，保持 fail-closed；`Ran 69 tests in 0.051s OK`。 |
| 手机端只读展示 evidence kit | 通过 | Task C 新增“路线现场证据包” panel；`38 tests OK`、`node --check mobile/web/app.js` pass。 |
| 不放行控制动作，不宣称送达 | 通过 | 全链路保持 `primary_actions_enabled=false`、`delivery_success=false`，不改变 Start/Confirm/Cancel gating。 |

## 2. OKR 对照

- Objective 2：通过 evidence kit 把任务状态、dropoff/cancel 材料、失败/恢复原因、operator next steps 和 completion 缺口组织成现场执行前交接包，可支持 KR4/KR5 的下一步补证；从约 66% 保守上调到约 67%。
- Objective 3：通过 evidence kit 把 route status/replay、execution pack、task record、completion signal、console summary 和未来现场回填材料统一到同一 `evidence_ref`；从约 66% 保守上调到约 67%。
- Objective 5：没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 外部材料；保持约 66%。

## 3. 证据边界检查

- 本轮证据边界是 `software_proof_docker_route_task_field_run_evidence_kit_gate`。
- 该边界只证明 Docker/local evidence kit artifact、Robot diagnostics summary、mobile read-only panel 和 fail-closed 控制边界。
- 不证明真实路线运行、真实底盘运动、真实 dropoff/cancel completion、真实送达、HIL、真实手机/browser 或 Objective 5 external proof。

## 4. 阻塞与下一步

- O2/O3 下一步：把 evidence kit 带到真实 Nav2/fixed-route 或上车实机复账，补齐同一 `evidence_ref` 的现场材料。
- Objective 5 下一步：只有拿到真实外部材料时才继续提升完成度；外部材料不可用时不继续重复本地 metadata depth。
