# Sprint 2026.05.20_12-13 Field Evidence Rerun Material Dispatch - Pre Start

## 1. Sprint 声明

- sprint_type: epic
- 启动时间：2026-05-20 12:04 Asia/Shanghai
- 本轮抓手：`field_evidence_rerun_material_dispatch`
- 产品北极星：把 rober 做成普通手机用户可用的低成本 ROS2 自主垃圾投递机器人；证据不足时，手机、Robot diagnostics 和 PC gate 必须解释下一步真实材料，而不是把本地 metadata 当成真实送达。
- 证据边界：`software_proof_docker_field_evidence_rerun_material_dispatch_gate`
- 固定安全状态：`source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`

## 2. 用户价值

现场 owner 现在需要的不是再看一层本地 handoff wrapper，而是拿到一个能执行的真实材料派发包：同一 safe `evidence_ref` 下，谁要补什么、怎么重跑、补完后 Autonomy / Robot / mobile 三方用哪些命令验收。这样可以减少三类误判：

- 把 O5 本地 cloud metadata 当作真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic 或 production DB/queue proof。
- 把 O1 reply publication、vendor-source citation reply 或 PR #5 docs closeout 当作硬件/HIL 进度提升。
- 把 O4 手机 handoff wrapper 当作真实手机/browser 或 production app 现场验收。

## 3. 上轮未完成项

最新 sprint `sprints/2026.05.20_11-12_mobile-real-device-acceptance-handoff-review-handoff/final.md` 已完成 `mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff`，只推进 Objective 4 phone-safe handoff chain，OKR 百分比不提高。继续同义 handoff wrapper 会重复消费真实手机/browser blocker。

2026-05-18 route/elevator rerun chain 已推进到 `route_task_field_retest_acceptance_execution_rerun_result_review_handoff`。2026-05-19 real-material followup/escalation/status 已明确下一步需要现场 owner 提交真实材料，包括真实 route completion、task record、Nav2/fixed-route runtime log、电梯门/楼层/人工协助摘要、dropoff/cancel completion、delivery result 和真实手机/browser evidence。

## 4. OKR 排序与切换理由

- Objective 5 当前约 68%，是 `OKR.md` 4.1 数字最低 Objective。但继续提高它只能依赖真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 外部材料。本机只有 Docker，不能继续堆本地 O5 metadata depth。
- Objective 1 当前约 81%，是次低 Objective。但 PR #5 `PRRT_kwDOSWB9286CJ3tX` live 状态仍 unresolved / `is_resolved=false` / material pending；Q/U 已 resolved。reply publication 或 vendor-source citation reply 不能作为 O1 提升。
- Objective 2 / Objective 3 / Objective 4 数字较高，但共同缺口已变成真实现场材料。把这个缺口转成跨 owner 派发包，是当前 Docker-only 主机上最能减少后续误判、推进下一次真实 field rerun 的工作。

本轮因此不做 O5 / O1 / O4 同义本地 wrapper，而是启动 `field_evidence_rerun_material_dispatch`：把真实材料缺口转成 Autonomy、Robot、Full-stack 可消费、可验证、fail-closed 的受控派发包。

## 5. Owner

- Product Manager / OKR Owner：维护本轮 planning docs，定义证据边界、OKR 映射、验收口径和后续 closeout 范围。
- Autonomy Algorithm Engineer：负责 PC evidence gate 和 focused test，产出同一 safe `evidence_ref` 的真实材料派发/重跑指令。
- Robot Platform Engineer：负责 Robot diagnostics safe alias、focused test 和 ROS contract 文档，保证下游只读消费。
- User Touchpoint Full-Stack Engineer：负责 mobile/web 只读 panel、fixtures/tests 和手机用户流程文档，保证普通用户只看到安全下一步。

## 6. 阻塞与 forbidden claims

当前阻塞：

- 没有真实外部云材料，Objective 5 不能提高。
- 没有真实 WAVE ROVER/UART/HIL 和 PR #5 2D LiDAR / ToF 材料，Objective 1 不能提高。
- 没有真实现场 rerun 结果、真实手机/browser 和真实 route/elevator field pass，Objective 2 / 3 / 4 不能写成完成。

本轮禁止宣称：

- 真实 field pass、真实 route/elevator pass、delivery success、dropoff/cancel completion。
- HIL、真实 WAVE ROVER/UART、真实 `feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery`。
- Objective 5 external proof、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved。
- 真实手机/browser、production app、真实 PWA prompt/userChoice。

## 7. 本轮需要创建或更新的 sprint 文档

Planning 阶段创建：

- `sprints/2026.05.20_12-13_field-evidence-rerun-material-dispatch/pre_start.md`
- `sprints/2026.05.20_12-13_field-evidence-rerun-material-dispatch/prd.md`
- `sprints/2026.05.20_12-13_field-evidence-rerun-material-dispatch/tech-plan.md`

实现和收口阶段后续需要创建：

- `sprints/2026.05.20_12-13_field-evidence-rerun-material-dispatch/tech-done.md`
- `sprints/2026.05.20_12-13_field-evidence-rerun-material-dispatch/side2side_check.md`
- `sprints/2026.05.20_12-13_field-evidence-rerun-material-dispatch/final.md`
