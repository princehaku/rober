# Field Route Evidence Manifest

`onboard/scripts/field_route_evidence_manifest.py` 生成 `trashbot.field_evidence_manifest.v1`。它是现场路线材料的 artifact gate，只读扫描材料目录，不发布 `/cmd_vel`，不启动导航，不修改 WAVE ROVER、ESP32、UART、串口、波特率、速度映射、底盘反馈协议或 launch 默认硬件参数。

这份 manifest 也可以直接喂给 `POST /api/o6/archive/field-evidence` 进入本地/mock O6 archive。那条链路只证明软件侧归档与读回，不证明真实云、真实 OSS、真实 4G、真实 TLS、真实控制或真实送达；O6 consumer detail 读回时会显式带上 `field_evidence_manifest` / `field_evidence_consumer_ingest` 作为来源摘要。

## 输入和输出

必需输入：

- `--mode local|ssh`
- `--artifact-root <dir>` 或 `--input <dir>`
- `--output <manifest.json>`

`--input` 是离线 evidence packet intake 的别名，语义等同于 `--artifact-root`。保留 `--artifact-root` 是为了兼容前序 SSH/manifest 脚本；新增 `--input` 是为了让现场人工导出的本地目录可以直接进入 sprint P0 验收命令，不需要再连 `root@192.168.1.11 -p 37878`。

可选输入：

- `--preflight-json <field_route_evidence_preflight.py 输出>`
- `--map-yaml <map.yaml>`：当 `--artifact-root` 指向 `artifacts/route/` 而 map 位于相邻 `artifacts/map/` 时必须显式传入。
- `--map-pgm <map.pgm>`：同上，必须显式传入相邻 map 图像，脚本不会隐式猜测任意父目录。
- `--derive-replay-jsonl <output.jsonl>`
- `--motion-log-root <remote_capture_dir>`：显式接入同一轮现场 `remote_capture/` 文本日志，生成 `field_motion_evidence_packet` 的 live motion 摘要。
- `--nav2-goal-proof-json <o11_nav2_goal_execution_proof.json>`：可选接入 O11 NavigateToPose 执行 proof JSON，生成 additive `nav2_goal_execution_evidence` 安全摘要，并同时写入 manifest 顶层和 `field_motion_evidence_packet.nav2_goal_execution_evidence`。
- `--delivery-result-json <delivery_result.json>`：可选接入本地/mock `trashbot.delivery_result.v1`，生成 additive `delivery_result_evidence` 安全摘要，并同时写入 manifest 顶层和 `field_motion_evidence_packet.delivery_result_evidence`。
- `--cloud-terminal-result-json <cloud_terminal_result.json>`：可选接入 O5 `trashbot.cloud_command_terminal_result.v1`，也兼容 `trashbot.cloud_command_result_reconciliation.v2` wrapper；在未提供 `--delivery-result-json` 时转换成同一个 additive `delivery_result_evidence`；如果两者同时提供，优先使用 `--delivery-result-json`。
- `--localization-path-material-json <38_pc_summary_after_map_fix.json>`：可选接入 same-run localization/path readback summary，生成 additive `localization_path_material_readback`，并同时写入 manifest 顶层和 `field_motion_evidence_packet.localization_path_material_readback`。
- `--field-operator-confirmation-json <operator_report_or_summary.json>`：可选接入真实上位机 operator report/latest result 或准现场 summary，生成 additive `field_operator_confirmation_material` 安全摘要，并同时写入 manifest 顶层和 `field_motion_evidence_packet.field_operator_confirmation_material`。
- `--pc-live-nav2-execution-material-json <pc_live_nav2_execution_material.json>`：可选接入 2026-07-03 PC live Nav2 execution 的短安全 JSON material，生成 additive `pc_live_nav2_execution_material` 安全摘要，并同时写入 manifest 顶层和 `field_motion_evidence_packet.pc_live_nav2_execution_material`。
- `--route-bag-db3 <route_bag_0.db3>`：可选接入 rosbag2 SQLite DB3，生成 additive `route_bag_evidence` 安全摘要，并同时写入 manifest 顶层和 `field_motion_evidence_packet.route_bag_evidence`；同一输入还会生成 `route_bag_payload_replay`（messages.data payload hash 摘要）、`route_bag_pose_progress_replay`（白名单位姿进度摘要）、`route_bag_semantic_replay`（白名单 ROS 语义统计）与 `route_bag_full_semantic_decode_matrix`（per topic/type 语义解码覆盖矩阵），它们都写入 manifest 顶层和 `field_motion_evidence_packet` 同名 section。
- `--route-bag-metadata-yaml <metadata.yaml>`：可选接入同一 route bag 的 metadata，只输出 basename、size、hash prefix 和安全状态。
- `--route-bag-source-label <safe-label>`：可选写入短 source label；绝对路径、credential URL、token/raw/base64 等文本会 fail closed，输出不会回显原值。

脚本会基于同一 `task_id` 的 `nav2_goal_execution_evidence`、`delivery_result_evidence`、`route_bag_pose_progress_replay` 和 `field_motion_evidence_packet.route_bag_or_live_nav2_log`，额外生成 `route_execution_result_delivery_readiness`。该 additive schema 固定为 `trashbot.route_execution_result_delivery_readiness.v1`，`proof_scope=software_proof_route_execution_result_delivery_readiness_only`，并同时写入 manifest 顶层与 `field_motion_evidence_packet.route_execution_result_delivery_readiness`。

脚本还会继续把同一 `task_id` 的 `nav2_goal_execution_evidence`、`delivery_result_evidence`、`route_execution_result_delivery_readiness` 与 `route_bag_pose_progress_replay` 收束成 `route_delivery_closure_packet`。该 additive schema 固定为 `trashbot.route_delivery_closure_packet.v1`，`proof_scope=software_proof_route_delivery_closure_packet_only`；`ready` 只表示软件证据闭合，状态固定为 `route_delivery_closure_ready_not_success_proof`，并同时写入 manifest 顶层与 `field_motion_evidence_packet.route_delivery_closure_packet`。

脚本最后会只读消费当前 manifest 已生成的 linked additive，生成 `same_task_mission_evidence_gate`。该 additive schema 固定为 `trashbot.same_task_mission_evidence_gate.v1`，`proof_scope=software_proof_same_task_mission_evidence_gate_only`；`ready` 状态为 `same_task_mission_gate_ready_not_success_proof`，blocked 状态为 `blocked_not_proven`，并同时写入 manifest 顶层与 `field_motion_evidence_packet.same_task_mission_evidence_gate`。它不读取 raw cloud terminal result、route bag payload、route.csv、keyframe 或任何原始路线文件，只消费已经脱敏的 `delivery_result_evidence`、`route_execution_result_delivery_readiness`、`route_delivery_closure_packet` 和 `route_bag_pose_progress_replay` 摘要。

脚本也会直接从同一 `artifact_root` 的路线材料生成 `same_task_field_material_packet`。该 additive schema 固定为 `trashbot.same_task_field_material_packet.v1`，`proof_scope=software_proof_same_task_field_material_packet_only`，并同时写入 manifest 顶层与 `field_motion_evidence_packet.same_task_field_material_packet`。它只输出 `task_id`、`present_materials`、`missing_materials`、各材料的 basename/size/hash 前缀/安全 sample refs、blocked reasons 和 false safety fields，用来证明 O6/O7 已经消费同 task 的准现场 route materials，而不是 delivery success proof。

脚本还支持可选 `--localization-path-material-json <38_pc_summary_after_map_fix.json>`，生成 additive `trashbot.localization_path_material_readback.v1`。它的 `proof_scope` 与 `evidence_boundary` 都固定为 `software_proof_localization_path_material_readback_only`，并同时写入 manifest 顶层与 `field_motion_evidence_packet.localization_path_material_readback`。这个入口只消费 O1 已经验证过的 allowlisted same-run readback 形状：`status`、`map_proof_latest`、`localize_proof_latest`、`nav2_status`、`nav2_proof_latest` 和 `o3_proof_summary` 中的安全布尔/计数字段。

`localization_path_material_readback.status=localization_path_material_readback_ready_not_route_execution_proof` 的前提是：同一 `task_id` 下 required endpoints 全部 `request_status=loaded` 且 `http_status=200`、schema 对齐、`map_once_observed=true`、`amcl_pose_observed=true`、`localization_tf_observed.map_to_odom=true`、`localization_tf_observed.map_to_base_link=true`、`planner_server_active=true`、`path_generation_requested=true`，同时 same-run path 仍保持 fail-closed：`path_generation_succeeded=false`、`path_generated=false`、`path_point_count=0`、`same_run_path_proven=false`。否则 status 固定为 `blocked_not_proven`。

该 additive 只输出：

- `same_run_localization_material_present | same_run_localization_material_consumed`
- `same_run_map_once_observed | same_run_amcl_pose_observed`
- `same_run_localization_tf_map_to_odom | same_run_localization_tf_map_to_base_link`
- `same_run_planner_server_active | same_run_path_generation_requested`
- `same_run_path_generation_succeeded=false | same_run_path_generated=false | same_run_path_point_count=0 | same_run_path_proven=false`
- `cross_run_clean_baseline_path_comparator_present=false | same_run_override_allowed=false`
- `material_summaries | blocked_reasons | next_required_evidence`

该 packet 不消费 cross-run clean-baseline comparator，也不允许输入把 `cross_run_clean_baseline_*` 混进 same-run readback。若输入试图混入 cross-run comparator、危险 true、task mismatch、unsafe text、或把 same-run path 改成成功态，section 必须 fail-closed，而且不会回显 URL、路径、token、traceback、base64、endpoint 或 runtime 原文。

