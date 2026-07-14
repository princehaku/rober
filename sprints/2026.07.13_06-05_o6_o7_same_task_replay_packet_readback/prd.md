# PRD - O6/O7 Same-Task Replay Packet Readback

## 用户价值和产品北极星

产品北极星：普通用户最终只需要把垃圾交给小车，小车沿固定路线完成送达；工程侧必须能证明每条路线材料从生成、消费、回读到现场执行的证据链没有断。

本轮用户价值：把 05:02 已接受的 28-pose same-task replay packet 接入 O6 local/mock archive/readback 与 O7 PC consumer detail。运营或开发人员可以按同一 `task_id` 查看 packet 是否被消费、哪些材料已存在、哪些真实执行/交付材料仍缺失，从而避免下一轮继续重复 helper/export/readiness 包装。

## 背景事实

05:02 Product closeout 已接受：

- `packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`
- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- `route_csv_row_count=28`
- `replay_jsonl_event_count=28`
- `path_structured_pose_count=28`
- `same_task_identity_verified=true`
- `same_task_replay_packet_ready=true`

05:02 Product closeout 同时明确拒绝：

- route execution
- fixed-route movement
- NavigateToPose
- controller/BT execution
- `/cmd_vel`
- `/api/base/manual`
- WAVE ROVER UART
- delivery/operator acceptance
- current live HIL
- safe-to-control
- O5 production/external evidence
- O6 archive/readback
- O7 UI/consumer completion

## OKR 映射和方向判断

- O5：暂停本轮 support-only 推进。O5 约 `85%`，主要卡在真实 production/external evidence，不应继续靠 readiness/wrapper 涨分。
- O6：继续。O6 约 `93%`，本轮消费新的 same-task replay packet 到 local/mock archive/readback，是比重复 support wrapper 更具体的证据链增量。
- O7：继续。O7 约 `93%`，本轮让 PC consumer detail 能读同一 `task_id` 的 replay packet 摘要，服务运营调试与证据复盘。
- O1/O3：只作为 source evidence 背景。本轮不推动底盘/HIL/导航执行完成度。
- 方向判断：继续 O6/O7 read-only evidence consumption；暂停 O5 support-only wrapper；KR 暂不归档。

## KR 拆解、更新或历史归档

本轮不归档任何 KR。计划拆解如下：

- O6-KR：新增或复用本地/mock archive section，把 05:02 packet 转成安全 O6 readback 摘要。
- O6-KR：`GET /api/o6/consumer/tasks/<task_id>` 能按 include 返回 packet readback，固定 fail-closed 边界。
- O7-KR：PC consumer detail 默认或专项 include 能展示 packet id、route intent、counts、source refs、blocked reasons 和 next required evidence。
- O7-KR：UI/adapter 不把 packet readback 误译为真实路线执行、真实送达、HIL 或 safe-to-control。

历史记录位置：本轮完成后，若实现和验收通过，应在本 sprint `final.md` 记录证据来源、验收命令、OKR 影响和不归档理由。按当前文件范围，本轮规划不更新 `OKR.md` 或历史区。

## 本轮核心抓手

核心抓手是同一 `task_id` 的消费链：

```text
05:02 O3/O1 same-task replay packet
  -> O6 local/mock archive/readback safe summary
  -> O6 consumer detail include
  -> O7 PC consumer detail display
```

不得把这条链包装成 route execution chain。它只回答“packet 是否进入 O6/O7 可读模型”，不回答“车是否跑了”。

## 需要做什么

后续 full-stack owner 需要：

1. 读取 05:02 packet summary 与 packet JSONL，确认输入字段和 source hashes。
2. 在 O6 local/mock archive/readback 中加入 safe summary 消费路径，或用既有 same-task material section 做无歧义映射。
3. 在 O6 consumer read API 中按同一 `task_id` 暴露 packet readback section。
4. 在 O7 consumer read adapter 和 PC detail UI 中展示 packet readback。
5. 补充 O6 Python tests 与 O7 Vitest/build/lint。
6. 更新相关 docs，并在 sprint `tech-done.md` 记录实际改动、验证结果和剩余风险。

## 非目标

- 不执行 Nav2 route。
- 不发送 `/cmd_vel`。
- 不调用 `/api/base/manual`。
- 不调用 WAVE ROVER UART。
- 不声明 route execution success。
- 不声明 delivery success。
- 不声明 HIL pass。
- 不声明 safe-to-control。
- 不接真实 production cloud、DB、queue、OSS/CDN 或公网 HTTPS/TLS。
- 不新增手机端普通用户发车入口。

## 优先级和验收口径

优先级：P0 for O6/O7 evidence consumption。

验收必须同时满足：

- O6: `remote_cloud_relay.py` py_compile 通过。
- O6: targeted unittest 通过。
- O7: workstation test/build/lint 通过。
- Contract: O6 consumer detail 可按 `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402` 回读 packet section。
- Contract: O7 detail 保留 selected task id，不因缺其他 section 丢失 routing context。
- Contract: packet identity 和 28-pose counts 与 05:02 source 完全一致。
- Safety: 所有控制、交付、HIL、安全字段保持 false。
- Docs: 相关 `docs/` 合同同步说明本轮 readback 是 local/mock software proof，不是 route execution 或 delivery proof。

## 对应责任 Engineer

- 主责：`full-stack-software-engineer`
- 可咨询：`robot-software-engineer`，仅限 O6 relay/store contract 事实确认。
- 不需要：`robot-algorithm-engineer`，除非后续发现 05:02 packet artifact 缺字段且必须重新生成。
- 不需要：`rober-hardware-engineer`，本轮无硬件集成。

## 风险、阻塞和需要补齐的证据链

- 风险：若把 `same_task_replay_packet_ready=true` 映射成 `route_execution_material_consumed=true`，会误导 OKR 计分；必须命名和状态上明确 readback-only。
- 风险：O7 默认 include 已覆盖很多 section，新增 packet section 可能和 `same_task_route_execution_material_packet` 混淆；UI 文案和 schema 字段要区分 replay packet 与 execution material packet。
- 风险：O6 archive/readback 若只保存 raw refs 或绝对路径，会违反安全摘要边界；只能保存 basename、counts、sha256 prefix 和短 safe status。
- 仍需补齐证据链：受控 route execution record、真实 delivery/operator acceptance、current live HIL、safe-to-control、production/external cloud evidence。

## 已完成 KR 的历史记录位置、证据来源和剩余风险

本轮规划阶段没有完成或归档 KR。已有 source evidence 位于：

- `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/final.md`
- `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/artifacts/algorithm/same_task_replay_packet_summary.json`
- `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/artifacts/algorithm/same_task_route_replay_packet.jsonl`

剩余风险保持：source packet 仍是 strict no-motion offline packet，不是 route execution、delivery、HIL、safe-to-control 或 O5 production/external evidence。

## 需要创建或更新的 sprint 文档

本阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续实现完成后必须补：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
