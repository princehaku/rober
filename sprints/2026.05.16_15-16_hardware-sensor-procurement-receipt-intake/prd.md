# Sprint 2026.05.16_15-16 Hardware Sensor Procurement Receipt Intake - PRD

sprint_type: epic

## 1. 用户价值和产品北极星

产品北极星：小车以低成本、可量产、可诊断的硬件边界完成可解释的送垃圾任务；每一次硬件升级都必须能被采购、安装、标定和 HIL 证据追溯。

当前用户价值：真实 2D LiDAR / ToF 材料即使未来到位，也需要一个统一入口判断“材料是否足以进入安装、标定或 HIL”。`hardware_sensor_procurement_receipt_intake` 把 receipt/source/vendor/SKU/cost/install/wiring/power/calibration/HIL-entry 回填变成可校验 artifact 和 phone-safe summary，避免再次出现 PR #5 暴露的 mandatory sensor baseline 与默认硬件/来源口径打架。

## 2. OKR 映射

- Objective 4：主目标。KR8/KR9 需要把 2D LiDAR / ToF 作为量产硬件约束和可扩展感知 contract 管住；本轮建立真实 receipt / install / calibration / HIL-entry 材料回填入口。
- Objective 1：受益目标。未来真实传感器上车、接线、电源和 HIL entry 可进入硬件 evidence chain；本轮不证明 WAVE ROVER、UART、Orange Pi 串口或 HIL。
- Objective 2 / Objective 3：受益目标。真实 route/elevator field pass、Nav2/fixed-route 和 task record 需要 2D LiDAR / ToF 前置材料；本轮只提供材料 intake，不证明 field pass 或 delivery success。
- Objective 5：不推进。Live `OKR.md` 4.1 Objective 5 约 66% 最低，但本机只有 Docker，缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、worker/migration；按 stop rule 不继续堆 O5 local metadata。

## 3. KR 拆解或更新

- KR4.8 / KR4.9：新增 receipt intake 入口，要求 2D LiDAR / ToF SKU/source/procurement/receipt/install/wiring/power/calibration/HIL-entry 材料可被结构化接收；仍保持 `hardware_material_pending` 和 `not_proven`，直到真实材料齐备并进入后续 HIL。
- KR1.5：receipt intake 的 serial/UART/WAVE ROVER/Orange Pi 相关字段只能作为未来 HIL entry placeholder，不得写成真实串口或底盘反馈证据。
- KR2.6 / KR2.7：receipt intake 可作为后续电梯 assisted delivery 感知材料前置，不得写成真实电梯、目标楼层确认、人工协助记录或 delivery result。
- KR3.1 / KR3.4：receipt intake 可作为后续 SLAM/Nav2/fixed-route 传感器材料前置，不得写成真实路线采集或 Nav2/fixed-route 实跑。

## 4. 本轮核心抓手

新增能力：`hardware_sensor_procurement_receipt_intake`。

输入：

- 上一轮 `hardware_sensor_procurement_execution_pack` artifact 或 summary。
- 未来真实 receipt/source/vendor/SKU/cost/install/wiring/power/calibration/HIL-entry 材料的脱敏 JSON 或路径引用。

输出：

- PC artifact schema：`trashbot.hardware_sensor_procurement_receipt_intake.v1`。
- Summary schema：`trashbot.hardware_sensor_procurement_receipt_intake_summary.v1`。
- Evidence boundary：`software_proof_docker_hardware_sensor_procurement_receipt_intake_gate`。
- 状态字段：`receipt_intake_status`、`material_status`、`source_boundary`、`missing_materials`、`accepted_materials`、`rejected_materials`、`blocked_reason`、`next_required_evidence`、`owner_handoff`、`safe_evidence_ref`。

## 5. 需要做什么

- Hardware PC gate：实现 receipt intake gate，能校验 execution pack 来源、receipt/source/SKU/cost/install/wiring/power/calibration/HIL-entry 字段、unsafe copy 和弱边界。
- Robot diagnostics consumer：只读消费 receipt intake summary，缺失/unsupported/unsafe 时 fail closed；不触发 collect/dropoff/cancel、ACK、cursor、Nav2、HIL 或 delivery result。
- Full-stack mobile panel：在 mobile/web 首屏新增只读“传感器采购收货回填” panel，展示 receipt intake 状态、缺失材料、下一步证据和 safe copy。
- Product closeout：核对证据边界、更新 sprint closeout、`OKR.md` 和进度日志；如只完成软件 proof，最多按 Objective 4 材料链保守描述，不提升硬件/HIL/O5。

## 6. 优先级和验收口径

P0 验收：

- 所有输出必须包含 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 缺 execution pack、unsupported schema、缺 receipt/source/SKU、unsafe success/control claim、credential/path/raw hardware leakage 时必须 fail closed。
- Robot diagnostics 与 mobile panel 均 metadata-only / read-only，不改变 Start / Confirm Dropoff / Cancel gating。
- 文档必须同步更新 `docs/product/production_hardware_boundary.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md`。

P1 验收：

- Receipt intake 能区分材料“已接收但未证明”“缺材料”“unsupported wrapper”“unsafe copy”。
- Phone-safe copy 只包含 allowlisted 字段，不包含 raw JSON、ROS topic、串口细节、凭证、checksum、完整本机路径或成功/放行动作措辞。
- Product closeout 明确 Objective 5 仍未推进，并回顾 PR #5 的 sensor baseline / vendor source / routing 风险是否被本轮规划约束覆盖。

## 7. 对应责任 Engineer

- Hardware Infra Engineer：Task A，PC gate 和 `docs/product/production_hardware_boundary.md`。
- Robot Platform Engineer：Task B，operator diagnostics 和 `docs/interfaces/ros_contracts.md`。
- User Touchpoint Full-Stack Engineer：Task C，mobile/web panel 和 `docs/product/mobile_user_flow.md`。
- Product Manager / OKR Owner：Task D，sprint closeout、OKR 进度和证据边界验收。

## 8. 非目标

- 不采购真实硬件。
- 不声明真实 receipt、source、SKU、安装、接线、电源、标定或 HIL entry 已通过。
- 不运行真实串口、WAVE ROVER、Nav2/fixed-route、真实手机或公网云验证。
- 不推进 Objective 5 external proof。
- 不新增大范围回归测试；只跑各 owner 的围栏命令。

## 9. 风险、阻塞和需要补齐的证据链

- 当前仍没有真实 2D LiDAR / ToF receipt、source document、SKU、成本、安装照片、接线图、电源预算、标定结果或 HIL entry。
- 当前仍没有真实 WAVE ROVER/UART/HIL、真实 route/elevator field pass、真实手机/browser、dropoff/cancel completion 或 delivery success。
- 当前仍没有 Objective 5 所需真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、worker/migration。
- 实现阶段必须避免把 receipt intake 写成 procurement completion；receipt intake 是材料接收和校验入口，不是采购履约证明。
