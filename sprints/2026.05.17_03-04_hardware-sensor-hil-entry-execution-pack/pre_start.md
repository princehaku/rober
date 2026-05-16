# Sprint 2026.05.17_03-04 Hardware Sensor HIL-entry Execution Pack - Pre Start

sprint_type: epic

## 1. 开工依据

本轮目标是 `hardware_sensor_hil_entry_execution_pack`。上一轮 `2026.05.17_02-03_hardware-sensor-hil-entry-readiness-review` 已完成 readiness review，但结论仍是 `hardware_material_pending` 与 `not_proven`：真实 2D LiDAR / ToF SKU、source、receipt、procurement、install、wiring、power、calibration、HIL-entry 材料仍缺。

当前 `OKR.md` 4.1 显示 Objective 5 约 66%，是数值最低 Objective；但本机是 Docker-only 环境，缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration，继续本地 O5 wrapper 会重复消费同一外部证据 blocker。因此本轮从 PR #5 暴露的硬件材料链路继续推进 Objective 1，并同步 Objective 4 的只读用户解释面。

## 2. 用户价值和产品北极星

产品北极星仍是：普通手机用户把垃圾交给低成本 ROS2 小车后，小车能可验证地送达垃圾站/垃圾桶点位，并在失败时给出可理解、可追溯、可支持的解释。

本轮用户价值不是宣称已经装上传感器，而是把“下一次真实 HIL-entry 要准备什么”从工程师口头 checklist 变成 PC/Robot/mobile 三端一致的执行包。现场支持人员可以按同一个 `evidence_ref` 补齐 SKU、来源、收货、安装、接线、供电、标定和 HIL-entry 材料；普通用户手机端只看到只读、不可误触发控制的安全解释。

## 3. 上轮证据与未完成项

已完成：

- `software_proof_docker_hardware_sensor_hil_entry_readiness_review_gate`。
- Hardware PC gate 合成 receipt intake 与 config precheck。
- Robot diagnostics metadata-only consumer。
- mobile/web 只读“传感器 HIL 准入评审” panel。

仍未完成：

- 真实 2D LiDAR / ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry。
- 真实 WAVE ROVER / Orange Pi 串口、UART JSON feedback、`T=1001`、`/odom`、`/imu/data`、`/battery`、`hil_pass`。
- 真实 Nav2/fixed-route、route/elevator field pass、dropoff/cancel completion、delivery success。
- 真实手机/browser、production app、PWA prompt/user choice。
- Objective 5 external proof。

## 4. 本轮核心抓手

把 readiness review 转成 `hardware_sensor_hil_entry_execution_pack`：

- Hardware：生成 fail-closed HIL-entry execution pack artifact/summary，列出 controlled HIL-entry manifest、material templates、first-run/rerun command summary、owner handoff 和 next required evidence。
- Robot：只消费 sanitized summary，暴露 metadata-only diagnostics；不得进入 ACK、cursor、Nav2、collect、dropoff、cancel 或 delivery-control 路径。
- Full-stack：新增 mobile/web 只读 panel，只展示 phone-safe 字段；Start Delivery / Confirm Dropoff / Cancel gating 不变。

## 5. Owner 与协作方式

- Hardware Infra Engineer：主责 `hardware_sensor_hil_entry_execution_pack` PC gate 和 vendor/source boundary。
- Robot Platform Engineer：主责 diagnostics metadata-only summary。
- User Touchpoint Full-Stack Engineer：主责 mobile/web 只读 panel 与 phone-safe copy。
- Product Manager / OKR Owner：本轮只负责 planning docs；工程返回后另派 closeout 更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和进展日志。

## 6. 证据边界

本轮唯一允许的证据边界是 `software_proof_docker_hardware_sensor_hil_entry_execution_pack_gate`。

必须保持：

- `hardware_material_pending`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

不得声称真实 2D LiDAR/ToF、采购、安装、接线、标定、HIL、route/elevator pass、真实手机/browser 或 Objective 5 external proof。

## 7. 需要创建或更新的 sprint 文档

本轮先创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

工程结果返回后再创建或更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
