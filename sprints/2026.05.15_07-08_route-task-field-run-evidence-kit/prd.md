# Sprint 2026.05.15_07-08 Route Task Field Run Evidence Kit - PRD

sprint_type: epic

## 1. 用户价值

现场同学准备真实路线-任务联跑时，不应再从多个 JSON、日志和上一轮 console 输出里手动拼材料。本轮要产出一份 evidence kit：告诉现场应该创建哪些文件、按什么顺序执行、哪些材料仍缺失、如何保持同一 `evidence_ref`，以及哪些结论仍是 `not_proven`。

## 2. OKR 映射

- Objective 2：推进 KR4/KR5。证据包应明确任务状态、dropoff/cancel 材料、失败/恢复原因、operator next steps 和 completion 证明缺口。
- Objective 3：推进 KR2/KR3/KR5。证据包应把 route status/replay、execution pack、task record、completion signal、console summary 和未来现场回填材料统一到同一 `evidence_ref`。
- Objective 5：不推进。没有真实外部云/4G/OSS/CDN/DB/queue 材料时不做本地替代证明。

## 3. 核心需求

1. PC 侧新增 dependency-free CLI，读取上一轮 console artifact，输出 evidence kit JSON。
2. Evidence kit 必须包含 `schema=trashbot.route_task_field_run_evidence_kit.v1`、`schema_version=1`、`evidence_boundary=software_proof_docker_route_task_field_run_evidence_kit_gate`。
3. Evidence kit 必须包含 material directory manifest、capture templates、commands to run/rerun、same `evidence_ref` verdict、missing materials、operator handoff、robot diagnostics summary、mobile readonly summary、`not_proven`、`primary_actions_enabled=false`、`delivery_success=false`。
4. Robot diagnostics 只能 metadata-only 消费 evidence kit 或 summary，不得触发 collect/dropoff/cancel、ACK、cursor、Nav2、HIL 或 delivery success。
5. 手机端只读展示 evidence kit 状态，不读取 raw artifact、本机绝对路径、token、serial/UART、`/cmd_vel`、checksum 或 traceback。

## 4. 验收口径

- 成功输出 evidence kit JSON，且缺材料时保持 blocked/not_proven。
- Diagnostics 和 mobile 都能展示只读摘要。
- 所有控制动作保持 fail-closed。
- 验证只跑对应文件范围的 py_compile、目标 unittest、`node --check`、required `rg` 和 scoped diff check。

## 5. 不做事项

- 不跑真实 Nav2/fixed-route。
- 不接入 WAVE ROVER、串口、HIL 或真实硬件。
- 不新增 O5 外部云证明。
- 不做 broad regression 或新增大测试矩阵。
