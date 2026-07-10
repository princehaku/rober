# O1 Bounded Motion Feedback Material Tech Plan

## sprint_type

sprint_type: epic

## 目标

规划一次 O1 hardware material intake：由 `robot-hardware-engineer` 在后续 implementation 中扩展现有 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`，接入 2026-06-10 真实上位机 bounded motion / T1001 / IMU-battery / odom readback 材料，新增 `bounded_motion_feedback` / `bounded_motion_feedback_material` 摘要。

本 sprint 的语义是 bounded motion feedback material ready, software proof only。它不是 current live HIL，不是真实 safe-to-control，不是真实 delivery success，不是真实 wheel direction proof，不是真实 IMU/battery calibration。

必须固定：

- `proof_scope=software_proof_o1_motion_map_hil_material_bundle_only`
- `hil_pass=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`
- `nav2_route_execution_success=false`
- `wheel_direction_proven=false`
- `imu_battery_calibration_proven=false`

本 planning 阶段不修改产品代码、测试、`OKR.md` 或 `docs/process/okr_progress_log.md`。

## 用户价值和产品北极星

用户需要最终可安全送达的机器人。这个 sprint 的价值是把一次真实上位机受控短动和反馈读回材料变成可审计 O1 bundle，让执行团队下一步明确缺 current HIL、L/R 非零、轮向、IMU/battery 标定和 route execution，而不是继续围绕 O5 support-only 或 O6/O7 readback surface 打转。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节里完成度最低的 Objective 是 O5，约 `85%`。
2. 本 sprint 不针对最低 Objective O5，而是转向 O1，约 `90%`。
3. 不继续 O5 的理由：
   - `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/final.md` 明确 O5 `okr_credit_allowed=false`。
   - O5 当前缺真实 external production evidence，包括公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic 和真实 phone/browser 材料。
   - 没有这些真实材料时，O5 readiness / probe / support-only packet 只能作为回归守护，不应继续计主 OKR 增量。
4. 不继续 O6/O7 localization/readback-only 的理由：
   - `sprints/2026.07.10_21-27_o6_o7_localization_path_material_readback/final.md` 已要求下一轮 O6/O7 必须接 live route execution、delivery record、operator acceptance 或 production cloud readback。
   - 当前本轮候选材料是 O1 硬件 bounded motion / feedback material，不是 O6/O7 新 route execution 或 delivery/operator 材料。
5. 转向 O1 的理由：
   - O1 仍缺 current HIL、WAVE ROVER nonzero L/R、轮速方向、IMU/battery 标定、motion command record 和 HIL acceptance。
   - 2026-06-10 候选材料包含真实上位机 bounded motion、T1001 readback、IMU/battery sample 和 odom readback，且尚未作为 `bounded_motion_feedback_material` 接入现有 O1 bundle。
   - 这些材料可以补强 O1 的可观测性和 fail-closed ladder，但必须保持 `hil_pass=false`、`safe_to_control=false`、`delivery_success=false`。

## Owner 和执行方式

- 主责 owner：`robot-hardware-engineer`
- 执行方式：单 owner 单线闭环。
- Product / 主节点只负责 planning、验收和收口，不直接写产品代码或运行 implementation 验证命令。

## 后续 implementation 文件范围

允许 `robot-hardware-engineer` 后续修改：

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_motion_map_hil_material_bundle.py`
- `onboard/src/ros2_trashbot_hardware/test/test_wave_rover_motion_map_hil_material_bundle.py`
- `docs/hardware/wave_rover_motion_map_hil_material_bundle.md`
- `sprints/2026.07.10_22-29_o1_bounded_motion_feedback_material/tech-done.md`

只读输入材料：

- `sprints/2026.06.10_01-35_motion-feedback-alignment/artifacts/remote_capture/feedback_motion_summary.json`
- `sprints/2026.06.10_01-35_motion-feedback-alignment/artifacts/remote_capture/pulse_and_stop.log`
- `sprints/2026.06.10_01-35_motion-feedback-alignment/artifacts/remote_capture/odom_after_motion.txt`
- `sprints/2026.06.10_01-35_motion-feedback-alignment/artifacts/remote_capture/imu_once.txt`
- `sprints/2026.06.10_22-40_pc_real_robot_api_readback/artifacts/readback_summary.json`
- `sprints/2026.06.10_22-40_pc_real_robot_api_readback/artifacts/base_feedback_samples_latest.json`
- 可选诊断：`sprints/2026.06.10_02-05_wheel-feedback-diagnostic-sweep/artifacts/remote_capture/wheel_feedback_sweep_summary.json`

