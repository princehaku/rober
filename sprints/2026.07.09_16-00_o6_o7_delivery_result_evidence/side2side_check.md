# O6/O7 Delivery Result Evidence Side2Side Check

## sprint_type: epic

Product 收口时间：2026-07-09 16:00 CST。

## 对照 tech-plan 验收口径

| 验收项 | 结论 | 证据 |
| --- | --- | --- |
| Algorithm 产出同一 `task_id` 的 `delivery_result_evidence` | 通过 | `--delivery-result-json` 已接入 manifest 顶层与 `field_motion_evidence_packet.delivery_result_evidence`，schema 为 `trashbot.delivery_result_evidence.v1` |
| Algorithm fail-closed 与安全字段 false | 通过 | 缺输入、JSON 不可读、schema mismatch、`task_id` mismatch、危险 true、path/root/token/raw/base64/credential URL 均输出阻断摘要，`safe_to_control=false`、`delivery_success=false` 保持不变 |
| Algorithm 验证通过 | 通过 | `Ran 20 tests in 0.069s OK` |
| O6 ingest/readback 白名单回读摘要 | 通过 | field evidence、artifact bundle、archive task detail、field evidence、artifact bundle、consumer detail alias 与 `include=delivery_result_evidence` 均已接入 |
| O6 fail-closed 和安全字段 false | 通过 | 坏 schema、坏 proof_scope、危险 true、path/root/token/raw/base64/credential URL/unsafe text 继续 fail-closed，控制类字段保持 false |
| O6 验证通过 | 通过 | `Ran 157 tests in 55.196s OK` |
| O7 consumer/UI 展示 readiness、blocked reasons、next evidence | 通过 | adapter/shared contract/UI/readiness 已接入 delivery result 摘要，且不打开 submit/control/action |
| O7 fail-closed 和安全字段 false | 通过 | 坏 schema、危险 true、path/root/token/raw/base64/credential URL/unsafe text 均 fail-closed，`primary_actions_enabled=false`、`robot_control_executed=false` 维持不变 |
| O7 test/build/lint 通过 | 通过 | `Test Files 3 passed`、`Tests 478 passed`，build 通过且仅保留既有 Vite chunk warning，lint 通过 |
| 不宣称真实生产云、真实 delivery success 或真实控制执行 | 通过 | 三方 worker 证据与本次收口均保持 `software_proof_delivery_result_evidence_only` 边界 |

## 未证明项

- 未证明真实 production cloud、production DB/queue、TLS/4G、OSS/CDN live traffic。
- 未证明真实 delivery record、真实 operator confirmation 媒体、真实 live Nav2 run、真实底盘运动或真实 delivery success。
- 未证明真实手机/browser 现场验收、真实 annotation API/export、真实 dataset export 或完整路线长期验收。

## OKR 映射和方向判断

- O6：通过。archive/read model 已从 Nav2 goal evidence 再前进一步，能围绕同一 `task_id` 回读 delivery result readiness。
- O7：通过。PC consumer detail 与 artifact bundle readiness 已能直接展示 delivery result readiness，而不是只靠 `next_required_evidence` 推断。
- 方向判断：继续推进 O6/O7，保守上调到约 `56%`；不归档 KR。

## 安全旗标核对

- `safe_to_control=false`：通过。
- `delivery_success=false`：通过。
- `primary_actions_enabled=false`：通过。
- `robot_control_executed=false`：通过。

## 下一轮建议

优先补真实或准现场 `delivery_record`、operator confirmation 媒体、`route_bag` / live Nav2 pose progress，并让 O6/O7 继续消费这些现场材料。不要把新的只读 wrapper 当作主要成果，除非它直接接住这些执行证据。
