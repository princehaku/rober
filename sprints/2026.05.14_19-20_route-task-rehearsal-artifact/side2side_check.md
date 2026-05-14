# Sprint 2026.05.14_19-20 Route Task Rehearsal Artifact - Side2Side Check

sprint_type: epic

## 用户价值对照

本轮目标是让路线状态、任务记录和 evidence crosscheck 不再散落在多个日志或口头汇报里，而是形成同一 `evidence_ref` 的可保存 route/task rehearsal artifact。Task A 已把 artifact 输出落到 `evidence_crosscheck.py`；Task B 已让 task record / behavior fixed-route evidence anchor 更稳定；Task C 已按软件证明边界更新 OKR 和 sprint 收口。

产品北极星保持不变：普通用户最终需要真实送垃圾闭环，但工程团队必须先能复核每次路线/任务排练的证据链，并清楚知道哪些材料还没有到真实 Nav2/fixed-route、WAVE ROVER、HIL 或 delivery success。

## 验收口径对照

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| artifact 输出包含 schema/version 与 evidence boundary | 通过 | Task A 新增 `--rehearsal-artifact`，写出 `software_proof_docker_route_task_rehearsal_artifact_gate`。 |
| artifact 保留 `evidence_ref` 与 route/task summary | 通过 | Task A artifact 字段覆盖；Task B 保证 `route_progress.evidence_ref` 可提升到 top-level。 |
| HIL 缺失或 blocked 时仍可保存 artifact 且不声明真实 HIL | 通过 | Task A fenced test 覆盖 blocked HIL；artifact 输出 HIL alignment status 与 `not_proven`。 |
| task record / behavior evidence anchor 与 fixed-route 对齐 | 通过 | Task B 更新 `task_record.py`、`task_orchestrator.py` 并通过 targeted tests。 |
| artifact pass 不等于真实 delivery success | 通过 | Task A/B 文档和 tests 均保留非声明边界；Task C closeout 重复固定该口径。 |
| docs 同步 | 通过 | `pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`、`docs/interfaces/ros_contracts.md` 已由 Task A/B 同步。 |

## OKR 最低优先级回顾

`tech-plan.md` 中的 OKR 最低优先级核对仍成立：Objective 5 仍约 68%，本轮期间没有出现真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration 或其他真实外部 O5 材料。继续堆本地 O5 metadata depth 不能移动 O5 completion，因此本轮切到 Objective 2/3 的 route/task rehearsal artifact 是合理的。

本轮可以谨慎把 Objective 2 和 Objective 3 从约 77% 上调到约 78%，因为 status/replay/task_record 对账材料已经形成可保存 artifact，并且 task record 的 `evidence_ref` anchor 更稳定。Objective 5 必须保持约 68%；Objective 1 和 Objective 4 不调整。

## 证据边界

- 证据边界：`software_proof_docker_route_task_rehearsal_artifact_gate`
- 核心材料：fixed-route status、software proof replay、task record、evidence crosscheck、可选 HIL gate alignment status
- 证据性质：Docker/local route-task rehearsal software proof

不证明：

- 真实 Nav2/fixed-route 实跑
- 真实路线采集或关键帧实景证据
- WAVE ROVER、真实串口或 HIL
- 同一 `evidence_ref` 的上车复账
- dropoff/cancel completion 或 delivery success
- Objective 5 external proof、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration

## 未处理 TODO / 范围检查

- Task C 未修改产品代码、测试代码、硬件配置、launch 参数、Task A/B 文件或 `docs/interfaces/ros_contracts.md`。
- 工作树中存在 A/B worker 的允许范围改动，Task C 只引用并收口，不回滚或覆盖。
- 后续 O2/O3 若继续推进，必须补真实 Nav2/fixed-route、真实路线采集、WAVE ROVER/HIL 和同一 `evidence_ref` 的上车复账。
