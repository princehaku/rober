# O6/O7 Field Motion Evidence Packet Final

## sprint_type: epic

## 用户价值和产品北极星

本轮把已有 6 月现场路线材料推进成一个可以被 O6 archive 和 O7 consumer 共同消费的 `field_motion_evidence_packet`。它解决的不是“又多一个 local/mock wrapper”，而是让同一 `task_id` 下的 `map/route/keyframe/motion-log/replay` 开始形成可回放、可归档、可标注的现场运动证据链。

产品北极星不变：普通手机用户把垃圾交给机器人后，机器人要可验证地完成投递。本 sprint 只把现场运动证据链往前推一格，不宣称真实送达、真实控制或真实生产云闭环。

## OKR 映射和方向判断

- 目标 Objective：O6、O7
- 方向判断：继续
- 进度调整：
  - O6：约 `47% -> 50%`
  - O7：约 `47% -> 50%`
- 调整理由：
  - O6 新增对 `field_motion_evidence_packet` 的 additive ingest/readback，且 readback 验证达到 `Ran 155 tests in 53.281s OK`。
  - O7 已消费同一 packet 到 consumer detail、artifact bundle readiness、route replay、labeling workspace，且前端验证达到 `3 passed / 476 passed`、build、lint 通过。

## KR 拆解、更新或历史归档

- O6 KR2：同一 `task_id` 的路线帧、运动摘要、事件线索进一步靠近真实现场材料，archive/read model 继续前进。
- O6 KR6：consumer read 主路径已能回读 `field_motion_evidence_packet`，O6 数据消费合同继续增强。
- O7 KR3：历史路线回放从 route-root seed/offline seed smoke 推进到 field motion evidence packet 消费，离真实路线回放又近一层。
- O7 KR4：标注工作台现已能围绕同一 packet 判断证据是否足够，减少只看摘要的盲区。
- KR 历史归档判断：本轮不归档任何 KR。
- 不归档理由：`software_proof_field_motion_evidence_packet_only` 仍不证明真实 production cloud、真实 `route_bag`、真实 Nav2 live run、真实 delivery success、真实 OSS/CDN、真实 annotation API/export。

## 本轮核心抓手

把 `field_motion_evidence_packet` 作为 O6/O7 共用的现场运动证据合同，而不是继续增加与真实材料脱节的 wrapper。

## 需要做什么

1. 先补 `nonzero_odom_capture_or_bag_replay`，让运动证据从 TF/route displacement 提升到更强 odom 或 bag replay 级别。
2. 补 `route_bag_or_live_nav2_log_with_pose_progress`，优先争取真实 `route_bag` 或更强 live Nav2 pose progress 证据。
3. 再补 `nav2_goal_result_or_delivery_record`，把现场运动证据推进到任务完成或送达记录。

## 优先级和验收口径

- 当前优先级：O3 现场路线证据 lane 仍高于 O6/O7；在 O6/O7 内，本轮之后优先补更强现场运动证据，而不是继续叠加 summary surface。
- 下一轮验收口径应至少满足以下之一：
  - 真实 `route_bag` 可被 packet 消费；
  - 非零 odom capture / bag replay 证据补齐；
  - Nav2 目标结果或 delivery record 进入同一 `task_id` 的证据链。

## 对应责任 Engineer

- `robot-algorithm-engineer`：补 `route_bag`、非零 odom / Nav2 pose progress、delivery record 等现场运动强证据。
- `robot-software-engineer`：维护 O6 packet ingest/readback 合同，并接住更强现场证据输入。
- `full-stack-software-engineer`：让 O7 route replay / labeling workspace 继续消费更强 packet 证据，而不是重新退回 wrapper。
- `product-okr-owner`：维护 O6/O7 保守进度、验收边界和 KR 不归档判断。

## 风险、阻塞和需要补齐的证据链

- 当前 packet 仍有 `source_manifest_task_id_missing`，需要后续现场材料提供原生 `task_id`。
- `direct_odom_capture_nonzero=false`，说明当前 motion proof 仍偏向 TF/route 位移证据。
- `route_bag_present=false`，真实 bag replay 仍缺。
- 仍缺 `nav2_goal_result_or_delivery_record`，所以离“真实送达闭环”还有明显距离。

## 已完成 KR 的历史记录位置、证据来源和剩余风险

- 本轮无新增已完成 KR，因此没有 KR 移入历史区。
- 历史记录更新位置：`docs/process/okr_progress_log.md` 新增本 sprint 条目。
- 证据来源：本 sprint artifacts 中的 `field_motion_evidence_manifest.json`、`derived_replay.jsonl` 以及对应 worker 验证结果。
- 剩余风险：真实 production cloud、真实 `route_bag`、真实 Nav2 run、真实 annotation/export、真实 delivery success 均未证明。

## Sprint 文档更新

- 已创建：
  - `tech-done.md`
  - `side2side_check.md`
  - `final.md`
- 已同步更新：
  - `OKR.md`
  - `docs/process/okr_progress_log.md`

## 安全旗标

safe_to_control: false
delivery_success: false
primary_actions_enabled: false
robot_control_executed: false

## 收口结论

本 sprint 收口通过。O6/O7 基于同一 `field_motion_evidence_packet` 的软件侧现场运动证据链已经建立，可以把进度保守上调到约 `50%`，但不得把任何 KR 标为完成或归档。
