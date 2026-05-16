# Sprint 2026.05.16_13-14 Hardware Sensor Procurement Review Decision - Pre Start

sprint_type: epic

## 1. 启动原因

本轮启动 `hardware_sensor_procurement_review_decision`。目标是承接上一轮 `hardware_sensor_procurement_intake`，把真实 2D LiDAR / ToF 的 SKU、source、采购、安装、接线、标定和 HIL entry 缺口，转成可执行的采购评审决策、blocker、next_required_evidence、owner_handoff 和重跑命令。

当前 live `OKR.md` 4.1 显示 Objective 5 约 66%，为数值最低 Objective；但当前主机只有 Docker，仍没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration。继续堆本地 O5 metadata 不能补齐真实外部证据，因此本轮不主攻 O5。

上一轮 sprint：`sprints/2026.05.16_12-13_hardware-sensor-procurement-intake/`。该 sprint 已完成 `hardware_sensor_procurement_intake` gate、Robot diagnostics metadata-only consumer 和 mobile/web 只读 panel，把 2D LiDAR / ToF 材料缺口 fail closed 暴露为 `hardware_material_pending`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

近期 PR #5 `Make elevator-assisted delivery mandatory; update agents, OKR and hardware baseline` 已把电梯 assisted delivery、2D LiDAR / ToF 硬件基线和参数化 sensor configs 写入主线。11-12 sprint 修复了 PR #5 review 指出的硬件基线矛盾和 schema handoff drift；12-13 sprint 建立了材料 intake。本轮要把 intake 的 blocked material 状态推进到采购评审决策，而不是继续停在“缺材料列表”。

## 2. 用户价值和产品北极星

产品北极星：普通手机用户把垃圾交给小车后，小车能低成本、可解释、可复盘地完成固定路线/电梯 assisted delivery，而不是依赖未采购、未安装、未标定的传感器假设。

本轮用户价值：

- 对 CEO / Product：把“还缺哪些材料”升级为“采购评审现在是否可继续、谁补什么、补完后跑什么命令”。
- 对 Hardware：明确每个 2D LiDAR / ToF material blocker 的 owner_handoff、next_required_evidence 和重跑命令。
- 对 Robot / Full-stack：继续只读消费 sanitized summary，保持 metadata-only / fail closed，不把采购评审决策误写成可控制机器人。
- 对后续现场验证：形成从 intake artifact 到 review decision 到 HIL entry / route/elevator field material 的证据链。

## 3. 背景证据

- `OKR.md` 4.1：Objective 5 约 66% 最低，但 O5 需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration；当前 Docker-only 主机不能补齐。
- `OKR.md` 6：当前最高可行动作包含真实 2D LiDAR / ToF SKU/vendor/procurement/installation/HIL-entry 材料，或 Objective 2/O3 的受控现场材料回填。
- `sprints/2026.05.16_11-12_hardware-baseline-review-gate/final.md`：PR #5 review 的硬件基线矛盾已修复，但结果仍是 `software_proof_docker_hardware_baseline_review_gate`，不证明真实 2D LiDAR / ToF。
- `sprints/2026.05.16_12-13_hardware-sensor-procurement-intake/final.md`：`hardware_sensor_procurement_intake` 已把真实 SKU/source/采购/安装/接线/标定/HIL entry 缺口暴露为 fail-closed intake。
- `docs/product/production_hardware_boundary.md`：2D LiDAR / ToF 是 Product Target / Procurement Validation Pending，`docs/vendor/VENDOR_INDEX.md` 不证明这些硬件已采购、接线、标定或 HIL。

## 4. OKR 映射

- Objective 4：主目标。把低成本量产硬件材料 intake 推进为采购评审决策和手机/诊断只读状态，提升普通用户路径背后的硬件可交付性。
- Objective 1：支撑目标。review decision 可列出进入 WAVE ROVER / Orange Pi / UART / HIL 前缺失的硬件材料，但本轮不宣称 HIL。
- Objective 2 / Objective 3：支撑目标。2D LiDAR / ToF 采购评审是后续 route/elevator field pass、Nav2/SLAM 和 same `evidence_ref` 复账的前置材料，不宣称 delivery success。
- Objective 5：非本轮主线。O5 数值最低，但当前真实外部云/4G/OSS/CDN/DB/queue 证据不可得；本轮明确停止重复消费 Docker-only O5 blocker。

## 5. KR 拆解或更新

