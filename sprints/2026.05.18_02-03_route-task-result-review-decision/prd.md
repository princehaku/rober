# Sprint 2026.05.18_02-03 Route Task Result Review Decision - PRD

sprint_type: epic

## 1. 用户价值和产品北极星

用户价值：现场材料回传到 `route_task_field_retest_result_review_intake` 后，支持同学需要一个明确复核决策，而不是继续人工解释 intake 是否可用。本轮要让系统输出可追责的 result review decision：可进入 acceptance/backfill、缺材料、证据不一致需 rerun、或 schema 不支持。

产品北极星：普通手机用户最终只关心小车是否能可靠送达垃圾；工程侧必须把 route/elevator 的真实现场材料链做成可验证、可复核、可回填的产品能力。本轮仍停留在 software proof，不把任何 metadata-only 结果写成真实送达。

## 2. OKR 映射

- Objective 2：主目标，对齐“可送垃圾任务 + 电梯 assisted delivery 必达闭环”。本轮推进 PR #4 的 route/elevator result chain，从 review intake 进入 review decision。
- Objective 3：主目标，对齐“可验证导航与固定路线能力”。本轮要求 Nav2/fixed-route runtime log、route completion signal、task record 与同一 safe `evidence_ref` 进入决策口径。
- Objective 4：受益目标，后续只读展示 review decision，保持手机端普通用户不暴露 raw JSON、ROS topic 或控制命令。
- Objective 5：暂不推进。Objective 5 当前约 68%，但缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 和真实手机/browser external proof。
- Objective 1：暂不推进。Objective 1 当前约 81%，但最近三轮已消费同一真实 WAVE ROVER HIL packet blocker；没有真实硬件材料时不再做本地包装。

## 3. KR 拆解或更新

- KR2.4：review decision 必须把导航失败、投放失败、取消完成缺失、任务结果缺失转成明确 decision state 和 error/retry 指引。
- KR2.5：每次 route/elevator 结果复核必须保留起止材料、目标、状态、失败原因和同一 safe `evidence_ref` 的复盘引用。
- KR2.6 / KR2.7：电梯门状态、目标楼层确认、人工协助记录和 evidence_ref 必须继续作为必需材料；缺失时保持 `not_proven`。
- KR3.4 / KR3.5：Nav2 waypoint / fixed route runtime log、route completion signal、task record、关键状态和失败原因必须进入 review decision。
- KR4.6 / KR4.7：手机端只能展示中文优先、phone-safe、只读的复核决策；不得启用 Start Delivery、Confirm Dropoff 或 Cancel。

## 4. 本轮核心抓手

新增 `route_task_field_retest_result_review_decision` 能力层，承接 `route_task_field_retest_result_review_intake`：

- 读取 review intake artifact / summary 或 compatible Robot diagnostics summary。
- 验证 safe `evidence_ref`、source schema、evidence boundary 和 required materials。
- 输出 `software_proof_docker_route_task_field_retest_result_review_decision_gate`。
- 对 missing route/elevator result materials 给出 owner handoff、next required evidence 和 rerun commands。
- 输出保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 5. 需要做什么

1. Autonomy Algorithm Engineer 实现 PC gate 与 focused tests，产出 artifact / summary schema。
2. Robot Platform Engineer 接入 diagnostics metadata-only consumer，保持只读和 fail-closed。
3. User Touchpoint Full-Stack Engineer 接入 mobile/web 只读 panel、fixture 和 entrypoint tests，保持控制按钮 gating 不变。
4. Product Manager / OKR Owner 在实现后更新 sprint closeout、OKR 进度、docs 同步证据和剩余风险。

## 6. 优先级和验收口径

P0：
- 必须识别 `route_task_field_retest_result_review_intake` 上游。
- 必须输出 `route_task_field_retest_result_review_decision` artifact / summary。
- 必须保留 `software_proof_docker_route_task_field_retest_result_review_decision_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 必须 fail closed：missing intake、unsupported schema、unsafe evidence_ref、missing route/elevator material、success copy、raw credential/path/control material。

P1：
- Robot diagnostics 和 mobile/web 能只读展示 decision status、safe `evidence_ref`、missing materials、owner handoff、rerun commands 和 next required evidence。
- docs 同步更新 evidence contracts、ROS diagnostics contract 和 mobile user flow。

P2：
- Product closeout 根据实际实现更新 `OKR.md` 和 `docs/process/okr_progress_log.md`，但不得上调 O5 或 O1，除非真实外部/硬件材料出现。

验收口径：本轮完成后只能声明 `software_proof_docker_route_task_field_retest_result_review_decision_gate`，不能声明真实 route/elevator field pass、真实 Nav2/fixed-route、真实 task record、真实 dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## 7. 对应责任 Engineer

- Autonomy Algorithm Engineer：PC evidence gate、schema、decision 状态机、focused unittest。
- Robot Platform Engineer：diagnostics consumer、metadata-only ROS contract、focused diagnostics tests。
- User Touchpoint Full-Stack Engineer：mobile/web panel、fixture、phone-safe copy 和 entrypoint tests。
- Product Manager / OKR Owner：PRD、tech-plan、阶段验收、OKR 和 sprint closeout。

## 8. 风险、阻塞和需要补齐的证据链

- 真实 route/elevator field pass 仍缺：真实电梯门状态、真实楼层确认、人工协助记录、真实 Nav2/fixed-route runtime log、真实 route completion signal、真实 task record、真实 dropoff/cancel completion 和 delivery result。
- 真实硬件仍缺：WAVE ROVER、UART、HIL packet、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery` 和 operator HIL report。
- PR #5 硬件材料仍缺：2D LiDAR / ToF source、receipt、采购、安装、接线、电源、标定和 HIL-entry；`docs/vendor/` 当前不能证明这些材料已到位。
- Objective 5 仍缺：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser external proof。
- 手机端仍缺：真实 iPhone/Android、production app、真实 PWA prompt/user choice 和现场 phone behavior。

## 9. 需要创建或更新的 sprint 文档

Planning 本轮创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实现后必须继续创建或更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
- 相关 `docs/interfaces/`、`docs/product/` 文档
