# WAVE ROVER Motion Map HIL Material Bundle

## Vendor sources

本 bundle 采用以下本地 vendor 资料，不从记忆推断底盘协议：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`

采用的硬件事实：

- WAVE ROVER 上下位机链路是 UTF-8 JSON line，以 `\n` 分帧。
- `T=1` 是左右轮速度命令，字段为 `L/R`。
- `T=130` 是一次性底盘反馈请求。
- `T=1001` 是底盘反馈类型，历史 feedback sample 至少观察到 `[130, 1001]`。
- `base_feedback_samples_latest.latest_result.sends_commands=true` 在本 bundle 中只解释为发送 `T=130` feedback request 的上下文；它不表示 motion command、safe control 或 HIL pass。

## Historical inputs

该 bundle 默认只读消费 `sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts/` 下的历史现场材料：

- `10_pc_first_jog_for_scan_delta.json`
- `12_pc_feedback_samples_after_scan_delta_jog.json`
- `14_scan_delta_metrics.json`
- `18_operator_report_lidar_delta_response.json`
- `22_field_first_jog_map.yaml`
- `23_field_first_jog_map.pgm`
- `24_field_first_jog_map_pixel_review.json`
- `30_manual_motion_map.yaml`
- `31_manual_motion_map.pgm`
- `32_manual_motion_map_pixel_review.json`

这些材料来自历史真实现场 run，但 bundle 的证据边界仍然是 software proof intake，不是 current live HIL pass。

本轮继续消费同一 artifact 目录下的 free-cell map materials：

- `33_pc_map_start_after_free_pixel_fix.json`
- `34_pc_map_list_after_free_pixel_fix.json`
- `35_fixed_free_cells_map.yaml`
- `36_fixed_free_cells_map.pgm`
- `37_fixed_free_cells_map_pixel_review.json`
- `38_pc_summary_after_map_fix.json`

这些材料只证明历史 free-cell map fix material 已被安全 intake。`35` 中的 YAML `image` basename 必须和 lifecycle/list 中的 map name 配对；`36` 是本 sprint 归档用 PGM copy，必须和 `37` 的 pixel review 以及 PGM header 配对。

本轮进一步消费 `38_pc_summary_after_map_fix.json` 中 allowlisted same-run localization/path readback：

- `status`
- `map_proof_latest`
- `localize_proof_latest`
- `nav2_status`
- `nav2_proof_latest`

该 bridge 只确认 `map_once_observed=true`、`amcl_pose_observed=true`、localization TF `map_to_odom=true` / `map_to_base_link=true` 已被安全 intake。它同时固定 same-run path 仍未证明：`path_generation_requested=true`、`path_generation_succeeded=false`、`path_generated=false`、`path_point_count=0`。

可选 comparator 来自 June 11 clean-baseline Nav2 path artifacts：

- `sprints/2026.06.11_11-15_clean_baseline_nav2_path_refresh/artifacts/nav2_latest_after_success.json`
- `sprints/2026.06.11_11-15_clean_baseline_nav2_path_refresh/artifacts/nav2_retry_summary.json`

这些 comparator 只能输出 `cross_run_clean_baseline_*` 字段，例如 `path_point_count=31`。它们不能覆盖 same-run `path_point_count=0`，也不能让 `same_run_path_proven` 变成 `true`。

本轮新增消费 2026-06-10 historical upper-computer bounded motion feedback materials：

- `sprints/2026.06.10_01-35_motion-feedback-alignment/artifacts/remote_capture/feedback_motion_summary.json`
- `sprints/2026.06.10_01-35_motion-feedback-alignment/artifacts/remote_capture/pulse_and_stop.log`
- `sprints/2026.06.10_01-35_motion-feedback-alignment/artifacts/remote_capture/odom_after_motion.txt`
- `sprints/2026.06.10_01-35_motion-feedback-alignment/artifacts/remote_capture/imu_once.txt`
- `sprints/2026.06.10_22-40_pc_real_robot_api_readback/artifacts/readback_summary.json`
- `sprints/2026.06.10_22-40_pc_real_robot_api_readback/artifacts/base_feedback_samples_latest.json`

可选 diagnostic context：

- `sprints/2026.06.10_02-05_wheel-feedback-diagnostic-sweep/artifacts/remote_capture/wheel_feedback_sweep_summary.json`

这些材料只证明历史上位机 bounded pulse、stop、T1001 readback、IMU/battery sample 和 odom readback sample 已被当前软件安全 intake。它们不证明 current live HIL、safe-to-control、delivery success、wheel direction、IMU/battery calibration 或 Nav2 route execution。

本轮继续把 2026-06-11 manual HIL gate current evidence 接入同一 bundle：

- `sprints/2026.06.11_10-35_pc_manual_hil_gate_current_evidence/artifacts/pc_proxy/gate_decision_before.json`
- `sprints/2026.06.11_10-35_pc_manual_hil_gate_current_evidence/artifacts/pc_proxy/stop_safety_smoke.json`
- `sprints/2026.06.11_10-35_pc_manual_hil_gate_current_evidence/artifacts/pc_proxy/manual_forward_expected_reject.json`
- `sprints/2026.06.11_10-35_pc_manual_hil_gate_current_evidence/artifacts/pc_proxy/proxy_smoke_result.json`
- `sprints/2026.06.11_10-35_pc_manual_hil_gate_current_evidence/artifacts/remote_readback/after_api_base_feedback-samples_latest.json`
- `sprints/2026.06.11_06-05_pc_structured_hil_report_readback/artifacts/real_board_operator_report_direct_192_168_1_11_8787.json`
- `sprints/2026.06.11_06-05_pc_structured_hil_report_readback/artifacts/real_board_robot_control_summary_192_168_1_11_8787.json`

这些材料只证明 manual HIL gate 的 fail-closed 语义已经被当前软件 intake：

- stop 可经 PC proxy 转发到 `/api/base/stop`
- 非 stop manual request 被本地拒绝
- 远端 `/api/base/manual` 没有被调用
- `T=130` feedback request 后观察到 2 个 `T=1001` samples
- operator structured report 里的 `delivery_success=true` 只能算 material-only claim，不能抬升顶层成功字段

## Contract

新增合同：

- `schema=trashbot.wave_rover_motion_map_hil_material_bundle.v1`
- `proof_scope=software_proof_o1_motion_map_hil_material_bundle_only`
- ready status: `motion_map_hil_material_bundle_ready_not_hil_pass`

输出摘要只保留：

- first jog command 的方向、速度、时长、HIL checklist gate 摘要；
- feedback samples 的 sample count、`t1001_observed_count`、`observed_feedback_types` 摘要；
- scan delta 的 `paired_bins`、`median_abs_diff_m`、`changed_bin_ratio` 和 pass 摘要；
- operator claims 的布尔位与 `site_state`；
- field/manual map 的 yaml 基本参数、PGM header、pixel review 统计；
- free-cell map lifecycle/list、YAML/PGM、pixel review 和 PC summary 的 allowlisted 摘要；
- localization/path bridge 的 allowlisted readback 摘要；
- cross-run clean-baseline comparator 的安全摘要；
- `blocked_reasons` 与 `next_required_evidence`；
- 固定 false 安全字段：`hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`nav2_route_execution_success=false`。

