# Sprint 2026.05.18_06-07 Route Task Material Callback Review Decision - Pre Start

sprint_type: epic

## 1. 启动背景

本轮从 `OKR.md` 4.1 和最近两轮 sprint final 重新排序。当前数值最低 Objective 仍是 Objective 5，约 68%，但本机只有 Docker，没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser external proof。继续堆本地 O5 metadata depth 不会形成可验收进展。

下一低项 Objective 1 约 81%，但最近已连续完成 WAVE ROVER feedback replay、HIL packet intake、review decision、execution pack；剩余缺口是实际 WAVE ROVER、真实 UART/串口、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery` 和 operator HIL report。本机没有真实硬件，本轮不第三次消费同一硬件 blocker。

因此本轮继续 Objective 2 / Objective 3 / Objective 4 的 route/elevator 现场材料链，目标是把上一轮 `route_task_field_retest_material_callback_packet` 推进为 `route_task_field_retest_material_callback_review_decision`：对现场回执 packet 做复核决策，明确 accepted / missing / rejected material 是否足够进入真实复跑、材料补齐或 owner handoff。

## 2. 证据来源

- PR #4：`Add elevator-assisted delivery capability to agents, registry and OKR`，把电梯 assisted delivery 写入主链路和证据要求。
- PR #5：`Make elevator-assisted delivery mandatory; update agents, OKR and hardware baseline`，review 反馈指出 `docs/product/production_hardware_boundary.md` 的 default hardware set 与 `monocular + 2D LiDAR + ToF` mandatory baseline 冲突，以及新增 sensor assumption 缺 `docs/vendor/` 来源。
- Sprint `2026.05.18_04-05_route-task-field-retest-material-pack`：完成 material pack 和 callback skeleton，但仍不是真实 route/elevator field pass。
- Sprint `2026.05.18_05-06_route-task-material-callback-packet`：完成可填写、可回传、可被 diagnostics/mobile 只读消费的 callback packet，但还缺复核决策。

## 3. 本轮目标

交付 `software_proof_docker_route_task_field_retest_material_callback_review_decision_gate`：

- PC gate 读取 material callback packet artifact / summary / wrapper / diagnostics nested JSON，生成 review decision artifact / summary。
- Robot diagnostics 只读消费 review decision summary，输出 metadata-only alias，fail closed。
- mobile/web 只读展示“现场材料回执复核决策”，不启用 Start Delivery、Confirm Dropoff、Cancel 或任何 robot command。
- Product closeout 更新 OKR、progress log、sprint 收口，保持所有真实证据边界。

## 4. Owner

- Autonomy Algorithm Engineer：PC evidence gate、focused test、evidence contract。
- Robot Platform Engineer：operator gateway diagnostics metadata-only consumer、diagnostics test、ROS contract。
- User Touchpoint Full-Stack Engineer：mobile/web read-only panel、fixture/test、mobile flow doc。
- Product Manager / OKR Owner：收口 OKR、progress log、`tech-done.md`、`side2side_check.md`、`final.md`。

## 5. 风险和边界

本轮不是 real route/elevator field pass，不是 Nav2/fixed-route proof，不是 task record/completion signal，不是 dropoff/cancel completion，不是 delivery success，不是 HIL，不是 WAVE ROVER/UART，不是真实手机/browser，不是 Objective 5 external proof。

如果任一 worker 需要新增 WAVE ROVER、UART、波特率、JSON 指令、速度映射、反馈协议、引脚、电压、固件、2D LiDAR、ToF 或机械尺寸事实，必须先读 `docs/vendor/VENDOR_INDEX.md` 及其指向资料；本轮默认不新增硬件事实，只引用 PR #5 review 作为材料缺口依据。
