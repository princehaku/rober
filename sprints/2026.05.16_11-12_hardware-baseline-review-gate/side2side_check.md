# Sprint 2026.05.16_11-12 Hardware Baseline Review Gate - Side2Side Check

## 1. 对照结论

本轮验收通过。PR #5 review 暴露的硬件基线矛盾已被转成可执行的 product/hardware baseline gate，并在四条链路上闭环：

- Product/Hardware 文档：`Default Hardware Set` 不再与 `Navigation/Sensing Baseline` 冲突；2D LiDAR / ToF 明确为 Product Target / Procurement Validation Pending。
- PC/Autonomy gate：`hardware_baseline_review` 输出 `software_proof_docker_hardware_baseline_review_gate`、`hardware_material_pending`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- Robot diagnostics：新增 metadata-only consumer，保持 fail-closed，不触发控制、ACK、Nav2、HIL 或 delivery success。
- Mobile：新增只读“硬件基线评审状态”panel，copy/export whitelist-only，Start / Confirm Dropoff / Cancel gating 不变。

## 2. 用户价值核对

本轮提升的是普通用户产品化路径中的低成本量产边界清晰度。团队现在可以在同一口径下讨论默认硬件、目标传感器、采购待补证、Nav2/SLAM 责任、近场 safety gate 和手机可见状态，减少后续 BOM、bringup、UI copy 和验收材料互相打架。

这不是 hardware proof。真实用户仍不能因为这个 panel 就发车成功，也不能把 2D LiDAR / ToF 当成已采购或已实测。

## 3. OKR 映射核对

- Objective 4：主收益。量产硬件边界矛盾被修复，并被 PC gate、Robot diagnostics 和手机只读 panel 串起来，支持从约 80% 保守上调到约 81%。
- Objective 1：支撑但不加分。本轮强化硬件事实可追溯和 `hardware_material_pending`，但没有真实 WAVE ROVER、UART、`T=1001` feedback、真实串口或 HIL。
- Objective 2 / Objective 3：间接受益但不加分。传感器职责边界更清楚，但没有真实 route/elevator field pass、Nav2/fixed-route runtime log、task record、dropoff/cancel completion 或 delivery success。
- Objective 5：不加分。Objective 5 仍是最低约 66%，但本机只有 Docker；本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration，不是 Objective 5 external proof。

## 4. 验收口径核对

- `hardware_baseline_review` 不暴露 raw artifacts、本机路径、credentials、DB/queue URL、OSS AK/SK、ROS topic、`/cmd_vel`、serial/UART 或 WAVE ROVER 参数。
- `delivery_success=false` 和 `primary_actions_enabled=false` 保持贯穿 PC gate、Robot diagnostics、mobile fixture/panel 和 sprint closeout。
- `hardware_material_pending` 与 `not_proven` 保持贯穿 2D LiDAR / ToF 责任说明、OKR 和进度日志。
- PC `--summary-output` 与 Robot diagnostics 已统一到 `trashbot.hardware_baseline_review_summary.v1`，最终回归证明 summary handoff 不再进入 `unsupported_schema`。
- 文档同步已覆盖 `docs/product/production_hardware_boundary.md`、`docs/navigation/fixed_route_workflow.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md` 和 `pc-tools/README.md`。

## 5. 未完成事项

- 真实 2D LiDAR / ToF 采购、安装、接线、标定和 HIL 证据未完成。
- 真实 WAVE ROVER/UART/HIL 未完成。
- 真实手机设备、production app 或真实 PWA prompt/user choice 未完成。
- 真实 Nav2/fixed-route、route/elevator field pass、dropoff/cancel completion 和 delivery success 未完成。
- Objective 5 external proof 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 和 worker/migration。