禁止后续 implementation 修改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- 本 sprint `pre_start.md`、`prd.md`、`tech-plan.md`，除非 Product 明确要求修正 planning
- O5/O6/O7、PC UI、cloud relay、Nav2 execution 或无关业务文件

## Vendor 和事实来源

后续 Hardware owner 必须继续采用 `docs/vendor/VENDOR_INDEX.md` 指向的本地 WAVE ROVER 资料。本 planning 已读取 vendor index，并采用以下事实边界：

- WAVE ROVER 上下位机链路是 UART newline-delimited JSON。
- Vendor Raspberry Pi reference 使用 115200，但 Orange Pi 真实串口设备名必须在目标硬件确认，不能从历史材料反推 launch 默认值。
- `T=130` 是请求 base feedback。
- `T=1001` 是本轮可消费的 feedback material 类型。
- `T=1` / `T=13` / `/cmd_vel` 相关动作不得在本 implementation 中新增执行。

本 sprint 不新增串口、引脚、电压、波特率、速度映射或固件假设；只扩展历史 artifact safe summary。

## 接口影响

- 继续使用现有 schema：`trashbot.wave_rover_motion_map_hil_material_bundle.v1`。
- 只新增 additive fields，不改变控制策略、串口配置、launch 默认值、真实硬件动作或 `/cmd_vel` 行为。
- `bounded_motion_feedback_material_present=true` 只表示 historical upper-computer bounded motion feedback material 被安全 intake。
- `base_feedback_samples_latest_present=true` 只表示 T1001 feedback sample readback artifact 被消费；不表示 HIL pass 或 motion command success。
- `odom_readback_sample_present=true` 只表示 odom sample material 存在；不表示 route execution 或 reliable odometry。
- 若未来要给 O6/O7 消费这些字段，需要另起 sprint 明确 archive/readback/UI 范围。

## 计划任务

### 1. 扩展默认输入路径

在 `DEFAULT_PATHS` 中新增或复用：

- `bounded_motion_feedback_summary_json`
- `bounded_motion_pulse_and_stop_log`
- `bounded_motion_odom_after_motion_txt`
- `bounded_motion_imu_once_txt`
- `pc_real_robot_api_readback_summary_json`
- `base_feedback_samples_latest_json`
- 可选 `wheel_feedback_diagnostic_sweep_summary_json`

CLI 应支持逐项覆盖，方便 positive smoke、negative smoke 和 optional diagnostic 禁用。

### 2. 新增 bounded motion feedback parser

解析 `feedback_motion_summary.json` 的 allowlisted fields：

- `schema=rober.motion_feedback_alignment.v1`
- `motion_command.linear_x_mps=0.03`
- `motion_command.nonzero_duration_target_s=0.25`
- `motion_command.zero_command_sent=true`
- `motion_command.trashbot_stop_called=true`
- `observed.subscription_count_before_pulse=1`
- `observed.nonzero_duration_s=0.260472`
- `observed.nonzero_duration_lte_0_3s=true`
- `observed.stop_service_success_text=true`
- `observed.battery_topic_sample_present=true`
- `observed.imu_topic_sample_present=true`
- `observed.status_before.json.feedback_ack_t1001_observed=true`
- `observed.status_after.json.feedback_ack_t1001_observed=true`
- `t1001_lr_motion_window.left_nonzero_proven=false`
- `t1001_lr_motion_window.right_nonzero_proven=false`

`t1001_lr_motion_window` 缺非零 L/R 不应让 bounded material 正例失败，但必须固定 `bounded_motion_lr_nonzero_proven=false`，并写入 `next_required_evidence`。

### 3. 新增 ROS sample readback parser

从文本材料中只提取安全 summary：

- `pulse_and_stop.log`：node/topic list present、bounded pulse present、stop success、battery/imu/odom sections present。
- `odom_after_motion.txt`：`frame_id=odom`、`child_frame_id=base_link`、pose sample present；不得输出 raw file path 或把 sample 包装成 route execution。
- `imu_once.txt`：`frame_id=imu_link`、orientation/velocity/acceleration sample present；不得输出 raw calibration proof。

输出建议：

- `odom_readback_sample_present=true`
- `odom_readback_frame_id=odom`
- `odom_readback_child_frame_id=base_link`
- `imu_sample_present=true`
- `imu_frame_id=imu_link`
- `battery_sample_present=true` 从 `pulse_and_stop.log` 或 summary 得出
- `imu_battery_calibration_proven=false`

### 4. 新增 T1001 readback parser

消费 `readback_summary.json` 和 `base_feedback_samples_latest.json`：

