# Sprint 2026.05.20_07-08 Hardware Sensor HIL-entry Callback Intake - Pre Start

sprint_type: epic

## 1. 启动结论

本轮启动 `hardware_sensor_hil_entry_callback_intake` Epic sprint planning。目标是在既有 `hardware_sensor_hil_entry_execution_pack` 之后，补齐真实现场材料执行后的回调入口，让未来现场 owner 能回填 2D LiDAR / ToF SKU/source/receipt、mounting/wiring/power、calibration 和 HIL-entry operator result，而不是继续堆本地 metadata wrapper。

本文件最初用于 planning 启动；implementation worker 已在同一 sprint 完成 Hardware / Robot / Full-Stack 三段落地，Product closeout 已补齐 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。本轮仍只产生 `software_proof_docker_hardware_sensor_hil_entry_callback_intake_gate`，不提高 OKR 百分比。

## 2. 背景证据

- `OKR.md` 4.1 当前最低 Objective 是 Objective 5，约 68%。但仍没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 材料。本轮不应继续做同一 O5 本地 wrapper。
- Objective 1 约 81%。PR #5 review thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / material pending。
- PR #5 review 要求 mandatory sensor assumptions cite local vendor sources and real materials；已发布 GitHub reply 只是 `software_proof` / `not_proven` / `hardware_material_pending`，不能 resolve thread。
- 最近 sprint `2026.05.20_03-04_pr5-vendor-source-review-packet`、`2026.05.20_04-05_pr5-vendor-source-review-reply-dispatch`、`2026.05.20_05-06_pr5-review-reply-publication-closeout`、`2026.05.20_06-07_cloud-command-idempotency-visibility-guard` 均确认：O5/O1 都不能靠本地 proof 提升百分比，下一步需要真实材料或真实材料执行后的回调入口。
- 已有 `hardware_sensor_hil_entry_execution_pack` 只生成执行包，证据见 `sprints/2026.05.17_03-04_hardware-sensor-hil-entry-execution-pack/final.md`、`pc-tools/evidence/hardware_sensor_hil_entry_execution_pack_gate.py`、Robot diagnostics 和 mobile panel。
- `docs/vendor/VENDOR_INDEX.md` 是硬件事实入口。它覆盖 Orange Pi Zero 3、WAVE ROVER、UART newline-delimited JSON、ESP32 firmware/vendor app 和机械参考，但不证明项目 2D LiDAR / ToF 已采购、安装、接线、供电、标定或 HIL pass。

## 3. 用户价值和产品北极星

用户价值：把 PR #5 / Objective 1 的真实硬件材料缺口从“聊天和 reviewer 线程里等待”变成可执行、可回填、可复核的入口。现场 owner 拿到真实材料后，可以按同一 safe `evidence_ref` 提交回调材料，Robot 和手机端只能看见安全摘要，不会把材料回填误写成真实 HIL 或 delivery success。

产品北极星：普通手机用户最终能用低成本 ROS2 小车可靠交付垃圾；硬件假设必须可追溯、可复盘、可 fail-closed。任何缺真实材料的传感器能力都必须保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 4. OKR 映射

- Objective 5：数值最低约 68%，但本轮不针对 O5 completion。原因是 O5 当前缺真实外部材料，继续做本地 wrapper 会重复消费同一 blocker。
- Objective 1：本轮主抓手。为 PR #5 `PRRT_kwDOSWB9286CJ3tX` 和 2D LiDAR / ToF / WAVE ROVER HIL-entry 材料链补 callback intake，但不在 planning 阶段提高进度。
- Objective 4：次要受益。未来 Full-Stack worker 需要把回调入口做成只读手机 panel，让普通用户和现场支持看懂材料状态，同时不改变 Start / Confirm Dropoff / Cancel gating。

## 5. KR 拆解

- KR-A：Hardware PC gate 定义 `hardware_sensor_hil_entry_callback_intake` artifact / summary，消费 execution pack 与 callback materials，白名单接受真实材料引用和 operator result。
- KR-B：Robot diagnostics safe alias 只消费 sanitized summary，屏蔽 raw materials、serial/UART、路径、凭证、checksums 和控制语义。
- KR-C：mobile/web panel 只读展示 callback intake 状态、accepted/missing/rejected materials、safe `evidence_ref`、owner handoff 和 next required evidence。
- KR-D：全链保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`；真实材料到位前不能 resolve `PRRT_kwDOSWB9286CJ3tX`。

## 6. 本轮核心抓手

本轮 planning 的核心抓手是把下一步执行拆成 3 个并行 worker 任务：

- Hardware PC gate：负责 callback intake contract、fixtures/tests 和 product hardware boundary doc sync。
- Robot diagnostics safe alias：负责 metadata-only diagnostics consumer 和 ROS contract doc sync。
- Full-Stack mobile/web panel：负责 phone-safe read-only panel 和 mobile user flow doc sync。

## 7. 风险、阻塞和证据链缺口

- 真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 仍缺。
- 真实 WAVE ROVER/UART/HIL、`T=1001`、`/odom`、`/imu/data`、`/battery`、operator HIL report 仍缺。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false`，不能由本轮 planning 或未来 software proof 自动关闭。
- O5 external proof 仍缺，不能把本轮 callback intake 写成公网 HTTPS/TLS、4G/SIM、OSS/CDN、production DB/queue、worker/cutover 或真实手机/browser proof。
- 本轮已由 implementation worker 完成代码、测试和 docs 同步；Product closeout 只负责 sprint 收口、OKR/progress 同步、集成验收、提交和推送。

## 8. 需要创建或更新的 sprint 文档

- 已创建本文件：`pre_start.md`
- 已创建：`prd.md`
- 已创建：`tech-plan.md`
- 已补齐：`tech-done.md`、`side2side_check.md`、`final.md`
