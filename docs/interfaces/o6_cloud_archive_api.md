# O6 Cloud Archive API

## Scope

`POST /api/o6/archive/tasks`
`GET /api/o6/archive/tasks`
`GET /api/o6/archive/tasks/<task_id>`
`POST /api/o6/archive/labels`
`GET /api/o6/archive/labels`
`GET /api/o6/archive/labels/<task_id>`
`GET /api/o6/archive/labels/<task_id>/export?format=jsonl`
`POST /api/o6/archive/events`
`GET /api/o6/archive/events`
`POST /api/o6/archive/evidence`
`GET /api/o6/archive/evidence`
`POST /api/o6/archive/field-evidence`
`POST /api/o6/archive/artifact-bundle`
`POST /api/o6/archive/inference`
`GET /api/o6/consumer/tasks`
`GET /api/o6/consumer/tasks/<task_id>`

这是 `remote_cloud_relay.py` 内置的本地 mock archive API。它提供 `trashbot.o6.cloud_archive.v1` 的 O6-shaped 数据源，让后续 O7 route replay / labeling / voice / safe command 可以从统一的任务存档形状继续消费，但它不连接真实云数据库，不连接真实 OSS，不下发机器人控制，也不声明 production cloud ready。

`POST /api/o6/archive/field-evidence` 是同一份 local/mock archive 的现场材料入口。它接受 `trashbot.field_evidence_manifest.v1` 本体或包含该 manifest 的小型 wrapper，按 manifest 派生 task、trajectory、events、evidence refs 和 field evidence 摘要后写入 `FileBackedO6CloudArchiveStore`。它的成功响应固定保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`connects_cloud_production=false`、`robot_control_executed=false`、`real_cloud_db_connected=false`、`real_oss_connected=false`，并使用 `source=local_mock_field_evidence_archive`。

`POST /api/o6/archive/artifact-bundle` 是本轮新增的 additive ingest alias。它接受 `trashbot.o6.artifact_bundle.v1` 的结构化 route/replay/keyframe/evidence 摘要，复用同一份 file-backed store，成功响应固定保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`connects_cloud_production=false`、`robot_control_executed=false`、`real_cloud_db_connected=false`、`real_oss_connected=false`，并使用 `source=local_mock_artifact_bundle_archive`。为兼容现有入口，`POST /api/o6/archive/field-evidence` 在 body 顶层为 `artifact_bundle` wrapper 或 `schema=trashbot.o6.artifact_bundle.v1` 时，也会路由到同一条 artifact bundle ingest 逻辑。

`artifact_access_probe` 是新增 additive 只读摘要，schema 为 `trashbot.o6.artifact_access_probe.v1`，证据边界固定为 `software_proof_local_mock_artifact_access_probe_only`。它只在请求字段 `artifact_access_root` 或环境变量 `TRASHBOT_O6_ARTIFACT_ACCESS_ROOT` 指定 allowlist root 后，对 artifact bundle 原始相对 refs 或 field evidence 安全 basename refs 做本机小文件探测；响应只返回存在性、大小、sha256、detected_type、blocked_reason、proof_scope 和计数，不回显 allowlist root、绝对路径、token、URL query、base64/raw 内容或控制字段。没有 root、root 无效、ref 不安全、越界、目录、缺文件或超过 64KB 时均返回 blocked probe，不读取文件内容。

`offline_artifact_seed_smoke` 是本轮新增的 additive 离线种子摘要，schema 为 `trashbot.o6.offline_artifact_seed_smoke.v1`，source 为 `local_mock_offline_artifact_seed_smoke`，proof_scope 为 `software_proof_offline_artifact_seed_smoke_only`。它由 `artifact_access_probe` 与 artifact bundle / field evidence refs 派生，只保留 counts、sample basename refs、sha256 prefix、blocked_reasons、next_required_evidence、proof_boundary 和全 false 安全旗标，不回显 allowlist root、绝对路径、原始文件内容、token、URL query、base64、串口路径或 `/cmd_vel`。

`offline_artifact_seed_smoke` 是本轮新增的 additive 离线种子摘要，schema 为 `trashbot.o6.offline_artifact_seed_smoke.v1`，source 为 `local_mock_offline_artifact_seed_smoke`，proof_scope 为 `software_proof_offline_artifact_seed_smoke_only`。它由 `artifact_access_probe` 与 artifact bundle / field evidence refs 派生，只保留 counts、sample basename refs、sha256 prefix、blocked_reasons、next_required_evidence、proof_boundary 和全 false 安全旗标，不回显 allowlist root、绝对路径、原始文件内容、token、URL query、base64、串口路径或 `/cmd_vel`。

