# Sprint 2026.05.19_16-17 Task Terminal Field Material Review Decision - Tech Plan

## 1. 目标

实现 `task_terminal_field_material_review_decision` Docker/local software-proof chain：

- Robot diagnostics 暴露 `robot_diagnostics_task_terminal_field_material_review_decision_summary`。
- mobile/web 展示只读“现场材料复核决策”panel，并保持 Start Delivery、Confirm Dropoff、Cancel gating 不扩大。
- Autonomy/PC evidence gate 将 terminal field material intake 的 returned/missing materials 转成 accepted/missing/rejected、owner_handoff、next_required_evidence 和 rerun guidance。
- Product closeout 更新 sprint、OKR 和 progress log，但不提高 O5/O1 真实进度。

证据边界必须保持：`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

本轮不是 O5 external proof，不是 O1 HIL，不是 PR #4 route/elevator field pass，不证明真实手机、真实电梯、真实 Nav2/fixed-route、真实 dropoff/cancel completion、真实 delivery success、真实 WAVE ROVER/UART/HIL 或 PR #5 真实 2D LiDAR / ToF 材料。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5，约 68%。
2. 本 sprint 不针对 Objective 5 completion。
3. 具体理由：Objective 5 下一步需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser external proof；当前本机只有 Docker，不能生成这些外部材料。继续做本地 O5 metadata depth 不会提高真实 O5 进度，并会重复消费 blocker。
4. 下一低项是 Objective 1，约 81%。PR #5 已有两个 docs-closeout thread resolved，但 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `blocked_pending_real_materials`，只能由真实 2D LiDAR / ToF vendor/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料解锁。本轮不得关闭该 thread，也不得写成 Objective 1 进展。
5. 本轮选择 Objective 2 / Objective 3 / Objective 4 的主链路 evidence hygiene：PR #4 让 elevator-assisted delivery 成为主链路，`task_terminal_field_material_intake` 已提供只读现场材料回填入口；下一步 `task_terminal_field_material_review_decision` 把 returned/missing materials 转成复核决策、owner handoff 和 rerun guidance，避免现场 owner 重复提交不完整材料或把缺口误读为通过。
6. `final.md` 收口时必须复核：如果期间拿到 O5 external proof 或 O1 real hardware/HIL materials，下一轮应优先切回对应最低 Objective；如果没有，本轮仍只能记录 `software_proof` / `not_proven`。

## 2. 角色分工和文件范围

### robot-software-engineer

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_diagnostics.md`
- 当前 sprint `tech-done.md` 中 Robot 段落

要求：

- 新增/暴露 `robot_diagnostics_task_terminal_field_material_review_decision_summary`。
- 只消费 sanitized `task_terminal_field_material_intake` / `task_terminal_field_material_review_decision` payload；缺 payload、unsupported schema、unsafe copy、raw artifact、local path、checksum、credential、success wording、field-pass wording、HIL/pass wording、O5 external proof wording 均 fail closed。
- summary 至少包含 schema/status/source、review decision、safe `evidence_ref`、accepted materials、missing materials、rejected materials、blocked materials、owner_handoff、next_required_evidence、rerun guidance、phone-safe copy、evidence boundary。
- 固定保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- 不触发 ACK、commands、collect、dropoff、cancel、Nav2、route execution、HIL、terminal ACK、cursor advance 或 robot command。
- 代码新增技术注释必须使用中文，复杂逻辑说明为什么 fail closed。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "task_terminal_field_material_review_decision|robot_diagnostics_task_terminal_field_material_review_decision_summary|accepted|missing|rejected|owner_handoff|next_required_evidence|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|Objective 2|Objective 3|PR #4|PR #5" onboard/src/ros2_trashbot_behavior docs/interfaces sprints/2026.05.19_16-17_task-terminal-field-material-review-decision
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces sprints/2026.05.19_16-17_task-terminal-field-material-review-decision
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

- mobile/web 新增只读“现场材料复核决策”panel。
- 优先消费 `robot_diagnostics_task_terminal_field_material_review_decision_summary`；缺失时 fail closed，不从 raw artifacts、ACK、cursor、old material status、completion summary 或 accepted list 推导真实成功。
- 展示 review decision、safe `evidence_ref`、accepted/missing/rejected materials、blocked materials、owner_handoff、next_required_evidence、rerun guidance、phone-safe copy、evidence boundary。
- 固定展示 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- 不扩大 Start Delivery、Confirm Dropoff、Cancel gating；不新增 ACK、cursor、diagnostics fetch、handoff route、review route、Nav2、HIL 或 robot command。
- 不展示 raw JSON、ROS topic、`/cmd_vel`、serial/UART path、baudrate、credential、local path、complete artifact、checksum、HIL/pass wording、delivery success wording、dropoff/cancel completion wording、route/elevator field-pass wording。
- 代码新增技术注释必须使用中文，解释用户安全边界和 fail-closed 原因。

