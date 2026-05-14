# Sprint 2026.05.15_01-02 Route Task Field Run Intake Crosscheck - Tech Plan

sprint_type: epic

## 1. 技术目标

交付 `route_task_field_run_intake` / crosscheck 软件能力，把 `software_proof_docker_route_task_field_run_readiness_gate` 的 handoff 推进为 `software_proof_docker_route_task_field_run_intake_crosscheck_gate`。

该能力必须用同一 `evidence_ref` 接收和校验 route status、task record、Nav2/fixed-route runtime log、robot-side task evidence、support-safe mobile summary，输出：

- `missing_materials`
- `mismatch_reasons`
- `not_proven`
- `commands_to_rerun`
- phone-safe summary

## 2. 架构与接口

### 2.1 新 artifact 契约

建议 schema：

- `schema=trashbot.route_task_field_run_intake_crosscheck.v1`
- `schema_version=1`
- `evidence_boundary=software_proof_docker_route_task_field_run_intake_crosscheck_gate`
- `same_evidence_ref_required=true`
- `delivery_success=false`
- `primary_actions_enabled=false`

建议顶层字段：

- `overall_status`: `ready_for_review`、`blocked_missing_material`、`blocked_mismatch`、`blocked_unsupported_schema`、`blocked_unsafe_summary`
- `evidence_ref`
- `source_materials`
- `missing_materials`
- `mismatch_reasons`
- `commands_to_rerun`
- `phone_safe_summary`
- `not_proven`

### 2.2 输入材料

CLI 需要支持以下参数或等价 JSON 输入：

- `--route-status-json`
- `--task-record-json`
- `--runtime-log-json`
- `--robot-side-task-evidence-json`
- `--support-safe-mobile-summary-json`
- `--evidence-ref`
- `--once-json`

输入材料可以是 artifact 或 summary，但必须是 JSON object。缺失、坏 JSON、unsupported schema、unsafe summary 都必须变成 blocked 状态，不得抛出未处理异常。

### 2.3 Crosscheck 规则

- 所有材料都要提取 `evidence_ref`；顶层、summary、route/task 子对象中的兼容字段都可以读取，但输出要脱敏为 safe ref。
- 任何材料缺失：`overall_status=blocked_missing_material`。
- 任何 `evidence_ref` 不一致：`overall_status=blocked_mismatch`，`mismatch_reasons` 包含来源名称和不一致原因。
- 任一 source schema 不支持：`overall_status=blocked_unsupported_schema`。
- 任一输出含敏感词：`overall_status=blocked_unsafe_summary` 或至少阻断 phone-safe copy。
- happy path 只能是 `ready_for_review`，不能是 delivery success。

### 2.4 Phone-safe summary

`phone_safe_summary` 只能包含：

- schema / boundary / status
- 同一 `evidence_ref` 的 safe ref
- 材料是否 present/missing/mismatch
- `commands_to_rerun` 摘要
- `not_proven`
- ACK 语义：accepted/processing/support metadata only, not delivery success

不得包含：

- raw artifact
- 完整本地路径
- raw ROS topic、`/cmd_vel`
- 串口/UART、baudrate、WAVE ROVER 参数
- token、Authorization、OSS AK/SK、root password
- DB/queue URL
- traceback、checksum、complete artifact、raw robot response

## 3. Owner / File Scope

### Task A - `autonomy-engineer` P0

允许改动：

- `pc-tools/evidence/route_task_field_run_intake.py`
- `pc-tools/evidence/test_route_task_field_run_intake.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

职责：

- 新增 intake/crosscheck CLI 和 artifact builder。
- 覆盖 happy path、missing material、mismatched evidence_ref、unsupported schema、unsafe summary redaction。
- 文档说明该 gate 是 `software_proof_docker_route_task_field_run_intake_crosscheck_gate`，不是真实 Nav2/fixed-route、真实路线采集、HIL 或 delivery success。

### Task B - `robot-software-engineer` P0

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

职责：

- 在 diagnostics 中 metadata-only 消费 `route_task_field_run_intake` / `route_task_field_run_intake_summary`。
- 只输出 phone-safe summary，不读取 raw artifact 内容到 mobile copy。
- 证明 metadata-only summary 不触发 collect/dropoff/cancel、ACK POST、cursor advance/persistence、Nav2、HIL、dropoff/cancel completion 或 delivery success。

### Task C - `full-stack-software-engineer` P1

允许改动：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

职责：

- 新增只读“路线任务现场材料复核”或等价 panel。
- 消费 `route_task_field_run_intake`、`route_task_field_run_intake_summary` 或 nested phone_readiness/diagnostics compatible summary。
- 显示 status、safe evidence_ref、missing/mismatch、commands_to_rerun、not_proven 和 boundary。
- 不改变 Start Delivery、Confirm Dropoff、Cancel gating；不发起任何 robot command。

### Task D - `product-okr-owner` P1

允许改动：

- `sprints/2026.05.15_01-02_route-task-field-run-intake-crosscheck/tech-done.md`
- `sprints/2026.05.15_01-02_route-task-field-run-intake-crosscheck/side2side_check.md`
- `sprints/2026.05.15_01-02_route-task-field-run-intake-crosscheck/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

职责：

- 在 Engineer 验证返回后收口 sprint。
- 仅当 intake/crosscheck、diagnostics、mobile/docs 全部通过后，谨慎更新 Objective 2 / Objective 3 进度。
- Objective 5 不因本地 metadata 增长；Objective 1 不因本地 artifact 增长。

## 4. 并行执行要求

