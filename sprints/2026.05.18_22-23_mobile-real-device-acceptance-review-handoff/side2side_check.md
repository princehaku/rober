# Sprint 2026.05.18_22-23 Mobile Real Device Acceptance Review Handoff - Side2Side Check

## 1. 验收对象

- sprint_type: epic
- 验收对象：`mobile_real_device_field_trial_acceptance_review_handoff*` software proof。
- 对照来源：`pre_start.md`、`prd.md`、`tech-plan.md`、Full-stack worker evidence、Robot worker evidence。

## 2. 用户价值和产品北极星

北极星仍是普通手机用户可用的低成本 ROS2 自主垃圾投递机器人。本轮把上一轮真实手机验收 review decision 转成现场 owner 可执行的 handoff packet：谁补材料、补什么、如何保持同一 safe `evidence_ref`、哪些 copy 不能被解释成真实手机通过。

## 3. OKR 映射与 KR 拆解验收

- Objective 4 KR1 / KR5 / KR7：手机端新增只读“现场验收复核交接”视图，普通用户仍不接触 raw JSON、ROS topic、串口、硬件调试或命令行。
- Robot diagnostics：新增 `robot_diagnostics_mobile_real_device_field_trial_acceptance_review_handoff_summary` safe alias，供手机和支持侧读取 metadata-only summary。
- Product closeout：本轮证据只支持 Objective 4 的 handoff chain 更完整，不能证明真实手机验收完成。

## 4. 优先级和验收口径

- P0：handoff summary 出现在 mobile/web 和 Robot diagnostics 的安全白名单路径。已满足。
- P0：`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false` 在 fixture、UI copy、diagnostics summary 和 docs 中一致。已满足。
- P0：Start Delivery、Confirm Dropoff、Cancel gating 不变。已满足。
- P1：缺 summary 或缺 safe copy 时 fail closed。已通过前端和 diagnostics tests 覆盖。
- P1：unsafe copy、success claim、control claim 不会透出成可执行成功。已通过 whitelist / unsafe fence 和 diagnostics tests 覆盖。

## 5. 证据边界核对

本轮必须保持并已保持：

- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `software_proof_docker_mobile_real_device_field_trial_acceptance_review_handoff_gate`

本轮不证明：

- 真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice。
- delivery success、dropoff/cancel completion。
- Objective 5 external proof。
- WAVE ROVER、UART、HIL。
- PR #4 route/elevator field pass。
- PR #5 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry materials。

## 6. 验收结论

本轮可收口为 Objective 4 的 software proof handoff packet：它能降低下一次真实手机现场验收材料回填的交接偏差，但不改变真实证据缺口。OKR 进度保持保守，不把 Objective 4、Objective 2 或 Objective 3 写成 100%。
