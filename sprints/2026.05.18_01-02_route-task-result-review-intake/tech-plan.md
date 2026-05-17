# Sprint 2026.05.18_01-02 Route Task Result Review Intake - Tech Plan

sprint_type: epic

## 1. 技术目标

新增 `route_task_field_retest_result_review_intake`，承接上一轮 `route_task_field_retest_result_callback_review_handoff`，形成 PC gate、Robot diagnostics consumer、mobile/web read-only panel 和 Product closeout 四段链路。

本轮技术目标只证明：repo 能在 Docker-only / PC-only 环境中把 result callback review handoff 摄取成 metadata-only result review intake summary，并在 Robot / mobile 触点 fail closed 展示。证据边界为 `software_proof_docker_route_task_field_retest_result_review_intake_gate`。

必须保持：

- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

## 2. Owner 拆分

### Task A - Autonomy Algorithm Engineer

允许改动：

- `pc-tools/evidence/route_task_field_retest_result_review_intake.py`
- `pc-tools/evidence/test_route_task_field_retest_result_review_intake.py`
- `docs/interfaces/evidence_contracts.md`

任务：

- 新增 PC gate `route_task_field_retest_result_review_intake.py`。
- 输入上一轮 handoff artifact / summary，输出 `trashbot.route_task_field_retest_result_review_intake.v1` artifact 与 summary。
- 校验 schema、safe `evidence_ref`、handoff status、review-ready package、rerun package、owner follow-up、next required evidence。
- 检测 forbidden success copy、raw path、checksum、credential、raw artifact、unsafe evidence ref。
- 缺失或 mismatch 必须 fail closed。
- 更新 evidence contract 文档。

验收命令：

```bash
python3 -m py_compile pc-tools/evidence/route_task_field_retest_result_review_intake.py
python3 -m unittest pc-tools/evidence/test_route_task_field_retest_result_review_intake.py
rg -n "route_task_field_retest_result_review_intake|software_proof_docker_route_task_field_retest_result_review_intake_gate|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence docs/interfaces/evidence_contracts.md
git diff --check -- pc-tools/evidence/route_task_field_retest_result_review_intake.py pc-tools/evidence/test_route_task_field_retest_result_review_intake.py docs/interfaces/evidence_contracts.md
```

### Task B - Robot Platform Engineer

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

任务：

- 在 diagnostics 中新增 `route_task_field_retest_result_review_intake` metadata-only consumer。
- 缺 summary 时输出 blocked/not_proven，不编造 route/elevator 状态。
- 输出 phone-safe / diagnostics-safe summary，保留 `delivery_success=false` 与 `primary_actions_enabled=false`。
- 不暴露 raw artifact、local absolute path、checksum、raw ROS topic、`/cmd_vel`、serial/UART、WAVE ROVER 参数、credentials。
- 更新 ROS contract 文档。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_task_field_retest_result_review_intake|software_proof_docker_route_task_field_retest_result_review_intake_gate|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

### Task C - User Touchpoint Full-Stack Engineer

允许改动：

- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

任务：

- 在 mobile/web 增加只读 “路线/电梯结果复核入口” panel。
- 从 `/api/status`、`phone_readiness`、`/api/diagnostics`、`diagnostics.summary`、`diagnostics.diagnostics_summary` 或 nested summary 中消费 `route_task_field_retest_result_review_intake` / summary。
- 只展示 review intake status、safe `evidence_ref`、missing materials、owner follow-up、rerun package、next required evidence、evidence boundary、not_proven。
- 不改变 Start Delivery、Confirm Dropoff、Cancel gating。
- 不 fetch raw artifacts，不发送 ACK、cursor、diagnostics fetch 或 robot command。
- 更新 fixture/test 和 mobile user flow 文档。

验收命令：

```bash
python3 -m unittest mobile.web.test_mobile_web_entrypoint
node --check mobile/web/app.js
rg -n "route_task_field_retest_result_review_intake|software_proof_docker_route_task_field_retest_result_review_intake_gate|not_proven|delivery_success=false|primary_actions_enabled=false" mobile docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### Task D - Product Manager / OKR Owner

允许改动：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.18_01-02_route-task-result-review-intake/tech-done.md`
- `sprints/2026.05.18_01-02_route-task-result-review-intake/side2side_check.md`
- `sprints/2026.05.18_01-02_route-task-result-review-intake/final.md`

任务：

- 在 A/B/C 完成后核对用户价值、OKR 映射和证据边界。
- 只把本轮写成 software proof / metadata-only / Docker-only 进展。
- Objective 2 / Objective 3 是否上调必须谨慎：若没有真实 route/elevator field materials，不上调或只写边界内微调。
- Objective 5 不因本轮上调。
- Objective 1 不因本轮上调。
- 更新 sprint closeout 文档。

验收命令：

```bash
test -f sprints/2026.05.18_01-02_route-task-result-review-intake/tech-done.md && test -f sprints/2026.05.18_01-02_route-task-result-review-intake/side2side_check.md && test -f sprints/2026.05.18_01-02_route-task-result-review-intake/final.md
rg -n "route_task_field_retest_result_review_intake|software_proof_docker_route_task_field_retest_result_review_intake_gate|Objective 5|Objective 1|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_01-02_route-task-result-review-intake
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_01-02_route-task-result-review-intake/tech-done.md sprints/2026.05.18_01-02_route-task-result-review-intake/side2side_check.md sprints/2026.05.18_01-02_route-task-result-review-intake/final.md
```

## 3. 并行启动计划