- `readback_summary.schema=trashbot.sprint.pc_real_robot_api_readback.summary.v1`
- `readback_summary.base.t1001_observed=true`
- `base_feedback_samples_latest.schema=trashbot.upper_robot_api.v1.base_feedback_samples_latest_result`
- `base_feedback_samples_latest.latest_result.all_samples_observed_t1001=true`
- `base_feedback_samples_latest.latest_result.t1001_observed_count=2`
- `base_feedback_samples_latest.latest_result.completed_sample_count=2`
- `base_feedback_samples_latest.latest_result.observed_feedback_types=[1001]`
- `base_feedback_samples_latest.readback_sends_commands=false`
- `base_feedback_samples_latest.sends_motion_commands=false`
- `base_feedback_samples_latest.robot_control_executed=false`
- `base_feedback_samples_latest.safe_to_control=false`
- `base_feedback_samples_latest.delivery_success=false`
- `base_feedback_samples_latest.hil_pass=false`

注意：source artifact 内 `latest_result.sends_commands=true` 表示发送 `T=130` feedback request，不得把它升格成 motion command 或 safe control proof。summary 输出只能保留 `feedback_request_observed=true`、`sends_motion_commands=false` 和 fixed false safety fields。

### 5. 可选 diagnostic sweep context

若消费 `wheel_feedback_sweep_summary.json`，只能输出：

- `wheel_feedback_diagnostic_context_present=true`
- `wheel_feedback_sweep_all_nonzero_lr_count_zero=true`
- `wheel_direction_proven=false`
- `bounded_motion_lr_nonzero_proven=false`

不得把该材料包装成 wheel direction proof。若 summary 中任何 segment 的 `nonzero_lr_count` 被篡改为非零，本 sprint 应 blocked，并提示需要另起 current same-run wheel proof intake。

### 6. Summary 输出规则

Positive output 必须包含：

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
- `imu_sample_present=true`
- `battery_sample_present=true`
- `bounded_motion_lr_nonzero_proven=false`
- `wheel_direction_proven=false`
- `imu_battery_calibration_proven=false`
- `bounded_motion_feedback_ready_not_hil_pass=true`
- `hil_pass=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`
- `nav2_route_execution_success=false`

Status 建议保持现有保守命名 `motion_map_hil_material_bundle_ready_not_hil_pass`，并新增 section status `bounded_motion_feedback_material_ready_not_hil_pass`，避免误导为 HIL pass 或 wheel proof。

### 7. Fail-closed 和脱敏规则

以下情况必须 fail-closed：

- 任一 required source artifact 缺失、不可读或 schema 不匹配。
- bounded motion duration 缺失或 `nonzero_duration_lte_0_3s` 不是 true。
- stop/zero command 缺失。
- before/after T1001 ACK 不成立。
- `base_feedback_samples_latest` 缺失、不是 2/2 T1001 observed、或 observed feedback types 不含 `1001`。
- IMU、battery 或 odom sample required section 缺失。
- `safe_to_control`、`delivery_success`、`primary_actions_enabled`、`robot_control_executed`、`hil_pass`、`nav2_route_execution_success` 被置 true。
- source 或 summary 试图把 L/R 非零、wheel direction、IMU/battery calibration 或 route execution 置 true。
- 被消费字段出现 URL、token、secret、password、absolute path、`/dev/tty`、baudrate、raw UART frame、base64 或 traceback。
- optional diagnostic sweep 被包装成 wheel proof。

Fail-closed 输出必须保留 `blocked_reasons` 和 `next_required_evidence`，同时保持全部 fixed false fields。

### 8. 测试与文档

新增或更新测试覆盖：

- positive bounded motion feedback material from `feedback_motion_summary`、`pulse_and_stop`、`odom_after_motion`、`imu_once`、`base_feedback_samples_latest`。
- duration 超界 blocked。
- stop 缺失 blocked。
- T1001 before/after 或 sample count 缺失 blocked。
- IMU/battery/odom sample 缺失 blocked。
- source 内 `latest_result.sends_commands=true` 只作为 T130 feedback request context，不打开 `robot_control_executed`。
- dangerous true fields blocked。
- unsafe URL/path/token/traceback、`/dev/tty`、baudrate 不外泄。
- diagnostic sweep L/R 非零为 0 只进入 blocked context，不生成 wheel proof。
- CLI default ready 和 negative override exit `4`。

同步 `docs/hardware/wave_rover_motion_map_hil_material_bundle.md`，说明 `bounded_motion_feedback_material` 是 historical upper-computer software proof，不是 current live HIL、安全控制、轮向证明、IMU/battery 标定、Nav2 route execution 或 delivery success。

