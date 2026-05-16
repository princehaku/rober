# Sprint 2026.05.17_03-04 Hardware Sensor HIL-entry Execution Pack - Side2Side Check

sprint_type: epic

## 1. 验收口径对照

| PRD / Tech-plan 要求 | 验收结果 | 结论 |
| --- | --- | --- |
| PC gate 生成 `hardware_sensor_hil_entry_execution_pack` artifact/summary | Hardware worker 新增 gate 与测试，输出 `software_proof_docker_hardware_sensor_hil_entry_execution_pack_gate`，保留 `hardware_material_pending`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false` | 通过 |
| Vendor/source boundary 不得写成真实硬件 proof | Hardware worker 已读 `docs/vendor/VENDOR_INDEX.md`、`base_ctrl.py`、`config.yaml`、`json_cmd.h`、`uart_ctrl.h`；closeout 明确这些只作为 source boundary | 通过 |
| Robot diagnostics metadata-only 消费 execution pack | Robot worker 新增 consumer，支持 explicit ref、env、latest status、nested summary，fail closed；不改变 collect/dropoff/cancel/ACK/cursor/Nav2/HIL/delivery success | 通过 |
| Mobile/web 只读 panel phone-safe 可读化 | Full-stack worker 新增只读“传感器 HIL 执行包” panel，过滤 raw vendor docs、raw JSON、serial/UART、路径、凭证、DB/queue URL、OSS AK/SK、checksums、complete artifacts | 通过 |
| Start Delivery / Confirm Dropoff / Cancel gating 不变 | Full-stack worker 验证 mobile unittest `28 tests OK` 与 required rg；本轮只读 panel 不启用主操作 | 通过 |
| Objective 5 不因本轮上调 | 本轮没有公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration；O5 保持约 66% | 通过 |

## 2. 用户价值和北极星核对

北极星仍是普通手机用户可以把垃圾交给低成本 ROS2 小车，并在失败时得到可理解、可追溯、可支持的解释。本轮没有让小车真实送达，但把“真实 HIL-entry 前还缺什么”从工程口头信息推进为 PC gate、Robot diagnostics 和 mobile/web 三端一致的执行包。

用户价值成立点：

- 现场支持能按同一 `evidence_ref` 看到 material templates、owner handoff、first-run / rerun summary 和 next required evidence。
- 普通手机入口只看到只读解释，不暴露 raw JSON、ROS topic、serial/UART、vendor 原文、路径或凭证。
- 控制链路保持 fail-closed，不把 `hardware_material_pending` 误写成 ready/pass/complete。

## 3. OKR 映射核对

- Objective 1：可保守上调到约 77%，因为 HIL-entry readiness review 已变成 execution pack 和 owner handoff；但仍是 software proof。
- Objective 4：可保守上调到约 97%，因为 mobile/web 对 execution pack 的 phone-safe 可读解释更完整；但仍不是真实手机/browser。
- Objective 2 / Objective 3：保持约 86%，没有真实任务闭环、Nav2/fixed-route、route/elevator field pass、task record 或 delivery success。
- Objective 5：保持约 66%，Docker-only 环境仍缺真实 external proof。

## 4. 阻塞和证据链缺口

本轮剩余阻塞不是软件 closeout 阻塞，而是真实材料缺口：

- 真实 2D LiDAR / ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry。
- 真实 WAVE ROVER、真实串口/UART JSON feedback、`T=1001`、`/odom`、`/imu/data`、`/battery`、`hil_pass`。
- 真实 route/elevator field pass、Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion、delivery success。
- 真实 iPhone/Android browser、production app、PWA prompt/user choice。
- Objective 5 external proof：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。

## 5. Product 验收结论

本 sprint 达到 PRD / tech-plan 的软件验收口径，可以收口为 `software_proof_docker_hardware_sensor_hil_entry_execution_pack_gate`。不得把本轮写成真实 2D LiDAR/ToF、采购、安装、接线、供电、标定、HIL、route/elevator field pass、真实手机/browser、delivery success 或 Objective 5 external proof。
