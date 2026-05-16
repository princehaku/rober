# Sprint 2026.05.16_14-15 Hardware Sensor Procurement Execution Pack - PRD

sprint_type: epic

## 1. 用户价值

当前手机端和 diagnostics 已能显示传感器采购材料缺口，但现场同学仍需要把 review decision 手工转成采购/安装/标定/HIL entry 执行清单。本轮把这一层变成结构化 execution pack，减少材料采集反复和口径漂移。

## 2. OKR 映射

- Objective 4：建立手机用户体验与低成本量产边界。本轮让量产传感器材料从 intake/review 进入可执行材料包。
- Objective 1：为后续真实硬件/HIL entry 准备材料入口，但本轮不证明 WAVE ROVER/UART/HIL。
- Objective 2 / 3：为 route/elevator field pass 需要的 2D LiDAR / ToF 材料提供前置 checklist，但本轮不证明真实 route/elevator。
- Objective 5：本轮不推进；仍等待真实外部云/4G/OSS/CDN/DB/queue 证据。

## 3. 本轮核心抓手

新增 `hardware_sensor_procurement_execution_pack`：

- 输入：上一轮 `hardware_sensor_procurement_review_decision` artifact 或 summary。
- 输出：metadata-only artifact 和 phone-safe summary。
- 状态：缺 review decision 时 `blocked_missing_hardware_sensor_procurement_review_decision`；schema/boundary/unsafe success claim 不支持时 fail closed；材料仍缺时 `hardware_material_pending`；即使形成执行包也保持 `not_proven`。
- 下游：Robot diagnostics 与 mobile/web 只读消费，不打开主操作。

## 4. 验收口径

- PC gate 能生成 artifact/summary，并拒绝 unsupported wrapper、unsafe success/control claim、弱证据边界。
- Robot diagnostics 能从显式 ref 或 summary 构建 metadata-only diagnostics，缺失/错误均 fail closed。
- Mobile 首屏能展示 execution pack 的 owner checklist、material templates、rerun commands 和 safe evidence_ref；copy/export whitelist-only。
- 文档同步更新：`docs/product/production_hardware_boundary.md`、`docs/product/mobile_user_flow.md`、`docs/interfaces/ros_contracts.md`。
- `OKR.md` 和 `docs/process/okr_progress_log.md` 只按 software proof 保守更新。

## 5. 非目标

- 不采购真实硬件。
- 不声明真实 SKU/source/procurement/installation/calibration/HIL entry 通过。
- 不运行真实串口、WAVE ROVER、Nav2/fixed-route、真实手机或公网云验证。
- 不新增大范围测试；只运行围栏命令。
