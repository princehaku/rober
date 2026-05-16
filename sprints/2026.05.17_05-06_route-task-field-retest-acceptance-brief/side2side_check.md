# Sprint 2026.05.17_05-06 Route Task Field Retest Acceptance Brief - Side2Side Check

sprint_type: epic

## 1. 用户价值对照

本轮目标是把 `route_task_field_retest_drill_console` 的下一步命令、缺失材料和回调清单转成现场支持可执行的 acceptance brief / handoff packet。工程交付已覆盖 PC gate、Robot diagnostics metadata-only consumer 和 mobile/web 只读 panel，能让现场支持围绕同一 safe `evidence_ref` 看到现场准入、执行清单、pass/fail criteria、required evidence packet、owner handoff、rerun notes 和边界。

对产品北极星的贡献是：普通手机用户路径仍不暴露 raw JSON、ROS topic、serial/UART、WAVE ROVER 或工程内部材料；现场/工程侧则得到更清晰的证据链，知道下一次真实复测必须补齐哪些材料。

## 2. OKR 映射核对

- Objective 2：本轮把电梯 assisted delivery / route-task 现场复测从 drill console 推进到 acceptance brief。`door_state`、`target_floor_confirmation`、`human_assistance_note`、`dropoff_or_cancel_completion`、`delivery_result` 进入 required evidence packet，因此任务闭环材料回填路径更可执行。
- Objective 3：本轮把 Nav2/fixed-route runtime log、route completion signal、task record 纳入验收包和 pass/fail criteria，降低后续真实 fixed-route 复测时的材料遗漏风险。
- Objective 4：mobile/web 新增只读“现场复测验收简报” panel，phone-safe 展示 acceptance status、safe evidence ref、required evidence packet、owner handoff、boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`，主操作 gating 不变。
- Objective 5：不提升。本轮是 Docker-only local software proof，没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。
- Objective 1：不提升。本轮没有真实 WAVE ROVER、UART、HIL、2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。

## 3. 验收口径对照

已满足：

- 输出和消费链路均围绕 `route_task_field_retest_acceptance_brief`。
- 证据边界使用 `software_proof_docker_route_task_field_retest_acceptance_brief_gate`。
- 保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- Acceptance brief required evidence packet 包含 Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result。
- Robot diagnostics 只读消费 metadata summary，不新增动作授权。
- mobile/web panel 只读展示，Start Delivery、Confirm Dropoff、Cancel gating 不变。
- PR #5 的硬件边界仍作为风险保留：单目 + 2D LiDAR + ToF safety ring 的真实 SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料仍未补齐。

未满足但不属于本轮承诺：

- 真实 route/elevator field pass。
- 真实 HIL、WAVE ROVER feedback、serial/UART 证据。
- 真实 iPhone/Android browser、production app 或真实 PWA prompt/user choice。
- Objective 5 external proof。

## 4. Side-by-side 结论

本轮可以作为 Objective 2 / Objective 3 / Objective 4 的 software proof 增量收口：它没有直接完成真实送达，但把下一次真实 route/elevator field retest 的准入、执行、验收、失败判定和 owner handoff 固化到了 PC / Robot / mobile 共同消费的 safe summary 中。

本轮不能作为 Objective 5 external proof、O1 HIL proof、真实手机 proof 或 delivery success proof。所有 closeout 文案必须继续使用 Docker-only / software proof / metadata-only / fail-closed 边界。
