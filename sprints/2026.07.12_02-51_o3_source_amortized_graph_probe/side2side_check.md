# Side-by-Side Check - O3 Source-Amortized Graph Probe

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_02-51_o3_source_amortized_graph_probe/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Closeout time: `2026-07-12 03:16 CST`
- Product verdict: accepted as O3/O1 supporting no-motion diagnostic progress only.

## User Value And North Star

北极星仍是普通手机用户一键让机器人沿固定路线送垃圾。本轮用户价值不是证明送达，而是纠正上一轮 graph timeout 的测量层，让下一条工程命令从“继续怀疑 CLI/plugin/import”收敛到“定位 ROS2 daemon / DDS graph discovery timeout 与 managed lifecycle/TF secondary”。

## Requirement Check

| PRD / Tech-plan gate | Evidence | Product decision |
|---|---|---|
| Source-amortized batch 必须存在 | `proof.ros2_graph_timeout_root_cause.probes.source_amortized_batch.boundary=source_amortized_batch_completed` | 通过 |
| 单次 source 后区分 source overhead 与命令 timeout | source stage elapsed about `5984ms`; `ros2_node_list_help.boundary=ros2_node_list_help_ok`; `ros2_node_list.boundary=ros2_node_list_timeout`; `ros2_topic_list.boundary=ros2_topic_list_timeout` | 通过 |
| rclpy graph stage stream 必须能说明卡点 | `rclpy_graph_stage_stream.boundary=rclpy_graph_nodes_observed`; node count `21` | 通过 |
| 分类必须优先使用 source-amortized evidence | `evidence_priority=source_amortized_batch`; classification `ros2_daemon_or_dds_graph_discovery_timeout`; primary reason `ros2_node_list_timeout` | 通过 |
| final artifact 不能停在 partial command | `status=blocked_with_root_cause`; `artifact_kind=final`; `current_command=null` | 通过 |
| no-motion 边界必须保持 false | `path_generation_attempted=false`; `path_generated=false`; `safe_to_control=false`; `publishes_cmd_vel=false`; `calls_base_manual=false`; `robot_control_executed=false`; `route_execution_success=false`; `delivery_success=false`; `hil_pass=false`; `uses_base_uart=false` | 通过 |

## Superseded Previous Reason

上一轮 `ros2_node_list_help_timeout_and_rclpy_graph_segment_probe_timeout` 不再作为当前主因。原因是本轮 source-amortized batch 证明：

- `ros2 node list --help` 在单次 source 后可完成，边界为 `ros2_node_list_help_ok`。
- rclpy graph stage stream 已观察到 graph nodes，边界为 `rclpy_graph_nodes_observed`，node count 为 `21`。
- 真正剩余的是 `ros2 node list`、`ros2 topic list` 等 graph discovery command timeout。

因此 Product 接受新的主分类 `ros2_daemon_or_dds_graph_discovery_timeout`，同时把 managed lifecycle 与 TF 保留为 secondary remaining candidates。

## OKR Decision

- O5：继续约 `85%`，`不调整`。本轮没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker/cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence。
- O1：继续约 `93%`，`不调整`。本轮没有 current same-run path generation success、Nav2 route execution success、current live HIL pass、safe-to-control 或底盘运动证据。
- O6：继续约 `93%`，`不调整`。本轮没有新的 route/delivery/operator/production material 可供 archive/readback 消费。
- O7：继续约 `93%`，`不调整`。本轮没有新的 operator-facing delivery acceptance、route replay completion 或 production evidence。
- KR：`不归档`。没有 KR 达到完成、取消、替换或过期归档条件。

## Remaining Risk

- ROS2 daemon / DDS graph discovery 在真实板上仍 timeout，`ros2 node list` 与 `ros2 topic list` 不能作为稳定 graph readback。
- managed lifecycle readiness、map server / AMCL 状态、TF visibility 仍是 secondary blocker。
- 本轮没有 `map.yaml`、`route.csv`、keyframe、rosbag、replay JSONL、delivery record、operator acceptance、current live HIL 或 production cloud evidence。

## Next Acceptance Target

下一轮继续由 `robot-algorithm-engineer` 负责 O3/O1 no-motion lane，优先把 `ros2_daemon_or_dds_graph_discovery_timeout` 拆到 daemon lifecycle、DDS discovery、domain/env mismatch、managed process lifecycle 或 graph command budget 的具体层。graph/lifecycle/localization gate clean 前，不允许进入 path generation、NavigateToPose、`/cmd_vel`、`/api/base/manual` 或 WAVE ROVER UART。
