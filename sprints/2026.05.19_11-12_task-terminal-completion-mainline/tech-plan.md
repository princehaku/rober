# Sprint 2026.05.19_11-12 Task Terminal Completion Mainline - Tech Plan

## 1. 目标

实现 `task_terminal_completion_mainline` Docker/local software-proof chain：

- Robot task_record / diagnostics 暴露 terminal action mainline summary。
- mobile/web 展示 terminal action mainline 状态，并保持 Start Delivery、Confirm Dropoff、Cancel gating 不扩大。
- Product closeout 更新 sprint、OKR 和 progress log。

证据边界必须保持：`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

本轮不是 O5 external proof，不是 O1 HIL，不是 PR #4 route/elevator field pass，不证明真实 dropoff completion、真实 cancel completion、真实手机或 delivery success。

## 2. OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5，约 68%。
2. 本 sprint 不针对 Objective 5 completion。
3. 具体理由：Objective 5 下一步需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser proof；当前本机只有 Docker，没有这些外部材料。继续做本地 O5 metadata wrapper 不能提高真实 O5 进度。
4. 下一低项是 Objective 1，约 81%。最新 `2026.05.19_10-11_hardware-real-material-escalation-request` 已完成 O1 硬件真实材料升级请求，并明确不能把 Docker/local `software_proof` 当真实 HIL/硬件材料；PR #5 2D LiDAR / ToF mandatory sensor real materials 仍 `blocked_pending_real_materials`。本轮不继续 O1 wrapper。
5. Objective 2 / Objective 3 / Objective 4 约 99%，但 PR #4 route/elevator field materials 已被多轮消耗并触发重复 blocker 红线。本轮不做第三个 route/elevator material wrapper，而是推进 dropoff / cancel terminal action 的主链路软件契约，让下一次真实材料回填有一致字段和安全边界。

## 3. 角色分工和文件范围

### robot-software-engineer

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_task_record.py`
- `onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_diagnostics.md`
- `docs/interfaces/task_record.md`
- 当前 sprint `tech-done.md` 中 Robot 段落

要求：

- 新增或整理 `task_terminal_completion_mainline` / `robot_diagnostics_task_terminal_completion_mainline_summary`。
- dropoff / cancel terminal action summary 必须包含 same `evidence_ref`、terminal action、terminal status、operator confirmation、missing materials、next required evidence、failure reason。
- `dropoff_completion_proven=false`、`cancel_completion_proven=false`、`delivery_success=false`、`primary_actions_enabled=false` 必须在缺真实材料时固定 fail closed。
- 不读取硬件、serial/UART、ROS graph、raw artifacts、cloud resources 或 mobile browser state。
- 不触发 collect、dropoff、cancel、ACK POST、cursor advance、Nav2、HIL、terminal ACK 或 robot command。
- 代码新增技术注释必须使用中文，且复杂逻辑注释说明为什么 fail closed。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_task_record.py onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "task_terminal_completion_mainline|robot_diagnostics_task_terminal_completion_mainline_summary|dropoff|cancel|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|Objective 2|PR #4" onboard/src/ros2_trashbot_behavior docs/interfaces sprints/2026.05.19_11-12_task-terminal-completion-mainline
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces sprints/2026.05.19_11-12_task-terminal-completion-mainline
```

### full-stack-software-engineer

允许改动：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/fixtures/status.json`
- `docs/product/mobile_user_flow.md`
- 当前 sprint `tech-done.md` 中 Full-Stack 段落

要求：

- mobile/web 新增或调整 terminal action mainline 状态展示。
- 优先消费 `robot_diagnostics_task_terminal_completion_mainline_summary`；缺失时 fail closed，不从 raw artifact 推导成功。
- 展示 safe terminal action、safe `evidence_ref`、operator confirmation、missing materials、next required evidence、evidence boundary、`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 不扩大 Start Delivery、Confirm Dropoff、Cancel gating；不新增 ACK、cursor、diagnostics fetch、handoff route、review route 或 robot command。
- 不展示 raw JSON、ROS topic、`/cmd_vel`、serial/UART path、baudrate、credential、local path、complete artifact、checksum、HIL/pass wording、delivery success wording、dropoff/cancel completion wording。
- 代码新增技术注释必须使用中文，解释用户安全边界和 fail-closed 原因。

验收命令：

```bash
python3 mobile/web/test_mobile_web_entrypoint.py
python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "task_terminal_completion_mainline|robot_diagnostics_task_terminal_completion_mainline_summary|dropoff|cancel|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|Start Delivery|Confirm Dropoff|Cancel|Objective 4|PR #4" mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.19_11-12_task-terminal-completion-mainline
git diff --check -- mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.19_11-12_task-terminal-completion-mainline
```

### product-okr-owner

允许改动：

- `sprints/2026.05.19_11-12_task-terminal-completion-mainline/tech-done.md`
- `sprints/2026.05.19_11-12_task-terminal-completion-mainline/side2side_check.md`
- `sprints/2026.05.19_11-12_task-terminal-completion-mainline/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

要求：

