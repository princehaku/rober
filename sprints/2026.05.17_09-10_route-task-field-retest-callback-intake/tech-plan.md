# Sprint 2026.05.17_09-10 Route Task Field Retest Callback Intake - Tech Plan

sprint_type: epic

## 1. 总体方案

实现 `route_task_field_retest_callback_intake`，作为 `route_task_field_retest_evidence_dispatch` 后的 PC / Robot / mobile software-proof 现场回执入口。该层不读取真实材料目录，不访问真实机器人或外部云，只接收 field staff sanitized callback JSON，把推荐文件名是否收到、`evidence_ref` 是否一致、缺项和下一次回填动作转成 metadata-only artifact / summary。

统一 evidence boundary：

- `software_proof_docker_route_task_field_retest_callback_intake_gate`
- `trashbot.route_task_field_retest_callback_intake.v1`
- `trashbot.route_task_field_retest_callback_intake_summary.v1`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

本轮文件范围由 3 个并行 Engineer owner 和 1 个 Product closeout owner 拆分。Task A/B/C 互不重叠，必须并行启动；Task D 等 A/B/C worker 证据返回后执行收口。

## 2. Task A - Autonomy

Owner：`autonomy-engineer`

允许改动：

- `pc-tools/evidence/route_task_field_retest_callback_intake.py`
- `pc-tools/evidence/test_route_task_field_retest_callback_intake.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

实现要求：

- 新增 dependency-free PC CLI，建议参数为 `--dispatch-json`、`--callback-json`、`--evidence-ref`、`--output`、`--summary-output`、`--once-json`。
- 兼容 `route_task_field_retest_evidence_dispatch` artifact、summary、wrapper / nested JSON。
- 接收 sanitized callback JSON，只允许 metadata 字段：recommended filename received status、safe `evidence_ref`、missing material ids、next backfill action、owner callback note、callback checklist result。
- 输出 `trashbot.route_task_field_retest_callback_intake.v1` 与 `trashbot.route_task_field_retest_callback_intake_summary.v1`。
- Summary 必须包含 intake status、safe `evidence_ref`、received filenames summary、missing materials、same-evidence-ref match result、next backfill action、callback checklist result、owner handoff、fail-closed rerun notes、not-proven 列表和 evidence boundary。
- Required evidence packet 至少覆盖 Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result。
- 不读取真实材料目录，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue 或 4G。
- 对 missing input、坏 JSON、unsupported schema/boundary、证据号不一致、弱类型 callback 字段、unsafe copy、raw path/credential/ROS topic/serial/UART/WAVE ROVER、success wording、`delivery_success=true`、`primary_actions_enabled=true` fail closed。
- 新增代码技术注释使用中文，解释为什么 fail closed、为什么只接收 sanitized callback JSON、为什么不读取真实材料目录。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_retest_callback_intake.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_callback_intake.py
python3 pc-tools/evidence/route_task_field_retest_callback_intake.py --help
rg -n "route_task_field_retest_callback_intake|software_proof_docker_route_task_field_retest_callback_intake_gate|trashbot.route_task_field_retest_callback_intake.v1|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence/route_task_field_retest_callback_intake.py pc-tools/evidence/test_route_task_field_retest_callback_intake.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
git diff --check -- pc-tools/evidence/route_task_field_retest_callback_intake.py pc-tools/evidence/test_route_task_field_retest_callback_intake.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
```

## 3. Task B - Robot

Owner：`robot-software-engineer`

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

实现要求：

- 新增 `route_task_field_retest_callback_intake` / `_summary` diagnostics metadata-only consumer。
- 支持 callback intake artifact、summary、Robot-compatible summary 和 nested diagnostics summary。
- 只暴露 safe summary、safe `evidence_ref`、intake status、received filenames summary、missing materials、same-evidence-ref match result、next backfill action、callback checklist result、boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 对 missing、unsupported schema/boundary、unsafe copy、success phrasing、`delivery_success=true`、`primary_actions_enabled=true` fail closed。
- 不改变 collect、dropoff、cancel、ACK、Nav2、HIL、cursor、diagnostics fetch 或 delivery success 语义。
- 新增代码技术注释使用中文，解释 metadata-only、sanitized callback 和动作隔离边界。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_task_field_retest_callback_intake|software_proof_docker_route_task_field_retest_callback_intake_gate|metadata-only|fail closed|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

## 4. Task C - Full-stack

Owner：`full-stack-software-engineer`

允许改动：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/status.json`
- `docs/product/mobile_user_flow.md`

实现要求：

- 新增只读“现场回执入口” panel，消费 `route_task_field_retest_callback_intake` artifact / summary / Robot diagnostics compatible summary。
- 展示 intake status、safe `evidence_ref`、received filenames summary、missing materials、same-evidence-ref match result、next backfill action、callback checklist result、boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- Start Delivery、Confirm Dropoff、Cancel gating 不变；不得新增 Start / Confirm / Cancel / ACK / cursor / robot command 请求。
- Copy/export 采用 whitelist-only，只允许导出 safe summary fields。
- 不展示 raw artifact、raw JSON、raw path、credential、ROS topic、serial/UART、WAVE ROVER、DB/queue URL、OSS AK/SK、checksums、complete artifact 或 raw robot response。
- 新增代码技术注释使用中文，解释为什么只读、为什么 copy/export 白名单、为什么主操作 gating 不变。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "route_task_field_retest_callback_intake|software_proof_docker_route_task_field_retest_callback_intake_gate|现场回执入口|not_proven|delivery_success=false|primary_actions_enabled=false|Start Delivery|Confirm Dropoff|Cancel" mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
```

