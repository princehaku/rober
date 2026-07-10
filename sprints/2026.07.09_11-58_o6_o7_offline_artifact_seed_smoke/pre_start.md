# O6/O7 Offline Artifact Seed Smoke Pre Start

## Sprint Type

sprint_type: epic

## 背景

本轮是 O6/O7 的双目标 epic sprint，目标不是继续堆叠只读 wrapper，而是把已有离线路线材料真正纳入一条可重复的 seed smoke 计划：

- `sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/`
- `sprints/2026.06.10_02-05_field-run-bundle-replay-intake/artifacts/derived_replay.jsonl`

前一轮 O6/O7 已经把 local/mock archive、consumer read、annotation submit/export、artifact media preflight、artifact bundle 和 artifact access probe 的软件合同补齐到可读状态，但仍缺“离线路线材料如何稳定进入同一 task_id 并贯穿 O6/O7”的 seed smoke 计划。本轮只先把计划文档补齐，后续实现阶段再进入具体代码与测试。

## 目标

把以上离线材料作为固定 seed，建立一条可复用的 O6/O7 offline artifact seed smoke 计划，让后续实现阶段可以验证：

1. O6 能把离线 route / replay 材料绑定到同一 `task_id` 并产出可读摘要。
2. O7 能消费同一 `task_id` 下的 O6 摘要，并以 fail-closed 方式展示 readiness、blocked reasons 和 next evidence。
3. 全链路保持软件侧边界，不触发真实机器人控制、底盘动作、串口、云端生产写入或现场任务执行。

## 证据输入

- `sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/route/route.csv`
- `sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/route/manifest.json`
- `sprints/2026.06.10_02-05_field-run-bundle-replay-intake/artifacts/derived_replay.jsonl`
- `sprints/2026.06.10_02-05_field-run-bundle-replay-intake/artifacts/field_run_manifest.json`

## Owners

- `robot-software-engineer`：负责 O6 offline seed ingest/readback 计划、后续实现与验证主链路。
- `robot-algorithm-engineer`：负责离线路线材料的语义整理，确认 route / replay / manifest 的对应关系与 task_id 绑定方式。
- `full-stack-software-engineer`：负责 O7 consumer detail 的展示计划，保证 UI 只消费摘要，不把 ref 字符串误报成真实可读媒体。
- `product-okr-owner`：负责本 sprint 的 OKR 对齐、验收口径和收口判断。

## 重复 Blocker 检查

最近两轮收口都没有形成同一 blocker 的连续消费，本轮不需要升级 CEO 求决策。

本 sprint 选择离线材料而不碰真实硬件或生产云，是为了主动避开尚未完成的现场环境依赖，而不是因为新 blocker 出现。

## 风险边界

- `safe_to_control: false`
- `delivery_success: false`
- `primary_actions_enabled: false`
- `robot_control_executed: false`

本轮不声明真实投递、真实机器人控制、真实云端生产写入、真实媒体可访问或真实路线验收完成。
