# Sprint 2026.05.17_20-21 Wave Rover Feedback Replay Gate - Pre Start

sprint_type: epic

## 1. 启动结论

本轮启动新的 Epic sprint：`wave-rover-feedback-replay-gate`。

方向：在 Objective 5 外部证明不可用、真实 WAVE ROVER / 串口 / HIL 也不可用时，转向 Objective 1 的 Docker-only 可行动作：实现 WAVE ROVER `T=1001` feedback log replay / interval / topic-alignment gate。该 gate 只作为真实 HIL 前的验收工具，允许用合成 fixture 做软件围栏，未来消费真实 HIL 后产生的 `feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`。

证据边界固定为：`software_proof_docker_wave_rover_feedback_replay_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。本轮不得声明 `hil_pass`、真实串口通过、真实 WAVE ROVER 反馈通过、真实 `/odom`、真实 `/imu/data`、真实 `/battery` 或真实 delivery success。

## 2. 用户价值和产品北极星

用户价值：真实上车人员拿到 WAVE ROVER HIL evidence packet 后，可以先离线回放 `T=1001` feedback 与 ROS topic once snapshots，判断 feedback interval、字段完整性、topic 对齐和 evidence packet 是否足够进入复核，而不是把串口日志人工翻译成口头结论。

产品北极星：把低成本 ROS2 垃圾投递机器人推进到“硬件协议可信、证据可回放、真实 HIL 可复核”。本轮只补真实 HIL 前的验收工具，不用软件 fixture 替代真实 WAVE ROVER。

## 3. 当前证据

- `OKR.md` 4.1 更新时间为 2026-05-17 19:17 Asia/Shanghai：Objective 5 约 68%，是数值最低 Objective；Objective 1 约 77%，仍缺真实 WAVE ROVER `hil_pass`、真实串口日志、`T=1001` feedback、`/odom`、`/imu/data`、`/battery` 实机样本。
- `OKR.md` 第 6 节明确：继续推进 Objective 5 需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser 外部证据。本机只有 Docker，因此本轮不继续叠加 O5 本地 metadata depth。
- 最近三轮 final 形成同一边界：`2026.05.17_17-18_route-task-result-review-dispatch`、`2026.05.17_18-19_route-task-result-callback-intake`、`2026.05.17_19-20_route-task-result-callback-review-decision` 都把 PR #4 route/elevator 材料链继续推进到 Docker-only / metadata-only software proof；Objective 2/3 已约 99%，仍缺真实现场材料，继续包装同一链路不会越过现场 blocker。
- PR #4 `Add elevator-assisted delivery capability to agents, registry and OKR` 已合并，要求 elevator-assisted delivery 进入主行为链和证据采集边界；但最近 route/elevator result chain 已接近软件证明上限。
- PR #5 `Make elevator-assisted delivery mandatory; update agents, OKR and hardware baseline` 已合并；review 指出 `production_hardware_boundary.md` 默认硬件集与 mandatory `monocular + 2D LiDAR + ToF` 基线矛盾、OKR 最低项叙述漂移、mandatory sensor assumptions 缺 `docs/vendor/` 来源。最近 hardware chain 已完成 baseline/source/procurement/HIL-entry execution-pack，但仍缺真实串口、T=1001、2D LiDAR / ToF 真实材料。
- `docs/vendor/VENDOR_INDEX.md` 是硬件事实入口，列明 WAVE ROVER upper/lower link 是 UART newline-delimited JSON；`docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h` 和 vendor `ugv_rpi/base_ctrl.py` / `config.yaml` 是 JSON command、feedback flow、interval 和 command IDs 的本地来源。
- 历史 `sprints/2026.05.10_18-19_hardware-diagnostics-proof/` 已确认 `T=1001` feedback sample 可离线解析，但当时仍缺真实反馈频率、字段稳定性、IMU 姿态、电池电压和轮速读数实测。本轮不是重做 sample parse，而是把真实 HIL packet 的 replay/interval/topic alignment 做成 gate。

## 4. 本轮核心抓手

核心抓手：`software_proof_docker_wave_rover_feedback_replay_gate`。

它要把 O1 的真实 HIL 缺口拆成下一轮可执行的工具链：

1. 读取真实 HIL 之后产出的 `feedback_T1001.log`，逐行解析 WAVE ROVER `T=1001` JSON feedback。
2. 计算 feedback interval：输出 interval count、min/max/median、missing/large gap、timestamp/order verdict。
3. 读取 `odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`，检查它们是否与 feedback 样本同一 `evidence_ref`、同一 run window、字段可对齐。
4. 输出 fail-closed summary：`schema`、`evidence_boundary`、`source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`topic_alignment_status`、`next_required_evidence`。
5. 在本机用合成 fixture 做软件围栏；不得把 fixture 结果写成真实 HIL。

