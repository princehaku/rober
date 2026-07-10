# O5/O6 Live Endpoint Probe Readback Side-to-Side Check

## 对照目标

- 计划目标：把 O5/O6 从已有本地 SQLite shadow same-task readback，推进到可复核的 live endpoint probe readback 契约。
- 实际结果：已完成 same-task smoke 到 `cloud_external_probe` / `cloud_db_queue_external_probe` additive readback，并可通过 O6 consumer 回读。

## 计划 vs 实际

| 检查项 | 计划口径 | 实际结果 | 判定 |
| --- | --- | --- | --- |
| same-task 汇总 | probe artifact 与 same-task gate 同一 `task_id` 关联 | smoke summary 同时回显 same-task gate、cloud external probe、cloud DB/queue probe 的 readback 状态 | 通过 |
| O6 additive readback | O6 archive/readback 或 consumer detail 可回读 probe 摘要 | 已新增 `trashbot.o6.cloud_external_probe_readback.v1` 与 `trashbot.o6.cloud_db_queue_external_probe_readback.v1`，支持 archive detail、`field_evidence`、`artifact_bundle`、consumer detail 和 include 回读 | 通过 |
| phone-safe / fail-closed | 不泄露 URL、token、response body、本地路径 | hostile probe payload 仅降级对应 section 为 `blocked_not_proven`，不回显敏感内容 | 通过 |
| 安全不越界 | 不把 probe pass 推导成 production success 或 delivery success | 继续固定 `connects_cloud_production=false`、`delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false` | 通过 |
| 真实外部材料 | 若环境允许，可证明真实 production cloud / DB/queue / live endpoint | 当前仅有本地 relay software proof，没有真实 production cloud、production DB/queue 或真实公网 endpoint 证据 | 未通过，但符合 proof boundary |

## 用户价值核对

- 本轮新增价值：把“是否接到 live endpoint / DB / queue probe 结果”纳入同一 `task_id` 的 O5/O6 证据链，减少后续接入真实 production cloud 时的人工对照成本。
- 本轮未达成价值：没有把真实公网 HTTPS/TLS、真实 4G/SIM、真实 production DB/queue 或真实手机/browser 验收带进证据链。

## OKR 方向判断

- 判断：继续。
- 原因：本轮是对 O5/O6 最低并列项的有效小步推进，但已触到 local/mock probe wrapper 的上限。
- 约束：下一轮若仍没有真实 production cloud / production DB/queue external probe / 真实 live endpoint evidence，O5/O6 不应继续靠同类 local/mock 包装提升百分比。

## 验收结论

- 本轮可验收为 `software_proof_o5_o6_live_endpoint_probe_readback_only`。
- 不可验收为真实 production cloud、production DB/queue、真实 delivery success 或真实手机/browser 闭环。
