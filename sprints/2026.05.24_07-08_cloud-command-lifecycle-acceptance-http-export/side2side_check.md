# Cloud Command Lifecycle Acceptance HTTP Export Side-by-Side Check

Run time: 2026-05-24 Asia/Shanghai

## Sprint Type

sprint_type: epic

## 对照结论

本轮 PRD 目标是把上一轮 CLI export 的安全验收包推进为 independent cloud relay 的只读 HTTP GET support endpoint。Task A 已实现 route，Task B 已只读核对 Robot safe alias，Task C 完成 Product closeout；本轮满足 PRD P0/P1/P2 的 software proof 验收，但不提升 OKR 百分比。

## P0 验收对照

| PRD P0 项 | 对照结果 |
| --- | --- |
| HTTP GET route 可用且只读 | 通过。`/api/support/cloud-command-lifecycle-replay-acceptance-packet-export` 返回 `cloud_command_lifecycle_replay_acceptance_packet_http_export`，测试覆盖 no-auth GET 和 no state-file side effects。 |
| Payload 包含目标 marker | 通过。包含 `cloud_command_lifecycle_replay_acceptance_packet_http_export`。 |
| Payload 包含目标 evidence boundary | 通过。包含 `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_http_export_gate`。 |
| 保留 false-state flags | 通过。保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。 |

## P1 验收对照

| PRD P1 项 | 对照结果 |
| --- | --- |
| Missing / unsafe / stale source fail closed | 通过。Focused tests 覆盖 unsafe text redaction，payload 只输出 support-safe copy。 |
| 不输出敏感信息 | 通过。Docs 与 tests 保留 unsafe text redaction；route 不输出 bearer token、Authorization、credential-bearing URL、DB/queue URL、本地 state path、ROS topic、hardware details 或 raw traceback。 |
| GET 前后 cursor/state 不变 | 通过。Focused tests 验证 GET 不写 state file。 |

## P2 验收对照

| PRD P2 项 | 对照结果 |
| --- | --- |
| docs/product 同步 API route | 通过。`docs/product/remote_4g_mvp.md` 和 `docs/product/cloud_4g_infrastructure.md` 已写入 route、support boundary 和 no-overclaim 说明。 |
| cloud relay README 同步 | 通过。`cloud-relay/README.md` 已记录 HTTP export 使用边界。 |

## Product Boundary

- 本轮是 `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_http_export_gate`。
- 本轮不是 true phone/browser proof、not delivery success、not HIL、not PR #5 resolved、not real external cloud proof。
- PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`。
- `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` 保持可见。
- Objective 5 保持约 68%，no OKR percentage lift。

## 剩余验收风险

- 未跑真实公网 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN live traffic 或 production worker/cutover。
- 未跑真实 iPhone/Android browser、production app、PWA prompt/userChoice 或 phone-device acceptance。
- 未跑 Nav2/fixed-route runtime、route/elevator field pass、WAVE ROVER/UART/HIL 或 verified terminal delivery/dropoff/cancel result。
