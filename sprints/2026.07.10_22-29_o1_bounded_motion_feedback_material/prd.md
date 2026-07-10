# O1 Bounded Motion Feedback Material PRD

## sprint_type

sprint_type: epic

## 背景

O5 是当前最低 Objective，约 `85%`，但 `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/final.md` 已把 O5 锁定为 `okr_credit_allowed=false`。没有真实 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN、真实 phone/browser 和 production worker/cutover 证据时，O5 support-only packet 不能继续涨分。

上一轮 `sprints/2026.07.10_21-27_o6_o7_localization_path_material_readback/final.md` 要求不要继续 O6/O7 localization/readback-only；若继续 O6/O7，必须消费 live route execution、delivery record、operator acceptance 或 production cloud readback。

O1 当前约 `90%`，已经有 motion/map/free-cell/localization 的 historical software proof，但仍缺 current live HIL、轮速方向、IMU/battery 标定、同 run HIL acceptance 和真实 route execution。当前可推进的未消费材料是 2026-06-10 上位机真实 bounded motion / T1001 / IMU-battery / odom readback，而不是再做 O5 support surface 或 O6/O7 localization wrapper。

## 用户价值和产品北极星

用户价值是让硬件可信底盘从“有若干历史 map/localization 材料”继续靠近“能解释一次受控短动、能读到反馈、能读到基础传感器、能明确禁止误控”的证据链。普通用户最终只关心小车能安全送达；本 sprint 的价值是把底盘动作反馈材料收敛成可复验合同，并明确哪些还没有证明。

产品北极星仍是普通手机用户可安全、可验证地完成垃圾送达。本 sprint 是 `bounded_motion_feedback_material` software proof only，不是真实 HIL pass，不是真实 safe-to-control，不是真实 delivery success，不是真实 wheel direction proof。

## 需求目标