脚本还会在 `same_task_field_material_packet` 与已有 route execution additive 生成后，新增 `same_task_route_execution_material_packet`。该 additive schema 固定为 `trashbot.same_task_route_execution_material_packet.v1`，`proof_scope` 与 `evidence_boundary` 都固定为 `software_proof_same_task_route_execution_material_packet_only`，并同时写入 manifest 顶层与 `field_motion_evidence_packet.same_task_route_execution_material_packet`。它只读消费同一 `task_id` 的 `same_task_field_material_packet`、`route_execution_result_delivery_readiness`、`route_delivery_closure_packet`、`route_bag_pose_progress_replay`、`nav2_goal_execution_evidence`、`delivery_result_evidence`、route bag replay / semantic / matrix 摘要和 replay JSONL artifact 摘要；不会重新读取 raw ROS payload、cloud terminal 原文或 route bag BLOB。

`same_task_route_execution_material_packet.status=route_execution_material_ready_not_delivery_proof` 的前提是：`same_task_field_material_packet` 已 ready、task_id 对齐、至少一类 route execution 相关材料已被安全消费（例如 readiness/closure/pose progress/Nav2/delivery result/route bag 摘要或 replay JSONL），且 linked summary 没有危险 true、unsafe text、unsafe 字段或 task mismatch。否则 status 固定为 `blocked_not_proven`。该 packet 保留 `same_task_id_consumed`、`same_task_field_material_packet_status`、`route_execution_material_consumed`、各 linked/material status、`route_execution_material_flags`、`material_summaries`、`material_sample_refs`、`blocked_reasons` 和 `next_required_evidence`，但只输出 basename、count、短 hash 前缀、短安全 refs、状态和计数。

脚本还会在 `same_task_route_execution_material_packet` 之后，额外接收可选 `--current-field-evidence-json <current_field_evidence_summary.json>`，只读消费 2026-06-11 真实上位机 current evidence summary 形状，生成 additive `trashbot.current_field_evidence_material.v1`。该 additive 的 `proof_scope` 固定为 `software_proof_current_field_evidence_material_only`，并同时写入 manifest 顶层与 `field_motion_evidence_packet.current_field_evidence_material`。它只消费 camera / radar / map / Nav2 no-motion path / manual gate 的安全布尔摘要，输出 `present_materials`、`missing_materials`、`blocked_reasons`、`next_required_evidence`、`live_or_field_material_consumed`、`current_field_evidence_ready_not_route_execution_proof`，并固定 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`hil_pass=false`、`connects_cloud_production=false`。该 packet 只证明当前 field evidence summary 被安全消费，不证明 route execution 或真实控制。

脚本还支持可选 `--clean-baseline-nav2-path-json <summary|latest|status|txt>`，生成 additive `trashbot.clean_baseline_nav2_path_material.v1`。它的 `proof_scope` 与 `evidence_boundary` 都固定为 `software_proof_clean_baseline_nav2_path_material_only`，并同时写入 manifest 顶层与 `field_motion_evidence_packet.clean_baseline_nav2_path_material`。这个入口兼容 `nav2_refresh_summary.json`、`nav2_retry_summary.json`、`nav2_latest_after_success.json`、`nav2_status_after_success.json` 和 `nav2_success_readback_summary.txt`；传任一入口文件后，脚本会安全读取同目录的 refresh/retry/latest/status/cleanup siblings，只抽取 first failure、retry success、path point count、planner/amcl/map/runtime/cleanup 这些白名单字段。

`clean_baseline_nav2_path_material.status=clean_baseline_nav2_path_material_ready_not_route_execution_proof` 的前提是：同一 `task_id` 下 first failure 已记录、retry 已成功生成 path、`path_point_count > 0`、planner / initialpose / AMCL pose / map_server / amcl / managed runtime 至少能从 retry 或 status summary 安全读到、cleanup readback 没有残留进程或串口占用，并且所有输入都没有 dangerous true、unsafe key、unsafe text 或 task mismatch。否则 status 固定为 `blocked_not_proven`。它会输出：

- `first_attempt_status`、`retry_status`、`retry_success`
- `path_generation_succeeded`、`path_generated`、`path_point_count`
- `planner_server_active`、`managed_runtime_started`、`managed_runtime_cleanup_ok`
- `initialpose_published`、`amcl_pose_observed`、`map_server_active`、`amcl_active`、`cleanup_readback_clean`
- `first_failure`、`retry_success_summary`、`material_sample_refs`
- `blocked_reasons`、`next_required_evidence`

该 additive 固定 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`route_execution_success=false`、`hil_pass=false`、`connects_cloud_production=false`。任一输入 summary 命中 bad schema、task mismatch、`safe_to_control=true`、`delivery_success=true`、`primary_actions_enabled=true`、`robot_control_executed=true`、`hil_pass=true`、`connects_cloud_production=true`，或字段名/文本里出现 raw、base64、绝对路径、token、traceback、response body、credential URL 时，该 section 必须 fail-closed，而且只输出 blocked reason、危险字段名和 unsafe 计数，不回显原值。

脚本还支持可选 `--field-operator-confirmation-json <operator_report_or_summary.json>`，生成 additive `trashbot.field_operator_confirmation_material.v1`。它的 `proof_scope` 与 `evidence_boundary` 都固定为 `software_proof_field_operator_confirmation_material_only`，并同时写入 manifest 顶层与 `field_motion_evidence_packet.field_operator_confirmation_material`。这个入口只消费白名单字段：同一 `task_id`、operator material identity 是否存在、operator report / confirmation 状态、operator 是否在场、现场 clearance、急停准备、人工观察到 motion/stop，以及带时区的 `reported_at`。

`field_operator_confirmation_material.status=field_operator_confirmation_material_ready_not_delivery_proof` 的前提是：输入 JSON 可读且为 object、输入 `task_id` 与 manifest / field packet 对齐、同 task route material 已存在、operator identity 或 material id 存在、operator report 与 confirmation 均为 ready/confirmed 类状态、operator 在场、physical clearance 已确认、emergency stop ready、observed_motion 与 observed_stop 均为 true、`reported_at` 可归一为 UTC，并且输入没有 dangerous true、unsafe key、unsafe text。否则 status 固定为 `blocked_not_proven`。它会输出：

- `schema`、`proof_scope`、`evidence_boundary`、`status`
- `task_id`、`task_id_source`、`source`
- `operator_report_present`、`operator_report_status`
- `operator_confirmation_present`、`operator_confirmation_status`
- `operator_present`、`physical_clearance_confirmed`、`emergency_stop_ready`
- `observed_motion`、`observed_stop`、`reported_at`
- `same_task_id_consumed`、`linked_route_material_present`、`linked_delivery_material_present`
- `operator_material_consumed`、`support_only_reason`
- `blocked_reasons`、`next_required_evidence`、`material_summaries`

该 additive 固定 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`route_execution_success=false`、`hil_pass=false`、`connects_cloud_production=false`。缺输入、bad JSON、非 object、task mismatch、operator identity 缺失、危险 true、字段名或文本里出现 raw/body/path/token/URL/base64/traceback/credential，都会只让本 section fail-closed；输出不会回显 operator identity 原文、raw/body、路径、URL、token、base64、traceback 或长备注正文。

脚本还支持可选 `--pc-live-nav2-execution-material-json <pc_live_nav2_execution_material.json>`，生成 additive `trashbot.pc_live_nav2_execution_material.v1`。它的 `proof_scope` 与 `evidence_boundary` 都固定为 `software_proof_pc_live_nav2_execution_material_only`，并同时写入 manifest 顶层与 `field_motion_evidence_packet.pc_live_nav2_execution_material`。这个入口只消费 2026-07-03 PC live Nav2 执行记录里的短安全字段：`source_sprint`、`source_doc`、`verified_at`、`goal_accepted`、`cancel_accepted`、`uses_base_uart`、`robot_control_executed`（仅作为 source fact 摘要）、`base_command_nonzero_observed`、`base_command_nonzero_count`、`base_feedback_sample_count`、`base_feedback_lr_nonzero_proven`、`base_feedback_imu_attitude_delta_observed`、`motion_signal_observed`、`goal_result_status`（兼容 `terminal_status` alias）和短 `remaining_evidence[]`。

`pc_live_nav2_execution_material.status=pc_live_nav2_execution_material_ready_not_delivery_proof` 的前提是：输入 JSON 可读且为 object、`task_id` 已稳定、`source_sprint` 与 `source_doc` 存在、`goal_accepted=true`、`uses_base_uart=true`、`base_command_nonzero_observed=true`、`base_command_nonzero_count > 0`、`base_feedback_sample_count > 0`、`base_feedback_lr_nonzero_proven=false`、`base_feedback_imu_attitude_delta_observed=true`、`motion_signal_observed=true`，并且输入没有 dangerous true、unsafe key 或 unsafe text。否则 status 固定为 `blocked_not_proven`。它会输出：

- `schema`、`proof_scope`、`evidence_boundary`、`status`
- `task_id`、`task_id_source`、`source`
- `source_sprint`、`source_doc`、`verified_at`
- `goal_accepted`、`nav2_goal_accepted`、`cancel_accepted`、`uses_base_uart`
- `source_robot_control_executed`
- `base_command_nonzero_observed`、`base_command_nonzero_count`
- `base_feedback_sample_count`、`base_feedback_lr_nonzero_proven`、`base_feedback_imu_attitude_delta_observed`
- `motion_signal_observed`、`goal_result_status`、`result_status`、`nav2_terminal_status`
- `blocked_reasons`、`next_required_evidence`、`material_summaries`

该 additive 固定 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`route_execution_success=false`、`hil_pass=false`。输入若试图把 `delivery_success=true`、`safe_to_control=true`、`primary_actions_enabled=true`、`route_execution_success=true` 或 `hil_pass=true` 混入材料，或者字段名/文本中出现 URL、token、raw log、traceback、base64 或本机绝对路径，section 必须 fail-closed，而且不会回显原值。

在这个基础上，packet 还会输出 credit-aware 字段，专门给 O6/O7 / Product 判断“这次 same-task route execution material 只是 support-only，还是已经具备 credit candidate 形态”：

