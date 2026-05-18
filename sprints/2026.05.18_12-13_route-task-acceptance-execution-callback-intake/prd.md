# Sprint 2026.05.18_12-13 Route Task Acceptance Execution Callback Intake - PRD

## 1. 用户价值和产品北极星

用户价值：现场 owner 完成 acceptance execution pack 中的操作后，可以把回执材料按安全 packet 回传，Product、Autonomy、Robot diagnostics 和 mobile/web 都能看见同一份摄取结果、缺口和下一步，而不需要人工翻聊天记录或解释 raw artifacts。

产品北极星：PR #4 的 elevator-assisted delivery 主链能从“执行包已准备”推进到“现场回执可摄取、可复核、可继续补齐”，但始终清楚标注当前仍是 `not_proven`，不把回执摄取误报为真实送达成功。

## 2. OKR 映射

- Objective 2：电梯 assisted delivery 必达闭环需要真实门状态、楼层确认、人工协助记录、dropoff/cancel completion 和 delivery result。本轮只建立 callback intake 入口，让这些材料能被安全接回并判定缺口。
- Objective 3：Nav2/fixed-route 验收需要 runtime log、route completion signal、task record 和同一 `evidence_ref` 复账。本轮把回执 packet 的 evidence_ref 对齐与缺失材料状态做成可复核 artifact。
- Objective 4：手机用户体验需要只读展示现场回执摄取状态和下一步，不开放 Start Delivery、Confirm Dropoff、Cancel 或任何 primary action。
- Objective 5：不推进。当前缺真实 HTTPS/TLS、公网、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 和真实手机/browser external proof，O5 stop rule 成立。
- Objective 1：不推进。当前缺真实 WAVE ROVER、UART、HIL packet、`/dev/ttyUSB*`、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery` 和 operator HIL report，且同一硬件 blocker 近期已重复消费。

## 3. KR 拆解或更新

KR-A Autonomy：新增 `route_task_field_retest_acceptance_execution_callback_intake` PC gate，消费 `route_task_field_retest_acceptance_execution_pack` artifact/summary/wrapper 与 safe callback packet，输出 callback intake artifact/summary。

KR-B Robot：diagnostics 支持 callback-intake artifact/summary/nested wrapper/file/env source，输出 `route_task_field_retest_acceptance_execution_callback_intake`、`route_task_field_retest_acceptance_execution_callback_intake_summary` 和 `robot_diagnostics_route_task_field_retest_acceptance_execution_callback_intake_summary` safe alias。

KR-C Full-stack：mobile/web 新增只读 callback-intake panel，展示 safe `evidence_ref`、source execution pack、callback packet status、received/missing/rejected materials、owner next steps、safe copy、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

KR-D Product：后续收口时只根据实际 worker 证据更新 `tech-done.md`、`side2side_check.md`、`final.md` 与必要 OKR 进度；若只有 software proof，不把 Objective 2/3/4 写成真实 field pass，也不提高 Objective 5 production proof。

## 4. 本轮核心抓手

本轮不是再派发执行包，而是把执行包后的现场回执接回来：

- source pack gate：确认 callback 对应的 acceptance execution pack schema、safe `evidence_ref`、owner checklist 与 required materials。
- safe callback packet：只允许白名单材料摘要，不允许 raw ROS topic、`/cmd_vel`、serial/UART、credentials、local paths、完整 artifact、checksum、traceback 或 success/control wording。
- callback intake decision：对真实门状态、楼层确认、人工协助记录、Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion、delivery result 和 diagnostics/mobile safe summary 做 received/missing/rejected 分类。
- fail-closed boundary：unsupported schema、missing/weak `evidence_ref`、source/callback evidence_ref mismatch、unsafe copy、success/control wording、`delivery_success=true` 或 `primary_actions_enabled=true` 必须阻断。

## 5. 需要做什么

1. Autonomy 新增 PC callback-intake gate 和 focused unittest。
2. Robot 新增 diagnostics callback-intake safe summary 和 focused unittest。
3. Full-stack 新增 mobile/web 只读 callback-intake panel、fixture 和 focused unittest。
4. Product 在实现完成后核对证据边界、补齐 Epic sprint 后三份文档，并保守更新 OKR 进展。

## 6. 优先级和验收口径

P0：所有产物必须同时引用 source acceptance execution pack 与 safe callback packet，并输出 `software_proof_docker_route_task_field_retest_acceptance_execution_callback_intake_gate`。

P0：所有端保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。任何 success/control wording 都必须 fail closed。

P0：callback packet 与 source execution pack 必须强制同一 safe `evidence_ref`；不一致时输出 blocked/mismatch，不得继续写成 ready。

P1：artifact/summary 必须覆盖 route/elevator required materials 的 received/missing/rejected 分类、owner next steps、safe copy 和 next required evidence。

P1：mobile/web 只读展示，不得启用 Start Delivery、Confirm Dropoff、Cancel、ACK、cursor 或 robot command routes。

P2：PR #5 hardware boundary / 2D LiDAR / ToF 材料缺口只能作为风险列出，不得写成已解决或本轮验收完成。

## 7. 对应责任 Engineer

- Autonomy Algorithm Engineer：PC evidence gate、callback intake schema、safe callback packet validation。
- Robot Platform Engineer：Robot diagnostics safe summary consumer 与 `robot_diagnostics_*` alias。
- User Touchpoint Full-Stack Engineer：mobile/web callback-intake panel、fixture、browser-safe copy boundary。
- Product Manager / OKR Owner：OKR 映射、验收边界、sprint 留档、阶段验收和后续 OKR 保守收口。

## 8. 风险、阻塞和需要补齐的证据链

- Objective 5 仍缺真实 HTTPS/TLS、公网、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 和真实手机/browser external proof。
- Objective 1 仍缺真实 WAVE ROVER/UART/HIL、真实串口日志和真实 feedback/odom/imu/battery 样本。
- Objective 2/3/4 仍缺真实 route/elevator field pass、真实 Nav2/fixed-route、真实 route completion signal、真实 task record、真实门状态、真实楼层确认、人工协助记录、真实 dropoff/cancel completion 和真实 delivery result。
- PR #5 仍缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。
- 本轮 callback intake 只能证明 repo-local safe packet 摄取和 fail-closed 展示，不证明现场材料真实性。

## 9. 需要创建或更新的 sprint 文档

本轮已创建规划文档：

- `sprints/2026.05.18_12-13_route-task-acceptance-execution-callback-intake/pre_start.md`
- `sprints/2026.05.18_12-13_route-task-acceptance-execution-callback-intake/prd.md`
- `sprints/2026.05.18_12-13_route-task-acceptance-execution-callback-intake/tech-plan.md`

后续实现与验收必须继续补齐：

- `sprints/2026.05.18_12-13_route-task-acceptance-execution-callback-intake/tech-done.md`
- `sprints/2026.05.18_12-13_route-task-acceptance-execution-callback-intake/side2side_check.md`
- `sprints/2026.05.18_12-13_route-task-acceptance-execution-callback-intake/final.md`