验收命令：

```bash
python3 mobile/web/test_mobile_web_entrypoint.py
python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "task_terminal_field_material_review_decision|robot_diagnostics_task_terminal_field_material_review_decision_summary|现场材料复核决策|accepted|missing|rejected|owner_handoff|next_required_evidence|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|Start Delivery|Confirm Dropoff|Cancel|Objective 4|PR #4|PR #5" mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.19_16-17_task-terminal-field-material-review-decision
git diff --check -- mobile/web mobile/fixtures docs/product/mobile_user_flow.md sprints/2026.05.19_16-17_task-terminal-field-material-review-decision
```

### autonomy-engineer

允许改动：

- `pc-tools/evidence/task_terminal_field_material_review_decision.py`
- `tests/test_task_terminal_field_material_review_decision.py`
- `pc-tools/README.md`
- 当前 sprint `tech-done.md` 中 Autonomy 段落

要求：

- 新增或复用只读 CLI gate：从上一轮 `task_terminal_field_material_intake` artifact/summary 读取 returned/missing materials，输出 `task_terminal_field_material_review_decision` artifact 和 summary。
- Decision mapping 至少覆盖：
  - `ready_for_owner_handoff_not_proven`
  - `needs_required_material_backfill_not_proven`
  - `blocked_rejected_or_unsafe_materials_not_proven`
  - `blocked_evidence_ref_mismatch_not_proven`
  - `blocked_missing_or_unsupported_intake_not_proven`
- 输出字段必须包含 `accepted_materials`、`missing_materials`、`rejected_materials`、`blocked_materials`、`owner_handoff`、`next_required_evidence`、`rerun_guidance`、`same_evidence_ref_required=true`、`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- 不读取真实材料目录，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser。
- 任何 raw path、credential、ROS topic、`/cmd_vel`、serial/UART、WAVE ROVER low-level detail、checksum、complete artifact、success/control claim、`delivery_success=true`、`primary_actions_enabled=true` 或 `safe_to_control=true` 必须 fail closed。
- 代码新增技术注释必须使用中文，解释为什么只输出 review decision 而不是 field pass。

验收命令：

```bash
python3 -m py_compile pc-tools/evidence/task_terminal_field_material_review_decision.py
python3 -m unittest tests.test_task_terminal_field_material_review_decision
python3 pc-tools/evidence/task_terminal_field_material_review_decision.py --help
rg -n "task_terminal_field_material_review_decision|accepted_materials|missing_materials|rejected_materials|owner_handoff|next_required_evidence|rerun_guidance|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|Objective 3|PR #4|PR #5" pc-tools/evidence tests pc-tools/README.md sprints/2026.05.19_16-17_task-terminal-field-material-review-decision
git diff --check -- pc-tools/evidence tests pc-tools/README.md sprints/2026.05.19_16-17_task-terminal-field-material-review-decision
```

### product-okr-owner

允许改动：

- `sprints/2026.05.19_16-17_task-terminal-field-material-review-decision/tech-done.md`
- `sprints/2026.05.19_16-17_task-terminal-field-material-review-decision/side2side_check.md`
- `sprints/2026.05.19_16-17_task-terminal-field-material-review-decision/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

要求：

- 核对 Robot、Full-Stack 和 Autonomy 输出、验证日志和 docs 同步。
- 收口 Objective 5 不提高，Objective 1 不提高；Objective 2/3/4 只记录 `task_terminal_field_material_review_decision` 的主链路复核和现场 rerun guidance。
- 明确剩余风险：无真实 dropoff/cancel completion、无 delivery success、无真实电梯/Nav2/fixed-route、无真实手机、无 WAVE ROVER/UART/HIL、无 PR #5 真实 2D LiDAR / ToF 材料、无 O5 external proof。
- 不能把 review decision、accepted metadata、owner_handoff、rerun guidance、diagnostics summary、mobile panel 或 ACK 写成真实完成。

验收命令：

```bash
test -f sprints/2026.05.19_16-17_task-terminal-field-material-review-decision/tech-done.md && test -f sprints/2026.05.19_16-17_task-terminal-field-material-review-decision/side2side_check.md && test -f sprints/2026.05.19_16-17_task-terminal-field-material-review-decision/final.md
rg -n "Objective 5|Objective 1|Objective 2|Objective 3|Objective 4|PR #4|PR #5|task_terminal_field_material_review_decision|robot_diagnostics_task_terminal_field_material_review_decision_summary|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.19_16-17_task-terminal-field-material-review-decision
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.19_16-17_task-terminal-field-material-review-decision
```

### hardware-engineer

本轮不写文件。

原因：

