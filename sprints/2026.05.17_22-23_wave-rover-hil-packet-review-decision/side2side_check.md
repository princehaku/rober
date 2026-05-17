# Sprint 2026.05.17_22-23 Wave Rover HIL Packet Review Decision - Side2Side Check

sprint_type: epic

## 1. 用户价值和产品北极星核对

用户价值：真实 WAVE ROVER HIL packet 回填前，现场支持和工程同学可以先看到材料评审决策：哪些材料已 accepted、哪些 missing、哪些 rejected、下一步由谁补、用什么命令重跑。普通用户不需要理解 raw packet、UART 或 ROS topic，手机端只显示安全的只读解释。

产品北极星：低成本 ROS2 自主垃圾投递机器人要把底盘证据链做成可复盘、可审计、不会误报成功的产品能力。HIL packet intake 只是材料入口；本轮 review decision 让入口材料进入 accepted/missing/rejected 决策层，但仍不是真实硬件通过。

## 2. OKR 映射核对

- Objective 1：本轮主目标，完成 HIL packet review decision software proof。Objective 1 可从约 79% 保守上调到约 80%，理由是 PC / Robot diagnostics / mobile / Product 现在能共同消费同一 review decision summary。
- Objective 2 / Objective 3：保持约 99%。本轮没有真实 route/elevator field pass、真实 Nav2/fixed-route、真实 task record、真实 dropoff/cancel completion 或真实 delivery result。
- Objective 4：保持约 99%。本轮新增 mobile 只读 panel，但没有真实 iPhone/Android、production app、真实 PWA prompt/user choice 或真实现场 phone behavior。
- Objective 5：保持约 68%。O5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration/cutover 或真实手机/browser external proof；O5 stop rule 继续成立。

## 3. Side-by-side 验收

| 验收项 | 计划要求 | 实际结果 | 结论 |
| --- | --- | --- | --- |
| PC gate | 消费上一轮 intake artifact/summary，输出 review decision，不打开串口，不调用 ROS graph | 新增 dependency-free review-decision gate、fixture、测试和硬件说明；worker 已读 vendor 来源 | 通过 |
| Robot diagnostics | metadata-only consumer，fail closed，不启用 primary action | 新增 review decision diagnostics consumer 与测试，保留 `primary_actions_enabled=false` | 通过 |
| Mobile panel | 只读展示 review decision、材料状态、next evidence、owner handoff，不改 Start / Confirm / Cancel | 新增 WAVE ROVER HIL packet review decision panel 与 fixture/test，gating 不变 | 通过 |
| Docs sync | 硬件、接口、产品流程同步 | `docs/hardware/`、`docs/interfaces/`、`docs/product/` 已由对应 worker 更新 | 通过 |
| Product closeout | 更新 sprint 留档、OKR、progress log | Task D 更新三份 closeout 文档、`OKR.md`、`docs/process/okr_progress_log.md` | 通过 |

## 4. 边界核对

本轮必须保持并已在 closeout / OKR / progress log 中继续保留：

- `software_proof_docker_wave_rover_hil_packet_review_decision_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

本轮没有真实硬件，只有 Docker/local synthetic fixture 和 software-proof review decision。不得声明 `hil_pass`、真实 WAVE ROVER、真实 UART、真实 `/odom`、真实 `/imu/data`、真实 `/battery`、真实 route/elevator field pass、真实手机/browser、Objective 5 external proof 或 delivery success。

## 5. 剩余证据链

- 真实 WAVE ROVER HIL run。
- 真实 `feedback_T1001.log`。
- 真实 `odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`。
- 真实 `operator_hil_report`。
- 同一 safe `evidence_ref` 的完整 HIL packet。
- PR #4 route/elevator 现场材料和 PR #5 2D LiDAR / ToF 真实材料。