- 本 sprint 为 Epic，默认 3 个 Engineer 并行执行：Task A、Task B、Task C。
- Task B 依赖 Task A 的 schema 名称和 summary 字段，但不应串行等待完整实现；可以先按本 tech-plan 契约写 metadata-only mapper/test，再在集成时对齐字段名。
- Task C 依赖 Task B 对外 summary 形状，但也可以先按 compatible candidate resolver 和 fixture 实现。
- 主节点不得自己写产品代码、测试代码或硬件配置；如果执行阶段出现失败，必须把定位和修复任务派回对应 owner。

## 5. 验收命令

Task A `autonomy-engineer` 必须运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_run_intake.py
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/test_route_task_field_run_intake.py
python3 pc-tools/evidence/route_task_field_run_intake.py --help
python3 pc-tools/evidence/route_task_field_run_intake.py --once-json --route-status-json <tmp-route-status.json> --task-record-json <tmp-task-record.json> --runtime-log-json <tmp-runtime-log.json> --robot-side-task-evidence-json <tmp-robot-evidence.json> --support-safe-mobile-summary-json <tmp-mobile-summary.json> --evidence-ref <same-ref>
rg -n "route_task_field_run_intake|software_proof_docker_route_task_field_run_intake_crosscheck_gate|missing_materials|mismatch_reasons|commands_to_rerun|not_proven|delivery_success|HIL" pc-tools/evidence/route_task_field_run_intake.py pc-tools/evidence/test_route_task_field_run_intake.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
git diff --check -- pc-tools/evidence/route_task_field_run_intake.py pc-tools/evidence/test_route_task_field_run_intake.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
```

Task B `robot-software-engineer` 必须运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics
rg -n "route_task_field_run_intake|software_proof_docker_route_task_field_run_intake_crosscheck_gate|metadata-only|not_proven|delivery success|HIL|ACK|cursor" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

Task C `full-stack-software-engineer` 必须运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_mobile_web_entrypoint
python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "route_task_field_run_intake|software_proof_docker_route_task_field_run_intake_crosscheck_gate|commands_to_rerun|not_proven|delivery success|HIL|Start Delivery|Confirm Dropoff|Cancel" mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

Product planning 本轮已限定只运行：

```bash
rg -n "sprint_type: epic|route_task_field_run_intake|software_proof_docker_route_task_field_run_intake_crosscheck_gate|Objective 2|Objective 3|Objective 5|not_proven|delivery success|HIL|OKR 最低优先级核对" sprints/2026.05.15_01-02_route-task-field-run-intake-crosscheck
git diff --check -- sprints/2026.05.15_01-02_route-task-field-run-intake-crosscheck/pre_start.md sprints/2026.05.15_01-02_route-task-field-run-intake-crosscheck/prd.md sprints/2026.05.15_01-02_route-task-field-run-intake-crosscheck/tech-plan.md
```

## 6. 接口影响

- 新增 PC evidence artifact schema：`trashbot.route_task_field_run_intake_crosscheck.v1`。
- 新增 diagnostics summary 字段：`route_task_field_run_intake` 和 alias `route_task_field_run_intake_summary`。
- 新增 mobile compatible candidate：从 `/api/status`、`phone_readiness` 或 `/api/diagnostics` 消费上述 summary。
- 不修改 `/api/collect`、`/api/dropoff/confirm`、`/api/cancel` 请求语义。
- 不修改 remote command、ACK、cursor、Nav2/fixed-route 执行接口。
- 不新增硬件配置、串口参数、WAVE ROVER 参数或 vendor 假设。

## 7. 风险边界

- 本轮只能声明 Docker/local software proof。
- `ready_for_review` 只表示材料形状可人工复盘，不表示真实路线、真实送达、投放完成或取消完成。
- `delivery_success` 必须保持 false；文案必须明确 “not delivery success”。
- `not_proven` 必须覆盖：真实 Nav2/fixed-route、真实路线采集、WAVE ROVER、串口/UART、HIL、dropoff/cancel completion、delivery success、Objective 5 external proof。
- 如果真实外部 O5 材料缺失，不得通过本轮 artifact 提升 Objective 5。
- 如果真实硬件/HIL 缺失，不得通过本轮 artifact 提升 Objective 1。
- docs 更新是实现阶段必做项；否则代码功能即使通过测试也不能收口。

## 8. OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 68%。
- 本 sprint 是否针对该最低 Objective：否。
- 如不针对，理由：Objective 5 下一步有效推进需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 等外部材料；当前主机只有 Docker/local 软件环境，继续堆本地 O5 metadata 不能提升 external proof，且会重复消费同一类 blocked-by-design 证据。
- Objective 1 约 75%，但仍缺真实 WAVE ROVER、串口/UART、`T=1001` feedback 和 HIL；本轮也不继续消费 O1 blocker。
- 本轮改投 Objective 2 / Objective 3：从上轮 readiness handoff 继续推进 route-task field-run material intake/crosscheck 软件能力，为后续真实路线/任务 field run 建立同一 `evidence_ref` 复盘入口。
- `final.md` 收口时需复核：O5 external 材料是否仍缺失；O1 HIL 是否仍缺失；本轮是否只提升 O2/O3 软件复盘能力，且没有宣称 delivery success 或 HIL。

## 9. 收口文档要求

- Engineer 完成后必须更新 `tech-done.md`，列出实际改动、验证输出、失败定位和剩余风险。
- Product owner 必须更新 `side2side_check.md`，对照 PRD 验收 missing/mismatch/not_proven/commands_to_rerun 和 mobile/diagnostics 只读边界。
- Product owner 必须更新 `final.md`，明确 OKR 进度是否调整、证据边界、未完成事项。
- 若 OKR 调整成立，最后再更新 `OKR.md` 和 `docs/process/okr_progress_log.md`；planning 阶段不得修改 `OKR.md`。
