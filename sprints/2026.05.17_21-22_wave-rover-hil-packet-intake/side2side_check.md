# Sprint 2026.05.17_21-22 Wave Rover HIL Packet Intake - Side2Side Check

sprint_type: epic

## 1. 用户价值和产品北极星核对

用户价值：现场支持以后可以把真实 WAVE ROVER HIL packet 按 `feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`、`operator_hil_report` 和同一 `evidence_ref` 交给系统，PC gate、Robot diagnostics 和 mobile panel 都能给出一致的只读结论。

产品北极星：低成本 ROS2 自主垃圾投递机器人要先有可信底盘证据入口，后续 route/elevator/delivery 证据才不会建立在不可复核的硬件假设上。

## 2. OKR 映射核对

- Objective 1：本轮主目标，形成 HIL packet intake contract 和软件围栏。若整体验收通过，可从约 78% 保守上调到约 79%。
- Objective 2 / Objective 3：不调整。本轮没有真实 route/elevator field pass、真实 Nav2/fixed-route、真实 task record 或真实 delivery result。
- Objective 4：不调整。本轮新增 mobile 只读 panel，但没有真实 iPhone/Android、production app、真实 PWA prompt/user choice 或真实现场 phone behavior。
- Objective 5：不调整。O5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration/cutover 或真实手机/browser external proof。

## 3. Side-by-side 验收

| 验收项 | 计划要求 | 实际结果 | 结论 |
| --- | --- | --- | --- |
| PC gate | 只读 packet directory，不打开串口，不调用 ROS graph | 新增 dependency-free gate、synthetic fixtures 和测试 | 通过 |
| Robot diagnostics | metadata-only consumer，fail closed，不启用 primary action | 新增 diagnostics summary consumer 与测试，保留 `primary_actions_enabled=false` | 通过 |
| Mobile panel | 只读展示 packet status / evidence / missing materials，不改 Start / Confirm / Cancel | 新增 WAVE ROVER HIL packet intake panel 与 fixture/test，gating 不变 | 通过 |
| Docs sync | 硬件、接口、产品流程同步 | `docs/hardware/`、`docs/interfaces/`、`docs/product/` 已更新 | 通过 |
| Product closeout | 更新 sprint 留档、OKR、progress log | Task D 更新本 sprint 三份 closeout 文档、`OKR.md`、`docs/process/okr_progress_log.md` | 通过 |

## 4. 边界核对

本轮必须保持并已在 closeout / OKR / progress log 中继续保留：

- `software_proof_docker_wave_rover_hil_packet_intake_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

本轮没有真实硬件，只有 Docker/local synthetic fixture。不得声明 `hil_pass`、真实 WAVE ROVER、真实 UART、真实 `/odom`、真实 `/imu/data`、真实 `/battery`、真实 route/elevator field pass、真实手机/browser、Objective 5 external proof 或 delivery success。

## 5. 剩余证据链

- 真实 WAVE ROVER HIL run。
- 真实 `feedback_T1001.log`。
- 真实 `odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`。
- 真实 `operator_hil_report`。
- 同一 safe `evidence_ref` 的完整 HIL packet。
- PR #4 route/elevator 现场材料和 PR #5 2D LiDAR / ToF 真实材料。
