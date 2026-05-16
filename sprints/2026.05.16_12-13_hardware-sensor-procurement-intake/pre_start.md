# Sprint 2026.05.16_12-13 Hardware Sensor Procurement Intake - Pre Start

sprint_type: epic

## 1. 启动原因

本轮启动 `hardware_sensor_procurement_intake`。目标不是继续堆本地 Objective 5 / O5 metadata，而是把真实 2D LiDAR / ToF 材料缺口收敛成一个 fail-closed intake artifact，并让 Robot diagnostics / mobile 只读消费该 artifact 的安全摘要。

当前 live `OKR.md` 4.1 显示 Objective 5 约 66%，为数值最低 Objective；但本机只有 Docker，仍缺真实 HTTPS/TLS、公网入口、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。继续本地 O5 metadata 不会补齐真实外部证据。

上一轮已完成 sprint：`sprints/2026.05.16_11-12_hardware-baseline-review-gate/`，commit `440f553 Add hardware baseline review gate`。该 sprint 修复 PR #5 的 P1：`Default Hardware Set` 与 mandatory sensor baseline 矛盾，并新增 `hardware_baseline_review` PC/Robot/mobile software proof。剩余 P2 缺口仍是：2D LiDAR / ToF SKU、vendor/source document、采购状态、机械安装、接线、标定和 HIL entry evidence。

## 2. 用户价值和产品北极星

产品北极星：普通手机用户把垃圾交给小车后，小车能低成本、可解释、可复盘地完成固定路线送达，而不是依赖未采购、未接线、未标定的传感器假设。

本轮用户价值：

- 把“未来要上 2D LiDAR / ToF”的口头目标变成可审查的材料 intake gate。
- 让硬件、Robot、Autonomy、Full-stack 对同一材料状态说同一种话：`hardware_material_pending`、`not_proven`、`software_proof`，不把计划或 vendor 索引写成真实硬件证明。
- 为后续真实采购、机械安装、接线、标定、Nav2/SLAM、电梯 evidence chain 和 HIL entry 建立最小材料清单。

## 3. 背景证据

- `OKR.md` 4.1：Objective 5 约 66% 最低，但 O5 下一步需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration；当前 Docker-only 环境不能补齐。
- `OKR.md` 6：若 O5 外部材料不可用，当前最高可行动作包含真实 2D LiDAR / ToF SKU/vendor/procurement/installation/HIL-entry 材料。
- `sprints/2026.05.16_11-12_hardware-baseline-review-gate/final.md`：`hardware_baseline_review` 只是 `software_proof_docker_hardware_baseline_review_gate`，不证明真实 2D LiDAR、真实 ToF、WAVE ROVER/UART/HIL、Nav2/fixed-route 或 delivery success。
- PR #5 Codex review 证据：P1 要求 default hardware set 与 mandatory baseline 对齐，已修复；P2 要求 sensor mix / ToF channel count 引用 `docs/vendor/` 本地来源，下一步应深入 source/procurement material gap。
- `docs/vendor/VENDOR_INDEX.md` 当前覆盖 Orange Pi Zero 3、WAVE ROVER、UART JSON、WAVE ROVER mechanical refs、vendor camera/tutorial material；不证明 2D LiDAR / ToF 已采购、接线、标定或 HIL。
- `docs/product/production_hardware_boundary.md` 当前已将 2D LiDAR / ToF 写为 Product Target / Procurement Validation Pending，并保留 `hardware_material_pending`、`not_proven`。

## 4. OKR 映射

- Objective 4：主目标。补齐低成本量产边界中的真实传感器材料 intake，让默认硬件集、目标 sensor baseline、手机只读状态和采购验证边界一致。
- Objective 1：支撑目标。真实硬件材料是后续 WAVE ROVER / Orange Pi / UART / HIL entry 的前置证据，但本轮不宣称 HIL。
- Objective 2 / Objective 3：支撑目标。2D LiDAR / ToF 材料链将支撑 route/elevator field pass、Nav2/SLAM 和 same `evidence_ref` 现场复账，但本轮不宣称 route/elevator field pass 或 delivery success。
- Objective 5：不作为本轮主线。O5 数值最低，但当前真实外部云/4G/OSS/CDN/DB/queue 证据不可得；本轮明确停止重复消费 Docker-only O5 blocker。

## 5. KR 拆解或更新

