# Same-Task Mission Artifact Credit Gate Pre-start

## sprint_type

epic

## 背景

本轮自动化先读取 `AGENTS.md`、`OKR.md` 和 `rober-okr` automation memory。当前活跃 O1/O5/O6/O7 均约 85%，但最近多轮已经明确：O5/O6/O7 的 local/mock probe、SQLite shadow、checklist、readback-only wrapper 不能继续作为 OKR 百分比提升来源。

最近 2 轮相关 sprint：

- `sprints/2026.07.10_07-13_o5_o6_live_endpoint_probe_readback/final.md`：已完成但证据边界为 `software_proof_o5_o6_live_endpoint_probe_readback_only`，下一轮明确要求真实 production cloud、production DB/queue external probe 或真实 live endpoint evidence，否则 O5/O6 不能继续靠 local/mock probe wrapper 提升。
- `sprints/2026.07.10_06-10_o7_same_task_mission_material_checklist/final.md`：已完成但证据边界为 `software_proof_o7_same_task_mission_material_checklist_only`，下一轮要求消费真实或准现场 same-task mission materials，不再做只读 checklist/surface。

本轮不继续包装 probe/readback surface，而是把“是否允许计 OKR 主进度”的 gate 固化到 Algorithm manifest、O6 archive/readback 和 O7 consumer detail。若没有新 live/field mission artifact，本轮输出必须显式 `okr_credit_allowed=false` 和 `support_only_reason`，不能再把 support-only 工作算作主 OKR 增量。

## 本轮目标 Objective

- 主目标：O6 / O7，围绕同一 `task_id` 的 mission material 消费和只读回放链路。
- 关联目标：O5，因为 cloud terminal result / production cloud 证据是 same-task gate 的输入之一。
- O1 保持约 85%，本轮不声称补齐真实 WAVE ROVER 轮速非零反馈；旧真实材料只能作为 mission artifact 参考，不升级硬件完成度。

## 同一 blocker 避免

本轮避免连续消费以下 blocker：

- 无真实 production cloud / DB / queue / TLS / 4G 凭证。
- 无新增真实 delivery success、operator confirmation 或现场 route execution 材料。
- 无 WAVE ROVER L/R 非零 raw feedback。

处理策略：把这些缺口从“下一轮建议”提升为机器可读 gate。没有 mission artifact delta 时，后续 sprint 只能记 support-only regression，不允许提高 O5/O6/O7 百分比。

## Owner

- Robot Algorithm Engineer：扩展 `field_route_evidence_manifest.py` 的 same-task mission gate delta，增加 OKR credit 判定字段与 fail-closed 测试。
- Robot Software Engineer：扩展 O6 archive/readback 的 same-task mission gate summary，保留 `okr_credit_allowed`、`support_only_reason`、`live_or_field_command_executed` 等字段并新增回归测试。
- Full-stack Software Engineer：扩展 O7 consumer detail 和 UI/fixture，使 operator 能看到 OKR credit gate 状态，不把 support-only gate 渲染成 mission progress。
- Product OKR Owner：收口 OKR/进度日志/sprint 文档，明确本轮是否允许百分比变化。

## 验收口径

- `same_task_mission_evidence_gate` 或其 O6/O7 消费摘要必须包含：
  - `same_task_id_consumed`
  - `mission_artifact_delta`
  - `live_or_field_command_executed`
  - `support_only_reason`
  - `okr_credit_allowed`
- local/mock/readback-only/probe-only/checklist-only 输入必须 fail-closed 为 `okr_credit_allowed=false`。
- 真正允许 OKR 主进度时，必须同时满足同一 `task_id`、至少一种 live/field mission artifact delta、且所有 safety fields 仍为 false。
- 本轮不宣称 `delivery_success=true`、`safe_to_control=true`、`primary_actions_enabled=true` 或 `robot_control_executed=true`。
