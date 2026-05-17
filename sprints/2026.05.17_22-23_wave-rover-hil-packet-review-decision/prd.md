# Sprint 2026.05.17_22-23 Wave Rover HIL Packet Review Decision - PRD

sprint_type: epic

## 1. 用户价值和产品北极星

用户价值：普通用户不需要理解 WAVE ROVER、UART、ROS topic 或 HIL packet；现场支持和工程同学需要知道“这包材料哪些已被接受、哪些缺失、哪些被拒绝、下一步谁补、怎么重跑”。只有评审决策清楚，手机端和诊断端才不会把摄取成功误解为真实硬件通过。

产品北极星：低成本 ROS2 自主垃圾投递机器人必须先建立可信底盘证据链。真实送达、电梯 assisted delivery 和手机一键发车都依赖底盘反馈可信；在没有真实硬件的 Docker-only 主机上，产品侧必须把 `software_proof`、`not_proven` 和下一步证据边界写死。

## 2. OKR 映射

- Objective 1：本轮主目标。基于上一轮 `wave_rover_hil_packet_intake` 输出，新增 review decision 层，把 `feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`、`operator_hil_report` 的材料状态转成 accepted/missing/rejected 和下一步 evidence handoff。
- Objective 2 / Objective 3：只读受益。未来 route/elevator/task record 可以引用同一 `evidence_ref` 的 HIL packet review decision；本轮不改变 task_orchestrator、Nav2、fixed-route 或 delivery result。
- Objective 4：只读受益。手机端新增安全说明 panel，帮助普通用户/支持人员理解 HIL packet review decision；Start Delivery、Confirm Dropoff、Cancel gating 不变。
- Objective 5：不推进。Objective 5 仍约 68%，但当前缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 和真实手机/browser external proof；本轮不得把本地 gate 写成 O5 production proof。

## 3. KR 拆解或更新

### Objective 1 KR

- KR3：把 `T=1001` feedback、`/odom`、`/imu/data`、`/battery` snapshot 与 operator HIL report 的 review decision 固化为进入真实 HIL 复账前的产品决策层。
- KR4：新增 synthetic fixture 单元测试，覆盖 accepted、missing、rejected、intake artifact 缺失、schema 不支持、evidence_ref mismatch、unsafe success claim、`delivery_success=true` 和 `primary_actions_enabled=true` 等 fail-closed 分支。
- KR5：继续保持串口设备、baudrate、command mode 不在本轮硬编码；PC gate 只读上一轮 intake artifact/summary，不打开 serial。

### Objective 4 KR

- KR1 / KR5：手机端必须用普通用户可理解语言展示 review decision、缺失材料和 owner handoff，不暴露 raw ROS/serial 细节。
- KR7：新增面板不得破坏当前 Start / Confirm Dropoff / Cancel 的 fail-closed gating。

## 4. 本轮核心抓手

核心抓手是 `wave_rover_hil_packet_review_decision`，不是再做 intake-only summary。

最小可验收产品行为：

1. PC gate 读取上一轮 HIL packet intake artifact/summary，输出 `schema=trashbot.wave_rover_hil_packet_review_decision.v1` 和 diagnostics/mobile-safe summary。
2. Review decision 至少区分 `accepted_for_review`、`missing_required_materials`、`rejected_materials`、`blocked_pending_real_hil_packet`，并给出 `next_required_evidence`、`owner_handoff`、`rerun_commands`。
3. Robot diagnostics 只读消费 summary，识别 `software_proof_docker_wave_rover_hil_packet_review_decision_gate`，但永不启用 primary action。
4. Mobile web 显示只读 panel，说明 review decision、材料状态、下一步证据、owner handoff 和边界 flags。
5. Product closeout 只允许把本轮写为 software-proof review decision gate，不允许写成 `hil_pass`。

## 5. 需要做什么

- 新增 PC gate：`pc-tools/evidence/wave_rover_hil_packet_review_decision.py`。
- 新增测试和 fixtures：覆盖 intake summary accepted / missing / rejected / unsafe boundary cases。
- 新增硬件说明：`docs/hardware/wave_rover_hil_packet_review_decision.md`，引用 `docs/vendor/VENDOR_INDEX.md`、WAVE ROVER `json_cmd.h`、`uart_ctrl.h`、`base_ctrl.py`、`config.yaml`，并说明本轮只消费 summary。
- Robot diagnostics 新增 metadata-only consumer 和测试，更新 ROS contract 文档。
- Mobile web 新增 read-only panel、fixture/test 和产品流程文档。
- Product closeout 更新 sprint 文档、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 6. 优先级和验收口径

P0：

- 全链路保留 `software_proof_docker_wave_rover_hil_packet_review_decision_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- PC gate 不打开串口，不读硬件，不调用 ROS graph，只读 intake artifact/summary 和 synthetic fixture。
- 缺失 intake summary、schema 不支持、evidence_ref 不一致、required material 缺失、operator report 缺失、unsupported review decision、unsafe success language、`delivery_success=true` 或 `primary_actions_enabled=true` 必须 fail closed。
- Review decision 必须输出 accepted/missing/rejected required materials、next_required_evidence、owner_handoff 和 rerun_commands。

P1：

- Robot diagnostics 和 mobile panel 只显示安全字段，不暴露 raw artifact、local path、serial device、baudrate、raw feedback、traceback、checksum、credential、`/cmd_vel`。
- Mobile Start Delivery、Confirm Dropoff、Cancel gating 不变。
- docs 同步更新，说明本轮不是 `hil_pass`。

验收命令以 `tech-plan.md` 为准；测试只做围栏，不做大范围回归。

## 7. 对应责任 Engineer

- hardware-engineer：PC review-decision gate / fixtures / tests / hardware doc。
- robot-software-engineer：Robot diagnostics metadata-only consumer / tests / ROS contract doc。
- full-stack-software-engineer：mobile/web read-only panel / fixture / test / mobile product doc。
- product-okr-owner：closeout docs / OKR / progress log。

## 8. 风险、阻塞和需要补齐的证据链

- 本机没有真实硬件，只有 Docker；synthetic fixture 不能证明真实 WAVE ROVER、UART、feedback interval、`/odom`、`/imu/data`、`/battery` 或 `hil_pass`。
- 真实 HIL packet 仍需现场补齐：`feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`、`operator_hil_report`、同一 `evidence_ref`。
- PR #4 route/elevator field materials 仍需真实门状态、楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record、delivery result。
- PR #5 2D LiDAR / ToF 仍需真实 SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry 材料；本轮不能替代该证据链。