- 本轮不涉及 WAVE ROVER、ESP32、Orange Pi、UART、波特率、JSON 指令、速度映射、反馈协议、引脚、电压、固件或机械尺寸改动。
- PR #5 2D LiDAR / ToF 真实材料仍是独立 blocker，由现场 owner 后续补齐；本轮不得新增或猜测硬件事实。
- 如果后续实现触及硬件事实，必须先读 `docs/vendor/VENDOR_INDEX.md` 及其指向的本地 vendor 文件。

## 3. 并行启动策略

本 sprint 是 Epic，跨 Robot、Full-Stack、Autonomy、Product 四个 owner。实现阶段必须同一轮并行启动至少 3 个 worker：

- `robot-software-engineer`
- `full-stack-software-engineer`
- `autonomy-engineer`

`product-okr-owner` 可在实现并行期间准备 closeout checklist，但必须等 Robot / Full-Stack / Autonomy 输出返回后才能完成 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 4. 接口边界

- Autonomy/PC gate 负责把 intake 材料分类为 accepted/missing/rejected 和 review decision。
- Robot diagnostics 是 `robot_diagnostics_task_terminal_field_material_review_decision_summary` 的 phone-safe 上游事实源。
- mobile/web 只能消费 sanitized summary，不得读取 raw artifact、从 ACK/material status/accepted list 推导 completion，或把 review decision 写成真实 field pass。
- Product closeout 只能记录 software-proof reviewability，不得上调 O5 external proof、O1 HIL、真实 route/elevator field pass、真实手机或 delivery success。
- 缺字段、unsupported schema、unsafe copy、success wording、raw path、checksum、credential、HIL/pass wording、field-pass wording、O5 external proof wording、control grant 均必须 fail closed。

建议 summary 字段：

```json
{
  "schema": "trashbot.task_terminal_field_material_review_decision_summary.v1",
  "summary_alias": "robot_diagnostics_task_terminal_field_material_review_decision_summary",
  "review_decision": "needs_required_material_backfill_not_proven",
  "source": "software_proof",
  "safe_evidence_ref": "safe-terminal-field-material-ref",
  "accepted_materials": [],
  "missing_materials": [
    "real_task_record",
    "real_dropoff_or_cancel_terminal_material",
    "real_route_elevator_field_material",
    "real_phone_browser_evidence"
  ],
  "rejected_materials": [],
  "blocked_materials": [
    "missing_real_task_record",
    "missing_real_dropoff_or_cancel_terminal_material"
  ],
  "owner_handoff": [
    "现场 owner 补齐同一 safe evidence_ref 下的真实 task record 和 terminal materials",
    "Autonomy 复核 route/elevator/Nav2 runtime log 和 route completion signal",
    "Full-Stack 复核真实手机/browser evidence"
  ],
  "next_required_evidence": [
    "同一 safe evidence_ref 的真实 task record",
    "真实 dropoff/cancel terminal materials",
    "真实 Nav2/fixed-route runtime log",
    "真实 route completion signal",
    "真实电梯门状态、目标楼层确认和人工协助记录",
    "真实手机/browser evidence"
  ],
  "rerun_guidance": [
    "补齐缺失材料后重新运行 task_terminal_field_material_intake",
    "保持同一 safe evidence_ref 后再运行 task_terminal_field_material_review_decision"
  ],
  "phone_safe_copy": "现场材料仍需补齐，当前只能查看复核决策和下一步证据要求。",
  "evidence_boundary": [
    "software_proof",
    "not_proven",
    "delivery_success=false",
    "primary_actions_enabled=false",
    "safe_to_control=false"
  ]
}
```

## 5. 风险和阻塞

- Docker-only 主机无法采集真实 dropoff/cancel completion、真实 route/elevator field pass、真实 Nav2/fixed-route runtime、真实手机/browser、WAVE ROVER/UART/HIL 或 O5 external proof。
- PR #4 真实现场材料仍是独立缺口；本轮 review decision 不能替代现场材料或现场通过。
- PR #5 2D LiDAR / ToF 真实材料仍 blocked；本轮不新增硬件假设，不关闭 `PRRT_kwDOSWB9286CJ3tX`。
- 若实现发现旧 mobile panel、diagnostics copy 或 PC gate 暗示 completion，需要降级为 `not_proven`，不能保留 success wording。

## 6. 本 Product planning 验收命令

Product Owner 启动文档完成后必须运行：

```bash
test -f sprints/2026.05.19_16-17_task-terminal-field-material-review-decision/pre_start.md && test -f sprints/2026.05.19_16-17_task-terminal-field-material-review-decision/prd.md && test -f sprints/2026.05.19_16-17_task-terminal-field-material-review-decision/tech-plan.md
rg -n "sprint_type: epic|task_terminal_field_material_review_decision|OKR 最低优先级核对|Objective 5|Objective 1|PR #4|PR #5|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.19_16-17_task-terminal-field-material-review-decision
git diff --check -- sprints/2026.05.19_16-17_task-terminal-field-material-review-decision
```
