# Sprint 2026.05.16_12-13 Hardware Sensor Procurement Intake - Side-by-Side Check

sprint_type: epic

## 1. PRD 对照

| PRD / Tech Plan 目标 | 实际结果 | 判定 |
| --- | --- | --- |
| 建立 `hardware_sensor_procurement_intake` artifact/gate | 已新增 PC gate 和 tests，schema 对齐为 `trashbot.hardware_sensor_procurement_intake_gate.v1` / `trashbot.hardware_sensor_procurement_intake_summary.v1` | 通过 |
| 缺 SKU/source/procurement/mounting/wiring/calibration/HIL entry 时 fail closed | 缺 intake JSON 返回 exit 2，status 为 `blocked_missing_hardware_sensor_procurement_intake`；summary 保留 `hardware_material_pending`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false` | 通过 |
| `docs/vendor/VENDOR_INDEX.md` 不能冒充 LiDAR/ToF source proof | Hardware worker 读取 vendor index 和 WAVE ROVER vendor files 后确认当前资料不覆盖真实 2D LiDAR / ToF SKU、采购、接线、标定或 HIL | 通过 |
| Robot diagnostics metadata-only consumer | 已接入 summary，保留 no collect/dropoff/cancel、ACK、cursor、Nav2、HIL、completion、delivery result | 通过 |
| mobile phone-safe 只读展示 | 已新增只读 panel / copy / export whitelist，Start / Confirm Dropoff / Cancel fail closed | 通过 |
| Product closeout 后保守更新 OKR | Objective 4 可由约 81% 上调到约 82%；Objective 1/2/3/5 保持不变 | 通过 |

## 2. Evidence Boundary Check

本轮证据是 `software_proof_docker_hardware_sensor_procurement_intake_gate`。

它证明：

- 2D LiDAR / ToF 真实材料缺口可以被 machine-readable intake gate 收敛。
- PC gate、Robot diagnostics 和 mobile read-only panel 对 `hardware_material_pending` / `not_proven` / fail-closed 状态使用同一 summary schema。
- 手机首屏可以安全展示材料待补齐状态，不解锁主操作。

它不证明：

- 真实 2D LiDAR 或 ToF 已选型、采购、收货、安装、接线、标定。
- WAVE ROVER、Orange Pi、UART、真实串口、`T=1001` feedback 或 HIL。
- 真实 route/elevator field pass、Nav2/fixed-route、dropoff/cancel completion 或 delivery success。
- Objective 5 / O5 external proof、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration。

## 3. 用户价值检查

本轮没有直接让普通用户完成一次送垃圾任务；它补的是低成本量产边界的材料入口。用户价值成立的原因是：后续真实硬件采购、安装、接线、标定和 HIL entry 不再散落在口头计划或单个文档里，而是进入同一个 fail-closed gate，并可被 Robot diagnostics 与 mobile 只读展示。

## 4. OKR 检查

- Objective 4：可保守上调。量产硬件材料 intake gate + Robot/mobile read-only consumer 已形成闭环。
- Objective 1：保持约 73%。无真实 WAVE ROVER/UART/HIL/T=1001。
- Objective 2：保持约 78%。无真实电梯、dropoff/cancel completion 或 delivery success。
- Objective 3：保持约 78%。无真实 Nav2/fixed-route runtime log、路线采集或 task record。
- Objective 5：保持约 66%。无外部云/4G/OSS/CDN/DB/queue proof。

## 5. 未完成事项

- 补真实 2D LiDAR / ToF SKU、vendor/source document、采购状态和成本材料。
- 补机械安装、接线、电源预算、线缆固定、frame、标定流程。
- 用同一 `evidence_ref` 衔接后续真实 HIL entry、Nav2/fixed-route 和 route/elevator field materials。
