# Pre Start - O3 28-Pose Same-Task Replay Packet

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Planning status: ready for PRD and tech plan
- Start time: 2026-07-13 05:02 CST
- Proof boundary target: `software_proof_o3_o1_strict_no_motion_same_task_route_replay_packet_only`

## 用户价值和产品北极星

北极星仍是固定路线送垃圾任务的可验证闭环：普通手机用户交付垃圾后，小车沿固定路线完成送达，并且每次任务有可复盘证据。本轮不做发车、不做控制、不做送达；用户价值是把 04:02 已 accepted 的 28-pose fixed-route CSV/JSONL 材料推进为同一任务可消费的 route replay / material packet，减少后续受控 route execution 前的证据断点。

## 上轮事实输入

上轮已 accepted：`sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer/`。

可作为本轮 primary input 的事实：

- Summary: `sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer/artifacts/algorithm/fixed_route_28_pose_consumer_summary.json`
- `route_csv`: `sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer/artifacts/algorithm/fixed_route_28_pose_route.csv`
- `replay_jsonl`: `sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer/artifacts/algorithm/fixed_route_28_pose_replay.jsonl`
- `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `path_structured_pose_count=28`
- `fresh_28_pose_structured_material_consumed=true`
- `historic_21_57_artifact_primary_source=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `safe_to_control=false`

## OKR 和方向判断

当前最低进度 Objective 是 Objective 5 / O5，约 `85%`。但 O5 的下一步只有接入真实 external production evidence，包含 HTTPS/TLS、公网入口、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser，才可继续计主进度。当前环境没有这些外部材料，继续做 readiness、checklist、wrapper 或 cutover packet 会重复消费同一 blocker。

本轮方向判断：继续 O3/O1 strict no-motion evidence chain，暂停 O5 support-only 包装；不调整 OKR 百分比，不归档 KR。本轮只把 04:02 的 28-pose fixed-route consumer material 推进为 same-task route replay / material packet 或等价 consumer integration artifact。

## 本轮核心抓手

核心抓手不是再导出一次 28-pose，也不是再生成 route-intent 文案，而是让 Algorithm worker 消费 04:02 的 summary、route_csv 和 replay_jsonl，输出同一 `task_id` / `route_intent_id` 下的 replay/material packet：

- 证明 CSV 与 JSONL 同源、同 task、同 route intent。
- 证明 28 个 pose 的 order、source_index、frame、position、orientation 可被 replay consumer 顺序读取。
- 证明 material packet 包含 `route_csv`、`replay_jsonl`、summary ref、hash/count/readback 状态和下一步缺口。
- 保持全部 safety fields false。

## Owner 和协作边界

- 单 owner：`robot-algorithm-engineer`
- Product 本轮只负责 sprint planning，不改产品代码、测试代码、硬件配置或 OKR.md。
- Algorithm worker 负责后续实现、验证、修复和 `tech-done.md` 留档。
- 不需要 Hardware owner：本轮不碰 WAVE ROVER、UART、串口、波特率、引脚、电压或机械事实。
- 不需要 Full-stack/O6/O7 owner：本轮不是 PC UI、cloud archive/readback 或 production evidence。

## 需要做什么

1. 创建 strict no-motion same-task route replay / material packet。
2. 消费 04:02 `route_csv` 和 `replay_jsonl`，不得只复制 summary 字段冒充 packet。
3. 输出机器可读 summary JSON，至少包含 `task_id`、`route_intent_id`、`route_csv_ref`、`replay_jsonl_ref`、row/event count、source hash、packet status、rejected claims 和 safety fields。
4. 输出 replay/material packet JSONL 或等价 consumer integration artifact，证明 28 个 pose 已按同一任务顺序读入。
5. 写 `tech-done.md`，记录实际改动、验证结果、失败定位和剩余风险。

## 风险、阻塞和证据链缺口

- 本轮仍不是 route execution、NavigateToPose、controller/BT、`/cmd_vel`、`/api/base/manual`、WAVE ROVER UART、delivery、HIL 或 safe-to-control。
- 若 worker 只生成 helper/export/readiness/route-intent 文案，而没有消费 `route_csv` 与 `replay_jsonl`，Product 不接受。
- 若 packet 不能保持 `route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`，必须 fail closed。
- 真正提升 O1/O3 证据强度的下一层仍是受控 route execution record、delivery/operator acceptance、current live HIL 或安全准入后的实跑材料；当前 sprint 不声明这些。

## Sprint 文档要求

本轮是 Epic planning，必须先完成：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续实现 worker 完成后再补：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
