# Sprint 2026.05.17_20-21 Wave Rover Feedback Replay Gate - Side2Side Check

sprint_type: epic

## 1. 验收对照

| 计划验收项 | 本轮结果 | Product 判断 |
| --- | --- | --- |
| PC gate 读取 `feedback_T1001.log`、topic once snapshots，并输出 replay / interval / topic-alignment summary | Task A 已新增 `wave_rover_feedback_replay_gate.py`、fixtures、tests 和硬件文档；happy fixture `overall_status=ready_for_hil_review_not_proven`，evidence_ref mismatch blocked | 通过软件围栏；仍是 `software_proof_docker_wave_rover_feedback_replay_gate` |
| 输出固定边界 token | PC / Robot / mobile / docs 均保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false` | 通过 |
| Robot diagnostics 只读消费 replay summary | Task B 新增 `wave_rover_feedback_replay` / `_summary` metadata-only consumer，diagnostics unittest `Ran 158 tests OK` | 通过；未启用 primary action |
| Mobile/web 只读展示 replay 状态 | Task C 新增只读 panel，mobile unittest `Ran 54 tests OK`，`node --check` pass | 通过；Start / Confirm Dropoff / Cancel gating 不变 |
| Vendor source 可追溯 | Task A 明确读过 `docs/vendor/VENDOR_INDEX.md`、`json_cmd.h`、`ugv_rpi/base_ctrl.py`、`ugv_rpi/config.yaml` 和 `docs/hardware/wave_rover_json_bridge.md` | 通过；未新增硬件猜测 |
| OKR conservative closeout | `OKR.md` 与 `docs/process/okr_progress_log.md` 已按 O1 HIL-prep software proof 更新，O5 保持约 68% | 通过 |

## 2. 用户价值核对

本轮把 Objective 1 的真实 HIL 缺口拆成可复核工具链：现场拿到真实 WAVE ROVER packet 后，可以先离线回放 `T=1001` feedback、检查 interval、核对 `/odom` / `/imu/data` / `/battery` once snapshots 与同一 `evidence_ref`，再决定是否进入 HIL review。

这符合产品北极星：普通用户可用的低成本送垃圾机器人，必须先让底盘反馈证据可追溯、可回放、可拒绝，而不是靠人工口头判断硬件是否可信。

## 3. OKR 映射

- Objective 1：本轮主推进项。`software_proof_docker_wave_rover_feedback_replay_gate` 使 `T=1001` feedback、topic alignment 和 HIL packet replay 的验收工具就绪，因此可从约 77% 保守上调到约 78%。该上调不代表 `hil_pass`。
- Objective 2 / Objective 3 / Objective 4：本轮只增加 WAVE ROVER feedback replay 的只读消费面，不新增真实 route/elevator field pass、真实 Nav2/fixed-route、真实手机设备或 production app proof，保持约 99%。
- Objective 5：继续保持约 68%。本轮没有公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof；O5 stop rule 仍成立。

## 4. 未完成证据链

- 真实 WAVE ROVER / UART / HIL：缺真实串口日志、真实 `feedback_T1001.log`、真实 `/odom`、真实 `/imu/data`、真实 `/battery`、真实 feedback interval 和 `hil_pass`。
- PR #4 route/elevator：缺真实电梯门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record、completion signal、dropoff/cancel completion 和 delivery result。
- PR #5 hardware materials：缺真实 2D LiDAR / ToF source、receipt、procurement、installation、wiring、power、calibration 和 HIL-entry。
- Objective 5：缺真实外部云、4G、OSS/CDN、DB/queue、worker/cutover 和真实手机/browser 证据。
