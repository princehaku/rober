# Sprint 2026.05.16_13-14 Hardware Sensor Procurement Review Decision - PRD

## 1. 产品问题

PR #5 已把电梯 assisted delivery、2D LiDAR / ToF 硬件基线和参数化 sensor configs 写入主线。11-12 sprint 修复了硬件基线矛盾和 schema handoff drift；12-13 sprint 新增 `hardware_sensor_procurement_intake`，把真实 2D LiDAR / ToF SKU、source、采购、安装、接线、标定、HIL entry 缺口 fail closed 暴露出来。

当前问题是：intake 只能说明“缺什么”，还没有把缺口转成采购评审可执行决策。没有 review decision 时，Hardware 不知道下一份材料优先补什么，Robot / mobile 只能展示材料待补齐，Product closeout 也缺少判断“是否可以进入采购评审 / 是否继续 blocked / 补材料后重跑什么”的统一证据。

## 2. 用户价值和产品北极星

北极星：让普通手机用户最终可以把垃圾交给小车，并由低成本、可验证的传感器组合支撑固定路线、近场安全和电梯 assisted delivery，而不是靠未采购、未接线、未标定的硬件假设推进。

本 PRD 的用户价值：

- 对 CEO / Product：从“材料缺口列表”升级为“采购评审决策和下一步证据清单”。
- 对 Hardware：明确 SKU/source/procurement/mounting/wiring/power/calibration/HIL entry 哪些 blocker 阻塞采购评审，以及谁补什么。
- 对 Robot / Full-stack：继续只读展示 safe summary，确保用户和支持人员不会误以为已经可发车、已采购、已 HIL 或已 delivery success。
- 对后续现场验证：为真实 2D LiDAR / ToF 材料进入 Nav2/SLAM、ToF safety、route/elevator field material 和 HIL entry 建立可重跑链路。

## 3. OKR 映射

| Objective | 映射 | 本轮口径 |
| --- | --- | --- |
| Objective 4 | 主线：低成本量产硬件边界和手机用户体验 | 把 sensor procurement intake 转成 review decision，支持量产材料评审与手机只读状态 |
| Objective 1 | 支撑：可信硬件协议和 HIL entry | review decision 可列出硬件材料进入 HIL 前的 blocker，但不宣称 WAVE ROVER/UART/HIL 通过 |
| Objective 2 | 支撑：电梯 assisted delivery 必达闭环 | 传感器采购评审支撑电梯/近场安全材料链，但不宣称真实电梯或 delivery success |
| Objective 3 | 支撑：Nav2/SLAM 和固定路线 | 2D LiDAR 只在采购、安装、标定和 HIL entry 后进入 Nav2/SLAM 主链 |
| Objective 5 | 非本轮主线 | O5 约 66% 最低，但 Docker-only 主机缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration |

## 4. KR 拆解

### KR1 - Review Decision Artifact

新增 `hardware_sensor_procurement_review_decision` artifact，至少包含：

- `schema=trashbot.hardware_sensor_procurement_review_decision.v1`
- `source_intake_schema=trashbot.hardware_sensor_procurement_intake_summary.v1` 或兼容 intake artifact reference
- `evidence_boundary=software_proof_docker_hardware_sensor_procurement_review_decision_gate`
- `review_decision`
- `blockers`
- `next_required_evidence`
- `owner_handoff`
- `rerun_commands`
- `hardware_material_pending`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `not_proven`

### KR2 - Decision Rules

任何以下情况必须保持 blocked / not proven：

- intake summary 缺失、schema unsupported、或 `evidence_boundary` 不是 software proof / metadata-only 口径。
- 2D LiDAR / ToF SKU 为空、placeholder、或无 vendor/source document。
- 采购状态缺失，或无法区分 not_selected / selected_not_ordered / ordered / received / installed / calibrated / hil_entry_ready。
- mounting / wiring / power / calibration / HIL entry 任一关键材料缺失。
- artifact 或 summary 出现 `delivery_success=true`、`primary_actions_enabled=true`、field pass、HIL pass、已采购通过、已可发车或 Objective 5 external proof 文案。

允许的非成功决策：

- `blocked_missing_hardware_sensor_procurement_intake`
- `blocked_unsupported_hardware_sensor_procurement_intake`
- `blocked_missing_procurement_materials`
- `blocked_missing_mounting_wiring_calibration`
- `ready_for_procurement_review_not_proven`

### KR3 - Hardware Owner Handoff

Hardware 输出必须足够执行：

- 每个 blocker 指定 owner：Hardware / Robot / Full-stack / Product closeout。
- 每个 blocker 指定 next_required_evidence：具体材料名称和验收条件。
- 每个 blocker 指定 rerun_commands：补材料后应重跑的 PC gate、diagnostics、mobile 和 closeout `rg` / diff check。
- 明确 `docs/vendor/VENDOR_INDEX.md` 只证明当前 vendor coverage，不证明 LiDAR/ToF source/procurement。

