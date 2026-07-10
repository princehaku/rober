# O1 Bounded Motion Feedback Material Pre-Start

## sprint_type

sprint_type: epic

## 用户价值和产品北极星

用户价值是把已经存在但尚未被当前 O1 material bundle 消费的真实上位机材料接进可复验证据链：bounded motion、T1001 feedback readback、IMU/battery sample、odom readback 都必须被安全摘要化，便于下一轮 current HIL 或现场执行命令直接对照缺口。

产品北极星仍是普通手机用户可安全、可验证地完成垃圾送达。本 sprint 只规划 `bounded_motion_feedback` / `bounded_motion_feedback_material` 的 historical upper-computer software proof，不证明 HIL pass、真实 safe-to-control、真实 delivery success、轮速方向、IMU/battery 标定或 Nav2 route execution。

## 上轮状态和切换原因

O5 当前约 `85%`，仍是 `OKR.md` 4.1 节最低 Objective。但 `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/final.md` 已明确：

- `okr_credit_allowed=false`
- `support_only_reason=no_real_production_external_evidence`
- `proof_boundary=software_proof_cloud_production_cutover_readiness_packet_only`
- 缺真实公网 HTTPS/TLS、4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic、真实 phone/browser 和真实 delivery success

因此本轮不继续 O5 readiness / probe / support-only packet。没有真实 external production evidence 时，继续消费同一 blocker 只能作为回归守护，不能计主 OKR 增量。

上一轮 `sprints/2026.07.10_21-27_o6_o7_localization_path_material_readback/final.md` 也明确要求：若继续 O6/O7，下一轮必须接 live route execution、delivery record、operator acceptance 或 production cloud readback，避免继续靠 localization/readback wrapper 提升百分比。因此本轮不继续 O6/O7 localization/readback-only。

O1 当前约 `90%`。最近 O1 已消费 historical same-run motion/map/free-cell/localization materials，但仍缺 current live HIL、WAVE ROVER nonzero L/R、轮速方向、IMU/battery 标定、motion command record、operator observation 和 HIL acceptance。当前可移动的新增材料不是再做 map/localization wrapper，而是把 2026-06-10 真实上位机 bounded motion / feedback readback 材料接入现有 O1 bundle。

## 本轮输入材料摘要

必须由后续 `robot-hardware-engineer` 只读消费并安全摘要：

- `sprints/2026.06.10_01-35_motion-feedback-alignment/artifacts/remote_capture/feedback_motion_summary.json`
  - schema 为 `rober.motion_feedback_alignment.v1`。
  - bounded motion command：`linear_x_mps=0.03`、目标非零时长 `0.25s`、`nonzero_duration_s=0.260472`、`nonzero_duration_lte_0_3s=true`。
  - safety stop：`zero_command_sent=true`、`trashbot_stop_called=true`、`stop_service_success_text=true`。
  - T1001：before/after 都观察到 `feedback_ack_t1001_observed=true`。
  - 边界：raw T1001 L/R motion window 不可用，`left_nonzero_proven=false`、`right_nonzero_proven=false`。
- `sprints/2026.06.10_01-35_motion-feedback-alignment/artifacts/remote_capture/pulse_and_stop.log`
  - 记录 `/esp32_bridge`、`/battery`、`/imu/data`、`/odom`、`/tf`、bounded pulse、stop success、odom/battery/imu sample。
- `sprints/2026.06.10_01-35_motion-feedback-alignment/artifacts/remote_capture/odom_after_motion.txt`
  - 可作为 odom readback sample material；不得单独包装成 dynamic odom proof 或 HIL pass。
- `sprints/2026.06.10_01-35_motion-feedback-alignment/artifacts/remote_capture/imu_once.txt`
  - 可作为 IMU sample present；不得包装成 IMU calibration proof。
- `sprints/2026.06.10_22-40_pc_real_robot_api_readback/artifacts/readback_summary.json`
  - 上位机服务 active，base direct status loaded，T1001 observed。
  - workstation base endpoints 因 dangerous true field 被 blocked，只能作为 readback/fail-closed context。
- `sprints/2026.06.10_22-40_pc_real_robot_api_readback/artifacts/base_feedback_samples_latest.json`
  - `base_feedback_samples_latest` 包含 2/2 samples observed T1001、`observed_feedback_types=[1001]`、`t1001_observed_count=2`。
  - 顶层固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`hil_pass=false`。
- 可选对照 `sprints/2026.06.10_02-05_wheel-feedback-diagnostic-sweep/artifacts/remote_capture/wheel_feedback_sweep_summary.json`
  - 三段 L/R 非零计数均为 `0`，只能作为 blocked/diagnostic context，不得包装成 wheel direction proof。

## OKR 映射和方向判断

