# Sprint 2026.05.17_12-13 Route Task Handoff Result Intake Bridge - Tech Plan

sprint_type: epic

## 1. 技术目标

让 `pc-tools/evidence/route_task_field_retest_result_intake.py` 可安全消费上一轮 `route_task_field_retest_review_result_handoff` artifact / summary / wrapper / nested JSON，并继续产出 result-intake artifact / summary：

- `trashbot.route_task_field_retest_result_intake.v1`
- `trashbot.route_task_field_retest_result_intake_summary.v1`
- `software_proof_docker_route_task_field_retest_result_intake_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

Robot/mobile 不新增控制动作，只验证既有 result-intake consumer 能读取该输出。

## 2. OKR 最低优先级核对

当前 `OKR.md` 4.1 中数字最低 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。

本 sprint 不直接针对 Objective 5。理由：

- 当前 Docker-only 主机没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser。
- 继续新增本地 O5 metadata 会重复消费同一 external-proof blocker，不能形成真实 Objective 5 progress。
- GitHub PR #5 的真实 2D LiDAR / ToF SKU/source/receipt/install/wiring/calibration/HIL-entry 材料仍缺；近期硬件材料链已经多轮消费，不适合继续写本地 wrapper。
- GitHub PR #4 已把电梯/跨楼层 assisted delivery 升级为主链必须能力；上一轮 final 指向 result handoff 到 result intake / reconciliation / execution evidence 的可行动缺口。

因此本轮选择 Objective 2 / Objective 3 的 route-task field evidence ladder，修复已发现的 handoff -> result-intake 断点。

## 3. 文件范围和责任分工

### Task A - Autonomy Algorithm Engineer

允许改动：

- `pc-tools/evidence/route_task_field_retest_result_intake.py`
- 相关 focused unittest，例如 `tests/` 或 `pc-tools/tests/` 下既有 result-intake 测试文件
- 必要的 evidence fixture，优先放在既有测试 fixture 目录
- 相关 docs 中 result-intake 说明，若代码行为变化需要同步
- 当前 sprint 的 `tech-done.md` 中 Task A 结果段

任务：

- 将 `trashbot.route_task_field_retest_review_result_handoff.v1` 和 `trashbot.route_task_field_retest_review_result_handoff_summary.v1` 加入支持来源。
- 在 `_source_candidates` 中白名单支持 review-result handoff artifact / summary / wrapper / nested JSON key。
- 确保输出仍是 result-intake schema 和 `software_proof_docker_route_task_field_retest_result_intake_gate`。
- 保留固定八类 result materials：`nav2_or_fixed_route_runtime_log`、`route_completion_signal`、`task_record`、`door_state`、`target_floor_confirmation`、`human_assistance_note`、`dropoff_or_cancel_completion`、`delivery_result`。
- 保留 unsafe copy、raw path、success claim、same-`evidence_ref` mismatch、placeholder fail-closed 行为。
- 增加 focused tests 覆盖 artifact、summary、wrapper、nested JSON、unsupported schema 和 success/control claim。

验收命令：

```bash
python3 -m py_compile pc-tools/evidence/route_task_field_retest_result_intake.py
python3 -m unittest <focused result-intake unittest module>
python3 pc-tools/evidence/route_task_field_retest_result_intake.py --help
rg -n "route_task_field_retest_review_result_handoff|route_task_field_retest_result_intake|software_proof_docker_route_task_field_retest_result_intake_gate|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools tests docs sprints/2026.05.17_12-13_route-task-handoff-result-intake-bridge
git diff --check -- pc-tools/evidence/route_task_field_retest_result_intake.py <focused test/docs files> sprints/2026.05.17_12-13_route-task-handoff-result-intake-bridge/tech-done.md
```

### Task B - Robot Platform Engineer

允许改动：

- 既有 Robot diagnostics result-intake consumer 或 focused tests
- 相关 Robot diagnostics 文档，若 consumer 读取 contract 需要同步
- 当前 sprint 的 `tech-done.md` 中 Task B 结果段

任务：

- 使用 Task A 产出的 result-intake summary 或 fixture，验证 Robot diagnostics consumer 仍按 metadata-only/read-only 读取。
- 不新增 launch 参数、硬件配置、动作授权或 `/cmd_vel` 控制路径。
- 输出必须保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

验收命令：

```bash
python3 -m unittest <focused robot diagnostics result-intake consumer test>
rg -n "route_task_field_retest_result_intake|software_proof_docker_route_task_field_retest_result_intake_gate|not_proven|delivery_success=false|primary_actions_enabled=false" onboard pc-tools docs sprints/2026.05.17_12-13_route-task-handoff-result-intake-bridge
git diff --check -- <focused robot diagnostics files> sprints/2026.05.17_12-13_route-task-handoff-result-intake-bridge/tech-done.md
```

### Task C - User Touchpoint Full-Stack Engineer

允许改动：

- 既有 mobile/web result-intake consumer 或 focused tests
- `docs/product/mobile_user_flow.md` 中 result-intake 只读说明，若 UI contract 需要同步
- 当前 sprint 的 `tech-done.md` 中 Task C 结果段

任务：

- 使用 Task A 产出的 result-intake summary 或 fixture，验证 mobile/web 仍能只读展示 result-intake 状态。
- 不改变 Start Delivery、Confirm Dropoff、Cancel 的 enable 条件。
- 不暴露 raw JSON、ROS topic、串口/UART、WAVE ROVER、credentials、DB/queue URL、本机路径、checksum、complete artifact 或 success phrasing。

验收命令：

```bash
python3 -m unittest <focused mobile/web result-intake test>
node --check mobile/web/app.js
rg -n "route_task_field_retest_result_intake|software_proof_docker_route_task_field_retest_result_intake_gate|not_proven|delivery_success=false|primary_actions_enabled=false" mobile docs/product sprints/2026.05.17_12-13_route-task-handoff-result-intake-bridge
git diff --check -- <focused mobile/web files> docs/product/mobile_user_flow.md sprints/2026.05.17_12-13_route-task-handoff-result-intake-bridge/tech-done.md
```

### Task D - Product Manager / OKR Owner

允许改动：

- `sprints/2026.05.17_12-13_route-task-handoff-result-intake-bridge/tech-done.md`
- `sprints/2026.05.17_12-13_route-task-handoff-result-intake-bridge/side2side_check.md`
- `sprints/2026.05.17_12-13_route-task-handoff-result-intake-bridge/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