## 5. 本轮需要做什么

- Product Owner：完成本 sprint planning docs，明确 O5 stop rule、PR #4/#5 evidence、O1 抓手、owner 分工和验收口径。
- hardware-engineer：负责 PC evidence gate 与 fixture，必须复读 `docs/vendor/VENDOR_INDEX.md` 及 WAVE ROVER vendor 本地文件，不允许凭记忆猜测 `T=1001` 字段、feedback flow 或 interval 语义。
- robot-software-engineer：负责 Robot diagnostics metadata-only consumer，把 replay summary 只读纳入 diagnostics，不启用 primary action。
- full-stack-software-engineer：负责 mobile/web 只读摘要 panel，只展示 safe evidence fields，Start / Confirm Dropoff / Cancel gating 不变。
- product-okr-owner：实现后负责 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 与 `docs/process/okr_progress_log.md` 收口；除非真实硬件材料出现，否则 Objective 1 只能按工具 readiness 谨慎表述，不能写成 HIL pass。

## 6. 优先级和验收口径

P0：

- PC gate 能在 Docker/local 上用合成 fixture 通过，并对缺失 `feedback_T1001.log`、缺失 topic once snapshot、evidence_ref mismatch、unsupported schema、unsafe timestamp/interval 输出 blocked/not_proven。
- 输出必须包含 `software_proof_docker_wave_rover_feedback_replay_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- Vendor source 必须在实现或文档中引用 `docs/vendor/VENDOR_INDEX.md` 和 WAVE ROVER 本地 vendor 文件。

P1：

- Robot diagnostics 能 metadata-only 消费 replay summary，并在 unsupported/missing/unsafe 时 fail closed。
- mobile/web 能只读展示 replay verdict、interval summary、topic alignment、next required evidence 和 boundary flags，不暴露 raw artifact、本机路径、串口设备名、baudrate、raw ROS topic、traceback 或 credentials。

验收命令必须由对应 Engineer 子 agent 执行，Product 只做结果验收。

## 7. 风险、阻塞和证据链

- 真实硬件阻塞：当前主机没有真实 WAVE ROVER、真实串口/UART、真实 `feedback_T1001.log` 或 HIL；本轮只能产出 Docker/local software proof。
- Objective 5 阻塞：仍缺公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof；本轮不消费 O5 blocker。
- PR #4 现场材料阻塞：route/elevator chain 已到 callback-review-decision，仍缺真实电梯门状态、楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record、completion signal、dropoff/cancel completion 和 delivery result。
- PR #5 硬件材料阻塞：仍缺真实 2D LiDAR / ToF source、receipt、采购、安装、接线、电源、标定与 HIL-entry 材料；本轮不新增传感器假设。
- 证据链风险：如果 future HIL packet 没有 `feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl` 和同一 `evidence_ref`，gate 必须 blocked/not_proven。

## 8. 需要创建或更新的 sprint 文档

本轮 planning 阶段创建：

- `sprints/2026.05.17_20-21_wave-rover-feedback-replay-gate/pre_start.md`
- `sprints/2026.05.17_20-21_wave-rover-feedback-replay-gate/prd.md`
- `sprints/2026.05.17_20-21_wave-rover-feedback-replay-gate/tech-plan.md`

实现完成后必须继续更新：

- `sprints/2026.05.17_20-21_wave-rover-feedback-replay-gate/tech-done.md`
- `sprints/2026.05.17_20-21_wave-rover-feedback-replay-gate/side2side_check.md`
- `sprints/2026.05.17_20-21_wave-rover-feedback-replay-gate/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
