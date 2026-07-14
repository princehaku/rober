# O3 Runtime Wait AMCL CLI Closeout Side-by-Side Check

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Closeout date: `2026-07-12`
- Outcome: `valid O3/O1 supporting no-motion diagnostic delta; final runtime wait artifact returned, but path generation remains blocked`

## 用户价值和产品北极星

产品北极星仍是普通手机用户把垃圾交给机器人后，机器人能沿固定路线稳定送达。本轮没有完成送达，也没有证明路线执行；本轮价值在于把真实板 no-motion runtime blocker 从旧的 partial `current_command=ros2 node list` 收口成 final artifact 里的 `ros2_node_list_timeout`，并把 AMCL CLI fallback 的参数读取结果纳入 closeout，为下一步恢复 `/tf` / `/tf_static` 和 path gate 提供更窄入口。

## Plan vs Done

| 计划验收点 | 实际证据 | Product 判断 |
| --- | --- | --- |
| 不回到 O5 support-only | 本轮仅改 Algorithm helper/tests/docs、tech-done 和 artifacts；未触碰 O5/O6/O7/UI/cloud | 通过。O5 继续约 85%，无 external evidence 不计增量。 |
| 写出 final `managed_runtime_wait_result` | live artifact 为 `status=blocked_with_root_cause`、`evidence_type=blocked_with_root_cause`、`artifact_kind=final`、`last_phase=final`、`current_command=null` | 通过。旧 partial current command 已关闭。 |
| 收敛 graph wait root cause | primary root cause 为 `layer=Managed runtime wait`、`reason=ros2_node_list_timeout`；`managed_runtime_wait_result.reason=ros2_node_list_timeout`、`boundary=ros2_node_list_timeout` | 通过。当前 blocker 比 23-49 更窄。 |
| 消费 AMCL CLI fallback closeout | `tf_source_root_cause_detail.amcl_param_probe_boundary=cli_amcl_inventory_observed_amcl_params`、`amcl_param_probe_ok=true` | 通过。参数可读，但 TF topic 仍缺。 |
| gate 未 ready 前保持 no-motion path gate | `path_generation_attempted=false`、`path_generated=false` | 通过。没有越过 planner-only gate。 |
| 安全字段全部 fail-closed | `safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`uses_base_uart=false` | 通过。没有底盘控制、route execution、delivery 或 HIL。 |

## Live Artifact 验收事实

最终 live artifact `artifacts/live_o10_runtime_wait_amcl_cli_closeout.raw.json` 的 Product 采信字段：

- `status=blocked_with_root_cause`
- `evidence_type=blocked_with_root_cause`
- `artifact_kind=final`
- `last_phase=final`
- `current_command=null`
- `board_source_preflight_ready`
- `cli_invocation_timeout_s=6.0`
- `ros2_cli_invocation_ok=true`
- `rclpy_import_ok=true`
- `managed_runtime_started=true`
- `managed_runtime_wait_result.reason=ros2_node_list_timeout`
- `managed_runtime_wait_result.boundary=ros2_node_list_timeout`
- `graph_wait_summary.latest_ros2_node_list_boundary=ros2_node_list_timeout`
- `graph_wait_summary.latest_ros2_node_list_timed_out=true`
- `graph_wait_summary.fallback_used=true`
- `graph_wait_summary.fallback_observed=false`
- `graph_wait_summary.observed_node_names=[]`
- `tf_source_root_cause_detail.amcl_param_probe_boundary=cli_amcl_inventory_observed_amcl_params`
- `tf_source_root_cause_detail.amcl_param_probe_ok=true`
- `tf_source_root_cause_detail.reason=/tf_topic_missing`
- `tf_topics_observed./tf=false`
- `tf_topics_observed./tf_static=false`
- `commands.map_to_odom_tf.boundary=tf_probe_skipped_after_managed_runtime_graph_wait_blocked`
- `commands.scan_once.boundary=scan_probe_skipped_after_managed_runtime_graph_wait_blocked`
- `path_generation_attempted=false`
- `path_generated=false`
- `safe_to_control=false`

## 不能声明的结果

本轮不得声明：

- path generation success
- `path_generation_attempted=true`
- Nav2 route execution success
- delivery success
- operator acceptance
- current live HIL pass
- production cloud / external evidence success
- safe-to-control readiness

## OKR 映射和方向判断

- O5：保持约 `85%`，`不调整`。理由是本轮没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker/cutover、OSS/CDN live traffic 或真实手机/browser 证据。
- O1：保持约 `93%`，`不调整`。本轮是 O3/O1 supporting no-motion diagnostic delta，不是 current same-run path generation success 或 Nav2 route execution success。
- O6/O7：保持约 `93%`，`不调整`。本轮没有新 route execution、delivery、operator acceptance 或 production readback material。
- KR：`不归档`。没有完成可归档 KR。
- 方向：`继续` O3/O1 no-motion runtime graph / TF recovery lane；`暂停` O5 support-only lane。

## 失败定位

旧 blocker 已关闭：

- 旧 `board_source_preflight_ros2_cli_invocation_timeout` 不再成立，因为 `board_source_preflight_ready`、`cli_invocation_timeout_s=6.0`、`ros2_cli_invocation_ok=true`、`rclpy_import_ok=true`。
- 旧 `partial current_command=ros2 node list` 不再成立，因为 artifact 已自然返回 final，`current_command=null`。

新 blocker：

- `ros2 node list` 在 managed runtime wait 内继续 timeout，最终 root cause 是 `ros2_node_list_timeout`。
- AMCL CLI params 已 observed，但 `/tf` 与 `/tf_static` 仍未 observed，最终 TF reason 仍是 `/tf_topic_missing`。
- map/AMCL lifecycle、scan、map TF 和 path gate 因 graph wait blocker 被跳过或仍未 ready。

## 下一步建议

继续由 `robot-algorithm-engineer` 单线闭环，不回到 O5。下一轮优先定位为什么 sourced `ros2 node list` 在 managed runtime 后持续 timeout，尽管 preflight 已 ready 且 `rclpy_import_ok=true`；随后恢复 `/tf`、`/tf_static` 可见性，再判断是否允许 planner-only `ComputePathToPose` attempt。
