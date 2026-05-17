# Sprint 2026.05.18_00-01 Route Task Result Callback Review Handoff - Pre Start

sprint_type: epic

## 1. 启动结论

状态：`PLANNED_READY_FOR_TEAM_EXECUTION`。

本轮新建 fresh Epic sprint：`sprints/2026.05.18_00-01_route-task-result-callback-review-handoff/`。核心抓手是 `route_task_field_retest_result_callback_review_handoff`，承接上一轮 `route_task_field_retest_result_callback_review_decision`，把 callback review decision 转成 result review 前的 handoff status、owner follow-up、rerun package 和 review-ready package。

目标 evidence boundary：`software_proof_docker_route_task_field_retest_result_callback_review_handoff_gate`。本轮仍只允许 Docker-only / PC-only / metadata-only / mobile read-only software proof，必须保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。不得宣称真实 route/elevator field pass、真实手机/browser、HIL、WAVE ROVER 实机或 Objective 5 external proof。

## 2. 已读证据

- `AGENTS.md`：Epic sprint 必须走 `pre_start.md -> prd.md -> tech-plan.md -> tech-done.md -> side2side_check.md -> final.md`；跨 owner 工作必须由 Autonomy / Robot / Full-stack 子 agent 并行执行，验证只列围栏命令。
- `OKR.md` 4.1：Objective 5 约 68%，是当前数值最低 Objective；Objective 1 约 81%，是下一低项；Objective 2 / Objective 3 / Objective 4 约 99%。`OKR.md` 同时明确 O5 stop rule：没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof 时，不继续堆本地 metadata depth。
- PR #4：把 elevator-assisted delivery 设为主线必达能力，要求 route/elevator field materials 能被回填、复核、追责。
- PR #5 review comments：指出 production hardware boundary 曾存在默认硬件集与 2D LiDAR / ToF mandatory baseline 矛盾、OKR lowest-objective 叙述误导、mandatory sensor assumptions 缺本地 vendor/source。后续 sprint 已修正部分边界，但真实 2D LiDAR / ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry 材料仍缺。
- `sprints/2026.05.17_19-20_route-task-result-callback-review-decision/final.md`：已完成 `route_task_field_retest_result_callback_review_decision`，把 callback intake 的 accepted/missing/rejected updates 转成复核决策、owner handoff、next required evidence 和 rerun path；下一步需要把 review decision 推进到 result review 前的 handoff/status/rerun package。
- 最近 HIL packet finals：`2026.05.17_21-22_wave-rover-hil-packet-intake`、`2026.05.17_22-23_wave-rover-hil-packet-review-decision`、`2026.05.17_23-24_wave-rover-hil-packet-execution-pack` 连续三轮都以缺真实 WAVE ROVER HIL packet、真实 UART、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery` 和 operator HIL report 为剩余风险；本机无真实硬件，继续 O1 本地包装会重复消费同一 blocker。

## 3. 为什么不选 Objective 5

Objective 5 是当前最低完成度，约 68%。本轮不选 O5，因为可移动 O5 completion 的证据必须来自真实 external proof：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser external proof。

当前主机只有 Docker。继续创建本地 O5 metadata、sample、fixture、blocked summary 或 phone/browser local proof，不会形成 production external evidence，也会违反 `OKR.md` 4.1 的 stop rule。

## 4. 为什么不继续 Objective 1

Objective 1 约 81%，是下一低项，但最近 `21-22`、`22-23`、`23-24` 三轮已经围绕 WAVE ROVER HIL packet 做了 intake、review decision 和 execution pack。三轮 final 都指出真实 blocker 是缺真实 WAVE ROVER、真实 UART、真实串口日志、真实 topic samples 和 operator HIL report。

本机没有真实硬件，只有 Docker。继续做本地 HIL packet 包装会重复消费同一硬件 blocker，不能把 `software_proof_docker_wave_rover_hil_packet_*` 写成 `hil_pass` 或 Objective 1 的真实底盘闭环。

## 5. 本轮选择和用户价值

本轮选择 Objective 2 / Objective 3 的 `route_task_field_retest_result_callback_review_handoff`。

用户价值：现场支持在 callback review decision 之后，可以直接看到本次 result review 前还缺什么、谁负责补、哪些材料可进入 review、哪些必须 rerun，以及同一 `safe_evidence_ref` 的 handoff package 是否完整。这样 route/elevator 现场材料不会停在“已决策但未交接”的灰区。

产品北极星：低成本 ROS2 自主垃圾投递机器人闭环。当前阶段要把 PR #4 route/elevator field materials 回填链推进到“callback intake -> callback review decision -> result review handoff”的可执行、可复核、可追责状态，同时保持所有证据边界诚实。

## 6. OKR 映射

- Objective 2：主目标。把 elevator-assisted delivery 所需 door state、target floor confirmation、human assistance note、dropoff/cancel completion 和 delivery result 的 review handoff 做成可执行包。
- Objective 3：主目标。把 Nav2/fixed-route runtime log、route completion signal、task record 与同一 `safe_evidence_ref` 的 result review handoff 对齐。
- Objective 4：支援目标。mobile/web 只读 panel 展示 review handoff status、owner follow-up、rerun package 和 boundary flags，但不改变 Start Delivery、Confirm Dropoff、Cancel 或 ACK gating。
- Objective 5：不推进。缺真实 external proof。
- Objective 1：不推进。缺真实 WAVE ROVER HIL packet，且最近同一硬件 blocker 已重复消费。

## 7. 本轮核心抓手

`route_task_field_retest_result_callback_review_handoff`：

- 输入上一轮 callback review decision artifact / summary。
- 输出 result review handoff status、owner follow-up、rerun package、review-ready package、next required evidence 和 read-only mobile summary。
- 对 missing / rejected / unsafe / evidence-ref mismatch / success-control claim fail closed。
- 全程保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 8. Team 分工

- Autonomy Algorithm Engineer：负责 PC evidence gate、focused unit test、`docs/interfaces/evidence_contracts.md`。
- Robot Platform Engineer：负责 diagnostics metadata-only consumer、focused unit test、`docs/interfaces/ros_contracts.md`。
- User Touchpoint Full-Stack Engineer：负责 mobile/web read-only panel、fixture/test、`docs/product/mobile_user_flow.md`。
- Product Manager / OKR Owner：负责 closeout docs、`OKR.md`、`docs/process/okr_progress_log.md`，但只在 A/B/C durable work 和验证通过后更新。

## 9. 风险、阻塞和证据链缺口

- 仍缺真实 route/elevator field pass、真实 Nav2/fixed-route、真实 route completion signal、真实 task record、真实 door state、真实 target floor confirmation、真实 human assistance note、真实 dropoff/cancel completion 和真实 delivery result。
- 仍缺真实 WAVE ROVER、UART、HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery` 与 operator HIL report。
- 仍缺 PR #5 真实 2D LiDAR / ToF source、receipt、采购、安装、接线、电源、标定和 HIL-entry 材料。
- 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 和真实手机/browser external proof。

## 10. 需要创建或更新的 sprint 文档

本 planning 阶段创建：

- `sprints/2026.05.18_00-01_route-task-result-callback-review-handoff/pre_start.md`
- `sprints/2026.05.18_00-01_route-task-result-callback-review-handoff/prd.md`
- `sprints/2026.05.18_00-01_route-task-result-callback-review-handoff/tech-plan.md`

实现和收口阶段必须继续更新：

- `sprints/2026.05.18_00-01_route-task-result-callback-review-handoff/tech-done.md`
- `sprints/2026.05.18_00-01_route-task-result-callback-review-handoff/side2side_check.md`
- `sprints/2026.05.18_00-01_route-task-result-callback-review-handoff/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
