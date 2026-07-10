# O5 Reconciliation Same-Task Archive Smoke Side-to-Side Check

## 验收口径对照

| PRD 验收项 | 证据 | 结论 |
| --- | --- | --- |
| reconciliation v2 recorded 时，manifest 保持 `delivery_result_evidence.source_schema=trashbot.cloud_command_terminal_result.v1` | Algorithm worker report 记录 wrapper 只下钻 nested terminal result；输出合同仍为 `trashbot.delivery_result_evidence.v1` / `source_schema=trashbot.cloud_command_terminal_result.v1` | 通过 |
| pending / missing / unsafe 时 fail-closed | Algorithm 新增 pending、task drift、unsafe refs 测试；`Ran 58 tests in 0.304s OK` | 通过 |
| smoke 能从 relay result 串到 O6 archive/readback | Robot Software 新增 `o5_same_task_mission_archive_smoke.py`，链路覆盖 command、terminal result、reconciliation、manifest、archive、consumer readback；`Ran 2 tests in 1.180s OK` | 通过 |
| consumer detail 通过 `include=same_task_mission_evidence_gate` 读回 same-task gate | Robot Software report 明确最后一步为 `GET /api/o6/consumer/tasks/<task_id>?include=same_task_mission_evidence_gate`，读回 `same_task_mission_gate_ready_not_success_proof` | 通过 |
| safety flags 不放开 | Engineer reports 均记录 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false` | 通过 |
| 不宣称真实生产或现场成功 | 本 closeout、`OKR.md` 和 `docs/process/okr_progress_log.md` 均写入 `software_proof_o5_reconciliation_same_task_archive_smoke_only` 边界 | 通过 |

## 产品验收判断

本轮通过 Product 验收。它把 O5 的本地 relay reconciliation result 从 phone-safe 读模型推进到 same-task mission archive smoke：同一 `task_id` 可从 `trashbot.cloud_command_result_reconciliation.v2` 下钻到 terminal result，再进入 Algorithm manifest、O6 archive/readback 和 gate readback。

验收不包括真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实 live Nav2 route execution、真实 delivery record、真实 operator confirmation、真实手机/browser 或真实 delivery success。

## 方向判断

- O5：继续。O5 获得小幅软件侧进展，可从约 82% 上调到约 83%。
- O6：继续但不调整百分比。本轮复用 O6 既有 gate/readback 合同，没有新增生产数据底座能力。
- O7：继续但不调整百分比。本轮没有新增 O7 UI、browser 证据或真实回放/媒体材料。

## 下一轮验收重点

下一轮必须拿到真实或准现场 same-task mission material，而不是继续增加 wrapper 或 summary。优先验收口径：

- production-like O5 command/result 写入和查询，至少覆盖真实 TLS endpoint 或 production DB/queue 影子环境。
- 同一 `task_id` 的 live route execution / Nav2 result / delivery record / operator confirmation 至少一类从真实或准现场来源进入 gate。
- 若仍使用 local smoke，只能作为回归验证，不再作为 O5/O6/O7 百分比提升依据。
