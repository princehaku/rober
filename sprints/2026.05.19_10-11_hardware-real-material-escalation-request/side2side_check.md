# Sprint 2026.05.19_10-11 Hardware Real Material Escalation Request - Side2Side Check

## sprint_type: epic

Run time: 2026-05-19 10:19 Asia/Shanghai。

## 1. 用户价值和产品北极星

本轮用户价值是把 Objective 1 的真实材料缺口变成现场 owner 可执行的升级请求：需要补哪些 WAVE ROVER/UART/HIL、PR #5 2D LiDAR / ToF、采购/安装/接线/供电/标定/HIL-entry 材料，在哪里看 summary，下一步由谁补证据。

产品北极星不变：低成本 ROS2 送垃圾机器人必须先把硬件事实和证据链做成可追溯、可复核、可交接，再推进真实路线、电梯、手机和云端验证。本轮只证明软件链路能 fail-closed 地表达材料请求。

## 2. OKR 映射和 KR 拆解结果

- Objective 5：不提高。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof。
- Objective 1：只记录 `hardware_real_material_escalation_request` software-proof 可执行性。Hardware gate 能列出真实材料缺口和 owner handoff，但没有真实 WAVE ROVER/UART/HIL、真实 2D LiDAR / ToF 或真实 HIL pass。
- Objective 4：只记录 phone-safe read-only visibility。mobile/web 可以只读展示硬件真实材料升级请求，但不证明真实手机/iPhone/Android、production app 或 PWA prompt/user choice。
- Objective 2 / Objective 3：不提高。本轮不消费 PR #4 route/elevator field material blocker，不证明真实 route/elevator field pass、Nav2/fixed-route、dropoff/cancel completion 或 delivery success。

## 3. 本轮核心抓手验收

| 抓手 | 结果 | 边界 |
| --- | --- | --- |
| Hardware PC gate | `hardware_real_material_escalation_request` / summary 已由 Hardware worker 完成并验证。 | `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。 |
| Robot diagnostics safe alias | `robot_diagnostics_hardware_real_material_escalation_request_summary` 已由 Robot worker 完成并验证。 | 只读 summary，不读 raw artifact、串口、硬件设备或 ROS graph。 |
| mobile/web panel | “硬件真实材料升级请求”只读 panel 已由 Full-Stack worker 完成并验证。 | 不触发 ACK、cursor、diagnostics fetch、Start Delivery、Confirm Dropoff、Cancel 或 robot command。 |
| Product closeout | 本文、`final.md`、`OKR.md` 和 progress log 收口本轮证据。 | 不把软件证明写成真实 HIL、真实 PR #4 field pass 或 O5 external proof。 |

## 4. 优先级和验收口径核对

- P0：真实材料边界清晰。结果：通过；缺真实材料仍列为 `not_proven`，vendor/source 边界保持 `docs/vendor/VENDOR_INDEX.md`。
- P0：控制动作 fail-closed。结果：通过；Robot diagnostics 和 mobile/web 均保持 `primary_actions_enabled=false`。
- P1：手机端能看懂缺口。结果：通过；panel 只读展示 missing materials、next required evidence、owner handoff 和 evidence boundary。
- P1：OKR 不误提进度。结果：通过；Objective 5 不提高，Objective 1 / Objective 4 只记录可执行性与可见性。

## 5. 责任 Engineer 结果

- hardware-engineer：完成 PC gate、tests、interface doc、production hardware boundary 同步。
- robot-software-engineer：完成 diagnostics safe alias、tests、interface doc 同步。
- full-stack-software-engineer：完成 mobile/web panel、fixtures、targeted tests、mobile flow 文档同步。
- product-okr-owner：完成 closeout 文档、OKR 4.1 和 `docs/process/okr_progress_log.md` 更新。

## 6. 风险、阻塞和证据链缺口

- 仍缺真实 WAVE ROVER/UART/HIL、真实 `feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`、operator HIL report。
- 仍缺 PR #5 真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。
- 仍缺真实手机/iPhone/Android device behavior、production app、真实 PWA prompt/user choice。
- 仍缺 PR #4 route/elevator field pass、真实电梯门状态、真实楼层确认、人工协助记录、Nav2/fixed-route runtime log、dropoff/cancel completion 和 delivery success。
- 仍缺 Objective 5 external proof：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover。