- KR-A：定义 `hardware_sensor_procurement_intake` artifact 的必填字段：sensor role、target SKU、vendor/source document、procurement status、cost、mounting plan、wiring plan、power budget、calibration plan、HIL entry checklist、evidence boundary。
- KR-B：gate 对缺失或占位材料 fail closed，输出 `hardware_material_pending`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- KR-C：Robot diagnostics 只读消费 intake summary，不能触发 collect/dropoff/cancel、ACK、cursor、Nav2、HIL 或 delivery result。
- KR-D：mobile/web 只读展示 phone-safe summary，不能暴露 raw ROS topic、raw JSON、serial/UART 细节、完整 artifact、凭证、checksum 或硬件 jargon；Start / Confirm Dropoff / Cancel gating 不改变。
- KR-E：Product closeout 只在真实材料链进展足够时更新 OKR.md；不得把 software proof、docs/vendor/VENDOR_INDEX.md 或 intake summary 写成真实硬件采购/HIL。

## 6. 本轮核心抓手

核心抓手是一个可执行 fail-closed gate：`hardware_sensor_procurement_intake`。

它把“2D LiDAR / ToF 未来要买什么、来源在哪、是否采购、怎么安装、怎么接线、怎么标定、何时进入 HIL”的材料状态统一收敛为 machine-readable artifact 和 phone-safe / diagnostics-safe summary。没有真实材料时，artifact 必须清楚地 blocked，而不是产生乐观验收。

## 7. Owner 和协作边界

| Owner | 责任 | 计划内文件范围 | 验收重点 |
| --- | --- | --- | --- |
| `hardware-engineer` | 主责 intake schema、采购/source/安装/接线/标定/HIL entry 材料字段和硬件文档边界 | 后续实施可改 `docs/product/production_hardware_boundary.md`、新增硬件 intake artifact/gate、必要 docs；本计划阶段不改 | `docs/vendor/VENDOR_INDEX.md` 只作为已有 vendor coverage，不冒充 LiDAR/ToF 来源 |
| `robot-software-engineer` | Robot diagnostics metadata-only consumer 和 fail-closed compatibility fence | 后续实施可改 diagnostics / remote bridge / ROS contract 相关文件；本计划阶段不改 | metadata-only 不触发控制、ACK、cursor、Nav2 或 HIL |
| `autonomy-engineer` | SLAM/Nav2、电梯语义证据、ToF 近场 safety role 的 intake 消费边界 | 后续实施可改 pc-tools evidence gate、nav/vision/behavior docs/tests；本计划阶段不改 | ToF 不作为主建图输入；无材料不写 field pass |
| `full-stack-software-engineer` | mobile/web phone-safe 只读 panel 和 copy/export whitelist | 后续实施可改 `mobile/web`、fixture、mobile docs/tests；本计划阶段不改 | 不解锁 Start / Confirm Dropoff / Cancel |
| `product-okr-owner` | sprint 链路、OKR 边界、验收口径和 final closeout | 本轮计划只改 `sprints/.../pre_start.md`、`prd.md`、`tech-plan.md` | 不把计划文档当业务结果 |

## 8. 风险、阻塞和证据链缺口

- 真实 2D LiDAR SKU、vendor/source document 和采购状态仍缺。
- 真实 ToF channel count、vendor/source document、采购状态和安装位仍缺。
- 机械安装、接线、电源预算、线缆固定、传感器 frame、标定流程、HIL entry checklist 仍缺。
- 当前 `docs/vendor/VENDOR_INDEX.md` 不覆盖 LiDAR/ToF，不能引用为 LiDAR/ToF 已有来源。
- 当前环境没有真实硬件；所有本轮计划和后续本地 gate 只能是 `software_proof` / intake readiness，不是 HIL、field pass 或 delivery success。
- O5 真实外部证据仍阻塞，本轮不消费该 blocker。

## 9. 需要创建或更新的 sprint 文档

本轮计划阶段创建：

- `sprints/2026.05.16_12-13_hardware-sensor-procurement-intake/pre_start.md`
- `sprints/2026.05.16_12-13_hardware-sensor-procurement-intake/prd.md`
- `sprints/2026.05.16_12-13_hardware-sensor-procurement-intake/tech-plan.md`

后续实施阶段必须继续补：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

只有 Engineer 完成实现和验证后，Product 才能更新 `OKR.md`；本计划阶段不修改 `OKR.md`。
