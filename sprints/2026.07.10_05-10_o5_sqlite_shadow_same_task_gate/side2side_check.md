# Side-by-Side Check：O5 SQLite shadow same-task gate

## 对照结论

本轮达到 PRD 验收口径，但只能按软件 shadow proof 收口。它让同一 `task_id` 的 O5 command/result/reconciliation 链路跨 SQLite state store 和 relay restart 后仍可读回，并进入 O6 `same_task_mission_evidence_gate`；不证明真实送达或真实生产云。

## PRD 对照

| PRD 要求 | 结果 | 产品判断 |
| --- | --- | --- |
| smoke 支持 `--state-backend file|sqlite`，默认 file 兼容 | 已完成 | 通过 |
| SQLite 模式用同一 SQLite state path 重启 relay 后读取 reconciliation | 已完成，`relay_restart_readback=true`、`sqlite_state_store_reopened=true` | 通过 |
| summary 暴露 backend/restart/readback/result/gate 字段 | 已完成，含 `relay_state_backend=sqlite`、`reconciliation.result_state=terminal_result_recorded`、`same_task_mission_gate_ready_not_success_proof` | 通过 |
| false safety fields 固定为 false | 已完成，含 `connects_cloud_production=false`、`delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false` | 通过 |
| 单元测试覆盖 file 兼容和 sqlite restart/readback | 已完成，`Ran 3 tests in 2.282s OK` | 通过 |
| 文档同步说明不是 production DB/queue | 已完成，Robot Software 更新 O6 archive API 和 cloud 4G infrastructure 文档 | 通过 |

## OKR 对照

- O5：可保守从约 83% 上调到约 84%，理由是本地 O5 command/result 主路径从一次性 file/in-process smoke 推进到 SQLite shadow restart/readback。
- O6：维持约 84%，因为本轮复用既有 O6 gate/readback 合同，没有新增生产 DB/queue、真实隧道、OSS 或生产级查询容量。
- O7：维持约 83%，因为本轮没有新增 O7 UI、真实 browser 证据、真实媒体或现场回放材料。
- KR：本轮不归档任何 KR。

## 证据边界

本轮 proof boundary 为 `software_proof_o5_sqlite_shadow_same_task_gate_only`。

它不是真实 production cloud，不是真实 production DB，不是 queue，不是多实例一致性，不是 HTTPS/TLS，不是 4G/SIM，不是 OSS/CDN live traffic，不是 live Nav2，不是 delivery record，不是 operator confirmation，不是真实手机/browser，也不是 delivery success。

## 下一轮建议

继续 O5 只能接真实 production cloud、production DB/queue external probe 或 live endpoint evidence。若这些材料仍不可得，下一轮应转向 O7 的 same-task mission material checklist，而不是继续用 local shadow/smoke 提升百分比。