`route_root_seed_gate` 是 additive route-root seed gate 摘要，schema 为 `trashbot.o6.route_root_seed_gate.v1`，source 为 `local_mock_route_root_seed_gate`，proof_scope 为 `software_proof_local_mock_route_root_seed_gate_only`。它消费 field evidence manifest 或 artifact bundle 中的 route-root gate / refs 摘要，只返回 `route.csv`、manifest、derived replay、evidence 计数和 basename 样本。`route_bag` 是可选增强证据：缺失时必须输出 `route_bag_required=false`、`route_bag_present=false`、`route_bag_missing_optional` 和 `route_bag_optional_evidence`，但不得让已有 route/replay/manifest 的 local/mock route-root seed gate 失败。该摘要固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`，不回显绝对路径、token、base64/raw 内容、串口字段或 `/cmd_vel`。

`field_motion_evidence_packet` 是本轮新增的 additive 现场运动证据摘要，schema 为 `trashbot.field_motion_evidence_packet.v1`，proof_scope 固定为 `software_proof_field_motion_evidence_packet_only`。它允许由 `field_evidence_manifest` 或 `artifact_bundle` 携带后写入同一 `task_id`，并在 archive task detail、`field_evidence`、`artifact_bundle`、`field_evidence_consumer_ingest`、`artifact_bundle_consumer_ingest` 与 consumer detail 顶层 alias 中回读。O6 只保留 `status`、`route_summary.frame_count/nonzero_displacement_observed/displacement_m`、`motion_log_summary.live_motion_evidence_present/evidence_sources`、`route_bag_or_live_nav2_log.present/source/route_bag_present/live_motion_log_present`、`blocked_reasons`、`next_required_evidence` 和四个 false safety flags；`path/root/ref/token/raw/base64` 及任何危险 true 声明都不会回显，缺包时固定返回 `blocked_not_proven` 摘要，避免 consumer 猜测已完成。

`nav2_goal_execution_evidence` 是 additive Nav2 goal/result 证据摘要，schema 为 `trashbot.nav2_goal_execution_evidence.v1`，proof_scope 固定为 `software_proof_nav2_goal_execution_evidence_only`。它允许由 `field_evidence_manifest`、`artifact_bundle` 或其中的 `field_motion_evidence_packet` 携带后写入同一 `task_id`，并在 archive task detail、`field_evidence`、`artifact_bundle`、`field_evidence_consumer_ingest`、`artifact_bundle_consumer_ingest`、consumer detail 顶层 alias 与 `include=nav2_goal_execution_evidence` 中回读。O6 只保留 `task_id/status/proof_status/source/goal_requested/goal_sent/goal_accepted/result_received/goal_result_status/result_status_code/nav2_goal_execution_proven/base_motion_command_nonzero_proven/base_command_mode/requested_base_command_mode/pose_progress_summary/base_feedback_summary/base_command_summary/blocked_reasons/next_required_evidence` 和四个 false safety flags；缺包、schema/proof_scope 不匹配、危险 true、path/root/token/raw/base64 或 unsafe text 均返回 `blocked_not_proven` 占位摘要，不回显危险内容。

`delivery_result_evidence` 是 additive 送达结果/人工投放确认摘要，schema 为 `trashbot.delivery_result_evidence.v1`，proof_scope 固定为 `software_proof_delivery_result_evidence_only`。它允许由 `field_evidence_manifest`、`artifact_bundle` 或其中的 `field_motion_evidence_packet` 携带后写入同一 `task_id`，并在 archive task detail、`field_evidence`、`artifact_bundle`、`field_evidence_consumer_ingest`、`artifact_bundle_consumer_ingest`、consumer detail 顶层 alias 与 `include=delivery_result_evidence` 中回读。O6 只保留 `task_id/status/source/source_schema/record_present/record_read_ok/record_status/delivery_result_claimed/operator_confirmation_present/dropoff_confirmation_type/completed_at_utc/linked_nav2_goal_execution_proven/blocked_reasons/next_required_evidence` 和四个 false safety flags；坏 schema、proof_scope 不匹配、危险 true、path/root/token/raw/base64、credential URL 或 unsafe text 均返回 `blocked_not_proven` 占位摘要，不回显危险内容。

当 Algorithm 从 O5 云端命令终态转换送达结果时，`delivery_result_evidence.source` 可以是 `cloud_command_terminal_result`，`delivery_result_evidence.source_schema` 必须原样保留为 `trashbot.cloud_command_terminal_result.v1`。Algorithm 可输入 `status=ready_not_delivery_proof`；O6 会把该状态规范化为 O7 兼容的 `delivery_result_evidence_ready_not_delivery_proof` 后再写入 archive/readback 响应。这只表示 O6/O7 能读回云端终态来源，不表示真实 delivery success、真实 operator confirmation 或机器人控制已经执行。

`route_execution_result_delivery_readiness` 是 additive 结果链 readiness 摘要，输入 schema 为 `trashbot.route_execution_result_delivery_readiness.v1`，O6 回读 schema 为 `trashbot.o6.route_execution_result_delivery_readiness.v1`，proof_scope 固定为 `software_proof_route_execution_result_delivery_readiness_only`。它允许由 `field_evidence_manifest`、`artifact_bundle` 或其中的 `field_motion_evidence_packet` 携带后写入同一 `task_id`，并在 archive task detail、`field_evidence`、`artifact_bundle`、`field_evidence_consumer_ingest`、`artifact_bundle_consumer_ingest`、consumer detail 顶层 alias 与 `include=route_execution_result_delivery_readiness` 中回读。O6 只保留 `task_id/status/source/source_schema/task_id_source/route_execution_result_status/route_execution_result_source/route_execution_result_ready/route_execution_success=false/delivery_result_readiness_status/delivery_result_readiness_source/delivery_result_readiness_ready/operator_confirmation_readiness_status/operator_confirmation_readiness_source/operator_confirmation_readiness_ready/linked_nav2_goal_execution_proven/linked_delivery_result_claimed/linked_operator_confirmation_present/blocked_reasons/next_required_evidence` 和四个 false safety flags；坏 schema、proof_scope 不匹配、危险 true、unsafe path/topic/url/token/raw/base64/text 或缺必填字段均返回 `blocked_not_proven` 占位摘要，不回显危险内容。

`route_delivery_closure_packet` 是 additive delivery closure 安全摘要，输入 schema 为 `trashbot.route_delivery_closure_packet.v1`，O6 回读 schema 为 `trashbot.o6.route_delivery_closure_packet.v1`，proof_scope 固定为 `software_proof_route_delivery_closure_packet_only`。它允许由 `field_evidence_manifest`、`artifact_bundle` 或其中的 `field_motion_evidence_packet` 携带后写入同一 `task_id`，并在 archive task detail、`field_evidence`、`artifact_bundle`、`field_evidence_consumer_ingest`、`artifact_bundle_consumer_ingest`、consumer detail 顶层 alias 与 `include=route_delivery_closure_packet` 中回读。O6 只保留 `task_id/status/proof_scope/source/source_schema/linked_route_execution_result_delivery_readiness_ready/linked_nav2_goal_execution_ready/linked_delivery_result_ready/linked_operator_confirmation_ready/linked_pose_progress_ready/blocked_reasons/next_required_evidence` 和四个 false safety flags；坏 schema、proof_scope 不匹配、危险 true、unsafe path/topic/url/token/raw/base64/text、缺关键 linked flag 或缺 source 时均返回 `blocked_not_proven` 占位摘要，不回显 archive detail、原始 payload、路径、URL、token 或任何成功宣称。

`same_task_mission_evidence_gate` 是 additive same-task mission gate 安全摘要，输入 schema 为 `trashbot.same_task_mission_evidence_gate.v1`，O6 回读 schema 为 `trashbot.o6.same_task_mission_evidence_gate.v1`，proof_scope 固定为 `software_proof_same_task_mission_evidence_gate_only`。它允许由 `field_evidence_manifest`、`artifact_bundle` 或其中的 `field_motion_evidence_packet` 携带后写入同一 `task_id`，并在 archive task detail、`field_evidence`、`artifact_bundle`、`field_evidence_consumer_ingest`、`artifact_bundle_consumer_ingest`、consumer detail 顶层 alias 与 `include=same_task_mission_evidence_gate` 中回读。O6 兼容 legacy 字符串和新的结构化 `mission_artifact_delta`，回读时统一只保留 `task_id/status/source/source_schema/terminal_refs/terminal_ref_count/mission_artifact_delta/linked_readiness_flags/same_task_id_consumed/live_or_field_command_executed/support_only_reason/okr_credit_allowed/blocked_reasons/next_required_evidence` 和全 false safety flags；缺失字段、schema mismatch、proof scope mismatch、task mismatch、unsafe text/raw/base64/绝对路径/credential URL/token、support-only 输入或危险 true 均会 fail-closed 为 `okr_credit_allowed=false`，必要时把 gate 自身降级为 `blocked_not_proven`，且不回显原始 payload、绝对路径、URL、token 或任何 control / delivery success 字段。`same_task_mission_gate_ready_not_success_proof` 只表示同一 `task_id` 的 terminal result、route execution readiness、closure packet 与 pose progress 摘要可回读，不证明真实 production cloud、真实 route execution、真实 operator confirmation 或真实 delivery success。

`same_task_field_material_packet` 是 additive same-task 准现场材料包安全摘要，输入 schema 为 `trashbot.same_task_field_material_packet.v1`，O6 回读 schema 为 `trashbot.o6.same_task_field_material_packet.v1`，proof_scope 固定为 `software_proof_same_task_field_material_packet_only`。它允许由 `field_evidence_manifest`、`artifact_bundle` 或其中的 `field_motion_evidence_packet` 携带后写入同一 `task_id`，并在 archive task detail、`field_evidence`、`artifact_bundle`、`field_evidence_consumer_ingest`、`artifact_bundle_consumer_ingest`、consumer detail 顶层 alias 与 `include=same_task_field_material_packet` 中回读。Algorithm 实际 packet 支持 `present_materials` / `missing_materials` 中包含 `map_yaml`、`route_csv`、`keyframes`、`route_bag_or_rosbag`、`replay_jsonl`，并把 per-material 摘要放在 `material_summaries.<material>.basename|size_bytes|sha256_prefix|sample_refs|count|present`，顶层 `sample_refs` 保持 list 形态。O6 回读时保留 `task_id/status/source/source_schema/task_id_source/present_materials/missing_materials/map_yaml_present/route_csv_present/keyframes_present/route_bag_or_rosbag_present/replay_jsonl_present/counts/sample_refs/material_sample_refs/same_task_id_consumed/live_or_field_material_consumed/blocked_reasons/next_required_evidence` 和全 false safety flags；其中顶层 `sample_refs` 会被安全降级为 basename list，`material_sample_refs` 保留每种材料的 basename、size、sha256 短前缀、sample refs 与 count。`map_yaml` 当前是 optional：缺失时可保留 `same_task_field_material_map_yaml_missing_optional`，但不会单独把其他已消费材料打成 failed。坏 schema、proof scope mismatch、task mismatch、危险 true、unsafe text/raw/base64、绝对路径、URL/credential query、token 或缺关键材料字段时一律只把该 section 降级为 `blocked_not_proven`，不阻断整条 archive 写入。

`cloud_external_probe` 是本轮新增的 additive live endpoint probe readback 摘要，输入/回读 schema 为 `trashbot.o6.cloud_external_probe_readback.v1`，proof_scope 固定为 `software_proof_docker_cloud_external_probe_bundle_gate`。它复用既有 `trashbot.cloud_external_probe_bundle` artifact 的生成/校验逻辑，只把 `task_id/status/source/endpoint_count/endpoints_covered/endpoint_contract_ready/base_url_scheme/blocked_reasons/next_required_evidence` 和全 false safety flags 写入 O6 task detail、`field_evidence`、`artifact_bundle`、consumer detail 顶层 alias 与 `include=cloud_external_probe`。它不回显 base URL、Authorization、bearer token、response body、本地路径或 traceback；即使 endpoint contract ready，也只代表 software proof readback，不代表真实公网 HTTPS/TLS、真实 production cloud、真实 4G/SIM 或真实 delivery success。

`cloud_db_queue_external_probe` 是本轮新增的 additive production DB/queue probe readback 摘要，输入/回读 schema 为 `trashbot.o6.cloud_db_queue_external_probe_readback.v1`，proof_scope 固定为 `software_proof_docker_cloud_db_queue_external_probe_gate`。它复用既有 `trashbot.cloud_db_queue_external_probe_bundle` artifact 的生成/校验逻辑，只把 `task_id/status/source/probe_count/probe_names/probe_statuses/external_probe_complete=false/blocked_reasons/next_required_evidence` 和全 false safety flags 写入 O6 task detail、`field_evidence`、`artifact_bundle`、consumer detail 顶层 alias 与 `include=cloud_db_queue_external_probe`。它不回显 DB/queue endpoint、连接串、凭证、worker URL、本地路径或原始异常；即使 probe count 完整，也只代表 software proof readback，不代表真实 production DB/queue、真实多实例一致性、真实事务隔离、真实备份恢复或真实 delivery success。

本地复跑 smoke [`/Users/m1/apps/rober/onboard/scripts/o5_same_task_mission_archive_smoke.py`](/Users/m1/apps/rober/onboard/scripts/o5_same_task_mission_archive_smoke.py) 支持 `--state-backend file|sqlite`。默认 `file` 保持上一轮 in-process smoke 兼容；`sqlite` shadow 模式必须使用 `build_server(..., state_backend="sqlite")` 写入 terminal result 后关闭 relay，再用同一 SQLite state path 重启 relay，读取 `GET /api/commands/<command_id>/result?robot_id=...` 返回的 `trashbot.cloud_command_result_reconciliation.v2`。该 readback reconciliation 继续经 `field_route_evidence_manifest.py --cloud-terminal-result-json` 写入 `POST /api/o6/archive/field-evidence`，并额外复用既有 `cloud_external_probe` / `cloud_db_queue_external_probe` artifact summary 逻辑，把两类 probe 摘要以 `cloud_external_probe` / `cloud_db_queue_external_probe` additive section 写入同一 `task_id`。最后读取 `GET /api/o6/consumer/tasks/<task_id>?include=same_task_mission_evidence_gate,cloud_external_probe,cloud_db_queue_external_probe`。本轮 smoke 的总证明边界固定为 `software_proof_o5_o6_live_endpoint_probe_readback_only`，输出必须包含 `relay_state_backend`、`relay_restart_readback`、`sqlite_state_store_reopened`、`reconciliation.result_state=terminal_result_recorded`、`same_task_mission_gate_ready_not_success_proof`、`cloud_external_probe_ready_not_production_proof` 和 `cloud_db_queue_external_probe_ready_not_production_proof`，并继续保持 `connects_cloud_production=false`、`delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。它只证明本地/mock same-task archive/readback 可以安全消费 live endpoint probe 摘要，不证明真实 production cloud、production DB、queue、多实例一致性、真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、真实 route execution 或 delivery success。

`route_bag_evidence` 是 additive route bag DB3 摘要证据，输入 schema 为 `trashbot.route_bag_evidence.v1`，O6 回读 schema 为 `trashbot.o6.route_bag_evidence.v1`，proof_scope 固定为 `software_proof_route_bag_evidence_intake_only`。它允许由 `field_evidence_manifest`、`artifact_bundle` 或其中的 `field_motion_evidence_packet` 携带后写入同一 `task_id`，并在 archive task detail、`field_evidence`、`artifact_bundle`、`field_evidence_consumer_ingest`、`artifact_bundle_consumer_ingest`、consumer detail 顶层 alias 与 `include=route_bag_evidence` 中回读。O6 只保留 `task_id/status/source/source_label/task_id_source/metadata_present/db3_present/db3_read_ok/db3_size_bytes/db3_sha256_prefix/topic_count/message_count/timestamp_first_ns/timestamp_last_ns/sample_topic_names/blocked_reasons/next_required_evidence` 和四个 false safety flags；`sample_topic_names` 会降级成短 topic label，`/cmd_vel` 等控制 topic、坏 schema、坏 proof_scope、危险 true、path/root/token/raw/base64、credential URL 或 unsafe text 均返回 `blocked_not_proven` 占位摘要，不回显危险内容。

`route_bag_payload_replay` 是 additive route bag payload replay 摘要，输入 schema 为 `trashbot.route_bag_payload_replay.v1`，O6 回读 schema 为 `trashbot.o6.route_bag_payload_replay.v1`，proof_scope 固定为 `software_proof_route_bag_payload_replay_only`。它允许由 `field_evidence_manifest`、`artifact_bundle` 或其中的 `field_motion_evidence_packet` 携带后写入同一 `task_id`，并在 archive task detail、`field_evidence`、`artifact_bundle`、`field_evidence_consumer_ingest`、`artifact_bundle_consumer_ingest`、consumer detail 顶层 alias 与 `include=route_bag_payload_replay` 中回读。O6 只保留 `task_id/status/source/source_label/task_id_source/metadata_present/db3_present/db3_read_ok/db3_size_bytes/db3_sha256_prefix/topic_count/message_count/timestamp_first_ns/timestamp_last_ns/sample_topic_names/payload_sample_count/payload_size_min_bytes/payload_size_max_bytes/payload_size_avg_bytes/payload_sha256_prefix_samples/blocked_reasons/next_required_evidence` 和四个 false safety flags；`sample_topic_names` 只保留短 topic label，`payload_sha256_prefix_samples` 只保留短 hash 前缀，坏 schema、坏 proof_scope、危险 true、path/root/token/raw/base64、credential URL、unsafe topic 或负数/缺失 payload 统计均返回 `blocked_not_proven` 占位摘要，不回显原始 payload 或完整 hash。