本轮是跨 owner Epic sprint，且 Task A / B / C 文件范围互不重叠，必须并行启动 3 个 worker：

- Autonomy worker：Task A。
- Robot worker：Task B。
- Full-stack worker：Task C。

Product worker 在 A/B/C 返回后执行 Task D closeout。主节点只做子 agent 派发、结果验收、证据核对和最终汇总，不直接写产品代码、测试代码或硬件配置。

## 4. 接口契约

新 contract：

- artifact schema：`trashbot.route_task_field_retest_result_review_intake.v1`
- summary schema：`trashbot.route_task_field_retest_result_review_intake_summary.v1`
- evidence boundary：`software_proof_docker_route_task_field_retest_result_review_intake_gate`

最小 summary 字段：

- `schema`
- `schema_version`
- `intake_status`
- `source_schema`
- `source_evidence_ref`
- `evidence_ref`
- `same_evidence_ref_required=true`
- `missing_materials`
- `owner_follow_up`
- `review_ready_package`
- `rerun_package`
- `next_required_evidence`
- `evidence_boundary`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

fail-closed 规则：

- unsafe 或 mismatch `evidence_ref`：blocked。
- 缺 handoff summary / source schema mismatch：blocked。
- success claim、delivery pass、HIL pass、real phone proof、Objective 5 external proof copy：blocked。
- raw artifact、local absolute path、checksum、credential、serial/UART、WAVE ROVER low-level detail 泄漏：blocked。
- missing true field materials：保持 `not_proven`，只给 next required evidence。

## 5. OKR 最低优先级核对

当前 `OKR.md` 4.1 完成度排序：

1. Objective 5：约 68%，最低。
2. Objective 1：约 81%，次低。
3. Objective 2 / Objective 3 / Objective 4：均约 99%。

本 sprint 不针对 Objective 5。理由：Objective 5 的下一步真实进展需要公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser external proof，本 Docker-only 主机不能提供。继续做本地 metadata depth 会重复消费 O5 blocker。

本 sprint 不针对 Objective 1。理由：Objective 1 的剩余进展需要真实 WAVE ROVER、真实 UART、真实串口日志、真实 `feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery`、operator HIL report；最近三轮已经围绕 WAVE ROVER HIL packet intake/review/execution-pack 消费同一真实硬件 blocker，本轮不能第三次包装同一 blocker。

本 sprint 选择 Objective 2 / Objective 3。理由：PR #4 route/elevator result chain 仍缺真实现场材料，但上一轮已经把 callback review decision 转成 result review 前 handoff；本轮可以在 Docker-only 主机上把 handoff 消费为 `route_task_field_retest_result_review_intake`，为下一次真实现场材料回填建立严格 intake gate，同时保持 `software_proof_docker_route_task_field_retest_result_review_intake_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

PR #5 的 monocular camera + 2D LiDAR + ToF safety ring、参数化传感器配置和硬件材料边界仍是独立缺口；本轮只在计划与 acceptance 中保留该缺口，不写成真实 sensor/HIL 进展。

## 6. PR / 评审证据映射

- PR #4：`Add elevator-assisted delivery capability to agents, registry and OKR`，已合并。它把 elevator-assisted delivery 写入 agents、registry 和 `OKR.md`，推动 O2/O3 route/elevator evidence chain；Testing 明确没有 runtime integration tests。本轮补 result review intake，正是为了让 PR #4 的 route/elevator result materials 进入可复核证据链。
- PR #5：`Make elevator-assisted delivery mandatory; update agents, OKR and hardware baseline`，已合并。它把 elevator assisted delivery 设为 required MVP，写入 monocular camera + 2D LiDAR + ToF safety ring、参数化传感器配置和硬件材料边界。本轮不解决真实 2D LiDAR / ToF SKU/source/receipt/install/wiring/calibration/HIL-entry 缺口，只把这些仍缺材料写进 next required evidence。
- 最新 sprint final：`route_task_field_retest_result_callback_review_handoff` 已完成 handoff；下一轮需要 result review intake。本文即创建 fresh sprint 进入该下一步。

## 7. 风险和边界

- 本轮不是 hardware sprint，不查改 vendor 硬件细节，不写 UART、波特率、引脚、电压或机械尺寸结论。
- 本轮不证明真实 route/elevator field pass、真实 Nav2/fixed-route、真实手机/browser、真实 WAVE ROVER、HIL、真实 dropoff/cancel completion 或 delivery success。
- 本轮不推进 Objective 5 external proof。
- mobile/web 只读 panel 不能影响主操作授权。
- 文档和代码注释质量由各 Engineer 在实现中保证；新增技术注释必须中文且解释为什么，注释比例超过 20%。

## 8. 本计划文件验收命令

```bash
test -f sprints/2026.05.18_01-02_route-task-result-review-intake/pre_start.md && test -f sprints/2026.05.18_01-02_route-task-result-review-intake/prd.md && test -f sprints/2026.05.18_01-02_route-task-result-review-intake/tech-plan.md
rg -n "sprint_type: epic|route_task_field_retest_result_review_intake|OKR 最低优先级核对|Objective 5|Objective 1|PR #4|PR #5|software_proof_docker_route_task_field_retest_result_review_intake_gate|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.18_01-02_route-task-result-review-intake
git diff --check -- sprints/2026.05.18_01-02_route-task-result-review-intake/pre_start.md sprints/2026.05.18_01-02_route-task-result-review-intake/prd.md sprints/2026.05.18_01-02_route-task-result-review-intake/tech-plan.md
```
