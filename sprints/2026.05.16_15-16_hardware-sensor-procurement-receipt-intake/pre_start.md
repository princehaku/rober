# Sprint 2026.05.16_15-16 Hardware Sensor Procurement Receipt Intake - Pre Start

sprint_type: epic

## 1. 背景证据

- Live `OKR.md` 4.1 更新时间为 2026-05-16 14:15 Asia/Shanghai：Objective 5 约 66%，是当前数值最低 Objective。
- Objective 5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。当前开发主机只有 Docker，因此按 stop rule 不继续堆 O5 本地 metadata，不把 local software proof 写成 O5 external proof。
- PR #5 评审证据：
  - P1：`docs/product/production_hardware_boundary.md` 曾把 Default Hardware Set 写成不含 2D LiDAR / ToF，但同一文档又把 `monocular + 2D LiDAR + ToF` 写成 mandatory baseline，可能导致 BOM、采购和 bringup 计划漏掉后续必需传感器。
  - P2：新增 mandatory sensor assumptions 需要 `docs/vendor/` 来源；不能把 2D LiDAR / ToF channel、SKU、安装、电源、标定或 HIL 入口写成无来源硬件事实。
  - P2：OKR 最低项叙述曾可能误导 sprint routing；本轮必须在 `tech-plan.md` 写清 Objective 5 最低但外部证据不可本机推进的理由。
- 最近 sprint 链路：
  - `2026.05.16_12-13_hardware-sensor-procurement-intake` 完成 `hardware_sensor_procurement_intake`，能暴露真实 2D LiDAR / ToF SKU、source、采购、安装、接线、标定和 HIL entry 缺口。
  - `2026.05.16_13-14_hardware-sensor-procurement-review-decision` 完成 `hardware_sensor_procurement_review_decision`，把 intake 缺口转成 review decision、blockers、next_required_evidence、owner_handoff 和 rerun_commands。
  - `2026.05.16_14-15_hardware-sensor-procurement-execution-pack` 完成 `hardware_sensor_procurement_execution_pack`，把 review decision 转成 material templates、owner handoff、safe rerun command、blocked reason 和 safe `evidence_ref`。
- 以上三轮仍没有真实 2D LiDAR / ToF SKU、source、procurement、receipt、install、wiring、power、calibration 或 HIL entry 材料；也没有真实 WAVE ROVER/UART/HIL、真实 route/elevator field pass、真实手机/browser、dropoff/cancel completion 或 delivery success。

## 2. 本轮目标

本轮启动 `hardware_sensor_procurement_receipt_intake`，目标不是声明真实采购完成，而是建立未来真实采购与安装回填材料的接收、校验、分发和 closeout 口径。

`hardware_sensor_procurement_receipt_intake` 必须能接收并校验以下材料的脱敏摘要或引用：

- receipt / purchase order / invoice / payment status。
- vendor / source document / SKU / quantity / unit cost / total cost。
- install evidence / mounting note / wiring note / power budget note。
- calibration evidence / calibration plan / calibration result placeholder。
- HIL entry placeholder / HIL entry status / blocked reason。
- safe `evidence_ref`，用于 PC gate、Robot diagnostics、mobile read-only panel 和 Product closeout 对齐。

## 3. 用户价值和产品北极星

产品北极星：让普通用户最终能在低成本量产硬件边界内完成一次可解释、可恢复、可验收的送垃圾任务。

用户价值：现场或采购同学拿到真实传感器材料后，不需要在聊天或散落文档里人工解释“这张单据能不能推进 2D LiDAR / ToF 上车”。系统应能把回填材料转成统一的 receipt intake summary，Robot diagnostics 和手机端只读展示同一证据边界，并明确下一步还缺什么。

## 4. Owner

- Hardware Infra Engineer：PC gate 主责，建立 receipt intake artifact / summary 和 fail-closed 校验。
- Robot Platform Engineer：Robot diagnostics metadata-only consumer 主责，只读消费 receipt intake summary。
- User Touchpoint Full-Stack Engineer：mobile/web read-only panel 主责，展示 receipt intake 状态和 phone-safe copy。
- Product Manager / OKR Owner：closeout 主责，验收证据边界、更新 sprint 留档、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 5. 并行启动要求

本轮是 Epic sprint，跨 Hardware / Robot / Full-stack / Product 四个 owner。实现阶段必须在同一轮并行启动 3 个 Engineer worker，并保留 Product closeout：

- Task A：Hardware PC gate。
- Task B：Robot diagnostics metadata-only consumer。
- Task C：Full-stack mobile read-only panel。
- Task D：Product closeout。

任务边界互不重叠；除接口字段名需要按 Hardware summary schema 对齐外，不共享写同一产品代码文件。Robot 和 Full-stack 必须以 metadata-only / read-only consumer 方式接入，不打开主操作。

## 6. 风险边界

- 本轮只允许形成 `software_proof_docker_hardware_sensor_procurement_receipt_intake_gate`；不得写成真实采购、真实收货、真实安装、真实接线、真实标定、真实 HIL entry、真实 route/elevator field pass、真实手机通过、delivery success 或 Objective 5 external proof。
- `delivery_success=false`、`primary_actions_enabled=false`、`not_proven` 必须贯穿 PC gate、Robot diagnostics、mobile panel 和 Product closeout。
- Start / Confirm Dropoff / Cancel / primary actions 必须继续 fail closed。
- 硬件相关字段必须从 `docs/vendor/VENDOR_INDEX.md` 及其本地 vendor 指向资料建立 source boundary；当前 vendor 资料仍不证明项目已采购、安装、接线或标定真实 2D LiDAR / ToF。
- 如果实现 worker 发现 receipt intake 只能重复上一轮 execution pack，不能接收真实 receipt/source/install/wiring/power/calibration/HIL-entry 回填材料，应停止扩大实现并回报。

## 7. 需要创建或更新的 sprint 文档

- 本轮 planning：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 实现完成后必须继续补齐：`tech-done.md`、`side2side_check.md`、`final.md`。
- Product closeout 还需更新：`OKR.md`、`docs/process/okr_progress_log.md`。