### KR4 - Robot Diagnostics Read-Only Consumer

Robot diagnostics 可以消费 sanitized review summary：

- 展示 review decision、safe `evidence_ref`、blockers、next_required_evidence、owner_handoff、rerun_commands。
- 保持 metadata-only：不触发 collect/dropoff/cancel、ACK、cursor、Nav2、HIL、dropoff/cancel completion 或 delivery result。
- 缺 summary 或 unsupported schema 时 fail closed 为 `blocked_missing_hardware_sensor_procurement_review_decision` 或兼容 blocked reason。
- 不透传 raw artifact、raw ROS topic、raw JSON、serial/UART 细节、baudrate、hardware path、credential、checksum、完整供应商资料或 Objective 5 外部材料。

### KR5 - Mobile Phone-Safe Summary

mobile/web 可新增只读 panel 或扩展现有硬件材料 panel：

- 展示 procurement review decision、缺失材料分类、owner handoff、下一步重跑命令摘要、safe `evidence_ref`。
- 保持 phone-safe 中文优先 copy，不出现 raw ROS topic、raw JSON、串口、baudrate、完整 artifact、凭证、DB/queue/OSS/CDN 材料或硬件调试细节。
- Start / Confirm Dropoff / Cancel gating 不因该 summary 改变。
- 不出现“已通过”“可发车”“已采购”“已 HIL”“送达成功”等成功文案。

### KR6 - Product Closeout Discipline

Product closeout 只有在 Engineer 完成实现、验证并更新 `tech-done.md`、`side2side_check.md`、`final.md` 后，才能判断是否更新 `OKR.md`。

允许更新：

- Objective 4：如果 review decision gate、Robot/mobile 只读消费和 docs 同步完整，可保守记录量产硬件材料评审链改善。

禁止更新：

- Objective 1 HIL、Objective 2 delivery success、Objective 3 real Nav2/fixed-route、Objective 5 external proof，除非有真实硬件/现场/外部云证据。

## 5. 范围边界

### In Scope

- 建立 `hardware_sensor_procurement_review_decision` schema/gate/summary。
- 从 `hardware_sensor_procurement_intake` summary 或 artifact 推导 procurement review decision。
- 输出 blocker、next_required_evidence、owner_handoff、rerun_commands。
- Robot diagnostics metadata-only 消费。
- mobile/web phone-safe 只读消费。
- 后续实施完成后同步 docs、sprint 留档、OKR closeout。

### Out Of Scope

- 采购真实硬件。
- 接线、机械安装、标定或真实 HIL。
- 修改 WAVE ROVER、Orange Pi、UART launch 默认。
- 修改 Start / Confirm Dropoff / Cancel 控制 gating。
- 声明 Objective 5 external proof。
- 声明 delivery success、route/elevator field pass、Nav2/fixed-route field run 或真实手机验收。
- 在本计划阶段修改产品代码、测试代码、硬件配置、`OKR.md` 或 closeout docs。

## 6. 优先级和验收口径

P0：

- gate 能读取 intake summary / artifact，并对 missing / unsupported / placeholder / incomplete material fail closed。
- 输出必须包含 `hardware_material_pending`、`not_proven`、`software_proof`、`delivery_success=false`、`primary_actions_enabled=false`。
- 输出必须包含 blocker、next_required_evidence、owner_handoff、rerun_commands。
- `docs/vendor/VENDOR_INDEX.md` 只能作为 vendor coverage boundary，不能作为 LiDAR/ToF source proof。

P1：

- Robot diagnostics 只读消费 review summary，metadata-only fence 通过。
- mobile/web 只读展示 phone-safe review decision，copy/export whitelist-only。
- docs/product、docs/interfaces、docs/process 或相关 sprint closeout 在实施后同步更新。

P2：

- 后续真实材料到位后，可让 review decision 从 blocked 进入 `ready_for_procurement_review_not_proven`，但仍不得写成 HIL、field pass、delivery success 或 O5 external proof。

## 7. 对应责任 Engineer

- 主责：`hardware-engineer`，负责 review decision gate、blocker 分类、next_required_evidence、owner_handoff、rerun_commands 和硬件/source/procurement/material boundary。
- 协作：`robot-software-engineer`，负责 diagnostics metadata-only review summary consumer。
- 协作：`full-stack-software-engineer`，负责 mobile phone-safe read-only review decision surface。
- 收口：`product-okr-owner`，负责 sprint chain、OKR boundary、side-by-side check 和 final。

本轮不需要 `autonomy-engineer` 独立实现文件。Nav2/SLAM/ToF responsibility split 已在 11-12 / 12-13 sprint 与 `docs/product/production_hardware_boundary.md` 中形成边界；本轮只把材料评审决策闭环推进到 Hardware -> Robot -> Full-stack -> Product closeout。

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

计划阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实施阶段必须补齐：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

本 PRD 不修改 `OKR.md`。OKR 更新必须等实现和验证证据进入 final 后再做。
