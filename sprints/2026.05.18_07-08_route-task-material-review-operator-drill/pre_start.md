# Sprint 2026.05.18_07-08 Route Task Material Review Operator Drill - Pre Start

sprint_type: epic

## 1. 启动背景

本轮从 `OKR.md` 4.1、上一轮 final 和近期 PR/review 证据重新排序。当前数值最低 Objective 仍是 Objective 5，约 68%，但本机只有 Docker，没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser external proof。O5 stop rule 继续成立，本轮不再堆本地 O5 metadata depth。

下一低项 Objective 1 约 81%，但当前没有真实 WAVE ROVER、UART、串口 topic samples、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery` 或 operator HIL report。PR #5 review 暴露的 hardware baseline / vendor source 风险仍是真实材料缺口，本轮不继续包装同一硬件 blocker。

因此本轮继续 Objective 2 / Objective 3 / Objective 4 的 route/elevator 现场材料链。上一轮 sprint `2026.05.18_06-07_route-task-material-callback-review-decision` 已完成 `software_proof_docker_route_task_field_retest_material_callback_review_decision_gate`，把 material callback packet 推进成可复核的 `route_task_field_retest_material_callback_review_decision` artifact / summary。下一步不回退到老的 material pack-only drill，而是让 `route_task_field_retest_operator_drill` 直接消费 review decision artifact / summary / wrapper / nested diagnostics，生成同一 schema 的 operator drill artifact / summary。

## 2. 证据来源

- PR #4：把 elevator-assisted delivery 写成必达能力，要求 route/elevator 现场链覆盖真实门状态、楼层确认、人工协助、Nav2/fixed-route runtime、task record、dropoff/cancel completion 和 delivery result。
- PR #5：review 指出 production hardware boundary 的 default hardware set 与 mandatory sensor baseline 冲突，并指出 2D LiDAR / ToF 等 sensor assumption 缺 `docs/vendor/` source；这说明硬件材料不能靠叙述推进。
- Sprint `2026.05.18_06-07_route-task-material-callback-review-decision/final.md`：A/B/C worker 已完成 material callback review decision，剩余风险明确写明仍不是 route/elevator field pass、Nav2/fixed-route proof、task record/completion signal、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 O5 external proof。
- `docs/product/mobile_user_flow.md`：mobile/web 已有只读 `route_task_field_retest_material_callback_review_decision` 与 `route_task_field_retest_operator_drill` panels，后续 worker 只需验证或小补充 first-screen panel。

## 3. 用户价值和产品北极星

产品北极星仍是：普通用户只需要在手机端交付垃圾、选择目的地并理解当前状态；机器人和现场 operator 要用同一 `evidence_ref` 把路线、电梯、投放和失败恢复证据串起来，避免把缺材料、回执错误或 review decision 误认为真实送达。

本轮用户价值是把上一轮“现场材料回执复核决策”接成可执行 operator drill。现场同学不再从老 material pack-only checklist 重新开始，而是从 review decision 的 accepted / missing / rejected / owner handoff 结果进入下一步命令、回执清单和 rerun path。

## 4. 本轮目标

交付 `route_task_field_retest_operator_drill` 对 `route_task_field_retest_material_callback_review_decision` 的新输入能力：

- PC gate 能读取 review decision artifact / summary / wrapper / nested diagnostics。
- 输出仍使用 `trashbot.route_task_field_retest_operator_drill.v1` 与 `trashbot.route_task_field_retest_operator_drill_summary.v1`。
- evidence boundary 固定为 `software_proof_docker_route_task_field_retest_operator_drill_gate`。
- Robot diagnostics 与 mobile/web 仅做 metadata-only / first-screen read-only 支持。
- 全链路保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 5. Owner

- Autonomy Algorithm Engineer：A worker，主责 PC gate、focused test、evidence docs。
- Robot Platform Engineer：B worker，验证或小补 diagnostics contract。
- User Touchpoint Full-Stack Engineer：C worker，验证或小补 mobile first-screen panel。
- Product Manager / OKR Owner：closeout，后续工程完成后更新 `OKR.md`、progress log 和本 sprint 后续文档。

## 6. 风险和边界

本轮不是 real route/elevator field pass，不是 Nav2/fixed-route proof，不是 task record/completion signal，不是 dropoff/cancel completion，不是 delivery success，不是 HIL，不是 WAVE ROVER/UART，不是真实手机/browser，不是 Objective 5 external proof。

如果任一 worker 需要新增 WAVE ROVER、UART、波特率、JSON 指令、速度映射、反馈协议、引脚、电压、固件、2D LiDAR、ToF 或机械尺寸事实，必须先读 `docs/vendor/VENDOR_INDEX.md` 及其指向资料。本轮默认不新增硬件事实，只引用 PR #5 review 作为材料缺口依据。