`route_bag_semantic_replay` 是本轮新增的 additive route bag 语义 replay 摘要，输入 schema 为 `trashbot.route_bag_semantic_replay.v1`，O6 回读 schema 为 `trashbot.o6.route_bag_semantic_replay.v1`，proof_scope 固定为 `software_proof_route_bag_semantic_replay_only`。它允许由 `field_evidence_manifest`、`artifact_bundle` 或其中的 `field_motion_evidence_packet` 携带后写入同一 `task_id`，并在 archive task detail、`field_evidence`、`artifact_bundle`、`field_evidence_consumer_ingest`、`artifact_bundle_consumer_ingest`、consumer detail 顶层 alias 与 `include=route_bag_semantic_replay` 中回读。O6 只保留 `task_id/status/source/source_label/task_id_source/metadata_present/db3_present/db3_read_ok/db3_size_bytes/db3_sha256_prefix/topic_count/message_count/timestamp_first_ns/timestamp_last_ns/sample_topic_names/semantic_sample_count/semantic_decode_ok_count/semantic_decode_failed_count/semantic_topic_types/laser_scan_summary/image_summary/tf_summary/blocked_reasons/next_required_evidence` 和四个 false safety flags；`semantic_topic_types` 允许回读 `nav_msgs.msg.Odometry` 这类安全规范化 type label，但仍不回显 raw payload、base64、绝对路径、token、credential URL 或完整 hash。坏 schema、坏 proof_scope、危险 true、unsafe text/topic、缺必填字段均返回 `blocked_not_proven` 占位摘要。

`route_bag_full_semantic_decode_matrix` 是 additive route bag 全量语义解码覆盖矩阵摘要，输入 schema 为 `trashbot.route_bag_full_semantic_decode_matrix.v1`，O6 回读 schema 为 `trashbot.o6.route_bag_full_semantic_decode_matrix.v1`，proof_scope 固定为 `software_proof_route_bag_full_semantic_decode_matrix_only`。它允许由 `field_evidence_manifest`、`artifact_bundle` 或其中的 `field_motion_evidence_packet` 携带后写入同一 `task_id`，并在 archive task detail、`field_evidence`、`artifact_bundle`、`field_evidence_consumer_ingest`、`artifact_bundle_consumer_ingest`、consumer detail 顶层 alias 与 `include=route_bag_full_semantic_decode_matrix` 中回读。O6 只保留 `task_id/status/source/source_label/task_id_source/counts/coverage_ratio/topic_type_matrix/blocked_reasons/next_required_evidence` 和 false safety flags；`topic_type_matrix[]` 只回显 safe topic、safe ROS type、decoded/unsupported/failed/unsafe 状态、`decoder_name`、兼容 alias `decoder`、sample counts 和 blocked reasons，其中 `nav_msgs.msg.Odometry` 的 decoded item 会按安全规范化结果保留 `decoder_name=decode_odometry_payload`，`diagnostic_msgs.msg.DiagnosticArray` 的 decoded item 会保留 `decoder_name=decode_diagnostic_array_payload`，并保留对应 counts。坏 schema、坏 proof_scope、危险 true、unsafe topic/text/path/url/token/raw/base64、缺必填计数、负数或非法 coverage ratio 均返回 `blocked_not_proven` 占位摘要，不回显原始 ROS payload、完整 hash、绝对路径、credential URL 或控制字段。

## O6 Artifact Bundle Ingest

`POST /api/o6/archive/artifact-bundle` 接收 `trashbot.o6.artifact_bundle.v1` 的本地/mock 归档输入。它只读取 HTTP body 中已有的结构化摘要，不读取真实 `route.csv` / replay JSONL / keyframe / evidence 文件，不连接生产 DB/queue/OSS，不访问真实云或机器人控制链路。

请求体支持两种形态：

- 顶层 wrapper：`{ "artifact_bundle": { ... } }`
- 直传 bundle：顶层 `schema=trashbot.o6.artifact_bundle.v1`

bundle 建议字段：

- `schema=trashbot.o6.artifact_bundle.v1`
- `robot_id`
- `task_id`
- `route_refs[]`
- `replay_refs[]`
- `keyframe_refs[]`
- `evidence_refs[]`
- `trajectory_frames[]`
- `events[]`
- 可选 `artifact_access_root`：只用于本机 allowlist root 小文件 probe；绝对 root 不会写入 archive 响应
- 可选 `nav2_goal_execution_evidence`：只接收 `trashbot.nav2_goal_execution_evidence.v1` 的白名单摘要；也可放在 `field_motion_evidence_packet.nav2_goal_execution_evidence`
- 可选 `route_execution_result_delivery_readiness`：只接收 `trashbot.route_execution_result_delivery_readiness.v1` 的结果链 readiness 摘要；也可放在 `field_motion_evidence_packet.route_execution_result_delivery_readiness`
- 可选 `route_delivery_closure_packet`：只接收 `trashbot.route_delivery_closure_packet.v1` 的 delivery closure 摘要；也可放在 `field_motion_evidence_packet.route_delivery_closure_packet`
- 可选 `same_task_field_material_packet`：只接收 `trashbot.same_task_field_material_packet.v1` 的 same-task 材料包摘要；可含 `map_yaml` optional 材料，也可放在 `field_motion_evidence_packet.same_task_field_material_packet`
- 可选 `same_task_mission_evidence_gate`：只接收 `trashbot.same_task_mission_evidence_gate.v1` 的同 task mission gate 摘要；也可放在 `field_motion_evidence_packet.same_task_mission_evidence_gate`
- 可选 `route_bag_evidence`：只接收 `trashbot.route_bag_evidence.v1` 的白名单 DB3 摘要；也可放在 `field_motion_evidence_packet.route_bag_evidence`
- 可选 `route_bag_semantic_replay`：只接收 `trashbot.route_bag_semantic_replay.v1` 的白名单语义摘要；也可放在 `field_motion_evidence_packet.route_bag_semantic_replay`
- 可选 `route_bag_full_semantic_decode_matrix`：只接收 `trashbot.route_bag_full_semantic_decode_matrix.v1` 的解码覆盖矩阵摘要；也可放在 `field_motion_evidence_packet.route_bag_full_semantic_decode_matrix`
- 可选 `route_bag_pose_progress_replay`：只接收 `trashbot.route_bag_pose_progress_replay.v1` 的白名单位姿进度摘要；也可放在 `field_motion_evidence_packet.route_bag_pose_progress_replay`

必需安全条件：

- 顶层与 bundle 内的 `safe_to_control=false`
- 顶层与 bundle 内的 `delivery_success=false`
- 顶层与 bundle 内的 `primary_actions_enabled=false`
- 不得出现 `connects_cloud_production=true`、`robot_control_executed=true`、`real_cloud_db_connected=true`、`real_oss_connected=true`
- `route_refs[] / replay_refs[] / keyframe_refs[] / evidence_refs[]` 至少有一个非空
- 所有 ref 都只保存 basename 摘要；绝对路径、credential URL、token、base64/raw media、串口路径和 `/cmd_vel` 一律 fail-closed

成功响应固定：

- `schema=trashbot.o6.artifact_bundle_archive.v1`
- `source=local_mock_artifact_bundle_archive`
- `artifact_bundle_written=true`
- `task_origin=artifact_bundle`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `connects_cloud_production=false`
- `robot_control_executed=false`

写入后的 task 可继续通过 `GET /api/o6/archive/tasks/<task_id>` 和 `GET /api/o6/consumer/tasks/<task_id>?include=field_evidence,trajectory,evidence,events` 读回。为保持 additive：

- archive task detail 会返回 `task.artifact_bundle`
- consumer detail 会返回顶层 alias `artifact_bundle` 与 `artifact_bundle_consumer_ingest`
- `artifact_media_preflight` 会继续围绕同一 `task_id` 暴露 route/replay/keyframe/evidence 计数、样本 ref 和 `local_mock/not_proven` blocked reasons
- `artifact_access_probe` 会继续围绕同一 `task_id` 暴露受限只读探测摘要；默认 `blocked_not_proven`，只有 ref 在 allowlist root 内且文件不超过 64KB 时才计算 sha256
- `offline_artifact_seed_smoke` 会继续围绕同一 `task_id` 暴露离线种子摘要；它只返回 counts、sample basename refs、sha256 prefix、blocked reasons、next required evidence 和全 false 安全旗标，不证明真实 production cloud、OSS/CDN、真实媒体播放、真实机器人运动或 delivery success
- `route_root_seed_gate` 会继续围绕同一 `task_id` 暴露 route-root seed gate 摘要；`route_bag_required=false`，缺 `route_bag` 时只记录 optional blocked reason / next evidence，不阻断 route-root seed readback
- `nav2_goal_execution_evidence` 会继续围绕同一 `task_id` 暴露 Nav2 goal/request/result 摘要；它只证明 software proof readback，不证明真实 live Nav2 run、真实底盘控制或 delivery success
- `route_execution_result_delivery_readiness` 会继续围绕同一 `task_id` 暴露 route execution result / delivery readiness / operator confirmation readiness 摘要；它只证明 software proof readback，不证明真实 route execution、真实 delivery result、真实 operator confirmation 或 delivery success
- `same_task_mission_evidence_gate` 会继续围绕同一 `task_id` 暴露 terminal result、route execution readiness、closure packet 和 pose progress 的 gate 摘要；它只证明 software proof readback，不证明真实 production cloud、真实 route execution、真实 operator confirmation 或 delivery success
- `route_bag_evidence` 会继续围绕同一 `task_id` 暴露 DB3 metadata/topic/message/timestamp 摘要；它只证明 software proof readback，不证明真实 live Nav2 run、路线执行成功或 delivery success

失败时返回 `400`，且不得写入 store：

- bad JSON、非对象 body、schema 不匹配
- 四类 ref 全空
- 任何危险 true 字段
- 任意 ref 含绝对路径、credential URL、token、base64/raw content、串口或控制字段
- `trajectory_frames[]` / `events[]` 超过 O6 既有上限

## O6 Field Evidence Manifest Ingest

`POST /api/o6/archive/field-evidence` 接收 `trashbot.field_evidence_manifest.v1` 的本地/mock 归档输入，把现场/离线材料 manifest 转成 O6 local/mock archive task。它只读取 HTTP body 中已有的 manifest 摘要，不读取 artifact 原文件，不连接生产 DB/queue/OSS，不 SSH，不启动 ROS2 runtime，也不会发 `/cmd_vel`。

请求体必须至少包含：

- `robot_id`
- `task_id`
- `field_evidence_manifest`

兼容输入：

