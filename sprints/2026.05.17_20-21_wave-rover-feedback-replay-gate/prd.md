# Sprint 2026.05.17_20-21 Wave Rover Feedback Replay Gate - PRD

sprint_type: epic

## 1. 用户价值和产品北极星

用户价值：让现场硬件/HIL 同学在拿到真实 WAVE ROVER evidence packet 后，可以用同一个工具离线判断 `T=1001` feedback 是否可回放、feedback interval 是否可信、`/odom` / `/imu/data` / `/battery` once snapshots 是否与 feedback 对齐。这样 Objective 1 的下一步不再依赖人工读日志，也不会把 `hardware_smoke_wave_rover.py --status` 或合成 sample 当成 `hil_pass`。

产品北极星：低成本 ROS2 垃圾投递机器人必须先有可信底盘控制层。可信的含义不是“写了驱动”，而是 WAVE ROVER 官方 UART JSON feedback、ROS topic、HIL evidence packet 和后续 route/elevator 证据能被统一回放、核对和复盘。

## 2. OKR 映射

主目标：Objective 1，硬件协议可信底盘。

- KR1：本轮不改串口启动参数，但要求 replay gate 的文档/实现明确 WAVE ROVER UART JSON feedback 来源，避免继续扩展旧二进制或未验证协议假设。
- KR3：直接针对 `T=1001` 底盘反馈、`/imu/data`、`/battery` 和 `/odom` 来源边界，提供真实 HIL packet 后的 replay/topic alignment 验收工具。
- KR4：用合成 fixture 覆盖 JSON feedback replay、interval 异常、topic snapshot 缺失、bad data 容错。
- KR5：不硬编码 Orange Pi 设备名或真实串口路径；本轮是 file-based replay，不打开串口。

非主目标：

- Objective 5 约 68%，仍是数值最低，但 `OKR.md` 第 6 节要求真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof 才继续推进；本机只有 Docker，本轮不推进 O5。
- Objective 2/3/4 已约 99%，最近 route-task result dispatch/intake/review-decision chain 已接近软件证明上限；本轮不继续包装 PR #4 route/elevator field blocker。
- PR #5 的 2D LiDAR / ToF 真实材料仍缺，本轮不新增或猜测传感器硬件事实。

## 3. KR 拆解或更新

本 sprint 的 Product KR：

1. KR-O1-Replay-Gate：新增 `trashbot.wave_rover_feedback_replay.v1` 或等价 summary schema，输出 `software_proof_docker_wave_rover_feedback_replay_gate`。
2. KR-O1-Interval：从 `feedback_T1001.log` 计算 feedback interval summary，并对 timestamp missing、order mismatch、large gap、empty feedback fail closed。
3. KR-O1-Topic-Alignment：读取 `odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`，检查 evidence_ref、run window 和字段存在性，输出 `topic_alignment_status`。
4. KR-O1-Boundary：所有输出固定带 `source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`，且 `not_proven` 必须覆盖真实 WAVE ROVER、真实 UART、HIL、真实 `/odom`、真实 `/imu/data`、真实 `/battery`、真实 delivery success。
5. KR-O1-Team-Surfaces：PC gate、Robot diagnostics、mobile/web 只读 panel 三面只消费 safe summary，不启用任何 primary action。

## 4. 本轮核心抓手

核心抓手是 WAVE ROVER feedback replay / interval / topic-alignment gate。

输入：

- `feedback_T1001.log`：真实 HIL 后由 serial/session capture 产出的 WAVE ROVER feedback log；本轮验收使用合成 fixture。
- `odom_once.jsonl`：一次 `/odom` snapshot 或等价 normalized sample。
- `imu_once.jsonl`：一次 `/imu/data` snapshot 或等价 normalized sample。
- `battery_once.jsonl`：一次 `/battery` snapshot 或等价 normalized sample。
- `evidence_ref`：真实 HIL packet 和 topic snapshots 必须共享的安全引用。

输出：

- `schema`。
- `evidence_boundary=software_proof_docker_wave_rover_feedback_replay_gate`。
- `source=software_proof`。
- `feedback_replay_status`。
- `interval_status`。
- `topic_alignment_status`。
- `next_required_evidence`。
- `not_proven`。
- `delivery_success=false`。
- `primary_actions_enabled=false`。

## 5. 需要做什么

### Task A - hardware-engineer

职责：实现 PC evidence gate 和 fixtures。

允许范围建议：

- `pc-tools/evidence/wave_rover_feedback_replay_gate.py`
- `pc-tools/evidence/test_wave_rover_feedback_replay_gate.py`
- `pc-tools/evidence/fixtures/wave_rover_feedback_replay/`
- `docs/hardware/wave_rover_feedback_replay_gate.md` 或现有硬件证据文档

必须引用：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`

### Task B - robot-software-engineer

职责：Robot diagnostics metadata-only consumer。

允许范围建议：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

要求：只读消费 summary，缺失/unsupported/mismatch 时 fail closed，不发布控制命令，不打开串口，不声明 HIL。

### Task C - full-stack-software-engineer

职责：mobile/web 只读 panel。

允许范围建议：

- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

要求：展示 replay verdict、interval summary、topic alignment、next required evidence、boundary flags；不展示 raw local path、serial device、baudrate、raw ROS topic、traceback、checksum、credentials；Start / Confirm Dropoff / Cancel gating 不变。

### Task D - product-okr-owner

职责：验收、留档和 OKR closeout。

允许范围建议：

- `sprints/2026.05.17_20-21_wave-rover-feedback-replay-gate/tech-done.md`
- `sprints/2026.05.17_20-21_wave-rover-feedback-replay-gate/side2side_check.md`
- `sprints/2026.05.17_20-21_wave-rover-feedback-replay-gate/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

要求：如果只有 Docker fixture proof，Objective 1 只能描述为 HIL 前 replay gate readiness；不得把 completion 写成真实 HIL 或真实底盘反馈通过。

## 6. 优先级和验收口径

P0 验收：

- 合成 happy fixture 输出 pass/readiness，但仍 `not_proven`。
- 缺 `feedback_T1001.log`、缺任一 once snapshot、evidence_ref 不一致、unsupported schema、timestamp/interval 异常、unsafe topic fields 时输出 blocked/not_proven。
- summary 中包含 `software_proof_docker_wave_rover_feedback_replay_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- `rg` 能找到 PR #4、PR #5、Objective 5 stop reason、Objective 1 replay gate、vendor source 和边界字段。

P1 验收：

- Robot diagnostics 和 mobile/web 只读消费同一个 summary schema。
- 文档同步更新，不让 docs 落后于实现。
- 新增代码的技术注释使用中文且比例超过 20%；注释解释为什么 fail closed、为什么不把 fixture 写成 HIL。

## 7. 风险、阻塞和需要补齐的证据链

- 阻塞：本机没有真实 WAVE ROVER / UART / HIL，所以本轮不能证明真实 feedback interval、真实 topic timing 或真实电池/IMU/odom 数值。
- 证据链待补：真实 HIL packet 必须包含 `command.txt`、`serial.log`、`feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl` 和同一 `evidence_ref`。
- PR #4 待补：真实 route/elevator field materials 仍需门状态、目标楼层、人工协助、Nav2/fixed-route runtime log、task record、completion signal、dropoff/cancel completion、delivery result。
- PR #5 待补：真实 2D LiDAR / ToF source、receipt、procurement、installation、wiring、power、calibration、HIL-entry。
- Objective 5 待补：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof。