## 验收命令

后续 implementation 必须至少运行：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/*.py
python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*motion*map*hil*.py'
PYTHONPATH=onboard/src/ros2_trashbot_hardware python3 -m ros2_trashbot_hardware.wave_rover_motion_map_hil_material_bundle
rg -n "bounded_motion_feedback|bounded_motion_feedback_material|feedback_motion_summary|base_feedback_samples_latest|hil_pass=false|safe_to_control=false|delivery_success=false" onboard/src/ros2_trashbot_hardware docs/hardware sprints/2026.07.10_22-29_o1_bounded_motion_feedback_material
git diff --check -- onboard/src/ros2_trashbot_hardware docs/hardware sprints/2026.07.10_22-29_o1_bounded_motion_feedback_material
```

本 plan-stage 验收命令：

```bash
test -f sprints/2026.07.10_22-29_o1_bounded_motion_feedback_material/pre_start.md && test -f sprints/2026.07.10_22-29_o1_bounded_motion_feedback_material/prd.md && test -f sprints/2026.07.10_22-29_o1_bounded_motion_feedback_material/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|O5|robot-hardware-engineer|bounded_motion_feedback|feedback_motion_summary|base_feedback_samples_latest|hil_pass=false|safe_to_control=false|delivery_success=false" sprints/2026.07.10_22-29_o1_bounded_motion_feedback_material
git diff --check -- sprints/2026.07.10_22-29_o1_bounded_motion_feedback_material
```

## 证据边界

本 sprint 可以证明：

- 2026-06-10 historical upper-computer bounded motion material 可被当前软件安全 intake。
- bounded motion command、stop、T1001 before/after feedback ACK、T1001 feedback samples、IMU/battery sample 和 odom readback sample 可被摘要化。
- diagnostic sweep 可保留为 blocked context，说明 L/R 非零没有被证明。

本 sprint 不能证明：

- current live HIL
- hardware safe-to-control
- delivery success
- wheel direction
- IMU/battery calibration
- production cloud
- current same-run path generation success
- Nav2 route execution success
- route delivery completion

## Closeout 条件

Product closeout 可建议 O1 保守增量的条件：

- implementation 确实消费全部 required 候选材料。
- positive output 包含 bounded motion、T1001、IMU/battery、odom sample present，并固定 L/R、wheel direction、IMU/battery calibration、HIL、safe、delivery false。
- fail-closed tests 覆盖 duration 超界、stop/T1001/sample 缺失、dangerous true、unsafe 字段和 diagnostic sweep 误包装。
- 文档明确 proof boundary 为 `software_proof_o1_motion_map_hil_material_bundle_only`。
- `tech-done.md` 记录验证输出和剩余风险。

不得上调 O1 的情况：

- 只重复上一轮 map/localization fields。
- 只引用 diagnostic sweep。
- 未消费 `feedback_motion_summary` 或 `base_feedback_samples_latest`。
- 输出中出现 `hil_pass=true`、`safe_to_control=true`、`delivery_success=true`、`robot_control_executed=true`、`wheel_direction_proven=true` 或 `imu_battery_calibration_proven=true`。

## 风险和阻塞

- 这是 historical upper-computer software proof，不是当前上车实时 HIL。
- `T=1001` observed 容易被误读为 HIL pass，必须在代码、文档和 closeout 中固定 `hil_pass=false`。
- `/odom` sample 容易被误读为 route execution，必须只写成 readback sample。
- `base_feedback_samples_latest` 中的 feedback request 不能被误读为 motion command。
- diagnostic sweep 的 L/R 非零计数为 0，字段必须保守。
- 仍缺 current live `feedback_T1001.log`、motion command、operator/external observation、HIL acceptance、wheel direction、IMU/battery calibration、delivery record 和 route execution result。

## 下一步派发摘要

派给 `robot-hardware-engineer`：

- 文件范围：`wave_rover_motion_map_hil_material_bundle.py`、对应 `test_wave_rover_motion_map_hil_material_bundle.py`、`docs/hardware/wave_rover_motion_map_hil_material_bundle.md`、本 sprint `tech-done.md`。
- 核心任务：扩展现有 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`，消费 2026-06-10 bounded motion / T1001 / IMU-battery / odom readback materials，输出 `bounded_motion_feedback_material_present=true`、`base_feedback_samples_latest_present=true`、`hil_pass=false`、`safe_to_control=false`、`delivery_success=false` 等安全字段。
- 验收命令：`py_compile`、motion-map-HIL unittest、默认 CLI smoke、anchor `rg`、scoped `git diff --check`。
