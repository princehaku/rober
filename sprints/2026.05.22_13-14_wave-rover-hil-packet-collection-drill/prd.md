# WAVE ROVER HIL Packet Collection Drill PRD

Run time: 2026-05-22 13:06 Asia/Shanghai

## Product North Star

把 WAVE ROVER HIL packet 从“已经有 intake / review / execution-pack 三个局部 gate”推进为“现场 owner 可按步骤演练并复核的一条采集链”。这条链服务于未来真实 WAVE ROVER HIL 采集，但本轮仍是 Docker-only software proof，不得写成真实串口、真实 WAVE ROVER、真实 `hil_pass`、真实 2D LiDAR/ToF 或 delivery success。

## User Value

- Hardware owner：拿到一个 collection drill gate，能按同一 safe `evidence_ref` 预演真实采集材料是否齐套，避免上车时漏 `feedback_T1001.log`、topic once snapshot 或 operator report。
- Robot owner：拿到 diagnostics safe alias，只把采集演练摘要暴露给 `/api/status` / `/api/diagnostics`，不打开 serial、不触发 ROS motion、不扩大控制面。
- Mobile/support owner：在 `mobile/web` 看到只读 panel，知道还缺哪些真实 HIL 材料、下一步由谁采集、为什么 Start Delivery / Confirm Dropoff / Cancel 仍禁用。
- Product owner：获得一条 Objective 1 的可执行软件推进证据，同时保留 O5、PR #5 和真实 HIL 边界。

## OKR Mapping

| Objective | Mapping | Boundary |
| --- | --- | --- |
| Objective 1：硬件协议可信底盘 | 本 sprint 针对 Objective 1 次低项，把 WAVE ROVER HIL packet ladder 串成 collection drill。 | 只允许声明 `software_proof_docker_wave_rover_hil_packet_collection_drill_gate`；不提升为真实 HIL。 |
| Objective 4：手机用户体验与低成本量产边界 | mobile/web 增加只读 collection drill panel，让 support 能解释采集准备状态。 | `primary_actions_enabled=false`，无真实手机/browser proof。 |
| Objective 5：云中转 + OSS/CDN 数据通路产品化 | 不作为本轮主目标。O5 仍缺真实 external/cloud/terminal-result material。 | 不声明 public HTTPS/TLS、4G/SIM、OSS/CDN、DB/queue、worker/cutover 或 verified terminal result。 |

## KR Breakdown

### KR-A Hardware Collection Drill Gate

Hardware worker 新增 `wave_rover_hil_packet_collection_drill` PC gate，串接现有：

- `wave_rover_hil_packet_intake`
- `wave_rover_hil_packet_review_decision`
- `wave_rover_hil_packet_execution_pack`

验收口径：

- 输入为 execution pack artifact 或 summary，输出 collection drill artifact + summary。
- 输出 schema 使用 `trashbot.wave_rover_hil_packet_collection_drill.v1` 和 `trashbot.wave_rover_hil_packet_collection_drill_summary.v1`。
- 输出 evidence boundary 固定为 `software_proof_docker_wave_rover_hil_packet_collection_drill_gate`。
- 必须保留 `source=software_proof`、`overall_status=not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`、`same_evidence_ref_required=true`。
- required materials 至少覆盖 `feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`、`operator_hil_report`。
- collection drill 必须输出 human-executable sequence、preflight checklist、backfill commands 和 blocked reasons。
- 不打开 `/dev/*`，不使用真实 serial，不 import ROS2，不调用 robot motion。

### KR-B Robot Diagnostics Safe Alias

Robot worker 将 collection drill 作为 diagnostics safe alias 暴露。

验收口径：

- 新增 `robot_diagnostics_wave_rover_hil_packet_collection_drill_summary`。
- `/api/status` 和 `/api/diagnostics` 能从 status、diagnostics 或 nested summary 中消费 collection drill summary。
- 缺 summary、unsafe fields、success wording、raw path、serial/UART detail、credentials、traceback、`/cmd_vel`、`delivery_success=true`、`primary_actions_enabled=true` 或 `safe_to_control=true` 时 fail closed。
- alias 只读，不触发 ACK、cursor、Nav2、route execution、serial open、WAVE ROVER command 或 HIL pass。

### KR-C Mobile Read-Only Panel

Full-Stack worker 在 `mobile/web` 增加 collection drill 只读 panel。

验收口径：

- panel 消费 `wave_rover_hil_packet_collection_drill`、`wave_rover_hil_packet_collection_drill_summary` 或 `robot_diagnostics_wave_rover_hil_packet_collection_drill_summary`。
- panel 展示 collection drill status、safe `evidence_ref`、required material templates、preflight checklist、collection sequence、rerun/backfill commands、owner handoff、evidence boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- panel 不展示 raw artifact、raw JSON、完整 feedback、checksum、local path、serial/UART path、baudrate、credentials、traceback、ROS topic、`/cmd_vel` 或控制按钮。
- Start Delivery / Confirm Dropoff / Cancel 保持 disabled。

### KR-D Product Closeout

Product closeout 后续另派，不在 kickoff 范围内。

验收口径：

- `tech-done.md`、`side2side_check.md`、`final.md` 只在实现完成后补。
- `OKR.md` 是否更新由 closeout 根据 worker 证据决定；本 kickoff 不改 `OKR.md`。
- 如只有 Docker-only software proof，默认不声明真实 HIL、真实 UART、真实 WAVE ROVER、真实 2D LiDAR/ToF、PR #5 reviewer resolved 或 delivery success。

## Priority

1. Hardware gate 是 P0，因为没有 collection drill artifact，Robot 和 Mobile 没有安全输入。
2. Robot safe alias 是 P1，因为 mobile/web 只能消费 Robot/API phone-safe summary，不能直接读 raw artifact。
3. Mobile read-only panel 是 P1，因为普通用户/support 需要安全可见状态，但不能触发主操作。
4. Product closeout 是 P2，必须等 worker 验证证据完成后再更新。

## Evidence And Source Boundary

采用的本地资料来源：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/hardware/wave_rover_hil_packet_intake.md`
- `docs/hardware/wave_rover_hil_packet_review_decision.md`
- `docs/hardware/wave_rover_hil_packet_execution_pack.md`
- `docs/interfaces/operator_gateway_diagnostics.md`
- `docs/product/mobile_user_flow.md`

这些资料只证明协议、材料模板和软件接口来源。它们不证明真实 WAVE ROVER、真实 UART、真实 `feedback_T1001.log`、真实 `/odom`、真实 `/imu/data`、真实 `/battery`、真实 2D LiDAR/ToF、真实 HIL-entry、PR #5 reviewer resolution 或 delivery success。

## Risks And Blocks

- 当前主机是 Docker-only，没有真实 WAVE ROVER、真实 UART 或真实 `/dev/ttyUSB*` passthrough；本轮不得尝试真实运动或声明 `hil_pass`。
- PR #5 thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved；comment `3269642220` 只是 software-proof reply。
- O5 仍缺真实 external/cloud/terminal-result material；本轮不得把 O1 collection drill 写成 O5 external proof。
- 代码新增必须满足中文技术注释要求，worker 在新增/修改代码时需保持有意义中文注释比例超过 20%。
- 任何 docs/product、docs/hardware、docs/interfaces 变更必须由对应 worker 同步完成；Product kickoff 不改这些 docs。

