# Sprint 2026.05.16_14-15 Hardware Sensor Procurement Execution Pack - Pre Start

sprint_type: epic

## 1. 上轮未完成项

- `2026.05.16_13-14_hardware-sensor-procurement-review-decision` 已完成 `hardware_sensor_procurement_review_decision` software proof，把 2D LiDAR / ToF 材料缺口整理成 `review_decision`、`blockers`、`next_required_evidence`、`owner_handoff` 和 `rerun_commands`。
- 上轮明确没有真实 2D LiDAR / ToF SKU、vendor/source document、采购、安装、接线、标定、HIL entry、WAVE ROVER/UART/HIL、真实 Nav2/fixed-route、真实手机或 O5 external proof。
- `OKR.md` 4.1 当前 Objective 5 约 66% 最低，但本机只有 Docker，没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 worker/migration 材料；本轮不继续堆 O5 本地 metadata。

## 2. 本轮目标

本轮推进 Objective 4，并服务 Objective 1/2/3 的后续真实材料闭环：把 `hardware_sensor_procurement_review_decision` 的评审结果转成可执行的采购执行包 `hardware_sensor_procurement_execution_pack`。

执行包必须包含：

- 真实 2D LiDAR / ToF 采购与来源材料 checklist。
- 安装、接线、电源预算、标定和 HIL entry 材料模板。
- owner handoff、rerun command summary、blocked reason 和 safe evidence_ref。
- Robot diagnostics metadata-only 消费。
- mobile/web 首屏只读 panel，便于普通用户/现场同学知道下一步该补哪些材料。

## 3. Owner

- Hardware Infra Engineer：PC gate / execution pack artifact 主责。
- Robot Platform Engineer：Robot diagnostics metadata-only summary 主责。
- User Touchpoint Full-Stack Engineer：mobile/web read-only panel 与 copy package 主责。
- Product Manager / OKR Owner：Sprint closeout、OKR 口径和产品/接口文档验收。

## 4. 风险边界

- 本机没有真实硬件，只有 Docker；本轮只能形成 `software_proof_docker_hardware_sensor_procurement_execution_pack_gate`。
- 不得写成真实采购完成、真实安装/接线/标定、真实 HIL、真实 route/elevator field pass、真实手机通过、delivery success 或 O5 external proof。
- Start / Confirm Dropoff / Cancel / primary actions 必须继续 fail closed。
- 硬件资料引用必须以 `docs/vendor/VENDOR_INDEX.md` 和其指向资料为准；当前 vendor 资料不能替代真实 2D LiDAR / ToF SKU/source/procurement proof。

## 5. 近期证据

- 上轮 `final.md`：Objective 4 从约 82% 到约 83%，但真实 2D LiDAR / ToF SKU、source、采购、安装、接线、标定和 HIL entry 仍缺。
- 上轮 `tech-done.md`：Hardware 首轮 unsupported 顶层 schema bypass 已修复，证明本轮新 gate 也必须验证 outer schema 与 nested summary。
- `OKR.md` 4.1：Objective 5 约 66% 仍最低，但只接受真实外部云/4G/OSS/CDN/DB/queue 证据；Docker-only 本地 metadata 不再足以上调 O5。