`map_output_present=true` 只表示成对的 map artifact 存在。由于两个 pixel review 都是 `has_free_cells=false`，因此 `map_navigation_ready` 永远固定为 `false`。

新增 free-cell additive 字段：

- `free_cell_map_material_present=true`
- `free_cell_map_lifecycle_present=true`
- `free_cell_map_list_present=true`
- `free_cell_map_yaml_present=true`
- `free_cell_map_pgm_present=true`
- `free_cell_pixel_review_present=true`
- `free_cell_pixel_count=394`
- `free_cell_has_free_cells=true`
- `free_cell_usable_map_count=1`
- `map_navigation_material_ready=true`

`map_navigation_material_ready=true` 只表示 free-cell map material 可作为后续定位/路径 proof 输入；它不表示 Nav2 route execution、current live HIL、安全可控或送达成功已经通过。

新增 localization/path additive 字段：

- `localization_path_material_bridge_present=true`
- `same_run_localization_material_present=true`
- `same_run_map_once_observed=true`
- `same_run_amcl_pose_observed=true`
- `same_run_localization_tf_map_to_odom=true`
- `same_run_localization_tf_map_to_base_link=true`
- `same_run_planner_server_active=true`
- `same_run_path_generation_requested=true`
- `same_run_path_generation_succeeded=false`
- `same_run_path_generated=false`
- `same_run_path_point_count=0`
- `same_run_path_proven=false`
- `localization_path_bridge_ready_not_route_execution_proof=true`

这些字段只证明 historical same-run localization/path material 已被当前软件安全 intake。它们不证明 current live HIL、safe-to-control、delivery success、Nav2 route execution success 或当前 live path generation success。

新增 cross-run comparator 字段：

- `cross_run_clean_baseline_path_comparator_present=true`
- `cross_run_clean_baseline_path_summary.path_generation_succeeded=true`
- `cross_run_clean_baseline_path_summary.path_generated=true`
- `cross_run_clean_baseline_path_summary.path_point_count=31`
- `cross_run_clean_baseline_path_summary.same_run_override_allowed=false`

Comparator 的成功路径只用于说明“成功 path proof 的形态”，不是 same-run proof。

新增 bounded motion feedback additive 字段：