## 5. Task D - Product Closeout

Owner：`product-okr-owner`

后续允许改动：

- `sprints/2026.05.17_09-10_route-task-field-retest-callback-intake/tech-done.md`
- `sprints/2026.05.17_09-10_route-task-field-retest-callback-intake/side2side_check.md`
- `sprints/2026.05.17_09-10_route-task-field-retest-callback-intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

要求：

- 汇总 A/B/C worker 的实际改动、验证结果、失败定位和剩余风险。
- 保守更新 OKR：Objective 5 不提升；Objective 2 / Objective 3 / Objective 4 是否提升必须基于实际 worker 交付和证据边界。
- 明确本轮由 `route_task_field_retest_evidence_dispatch` 继续推进，不是 Objective 5 external proof，也不是 O1 HIL-entry 或 PR #5 硬件材料真实完成。
- 明确本轮不是真实 route/elevator field pass、HIL、真实手机/browser、production app、真实投放、dropoff/cancel completion 或 delivery success。

验收命令：

```bash
rg -n "route_task_field_retest_callback_intake|software_proof_docker_route_task_field_retest_callback_intake_gate|Objective 2|Objective 3|Objective 4|Objective 5|Docker-only|not_proven|delivery_success=false|primary_actions_enabled=false|PR #4|PR #5" sprints/2026.05.17_09-10_route-task-field-retest-callback-intake OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.17_09-10_route-task-field-retest-callback-intake/tech-done.md sprints/2026.05.17_09-10_route-task-field-retest-callback-intake/side2side_check.md sprints/2026.05.17_09-10_route-task-field-retest-callback-intake/final.md OKR.md docs/process/okr_progress_log.md
```

## 6. 接口影响

- PC 新增 `trashbot.route_task_field_retest_callback_intake.v1` artifact 和 `trashbot.route_task_field_retest_callback_intake_summary.v1` summary。
- Robot diagnostics 只读消费该 summary，不新增 action route，不改变 collect、dropoff、cancel、ACK、Nav2、HIL 或 delivery success 语义。
- mobile/web 只读消费该 summary，不新增 command request，不改变 Start Delivery、Confirm Dropoff、Cancel gating。
- 文档实现阶段同步更新 `pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`、`docs/interfaces/ros_contracts.md` 和 `docs/product/mobile_user_flow.md`。

## 7. OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 68%。
- 本 sprint 是否针对该 Objective：否。
- 不针对 Objective 5 的具体原因：当前主机只有 Docker，`OKR.md` 第 6 节明确 O5 继续提升必须依赖真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser 证据。最新 `sprints/2026.05.17_08-09_cloud-worker-cutover-drain-gate/final.md` 已完成 Docker-only `cloud_worker_cutover_drain`，但明确不是 real external proof；继续 O5 local wrapper 只会重复 metadata depth，不能证明云中转产品化。
- 为什么不是继续 O1 hardware wrapper：PR #5 unresolved threads 仍暴露 mandatory sensor baseline 与默认硬件集矛盾、OKR lowest claim 漂移、mandatory sensor assumptions 缺 `docs/vendor/` source；近期硬件 HIL-entry readiness / execution pack 已连续消费该 blocker。没有真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料时，再包一层硬件 precheck 只会重复消费同一根因 blocker。
- 为什么 O2/O3 callback intake 是当前 Docker-only 下的最小可执行功能前进：`sprints/2026.05.17_06-07_route-task-field-retest-evidence-dispatch/final.md` 已把 route/elevator field materials 派发到 owner/file/backfill/callback checklist，但仍缺现场人员回传 sanitized callback metadata 的入口。本轮只做 metadata-only callback intake，把推荐文件名收到状态、same-`evidence_ref` 检查、缺项和下一次回填动作变成 PC / Robot / mobile 可消费 artifact / summary，直接补 PR #4 route/elevator field materials 回填链路，同时保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- final.md 收口时需复核：O5 外部材料是否仍不可用；O1 真实硬件材料是否仍不可用；本轮是否仍保持 `software_proof_docker_route_task_field_retest_callback_intake_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 8. 本 planning 阶段验收命令

```bash
test -f sprints/2026.05.17_09-10_route-task-field-retest-callback-intake/pre_start.md && test -f sprints/2026.05.17_09-10_route-task-field-retest-callback-intake/prd.md && test -f sprints/2026.05.17_09-10_route-task-field-retest-callback-intake/tech-plan.md
rg -n "sprint_type: epic|route_task_field_retest_callback_intake|software_proof_docker_route_task_field_retest_callback_intake_gate|Objective 5|Objective 2|Objective 3|OKR 最低优先级核对|Docker-only|not_proven|delivery_success=false|primary_actions_enabled=false|PR #4|PR #5" sprints/2026.05.17_09-10_route-task-field-retest-callback-intake
git diff --check -- sprints/2026.05.17_09-10_route-task-field-retest-callback-intake/pre_start.md sprints/2026.05.17_09-10_route-task-field-retest-callback-intake/prd.md sprints/2026.05.17_09-10_route-task-field-retest-callback-intake/tech-plan.md
```