- `live_or_field_command_evidence_present`：来自 `motion_log_summary.live_motion_evidence_present`、`motion_log_summary.live_nav2_log_present`，或 `route_bag_or_live_nav2_log.source=live_motion_log`。普通 route bag / replay / readback 不能把它抬成 true。
- `delivery_or_operator_material_consumed`：只有 `delivery_result_evidence` 自身 ready，且 `delivery_result_claimed=true` 或 `operator_confirmation_present=true` 时才为 true。
- `route_execution_credit_candidate`：只有 `route_execution_material_consumed=true`、`live_or_field_command_evidence_present=true` 和 `delivery_or_operator_material_consumed=true` 三者同时满足才为 true。即使为 true，也仍然不表示真实送达成功。
- `credit_support_only_reason`：当 candidate=false 时，给出稳定分类，例如 `same_task_id_mismatch_or_missing`、`same_task_route_execution_material_not_ready`、`local_or_mock_same_task_artifacts_only`、`probe_only_same_task_artifacts`、`readback_only_same_task_artifacts` 或 `delivery_or_operator_material_missing`。
- `credit_required_evidence`：列出让 candidate 变成 true 还缺什么，通常包括 `same_task_live_motion_log_or_field_nav2_command_evidence`、`same_task_delivery_result_or_operator_confirmation` 或 packet 原有的 route execution linked evidence 缺口。

`same_task_route_execution_material_packet` 的安全边界更保守：`delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`hil_pass=false`、`route_execution_success=false` 始终固定。任一 linked summary 中出现 `safe_to_control=true`、`delivery_success=true`、`primary_actions_enabled=true`、`robot_control_executed=true`、`route_execution_success=true`、`hil_pass=true`、`live_nav2_run_proven=true`、`real_world_delivery_proven=true` 或 `connects_cloud_production=true`，都会把该 packet fail-closed。字段名或文本中出现 token、secret、credential、raw payload、base64、traceback、response body、带凭证 URL，或 `/Users`、`/root`、`/tmp` 等本机绝对路径时，也只输出 blocked reason、危险字段名和 unsafe 计数，不回显原值。

没有 `--preflight-json` 时仍会生成 manifest，但 `preflight.status=missing_preflight_json`、`not_proven=true`，只证明离线 artifact intake 软件路径，不证明现场 ready 或 delivery。

`--derive-replay-jsonl` 只在本地 intake 时生效：脚本会只读解析 `route.csv`，派生 deterministic replay JSONL，补给 O7/PC consumer 与 manifest gate。它不会生成 rosbag，不会发布 `/cmd_vel`，也不会把 `safe_to_control`、`delivery_success`、`primary_actions_enabled` 置为 `true`。

`--motion-log-root` 也只在本地摘要链路中生效。当前主要读取 `learn_launch.log`、`pulse_and_stop*.log`、`odom_after_motion*.txt`、`tf_after_motion*.txt`，并把它们整理进 `field_motion_evidence_packet.motion_log_summary`。这里必须区分“现场运动证据存在”和“direct odom/tf capture 非零”两件事：前者允许由非零 `cmd_vel` 日志、非零 waypoint 或 `route.csv` 非零位移支撑；后者若仍为 0，必须保留为 blocked reason，不能被 route replay 或 keyframe 摘要洗白。

`--nav2-goal-proof-json` 只读取 O11 proof 的白名单字段：`status` 会进入 `source_status`，另保留 `proof_status`、`result_status`、`result_status_code`、`goal_sent`、`goal_accepted`、`result_received`、`nav2_goal_execution_proven`、`base_motion_command_nonzero_proven`、`base_command_mode`、`requested_base_command_mode`、`feedback_sample_count`、`goal_request.frame_id/x/y/yaw`、`base_feedback_summary.wheel_feedback_lr_nonzero_proven/nonzero_sample_count/imu_attitude_delta_observed` 和 `base_command_summary.nonzero_command_observed/nonzero_command_count/latest_nonzero_command_mode`。输出 schema 固定为 `trashbot.nav2_goal_execution_evidence.v1`，`proof_scope=software_proof_nav2_goal_execution_evidence_only`。`task_id` 只沿用 `field_motion_evidence_packet` lineage，proof 内的 `task_id` 不会覆盖同一 packet。

O11 proof 缺失、JSON 不可读、root 不是 object、schema 不是 `trashbot.upper_robot_api.v1.nav2_goal_execution_proof`，或者包含 `safe_to_control=true`、`delivery_success=true`、`primary_actions_enabled=true`、路径/root/token/raw/base64 等不安全字段或文本时，`nav2_goal_execution_evidence.status=blocked_not_proven`。阻断摘要只输出 blocked reason、危险 true 字段名和 unsafe 计数，不回显原始路径、root、token、raw payload 或 base64 内容。即使 O11 proof 原文包含真实执行字段，摘要和 field packet 里的 `robot_control_executed` 仍固定为 `false`；这些事实只能进入 `blocked_reasons` / `next_required_evidence`，不能打开主动作，也不能宣称真实送达。

`--delivery-result-json` 只读取 `trashbot.delivery_result.v1` 的白名单字段：`record_status`（若缺则回退 `status`）、`delivery_result_claimed`、`operator_confirmation_present`、`dropoff_confirmation_type`、`completed_at_utc` 和可选 `task_id`。输出 schema 固定为 `trashbot.delivery_result_evidence.v1`，`proof_scope=software_proof_delivery_result_evidence_only`。摘要的 `task_id` / `task_id_source` 仍沿用 `field_motion_evidence_packet` lineage；输入里的 `task_id` 只做同 task 校验，不能覆盖 packet 主键。

delivery result JSON 缺失、JSON 不可读、root 不是 object、schema 不是 `trashbot.delivery_result.v1`、输入 `task_id` 与 packet lineage 不匹配、`completed_at_utc` 不是短 UTC 文本，或者包含 `safe_to_control=true`、`delivery_success=true`、`primary_actions_enabled=true`、`robot_control_executed=true`、路径/root/token/raw/base64、带凭证 URL 等不安全字段或文本时，`delivery_result_evidence.status=blocked_not_proven`。阻断摘要只输出 blocked reason、危险 true 字段名和 unsafe 计数，不回显原始路径、URL 凭证、token、raw payload 或 base64 内容。即使输入里出现 completed/delivered/operator confirmed 等完成声明，`delivery_success` 仍固定为 `false`；该 additive 只证明“同一 task 下已有 delivery result 记录可供 O6/O7 软件侧消费”，不证明真实投递成功。

`--cloud-terminal-result-json` 只在没有 `--delivery-result-json` 时生效，用于把 O5 robot-facing terminal result 主路径桥接到同一个 `delivery_result_evidence`。它直接支持 `schema=trashbot.cloud_command_terminal_result.v1`，也支持 `schema=trashbot.cloud_command_result_reconciliation.v2` 的 wrapper。wrapper 只有在 `result_state=terminal_result_recorded`、`terminal_result` 是 object、`terminal_result.schema=trashbot.cloud_command_terminal_result.v1`，并且 wrapper / nested `task_id` 与当前 manifest `task_id` 没有漂移时，才允许下钻到 nested terminal result。输出仍固定为 `trashbot.delivery_result_evidence.v1`，`source=cloud_command_terminal_result`，`source_schema=trashbot.cloud_command_terminal_result.v1`，并同时写入 manifest 顶层和 `field_motion_evidence_packet.delivery_result_evidence`。输入里的 `command_id`、`task_record_ref`、`evidence_ref` 只可作为短 safe ref 摘要输出，不能覆盖 manifest / packet 的主 `task_id`。

cloud terminal result 只有在 `terminal_result_type=delivery_terminal|dropoff_terminal`，且 `result_code` 或 `task_terminal_state` 表达 completed/succeeded/dropoff completed 时，才允许把 `delivery_result_claimed=true` 写入摘要；`delivery_success`、`safe_to_control`、`primary_actions_enabled` 和 `robot_control_executed` 始终固定为 `false`。对 reconciliation wrapper 而言，`result_state=terminal_result_recorded` 只是允许下钻 nested terminal result 的前置 gate，本身不是成功证明。schema mismatch、JSON 不可读、root 非 object、wrapper `result_state` 不是 `terminal_result_recorded`、nested `terminal_result` 缺失或 schema 不匹配、终态类型不是 delivery/dropoff、缺 result code/state、缺完成时间、`task_id` mismatch，或 `command_id` / `task_record_ref` / `evidence_ref` 含路径、URL、token、raw/base64、credential、`delivery_success=true`、`safe_to_control=true`、`primary_actions_enabled=true`、`robot_control_executed=true`、`real_world_delivery_proven=true` 时，都会 fail-closed 为 `blocked_not_proven`，并只输出 blocked reason、危险 true 字段名和 unsafe 计数，不回显原始路径、URL、token 或 raw/base64 内容。

`route_execution_result_delivery_readiness` 不直接读取新输入，只汇总已有 additive。它要求同一 `task_id` 下至少满足以下保守条件才会输出 `status=route_execution_result_delivery_readiness_ready_not_delivery_proof`：

- `nav2_goal_execution_evidence.status=ready_not_delivery_proof`
- `nav2_goal_execution_proven=true`
- `route_bag_pose_progress_replay.status=ready_not_live_nav2_proof`
- `nonzero_pose_progress_observed=true`
- `delivery_result_evidence.status=ready_not_delivery_proof`
- `delivery_result_claimed=true`
- `operator_confirmation_present=true`

任何 linked schema mismatch、dangerous true、unsafe 文本、route bag/live log 缺失、delivery claim 与 operator confirmation 状态冲突，或任一 linked additive 自己已 blocked 时，`route_execution_result_delivery_readiness.status` 都必须保持 `blocked_not_proven`。该摘要只输出：

- `schema`, `proof_scope`, `status`, `source`, `task_id`, `task_id_source`
- `route_execution_result_status`, `route_execution_source`, `route_execution_result_ready`, `route_execution_success=false`
- `delivery_result_readiness_status`, `delivery_result_source`, `delivery_result_readiness_ready`
- `operator_confirmation_readiness_status`, `operator_confirmation_source`, `operator_confirmation_readiness_ready`
- `linked_nav2_goal_execution_proven`, `linked_delivery_result_claimed`, `linked_operator_confirmation_present`
- `blocked_reasons`, `next_required_evidence`
- `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, `robot_control_executed=false`