- `bounded_motion_feedback_material_present=true`
- `bounded_motion_feedback_present=true`
- `feedback_motion_summary_present=true`
- `base_feedback_samples_latest_present=true`
- `bounded_motion_command_observed=true`
- `bounded_motion_duration_lte_0_3s=true`
- `bounded_motion_stop_observed=true`
- `t1001_feedback_before_after_observed=true`
- `t1001_feedback_sample_count=2`
- `t1001_observed_count=2`
- `odom_readback_sample_present=true`
- `odom_readback_frame_id=odom`
- `odom_readback_child_frame_id=base_link`
- `imu_sample_present=true`
- `imu_frame_id=imu_link`
- `battery_sample_present=true`
- `feedback_request_observed=true`
- `feedback_request_t130_observed=true`
- `bounded_motion_lr_nonzero_proven=false`
- `wheel_direction_proven=false`
- `imu_battery_calibration_proven=false`
- `bounded_motion_feedback_ready_not_hil_pass=true`

`wheel_feedback_diagnostic_context_present=true` 和 `wheel_feedback_sweep_all_nonzero_lr_count_zero=true` 只说明 optional diagnostic sweep 的 L/R 非零计数为 0。它不能作为 wheel proof；如果 diagnostic sweep 被篡改出非零 L/R，bundle 必须 blocked。

新增 manual HIL gate additive 字段：

- `manual_hil_gate_current_evidence_material_present=true`
- `manual_hil_gate_current_evidence_material_status=manual_hil_gate_current_evidence_material_ready_not_hil_pass`
- `manual_hil_gate_status=blocked`
- `manual_hil_gate_missing_fields=["external_video_recorded","visible_content_proven","wheel_feedback_lr_nonzero_proven","physical_motion_lidar_delta_proven"]`
- `visible_content_proven_blocks_motion=true`
- `manual_nonzero_policy=do_not_send_nonzero_expect_pc_local_reject`
- `stop_safety_smoke_forwarded=true`
- `manual_nonstop_local_reject_present=true`
- `manual_nonstop_remote_base_manual_called=false`
- `proxy_remote_base_manual_not_called_by_local_reject=true`
- `manual_gate_t1001_observed_count=2`
- `manual_gate_all_samples_observed_t1001=true`
- `manual_gate_feedback_request_t130_observed=true`
- `operator_structured_report_material_only=true`
- `operator_structured_report_status=ready_for_execution`
- `operator_structured_delivery_claim_material_only=true`
- `manual_hil_gate_ready_not_hil_pass=true`

这里的 `manual_hil_gate_status=blocked` 不是 bundle 失败，而是现场 manual gate 仍 blocked。bundle ready 仅表示这些 blocked/not-yet-safe 事实已被安全 intake。

## Fail-closed rules

下列任一情况必须 blocked：

