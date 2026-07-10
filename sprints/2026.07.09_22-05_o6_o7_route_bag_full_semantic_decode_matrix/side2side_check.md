# O6/O7 Route Bag Full Semantic Decode Matrix Side2Side Check

## 对照结论

状态：通过，边界为 `software_proof_route_bag_full_semantic_decode_matrix_only`。

## PRD 对照

- P0 新 schema：已实现 `trashbot.route_bag_full_semantic_decode_matrix.v1` 与 O6 `trashbot.o6.route_bag_full_semantic_decode_matrix.v1`。
- Algorithm matrix：已按 topic/type 输出 decoded、unsupported、failed、coverage ratio、message sample counts 和 `topic_type_matrix[]`。
- O6 readback：已覆盖 field evidence、artifact bundle、archive task detail、consumer detail 和 `include=route_bag_full_semantic_decode_matrix`。
- O7 展示：已纳入 consumer detail、artifact bundle readiness 和 O7 preview UI。
- 安全边界：raw payload、base64、完整 hash、绝对路径、token、credential URL、`/cmd_vel` 和 dangerous true 均不允许进入输出；所有控制/送达字段保持 false。

## OKR 对照

- 本轮针对最低 active Objective：O6/O7 并列约 71%。
- 本轮实际推进：命中 `OKR.md` 中 O6/O7 反复列出的 `raw ROS message payload 全量语义解析/回放` 缺口，但只推进到 coverage matrix 和有限 decoder 软件证明。
- 保守进度判断：O6/O7 可从约 71% 上调到约 74%；不归档 KR。

## 验证证据

- Algorithm worker report：`sprints/2026.07.09_22-05_o6_o7_route_bag_full_semantic_decode_matrix/artifacts/algorithm_worker_report.md`
- O6 worker report：`sprints/2026.07.09_22-05_o6_o7_route_bag_full_semantic_decode_matrix/artifacts/o6_worker_report.md`
- O7 worker report：`sprints/2026.07.09_22-05_o6_o7_route_bag_full_semantic_decode_matrix/artifacts/o7_worker_report.md`

## 未通过或不覆盖项

- 不覆盖真实 production cloud。
- 不覆盖真实 live Nav2 route execution。
- 不覆盖真实 robot motion、delivery record、operator confirmation 或 delivery success。
- 不覆盖完整 ROS message payload 全量 decoder；unsupported/failed topic type 已作为可见缺口展示。
