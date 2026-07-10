# O5/O6 Live Endpoint Probe Readback Pre-Start

## sprint_type

sprint_type: epic

## 背景

本轮自动化继续按 `AGENTS.md` 和 `OKR.md` 推进最低完成度 OKR。`OKR.md` 4.1 显示 O5 与 O6 均约 84%，为当前最低并列项；O7 与 O1 均约 85%。最近两轮 sprint 已完成 O5 SQLite shadow same-task gate 和 O7 same-task mission material checklist。

上一轮 `2026.07.10_06-10_o7_same_task_mission_material_checklist` 的 next step 明确要求：下一轮优先真实 production cloud、production DB/queue external probe 或 live endpoint evidence；若外部材料不可得，不要继续做只读 checklist/surface。

## 最近 blocker 核对

- `2026.07.10_05-10_o5_sqlite_shadow_same_task_gate`：不是 blocked，完成本地 SQLite shadow relay restart/readback，但明确下一轮继续 O5 只能接真实外部材料。
- `2026.07.10_06-10_o7_same_task_mission_material_checklist`：不是 blocked，完成 O7 operator checklist；提醒下一轮 O5/O6 需要 production cloud / DB/queue external probe / live endpoint evidence。

本轮没有连续消费同一 blocker；但必须避免把 local shadow/smoke 再次包装成 O5/O6 百分比提升。

## 本轮目标

把 O5/O6 从已有本地 shadow/readback 进一步推进到可复核的 live endpoint probe readback 契约：Robot Software 负责让 live endpoint probe 结果可以被同一 `task_id` 的 smoke 汇总、安全落入 O6 archive/readback，并保持 phone-safe、fail-closed 和所有危险控制/送达字段为 false。

若本机没有真实公网 endpoint、生产 DB/queue 或凭证，本轮只能证明 live-probe/readback 软件契约可执行，不声明真实 production cloud 成功。

## Owner

- 主责 owner：robot-software-engineer
- 收口 owner：product-okr-owner

## 验收口径

- 必须新增或更新可执行 smoke/test，让 `cloud_external_probe` 或 DB/queue external probe artifact 与 `same_task_mission_evidence_gate` / O6 consumer readback 在同一 `task_id` 下关联。
- 输出必须固定 `connects_cloud_production=false`，除非真实外部 endpoint、生产 DB/queue 和凭证在当前环境中可验证。
- 输出必须固定 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
- 不能输出 base URL、Authorization、bearer token、DB/queue URL、raw response body、state path 或本地绝对路径。

## 风险

- 当前环境可能没有真实 production endpoint / DB / queue / 4G / TLS 凭证，因此本轮 OKR 只能保守记录为 contract/readback 进展。
- `remote_cloud_relay.py` 已经很大，改动必须保持小范围、测试覆盖明确，避免影响既有 relay 和 O6 archive 主路径。