- KR-A：新增 `hardware_sensor_procurement_review_decision` artifact / summary，读取上一轮 intake artifact 或 summary，并输出 procurement review decision。
- KR-B：把缺失 SKU/source/procurement/mounting/wiring/power/calibration/HIL entry 转成 `blockers`、`next_required_evidence`、`owner_handoff` 和 `rerun_commands`。
- KR-C：保持 `hardware_material_pending`、`not_proven`、`software_proof`、`delivery_success=false`、`primary_actions_enabled=false`，直到真实材料补齐并重新跑 gate。
- KR-D：Robot diagnostics 只读消费 review summary，缺 summary 或 unsupported schema 必须 fail closed，不触发 ACK、cursor、Nav2、HIL、dropoff/cancel completion 或 delivery result。
- KR-E：mobile/web 只读展示 phone-safe review decision，Start / Confirm Dropoff / Cancel gating 不改变。
- KR-F：Product closeout 仅在 Engineer 证据完整后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 6. 本轮核心抓手

核心抓手是一个采购评审决策 gate：`hardware_sensor_procurement_review_decision`。

它不是再生成一份 intake 清单，而是把 intake 的 blocked / pending 材料转成可执行评审输出：

- 当前 decision：例如 `blocked_missing_procurement_materials` 或 `ready_for_procurement_review_not_proven`。
- blocker 分类：SKU/source/procurement/mounting/wiring/power/calibration/HIL entry。
- next_required_evidence：下一次需要补的具体材料。
- owner_handoff：Hardware、Robot、Full-stack、Product closeout 各自后续动作。
- rerun_commands：补材料后应该重跑的 gate / diagnostics / mobile / closeout 命令。

## 7. Owner 和协作边界

| Owner | 责任 | 计划内文件范围 | 验收重点 |
| --- | --- | --- | --- |
| `hardware-engineer` | 主责 procurement review decision gate、blocker 分类、next_required_evidence、owner_handoff 和硬件材料边界 | 后续实施可改 `pc-tools/evidence/*hardware_sensor_procurement_review_decision*`、硬件/产品边界 docs；本计划阶段不改 | 缺真实材料时必须 fail closed；`docs/vendor/VENDOR_INDEX.md` 不能冒充 LiDAR/ToF source proof |
| `robot-software-engineer` | Robot diagnostics metadata-only review summary consumer | 后续实施可改 diagnostics / ROS contract 相关文件；本计划阶段不改 | unsupported/missing summary fail closed；不触发控制路径 |
| `full-stack-software-engineer` | mobile/web phone-safe 只读 review decision panel | 后续实施可改 `mobile/web`、fixtures、mobile docs/tests；本计划阶段不改 | 不暴露 raw artifact / ROS / serial / credential；不解锁 Start / Confirm Dropoff / Cancel |
| `product-okr-owner` | sprint 链路、OKR 边界、PR #5 证据引用、closeout 验收 | 本计划阶段只改 `pre_start.md`、`prd.md`、`tech-plan.md`；实施完成后可收口 sprint 和 OKR | 不把计划文档或 software proof 写成真实采购、HIL、field pass、delivery success 或 O5 proof |

本轮 implementation 阶段至少应并行启动 Hardware、Robot、Full-stack 三个 Engineer；Product closeout 等待三方证据后执行。四个 owner 文件范围互不重叠。

## 8. 风险、阻塞和证据链缺口

- 真实 2D LiDAR SKU、vendor/source document、采购状态仍缺。
- 真实 ToF SKU、channel source、采购状态和安装位仍缺。
- 机械安装、接线、电源预算、线缆固定、传感器 frame、标定流程、HIL entry checklist 仍缺。
- 当前 `docs/vendor/VENDOR_INDEX.md` 不覆盖 LiDAR/ToF，不能引用为 LiDAR/ToF 已有来源。
- 当前环境没有真实硬件；本轮实现最多是 `software_proof` / metadata-only / fail closed，不是 HIL、route/elevator field pass 或 delivery success。
- O5 真实外部证据仍阻塞，本轮不消费该 blocker。

## 9. 需要创建或更新的 sprint 文档

本轮计划阶段创建：

- `sprints/2026.05.16_13-14_hardware-sensor-procurement-review-decision/pre_start.md`
- `sprints/2026.05.16_13-14_hardware-sensor-procurement-review-decision/prd.md`
- `sprints/2026.05.16_13-14_hardware-sensor-procurement-review-decision/tech-plan.md`

后续实施阶段必须继续补：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

只有 Engineer 完成实现和验证后，Product 才能更新 `OKR.md`；本计划阶段不修改 `OKR.md` 或 closeout docs。
