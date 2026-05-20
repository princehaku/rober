# Hardware Sensor HIL-entry Callback Review Handoff Pre-start

## Sprint Type

- sprint_type: epic
- Sprint: `2026.05.21_00-01_hardware-sensor-hil-entry-callback-review-handoff`
- Theme: `hardware_sensor_hil_entry_callback_review_handoff`
- Planning owner: Product Manager / OKR Owner
- Planned evidence boundary: `software_proof_docker_hardware_sensor_hil_entry_callback_review_handoff_gate`
- Required preserved states: `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`

## 背景证据

`OKR.md` 4.1 当前显示 Objective 5 约 68%，是数字最低 Objective。但本机没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof。最近 `2026.05.20_21-22_cloud-media-degradation-status-guard`、`2026.05.20_22-23_cloud-command-sequence-regression-guard`、`2026.05.20_23-24_cloud-status-stale-guard` 已连续把 O5 做成 Docker/local software guard；本轮不能继续把本地 metadata 当 O5 external proof。

Objective 1 当前约 81%，仍受 PR #5 review thread `PRRT_kwDOSWB9286CJ3tX` 阻塞：live review thread 仍 `is_resolved=false` / material pending，review 要求 mandatory 2D LiDAR / ToF sensor assumptions cite vendor/local sources and provide real materials。PR #6 已 merged，但它是 README docs-only，没有 review threads，也不是 runtime、hardware、HIL、phone 或 O5 proof。

上一轮 `sprints/2026.05.20_20-21_hardware-sensor-hil-entry-callback-review-decision/final.md` 已完成 `hardware_sensor_hil_entry_callback_review_decision` software proof。下一步应进入 review handoff，而不是重复 callback intake 或 review decision。

硬件事实入口已按 `AGENTS.md` 要求核对 `docs/vendor/VENDOR_INDEX.md`。本轮 planning docs 只引用 vendor/local source boundary，不新增 2D LiDAR / ToF SKU、引脚、电压、UART 设备名、波特率、安装尺寸或 HIL 结论。

## 用户价值和产品北极星

用户价值是把“PR #5 真实 2D LiDAR / ToF 材料仍未到位”转成下一轮工程可执行的 review handoff：现场或硬件 owner 能清楚知道缺哪些真实材料，Robot diagnostics 和 mobile/web 只能显示安全摘要，普通手机用户不会看到 raw JSON、ROS topic、串口路径、凭证或误导性成功结论。

产品北极星保持不变：rober 要成为普通手机用户可用、可解释、可复盘的低成本 ROS2 自主垃圾投递机器人。本轮只推进硬件材料证据链的可交接性，不宣称真实底盘控制、真实传感器、真实 HIL 或真实送达。

## 本轮核心抓手

将上一轮 `hardware_sensor_hil_entry_callback_review_decision` 的复核结果升级成 `hardware_sensor_hil_entry_callback_review_handoff`：

- Hardware PC gate：生成 handoff artifact 和 summary，保留缺失材料、owner handoff、next required evidence、source boundary 和 fail-closed 状态。
- Robot diagnostics safe alias：只暴露 scrubbed summary，不触发 task/action/ACK/cursor/Nav2/HIL 或控制路径。
- Full-Stack mobile/web read-only panel：只读展示 handoff 状态，保持 Start Delivery / Confirm Dropoff / Cancel disabled。
- Product closeout：后续只在真实实现与验证完成后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和相关 `docs/`。

## 需要做什么

本 sprint 实现阶段由 3 个并行 owner 推进：

1. Hardware Infra Engineer 负责 PC gate：`hardware_sensor_hil_entry_callback_review_handoff`。
2. Robot Platform Engineer 负责 diagnostics safe alias：`robot_diagnostics_hardware_sensor_hil_entry_callback_review_handoff_summary`。
3. User Touchpoint Full-Stack Engineer 负责 mobile/web 只读 panel：传感器 HIL 回调复核交接。

Product Manager / OKR Owner 后续负责阶段验收和 closeout，不写产品代码、不运行工程实现命令、不替 Engineer 做修复。

## 优先级和验收口径

P0：证据边界必须完整保留：`software_proof_docker_hardware_sensor_hil_entry_callback_review_handoff_gate`、`source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

P0：所有输出必须明确不声明真实 2D LiDAR / ToF、WAVE ROVER/UART/HIL、PR #5 resolved、O5 external proof、real phone/browser、route/elevator field pass 或 delivery success。

P1：PC gate、Robot diagnostics alias、mobile/web panel 的字段必须只支持安全摘要和 owner handoff，不暴露 raw material、raw JSON、ROS topic、serial/UART path、credential、local path、checksum 或完整内部日志。

P1：后续实现必须同步更新相关 `docs/`，并保持代码技术注释为中文且超过 20%。

## 风险、阻塞和需要补齐的证据链

- 真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料仍缺。
- PR #5 thread `PRRT_kwDOSWB9286CJ3tX` 仍不得写成 resolved。
- 真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report 仍缺。
- O5 真实外部材料仍缺：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实 phone/browser external proof。
- 真实 route/elevator field pass、Nav2/fixed-route runtime、dropoff/cancel completion、delivery result 和 delivery success 仍缺。

## 需要创建或更新的 sprint 文档

本 planning-only 开工创建：

- `sprints/2026.05.21_00-01_hardware-sensor-hil-entry-callback-review-handoff/pre_start.md`
- `sprints/2026.05.21_00-01_hardware-sensor-hil-entry-callback-review-handoff/prd.md`
- `sprints/2026.05.21_00-01_hardware-sensor-hil-entry-callback-review-handoff/tech-plan.md`

实现完成后必须继续补齐 Epic 链路：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