由 `robot-hardware-engineer` 在后续 implementation 中扩展现有 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`：

1. 消费 `feedback_motion_summary.json` 的 bounded motion、stop、T1001 before/after 和 proof boundary 字段。
2. 消费 `pulse_and_stop.log`、`odom_after_motion.txt`、`imu_once.txt` 中 allowlisted ROS topic sample/readback 材料。
3. 消费 `readback_summary.json` 和 `base_feedback_samples_latest.json` 的 T1001 readback material，其中 `base_feedback_samples_latest` 必须作为关键词和证据来源保留。
4. 可选消费 `wheel_feedback_sweep_summary.json` 作为 blocked/diagnostic context，必须固定 L/R 非零未证明。
5. 输出 `bounded_motion_feedback` / `bounded_motion_feedback_material` 安全字段，并保持 `hil_pass=false`、`safe_to_control=false`、`delivery_success=false`。
6. 对 unsafe raw path、URL、endpoint、token、traceback、`/dev/tty`、baudrate、raw UART frame、dangerous true fail-closed 或脱敏。

## 非目标

- 不执行真实 HIL。
- 不打开新的 WAVE ROVER 控制动作。
- 不发布新的 `/cmd_vel`。
- 不调用 `/api/base/manual`。
- 不执行 NavigateToPose / FollowPath / controller / BT。
- 不改 launch 参数、串口参数、速度映射或固件假设。
- 不证明 wheel direction。
- 不证明 IMU/battery calibration。
- 不改 O5/O6/O7、PC UI、cloud relay 或 OKR 文档。
- 不归档 KR。

## OKR 映射和方向判断

- O1：继续。理由是存在未消费的真实上位机 bounded motion / T1001 / IMU-battery / odom readback material，可在不打开控制面的前提下补强硬件可信底盘证据链。
- O5：暂停计分。理由是最低 Objective 当前缺真实 external production evidence，上一轮已明确 `okr_credit_allowed=false`。
- O6/O7：本轮不推进。上一轮已经要求不要继续 localization/readback-only；若后续需要云端存档或 UI 展示，应另起 sprint，不能把 O1 hardware bundle 扩散成跨 owner work。

方向判断：继续 O1，但 closeout 必须保守。只有实际消费候选材料并把 L/R 非零、wheel direction、IMU/battery calibration、HIL pass、safe-to-control、delivery success 保持 false，才可建议 Product closeout 评估 O1 是否有保守增量。只包装字段、不消费材料、不做 fail-closed 校验，不应上调。

## KR 拆解、更新或历史归档

- O1 KR3：补强 `T=1001` feedback readback、IMU/battery sample、odom readback 材料链。
- O1 KR4：补充 fail-closed 测试，避免 bounded motion、T1001 或传感器 sample 被误计为 HIL/safe/delivery 成功。
- O1 KR5：不调整 launch 参数，仅保留当前配置边界。
- 已完成 KR：无。
- 历史记录位置：本 planning 阶段不移动 KR。后续若 closeout 通过，在 `OKR.md` 和 `docs/process/okr_progress_log.md` 记录证据和剩余风险。

## 核心验收口径

后续 implementation 通过的最低验收口径：

- 输出 schema 仍为 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`。
- 输出 proof scope 仍为 `software_proof_o1_motion_map_hil_material_bundle_only`。
- `bounded_motion_feedback_material_present=true`。
- `feedback_motion_summary_present=true`。
- `base_feedback_samples_latest_present=true`。
- `bounded_motion_duration_lte_0_3s=true`。
- `bounded_motion_stop_observed=true`。
- `t1001_feedback_before_after_observed=true`。
- `t1001_observed_count=2`。
- `imu_sample_present=true`。
- `battery_sample_present=true`。
- `odom_readback_sample_present=true`。
- `bounded_motion_lr_nonzero_proven=false`。
- `wheel_direction_proven=false`。
- `imu_battery_calibration_proven=false`。
- `hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
- Positive output 不泄露 source URL、endpoint、absolute path、raw runtime context、`/dev/tty`、baudrate、token、secret、password、traceback 或长 base64。
- Negative tests 覆盖缺 source artifact、duration 超界、stop 缺失、T1001 缺失、IMU/battery/odom sample 缺失、dangerous true 和 diagnostic sweep 被误包装成 wheel proof。

## 对应责任 Engineer

- 主责：`robot-hardware-engineer`
- Product planning：`product-okr-owner`
- 不需要并行 owner。该任务文件范围集中在 hardware material bundle、hardware tests、hardware docs 和本 sprint `tech-done.md`。

## 证据来源

本 sprint planning 已读并采用：

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/final.md`
- `sprints/2026.07.10_20-26_o1_localization_path_material_bridge/final.md`
- `sprints/2026.07.10_21-27_o6_o7_localization_path_material_readback/final.md`
- `sprints/2026.06.10_01-35_motion-feedback-alignment/artifacts/remote_capture/feedback_motion_summary.json`
- `sprints/2026.06.10_01-35_motion-feedback-alignment/artifacts/remote_capture/pulse_and_stop.log`
- `sprints/2026.06.10_01-35_motion-feedback-alignment/artifacts/remote_capture/odom_after_motion.txt`
- `sprints/2026.06.10_01-35_motion-feedback-alignment/artifacts/remote_capture/imu_once.txt`
- `sprints/2026.06.10_22-40_pc_real_robot_api_readback/artifacts/readback_summary.json`
- `sprints/2026.06.10_22-40_pc_real_robot_api_readback/artifacts/base_feedback_samples_latest.json`
- `sprints/2026.06.10_02-05_wheel-feedback-diagnostic-sweep/artifacts/remote_capture/wheel_feedback_sweep_summary.json`

## 风险和阻塞

- 这些材料是 historical upper-computer material，不是 current live HIL。
- bounded motion 证明短时 pulse 和 stop 被记录，不证明 HIL pass。
- T1001 readback 证明 feedback observed，不证明 motion-window L/R 非零或 wheel direction。
- `odom_after_motion.txt` 只能作为 odom readback material，不能单独证明 dynamic odom、path generation 或 route execution。
- IMU/battery sample 只证明 sample present，不证明 calibration。
- `wheel_feedback_sweep_summary.json` 的 L/R 非零计数为 0，只能作为 diagnostic/blocked context。
- 如果 implementation 只新增字段但没有真实读取候选材料并做 fail-closed 校验，不能计为有效 O1 material delta。

## 后续文档要求

后续 implementation 必须同步更新：

- `docs/hardware/wave_rover_motion_map_hil_material_bundle.md`
- `sprints/2026.07.10_22-29_o1_bounded_motion_feedback_material/tech-done.md`

Product closeout 若发生，必须创建：

- `side2side_check.md`
- `final.md`

本 planning 阶段按用户限定范围不修改 `OKR.md`、`docs/process/okr_progress_log.md` 或产品代码。