- O5：暂停本轮主线推进。方向判断为“暂停计分，等待真实 external production evidence”。
- O1：继续推进。方向判断为“调整到 bounded_motion_feedback material intake”，把真实上位机 bounded motion / T1001 / IMU-battery / odom readback 接入既有 O1 material bundle。
- O6/O7：本轮不推进。上一轮已经要求不要继续 localization/readback-only；若未来需要云端归档或 UI 展示本 O1 材料，应另起跨 owner sprint。

Product closeout 只能在后续 implementation 确实消费上述材料、保持 `hil_pass=false`、`safe_to_control=false`、`delivery_success=false` 且 fail-closed 测试通过时，才评估 O1 是否有保守进度增量。本 planning 阶段不更新 `OKR.md`。

## KR 拆解、更新或历史归档

- O1 KR3：补强 `T=1001` feedback readback、IMU/battery sample、odom readback 的材料链，但不证明标定或实测里程计闭环。
- O1 KR4：后续需要增加 fail-closed 单测，覆盖 bounded motion 正例、T1001 feedback sample、IMU/battery/odom sample、wheel L/R 非零缺失、dangerous true 和 unsafe 泄露。
- O1 KR5：不改 launch 参数、不改串口参数、不改 command mode、不硬编码设备名。
- 已完成 KR：本 planning 阶段不归档任何 KR。
- 历史记录位置：待 implementation 和 Product closeout 后，再在 `OKR.md` 与 `docs/process/okr_progress_log.md` 记录；本轮禁止提前移动 KR。

## 本轮核心抓手

核心抓手是扩展现有 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`，新增 `bounded_motion_feedback` / `bounded_motion_feedback_material` 摘要，消费真实上位机 bounded motion、T1001 readback、IMU/battery sample 和 odom readback。

建议输出字段：

- `bounded_motion_feedback_material_present=true`
- `feedback_motion_summary_present=true`
- `base_feedback_samples_latest_present=true`
- `bounded_motion_command_observed=true`
- `bounded_motion_duration_lte_0_3s=true`
- `bounded_motion_stop_observed=true`
- `t1001_feedback_before_after_observed=true`
- `t1001_feedback_sample_count=2`
- `t1001_observed_count=2`
- `imu_sample_present=true`
- `battery_sample_present=true`
- `odom_readback_sample_present=true`
- `bounded_motion_lr_nonzero_proven=false`
- `wheel_direction_proven=false`
- `imu_battery_calibration_proven=false`
- `bounded_motion_feedback_ready_not_hil_pass=true`

以上字段只表示 bounded motion feedback material 已被安全 intake；不表示 current live HIL、safe-to-control、delivery success、wheel direction、IMU/battery calibration 或 route execution。

## 固定禁止宣称

本 sprint 及后续 implementation 必须固定：

- `proof_scope=software_proof_o1_motion_map_hil_material_bundle_only`
- `hil_pass=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`
- `nav2_route_execution_success=false`
- `wheel_direction_proven=false`
- `imu_battery_calibration_proven=false`

不得宣称：

- current live HIL
- hardware safe-to-control
- delivery success
- WAVE ROVER wheel direction proof
- IMU/battery calibration
- current same-run path generation success
- Nav2 route execution success
- production cloud proof

## Owner 和执行方式

- Product planning owner：`product-okr-owner`
- 后续 implementation owner：`robot-hardware-engineer`
- 执行方式：单 owner 单线闭环，由 `robot-hardware-engineer` 扩展现有 hardware bundle、测试、hardware docs 和 `tech-done.md`。

## 需要创建或更新的 sprint 文档

本 planning 阶段创建：

- `sprints/2026.07.10_22-29_o1_bounded_motion_feedback_material/pre_start.md`
- `sprints/2026.07.10_22-29_o1_bounded_motion_feedback_material/prd.md`
- `sprints/2026.07.10_22-29_o1_bounded_motion_feedback_material/tech-plan.md`

后续 implementation 完成后必须创建或更新：

- `sprints/2026.07.10_22-29_o1_bounded_motion_feedback_material/tech-done.md`
- 若进入收口：`side2side_check.md`、`final.md`

本 planning 阶段禁止改动：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- 产品代码、测试代码和硬件配置
- 其他 sprint 目录

## 风险、阻塞和需要补齐的证据链

- 这是 historical upper-computer software proof，不是 current live HIL。
- bounded motion 材料证明短时 pulse 和 stop 被记录，不证明 safe-to-control 或 delivery success。
- T1001 feedback readback 证明 feedback type observed，不证明 L/R 非零、轮向或 HIL pass。
- `odom_after_motion.txt` 和 `pulse_and_stop.log` 只能作为 odom readback material；不能单独证明 dynamic odom 或 route execution。
- IMU/battery sample 只证明 sample present，不证明标定。
- wheel diagnostic sweep 的 L/R 非零为 0，只能作为 blocked/diagnostic context。
- 仍缺 current live `feedback_T1001.log`、motion command record、operator/external observation、HIL acceptance、wheel direction、IMU/battery calibration、delivery result 和 live Nav2 route execution。
