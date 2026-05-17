# Sprint 2026.05.17_23-24 Wave Rover HIL Packet Execution Pack - Pre Start

sprint_type: epic

## 1. 启动背景

本轮按 `OKR.md` 4.1 重新排序。当前最低 Objective 仍是 Objective 5，约 68%，但继续提升需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser external proof。本机只有 Docker，没有这些外部材料，因此不继续堆 O5 本地 metadata depth。

下一低完成度是 Objective 1，约 80%。上一轮 `2026.05.17_22-23_wave-rover-hil-packet-review-decision` 已完成 `software_proof_docker_wave_rover_hil_packet_review_decision_gate`，但 `final.md` 明确仍缺真实 WAVE ROVER HIL packet：`feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`、`operator_hil_report` 和同一 safe `evidence_ref`。

本轮目标是新增 `wave_rover_hil_packet_execution_pack`，把上一轮 review decision 转成真实 HIL 执行前可交给硬件同学的操作包、材料模板、采集顺序、owner handoff 和 rerun commands。它仍是 Docker/local software proof，不声明 `hil_pass`。

## 2. 具体证据

- PR #5 review P1：`docs/product/production_hardware_boundary.md` 默认硬件集合曾与 mandatory `monocular + 2D LiDAR + ToF` baseline 不一致，说明硬件材料和执行包不能含糊。
- PR #5 review P2：mandatory sensor assumptions 缺 `docs/vendor/` 来源，说明硬件相关结论必须引用 `docs/vendor/VENDOR_INDEX.md` 及其指向文件。
- PR #4 / PR #5 共同主题：elevator assisted delivery 与硬件 baseline 已是必达产品边界，但真实 route/elevator field materials、真实 2D LiDAR / ToF source、采购、安装、接线、电源、标定和 HIL-entry 材料仍缺。
- `2026.05.17_22-23_wave-rover-hil-packet-review-decision/final.md`：上一轮只完成 PC / Robot diagnostics / mobile / Product closeout 的 review decision 软件证明链路，未完成真实 WAVE ROVER、真实 UART、真实串口日志或 topic sample。

## 3. 本轮 Owner

- hardware-engineer：新增 PC execution-pack gate、fixture、测试和硬件文档；必须读取 vendor index 与 WAVE ROVER vendor 文件。
- robot-software-engineer：新增 diagnostics metadata-only consumer、测试和 ROS contract 文档。
- full-stack-software-engineer：新增 mobile/web 只读 execution-pack panel、fixture/test 和产品流程文档。
- product-okr-owner：验收收口、OKR 更新、progress log 和本 sprint closeout。

## 4. 风险边界

- 本机没有真实硬件，不能跑真实 `/dev/ttyUSB*`、WAVE ROVER UART、HIL 或 Nav2/fixed-route 实测。
- 本轮不得把 execution pack 写成真实 HIL、真实串口、真实 `/odom`、真实 `/imu/data`、真实 `/battery`、真实手机/browser、route/elevator field pass、Objective 5 external proof 或 delivery success。
- 所有输出必须保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