- 任一核心 artifact 缺失、不可读、JSON/YAML/PGM header 解析失败。
- first jog / feedback / scan delta / operator / map 的 schema 或关键字段不匹配。
- first jog 的 `confirm_hil_checklist` 不是 `true`，或 `hil_checklist_gate_status` 不是 `manual_allowed`。
- feedback sample 的 `all_samples_observed_t1001` 不是 `"true"`，或 `feedback_ack_t1001_observed` 不是 `"true"`。
- operator 的 `physical_motion_lidar_delta_proven` 与 scan delta 结论不一致。
- operator required true 字段任一为 `false`：`operator_present`、`physical_clearance_confirmed`、`emergency_stop_ready`、`observed_stop`、`visible_content_proven`。
- operator required false 字段任一为 `true`：`external_video_recorded`、`wheel_feedback_lr_nonzero_proven`、`real_route_map_proven`、`delivery_success`。
- field/manual map 的 pixel review 与 PGM header 不一致，或 `has_free_cells` 不是 `false`。
- free-cell 33-38 任一核心 artifact 缺失、不可读或 schema 不匹配。
- free-cell map list 不是 `has_usable_map`、`usable_map_count != 1`，或 `map_usable_for_navigation` 不是 `true`。
- free-cell YAML image basename 不能和 lifecycle/list map name 配对。
- free-cell PGM header 与 pixel review 不匹配，`free_pixel_count != 394`，或 `has_free_cells` 不是 `true`。
- `38_pc_summary_after_map_fix.json` 缺失、不可读或 schema 不是 `trashbot.pc_tools_workstation.robot_control_summary.v1`。
- `status`、`map_proof_latest`、`localize_proof_latest`、`nav2_status`、`nav2_proof_latest` 任一 required readback 缺失、schema 不匹配、HTTP status 不是 `200` 或 request status 不是 `loaded`。
- `localization_tf_observed` 不是结构化 dict / JSON string，或缺 `map_to_odom=true`、`map_to_base_link=true`。
- same-run path 字段被篡改成 `path_generation_succeeded=true`、`path_generated=true`、`latest_path_generated=true` 或 `path_point_count>0`。
- 被消费字段里出现 URL、`/root/`、`/Users/`、`/dev/tty`、`token`、`secret`、`password`、traceback、baudrate 或长 base64 文本。
- 输入试图把 `hil_pass`、`safe_to_control`、`delivery_success`、`primary_actions_enabled`、`robot_control_executed`、`nav2_route_execution_success`、`same_run_path_proven`、`wheel_feedback_lr_nonzero_proven`、`real_route_map_proven` 提升为 `true`。
- bounded motion summary schema 不匹配、短动时长超出 0.3s、stop/zero command 缺失、before/after T1001 readback 缺失。
- `pulse_and_stop.log`、`odom_after_motion.txt` 或 `imu_once.txt` 缺 required sample/readback section。
- `readback_summary.json` 未证明 base direct status loaded 且 T1001 observed，或 safety proof boundary 不是 fixed false。
- `base_feedback_samples_latest.json` 不是 2/2 T1001 observed，或 observed feedback types 不是 `[1001]`。
- `base_feedback_samples_latest.latest_result.sends_commands=true` 缺少 `T=130` feedback request context，或任何层级把 `sends_motion_commands`、`robot_control_executed`、`safe_to_control`、`delivery_success`、`hil_pass` 提升为 `true`。
- optional diagnostic sweep 出现任一 segment 的 `nonzero_lr_count>0`。
- manual gate decision / stop smoke / manual reject / proxy smoke / feedback latest / operator latest / robot control summary 任一核心 artifact 缺失、schema 不匹配或 allowlisted 状态异常。
- manual gate 不是 `blocked`，或 missing fields 不是 `external_video_recorded`、`visible_content_proven`、`wheel_feedback_lr_nonzero_proven`、`physical_motion_lidar_delta_proven`。
- stop smoke 不是 `command_forwarded` 到 stop，或 non-stop manual request 不是本地 `command_rejected`。
- proxy smoke 未证明 `remote_base_manual_not_called_by_local_reject=true`。
- manual gate feedback 不是 `T=130` request、`t1001_observed_count!=2`、`all_samples_observed_t1001!=true`，或 `sends_motion_commands=true`。
- operator structured report 不是 material-only，或 nested `delivery_success=true` 泄漏到顶层 `delivery_success=true`。

正例原始材料里虽然含有 `source_base_url`、endpoint、`/root/...` 等 runtime 上下文，但 bundle 明确忽略这些 raw 字段；只要 allowlist 投影本身安全，正例仍应 ready。

June 11 comparator 缺失或不安全时，只会让 `cross_run_clean_baseline_path_comparator_present=false` 并写入 `cross_run_clean_baseline_path_comparator_blocked_reasons`；它不能让 same-run path 字段变成功。

## CLI smoke

默认读取历史 artifacts：

```bash
PYTHONPATH=onboard/src/ros2_trashbot_hardware python3 -m ros2_trashbot_hardware.wave_rover_motion_map_hil_material_bundle
```

负向覆盖某个输入文件：

```bash
PYTHONPATH=onboard/src/ros2_trashbot_hardware python3 -m ros2_trashbot_hardware.wave_rover_motion_map_hil_material_bundle --feedback-samples-json bad-feedback.json
```

free-cell 负向覆盖示例：

```bash
PYTHONPATH=onboard/src/ros2_trashbot_hardware python3 -m ros2_trashbot_hardware.wave_rover_motion_map_hil_material_bundle --free-cell-pixel-review-json bad-free-cell-review.json
```

bounded motion 负向覆盖示例：

```bash
PYTHONPATH=onboard/src/ros2_trashbot_hardware python3 -m ros2_trashbot_hardware.wave_rover_motion_map_hil_material_bundle --bounded-motion-feedback-summary-json bad-feedback-motion-summary.json
```

ready 输出只证明历史 motion + map 材料已被当前软件安全 intake。它不证明：

- current live HIL pass
- real wheel direction confirmation
- IMU/battery calibration
- current live map navigation readiness
- Nav2 route execution success
- same-run Nav2 path generation success
- delivery success

## Next evidence required

要继续推进 O1 真实现场履约，仍需新的同 run 材料：

- current live same-run `feedback_T1001.log`
- current live same-run motion command record
- current live same-run operator / external motion observation
- current live same-run HIL acceptance record
- current live route map with free cells
- current live same-run Nav2 path generation success
- current live same-run Nav2 route execution success
- current live same-run bounded motion T1001 L/R nonzero feedback
- current live same-run wheel direction confirmation
- current live same-run IMU/battery calibration record