- `manifest` 作为旧包装别名仍可被 relay 接受
- body 顶层直接传 `schema=trashbot.field_evidence_manifest.v1` 的 manifest 对象也可被接受
- 可选 `trajectory_frames[]`、`events[]`、`evidence_refs[]` 会被安全校验后写入同一条 file-backed task
- 可选 `artifact_access_root` 会让 relay 用 manifest 中已经脱敏的 basename refs 做本机小文件 probe；缺省时只返回 `allowlist_root_missing` blocked 摘要
- 可选 `nav2_goal_execution_evidence` 可放在 manifest 顶层或 `field_motion_evidence_packet` 内；O6 只回读白名单字段，坏包降级为 `blocked_not_proven`
- 可选 `route_execution_result_delivery_readiness` 可放在 manifest 顶层或 `field_motion_evidence_packet` 内；O6 只回读白名单字段，坏包降级为 `blocked_not_proven`
- 可选 `route_delivery_closure_packet` 可放在 manifest 顶层或 `field_motion_evidence_packet` 内；O6 只回读 linked readiness flags、blocked reasons、next evidence 与 false safety flags，坏包降级为 `blocked_not_proven`
- 可选 `same_task_field_material_packet` 可放在 manifest 顶层或 `field_motion_evidence_packet` 内；O6 优先读取 `material_summaries`，兼容旧的 dict-shaped `sample_refs` 或顶层材料字段，并回读材料 presence、safe counts、basename/size/sha256 prefix、顶层 basename list `sample_refs` 与 false safety flags，坏包降级为 `blocked_not_proven`
- 可选 `same_task_mission_evidence_gate` 可放在 manifest 顶层或 `field_motion_evidence_packet` 内；O6 只回读 terminal refs basename、mission artifact delta、linked readiness flags 与 false safety flags，坏包降级为 `blocked_not_proven`
- 可选 `route_bag_evidence` 可放在 manifest 顶层或 `field_motion_evidence_packet` 内；O6 只回读白名单字段，坏包降级为 `blocked_not_proven`
- 可选 `route_bag_full_semantic_decode_matrix` 可放在 manifest 顶层或 `field_motion_evidence_packet` 内；O6 只回读 counts、coverage ratio 和 safe topic/type matrix，坏包降级为 `blocked_not_proven`
- 可选 `route_bag_pose_progress_replay` 可放在 manifest 顶层或 `field_motion_evidence_packet` 内；O6 只回读白名单字段，坏包降级为 `blocked_not_proven`

必需安全条件：

- `field_evidence_manifest.schema=trashbot.field_evidence_manifest.v1`
- `manifest_gate.schema=trashbot.field_evidence_manifest.v1`
- `field_evidence_manifest.gate_pass=true`
- `manifest_gate.gate_pass=true`
- `manifest_gate.status=gated`
- 顶层 `safe_to_control=false`
- 顶层 `delivery_success=false`
- 顶层 `primary_actions_enabled=false`
- 顶层 `connects_cloud_production=false`
- 顶层 `robot_control_executed=false`
- `artifacts{}` 至少包含一个 present artifact，且 present artifact 必须有 `path/size_bytes/sha256`

成功响应固定：

- `schema=trashbot.o6.field_evidence_archive.v1`
- `source=local_mock_field_evidence_archive`
- `field_evidence_written=true`
- `task_origin=field_evidence_manifest`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `connects_cloud_production=false`
- `robot_control_executed=false`

写入后的 task 可继续通过 `GET /api/o6/archive/tasks/<task_id>` 和 `GET /api/o6/consumer/tasks/<task_id>?include=field_evidence,trajectory,evidence,events` 读回。`task.field_evidence` 只保留 artifact basename、size、sha256、mtime、derived replay 计数、manifest gate、preflight 摘要和请求摘要，不回显绝对路径、credential URL、原始图片、视频、音频、rosbag 内容或 base64。

新增 additive 摘要：

- `task.field_evidence.artifact_media_preflight`
- `task.field_evidence_consumer_ingest.artifact_media_preflight`
- `GET /api/o6/consumer/tasks/<task_id>?include=field_evidence` 顶层 alias `artifact_media_preflight`
- `task.field_evidence.artifact_access_probe`
- `task.field_evidence_consumer_ingest.artifact_access_probe`
- `GET /api/o6/consumer/tasks/<task_id>?include=field_evidence` 顶层 alias `artifact_access_probe`
- `GET /api/o6/consumer/tasks/<task_id>?include=artifact_access_probe` 可单独读取 probe section
- `task.field_evidence.field_motion_evidence_packet`
- `task.field_evidence_consumer_ingest.field_motion_evidence_packet`
- `GET /api/o6/consumer/tasks/<task_id>?include=field_evidence` 顶层 alias `field_motion_evidence_packet`
- `task.field_evidence.nav2_goal_execution_evidence`
- `task.field_evidence_consumer_ingest.nav2_goal_execution_evidence`
- `GET /api/o6/consumer/tasks/<task_id>?include=field_evidence` 顶层 alias `nav2_goal_execution_evidence`
- `GET /api/o6/consumer/tasks/<task_id>?include=nav2_goal_execution_evidence` 可单独读取 Nav2 goal evidence section
- `task.field_evidence.delivery_result_evidence`
- `task.field_evidence_consumer_ingest.delivery_result_evidence`
- `GET /api/o6/consumer/tasks/<task_id>?include=field_evidence` 顶层 alias `delivery_result_evidence`
- `GET /api/o6/consumer/tasks/<task_id>?include=delivery_result_evidence` 可单独读取 delivery result evidence section
- `task.field_evidence.route_execution_result_delivery_readiness`
- `task.field_evidence_consumer_ingest.route_execution_result_delivery_readiness`
- `GET /api/o6/consumer/tasks/<task_id>?include=field_evidence` 顶层 alias `route_execution_result_delivery_readiness`
- `GET /api/o6/consumer/tasks/<task_id>?include=route_execution_result_delivery_readiness` 可单独读取结果链 readiness section
- `task.field_evidence.route_delivery_closure_packet`
- `task.field_evidence_consumer_ingest.route_delivery_closure_packet`
- `GET /api/o6/consumer/tasks/<task_id>?include=field_evidence` 顶层 alias `route_delivery_closure_packet`
- `GET /api/o6/consumer/tasks/<task_id>?include=route_delivery_closure_packet` 可单独读取 delivery closure section
- `task.field_evidence.same_task_field_material_packet`
- `task.field_evidence_consumer_ingest.same_task_field_material_packet`
- `GET /api/o6/consumer/tasks/<task_id>?include=field_evidence` 顶层 alias `same_task_field_material_packet`
- `GET /api/o6/consumer/tasks/<task_id>?include=same_task_field_material_packet` 可单独读取 same-task material packet section
- `task.field_evidence.same_task_mission_evidence_gate`
- `task.field_evidence_consumer_ingest.same_task_mission_evidence_gate`
- `GET /api/o6/consumer/tasks/<task_id>?include=field_evidence` 顶层 alias `same_task_mission_evidence_gate`
- `GET /api/o6/consumer/tasks/<task_id>?include=same_task_mission_evidence_gate` 可单独读取 same-task mission gate section
- `task.field_evidence.route_bag_evidence`
- `task.field_evidence_consumer_ingest.route_bag_evidence`
- `GET /api/o6/consumer/tasks/<task_id>?include=field_evidence` 顶层 alias `route_bag_evidence`
- `GET /api/o6/consumer/tasks/<task_id>?include=route_bag_evidence` 可单独读取 route bag evidence section
- `task.field_evidence.route_bag_payload_replay`
- `task.field_evidence_consumer_ingest.route_bag_payload_replay`
- `GET /api/o6/consumer/tasks/<task_id>?include=field_evidence` 顶层 alias `route_bag_payload_replay`
- `GET /api/o6/consumer/tasks/<task_id>?include=route_bag_payload_replay` 可单独读取 payload replay section
- `task.field_evidence.route_bag_semantic_replay`
- `task.field_evidence_consumer_ingest.route_bag_semantic_replay`
- `GET /api/o6/consumer/tasks/<task_id>?include=field_evidence` 顶层 alias `route_bag_semantic_replay`
- `GET /api/o6/consumer/tasks/<task_id>?include=route_bag_semantic_replay` 可单独读取 semantic replay section
- `task.field_evidence.route_bag_full_semantic_decode_matrix`
- `task.field_evidence_consumer_ingest.route_bag_full_semantic_decode_matrix`
- `GET /api/o6/consumer/tasks/<task_id>?include=field_evidence` 顶层 alias `route_bag_full_semantic_decode_matrix`
- `GET /api/o6/consumer/tasks/<task_id>?include=route_bag_full_semantic_decode_matrix` 可单独读取 full semantic decode matrix section
- `task.field_evidence.route_bag_pose_progress_replay`
- `task.field_evidence_consumer_ingest.route_bag_pose_progress_replay`
- `GET /api/o6/consumer/tasks/<task_id>?include=field_evidence` 顶层 alias `route_bag_pose_progress_replay`
- `GET /api/o6/consumer/tasks/<task_id>?include=route_bag_pose_progress_replay` 可单独读取 pose progress replay section
- `task.field_evidence.route_root_seed_gate`
- `task.field_evidence_consumer_ingest.route_root_seed_gate`
- `GET /api/o6/consumer/tasks/<task_id>?include=field_evidence` 顶层 alias `route_root_seed_gate`
- `GET /api/o6/consumer/tasks/<task_id>?include=route_root_seed_gate` 可单独读取 route-root seed gate section

`artifact_media_preflight` 固定为本地/mock 证据边界，供 O7 直接读取，不声明真实媒体可访问。它至少包含：

- `schema=trashbot.o6.artifact_media_preflight.v1`
- `task_id`
- `task_origin=field_evidence_manifest`
- `consumer_section_names=["artifact_media_preflight","route_replay_mvp","labeling_mvp"]`
- `counts.route_ref_count / replay_ref_count / keyframe_ref_count / evidence_ref_count`
- `sample_refs.route_ref / replay_ref / keyframe_ref / evidence_ref`
- `blocked_reasons[]`，至少可表达 route/replay/keyframe 缺口、`local_mock_only`、`not_proven`、`real_media_fetch_blocked`
- `proof_boundary.local_mock=true`
- `proof_boundary.not_proven=true`
- `proof_boundary.real_media_read_executed=false`
- `real_oss_connected=false`

`artifact_access_probe` 固定为本地/mock 证据边界，供 O7/PC 判断“本地 fixture 文件是否可被受限读取”。它至少包含：

- `schema=trashbot.o6.artifact_access_probe.v1`
- `task_id`
- `proof_scope=software_proof_local_mock_artifact_access_probe_only`
- `allowlist_root_configured`
- `allowlist_root_echoed=false`
- `counts.requested_ref_count / readable_ref_count / blocked_ref_count / missing_ref_count`
- `probes[].exists / size_bytes / sha256 / detected_type / blocked_reason / proof_scope`
- `blocked_reasons[]`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`
- `real_oss_connected=false`

`route_root_seed_gate` 固定为本地/mock seed gate，供 O7 判断 route root 是否可作为回放/标注 seed。它至少包含：

- `schema=trashbot.o6.route_root_seed_gate.v1`
- `schema_version=1`
- `task_id`
- `route_root_seed_status=local_mock_route_root_seed_ready|blocked_not_proven`
- `route_bag_required=false`
- `route_bag_present=false|true`
- `route_csv_summary.present / sample_ref / ref_count`
- `manifest_summary.present / sample_ref / schema / status / sample_count`
- `derived_replay_summary.present / generated / frame_count / output_ref`
- `evidence_ref_summary.route_ref_count / replay_ref_count / keyframe_ref_count / evidence_ref_count`
- `blocked_reasons[]`，缺 `route_bag` 时包含 `route_bag_missing_optional`
- `next_required_evidence[]`，缺 `route_bag` 时包含 `route_bag_optional_evidence`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`

