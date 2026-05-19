# Sprint 2026.05.20_07-08 Hardware Sensor HIL-entry Callback Intake - Side2Side Check

sprint_type: epic

## 1. 用户价值对照

本轮核心用户价值成立：PR #5 / Objective 1 的真实硬件材料缺口不再只停留在 execution pack 或聊天回填，而是形成 PC gate、Robot diagnostics safe alias、mobile/web 只读 panel 三段式 callback intake。

产品北极星对照：普通手机用户最终只需要看到材料状态、下一步和安全边界；本轮 mobile/web 只读 panel 没有暴露 raw JSON、serial/UART、ROS topic、凭证、路径或控制入口。

## 2. OKR 映射对照

- Objective 5 仍是最低约 68%，但本轮没有真实 external materials，因此不推进 O5 completion。
- Objective 1 仍约 81%，本轮补齐 software-proof callback intake，但真实 2D LiDAR / ToF、WAVE ROVER/UART/HIL 和 PR #5 `PRRT_kwDOSWB9286CJ3tX` closure 仍未完成，因此不提高百分比。
- Objective 4 只获得 phone-safe 可读性收益，不写成真实手机/browser 验收。

## 3. 验收口径对照

通过项：

- Hardware callback intake gate 接受 sanitized refs/summaries，并拒绝 unsupported schema、weak boundary、evidence-ref mismatch、unsafe raw copy、success/control claims。
- Robot diagnostics 只消费 sanitized summary，保持 metadata-only fail-closed。
- mobile/web 只读展示 callback intake，不改变 Start Delivery / Confirm Dropoff / Cancel gating。
- 文档同步覆盖 `pc-tools/README.md`、`docs/product/production_hardware_boundary.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。

未通过或不适用项：

- 未做真实硬件、真实手机、真实云、公网、4G、OSS/CDN、Docker colcon 或现场路线/电梯验收；这些均不属于本轮验收围栏。

## 4. 边界复核

本轮必须保留并已在 OKR/progress/sprint 文档中复核的边界：

- `software_proof_docker_hardware_sensor_hil_entry_callback_intake_gate`
- `hardware_material_pending`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

不得写成：真实 2D LiDAR / ToF、真实采购/安装/接线/供电/标定/HIL-entry、WAVE ROVER/UART/HIL、PR #5 thread resolved、O5 external proof、真实手机/browser、route/elevator field pass 或 delivery success。
