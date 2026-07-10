# O6/O7 Route Execution Result Delivery Readiness PRD

## 用户价值

运营人员需要在同一 `task_id` 下判断三件事：路线是否执行到了“有结果可读”的程度、投递结果是否已有结构化 readiness、操作员确认是否已有可回读的确认 readiness。没有这条结果链，PC 端和后续手机端只能看到过程摘要，却无法回答“这次任务最后走到了哪一步、还差什么材料才能判定 delivery outcome”。

## 产品北极星

北极星仍是普通手机用户可验证地完成垃圾投递。本轮的产品价值，是把路线执行结果和投递确认材料从“下一步建议”推进为“同一 `task_id` 下能被读回、展示、继续追证的统一 readiness 结果”。这仍然只是 software proof，不替代真实 live Nav2、真实 delivery record、真实 operator confirmation 或真实 delivery success。

## OKR 映射和方向判断

- O6 对齐：继续增强任务记录、事件/证据存档和 consumer read API，让 route execution result 与 delivery/operator confirmation readiness 可被 archive/detail/include 回读。
- O7 对齐：让 PC 端 consumer detail / UI 能围绕同一 `task_id` 展示 route execution status、delivery readiness、operator confirmation readiness、blocked reasons 和 next evidence。
- 方向判断：继续推进 O6/O7，并把优先级从 route replay 证据切到结果链路 readiness，避免继续做只读 wrapper 型 sprint。
- KR 历史归档判断：本轮不归档 KR；工程完成后若仍只有 local/mock proof，也只能保守提升 O6/O7 进度，不进入历史完成区。

## 需求范围

1. Algorithm 结果摘要
   - 输入允许沿用已有 fixture/mock/离线 route 材料。
   - 输出新增或扩展 `route_execution_result_delivery_readiness` 类摘要，至少覆盖：
     - `task_id`
     - `proof_scope`
     - `route_execution_result_status`
     - `route_execution_source`
     - `delivery_result_readiness_status`
     - `delivery_result_source`
     - `operator_confirmation_readiness_status`
     - `operator_confirmation_source`
     - `blocked_reasons`
     - `next_required_evidence`
     - false safety fields
   - 允许有计数、短标签、basename ref、sha256 prefix、时间戳范围等安全摘要。
   - 禁止输出绝对路径、token、完整 payload、原始消息、控制 topic、完整 hash、任何真实投递完成暗示。
   - 缺字段、危险 true、unsafe 文本、schema mismatch、结果自相矛盾时 fail-closed。

2. O6 archive/readback
   - `field-evidence`、`artifact-bundle`、archive task detail、consumer detail 和 `include=` 支持读回 route execution result / delivery/operator confirmation readiness。
   - O6 仅保留安全白名单摘要，不放大为 live run 或生产云成功声明。
   - 对坏 schema、危险字段、unsafe 文本、必填缺失一律降级为 `blocked_not_proven`。

3. O7 consumer/UI
   - consumer adapter 从 O6 合法位置归一化读取 route execution result / delivery readiness / operator confirmation readiness。
   - UI 只读展示结果状态、readiness 状态、blocked reasons、next evidence、样本 refs 和 false safety fields。
   - 不解锁 submit/control/play/dispatch 等动作，不把 readiness 显示成完成。

## 非目标

- 不证明真实 production cloud、真实 4G/TLS、production DB/queue、真实 OSS/CDN live traffic。
- 不证明真实 live Nav2 route execution、真实 robot motion、真实底盘控制或 wheel raw 非零。
- 不证明真实 delivery record、真实 operator confirmation、真实 delivery success、真实 dropoff completion。
- 不启动 ROS2 runtime，不发送 `/cmd_vel`，不下发 live Nav2 goal，不触发任何硬件动作。
- 不更新 `OKR.md`、不更新 `docs/process/`，当前任务只创建本轮 sprint 初始文档。

## 验收口径

- Algorithm owner 的实现必须能通过：
  - `python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py`
  - `python3 -m unittest onboard.tests.test_field_route_evidence_manifest`
- O6 owner 的实现必须能通过：
  - `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`
- O7 owner 的实现必须能通过：
  - `cd pc-tools/workstation && npm run test && npm run build && npm run lint`
- Product 收口必须能用精确文件范围执行 `git diff --check -- ...`，并核对 sprint 文档、worker report 和结果 token。
- 全链路必须保持：
  - `safe_to_control=false`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
  - `robot_control_executed=false`

## 优先级

P0：打通同一 `task_id` 的 route execution result + delivery/operator confirmation readiness 主链路。

P1：O7 清晰展示 blocked reasons、next evidence 和 false safety fields，让运营知道下一步还缺什么。

P2：后续再接真实 live Nav2 result、真实 delivery record、真实 operator confirmation 和 production cloud 证据。

## 对应责任 Engineer

- `robot-algorithm-engineer`
- `robot-software-engineer`
- `full-stack-software-engineer`

## 风险、阻塞和需补齐证据链

- 当前最大风险是“readiness 被误读为完成结果”。文案、schema 和 UI 都必须保持 not_proven 边界。
- 当前仍缺真实 live Nav2 route execution result、真实 delivery record、真实 operator confirmation、真实 production cloud。
- 若任一 owner 只能继续增加 wrapper，而无法产出同一 `task_id` 的结果链摘要，应视为偏离目标并在 worker report 中说明。

## 已完成 KR 的历史记录位置

- 本轮不移动 KR 到历史区。
- 已完成/已归档 Objective 仍以 `OKR.md` 的“已归档 Objective（软件侧完成，等待真实现场验证）”和 `docs/process/okr_progress_log.md` 为准。
- 本轮证据来源的前置 sprint 主要是：
  - `sprints/2026.07.09_19-00_o6_o7_route_bag_semantic_replay/final.md`
  - `sprints/2026.07.09_20-03_o6_o7_route_bag_pose_progress_replay/final.md`
- 剩余风险：上述历史证据仍然只证明 software proof，不代表真实现场闭环。

## 需要创建或更新的 sprint 文档

- 当前创建：
  - `pre_start.md`
  - `prd.md`
  - `tech-plan.md`
- 后续工程完成后需更新：
  - `tech-done.md`
  - `side2side_check.md`
  - `final.md`
