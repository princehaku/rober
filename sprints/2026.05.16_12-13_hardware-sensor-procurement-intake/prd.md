# Sprint 2026.05.16_12-13 Hardware Sensor Procurement Intake - PRD

## 1. 产品问题

PR #5 已把 2D LiDAR / ToF 纳入产品目标硬件边界，但当前仓库只有 `hardware_baseline_review` 的 software proof。真实 2D LiDAR / ToF 的 SKU、vendor/source document、采购状态、机械安装、接线、标定和 HIL entry evidence 仍没有进入统一材料入口。

如果不先建立 fail-closed intake，后续 Robot / Autonomy / mobile 很容易把“目标硬件”误读成“已采购、已安装、已标定、已可用于 Nav2/SLAM 或安全闭环”。这会直接污染 Objective 1/2/3/4 的证据边界，并重复上一轮 PR #5 review 提到的 P2 source/procurement material gap。

## 2. 用户价值和产品北极星

北极星：让普通手机用户最终能把垃圾交给小车，并看到低成本、可解释、可复盘的送达过程；硬件传感器只是提高送达成功率和安全性的手段，不能靠无来源假设进入主链。

本 PRD 的用户价值：

- 对 CEO / Product：知道哪些真实硬件材料还没有补齐，不能用 `software_proof` 替代真实采购和 HIL。
- 对 Hardware：有明确采购、source、安装、接线、标定、HIL entry 清单。
- 对 Robot / Autonomy：在没有真实材料前 fail closed，不把 2D LiDAR / ToF 当作可运行传感器。
- 对 Full-stack / 手机用户：只看到安全、可理解的“材料待补齐”状态，不暴露 raw ROS/hardware details，不误导用户发车。

## 3. OKR 映射

| Objective | 映射 | 本轮口径 |
| --- | --- | --- |
| Objective 4 | 主线：低成本量产硬件边界和手机用户体验 | 建立真实 sensor procurement intake，支持后续量产硬件验收 |
| Objective 1 | 支撑：可信硬件协议和 HIL entry | intake 可列出接线、电源、串口/接口、HIL entry 需求，但不宣称 HIL |
| Objective 2 | 支撑：电梯 assisted delivery 必达闭环 | 2D LiDAR / ToF 材料链为后续电梯/近场安全证据做准备，不宣称 delivery success |
| Objective 3 | 支撑：Nav2/SLAM 和固定路线 | 2D LiDAR role 只在采购、安装、标定后进入 Nav2/SLAM 主链 |
| Objective 5 | 非本轮主线 | O5 约 66% 最低，但 Docker-only 主机缺真实外部云/4G/OSS/CDN/DB/queue 证据 |

## 4. KR 拆解

### KR1 - Intake Artifact

新增 `hardware_sensor_procurement_intake` artifact，至少包含：

- `schema=trashbot.hardware_sensor_procurement_intake.v1`
- `evidence_boundary=software_proof_docker_hardware_sensor_procurement_intake_gate`
- `source_documents`：真实 vendor/source document 列表；缺失时明确为空并 blocked
- `sensors`：2D LiDAR、ToF safety ring、monocular camera 的 role/state
- `procurement_status`：not_selected / selected_not_ordered / ordered / received / installed / calibrated / hil_entry_ready
- `mounting_plan`：安装位置、机械参考、固定方式、视场遮挡风险
- `wiring_plan`：接口、电源、线缆固定、host 连接方式
- `calibration_plan`：frame、外参、近场阈值、Nav2/SLAM 或 safety gate 接入条件
- `hil_entry_checklist`：进入真实 HIL 前必须具备的材料
- `delivery_success=false`
- `primary_actions_enabled=false`
- `not_proven=true`

### KR2 - Fail-Closed Rules

任何以下情况必须 fail closed：

- SKU 为空或使用 placeholder。
- vendor/source document 缺失，或只引用 `docs/vendor/VENDOR_INDEX.md` 作为 2D LiDAR / ToF 来源。
- ToF channel count 没有来源或验收解释。
- 机械安装、接线、电源预算、标定、HIL entry 任一关键字段缺失。
- artifact 或 summary 出现 `delivery_success=true`、`primary_actions_enabled=true`、field pass、HIL pass 或真实采购通过文案。

### KR3 - Robot Diagnostics Read-Only Consumer