任务：

- 验收 Task A/B/C 的证据。
- 检查本轮是否只证明 software proof bridge，不写成真实现场 pass。
- 若实现和验证落地，保守评估 Objective 2 / Objective 3 是否可小幅更新；Objective 5 不因本轮 bridge 更新。
- 写入 closeout 文档和 OKR progress log。

验收命令：

```bash
rg -n "route_task_field_retest_review_result_handoff|route_task_field_retest_result_intake|software_proof_docker_route_task_field_retest_result_intake_gate|Objective 2|Objective 3|Objective 5|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_12-13_route-task-handoff-result-intake-bridge
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_12-13_route-task-handoff-result-intake-bridge
```

## 4. 子 Agent 启动要求

实现阶段必须按 AGENTS.md 派发子 agent：

- Autonomy Algorithm Engineer 为主责实现 owner。
- Robot Platform Engineer 和 User Touchpoint Full-Stack Engineer 可并行做只读/窄验证，因为文件范围与 Task A 不重叠时才能改；若 Task A 输出 fixture 未就绪，可先做 consumer 事实补充并等待集成。
- Product Manager / OKR Owner 只在实现完成后做 closeout，不替 Engineer 写产品代码或测试代码。

所有子 agent prompt 必须包含：

- 角色 System Prompt。
- 本轮任务。
- 文件范围。
- 验收命令。
- 输出要求：实际改动文件、验证日志片段、失败定位、剩余风险。

## 5. 接口和数据契约

输入新增支持：

- `trashbot.route_task_field_retest_review_result_handoff.v1`
- `trashbot.route_task_field_retest_review_result_handoff_summary.v1`

输入形态：

- 顶层 artifact。
- 顶层 summary。
- wrapper JSON。
- nested JSON。

输出保持：

- `trashbot.route_task_field_retest_result_intake.v1`
- `trashbot.route_task_field_retest_result_intake_summary.v1`
- `software_proof_docker_route_task_field_retest_result_intake_gate`

固定 flags：

- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

禁止输出或弱化：

- `delivery_success=true`
- `primary_actions_enabled=true`
- raw ROS topic 或 `/cmd_vel`
- raw serial/UART/WAVE ROVER details
- credentials、DB/queue URL、OSS AK/SK、token
- local absolute path、checksum、complete artifact、raw robot response
- `field pass`、`HIL pass`、`delivery success` 等成功宣称

## 6. 风险控制

- wrapper / nested key 必须白名单，不能递归吞任意对象。
- review-result handoff readiness 只能说明可进入 result-intake，不等于 materials provided。
- required materials 仍由 result-intake gate 固定维护，不能被 upstream summary 裁剪。
- 如果 Robot/mobile 需要 UI 字段补齐，优先保持只读展示；不得为了展示开启 primary actions。
- 如果验证发现既有 consumer 已可读取，不强行改 UI 或 diagnostics code。

## 7. 本规划阶段验收命令

规划文档完成后运行：

```bash
rg -n "route_task_field_retest_review_result_handoff|route_task_field_retest_result_intake|software_proof_docker_route_task_field_retest_result_intake_gate|Objective 2|Objective 3|Objective 5|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.17_12-13_route-task-handoff-result-intake-bridge
git diff --check -- sprints/2026.05.17_12-13_route-task-handoff-result-intake-bridge/pre_start.md sprints/2026.05.17_12-13_route-task-handoff-result-intake-bridge/prd.md sprints/2026.05.17_12-13_route-task-handoff-result-intake-bridge/tech-plan.md
```
