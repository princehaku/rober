# O5 Reconciliation Same-Task Archive Smoke Pre-Start

## Sprint Type

sprint_type: epic

## 背景

上一轮 `sprints/2026.07.10_03-09_o5_o6_o7_same_task_mission_gate/` 已完成 `same_task_mission_evidence_gate`，但收口明确要求下一轮不要继续 wrapper/decoder，而要消费真实或准现场 same-task mission materials。当前最低活跃 Objective 是 O5（约 82%），O7 约 83%，O6 约 84%，O1 约 85%。

本轮选择 O5 主线：把 O5 relay 的 `GET /api/commands/<command_id>/result` reconciliation v2 结果作为准现场 terminal material，接入 Algorithm manifest，再写入 O6 local/mock archive 并读回 same-task gate。

## 最近 Blocker 核对

- 最近两轮均完成且未 blocked。
- 主要风险不是硬件/凭证 blocker，而是 proof boundary：上一轮仍是 `software_proof_same_task_mission_evidence_gate_only`，不证明 production cloud 或真实送达。
- 本轮不重复消费 wrapper/decoder blocker；改为消费 O5 relay reconciliation material。

## 本轮目标

1. Algorithm：`field_route_evidence_manifest.py` 支持从 O5 `trashbot.cloud_command_result_reconciliation.v2` 中提取 nested `trashbot.cloud_command_terminal_result.v1`，仍 fail-closed。
2. Robot Software：新增可复跑 smoke，驱动本地 relay command -> terminal result -> reconciliation -> manifest -> O6 archive -> consumer readback。
3. Product：更新 OKR、progress log 和 sprint 收口，明确证据边界。

## Owner

- 主责：`robot-software-engineer`
- 协同：`robot-algorithm-engineer`
- 收口：`product-okr-owner`

## 证据边界

本轮目标证据边界为 `software_proof_o5_reconciliation_same_task_archive_smoke_only`。它可以证明本地/mock O5 reconciliation terminal material 能进入 same-task mission gate 和 O6 consumer readback；不证明真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实 live Nav2 route execution、真实 delivery success、真实手机/browser 或 HIL。
