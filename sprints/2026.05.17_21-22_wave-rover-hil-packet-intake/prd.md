# Sprint 2026.05.17_21-22 Wave Rover HIL Packet Intake - PRD

sprint_type: epic

## 1. 用户价值和产品北极星

用户价值：普通用户不需要理解 WAVE ROVER、UART、ROS topic 或 HIL 细节；现场支持只需收集一包标准化 HIL packet，系统就能给出“哪些真实底盘证据已经齐、哪些仍缺、为什么不能发车/不能宣称通过”的安全结论。

产品北极星：低成本 ROS2 自主垃圾投递机器人必须先把底盘协议可信化。只有真实 WAVE ROVER feedback、topic snapshot 和人工 HIL 报告能被同一 `evidence_ref` 复核，后续 route/elevator/delivery 证据才不会建立在不可信底盘之上。

## 2. OKR 映射

- Objective 1：本轮主目标。把 `feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`、`operator_hil_report` 转成可摄取的 HIL packet contract，为真实 `hil_pass` 做准入，但本轮不声明真实通过。
- Objective 2 / Objective 3：只读受益。未来 route/elevator/task record 可以引用同一 `evidence_ref` 的底盘 packet；本轮不改变 task_orchestrator、Nav2、fixed-route 或 delivery result。
- Objective 4：只读受益。手机端新增安全说明 panel，帮助普通用户/支持人员理解 HIL packet 状态；Start Delivery、Confirm Dropoff、Cancel gating 不变。
- Objective 5：不推进。Objective 5 仍约 68%，但当前缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration/cutover 和真实手机/browser external proof；本轮不得把本地 gate 写成 O5 production proof。

## 3. KR 拆解或更新

### Objective 1 KR

- KR3：把 `T=1001` 底盘反馈与 `/odom`、`/imu/data`、`/battery` snapshot 的同一 `evidence_ref` 对齐列为 HIL packet intake 必备条件。
- KR4：新增 synthetic fixture 单元测试，覆盖完整 packet、缺失文件、evidence_ref mismatch、operator report 缺失、unsafe success claim、delivery flag 错误等 fail-closed 分支。
- KR5：继续保持串口设备、baudrate、command mode 不在本轮硬编码；PC gate 只读文件，不打开 serial。

### Objective 4 KR

- KR1 / KR5：手机端必须用普通用户可理解语言展示 HIL packet intake 状态和下一步材料，不暴露 raw ROS/serial 细节。
- KR7：新增面板不得破坏当前 Start / Confirm Dropoff / Cancel 的 fail-closed gating。

## 4. 本轮核心抓手

核心抓手是 `wave_rover_hil_packet_intake`，不是再做 replay-only summary。

最小可验收产品行为：

1. PC gate 读取一个目录中的 HIL packet 文件，输出 `schema=trashbot.wave_rover_hil_packet_intake.v1` 和 phone/diagnostics-safe summary。
2. Robot diagnostics 只读消费 summary，识别 `software_proof_docker_wave_rover_hil_packet_intake_gate`，但永不启用 primary action。
3. Mobile web 显示只读 panel，说明 packet 状态、缺失材料、下一步证据和边界 flags。
4. Product closeout 只允许把本轮写为 software-proof HIL packet intake，不允许写成 `hil_pass`。

## 5. 需要做什么

- 新增 PC gate：`pc-tools/evidence/wave_rover_hil_packet_intake.py`。
- 新增测试和 fixtures：覆盖 synthetic pass / fail-closed cases。
- 新增硬件说明：`docs/hardware/wave_rover_hil_packet_intake.md`，引用 `docs/vendor/VENDOR_INDEX.md`、WAVE ROVER `json_cmd.h`、`uart_ctrl.h`、`base_ctrl.py`、`config.yaml`。
- Robot diagnostics 新增 metadata-only consumer 和测试，更新 ROS contract 文档。
- Mobile web 新增 read-only panel、fixture/test 和产品流程文档。
- Product closeout 更新 sprint 文档、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 6. 优先级和验收口径

P0：

- 全链路保留 `software_proof_docker_wave_rover_hil_packet_intake_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- PC gate 不打开串口，不读硬件，不调用 ROS graph，只读 packet 文件和 synthetic fixture。
- 缺失任何必需文件、evidence_ref 不一致、operator report 缺失、unsupported schema、unsafe success language、`delivery_success=true` 或 `primary_actions_enabled=true` 必须 fail closed。

P1：

- Robot diagnostics 和 mobile panel 只显示安全字段，不暴露 raw artifact、local path、serial device、baudrate、raw feedback、traceback、checksum、credential、`/cmd_vel`。
- Mobile Start Delivery、Confirm Dropoff、Cancel gating 不变。
- docs 同步更新，说明本轮不是 `hil_pass`。

验收命令以 `tech-plan.md` 为准；测试只做围栏，不做大范围回归。

## 7. 对应责任 Engineer

- hardware-engineer：PC gate / fixtures / tests / hardware doc。
- robot-software-engineer：Robot diagnostics metadata-only consumer / tests / ROS contract doc。
- full-stack-software-engineer：mobile/web read-only panel / fixture / test / mobile product doc。
- product-okr-owner：closeout docs / OKR / progress log。

## 8. 风险、阻塞和需要补齐的证据链

- 本机没有真实硬件，只有 Docker；synthetic fixture 不能证明真实 WAVE ROVER、UART、feedback interval、`/odom`、`/imu/data`、`/battery` 或 `hil_pass`。
- 真实 HIL packet 仍需现场补齐：`feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`、`operator_hil_report`、同一 `evidence_ref`。
- PR #4 route/elevator field materials 仍需真实门状态、楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record、delivery result。
- PR #5 2D LiDAR / ToF 仍需真实 SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry 材料；本轮不能替代该证据链。