`field_motion_evidence_packet` 固定为本地/mock 现场运动证据摘要，供 O7 判断“同一 `task_id` 是否已有可读 motion proof packet，但仍不是 delivery proof”。它至少包含：

- `schema=trashbot.field_motion_evidence_packet.v1`
- `proof_scope=software_proof_field_motion_evidence_packet_only`
- `task_id`
- `status=field_motion_packet_ready_not_delivery_proof|blocked_not_proven`
- `route_summary.frame_count / nonzero_displacement_observed / displacement_m`
- `motion_log_summary.live_motion_evidence_present / evidence_sources[]`
- `route_bag_or_live_nav2_log.present / source / route_bag_present / live_motion_log_present`
- `blocked_reasons[]`
- `next_required_evidence[]`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`

如果 packet 缺失、schema/proof_scope 不匹配，或 source/path/root/token/raw/base64 不安全，O6 只能返回 `blocked_not_proven` 占位摘要；consumer 不得把缺包解释成“route 已实跑完成”。

`nav2_goal_execution_evidence` 固定为本地/software proof Nav2 目标执行摘要，供 O7 判断“同一 `task_id` 是否已有可读 goal/result evidence，但仍不是 delivery proof”。它至少包含：

- `schema=trashbot.nav2_goal_execution_evidence.v1`
- `proof_scope=software_proof_nav2_goal_execution_evidence_only`
- `task_id`
- `status=nav2_goal_execution_ready_not_delivery_proof|nav2_goal_execution_evidence_ready_not_delivery_proof|blocked_not_proven`
- `proof_status=software_proof|not_proven`
- `source`
- `goal_requested / goal_sent / goal_accepted / result_received`
- `goal_result_status / result_status_code`
- `nav2_goal_execution_proven / base_motion_command_nonzero_proven`
- `base_command_mode / requested_base_command_mode`
- `pose_progress_summary / base_feedback_summary / base_command_summary`
- `blocked_reasons[]`
- `next_required_evidence[]`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`

如果 Nav2 evidence 缺失、schema/proof_scope 不匹配，或包含危险 true、path/root/token/raw/base64/unsafe text，O6 只能返回 `blocked_not_proven` 占位摘要；consumer 不得把 goal accepted/result status 解释成真实送达成功或可控动作已打开。

`delivery_result_evidence` 固定为本地/software proof 送达结果摘要，供 O7 判断“同一 `task_id` 是否已有 delivery record/operator confirmation readback，但仍不是 delivery success proof”。它至少包含：

- `schema=trashbot.delivery_result_evidence.v1`
- `proof_scope=software_proof_delivery_result_evidence_only`
- `task_id`
- `status=delivery_result_evidence_ready_not_delivery_proof|delivery_result_ready_not_delivery_proof|ready_not_delivery_proof|blocked_not_proven`（输入允许 `ready_not_delivery_proof`，输出规范化为 `delivery_result_evidence_ready_not_delivery_proof`）
- `source / source_schema`
- `source=cloud_command_terminal_result` 时，`source_schema=trashbot.cloud_command_terminal_result.v1` 必须在 archive detail、consumer detail 和 `include=delivery_result_evidence` 中保留
- `record_present / record_read_ok / record_status`
- `delivery_result_claimed / operator_confirmation_present`
- `dropoff_confirmation_type`
- `completed_at_utc`
- `linked_nav2_goal_execution_proven`
- `blocked_reasons[]`
- `next_required_evidence[]`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`

如果 delivery result evidence 缺失、schema/proof_scope 不匹配，或包含危险 true、path/root/token/raw/base64/credential URL/unsafe text，O6 只能返回 `blocked_not_proven` 占位摘要；consumer 不得把 operator confirmation、record_status 或 completed_at_utc 解释成真实送达成功、真实用户确认完成或控制权限已打开。

`route_execution_result_delivery_readiness` 固定为本地/software proof 结果链 readiness 摘要，供 O7 判断“同一 `task_id` 是否已有 route execution result、delivery result readiness 和 operator confirmation readiness 的统一读模型，但仍不是 delivery success proof”。它至少包含：

- `schema=trashbot.o6.route_execution_result_delivery_readiness.v1`
- `source_schema=trashbot.route_execution_result_delivery_readiness.v1`
- `proof_scope=software_proof_route_execution_result_delivery_readiness_only`
- `task_id`
- `status=route_execution_result_delivery_readiness_ready_not_delivery_proof|blocked_not_proven`
- `source / task_id_source`
- `route_execution_result_status / route_execution_result_source / route_execution_result_ready`
- `route_execution_success=false`
- `delivery_result_readiness_status / delivery_result_readiness_source / delivery_result_readiness_ready`
- `operator_confirmation_readiness_status / operator_confirmation_readiness_source / operator_confirmation_readiness_ready`
- `linked_nav2_goal_execution_proven`
- `linked_delivery_result_claimed`
- `linked_operator_confirmation_present`
- `blocked_reasons[]`
- `next_required_evidence[]`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`

如果结果链 readiness 缺失、schema/proof_scope 不匹配，或包含危险 true、unsafe path/topic/url/token/raw/base64/text、缺必填字段，O6 只能返回 `blocked_not_proven` 占位摘要；consumer 不得把任何 `ready` 解释成真实 route execution 成功、真实 delivery result、真实 operator confirmation 或可控动作已打开。

`same_task_mission_evidence_gate` 固定为本地/software proof 同 task mission gate 摘要，供 O7 判断“同一 `task_id` 是否已有 terminal result、route execution readiness、delivery closure 和 pose progress 的一致读模型，但仍不是 delivery success proof”。它至少包含：

- `schema=trashbot.o6.same_task_mission_evidence_gate.v1`
- `source_schema=trashbot.same_task_mission_evidence_gate.v1`
- `proof_scope=software_proof_same_task_mission_evidence_gate_only`
- `task_id`
- `status=same_task_mission_gate_ready_not_success_proof|blocked_not_proven`
- `source`
- `terminal_refs[]`（只回显 basename）
- `terminal_ref_count`
- `mission_artifact_delta.same_task_id_consumed | cloud_terminal_result_source_consumed | route_execution_readiness_consumed | route_delivery_closure_consumed | nonzero_pose_progress_consumed | live_or_field_command_executed`
- `same_task_id_consumed`
- `live_or_field_command_executed`
- `support_only_reason`
- `okr_credit_allowed`
- `linked_readiness_flags.delivery_result_evidence_ready`
- `linked_readiness_flags.cloud_terminal_result_ready`
- `linked_readiness_flags.route_execution_result_delivery_readiness_ready`
- `linked_readiness_flags.route_delivery_closure_packet_ready`
- `linked_readiness_flags.route_bag_pose_progress_replay_ready`
- `linked_readiness_flags.same_task_id_match`
- `blocked_reasons[]`
- `next_required_evidence[]`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`
- `connects_cloud_production=false`

如果 same-task gate 缺失、schema/proof_scope 不匹配、task_id 与 archive task 不一致，或包含危险 true、unsafe text、raw/base64、绝对路径、credential URL、token，O6 只能返回 `blocked_not_proven` 占位摘要；consumer 不得把 `same_task_mission_gate_ready_not_success_proof` 解释成真实 production cloud、真实 route execution、真实 operator confirmation、真实机器人运动或 delivery success。

`route_bag_evidence` 固定为本地/software proof route bag DB3 摘要，供 O7 判断“同一 `task_id` 是否已有可读 bag metadata/topic/message/timestamp 摘要，但仍不是 route execution proof”。它至少包含：

- `schema=trashbot.o6.route_bag_evidence.v1`
- `source_schema=trashbot.route_bag_evidence.v1`
- `proof_scope=software_proof_route_bag_evidence_intake_only`
- `task_id`
- `status=ready_not_route_execution_proof|route_bag_evidence_ready_not_route_execution_proof|blocked_not_proven`
- `source / source_label / task_id_source`
- `metadata_present / db3_present / db3_read_ok`
- `db3_size_bytes / db3_sha256_prefix`
- `topic_count / message_count`
- `timestamp_first_ns / timestamp_last_ns`
- `sample_topic_names[]`（只保留短 topic label，拒绝 `/cmd_vel`）
- `blocked_reasons[]`
- `next_required_evidence[]`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`

如果 route bag evidence 缺失、schema/proof_scope 不匹配，或包含危险 true、path/root/token/raw/base64/credential URL/unsafe text，O6 只能返回 `blocked_not_proven` 占位摘要；consumer 不得把 DB3 可读、topic/message 计数或 timestamp 范围解释成真实 live Nav2 run、路线执行成功或 delivery success。

失败时返回 `400`，且不得写入 store：

- bad JSON、非对象 body、schema 不匹配
- 缺少 `field_evidence_manifest` / `manifest_gate` / `run_id` / `artifacts`
- `gate_pass=false` 或 `manifest_gate.status` 不是 `gated`
- 任意 `safe_to_control=true`、`delivery_success=true`、`primary_actions_enabled=true`
- 任意 `connects_cloud_production=true`、`robot_control_executed=true`、`real_cloud_db_connected=true`、`real_oss_connected=true`
- 可选数组不是小数组，或其中包含 unsafe / raw content
- artifact 缺 `sha256`、`size_bytes<=0`、必需 artifact 未 present 或带 `reason`
- payload 含 `Authorization` / `Bearer` / token / password / secret / `/cmd_vel` / 串口路径 / `baudrate` / `traceback`

## O6 Consumer Read API

