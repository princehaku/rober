# O7 Offline Manifest Consumer Detail Pre Start

## sprint_type: micro

## 背景

上一轮 `sprints/2026.06.09_21-03_board-offline-evidence-intake/` 已完成离线 evidence packet 到 `trashbot.field_evidence_manifest.v1` 的生成和安全校验，但 PC O7 consumer-detail 主路径仍主要依赖 O6 detail 已经内嵌 `field_evidence_manifest` 或 `field_evidence_consumer_ingest`。

本轮把上一轮生成的本地 manifest 接入 PC consumer-detail 主路径，避免继续只做独立 preview surface。

## 目标

在不连接真实云、不发送机器人控制、不声明送达成功的前提下，让 operator 可以在 O7 consumer detail 加载时提供本地 `fieldEvidenceManifestJson`，用于补齐 O6 detail 缺失的 field evidence 摘要。

## Owner

- 主责：`full-stack-software-engineer`
- 只读事实来源：上一轮 `tech-done.md` 和 `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`

## 边界

- 不触碰 ROS2、WAVE ROVER、UART、launch 或硬件参数。
- 不通过 SSH 访问 `root@192.168.1.11 -p 37878`，避免重复消费同一网络 blocker。
- 不把 `gate_pass=true` 渲染成 `delivery_success=true`。
- 所有新增入口必须保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。

## 验收口径

- O6 detail 缺少 field evidence 时，PC adapter 可用本地 `trashbot.field_evidence_manifest.v1` 补齐 `field_evidence`，并明确 `source_contract=trashbot.field_evidence_manifest.v1`。
- 本地 manifest 缺失、schema mismatch、坏 JSON 或危险 true claim 时 fail-closed。
- UI 中能看到该本地 manifest 输入和 fail-closed 摘要。
