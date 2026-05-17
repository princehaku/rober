# Sprint 2026.05.18_05-06 Route Task Material Callback Packet - Side2Side Check

sprint_type: epic

## 1. 对照对象

对照 `tech-plan.md` 的 Product Closeout 要求，以及 A/B/C workers 返回的完成证据：

- Task A：PC-only callback packet gate。
- Task B：Robot diagnostics metadata-only consumer。
- Task C：mobile/web 只读“路线/电梯现场材料回执”panel。

## 2. 验收对照

| 验收项 | 结果 | 说明 |
| --- | --- | --- |
| schema literal 固定 | 通过 | 使用 `trashbot.route_task_field_retest_material_callback_packet.v1` 与 `trashbot.route_task_field_retest_material_callback_packet_summary.v1`。 |
| evidence boundary 固定 | 通过 | 全链路使用 `software_proof_docker_route_task_field_retest_material_callback_packet_gate`。 |
| fail-closed flags | 通过 | 保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。 |
| PC packet gate | 通过 | Task A 已新增 artifact / summary 与 focused tests。 |
| Robot diagnostics | 通过 | Task B 已新增 metadata-only consumer 与 alias。 |
| mobile/web panel | 通过 | Task C 已新增只读 panel，copy/export whitelist-only。 |
| 主操作 gating | 通过 | Start Delivery、Confirm Dropoff、Cancel、dispatch、callback、robot command gating 不变。 |
| OKR 更新 | 通过 | `OKR.md` 保守更新：O2/O3/O4 保持约 99%，O1 保持约 81%，O5 保持约 68%。 |
| sprint 留档 | 通过 | 已创建 `tech-done.md`、`side2side_check.md`、`final.md`。 |

## 3. 边界核对

本轮只证明当前 repo 内的 callback packet software proof。它不是 real route/elevator field pass，不是 Nav2/fixed-route proof，不是 task record/completion signal，不是 dropoff/cancel completion，不是 delivery success，不是 HIL，不是 WAVE ROVER/UART，不是真实手机/browser，不是 Objective 5 external proof。

没有新增硬件事实、串口事实、波特率、WAVE ROVER JSON 指令、速度映射、反馈协议、2D LiDAR SKU、ToF SKU、引脚、电压、固件或机械尺寸。

## 4. 需要继续补齐的证据

- PR #4：真实 route/elevator field materials，包括门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record/completion signal、dropoff/cancel completion 和 delivery result。
- PR #5：真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- Objective 1：真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery` 与 operator HIL report。
- Objective 4：真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice。
- Objective 5：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover。

## 5. 结论

本 sprint 满足 Product Closeout 条件，可以收口为 `software_proof_docker_route_task_field_retest_material_callback_packet_gate`。OKR 不因本轮提升到真实现场、真实手机、真实硬件或真实云外部证明。