`GET /api/o6/consumer/tasks` 和 `GET /api/o6/consumer/tasks/<task_id>` 是只读聚合面。它们继续复用 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE` 的同一个 file-backed local/mock store，把已有 archive task、events、evidence refs、field evidence manifest、labels、`model_inference.*` events 和 tunnel latest known snapshot 整成给 PC/手机共享的读模型；它们不替代既有 `/api/o6/archive/*` 和 `/api/o6/tunnel/*`，也不连接真实云 DB、真实 OSS、真实手机、真实公网、真实机器人控制或真实交付成功。

### 固定顶层边界

- `schema=trashbot.o6.consumer_read.v1`
- `source=local_mock_consumer_read_model`
- `proof_status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `real_cloud_db_connected=false`
- `real_oss_connected=false`
- `connects_cloud_production=false`
- `robot_control_executed=false`

### GET /api/o6/consumer/tasks

作用：

- 返回任务卡片级聚合摘要
- 给 PC/手机共享同一份任务列表字段，不要求消费方自己 join task/events/evidence/labels/tunnel

支持 query：

- `robot_id`
- `task_id`
- `date=YYYY-MM-DD`（按 task `started_at_ms` 的 UTC 日期过滤）
- `status=all|completed_mock|failed_mock|in_progress_mock|unknown_not_proven`
- `limit`（默认 50，最大 200；非法或过大直接 fail-closed）
- `before_started_at_ms`
- `view=default|summary`
- `include=trajectory,events,evidence,field_evidence,artifact_access_probe,nav2_goal_execution_evidence,delivery_result_evidence,route_execution_result_delivery_readiness,route_delivery_closure_packet,same_task_field_material_packet,same_task_mission_evidence_gate,route_bag_evidence,route_bag_payload_replay,route_bag_semantic_replay,route_bag_full_semantic_decode_matrix,offline_artifact_seed_smoke,route_root_seed_gate,labeling,inference,tunnel`（白名单外直接 fail-closed）
- `include=route_delivery_closure_packet`：单独返回 delivery closure 摘要；仍固定 `safe_to_control=false`、`delivery_success=false`
- `include=same_task_field_material_packet`：单独返回 same-task 材料包摘要；ready 仍不是真实 delivery success proof
- `include=same_task_mission_evidence_gate`：单独返回 same-task mission gate 摘要；ready 仍不是真实 delivery success proof

列表 `task_list.tasks[]` 至少包含：

- `task_id`
- `robot_id`
- `started_at_ms`
- `finished_at_ms`
- `task_status_summary`
- `latest_event_at_ms`
- `trajectory_frame_count`
- `event_count`
- `evidence_count`
- `task_origin`
- `field_evidence_status`
- `labeling_status`
- `inference_status`
- `tunnel_status_summary`
- `selected`

约束：

- 列表按 `started_at_ms` 倒序返回
- `selected` 只是 store 中最后一次 upsert task 的单选标记，不等于前端用户选择状态
- `labeling_status` 沿用底层 `pending|partial|labeled` 语义，不把“没有 labels”改写成别的真值
- `tunnel_status_summary` 是 robot 维度 latest known snapshot 的摘要，不是 task 时间对齐历史

### GET /api/o6/consumer/tasks/<task_id>

作用：

- 返回单任务聚合详情
- 默认面向 PC；手机可走 `view=summary`

支持 query：

- `robot_id`
- `view=default|summary`
- `include=trajectory,events,evidence,field_evidence,artifact_access_probe,nav2_goal_execution_evidence,delivery_result_evidence,route_execution_result_delivery_readiness,route_delivery_closure_packet,same_task_field_material_packet,same_task_mission_evidence_gate,route_bag_evidence,route_bag_payload_replay,route_bag_semantic_replay,route_bag_full_semantic_decode_matrix,offline_artifact_seed_smoke,route_root_seed_gate,labeling,inference,tunnel`

固定 section：

- `task_summary`
- `proof_boundary`

按 `include` 返回的 section：

- `trajectory`
- `events`
- `evidence`
- `field_evidence`
- `route_execution_result_delivery_readiness`
- `route_delivery_closure_packet`
- `same_task_field_material_packet`
- `same_task_mission_evidence_gate`
- `route_bag_evidence`
- `route_bag_full_semantic_decode_matrix`
- `offline_artifact_seed_smoke`
- `route_root_seed_gate`
- `labeling`
- `inference`
- `tunnel_status`

聚合要求：

- `events` 继续经过 `_o6_cloud_archive_event_payload()`，必须保留 `model_inference.*` 的 `inference_id/input_id/result_type/result_value/confidence/not_proven`
- `evidence` 继续经过 `_o6_cloud_archive_evidence_ref_payload()`，兼容旧 string 和新 dict 摘要
- `field_evidence` 只返回 manifest gate、artifact basename 摘要、derived replay 计数和固定 fail-closed 边界
- `artifact_media_preflight` 是 `field_evidence` 的媒体预检小视图；它只返回计数、样本 ref、blocked reasons 和 `local_mock/not_proven` 边界，不读取真实 OSS/CDN，也不回显绝对路径、token、base64、raw media 或控制字段
- `artifact_access_probe` 是 `field_evidence` / artifact bundle 的本地 fixture 小文件只读探测；只有显式 allowlist root 内的小文件会计算 sha256，所有危险 ref 或缺 root 情况都返回 blocked reason
- `field_motion_evidence_packet` 是 `field_evidence` / artifact bundle 的现场运动证据摘要；缺包时固定 `blocked_not_proven`，危险字段和路径/root/token/raw/base64 不回显
- `delivery_result_evidence` 是 `field_evidence` / artifact bundle 的送达结果摘要；它只返回 record/operator confirmation 的白名单字段和 false 安全旗标，坏 schema 或危险文本一律降级为 `blocked_not_proven`
- `route_execution_result_delivery_readiness` 是 `field_evidence` / artifact bundle 的结果链 readiness 摘要；它只返回 route execution result、delivery readiness、operator confirmation readiness、三类 linked flags 和 false 安全旗标，坏 schema、危险 true、unsafe path/topic/url/token/raw/base64/text 或缺必填字段一律降级为 `blocked_not_proven`
- `route_delivery_closure_packet` 是 `field_evidence` / artifact bundle 的 delivery closure 摘要；它只返回 closure status、五个 linked readiness flags、blocked reasons、next required evidence 和 false 安全旗标，坏 schema、危险 true、unsafe path/topic/url/token/raw/base64/text 或缺关键 linked flag 一律降级为 `blocked_not_proven`
- `same_task_field_material_packet` 是 `field_evidence` / artifact bundle 的 same-task 材料包摘要；它返回 materials presence、`map_yaml` optional flag、safe counts、顶层 basename list `sample_refs`、按材料分组的 `material_sample_refs`、same-task 消费标记、blocked reasons、next required evidence 和 false 安全旗标，坏 schema、proof scope mismatch、task mismatch、危险 true、unsafe text/raw/base64/绝对路径/URL/token 一律降级为 `blocked_not_proven`
- `same_task_mission_evidence_gate` 是 `field_evidence` / artifact bundle 的同 task mission gate 摘要；它只返回 terminal basename refs、mission artifact delta、linked readiness flags、blocked reasons、next required evidence 和 false 安全旗标，坏 schema、proof scope mismatch、task mismatch、危险 true、unsafe text/raw/base64/绝对路径/credential URL/token 一律降级为 `blocked_not_proven`
- `route_bag_evidence` 是 `field_evidence` / artifact bundle 的 DB3 摘要；它只返回 metadata/topic/message/timestamp 白名单字段和 false 安全旗标，坏 schema、坏 proof_scope、危险 true 或危险文本一律降级为 `blocked_not_proven`
- `route_bag_payload_replay` 是 `field_evidence` / artifact bundle 的 payload replay 摘要；它只返回 topic/message/timestamp、payload size 统计、payload hash 前缀样本、blocked reasons 和 false 安全旗标，坏 schema、坏 proof_scope、危险 true、unsafe topic 或缺失/负数 payload 统计一律降级为 `blocked_not_proven`
- `route_bag_semantic_replay` 是 `field_evidence` / artifact bundle 的语义 replay 摘要；它只返回 topic/message/timestamp、LaserScan/Image/TF 白名单统计、decode counts、blocked reasons 和 false 安全旗标，坏 schema、坏 proof_scope、危险 true、unsafe text/topic、缺必填字段或任何 raw/base64/path/token/credential URL 一律降级为 `blocked_not_proven`
- `route_bag_full_semantic_decode_matrix` 是 `field_evidence` / artifact bundle 的全量语义解码覆盖矩阵摘要；它只返回 counts、coverage ratio、safe topic/type matrix、`decoder_name` / `decoder`、blocked reasons、next required evidence 和 false safety fields，`diagnostic_msgs.msg.DiagnosticArray` decoded item 必须能保留 `decoder_name=decode_diagnostic_array_payload` 与计数，坏 schema、坏 proof_scope、危险 true、unsafe topic/text/path/url/token/raw/base64、缺必填计数或负数一律降级为 `blocked_not_proven`
- `route_bag_pose_progress_replay` 是 `field_evidence` / artifact bundle 的位姿进度 replay 摘要；它只返回 topic/message/timestamp、pose sample/decode counts、topic types、frame pairs、time span、start/end pose、displacement 和 false 安全旗标，坏 schema、坏 proof_scope、危险 true、unsafe frame/topic、缺必填字段或任何 raw/base64/path/token/credential URL 一律降级为 `blocked_not_proven`
- `offline_artifact_seed_smoke` 是 `field_evidence` / artifact bundle 的离线种子摘要；它只返回 counts、sample basename refs、sha256 prefix、blocked reasons、next required evidence 和全 false 安全旗标，不证明真实 production cloud、OSS/CDN、真实媒体播放、真实机器人运动或 delivery success
- `route_root_seed_gate` 是 `field_evidence` / artifact bundle 的 route-root seed gate 摘要；它把 `route_bag` 作为 optional evidence，缺失时保持 `route_bag_required=false` / `route_bag_present=false`，并只返回可读 blocked reason 与 next evidence
- 当 `field_evidence` 存在时，detail 还会附带 `field_evidence_manifest` 和 `field_evidence_consumer_ingest` 作为显式读回 alias；两者继续保持所有危险字段为 false
- 当 `field_evidence` 存在时，detail 还会附带顶层 alias `artifact_media_preflight`，供 O7 直接消费固定 section 名
- `labeling` 返回 task 级状态和限量 item summary
- `inference` 只从 `model_inference.*` timeline 摘要抽取，不新建第二套 store
- `tunnel_status.latest_known_status` 明确是 latest known robot snapshot，并附带 `temporal_alignment=latest_known_robot_snapshot_not_task_aligned`

### fail-closed 规则（Consumer Read）

以下场景返回 4xx 或结构化 blocked/not_proven，而不是伪造成功态：

- `task_id` 不存在
- `robot_id` 与 task 不匹配
- `view` 未知
- `include` 含未知 section
- `limit` 非法或超过 200
- query 含 `Authorization` / `Bearer` / token / password / secret / `/cmd_vel` / 串口路径 / `baudrate` / `traceback`
- 缺 tunnel 时返回 `tunnel_status.status=blocked_not_proven`
- 没有 labels 时返回 `labeling_status=pending` + `label_count=0`
- 没有 inference event 但 task 有 events 时返回 `inference.status=absent`
- summary 视图和 `include=` 必须真的裁剪未请求的重 section

## Storage

- Store 由 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE` 注入
- 未设置时回落到系统临时目录下的默认文件
- 这是 file-backed 本地开发/测试存储，不是生产 DB

## Request Contract

`POST /api/o6/archive/tasks` 接受小型 JSON object，必须包含：

- `robot_id`
- `task_id`
- `started_at_ms`
- `finished_at_ms`
- `trajectory_frames[]`
- `events[]`

可选字段：

- `evidence_refs[]`

`trajectory_frames[]`、`events[]` 和 `evidence_refs[]` 都只允许小数组。当前实现上限分别是 64、64 和 64。超过上限直接 fail closed。

## Response Contract（Archive tasks）

固定顶层字段：

- `schema=trashbot.o6.cloud_archive.v1`
- `source=local_mock_archive`
- `proof_status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `pc_only=true`
- `real_cloud_db_connected=false`
- `real_oss_connected=false`
- `connects_cloud_production=false`
- `robot_control_executed=false`

任务详情只暴露白名单字段：

- `task_id`
- `robot_id`
- `started_at_ms`
- `finished_at_ms`
- `trajectory_frames[]`
- `events[]`
- `evidence_refs[]`
- `created_at_ms`
- `updated_at_ms`
- `selected`

列表响应还包含：

- `task_list.total_tasks`
- `task_list.tasks[]`
- `selected_task`
- `latest_task`
- `summary`

## Duplicate Semantics

同一 `task_id` 采用 idempotent upsert，不返回 `409 conflict`。再次 `POST` 同一 `task_id` 会覆盖该任务的安全摘要并返回：

- 新建：`201`
- 更新：`200`
- `write_status=created | updated`
 - `duplicate=true | false`

## O6 事件与证据引用本地 mock contract

`POST /api/o6/archive/events`、`GET /api/o6/archive/events`、`POST /api/o6/archive/evidence`、`GET /api/o6/archive/evidence` 是 O6-KR2/O6-KR3 的任务内增量存档入口。它们复用 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE` 和既有 file-backed local/mock store，只允许附着到已存在 task，不会隐式创建 task。

### POST /api/o6/archive/events

请求必须包含：

- `robot_id`
- `task_id`
- `events[]`：1 到 64 条

每条 event 必须包含：

- `event_id`：task 内幂等键，长度 1 到 128
- `event_type`：必须是白名单类型
- `occurred_at_ms`：必须落在 task `started_at_ms..finished_at_ms` 时间窗内

可选字段：

- `pose`：仅保留 `x_m / y_m / yaw_rad / floor_id`
- `summary`：最多 512 字符
- `severity=info|warning|error`
- `evidence_refs[]`：每条 event 最多 8 个引用，回包只返回 basename 摘要
- `metadata`：小型 object，深度最多 3，序列化后最多 8 KiB

event_type 白名单：

- `perception.detected_object`
- `route.frame`
- `route.pose`
- `elevator.door_state`
- `elevator.floor_evidence`
- `task.failure`
- `task.recovery`
- `operator.note`

成功响应固定：

- `schema=trashbot.o6.archive_events.v1`
- `schema_version=1`
- `source=local_mock_event_archive`
- `proof_status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `pc_only=true`
- `real_cloud_db_connected=false`
- `real_oss_connected=false`
- `connects_cloud_production=false`
- `robot_control_executed=false`
- `archive_event_written=true`

幂等键是 `task_id + event_id`。全新批次返回 `201/write_status=created/duplicate=false`；命中任一已有 `event_id` 返回 `200/write_status=updated/duplicate=true`，并在 `event_summary.created_count/updated_count` 给出混合批次摘要。

### GET /api/o6/archive/events

支持 query：

- `robot_id`
- `task_id`
- `event_type`
- `from_ms`
- `to_ms`
- `limit`：默认 50，最大 200

返回：

- `schema=trashbot.o6.archive_events.v1`
- `source=local_mock_event_archive`
- `query`
- `events[]`
- `event_summary`

`events[]` 只返回白名单字段：`event_id/event_type/occurred_at_ms/source/pose/summary/severity/evidence_refs/metadata/created_at_ms/updated_at_ms`，并按 `occurred_at_ms` 升序排列。非法 `limit`、未知 `event_type`、非法时间窗、`unknown_task` 或 `unauthorized_task` 都 fail-closed。

### POST /api/o6/archive/evidence

请求必须包含：

- `robot_id`
- `task_id`
- `evidence_refs[]`：1 到 64 条

每条 evidence ref 必须包含：

- `evidence_id`：task 内幂等键，长度 1 到 128
- `evidence_type`：必须是白名单类型
- `evidence_ref`：对象引用或 mock ref；服务端只保存 basename 摘要，不保存图片/视频/音频原始内容
- `captured_at_ms`：必须落在 task 时间窗内

可选字段：

- `event_id`
- `content_type`
- `size_bytes`
- `checksum`
- `metadata`：小型 object，深度最多 3，序列化后最多 8 KiB

evidence_type 白名单：

- `camera_frame`
- `snapshot`
- `route_frame`
- `elevator_frame`
- `failure_snapshot`
- `audio_clip`
- `log_excerpt`

成功响应固定：

- `schema=trashbot.o6.archive_evidence.v1`
- `schema_version=1`
- `source=local_mock_evidence_archive`
- `proof_status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `pc_only=true`
- `real_cloud_db_connected=false`
- `real_oss_connected=false`
- `real_oss_upload_success=false`
- `connects_cloud_production=false`
- `robot_control_executed=false`
- `archive_evidence_written=true`

幂等键是 `task_id + evidence_id`。全新批次返回 `201/write_status=created/duplicate=false`；命中任一已有 `evidence_id` 返回 `200/write_status=updated/duplicate=true`。

### GET /api/o6/archive/evidence

支持 query：

- `robot_id`
- `task_id`
- `evidence_type`
- `event_id`
- `limit`：默认 50，最大 200

返回：

- `schema=trashbot.o6.archive_evidence.v1`
- `source=local_mock_evidence_archive`
- `query`
- `evidence_refs[]`
- `evidence_summary`

`evidence_refs[]` 只返回白名单字段：`evidence_id/evidence_type/evidence_ref/captured_at_ms/event_id/content_type/size_bytes/checksum/metadata/created_at_ms/updated_at_ms`。它不返回 credential URL、token、base64、原始图片、原始音频、原始视频、完整日志或完整模型响应。写入后 `GET /api/o6/archive/tasks/<task_id>` 仍能在兼容 `events[]` / `evidence_refs[]` 中读到对应摘要。

### fail-closed 规则（Events/Evidence）

以下场景返回 4xx，且不得写入任何 event/evidence：

- bad JSON、非对象 JSON、空 body
- 缺少 `robot_id/task_id/events/evidence_refs` 或必填 item 字段
- `events[]` / `evidence_refs[]` 非数组、为空或超过 64
- `unknown_task`
- `unauthorized_task`
- 非白名单 `event_type` / `evidence_type`
- `occurred_at_ms` / `captured_at_ms` 越过 task 时间窗
- `metadata` 非 object、超深、超长或含 unsafe content
- payload 含 `Authorization`、`Bearer`、`token`、`password`、`secret`、`private_key`、credential URL、`/cmd_vel`、串口路径、`baudrate`、`traceback`
- payload 含 base64、原始图片/视频/音频、完整日志、完整模型响应或 raw content
- payload 声明真实能力，例如 `success=true`、`production_ready=true`、`cloud_db_connected=true`、`oss_uploaded=true`、`robot_control_executed=true`、`delivery_success=true`

## O6 local/mock 模型推理 contract

`POST /api/o6/archive/inference` 是 O6-KR5 的 local/mock 模型推理写入口。它复用 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE` 和 `FileBackedO6CloudArchiveStore`，只允许把推理结果写入已存在 archive task 的 `events[]`，不创建孤儿 inference record。

### Request Contract（POST）

必填字段：

- `robot_id`
- `task_id`
- `inference_id`
- `model_family`
- `requested_outputs`
- `inputs`

`requested_outputs[]` 当前上限是 8，但首批只允许：

- `elevator_door_state`
- `floor_recognition`

`inputs[]` 当前上限是 16。每条 input 必须包含：

- `input_id`
- `input_type`：`image_ref | frame_ref | snapshot_ref | metadata_only`
- `evidence_ref`
- `captured_at_ms`
- `metadata`：可选小型 JSON object 摘要，不能包含原始图片、凭证、完整模型返回体或真实能力声明

### Response Contract（POST）

所有成功响应固定：

- `schema=trashbot.o6.model_inference.v1`
- `schema_version=1`
- `source=local_mock_inference`
- `proof_status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `pc_only=true`
- `connects_cloud_production=false`
- `robot_control_executed=false`
- `real_gpu_model_connected=false`
- `real_external_model_api_connected=false`
- `real_model_inference_success=false`
- `real_floor_recognition_proven=false`
- `real_elevator_door_state_proven=false`
- `archive_event_written=true`

成功响应还包含：

- `write_status`：`created | updated`
- `duplicate`：首次写入 `false`，命中任一既有幂等键时 `true`
- `task_id`
- `robot_id`
- `inference_id`
- `results[]`
- `result_summary`
- `not_proven`

### Archive event contract

每个 `input + requested_output` 组合写成一条 task event：

- `event_type=model_inference.elevator_door_state`
- `event_type=model_inference.floor_recognition`

事件白名单字段包含：

- `event_id`
- `event_type`
- `timestamp_ms`
- `occurred_at_ms`
- `source=local_mock_inference`
- `inference_id`
- `input_id`
- `input_type`
- `model_family`
- `result_type`
- `result_value`
- `confidence`
- `evidence_ref`
- `metadata`
- `not_proven`

当前 deterministic local/mock stub 固定返回 `result_value=unknown` 与 `confidence=0.0`。这只证明 API、幂等、事件落库和读取链路，不证明真实 GPU、真实外部模型、真实楼层识别或真实电梯门状态。

### Duplicate Semantics（Inference）

幂等键：`task_id + inference_id + input_id + result_type`。

- 全新结果：`201` + `write_status=created` + `duplicate=false`
- 已有结果：`200` + `write_status=updated` + `duplicate=true`
- 混合批次：只要命中任一旧键即返回 `updated`，`result_summary.created_count/updated_count` 给出批内摘要

### Fail-Closed / 安全告警（Inference）

以下场景返回 fail-closed，且不得写入 `events[]`：

- 坏 JSON / 非对象 JSON / 空 body
- 缺少 `robot_id`、`task_id`、`inference_id`、`model_family`、`requested_outputs[]`、`inputs[]`
- `requested_outputs[]` 或 `inputs[]` 不是数组、为空或超过上限
- 未知 output 或 unsupported `input_type`
- `unknown_task`
- `unauthorized_task`
- `captured_at_ms` 不在 task `started_at_ms..finished_at_ms` 窗口内
- `metadata` 非小型 object 或包含 unsafe content
- unsafe content（`Authorization` / `Bearer` / token / `/cmd_vel` / 串口路径 / `baudrate` / `traceback` / 凭证 URL）
- 真实能力声明（如 `success=true`、`production_ready=true`、`gpu_connected=true`、`external_model_connected=true`、`floor_recognition_proven=true`、`elevator_door_state_proven=true`、`robot_control_executed=true`）

## O6 local/mock tunnel online status contract

`POST /api/o6/tunnel/heartbeat`、`GET /api/o6/tunnel/robots`、`GET /api/o6/tunnel/robots/<robot_id>` 为 O6-KR1 增补本地/文件化隧道观测入口，和既有 archive/labels/inference 共用同一套 `TRASHBOT_O6_CLOUD_ARCHIVE_STATE`。

### POST /api/o6/tunnel/heartbeat

必填字段：

- `robot_id`
- `tunnel_provider`（`frp` / `wireguard` / `ngrok` / `mock`）

可选字段：

- `endpoint`：可选上报 endpoint，必须脱敏保存/返回，不回显 credential token/secret/password/private_key/Authorization
- `observed_at`：可选，支持整数毫秒或 ISO8601；缺省用服务端当前毫秒
- `ttl_seconds`：可选，默认 `300`，范围 `60~86400`
- `metadata`：可选，仅允许 `ip_family / network_type / region / notes`

失败场景（fail-closed）：

- bad JSON、bad body
- 缺字段
- `tunnel_provider` 不在白名单
- `metadata` 非 object、超字段长度、非法 key
- `endpoint`/`metadata` 含 unsafe content（包含 `Authorization` / `Bearer` / token / `/cmd_vel` / 串口路径 / `baudrate` / `traceback` / credential URL）

成功响应固定：

- `schema=trashbot.o6.tunnel_status.v1`
- `schema_version=1`
- `source=local_mock_tunnel_status`
- `proof_status=not_proven`
- `real_tunnel_connected=false`
- `real_4g_connected=false`
- `connects_cloud_production=false`
- `robot_control_executed=false`
- `safe_to_control=false`
- `robot_id`
- `status`
- `last_seen_at_ms`
- `ttl_seconds`
- `observed_at_ms`
- `endpoint`
- `tunnel_provider`
- `metadata`

### GET /api/o6/tunnel/robots

查询参数：

- `status=online|offline|all`（默认 `all`）
- `provider=<frp|wireguard|ngrok|mock>`（可选）
- `limit`（默认 50，最大 100）

响应是按 `last_seen_at_ms` 倒序的列表，返回：

- `robots[]`
- `total_robots`
- `query`（`status`/`provider`/`limit`）
- `updated_at_ms`

### GET /api/o6/tunnel/robots/<robot_id>

- 存在则返回该 robot 的单机快照（同上字段）
- 不存在返回 `404 + error.code=not_found`

### 安全边界

## O6 标注本地 mock contract

`POST /api/o6/archive/labels` 及其查询接口是 O6 标注回路的 local/mock 入口，仍不连接真实生产云、OSS 或训练服务，不会下发控制。

### Request Contract（POST）

- `robot_id`
- `task_id`
- `labels`：数组，长度限制 `<= O6_CLOUD_LABELING_MAX_LABELS`（当前 64）

`labels[]` 中每条必须包含：

- `item_id`
- `item_type`
- `label_type`
- `value`

可选字段：

- `confidence`
- `annotator_id`
- `evidence_ref`
- `notes`

### Request constraints

- `task_id` 必须已经存在于 local O6 archive store 中。
- `robot_id` 必须与目标 task 的 `robot_id` 完全一致。
- `labels` 必须为数组，且不得空。
- 任何字段长度仍按 O6 local/mock 标注常量上限限制：
  - `item_id <= 80`
  - `item_type <= 120`
  - `label_type <= 120`
  - `value <= 240`
  - `annotator_id / evidence_ref / notes <= 512`

### Response Contract（POST/List/Detail）

固定成功字段：

- `schema=trashbot.o6.archive_labeling.v1`
- `schema_version=1`
- `source=local_mock_labeling`
- `proof_status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `pc_only=true`
- `submit_enabled=false`
- `rollback_enabled=false`
- `dataset_export_available=false`
- `real_cloud_db_connected=false`
- `real_oss_connected=false`
- `real_annotation_api_connected=false`
- `real_dataset_export_connected=false`
- `cloud_write_executed=false`
- `connects_cloud_production=false`
- `robot_control_executed=false`
- `command_dispatch_enabled=false`
- `manual_control_enabled=false`
- `navigate_goal_enabled=false`
- `keyboard_control_enabled=false`
- `not_proven` 至少包含
  - `real_annotation_submit_success`
  - `real_annotation_review_api`
  - `real_dataset_export`
  - `real_o7_labeling_production`

成功响应还带：

- `write_status`：`created | updated`
- `duplicate`：首次写入 `false`，存在至少一个幂等键时 `true`
- `local_mock_annotation_submit_written=true`：仅表示本地/mock file-backed store 已接收并保存安全 label 摘要，不代表真实标注 API。
- `submit_receipt.status=local_mock_annotation_written`
- `submit_receipt.receipt_id`：由 `task_id`、label 幂等键和最近更新时间派生的本地 receipt id。
- `submit_receipt.task_id`
- `submit_receipt.robot_id`
- `submit_receipt.label_count`
- `submit_receipt.item_count`
- `submit_receipt.safe_to_control=false`
- `submit_receipt.delivery_success=false`
- `submit_receipt.primary_actions_enabled=false`
- `submit_receipt.robot_control_executed=false`
- `submit_receipt.connects_cloud_production=false`
- `submit_receipt.real_annotation_api_connected=false`
- `submit_receipt.real_dataset_export_connected=false`
- `submit_receipt.submit_enabled=false`
- `submit_receipt.dataset_export_available=false`
- `dataset_export`：task 级 export 摘要，labels 存在时 `dataset_export.export_status=local_mock_export_ready`，无 labels 时 `blocked_not_proven`。
- `local_mock_dataset_export_ready=true|false`
- `local_mock_dataset_export_written=true|false`：仅表示 API 可派生 local/mock export 响应，不代表真实训练集文件已生产。
- `label_summary`
- `itemized_labels[]`（detail 接口）
- `task_summary[]`（list 接口）

重复语义（幂等）：`task_id + item_id + label_type` 为幂等键。

- 首次提交该 task 的 label 组合 → `201` + `write_status=created` + `duplicate=false`
- 重复提交命中幂等键 → `200` + `write_status=updated` + `duplicate=true`

### Labeling List Contract（GET /api/o6/archive/labels）

`task_summary` 仅返回任务级摘要，不原样回显完整 `labels`。支持：

- `status=pending|labeled|all`（默认 `all`）
- `limit`（正整数，默认 50，上限 100）

响应字段包含：

- `status`：`local_mock_labeling_ready | blocked_not_proven`
- `status_filter`
- `limit`
- `task_summary[]`（`task_id/robot_id/task_status/pending_item_count/labeled_item_count/latest_label_updated_at_ms/itemized_label_count/selected`）
- `label_summary.task_count`
- `label_summary.pending_task_count`
- `label_summary.partial_task_count`
- `label_summary.labeled_task_count`
- `blocked_reasons`

### Labeling Detail Contract（GET /api/o6/archive/labels/<task_id>）

- `task_id/robot_id`
- `task_status`
- `local_mock_annotation_submit_written`
- `submit_receipt`
- `dataset_export`
- `local_mock_dataset_export_ready`
- `local_mock_dataset_export_written`
- `itemized_labels[]`
- `label_summary`

`task_status` 的状态来源于 `labels` 完整度（`pending | partial | labeled | blocked`）。

### Task-level Dataset Export Contract（GET /api/o6/archive/labels/<task_id>/export?format=jsonl）

该接口从已存在 task 的 `labels[]` 派生安全 manifest 和限量 `sample_rows[]`。它不读取原始图片/视频/音频/rosbag，不连接 OSS/DB，不返回绝对路径、credential URL、base64、串口路径、`/cmd_vel` 或任何真实控制字段。

支持 query：

- `format=jsonl`：当前唯一支持格式；缺省时按 `jsonl` 处理。
- `robot_id`：可选；传入时必须与 task 的 `robot_id` 完全一致。

成功响应固定：

- `schema=trashbot.o6.annotation_dataset_export.v1`
- `schema_version=1`
- `source=local_mock_labeling_export`
- `proof_status=not_proven`
- `status=local_mock_export_ready`
- `export_status=local_mock_export_ready`
- `task_id`
- `robot_id`
- `format=jsonl`
- `export_id`
- `label_count`
- `item_count`
- `local_mock_dataset_export_ready=true`
- `local_mock_dataset_export_written=true`
- `dataset_export_available=false`
- `real_dataset_export_connected=false`
- `real_annotation_api_connected=false`
- `connects_cloud_production=false`
- `robot_control_executed=false`
- `submit_receipt`
- `export_manifest`
- `sample_rows[]`

`export_manifest` 只包含本地/mock 摘要字段，例如 `export_id/export_ref/task_id/robot_id/format/row_count/sample_row_count/sample_policy/latest_label_updated_at_ms`，并固定声明：

- `contains_raw_media=false`
- `contains_base64=false`
- `contains_credentials=false`
- `contains_absolute_paths=false`
- `connects_cloud_production=false`
- `robot_control_executed=false`

`sample_rows[]` 最多返回 5 条白名单行，字段为：

- `row_index`
- `task_id`
- `robot_id`
- `item_id`
- `item_type`
- `label_type`
- `value`
- `confidence`
- `annotator_id`
- `evidence_ref`（仅 basename 摘要）
- `notes`
- `updated_at_ms`

无 labels 时返回 `409` + `export_status=blocked_not_proven`，并保持 `dataset_export_available=false`、`local_mock_dataset_export_ready=false`、`sample_rows=[]`。这不是服务端异常，只表示该 task 尚无可导出的 local/mock 标注。

### Fail-Closed / 安全告警

- `/api/o6/archive/labels` 及详情接口在以下场景返回 fail-closed：
  - 坏 JSON / 非对象 JSON
  - `labels` 非数组
  - `labels` 空数组
  - 超大数组
  - 字段类型错 / 长度越界
  - `unknown_task`
  - `unauthorized_task`
  - 不安全内容（`Authorization` / `Bearer` / token / `/cmd_vel` / 串口路径 / baudrate / traceback / credentials URL）
- `POST /api/o6/archive/labels` 若出现任何真实能力 true 声明也会 fail-closed，例如 `submit_enabled=true`、`dataset_export_available=true`、`real_annotation_api_connected=true`、`real_dataset_export_connected=true`、`safe_to_control=true`、`delivery_success=true`、`robot_control_executed=true`、`connects_cloud_production=true`。
- `GET /api/o6/archive/labels/<task_id>/export` 在以下场景 fail-closed：
  - `task_id` 不存在：`404 unknown_task`
  - `robot_id` 与 task 不一致：`403 unauthorized_task`
  - `format` 非 `jsonl`：`400 bad_request`
  - query 含未知字段、凭证、`/cmd_vel`、串口路径或危险 true 字段：`400 bad_request`
  - task 存在但无 labels：`409 blocked_not_proven`，不写 store
- 失败响应不回显危险内容，不创建/更新不存在的 task。

## Fail-Closed Rules

以下情况必须 fail closed：

- 坏 JSON
- 缺少 `robot_id` / `task_id` / `started_at_ms` / `finished_at_ms` / `trajectory_frames[]` / `events[]`
- `trajectory_frames[]` / `events[]` / `evidence_refs[]` 不是数组
- `finished_at_ms < started_at_ms`
- 数组过大
- 任意 unsafe content
- `Authorization`
- `Bearer`
- `token`
- `credentials URL`
- `/cmd_vel`
- 串口路径
- `baudrate`
- `traceback`

unsafe content 出现时，接口不会尝试“修复”原始请求，只会拒绝并返回安全错误摘要。

## O7 Consumption Note

O7 后续可以把这个 O6-shaped 数据源当作历史任务基础输入，再派生 route replay / labeling / voice / command 的只读视图；但这仍然只是本地 mock archive，不等于真实 O6 云存档、真实 DB 或真实 OSS 接通。
