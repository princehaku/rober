# O6 Artifact Seed Media Preflight Pre-Start

- sprint_type: epic
- start_time: 2026-07-09 07:55 CST
- automation_id: rober-okr
- product_owner: product-okr-owner
- target_objectives: O6, O7
- primary_owner: robot-software-engineer
- collaborating_owner: full-stack-software-engineer

## 上轮状态

最近三轮 O6/O7 sprint 已完成：

- `sprints/2026.07.09_02-31_o6_field_evidence_archive_ingest/`：field evidence manifest 可写入 O6 local/mock archive 并由 consumer read 回读。
- `sprints/2026.07.09_05-51_o7_route_replay_labeling_mvp/`：O7 consumer detail 可围绕同一 `task_id` 展示 route replay MVP 与 labeling MVP。
- `sprints/2026.07.09_06-53_o6_o7_annotation_submit_export/`：local/mock annotation submit receipt 与 task-level JSONL export 主路径通过。

这些 sprint 没有因同一硬 blocker 连续 blocked；共同结论是下一轮必须优先消费 `route.csv`、replay JSONL、keyframe 或 media ref 可访问性证据，避免继续堆叠 local/mock wrapper。

## 本轮目标

本轮继续推进当前完成度最低的 O6（约 36%），并让 O7（约 37%）直接消费 O6 新增证据。核心目标是把现场 artifact seed 从“manifest 摘要可 ingest”推进到“可复现导入 route/replay/keyframe 摘要，并在 PC 侧看到 media preflight/可访问性状态”。

本轮仍是软件侧证明，不声明真实生产云、真实 OSS、真实 4G/TLS、真实机器人控制、真实视频或 delivery success。

## Blocker 核对

- 未重复消费同一 blocker：最近两轮 final 的主要结论均为验收通过，边界为 local/mock software proof，不是 blocked。
- 真实生产 DB/queue、OSS、TLS/4G、真实隧道和真实机器人数据仍缺；本轮不等待这些外部条件，使用本地 artifact fixture 和 local/mock archive 推进。
- 所有危险能力必须继续 fail-closed：`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。

## 验收口径

- O6 必须新增可复现 artifact seed/readback 证据，不能只新增文档或状态字段。
- O7 必须从 O6 consumer detail 主路径消费新增 artifact/media 状态，不能只做独立 fixture 展示。
- 必须运行 O6 单测、O7 测试/build/lint，以及 `git diff --check`。