`route_delivery_closure_packet` 不读取新输入，只消费前述 linked additive。只有以下条件全部满足时才允许 `status=route_delivery_closure_ready_not_success_proof`：

- `nav2_goal_execution_evidence.status=ready_not_delivery_proof`
- `delivery_result_evidence.status=ready_not_delivery_proof`
- `route_execution_result_delivery_readiness.status=route_execution_result_delivery_readiness_ready_not_delivery_proof`
- `route_bag_pose_progress_replay.status=ready_not_live_nav2_proof`
- 四个 linked additive 的 `task_id` 都等于 manifest / `field_motion_evidence_packet.task_id`
- 四个 linked additive 都没有危险 true、unsafe 文本、unsafe 计数或 schema mismatch

缺任一关键输入、schema mismatch、dangerous true、unsafe 文本或 task mismatch 时，`route_delivery_closure_packet.status` 必须保持 `blocked_not_proven`。该摘要只输出：

- `schema`, `proof_scope`, `status`, `source`, `task_id`, `task_id_source`
- `closure_ready`
- `linked_nav2_goal_status`, `linked_delivery_result_status`, `linked_route_execution_result_status`, `linked_pose_progress_status`
- `linked_route_execution_source`
- `linked_nav2_goal_execution_proven`, `linked_delivery_result_claimed`, `linked_operator_confirmation_present`
- `linked_nonzero_pose_progress_observed`
- `linked_route_execution_result_ready`, `linked_delivery_result_readiness_ready`, `linked_operator_confirmation_readiness_ready`
- `blocked_reasons`, `next_required_evidence`
- `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, `robot_control_executed=false`, `route_execution_success=false`

`same_task_mission_evidence_gate` 是 O5/O6/O7 mission gate，不读取新输入，只严格消费当前 manifest 已生成的 linked additive。只有以下条件全部满足时才允许 `status=same_task_mission_gate_ready_not_success_proof`：

- `delivery_result_evidence.status=ready_not_delivery_proof`
- `delivery_result_evidence.source_schema=trashbot.cloud_command_terminal_result.v1`
- `route_execution_result_delivery_readiness.status=route_execution_result_delivery_readiness_ready_not_delivery_proof`
- `route_delivery_closure_packet.status=route_delivery_closure_ready_not_success_proof`
- `route_bag_pose_progress_replay.status=ready_not_live_nav2_proof`
- `route_bag_pose_progress_replay.nonzero_pose_progress_observed=true`
- 四个 linked additive 的 `task_id` 都等于 manifest / `field_motion_evidence_packet.task_id`
- 四个 linked additive 都没有危险 true、unsafe 文本、unsafe 计数、schema mismatch 或 proof scope mismatch

缺任一条件时，`same_task_mission_evidence_gate.status` 必须保持 `blocked_not_proven`。该摘要只输出：

- `schema`, `proof_scope`, `status`, `source`, `task_id`, `task_id_source`
- `same_task_mission_gate_ready`
- `terminal_refs.source | source_schema | command_id_ref | task_record_ref | evidence_ref | completed_at_utc`
- `linked_readiness_flags.same_task_id_matched | delivery_result_evidence_ready | cloud_terminal_result_source_consumed`
- `linked_readiness_flags.route_execution_result_delivery_readiness_ready | route_delivery_closure_ready | route_bag_pose_progress_ready | nonzero_pose_progress_observed`
- `mission_artifact_delta.same_task_id_consumed | cloud_terminal_result_source_consumed | route_execution_readiness_consumed | route_delivery_closure_consumed | nonzero_pose_progress_consumed`
- `mission_artifact_delta.same_task_field_material_consumed`
- `mission_artifact_delta.same_task_terminal_result_linked_to_route_execution | delivery_success_delta=false | production_cloud_evidence_delta=false | live_or_field_command_executed=false`
- `blocked_reasons`, `next_required_evidence`
- `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, `robot_control_executed=false`, `route_execution_success=false`

`same_task_field_material_packet` 的 ready 语义也保持保守：

- 至少两类同 task 路线材料安全存在：`route_csv`、`keyframes`、`route_bag_or_rosbag`、`replay_jsonl` 中任意两类即可。
- `map.yaml` 缺失会被记录为 `same_task_field_material_map_yaml_missing_optional`，但不会阻止 packet 消费其它准现场材料。
- basename、sample ref、source manifest 上任一字段命中路径、token、raw、base64、credential、secret 或危险 true 时，packet 必须 fail-closed 为 `blocked_not_proven`，并且不回显原文。
- `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`route_execution_success=false` 始终保持。

`--route-bag-db3` 只使用 Python 标准库 `sqlite3` 只读摘要 rosbag2 DB3，不要求 ROS2 runtime，也不反序列化 `messages.data` BLOB。白名单字段包括 `topics` / `messages` 表的 topic count、message count、timestamp first/last 和最多 8 个安全 topic name 样本。输出 schema 固定为 `trashbot.route_bag_evidence.v1`，`proof_scope=software_proof_route_bag_evidence_intake_only`。`source_label` 默认可由 DB3 basename 派生，也可以通过 `--route-bag-source-label` 指定；manifest 只保留 label、basename、size 和 sha256 prefix，不回显 DB3 或 metadata 的绝对路径。

同一 `--route-bag-db3` 输入还会生成 `trashbot.route_bag_payload_replay.v1`。它继续保持只读、不启动 ROS2 runtime、不输出 raw/base64/content/完整 hash/绝对路径/credential URL；在 DB3 可读且 schema 正常时，`payload_sample_count`、`payload_size_min_bytes`、`payload_size_max_bytes`、`payload_size_avg_bytes` 和 `payload_sha256_prefix_samples` 会从 `messages.data` 的安全样本中派生。`payload_sha256_prefix_samples` 现在对齐 O6/O7 合同，仅输出 `string[]` 形式的短 hash 前缀，不再回显 per-sample topic、timestamp 或 payload size 结构，用于 O6/O7 定位问题，不表示真实路线执行成功，也不表示 delivery success。

同一 `--route-bag-db3` 输入还会生成 `trashbot.route_bag_pose_progress_replay.v1`。它只读派生位姿进度摘要，优先支持 `tf2_msgs/msg/TFMessage` 的 transform translation；在低风险场景下也支持 `nav_msgs/msg/Odometry`。DB3 可读且 schema 正常时，脚本只输出 `pose_sample_count`、`pose_decode_ok_count`、`pose_decode_failed_count`、`pose_topic_types`、`pose_frame_pairs`、`pose_time_span_ns`、`start_pose`、`end_pose`、`displacement_m`、`nonzero_pose_progress_observed`、`blocked_reasons` 和 `next_required_evidence`，并同时写入 manifest 顶层与 `field_motion_evidence_packet.route_bag_pose_progress_replay`。该摘要仍然不输出 raw payload、完整 hash、绝对路径、URL、token、控制 topic 或真实成功声明；`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`live_nav2_run_proven=false`、`route_execution_success=false` 始终保持。