Robot diagnostics 可以消费 sanitized summary：

- 展示 `hardware_material_pending`、blocked reason、missing materials、safe `evidence_ref`。
- 保持 metadata-only：不触发 collect/dropoff/cancel、ACK、cursor、Nav2、HIL、dropoff/cancel completion 或 delivery result。
- 不透传 raw artifact、raw ROS topic、raw JSON、serial/UART 细节、baudrate、hardware path、credential、checksum 或完整供应商资料。

### KR4 - Mobile Phone-Safe Summary

mobile/web 可新增只读 panel 或扩展现有硬件基线 panel：

- 展示 procurement/intake status、缺失材料、下一步 owner、safe copy 和 recovery hint。
- 保持 phone-safe 中文优先 copy，不出现 raw ROS topic、raw JSON、串口、baudrate、完整 artifact、凭证、DB/queue/OSS/CDN 材料或硬件调试细节。
- Start / Confirm Dropoff / Cancel gating 不因该 summary 改变。

### KR5 - OKR Closeout Discipline

只有在 Engineer 完成实现、验证并更新 `tech-done.md`、`side2side_check.md`、`final.md` 后，Product 才能判断是否更新 `OKR.md`。

允许更新：

- Objective 4：如果 intake gate、Robot/mobile 只读消费和 docs 同步完整，可保守记录量产硬件材料链改善。

禁止更新：

- Objective 1 HIL、Objective 2 delivery success、Objective 3 real Nav2/fixed-route、Objective 5 external proof，除非有真实硬件/现场/外部云证据。

## 5. 范围边界

### In Scope

- 建立 `hardware_sensor_procurement_intake` 的 schema/gate/summary。
- 明确 2D LiDAR / ToF 的 SKU/source/procurement/mounting/wiring/calibration/HIL entry 字段。
- Robot diagnostics metadata-only 消费。
- mobile/web phone-safe 只读消费。
- 同步 docs 和 sprint 留档。

### Out Of Scope

- 采购真实硬件。
- 接线、机械安装、标定或真实 HIL。
- 修改 WAVE ROVER、Orange Pi、UART launch 默认。
- 修改 Start / Confirm Dropoff / Cancel 控制 gating。
- 声明 Objective 5 external proof。
- 声明 delivery success、route/elevator field pass、Nav2/fixed-route field run 或真实手机验收。

## 6. 优先级和验收口径

P0：

- gate 对缺真实 SKU/source/procurement/installation/wiring/calibration/HIL entry fail closed。
- 输出必须包含 `hardware_material_pending`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- `docs/vendor/VENDOR_INDEX.md` 只能作为 vendor coverage boundary，不能作为 LiDAR/ToF source proof。

P1：

- Robot diagnostics 只读消费 summary，metadata-only fence 通过。
- mobile/web 只读展示 phone-safe summary，copy/export whitelist-only。
- docs/product 和 docs/interfaces 同步更新。

P2：

- 后续真实材料到位后，可以扩展 intake 为 selected/ordered/received/installed/calibrated/hil_entry_ready 的状态流转，但每一步仍需证据引用。

## 7. 责任 Engineer

- 主责：`hardware-engineer`，负责 intake artifact 字段和硬件/source/procurement/material boundary。
- 协作：`robot-software-engineer`，负责 diagnostics metadata-only consumer。
- 协作：`autonomy-engineer`，负责 2D LiDAR / ToF / monocular responsibility split 和 PC evidence gate。
- 协作：`full-stack-software-engineer`，负责 mobile phone-safe read-only surface。
- 收口：`product-okr-owner`，负责 sprint chain、OKR boundary、side-by-side check 和 final。

## 8. 风险、阻塞和需要补齐的证据链

- 真实 2D LiDAR SKU/source document：缺。
- 真实 ToF SKU/channel source document：缺。
- 采购状态、订单/收货证据：缺。
- 机械安装图、WAVE ROVER mounting reference 对齐：缺。
- 接线、电源预算、线缆固定、接口选择：缺。
- 标定和 frame 设置：缺。
- HIL entry checklist 和真实串口/运行证据：缺。
- O5 external proof：仍缺真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。

## 9. 需要创建或更新的 sprint 文档

计划阶段已创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实施阶段必须补齐：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

本 PRD 不修改 `OKR.md`。OKR 更新必须等实现和验证证据进入 final 后再做。
