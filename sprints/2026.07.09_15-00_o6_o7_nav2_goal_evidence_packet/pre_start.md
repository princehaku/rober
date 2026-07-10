# O6/O7 Nav2 Goal Evidence Packet Pre-Start

## sprint_type: epic

## 背景

`OKR.md` 4.1 当前最低 active Objective 为 O6 与 O7，均约 50%。最新完成的 `sprints/2026.07.09_14-00_o6_o7_field_motion_evidence_packet/final.md` 已把 6 月现场 `map.yaml/.pgm`、`route.csv`、keyframes、remote_capture motion logs 与 `derived_replay.jsonl` 归一到同一 `task_id` 的 `field_motion_evidence_packet`，但收口也明确下一步必须补：

- `nonzero_odom_capture_or_bag_replay`
- `route_bag_or_live_nav2_log_with_pose_progress`
- `nav2_goal_result_or_delivery_record`

O3 现场路线证据 lane 仍是更高优先级，因为真实路线采集、Nav2 实跑、关键帧和 bag/replay 证据最终决定送垃圾闭环是否可信。本轮仍选 O6/O7，是因为已有 `onboard/scripts/o11_nav2_goal_execution_proof.py` 产出的 Nav2 goal execution proof JSON 可以被当作现场路线/运动证据的上游摘要来消费：它不替代 O3 的实跑 lane，但能让 O6 archive 与 O7 consumer 围绕同一 `task_id` 先接住 Nav2 goal/result 证据字段。

## 最近两轮 blocker 扫描

- `sprints/2026.07.09_14-00_o6_o7_field_motion_evidence_packet/final.md`：完成态。主要剩余缺口是非零 odom/bag replay、route bag 或 live Nav2 pose progress、Nav2 goal result/delivery record，不是 blocked。
- `sprints/2026.07.09_12-58_o6_o7_route_root_seed_gate/final.md`：完成态。已解除 route-root seed 对 `route_bag` 的硬 gate，不是 blocked。
- 补充参考 `sprints/2026.07.09_11-58_o6_o7_offline_artifact_seed_smoke/final.md`：完成态。其下一步已被 12:58 与 14:00 sprint 继续推进。

结论：最近两轮不是同一 blocker 连续 blocked。本轮不消费真实 production cloud、真实硬件、真实底盘控制或真实 delivery success 缺口，而是使用现有 O11 proof fixture/离线证据推进 O6/O7 的证据归档与消费链路。

## 本轮目标

创建本轮 Epic sprint 的计划留档，为后续并行 Engineer 明确一条 additive 合同：把 O11 Nav2 goal execution proof JSON 归一成 `nav2_goal_execution_evidence` 摘要，并接入现有 `field_motion_evidence_packet`、O6 archive readback 与 O7 consumer detail。

核心抓手：

- 同一 `task_id` 下追加 `nav2_goal_execution_evidence`，不重写已有 `field_motion_evidence_packet` 合同。
- Algorithm 从 O11 proof JSON 生成或写入 packet 摘要。
- O6 只通过白名单字段回读该摘要，继续过滤危险 true、path/root/token/raw/base64。
- O7 只展示 readiness、blocked reasons 与 next evidence，不把软件证据误写成真实送达。

## 用户价值和产品北极星

用户价值是让“机器人是否真的朝目标执行过 Nav2 goal、执行结果是什么、下一条缺口是什么”进入可回放、可归档、可展示的证据链，而不是停留在脚本日志或无法被 O6/O7 消费的孤立 JSON。

产品北极星不变：普通手机用户把垃圾交给机器人后，机器人要可验证地完成投递。本 sprint 只推进 Nav2 goal/result 证据摘要进入数据链路，不宣称真实生产云、真实路线长期验收或真实送达成功。

## owner分工 / Owner 分工

- `robot-algorithm-engineer`：主责从 `onboard/scripts/o11_nav2_goal_execution_proof.py` 的 proof JSON 提取 `nav2_goal_execution_evidence`，并写入或关联到 `field_motion_evidence_packet`。
- `robot-software-engineer`：主责 O6 archive ingest/readback 的 additive 白名单字段，确保 consumer detail 可读且 fail-closed。
- `full-stack-software-engineer`：主责 O7 consumer detail 展示 readiness、blocked reasons、next required evidence 和 false safety fields。
- `product-okr-owner`：本轮只创建 `pre_start.md`、`prd.md`、`tech-plan.md`；后续实现完成后再收口 OKR 与 sprint 文档。
- `rober-hardware-engineer`：本轮无硬件实现；若后续进入真实上车或真实硬件控制，必须按 `docs/vendor/VENDOR_INDEX.md` 二次确认硬件事实。

## 文件范围

本次 planning-only 动作只允许创建或更新以下三个文件：

- `sprints/2026.07.09_15-00_o6_o7_nav2_goal_evidence_packet/pre_start.md`
- `sprints/2026.07.09_15-00_o6_o7_nav2_goal_evidence_packet/prd.md`
- `sprints/2026.07.09_15-00_o6_o7_nav2_goal_evidence_packet/tech-plan.md`

不得提前创建 `tech-done.md`、`side2side_check.md`、`final.md`，不得修改产品代码、测试代码、`OKR.md`、`docs/process/okr_progress_log.md` 或其他 sprint 文档。

## 接口边界

- `nav2_goal_execution_evidence` 是 additive 摘要，不破坏既有 `field_motion_evidence_packet`、field evidence、artifact bundle、route-root seed gate 合同。
- 输入来自 O11 proof JSON 或其 fixture，不代表真实 live Nav2 run 已完成。
- `safe_to_control`、`delivery_success`、`primary_actions_enabled`、`robot_control_executed` 必须保持 false。
- 危险 true claim、原始路径、root、token、raw payload、base64 媒体或跨任务混合数据必须 fail-closed。

## safe flags false / 安全旗标

safe_to_control: false
delivery_success: false
primary_actions_enabled: false
robot_control_executed: false

## 预期收口

后续实现完成时，`tech-done.md` 必须给出 Algorithm/O6/O7 三路验证日志，证明同一 `task_id` 可看到 `nav2_goal_execution_evidence` 摘要，并继续明确它只是 `software_proof_nav2_goal_execution_evidence_only` 或等价边界，不证明真实 production cloud、真实硬件控制、真实 live Nav2 run、真实 delivery success 或真实用户送达。