route bag DB3 缺失、不是 SQLite、缺 `topics` / `messages` 表、缺必需列、topic/message 为空、metadata/source label 含 `safe_to_control=true`、`delivery_success=true`、`primary_actions_enabled=true`、`robot_control_executed=true`、绝对路径、root、token、raw/base64、credential URL 或控制 topic 样本时，`route_bag_evidence.status=blocked_not_proven`。阻断摘要只输出 blocked reason、危险 true 字段名、unsafe 计数、basename、size/hash prefix 和 topic/message/timestamp 摘要，不回显原始 payload、完整 hash、路径、URL 凭证或 BLOB。即使 DB3 可读且含 `/scan`、`/camera/image_raw`、`/tf_static` 等 topic，`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`live_nav2_run_proven=false`、`route_execution_success=false` 仍固定保持。

`route_bag_payload_replay` 额外把 `messages.data` 作为 payload 摘要输入。DB3 缺失、不是 SQLite、缺 `topics` / `messages` / `data` 列、topic/message 为空、payload 为空、危险 true、路径/root/token/raw/base64/credential URL 或 unsafe topic 时，`route_bag_payload_replay.status=blocked_not_proven`。阻断摘要同样只输出 blocked reason、危险 true 字段名、unsafe 计数、basename、size/hash prefix、topic/message/timestamp 摘要以及 payload size/hash 前缀样本，不回显 raw payload、完整 hash、路径、URL 凭证或 BLOB；其中 `payload_sha256_prefix_samples` 也保持 `string[]`，不输出结构化样本对象。

`route_bag_semantic_replay` 在同一 DB3 上继续生成可读语义摘要。脚本只对白名单类型做有限 CDR 解码，不还原原始 payload：

- `sensor_msgs/msg/LaserScan`：样本数、range 样本长度、finite 计数、`angle_min/max`、`angle_increment`、`range_min/max`、`intensity_count`。
- `sensor_msgs/msg/Image`：样本数、`width/height`、`encoding` 集合、`step`、`data_size` 聚合。
- `tf2_msgs/msg/TFMessage`：transform sample 数、`transform_count_total`、`frame_pairs` 示例。
- `nav_msgs/msg/Odometry`：复用 pose progress 的安全 CDR 解析，只输出 `frame_pairs`、`start_translation/end_translation`、`translation_norm_min/max` 和 `nonzero_translation_sample_count`，不输出 twist、covariance 或 raw payload。
- `diagnostic_msgs/msg/DiagnosticArray`：只输出 `status_count`、`highest_level`、`level_distribution`、短 `status_name_samples`、短 `hardware_id_samples` 和 `key_value_pair_count`；`message`、key/value 原文、raw payload、base64、完整 hash、路径、URL、token 与 traceback 都不会进入 manifest。

`route_bag_semantic_replay.status=ready_not_route_execution_proof` 的前提是 DB3 可读、schema 正常、topic/message 非空、白名单 topic 至少出现一次、decode 成功且无 `unsafe` 证据；任何 one decode 失败、schema mismatch、unsafe topic、危险 true 或 unsafe text 会进入 `blocked_not_proven`。该摘要同样不会回显 raw payload、完整 hash、绝对路径、credential URL 或 token/path 文本。

同一 `--route-bag-db3` 输入还会生成 `trashbot.route_bag_full_semantic_decode_matrix.v1`，`proof_scope=software_proof_route_bag_full_semantic_decode_matrix_only`。该矩阵只读 SQLite DB3，并按安全 topic/name + type 聚合有限样本解码覆盖：

- 已支持且样本解码成功的 topic/type 计入 `decoded`。
- 未知但安全的 ROS type 计入 `unsupported`，用于提示后续补 decoder。
- 已支持但样本解码异常的 topic/type 计入 `failed`，用于提示 payload/schema 需要复核。

`route_bag_full_semantic_decode_matrix.status=ready_not_route_execution_proof` 的前提是 DB3 可读、schema 正常、至少一个 topic/type 达到 decoded，且没有 unsafe topic/type、危险 true、unsafe source label 或 metadata 文本。unsupported/failed 仍会进入 `blocked_reasons`、`topic_type_matrix[]` 和 `next_required_evidence`，但不会开启控制，也不会宣称 route execution success。矩阵 item 只允许输出安全 `topic_name`、`topic_type`、计数、`status`、`blocked_reason`、`decoder_name` 和短 `sample_sha256_prefixes`；不输出 raw payload、base64、完整 hash、绝对路径、credential URL、token、`/cmd_vel` 或任何成功控制字段。

可选 SSH 参数：

- `--ssh-target root@192.168.1.11`
- `--ssh-port 37878`
- `--timeout-s 5`

真实上位机入口仍是：

```bash
ssh root@192.168.1.11 -p 37878
```

SSH 模式只运行远端只读 Python 扫描，不启动 `ros2 launch`、Nav2、fixed route 或运动命令。SSH 不可达时状态记录为 `blocked_ssh_unreachable`。

## 必需 artifact

manifest 必需检查以下材料：

- `map.yaml`，或真实 bundle 下的 `map/*.yaml`
- `map.pgm`，或真实 bundle 下的 `map/*.pgm`
- `route.csv`，或真实 bundle 下的 `route/route.csv`
- `manifest.json`，或真实 bundle 下的 `route/manifest.json`
- `keyframes/`，或真实 bundle 下的 `route/keyframes/`，目录下至少一个 `.jpg`、`.jpeg`、`.png` 或 `.json`

完整 bundle / 旧 field packet intake 还会把以下运行材料纳入 gate：

- `rosbag` / `route_bag` 目录或 rosbag 文件
- `replay.jsonl` 或 `fixed_route_replay.jsonl`

当 `--artifact-root` / `--input` 明确指向 route-root seed（目录名为 `route` 或 `route_data`，或显式传入 `--map-yaml` 与 `--map-pgm`），并且已启用 `--derive-replay-jsonl` 或目录内已有 replay JSONL 时，脚本会进入 route-root seed 语义：`route.csv`、source `manifest.json`、keyframes、map 和 replay 仍是必需材料，`rosbag` / `route_bag` 则降级为可选增强证据。此时缺少 `route_bag` 不再阻断 `gate_pass=true`，manifest 会在 `route_root_seed_gate` 中记录 `route_bag_required=false`、`route_bag_present=false`、`blocked_reasons=["route_bag_missing_optional_for_route_root_seed"]` 和 `next_required_evidence=["route_bag_or_live_nav2_log_for_motion_proof", ...]`。这个入口只证明 O6/O7 可以消费 route/map/source/replay 摘要，不宣称 Nav2 实跑、固定路线成功或 delivery success，且 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false` 必须保持。

普通完整 bundle root 没有显式 route-root seed 条件时仍按旧 gate 扫描，`route_bag` 缺失会作为必需运行材料缺口保留 fail-closed。这样做是为了区分“离线路线材料可消费”和“现场运动/rosbag 证据完整”两类证明，避免 O6/O7 local/mock seed 被 route_bag 硬依赖阻塞，也避免把 route-only 材料误报成真实运动成功。

兼容顺序保持向后兼容：同层路径、`route/` 分层路径、`route_data/` 旧路径都会被扫描。真实 2026-06-10 现场 bundle 使用 `map/` 与 `route/` 分层结构时，可以直接传 bundle root；如果只传 `artifacts/route/`，必须用 `--map-yaml` 和 `--map-pgm` 显式引用相邻 map 文件。

每项 artifact 记录：

- `required`
- `present`
- `path`
- `size_bytes`
- `mtime_utc`
- `sha256`
- `reason`

目录 artifact 使用稳定排序后的目录摘要：对子文件的相对路径、大小和 sha256 做二次 sha256，因此可复跑比较，但不会把图片或 bag 内容写进 manifest。

`manifest.json` 是上游 route/source manifest。例如 `route_data_recorder` 写出的 `trashbot.vision_samples.v1` 会作为 `source_manifest` 记录 schema、路径和样本数量，不会因为 schema 不是 `trashbot.field_evidence_manifest.v1` 而阻断生成。只有 `field_evidence_manifest.json`、`trashbot_field_evidence_manifest.json` 或 `trashbot.field_evidence_manifest.v1.json` 这类旧 field-evidence 输出才进入 `input_manifest` 安全复用检查。

## 离线 evidence packet intake

本地目录可以来自现场人工 USB 拷贝、压缩包解压、后续 SSH 成功后的 run 目录，或已有 `trashbot.field_evidence_manifest.v1` 的材料包。推荐命令：

```bash
python3 onboard/scripts/field_route_evidence_manifest.py \
  --mode local \
  --input /tmp/trashbot_field_evidence_fixture \
  --output /tmp/trashbot_field_evidence_manifest.json
```

离线 intake 会在 artifact 扫描前检查目录内已有 field-evidence manifest 候选：

- `field_evidence_manifest.json`
- `trashbot_field_evidence_manifest.json`
- `trashbot.field_evidence_manifest.v1.json`
- `route_data/field_evidence_manifest.json`
- `route_data/trashbot_field_evidence_manifest.json`

已有 manifest 的 `schema` 必须是 `trashbot.field_evidence_manifest.v1`。如果 schema 不匹配、JSON 无法解析，或已有 manifest 自带以下危险成功声明，输出必须 fail closed，返回非零，并把 `input_manifest.blocked_reason` 写入新 manifest：

- `delivery_success=true`
- `safe_to_control=true`
- `primary_actions_enabled=true`

这条规则的原因是：离线 packet 是材料入口，不是现场控制或送达验收单。即使同一目录的 `map.yaml`、`route.csv`、keyframes、rosbag 和 replay 都齐全，也不能用 artifact 完整性把旧 manifest 的危险成功声明“洗白”。

## gate 语义

`gate_pass=true` 只表示必需 artifact 都存在且非空。它不等于真实路线成功、不等于 Nav2 实跑成功、不等于送达成功。

manifest 顶层始终保留安全边界：

- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

同时保留面向 O6/O7 消费的显式 gate 字段：

- `artifact_status`：`gated | missing | blocked`
- `artifact_health`：artifact 计数、present/missing 列表和摘要
- `manifest_gate.status`：`gated | blocked_not_proven`
- `manifest_gate.gate_pass`
- `manifest_gate.blocked_reason`
- `route_root_seed_gate.route_bag_required | route_bag_present | blocked_reasons | next_required_evidence`
- `derived_replay.generated | frame_count | output | source_route_csv | blocked_reason`
- `field_motion_evidence_packet.schema=trashbot.field_motion_evidence_packet.v1`
- `field_motion_evidence_packet.proof_scope=software_proof_field_motion_evidence_packet_only`
- `field_motion_evidence_packet.route_summary.frame_count | nonzero_displacement_observed | distance_m`
- `field_motion_evidence_packet.motion_log_summary.live_motion_evidence_present | evidence_sources | direct_odom_capture_nonzero | direct_tf_capture_nonzero`
- `field_motion_evidence_packet.route_bag_or_live_nav2_log.present | source | status`
- `nav2_goal_execution_evidence.schema=trashbot.nav2_goal_execution_evidence.v1`
- `nav2_goal_execution_evidence.proof_scope=software_proof_nav2_goal_execution_evidence_only`
- `nav2_goal_execution_evidence.status=ready_not_delivery_proof | blocked_not_proven`
- `nav2_goal_execution_evidence.source_status | proof_status | result_status | goal_sent | goal_accepted | result_received`
- `nav2_goal_execution_evidence.base_feedback_summary | base_command_summary | blocked_reasons | next_required_evidence`
- `delivery_result_evidence.schema=trashbot.delivery_result_evidence.v1`
- `delivery_result_evidence.proof_scope=software_proof_delivery_result_evidence_only`
- `delivery_result_evidence.status=ready_not_delivery_proof | blocked_not_proven`
- `delivery_result_evidence.record_status | delivery_result_claimed | operator_confirmation_present | dropoff_confirmation_type | completed_at_utc`
- `delivery_result_evidence.source | source_schema | command_id_ref | task_record_ref | evidence_ref`
- `delivery_result_evidence.linked_nav2_goal_execution_proven | blocked_reasons | next_required_evidence`
- `route_execution_result_delivery_readiness.schema=trashbot.route_execution_result_delivery_readiness.v1`
- `route_execution_result_delivery_readiness.proof_scope=software_proof_route_execution_result_delivery_readiness_only`
- `route_execution_result_delivery_readiness.status=route_execution_result_delivery_readiness_ready_not_delivery_proof | blocked_not_proven`
- `route_execution_result_delivery_readiness.route_execution_result_status | route_execution_source | route_execution_result_ready | route_execution_success=false`
- `route_execution_result_delivery_readiness.delivery_result_readiness_status | delivery_result_source | delivery_result_readiness_ready`
- `route_execution_result_delivery_readiness.operator_confirmation_readiness_status | operator_confirmation_source | operator_confirmation_readiness_ready`
- `route_execution_result_delivery_readiness.linked_nav2_goal_execution_proven | linked_delivery_result_claimed | linked_operator_confirmation_present`
- `route_execution_result_delivery_readiness.blocked_reasons | next_required_evidence | safe_to_control=false | delivery_success=false`
- `route_delivery_closure_packet.schema=trashbot.route_delivery_closure_packet.v1`
- `route_delivery_closure_packet.proof_scope=software_proof_route_delivery_closure_packet_only`
- `route_delivery_closure_packet.status=route_delivery_closure_ready_not_success_proof | blocked_not_proven`
- `route_delivery_closure_packet.closure_ready`
- `route_delivery_closure_packet.linked_nav2_goal_status | linked_delivery_result_status | linked_route_execution_result_status | linked_pose_progress_status`
- `route_delivery_closure_packet.linked_route_execution_source`
- `route_delivery_closure_packet.linked_nav2_goal_execution_proven | linked_delivery_result_claimed | linked_operator_confirmation_present`
- `route_delivery_closure_packet.linked_nonzero_pose_progress_observed`
- `route_delivery_closure_packet.linked_route_execution_result_ready | linked_delivery_result_readiness_ready | linked_operator_confirmation_readiness_ready`
- `route_delivery_closure_packet.blocked_reasons | next_required_evidence | safe_to_control=false | delivery_success=false | route_execution_success=false`
- `same_task_field_material_packet.schema=trashbot.same_task_field_material_packet.v1`
- `same_task_field_material_packet.proof_scope=software_proof_same_task_field_material_packet_only`
- `same_task_field_material_packet.status=ready_not_delivery_proof | blocked_not_proven`
- `same_task_field_material_packet.present_materials | missing_materials | material_flags`
- `same_task_field_material_packet.material_summaries.<material>.basename | size_bytes | sha256_prefix | sample_refs | count`
- `same_task_field_material_packet.blocked_reasons | next_required_evidence | safe_to_control=false | delivery_success=false | route_execution_success=false`
- `localization_path_material_readback.schema=trashbot.localization_path_material_readback.v1`
- `localization_path_material_readback.proof_scope=software_proof_localization_path_material_readback_only`
- `localization_path_material_readback.evidence_boundary=software_proof_localization_path_material_readback_only`
- `localization_path_material_readback.status=localization_path_material_readback_ready_not_route_execution_proof | blocked_not_proven`
- `localization_path_material_readback.same_run_localization_material_present | same_run_localization_material_consumed`
- `localization_path_material_readback.same_run_map_once_observed | same_run_amcl_pose_observed`
- `localization_path_material_readback.same_run_localization_tf_map_to_odom | same_run_localization_tf_map_to_base_link`
- `localization_path_material_readback.same_run_planner_server_active | same_run_path_generation_requested`
- `localization_path_material_readback.same_run_path_generation_succeeded=false | same_run_path_generated=false | same_run_path_point_count=0 | same_run_path_proven=false`
- `localization_path_material_readback.cross_run_clean_baseline_path_comparator_present=false | same_run_override_allowed=false`
- `localization_path_material_readback.material_summaries | blocked_reasons | next_required_evidence | safe_to_control=false | delivery_success=false | primary_actions_enabled=false | robot_control_executed=false | hil_pass=false | nav2_route_execution_success=false | route_execution_success=false`
- `same_task_route_execution_material_packet.schema=trashbot.same_task_route_execution_material_packet.v1`
- `same_task_route_execution_material_packet.proof_scope=software_proof_same_task_route_execution_material_packet_only`
- `same_task_route_execution_material_packet.evidence_boundary=software_proof_same_task_route_execution_material_packet_only`
- `same_task_route_execution_material_packet.status=route_execution_material_ready_not_delivery_proof | blocked_not_proven`
- `same_task_route_execution_material_packet.same_task_id_consumed | same_task_field_material_packet_status | route_execution_material_consumed`
- `same_task_route_execution_material_packet.route_execution_result_status | route_delivery_closure_status | nav2_goal_execution_status | delivery_result_status | pose_progress_replay_status`
- `same_task_route_execution_material_packet.route_replay_jsonl_status | route_bag_or_rosbag_status | route_csv_status | keyframe_material_status`
- `same_task_route_execution_material_packet.route_execution_material_flags | material_summaries | material_sample_refs`
- `same_task_route_execution_material_packet.blocked_reasons | next_required_evidence | safe_to_control=false | delivery_success=false | primary_actions_enabled=false | robot_control_executed=false | hil_pass=false | route_execution_success=false`
- `current_field_evidence_material.schema=trashbot.current_field_evidence_material.v1`
- `current_field_evidence_material.proof_scope=software_proof_current_field_evidence_material_only`
- `current_field_evidence_material.status=current_field_evidence_ready_not_route_execution_proof | blocked_not_proven`
- `current_field_evidence_material.present_materials | missing_materials | blocked_reasons | next_required_evidence`
- `current_field_evidence_material.camera_frame_observed | radar_scan_observed | map_material_observed | nav2_no_motion_path_generated | manual_gate_blocked_expected`
- `current_field_evidence_material.live_or_field_material_consumed | current_field_evidence_ready_not_route_execution_proof`
- `current_field_evidence_material.blocked_reasons | next_required_evidence | safe_to_control=false | delivery_success=false | primary_actions_enabled=false | robot_control_executed=false | hil_pass=false | connects_cloud_production=false`
- `clean_baseline_nav2_path_material.schema=trashbot.clean_baseline_nav2_path_material.v1`
- `clean_baseline_nav2_path_material.proof_scope=software_proof_clean_baseline_nav2_path_material_only`
- `clean_baseline_nav2_path_material.evidence_boundary=software_proof_clean_baseline_nav2_path_material_only`
- `clean_baseline_nav2_path_material.status=clean_baseline_nav2_path_material_ready_not_route_execution_proof | blocked_not_proven`
- `clean_baseline_nav2_path_material.first_attempt_status | retry_status | retry_success`
- `clean_baseline_nav2_path_material.path_generation_succeeded | path_generated | path_point_count`
- `clean_baseline_nav2_path_material.planner_server_active | managed_runtime_started | managed_runtime_cleanup_ok`
- `clean_baseline_nav2_path_material.initialpose_published | amcl_pose_observed | map_server_active | amcl_active | cleanup_readback_clean`
- `clean_baseline_nav2_path_material.first_failure | retry_success_summary | material_sample_refs`
- `clean_baseline_nav2_path_material.blocked_reasons | next_required_evidence | safe_to_control=false | delivery_success=false | primary_actions_enabled=false | robot_control_executed=false | hil_pass=false | connects_cloud_production=false | route_execution_success=false`
- `field_operator_confirmation_material.schema=trashbot.field_operator_confirmation_material.v1`
- `field_operator_confirmation_material.proof_scope=software_proof_field_operator_confirmation_material_only`
- `field_operator_confirmation_material.evidence_boundary=software_proof_field_operator_confirmation_material_only`
- `field_operator_confirmation_material.status=field_operator_confirmation_material_ready_not_delivery_proof | blocked_not_proven`
- `field_operator_confirmation_material.operator_report_present | operator_report_status | operator_confirmation_present | operator_confirmation_status`
- `field_operator_confirmation_material.operator_present | physical_clearance_confirmed | emergency_stop_ready | observed_motion | observed_stop | reported_at`
- `field_operator_confirmation_material.same_task_id_consumed | linked_route_material_present | linked_delivery_material_present | operator_material_consumed`
- `field_operator_confirmation_material.support_only_reason | material_summaries | blocked_reasons | next_required_evidence`
- `field_operator_confirmation_material.safe_to_control=false | delivery_success=false | primary_actions_enabled=false | robot_control_executed=false | route_execution_success=false | hil_pass=false | connects_cloud_production=false`
- `same_task_mission_evidence_gate.schema=trashbot.same_task_mission_evidence_gate.v1`
- `same_task_mission_evidence_gate.proof_scope=software_proof_same_task_mission_evidence_gate_only`
- `same_task_mission_evidence_gate.status=same_task_mission_gate_ready_not_success_proof | blocked_not_proven`
- `same_task_mission_evidence_gate.terminal_refs | linked_readiness_flags | mission_artifact_delta`
- `same_task_mission_evidence_gate.blocked_reasons | next_required_evidence | safe_to_control=false | delivery_success=false | route_execution_success=false`
- `route_bag_evidence.schema=trashbot.route_bag_evidence.v1`
- `route_bag_evidence.proof_scope=software_proof_route_bag_evidence_intake_only`
- `route_bag_evidence.status=ready_not_route_execution_proof | blocked_not_proven`
- `route_bag_evidence.source_label | db3_basename | db3_size_bytes | db3_sha256_prefix`
- `route_bag_evidence.topic_count | message_count | timestamp_first_ns | timestamp_last_ns | sample_topic_names`
- `route_bag_evidence.blocked_reasons | next_required_evidence | safe_to_control=false | delivery_success=false`
- `route_bag_payload_replay.schema=trashbot.route_bag_payload_replay.v1`
- `route_bag_payload_replay.proof_scope=software_proof_route_bag_payload_replay_only`
- `route_bag_payload_replay.status=ready_not_route_execution_proof | blocked_not_proven`
- `route_bag_payload_replay.source_label | db3_basename | db3_size_bytes | db3_sha256_prefix`
- `route_bag_payload_replay.topic_count | message_count | timestamp_first_ns | timestamp_last_ns | sample_topic_names`
- `route_bag_payload_replay.payload_sample_count | payload_size_min_bytes | payload_size_max_bytes | payload_size_avg_bytes | payload_sha256_prefix_samples`
- `route_bag_payload_replay.blocked_reasons | next_required_evidence | safe_to_control=false | delivery_success=false`
- `route_bag_pose_progress_replay.schema=trashbot.route_bag_pose_progress_replay.v1`
- `route_bag_pose_progress_replay.proof_scope=software_proof_route_bag_pose_progress_replay_only`
- `route_bag_pose_progress_replay.status=ready_not_live_nav2_proof | blocked_not_proven`
- `route_bag_pose_progress_replay.source_label | db3_basename | db3_size_bytes | db3_sha256_prefix`
- `route_bag_pose_progress_replay.topic_count | message_count | timestamp_first_ns | timestamp_last_ns | sample_topic_names`
- `route_bag_pose_progress_replay.pose_sample_count | pose_decode_ok_count | pose_decode_failed_count`
- `route_bag_pose_progress_replay.pose_topic_types | pose_frame_pairs | pose_time_span_ns`
- `route_bag_pose_progress_replay.start_pose | end_pose | displacement_m | nonzero_pose_progress_observed`
- `route_bag_pose_progress_replay.blocked_reasons | next_required_evidence | safe_to_control=false | delivery_success=false`
- `route_bag_semantic_replay.schema=trashbot.route_bag_semantic_replay.v1`
- `route_bag_semantic_replay.proof_scope=software_proof_route_bag_semantic_replay_only`
- `route_bag_semantic_replay.status=ready_not_route_execution_proof | blocked_not_proven`
- `route_bag_semantic_replay.source_label | db3_basename | db3_size_bytes | db3_sha256_prefix`
- `route_bag_semantic_replay.topic_count | message_count | timestamp_first_ns | timestamp_last_ns | sample_topic_names`
- `route_bag_semantic_replay.semantic_sample_count | semantic_decode_ok_count | semantic_decode_failed_count`
- `route_bag_semantic_replay.semantic_topic_types`
- `route_bag_semantic_replay.laser_scan_summary | image_summary | tf_summary | odometry_summary | diagnostic_array_summary`
- `route_bag_semantic_replay.blocked_reasons | next_required_evidence | safe_to_control=false | delivery_success=false`
- `route_bag_full_semantic_decode_matrix.schema=trashbot.route_bag_full_semantic_decode_matrix.v1`
- `route_bag_full_semantic_decode_matrix.proof_scope=software_proof_route_bag_full_semantic_decode_matrix_only`
- `route_bag_full_semantic_decode_matrix.status=ready_not_route_execution_proof | blocked_not_proven`
- `route_bag_full_semantic_decode_matrix.topic_type_count | decoded_topic_type_count | unsupported_topic_type_count | failed_topic_type_count`
- `route_bag_full_semantic_decode_matrix.decoded_message_sample_count | decode_failed_message_sample_count | unsupported_message_sample_count | coverage_ratio`
- `route_bag_full_semantic_decode_matrix.topic_type_matrix[].topic_name | topic_type | message_count | sampled_message_count | status | blocked_reason | decoder_name | sample_sha256_prefixes`
  - 当前 decoded decoder 白名单：`decode_laserscan_payload`、`decode_image_payload`、`decode_tf_message_payload`、`decode_odometry_payload`、`decode_diagnostic_array_payload`
- `route_bag_full_semantic_decode_matrix.blocked_reasons | next_required_evidence | safe_to_control=false | delivery_success=false`

`derived_replay` 只描述 replay JSONL 是否由 `route.csv` 派生成功：

- `generated=true` 说明派生文件已写出，并且 `replay_jsonl` artifact 会扫描到该输出。
- `frame_count` 是 JSONL 行数；例如 2026-06-10 的 01-15 真实 route bundle 期望值是 `17`。
- `blocked_reason=missing_route_csv` 表示请求了 derive，但输入 bundle 中没有可读 `route.csv`。
- `blocked_reason=not_requested` 表示本次没有启用 derive；如果 bundle 本身也没有 replay 文件，manifest 会继续因为缺 `replay_jsonl` 而 fail closed。

即使 `derived_replay.generated=true`，manifest 仍不会把这份材料升级成 Nav2 实跑、固定路线成功或 delivery proof。derive replay 只补 O7-safe 回放材料，不补 O3 现场 rosbag 证据。

当 preflight 是 dry-run、SSH 不可达、preflight JSON 缺失或不是 `ready_for_live_route_capture_not_proven` 时，即使本地 fixture 完整，也必须保持：

- `not_proven=true`
- `blocked_reason=<preflight 状态或 SSH blocker>`

这条规则用于“不再次只消费同一 SSH blocker”：SSH 仍不可达时，研发可以用本地完整 fixture 验证 manifest 功能；但输出不会伪装成真实现场路线材料。

`pc-tools/workstation` 的 O7 Field Evidence Consumer Ingest 会继续消费这份 manifest，并把它和 route replay / labeling fixture 合成统一只读摘要。入口说明见 [O7 Field Evidence Consumer Ingest](o7_field_evidence_consumer_ingest.md)。本地/mock 与 future SSH 读取都必须保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`，以及明确的 `blocked_reason` / `next_required_evidence`。

当这份 manifest 需要进入 O6 local/mock archive 时，relay 侧会接收 `POST /api/o6/archive/field-evidence`，请求体显式携带 `robot_id`、`task_id` 和 `field_evidence_manifest`，并可选附带少量 `trajectory_frames`、`events`、`evidence_refs`。该 ingest 只写 file-backed store，不读原始文件、不连真实云，也不把 `gate_pass=true` 解释成真实送达成功。

如果需要让 O6 对本地/mock fixture 做受限只读探测，请在请求体额外传入 `artifact_access_root`，或在 relay 进程环境变量中设置 `TRASHBOT_O6_ARTIFACT_ACCESS_ROOT`。这只会对 manifest 已经脱敏后的 basename refs 做 allowlist root 内小文件 probe，并在同一 `task_id` 下回读 `artifact_access_probe`；响应不会回显绝对 root，也不会读取 URL、token、base64/raw 内容、串口、ROS topic 或 `/cmd_vel`。缺少 root、root 无效、ref 不安全、越界、目录、缺文件或文件超过 64KB 时均只返回 blocked reason，不计算 sha256。

## O6 local/mock archive ingest

`trashbot.field_evidence_manifest.v1` 可以通过 `remote_cloud_relay.py` 的本地 mock API 写入 O6 archive：

```bash
curl -sS -X POST http://127.0.0.1:8088/api/o6/archive/field-evidence \
  -H 'Content-Type: application/json' \
  --data-binary @/tmp/trashbot_field_evidence_manifest.json
```

如果需要显式指定 robot/task，可以使用 wrapper：

```json
{
  "robot_id": "trashbot-001",
  "task_id": "field-evidence-field-run-001",
  "manifest": {
    "schema": "trashbot.field_evidence_manifest.v1"
  }
}
```

这个 ingest 入口只读取 manifest JSON 中的摘要字段，不读取 `route.csv`、`replay.jsonl`、keyframes、rosbag 或 map 原文件；不会 SSH 上车，不连接生产云，不启动 ROS2 runtime，不发布运动命令。写入成功后：

- `GET /api/o6/archive/tasks/<task_id>` 会返回 `task_origin=field_evidence_manifest` 和 `task.field_evidence`
- `GET /api/o6/consumer/tasks/<task_id>?include=field_evidence,evidence,events` 会返回 O7 可消费的 `field_evidence` section
- `field_evidence.artifacts[]` 只保留 basename、size、sha256、mtime、file_count 等摘要，不回显绝对路径或原始内容
- `field_evidence.artifact_access_probe` 只证明 `software_proof_local_mock_artifact_access_probe_only`，不等于真实 OSS/CDN 媒体可访问
- `manifest_gate.gate_pass=true` 只表示 artifact gate 通过，仍不等于 delivery success

O6 ingest 的 fail-closed 条件与 manifest gate 一致，并额外拒绝任何危险 true：

- `safe_to_control=true`
- `delivery_success=true`
- `primary_actions_enabled=true`
- `connects_cloud_production=true`
- `robot_control_executed=true`
- `real_cloud_db_connected=true`
- `real_oss_connected=true`

artifact 摘要必须包含非空 `sha256` 和正数 `size_bytes`。缺失 `manifest_gate`、`run_id`、`artifacts`、`gate_pass=false`、必需 artifact 未 present、或 payload 含 token/credential/`/cmd_vel`/串口/baudrate/traceback 时，O6 API 返回 `400` 且不写入 store。

## 本地 fixture 复跑

完整 fixture 示例：

```bash
rm -rf /tmp/trashbot_field_manifest_fixture_complete
mkdir -p /tmp/trashbot_field_manifest_fixture_complete/keyframes
mkdir -p /tmp/trashbot_field_manifest_fixture_complete/route_bag
printf 'image: map.pgm\nresolution: 0.05\n' >/tmp/trashbot_field_manifest_fixture_complete/map.yaml
printf 'x,y,yaw\n0,0,0\n1,0,0\n' >/tmp/trashbot_field_manifest_fixture_complete/route.csv
printf '{"x":0,"y":0}\n' >/tmp/trashbot_field_manifest_fixture_complete/keyframes/0001.json
printf 'rosbag2_bagfile_information:\n' >/tmp/trashbot_field_manifest_fixture_complete/route_bag/metadata.yaml
printf '{"event":"start"}\n{"event":"done"}\n' >/tmp/trashbot_field_manifest_fixture_complete/fixed_route_replay.jsonl

python3 onboard/scripts/field_route_evidence_manifest.py \
  --mode local \
  --artifact-root /tmp/trashbot_field_manifest_fixture_complete \
  --preflight-json /tmp/trashbot_field_preflight_ssh.json \
  --output /tmp/trashbot_field_manifest_complete.json
```

如果 `/tmp/trashbot_field_preflight_ssh.json` 仍是 `blocked_ssh_unreachable`，完整 fixture 的 `gate_pass` 可以为 `true`，但 `not_proven=true`、`delivery_success=false`、`primary_actions_enabled=false` 必须保持。

使用离线 intake alias 复跑同一个 fixture：

```bash
python3 onboard/scripts/field_route_evidence_manifest.py \
  --mode local \
  --input /tmp/trashbot_field_manifest_fixture_complete \
  --output /tmp/trashbot_field_manifest_complete_from_input.json
```

真实 bundle 或只有 `route.csv` 的 packet 可以直接派生 replay：

```bash
python3 onboard/scripts/field_route_evidence_manifest.py \
  --mode local \
  --input sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts \
  --derive-replay-jsonl sprints/2026.06.10_02-05_field-run-bundle-replay-intake/artifacts/derived_replay.jsonl \
  --output sprints/2026.06.10_02-05_field-run-bundle-replay-intake/artifacts/field_run_manifest.json \
  --run-id field_run_bundle_replay_intake_20260610
```

派生得到的每一行 JSONL 至少包含：

- `schema`
- `event`
- `frame_index`
- `timestamp_ms`
- `frame_id`
- `x_m`
- `y_m`
- `yaw_rad`
- `state`
- `evidence_ref`
- `source_route_csv`

其中 `evidence_ref` 与 `source_route_csv` 使用 `field_route://...` 安全引用，不写开发机绝对路径，便于后续 archive、解压和 O7 消费者复用。

route-root seed 不需要临时补 `route_bag` fixture 才能通过材料 gate。例如只有 `route/` 与相邻 `map/` 的离线 packet 可以这样复跑：

```bash
python3 onboard/scripts/field_route_evidence_manifest.py \
  --mode local \
  --input /tmp/rober_route_root_seed_gate/route \
  --map-yaml /tmp/rober_route_root_seed_gate/map/map.yaml \
  --map-pgm /tmp/rober_route_root_seed_gate/map/map.pgm \
  --derive-replay-jsonl /tmp/rober_route_root_seed_gate/derived_replay.jsonl \
  --output /tmp/rober_route_root_seed_gate/field_manifest.json
```

该输出可以 `gate_pass=true`，但 `route_root_seed_gate.route_bag_required=false`、`route_root_seed_gate.route_bag_present=false` 会保留缺口；`route_bag_or_live_nav2_log_for_motion_proof` 仍是下一步证据。安全旗标继续保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。

如果同时提供 `--motion-log-root`，manifest 还会新增同一 `task_id` 的 `field_motion_evidence_packet`。推荐命令：

```bash
python3 onboard/scripts/field_route_evidence_manifest.py \
  --mode local \
  --artifact-root sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/route \
  --map-yaml sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/map/trashbot_dynamic_odom_tf_map.yaml \
  --map-pgm sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/map/trashbot_dynamic_odom_tf_map.pgm \
  --motion-log-root sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/remote_capture \
  --derive-replay-jsonl /tmp/derived_replay.jsonl \
  --output /tmp/field_motion_evidence_manifest.json \
  --run-id field_motion_evidence_packet_20260709
```

这份 packet 的语义必须保持保守：

- `route.csv` 的非零位移和 `pulse_and_stop2.log` 的非零 `cmd_vel` 只能证明“现场 motion evidence 存在”。
- 如果 `odom_after_motion*.txt` / `tf_after_motion*.txt` 仍然是 0，packet 要保留 `direct_odom_capture_zero_or_missing` / `direct_tf_capture_zero_or_missing`，而不是宣称 odom/tf 已实证非零。
- `route_bag_or_live_nav2_log.present=true` 只表示存在 `route_bag` 或 live motion logs 支撑 not-delivery proof，不等于 Nav2 成功、不等于真实控制成功，也不等于 delivery success。

如果同时有 O11 proof JSON，可以追加：

```bash
python3 onboard/scripts/field_route_evidence_manifest.py \
  --mode local \
  --artifact-root sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/route \
  --map-yaml sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/map/trashbot_dynamic_odom_tf_map.yaml \
  --map-pgm sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/map/trashbot_dynamic_odom_tf_map.pgm \
  --motion-log-root sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/remote_capture \
  --derive-replay-jsonl /tmp/derived_replay.jsonl \
  --nav2-goal-proof-json /tmp/o11_nav2_goal_execution_proof.json \
  --output /tmp/field_motion_nav2_goal_evidence_manifest.json \
  --run-id field_motion_nav2_goal_evidence_packet_20260709
```

该输出会把 `nav2_goal_execution_evidence` 同时放在 manifest 顶层与 `field_motion_evidence_packet` 内。它只说明 O6/O7 可以白名单消费 Nav2 goal/result 摘要；`result_status=succeeded` 或 `nav2_goal_execution_proven=true` 仍不等于投递成功，真实送达必须另有 delivery record、人工投放确认或后续现场验收。

如果同时提供 `--delivery-result-json`，manifest 还会新增同一 `task_id` 的 `delivery_result_evidence`。推荐命令：

```bash
python3 onboard/scripts/field_route_evidence_manifest.py \
  --mode local \
  --artifact-root /tmp/trashbot_field_manifest_fixture_complete \
  --nav2-goal-proof-json /tmp/o11_nav2_goal_execution_proof.json \
  --delivery-result-json /tmp/delivery_result.json \
  --output /tmp/trashbot_field_manifest_with_delivery_result.json \
  --run-id field_delivery_result_evidence_20260709
```

该输出会把 `delivery_result_evidence` 同时放在 manifest 顶层与 `field_motion_evidence_packet` 内。它只说明 O6/O7 可以白名单消费 delivery result 摘要；即使 `record_status=operator_confirmed_dropoff` 或 `delivery_result_claimed=true`，也仍然只是 `ready_not_delivery_proof`，并保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。

如果只有 O5 cloud command terminal result，可以改用 `--cloud-terminal-result-json`：

```bash
python3 onboard/scripts/field_route_evidence_manifest.py \
  --mode local \
  --artifact-root /tmp/trashbot_field_manifest_fixture_complete \
  --nav2-goal-proof-json /tmp/o11_nav2_goal_execution_proof.json \
  --cloud-terminal-result-json /tmp/cloud_terminal_result.json \
  --output /tmp/trashbot_field_manifest_with_cloud_terminal_result.json \
  --run-id field_cloud_terminal_result_bridge_20260710
```

该输出仍写入 `delivery_result_evidence`，但 `source=cloud_command_terminal_result`、`source_schema=trashbot.cloud_command_terminal_result.v1`。如果同一命令同时带 `--delivery-result-json` 和 `--cloud-terminal-result-json`，脚本会优先使用 `--delivery-result-json`，避免旧 delivery result evidence 合同被 O5 terminal result 隐式覆盖。

如果同时提供 route bag DB3，可以追加：

```bash
python3 onboard/scripts/field_route_evidence_manifest.py \
  --mode local \
  --artifact-root /tmp/trashbot_field_manifest_fixture_complete \
  --route-bag-db3 /tmp/trashbot_field_manifest_fixture_complete/route_bag/route_bag_0.db3 \
  --route-bag-metadata-yaml /tmp/trashbot_field_manifest_fixture_complete/route_bag/metadata.yaml \
  --route-bag-source-label board-bringup-no-motion-sensor-route-bag \
  --output /tmp/trashbot_field_manifest_with_route_bag.json \
  --run-id field_route_bag_evidence_20260709
```

该输出会把 `route_bag_evidence`、`route_bag_payload_replay`、`route_bag_pose_progress_replay`、`route_bag_semantic_replay` 和 `route_bag_full_semantic_decode_matrix` 同时放在 manifest 顶层与 `field_motion_evidence_packet` 内。它只说明 O6/O7 可以消费 route bag DB3 的安全摘要、payload hash、位姿进度、有限语义统计与 per topic/type decode 覆盖矩阵；`status=ready_not_route_execution_proof` 不等于 live Nav2 run、不等于固定路线执行成功、不等于真实云存档成功，也不等于 delivery success。

缺失 fixture 示例：

```bash
rm -rf /tmp/trashbot_field_manifest_fixture_missing
mkdir -p /tmp/trashbot_field_manifest_fixture_missing/keyframes
printf 'image: map.pgm\n' >/tmp/trashbot_field_manifest_fixture_missing/map.yaml

python3 onboard/scripts/field_route_evidence_manifest.py \
  --mode local \
  --artifact-root /tmp/trashbot_field_manifest_fixture_missing \
  --preflight-json /tmp/trashbot_field_preflight_ssh.json \
  --output /tmp/trashbot_field_manifest_missing.json || true
```

缺失 fixture 必须输出 `gate_pass=false`，并通过 `blocked_artifacts_missing` 或 `blocked_artifacts_empty` fail closed。

## 真实 01-15 route artifact 复跑

`sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/route/` 是真实上位机路线材料目录，map 文件在相邻 `artifacts/map/`。生成 O6/O7 可消费的 fail-closed manifest：

```bash
python3 onboard/scripts/field_route_evidence_manifest.py \
  --mode local \
  --artifact-root sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/route \
  --map-yaml sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/map/trashbot_dynamic_odom_tf_map.yaml \
  --map-pgm sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/map/trashbot_dynamic_odom_tf_map.pgm \
  --output /tmp/trashbot_real_route_field_manifest.json
```

该输出应显式引用真实 `route.csv`、`manifest.json`、`keyframes/`、`map.yaml` 和 `map.pgm`。因为没有本轮真实 delivery/result 验收，它仍必须保持 `not_proven=true`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。如果 `route_bag` 或 replay 缺失，manifest 会记录到 optional 缺口，不阻断 O6/O7 route/material intake。

## 真实 SSH 复跑

先运行 preflight：

```bash
python3 onboard/scripts/field_route_evidence_preflight.py \
  --mode ssh \
  --ssh-target root@192.168.1.11 \
  --ssh-port 37878 \
  --timeout-s 5 \
  --output /tmp/trashbot_field_preflight_ssh.json
```

如果现场已经采集到材料，例如远端目录为 `$HOME/.ros/trashbot_runs/<RUN_ID>`，运行：

```bash
python3 onboard/scripts/field_route_evidence_manifest.py \
  --mode ssh \
  --artifact-root '$HOME/.ros/trashbot_runs/<RUN_ID>' \
  --preflight-json /tmp/trashbot_field_preflight_ssh.json \
  --ssh-target root@192.168.1.11 \
  --ssh-port 37878 \
  --timeout-s 5 \
  --output /tmp/trashbot_field_manifest_ssh.json
```

只有真实 SSH 可达、preflight 非 dry-run 且 artifact 完整时，manifest 才能作为 O3 现场路线材料完整性证据；它仍不证明 `delivery_success=true`。