- 核对 Robot 和 Full-Stack worker 输出、验证日志和 docs 同步。
- 收口 Objective 5 不提高，Objective 1 不提高，Objective 2/3/4 只记录 terminal action mainline 软件契约和 phone-safe visibility。
- 明确剩余风险：无真实 dropoff completion、无真实 cancel completion、无 delivery success、无真实电梯/Nav2/fixed-route、无真实手机、无 WAVE ROVER/UART/HIL、无 PR #5 真实材料、无 O5 external proof。
- 不能把 PRD、task_record summary、diagnostics summary、mobile panel、ACK 或 material status 写成真实完成。

验收命令：

```bash
test -f sprints/2026.05.19_11-12_task-terminal-completion-mainline/tech-done.md && test -f sprints/2026.05.19_11-12_task-terminal-completion-mainline/side2side_check.md && test -f sprints/2026.05.19_11-12_task-terminal-completion-mainline/final.md
rg -n "Objective 5|Objective 1|Objective 2|Objective 4|PR #4|PR #5|task_terminal_completion_mainline|dropoff|cancel|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.19_11-12_task-terminal-completion-mainline
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.19_11-12_task-terminal-completion-mainline
```

### autonomy-engineer

只读咨询，不写文件。

咨询范围：

- 确认 terminal action summary 的 `evidence_ref`、route/fixed-route evidence、task record field 语义不与 Objective 3 route evidence 冲突。
- 指出后续真实 Nav2/fixed-route runtime log、route completion signal、dropoff/cancel material 回填时需要的字段。

输出要求：

- 只返回字段建议和风险；不得修改文件或运行验收命令。

### hardware-engineer

本轮不写文件。

原因：

- 本轮不涉及 WAVE ROVER、ESP32、Orange Pi、UART、波特率、JSON 指令、速度映射、反馈协议、引脚、电压、固件或机械尺寸改动。
- PR #5 2D LiDAR / ToF 真实材料仍是独立 blocker，由现场 owner 后续补齐；本轮不得新增或猜测硬件事实。

## 4. 并行启动策略

本 sprint 是 Epic，跨 Robot、Full-Stack、Product 三个 owner。实现阶段必须并行启动 3 个 worker：

- `robot-software-engineer`
- `full-stack-software-engineer`
- `product-okr-owner`

`product-okr-owner` 可先准备 closeout checklist 和 OKR 更新草案，但必须等 Robot / Full-Stack 验证日志返回后才能完成 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。

Autonomy 只读咨询可与两个工程 worker 并行启动；Hardware 本轮不启动写任务。

## 5. 接口边界

- Robot 是 terminal action mainline summary 的唯一上游事实源。
- mobile/web 只能消费 sanitized summary，不得读取 raw artifact 或从 ACK/material status 推导 completion。
- Product closeout 只能记录 software-proof 主链路契约，不得上调真实 completion 或 delivery success。
- 缺字段、unsupported schema、unsafe copy、success wording、raw path、checksum、credential、HIL/pass wording、field-pass wording、O5 external proof wording 均必须 fail closed。

建议 summary 字段：

```json
{
  "schema": "trashbot.task_terminal_completion_mainline.v1",
  "status": "blocked_not_proven",
  "source": "software_proof",
  "evidence_ref": "safe-terminal-evidence-ref",
  "terminal_action": "dropoff",
  "terminal_status": "missing_materials",
  "operator_confirmation_required": true,
  "operator_confirmation_status": "missing",
  "dropoff_completion_proven": false,
  "cancel_completion_proven": false,
  "delivery_success": false,
  "primary_actions_enabled": false,
  "missing_required_materials": [
    "real_task_record",
    "real_dropoff_or_cancel_completion_material",
    "same_evidence_ref_field_replay"
  ],
  "next_required_evidence": [
    "真实 task record",
    "真实 dropoff/cancel completion 材料",
    "同一 evidence_ref 的现场复账"
  ],
  "evidence_boundary": [
    "software_proof",
    "not_proven",
    "delivery_success=false",
    "primary_actions_enabled=false"
  ]
}
```

## 6. 风险和阻塞

- Docker-only 主机无法采集真实 dropoff/cancel completion、真实 route/elevator field pass、真实 Nav2/fixed-route runtime、真实手机/browser、WAVE ROVER/UART/HIL 或 O5 external proof。
- PR #4 真实现场材料仍是独立缺口；本轮主链路契约不能替代现场材料。
- PR #5 2D LiDAR / ToF 真实材料仍 blocked；本轮不新增硬件假设。
- 若实现发现旧 mobile panel 或 diagnostics copy 暗示 completion，需要降级为 `not_proven`，不能保留 success wording。

## 7. 本 Product planning 验收命令

Product Owner 启动文档完成后必须运行：

```bash
test -f sprints/2026.05.19_11-12_task-terminal-completion-mainline/pre_start.md && test -f sprints/2026.05.19_11-12_task-terminal-completion-mainline/prd.md && test -f sprints/2026.05.19_11-12_task-terminal-completion-mainline/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|Objective 1|Objective 2|Objective 4|PR #4|PR #5|task_terminal_completion_mainline|dropoff|cancel|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|robot-software-engineer|full-stack-software-engineer|product-okr-owner" sprints/2026.05.19_11-12_task-terminal-completion-mainline
git diff --check -- sprints/2026.05.19_11-12_task-terminal-completion-mainline
```
