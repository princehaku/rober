# WAVE ROVER HIL Packet Collection Drill Pre-Start

Run time: 2026-05-22 13:06 Asia/Shanghai

## Sprint Declaration

- `sprint_type: epic`
- Sprint folder: `sprints/2026.05.22_13-14_wave-rover-hil-packet-collection-drill/`
- Capability: `wave_rover_hil_packet_collection_drill`
- Evidence boundary: `software_proof_docker_wave_rover_hil_packet_collection_drill_gate`
- Target objective: Objective 1, hardware protocol trusted base layer.
- Product owner: `product-okr-owner`
- Engineering owners: `hardware-engineer`, `robot-software-engineer`, `full-stack-software-engineer`

## User Value And Product North Star

用户价值：真实 WAVE ROVER HIL 上车前，现场 owner 需要一个可执行的采集演练 gate，把 `wave_rover_hil_packet_intake -> wave_rover_hil_packet_review_decision -> wave_rover_hil_packet_execution_pack` 串成一条清晰的采集顺序、材料模板、复跑命令和只读状态展示，减少下一次真实采集时漏文件、错 `evidence_ref` 或误报成功的风险。

产品北极星：普通手机用户和 support 只能看到安全、可解释、不可误操作的 HIL packet 采集准备状态。没有真实 WAVE ROVER、真实 UART、真实 `feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery` 和 operator HIL report 前，所有输出必须保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## Evidence Read Before Kickoff

- `AGENTS.md`：本轮是跨 Hardware / Robot / Full-Stack 的 Epic sprint，必须先建 `pre_start.md -> prd.md -> tech-plan.md`，实现阶段由对应 worker 并行执行。
- `OKR.md` 4.1：Objective 5 约 68%，当前最低；Objective 1 约 81%，当前次低。O5 缺真实 external/cloud/terminal-result material，本轮不继续包装 O5 metadata。
- `sprints/2026.05.22_12-13_verified-terminal-result-material-review-handoff/final.md`：上一轮明确 O5 没有真实 terminal result、public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/cutover，不能提升 O5。
- `sprints/2026.05.22_11-12_mobile-pwa-fresh-browser-proof-refresh/final.md`：最近一轮已因重复 blocker 切到 O4，明确 local browser proof 不能写成 O5 external proof。
- PR #5 review thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / hardware material pending；GitHub comment `3269642220` 只是 software-proof reply，不是 reviewer resolution。
- `docs/vendor/VENDOR_INDEX.md`：WAVE ROVER 上下位机链路是 UART newline-delimited JSON；vendor Raspberry Pi reference 使用 `/dev/ttyAMA0` at `115200`，但 Orange Pi 目标机不得硬编码该路径。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`：`FEEDBACK_BASE_INFO 1001`，`CMD_SPEED_CTRL 1`，`CMD_ROS_CTRL 13`，`CMD_BASE_FEEDBACK 130`，`CMD_BASE_FEEDBACK_FLOW 131`，`CMD_FEEDBACK_FLOW_INTERVAL 142`，`CMD_UART_ECHO_MODE 143`。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`：vendor upper-computer 以 `json.dumps(data) + '\n'` 发送命令，并以 `json.loads(...readline...)` 读取一行 JSON。
- `docs/hardware/wave_rover_hil_packet_execution_pack.md`：当前 execution pack 已定义 required material templates、collection sequence、owner handoff 和 rerun commands，但还没有 collection drill gate。
- `docs/product/mobile_user_flow.md`：mobile/web 只能消费 phone-safe / read-only summary，Start Delivery / Confirm Dropoff / Cancel 在 blocked 或 not-proven 状态保持禁用。

## Why This Sprint Does Not Target Objective 5

Objective 5 仍是最低项，但当前缺口需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser external proof 或 verified terminal delivery/dropoff/cancel result material。最近两轮已经证明继续在 Docker-only host 上包装同一缺真实材料 blocker 不会改变 O5 completion。

本轮选择 Objective 1 的 Docker-only 功能推进，是因为 `wave_rover_hil_packet_execution_pack` 已给出真实 HIL packet 采集顺序，但还缺一个可执行的 collection drill gate 把 intake、review decision 和 execution pack 串成现场 owner 可执行演练。该动作不会声明真实 HIL，也不会关闭 PR #5 reviewer thread。

## Scope Boundary

本轮 Product kickoff 只创建三份启动文档：

- `sprints/2026.05.22_13-14_wave-rover-hil-packet-collection-drill/pre_start.md`
- `sprints/2026.05.22_13-14_wave-rover-hil-packet-collection-drill/prd.md`
- `sprints/2026.05.22_13-14_wave-rover-hil-packet-collection-drill/tech-plan.md`

后续实现阶段允许的范围由 `tech-plan.md` 分配给 worker。Product kickoff 不改代码、测试、`OKR.md` 或其它 docs；收口文档稍后由 Product closeout 另派。

## Blocker Scan And Pivot Decision

- O5 blocker root cause: missing real external/cloud/terminal-result material.
- 最近两轮已说明不能继续包装同一 O5 blocker：`verified-terminal-result-material-review-handoff` 和 `mobile-pwa-fresh-browser-proof-refresh` 都保留 no OKR lift。
- O1 blocker root cause: missing real WAVE ROVER/UART/HIL packet and unresolved PR #5 hardware material thread.
- 本轮不是继续宣称真实 O1 proof，而是补 collection drill gate，让下一次真实采集能按同一 safe `evidence_ref` 收集 `feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl` 和 `operator_hil_report`。

## Initial Acceptance

- Epic kickoff docs exist.
- `tech-plan.md` includes `## OKR 最低优先级核对`.
- 文档显式包含 `wave_rover_hil_packet_collection_drill`、`software_proof_docker_wave_rover_hil_packet_collection_drill_gate`、Objective 5、Objective 1、PR thread `PRRT_kwDOSWB9286CJ3tX`、comment `3269642220`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` 和 `not_proven`。
- `git diff --check` 对本 sprint 文件通过。

