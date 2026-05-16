# Sprint 2026.05.17_02-03 Hardware Sensor HIL-entry Readiness Review - Side2Side Check

sprint_type: epic

## 1. 用户价值验收

验收结论：通过，证据边界为 Docker/local software proof。

本轮交付让现场支持能在手机只读面板和 diagnostics summary 中看到“传感器 HIL 准入评审”的状态、缺失材料、下一步证据和 owner handoff。它降低的是 HIL-entry 前材料误读风险，不是让普通用户直接操作 HIL 或真实传感器。

产品北极星仍是普通手机用户可用的低成本自主垃圾投递机器人；本轮只是把量产传感器材料链路做得更可追溯。

## 2. OKR 对照

| Objective | 本轮判断 | Product closeout 口径 |
| --- | --- | --- |
| Objective 1 | 保守上调到约 76% | PR #5 相关 2D LiDAR / ToF 材料缺口已从 receipt/config precheck 推进到 HIL-entry readiness review；仍不是真实 HIL。 |
| Objective 2 | 保持约 86% | 不触发 collect/dropoff/cancel/ACK/Nav2/HIL；不证明任务闭环。 |
| Objective 3 | 保持约 86% | 不包含真实 SLAM/Nav2/fixed-route runtime、route completion signal 或 task record。 |
| Objective 4 | 保守上调到约 96% | mobile/web 新增 phone-safe 只读 panel，并保持 Start Delivery / Confirm Dropoff / Cancel gating 不变。 |
| Objective 5 | 保持约 66% | 没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration。 |

## 3. 验收口径核对

- PC gate：已输出 `hardware_sensor_hil_entry_readiness_review` artifact/summary contract，并保持 dependency-free。
- Robot diagnostics：只复制白名单摘要，缺失、unsupported schema、weak boundary、success/control claim 均 fail closed。
- Mobile/web：只展示 readiness status、safe `evidence_ref`、missing materials、next required evidence、owner handoff、boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 控制面：Start Delivery / Confirm Dropoff / Cancel gating 未改变。
- 敏感信息：mobile panel 不展示 raw vendor docs、raw JSON、serial/UART、绝对路径、凭证、complete artifacts。

## 4. 证据链缺口

仍缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。仍缺真实 WAVE ROVER/UART/HIL、真实手机设备、真实 Nav2/fixed-route、真实 route/elevator field pass、真实 dropoff/cancel completion、delivery success 和 Objective 5 external proof。

Product 验收要求下一轮继续把 `software_proof` 与 `hil_pass`、手机/browser proof、field proof、cloud external proof 分开写，不得用本轮 readiness review 替代真实硬件或真实外部材料。
